import hashlib
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from canciones.adapters.db.repository import SQLiteRepository
from canciones.adapters.youtube.api_enricher import YouTubeAPIEnricher
from canciones.adapters.youtube.takeout_parser import YouTubeTakeoutParser
from canciones.adapters.spotify.export_parser import SpotifyExportParser
from canciones.api.dependencies import get_repository
from canciones.api.schemas import (
    ArtistResponse,
    CanonicalSongResponse,
    EnrichResponse,
    IngestRequest,
    IngestResponse,
    LinkRequest,
    ListeningEventResponse,
    MergeRequest,
    PlatformSongResponse,
    PlatformSummary,
    SongResponse,
    StatsResponse,
)
from canciones.domain.models import (
    ImportLog,
    ListeningEvent,
    Platform,
    PlatformSong,
)
from canciones.domain.services import SongMatchingService

router = APIRouter(prefix="/api/v1")


# --- Ingestion ---


def _ingest(
    file_path: str,
    platform: Platform,
    parser,
    repo: SQLiteRepository,
) -> IngestResponse:
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(404, f"File not found: {file_path}")

    # Check duplicate import
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if repo.get_import_by_hash(file_hash):
        return IngestResponse(
            events_imported=0,
            events_skipped=0,
            songs_new=0,
            message="File already imported (same hash).",
        )

    pairs = parser.parse(file_path)
    events_imported = 0
    events_skipped = 0
    songs_new = 0

    for song_data, event_data in pairs:
        # Get or create platform song
        existing = repo.get_platform_song_by_platform_id(
            song_data.platform, song_data.platform_id
        )
        if existing:
            platform_song_id = existing.id
        else:
            saved = repo.save_platform_song(song_data)
            platform_song_id = saved.id
            songs_new += 1

        # Deduplicate events by (song_id, timestamp)
        if repo.event_exists(platform_song_id, event_data.listened_at):
            events_skipped += 1
            continue

        event_data.platform_song_id = platform_song_id
        repo.save_listening_event(event_data)
        events_imported += 1

    repo.save_import_log(
        ImportLog(
            filename=path.name,
            file_hash=file_hash,
            platform=platform,
            events_imported=events_imported,
        )
    )

    return IngestResponse(
        events_imported=events_imported,
        events_skipped=events_skipped,
        songs_new=songs_new,
        message=f"Imported {events_imported} events ({songs_new} new songs, {events_skipped} duplicates skipped).",
    )


@router.post("/ingest/youtube", response_model=IngestResponse)
def ingest_youtube(
    req: IngestRequest,
    repo: SQLiteRepository = Depends(get_repository),
):
    return _ingest(req.file_path, Platform.YOUTUBE, YouTubeTakeoutParser(), repo)


@router.post("/ingest/spotify", response_model=IngestResponse)
def ingest_spotify(
    req: IngestRequest,
    repo: SQLiteRepository = Depends(get_repository),
):
    return _ingest(req.file_path, Platform.SPOTIFY, SpotifyExportParser(), repo)


@router.post("/ingest/lastfm", response_model=IngestResponse)
def ingest_lastfm(
    req: IngestRequest,
    repo: SQLiteRepository = Depends(get_repository),
):
    from canciones.adapters.lastfm.export_parser import LastFMExportParser
    return _ingest(req.file_path, Platform.LASTFM, LastFMExportParser(), repo)


# --- Enrichment ---


@router.post("/enrich/youtube", response_model=EnrichResponse)
def enrich_youtube(
    repo: SQLiteRepository = Depends(get_repository),
):
    enricher = YouTubeAPIEnricher()
    songs = repo.get_platform_songs_needing_enrichment(Platform.YOUTUBE, limit=50)
    if not songs:
        return EnrichResponse(songs_enriched=0, message="No songs need enrichment.")

    enriched = enricher.enrich(songs)
    for song in enriched:
        repo.update_platform_song(song)

    return EnrichResponse(
        songs_enriched=len(enriched),
        message=f"Enriched {len(enriched)} songs with YouTube API metadata.",
    )


# --- Sync (Google Drive) ---


@router.post("/sync/youtube", response_model=IngestResponse)
def sync_youtube(
    repo: SQLiteRepository = Depends(get_repository),
):
    from canciones.adapters.google_drive.drive_sync import GoogleDriveSync
    from canciones.config import settings

    drive = GoogleDriveSync()
    files = drive.find_takeout_files()

    if not files:
        return IngestResponse(
            events_imported=0,
            events_skipped=0,
            songs_new=0,
            message="No Takeout files found in Google Drive.",
        )

    # Try each zip (sorted largest first) until we find the watch-history
    dest_dir = str(Path(settings.data_dir) / "youtube")
    extracted = None
    for f in files:
        extracted = drive.download_and_extract(f["id"], dest_dir)
        if extracted:
            break

    if not extracted:
        return IngestResponse(
            events_imported=0,
            events_skipped=0,
            songs_new=0,
            message="Downloaded all Takeout files but no watch-history found inside.",
        )

    return _ingest(extracted, Platform.YOUTUBE, YouTubeTakeoutParser(), repo)


