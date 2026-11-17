from collections import Counter
from datetime import date, datetime
from typing import Literal
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query

from canciones.adapters.artwork import find_cover
from canciones.adapters.db.repository import CancionesRepository
from canciones.adapters.lastfm.api_ingestor import to_unix_timestamp
from canciones.adapters.lastfm.tags import build_genres
from canciones.api.dependencies import get_repository, require_access_key
from canciones.api.schemas import (
    ArtistResponse,
    ArtworkResponse,
    ObsessionDayResponse,
    ObsessionResponse,
    RecapAlbumResponse,
    RecapArtistResponse,
    RecapGenreResponse,
    RecapMonthlyArtistResponse,
    RecapProfileResponse,
    RecapResponse,
    RecapSongResponse,
    SongResponse,
    SongTimelineResponse,
    StatsResponse,
    SyncResponse,
)
from canciones.config import settings
from canciones.domain.models import Play
from canciones.domain.normalization import normalized_key
from canciones.domain.obsessions import ObsessionEpisode, detect_obsessions, local_date
from canciones.domain.recap import Recap, build_recap

router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(require_access_key)],
)


@router.post("/sync", response_model=SyncResponse)
def sync(repo: CancionesRepository = Depends(get_repository)):
    """Fetch new scrobbles from Last.fm and store them."""
    from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

    ingestor = LastFMAPIIngestor()
    try:
        last_played = repo.get_last_played_at()
        from_ts = to_unix_timestamp(last_played) + 1 if last_played else None
        pairs = ingestor.fetch_recent(from_ts=from_ts)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except (HTTPError, URLError) as e:
        raise HTTPException(502, f"Last.fm no está disponible ahora mismo: {e}")

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
    repo: CancionesRepository = Depends(get_repository),
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
    repo: CancionesRepository = Depends(get_repository),
):
    stats = repo.get_top_artists(limit=limit, offset=offset, since=since, until=until)
    return [ArtistResponse(artist=s.artist, plays=s.play_count, songs=s.song_count) for s in stats]


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    since: datetime | None = None,
    until: datetime | None = None,
    repo: CancionesRepository = Depends(get_repository),
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


def _episode_response(episode: ObsessionEpisode) -> ObsessionResponse:
    return ObsessionResponse(
        id=episode.id,
        song_id=episode.song_id,
        title=episode.title,
        artist=episode.artist,
        album=episode.album,
        start=episode.start,
        end=episode.end,
        span_days=episode.span_days,
        strong_days=episode.strong_days,
        active_days=episode.active_days,
        plays=episode.plays,
        peak_day=episode.peak_day,
        peak_plays=episode.peak_plays,
        tier=episode.tier,
        score=episode.score,
        days=[
            ObsessionDayResponse(date=day, plays=plays)
            for day, plays in episode.days
        ],
    )


def _recap_response(recap: Recap, genres: list[dict]) -> RecapResponse:
    def song(item) -> RecapSongResponse:
        return RecapSongResponse(
            song_id=item.song_id,
            title=item.title,
            artist=item.artist,
            album=item.album,
            plays=item.plays,
            minutes=item.minutes,
            share=item.share,
            days=item.days,
            longest_streak=item.longest_streak,
        )

    return RecapResponse(
        since=recap.since,
        until=recap.until,
        period_days=recap.period_days,
        total_plays=recap.total_plays,
        total_minutes=recap.total_minutes,
        total_hours=recap.total_hours,
        estimated_minutes=recap.estimated_minutes,
        estimated_hours=recap.estimated_hours,
        duration_coverage=recap.duration_coverage,
        unique_songs=recap.unique_songs,
        unique_artists=recap.unique_artists,
        unique_albums=recap.unique_albums,
        days_listened=recap.days_listened,
        longest_streak=recap.longest_streak,
        top_day=recap.top_day,
        top_day_plays=recap.top_day_plays,
        top_hour=recap.top_hour,
        top_hour_plays=recap.top_hour_plays,
        first_play=recap.first_play,
        first_song=recap.first_song,
        first_song_id=recap.first_song_id,
        last_play=recap.last_play,
        last_song=recap.last_song,
        last_song_id=recap.last_song_id,
        top_song=song(recap.top_song) if recap.top_song else None,
        top_song_days=recap.top_song_days,
        top_song_longest_streak=recap.top_song_longest_streak,
        top_songs=[song(item) for item in recap.top_songs],
        top_artists=[
            RecapArtistResponse(
                artist=item.artist,
                plays=item.plays,
                minutes=item.minutes,
                share=item.share,
                songs=item.songs,
                top_song=item.top_song,
                top_song_id=item.top_song_id,
            )
            for item in recap.top_artists
        ],
        top_albums=[
            RecapAlbumResponse(
                album=item.album,
                artist=item.artist,
                plays=item.plays,
                minutes=item.minutes,
                top_song=item.top_song,
                top_song_id=item.top_song_id,
            )
            for item in recap.top_albums
        ],
        top_genres=[RecapGenreResponse(**genre) for genre in genres],
        monthly_top_artists=[
            RecapMonthlyArtistResponse(
                month=item.month,
                artist=item.artist,
                plays=item.plays,
            )
            for item in recap.monthly_top_artists
        ],
        top_obsession=(
            _episode_response(recap.top_obsession) if recap.top_obsession else None
        ),
        profile=RecapProfileResponse(
            key=recap.profile.key,
            label=recap.profile.label,
            description=recap.profile.description,
        ),
    )


