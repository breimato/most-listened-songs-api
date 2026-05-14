from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from canciones.adapters.db.repository import SQLiteRepository
from canciones.api.dependencies import get_repository
from canciones.api.schemas import ArtistResponse, SongResponse, StatsResponse, SyncResponse
from canciones.domain.models import Play

router = APIRouter(prefix="/api/v1")


@router.post("/sync", response_model=SyncResponse)
def sync(repo: SQLiteRepository = Depends(get_repository)):
    """Fetch new scrobbles from Last.fm and store them."""
    from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

    ingestor = LastFMAPIIngestor()
    try:
        pairs = ingestor.fetch_recent()
    except ValueError as e:
        raise HTTPException(400, str(e))

    imported = 0
    skipped = 0

    for song_data, played_at in pairs:
        existing = repo.get_song_by_platform_id(song_data.platform_id)
        if existing:
            song_id = existing.id
        else:
            saved = repo.save_song(song_data)
            song_id = saved.id

        if repo.play_exists(song_id, played_at):
            skipped += 1
            continue

        repo.save_play(Play(song_id=song_id, played_at=played_at))
        imported += 1

    return SyncResponse(
        imported=imported,
        skipped=skipped,
        message=f"Imported {imported} scrobbles ({skipped} already known).",
    )


@router.get("/songs/top", response_model=list[SongResponse])
def get_top_songs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    top: int | None = Query(None, ge=1, le=500),
    year: int | None = None,
    artist: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    repo: SQLiteRepository = Depends(get_repository),
):
    effective_limit = top if top is not None else limit
    if year is not None:
        since = datetime(year, 1, 1)
        until = datetime(year, 12, 31, 23, 59, 59)
    stats = repo.get_top_songs(limit=effective_limit, offset=offset, artist=artist, since=since, until=until)
    return [
        SongResponse(id=s.song_id, title=s.title, artist=s.artist, album=s.album, plays=s.play_count)
        for s in stats
    ]


@router.get("/artists/top", response_model=list[ArtistResponse])
def get_top_artists(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    since: datetime | None = None,
    until: datetime | None = None,
    repo: SQLiteRepository = Depends(get_repository),
):
    stats = repo.get_top_artists(limit=limit, offset=offset, since=since, until=until)
    return [ArtistResponse(artist=s.artist, plays=s.play_count, songs=s.song_count) for s in stats]


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    since: datetime | None = None,
    until: datetime | None = None,
    repo: SQLiteRepository = Depends(get_repository),
):
    stats = repo.get_stats(since=since, until=until)
    return StatsResponse(
        total_plays=stats.total_plays,
        total_songs=stats.total_songs,
        total_artists=stats.total_artists,
        plays_by_month=stats.plays_by_month,
        plays_by_hour=stats.plays_by_hour,
        top_day=stats.top_day,
        first_listen=stats.first_listen,
        last_listen=stats.last_listen,
    )