@router.post("/sync/lastfm", response_model=IngestResponse)
def sync_lastfm(
    repo: SQLiteRepository = Depends(get_repository),
):
    from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

    ingestor = LastFMAPIIngestor()
    try:
        pairs = ingestor.fetch_recent()
    except ValueError as e:
        raise HTTPException(400, str(e))

    events_imported = 0
    events_skipped = 0
    songs_new = 0

    for song_data, event_data in pairs:
        existing = repo.get_platform_song_by_platform_id(
            song_data.platform, song_data.platform_id
        )
        if existing:
            platform_song_id = existing.id
        else:
            saved = repo.save_platform_song(song_data)
            platform_song_id = saved.id
            songs_new += 1

        if repo.event_exists(platform_song_id, event_data.listened_at):
            events_skipped += 1
            continue

        event_data.platform_song_id = platform_song_id
        repo.save_listening_event(event_data)
        events_imported += 1

    return IngestResponse(
        events_imported=events_imported,
        events_skipped=events_skipped,
        songs_new=songs_new,
        message=f"Imported {events_imported} scrobbles from Last.fm ({songs_new} new songs, {events_skipped} duplicates skipped).",
    )


# --- Query endpoints ---


@router.get("/songs/top", response_model=list[SongResponse])
def get_top_songs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    platform: str | None = None,
    artist: str | None = None,
    min_plays: int = Query(1, ge=1),
    since: datetime | None = None,
    until: datetime | None = None,
    repo: SQLiteRepository = Depends(get_repository),
):
    plat = Platform(platform) if platform else None
    stats = repo.get_top_songs(
        limit=limit,
        offset=offset,
        platform=plat,
        artist=artist,
        min_plays=min_plays,
        since=since,
        until=until,
    )
    return [
        SongResponse(
            platform_song_id=s.platform_song_id,
            title=s.title,
            artist=s.artist,
            channel=s.channel,
            platform=s.platform.value,
            platform_id=s.platform_id,
            play_count=s.play_count,
            canonical_song_id=s.canonical_song_id,
            thumbnail_url=s.thumbnail_url,
            duration_seconds=s.duration_seconds,
        )
        for s in stats
    ]


@router.get("/songs/{song_id}")
def get_song_detail(
    song_id: int,
    repo: SQLiteRepository = Depends(get_repository),
):
    canonical = repo.get_canonical_song(song_id)
    if not canonical:
        raise HTTPException(404, "Song not found")

    return CanonicalSongResponse(
        id=canonical.id,
        title=canonical.title,
        artist=canonical.artist,
        album=canonical.album,
        musicbrainz_id=canonical.musicbrainz_id,
    )


@router.get("/songs/{song_id}/history", response_model=list[ListeningEventResponse])
def get_song_history(
    song_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    repo: SQLiteRepository = Depends(get_repository),
):
    events = repo.get_events_for_song(song_id, limit=limit, offset=offset)
    return [
        ListeningEventResponse(
            id=e.id,
            platform_song_id=e.platform_song_id,
            listened_at=e.listened_at,
            platform=e.platform.value,
        )
        for e in events
    ]


@router.get("/artists/top", response_model=list[ArtistResponse])
def get_top_artists(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    platform: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    repo: SQLiteRepository = Depends(get_repository),
):
    plat = Platform(platform) if platform else None
    stats = repo.get_top_artists(
        limit=limit, offset=offset, platform=plat, since=since, until=until
    )
    return [
        ArtistResponse(
            artist=s.artist, play_count=s.play_count, song_count=s.song_count
        )
        for s in stats
    ]


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    platform: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    repo: SQLiteRepository = Depends(get_repository),
):
    plat = Platform(platform) if platform else None
    stats = repo.get_general_stats(platform=plat, since=since, until=until)
    return StatsResponse(
        total_plays=stats.total_plays,
        total_songs=stats.total_songs,
        total_artists=stats.total_artists,
        plays_by_platform=stats.plays_by_platform,
        plays_by_month=stats.plays_by_month,
        plays_by_hour=stats.plays_by_hour,
        top_day=stats.top_day,
        first_listen=stats.first_listen,
        last_listen=stats.last_listen,
    )


@router.get("/platforms", response_model=list[PlatformSummary])
def get_platforms(
    repo: SQLiteRepository = Depends(get_repository),
):
    summary = repo.get_platform_summary()
    return [PlatformSummary(**s) for s in summary]


# --- Matching ---


@router.get("/songs/unmatched", response_model=list[PlatformSongResponse])
def get_unmatched_songs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: SQLiteRepository = Depends(get_repository),
):
    songs = repo.get_unmatched_songs(limit=limit, offset=offset)
    return [
        PlatformSongResponse(
            id=s.id,
            platform=s.platform.value,
            platform_id=s.platform_id,
            title=s.title,
            artist=s.artist,
            channel=s.channel,
            canonical_song_id=s.canonical_song_id,
            duration_seconds=s.duration_seconds,
            thumbnail_url=s.thumbnail_url,
        )
        for s in songs
    ]


@router.post("/songs/link")
def link_song(
    req: LinkRequest,
    repo: SQLiteRepository = Depends(get_repository),
):
    repo.link_song(req.platform_song_id, req.canonical_song_id)
    return {"message": "Song linked successfully."}


@router.post("/songs/merge")
def merge_songs(
    req: MergeRequest,
    repo: SQLiteRepository = Depends(get_repository),
):
    repo.merge_canonical_songs(req.keep_id, req.merge_id)
    return {"message": "Songs merged successfully."}