@router.get("/artwork", response_model=ArtworkResponse)
def get_artwork(
    artist: str = Query(..., min_length=1),
    title: str = Query(""),
):
    """Carátula de una canción, resuelta en el servidor y cacheada."""
    return ArtworkResponse(url=find_cover(artist, title))


@router.get("/recap", response_model=RecapResponse)
def get_recap(
    since: datetime | None = None,
    until: datetime | None = None,
    repo: CancionesRepository = Depends(get_repository),
):
    records = repo.get_play_history(since=since, until=until)
    if not records:
        raise HTTPException(404, "No hay scrobbles en este periodo")

    recap = build_recap(
        records,
        settings.timezone,
        period_start=since.date() if since else None,
        period_end=until.date() if until else None,
    )
    genres = build_genres(
        [(artist.artist, artist.plays) for artist in recap.top_artists]
    )
    return _recap_response(recap, genres)


@router.get("/obsessions", response_model=list[ObsessionResponse])
def get_obsessions(
    since: datetime | None = None,
    until: datetime | None = None,
    tier: Literal["all", "obsesion", "racha"] = "all",
    limit: int = Query(50, ge=1, le=200),
    repo: CancionesRepository = Depends(get_repository),
):
    records = repo.get_play_history(since=since, until=until)
    episodes = detect_obsessions(records, settings.timezone)
    if tier != "all":
        episodes = [episode for episode in episodes if episode.tier == tier]
    return [_episode_response(episode) for episode in episodes[:limit]]


@router.get("/songs/{song_id}/timeline", response_model=SongTimelineResponse)
def get_song_timeline(
    song_id: int,
    since: datetime | None = None,
    until: datetime | None = None,
    repo: CancionesRepository = Depends(get_repository),
):
    song = repo.get_song(song_id)
    if song is None:
        raise HTTPException(404, "Canción no encontrada")

    key = normalized_key(song.artist or "", song.title or "")
    records = [
        record
        for record in repo.get_play_history(since=since, until=until)
        if normalized_key(record.artist or "", record.title or "") == key
    ]

    tz = ZoneInfo(settings.timezone)
    daily: Counter[date] = Counter()
    for record in records:
        daily[local_date(record.played_at, tz)] += 1

    episodes = detect_obsessions(records, settings.timezone)
    ordered_days = sorted(daily)
    first_listen = min((record.played_at for record in records), default=None)
    last_listen = max((record.played_at for record in records), default=None)

    return SongTimelineResponse(
        song=SongResponse(
            id=song.id,
            title=song.title,
            artist=song.artist,
            album=song.album,
            plays=sum(daily.values()),
        ),
        days=[
            ObsessionDayResponse(date=day, plays=daily[day])
            for day in ordered_days
        ],
        episodes=[_episode_response(episode) for episode in episodes],
        first_listen=first_listen,
        last_listen=last_listen,
    )
