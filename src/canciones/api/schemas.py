from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class SongResponse(BaseModel):
    id: int
    title: str
    artist: str
    album: str
    plays: int


class ArtistResponse(BaseModel):
    artist: str
    plays: int
    songs: int


class StatsResponse(BaseModel):
    total_plays: int
    total_songs: int
    total_artists: int
    plays_by_month: dict[str, int]
    plays_by_hour: dict[int, int]
    top_day: str
    first_listen: datetime | None
    last_listen: datetime | None


class SyncResponse(BaseModel):
    imported: int
    skipped: int
    message: str


class ArtworkResponse(BaseModel):
    url: str | None


class NowPlayingTrackResponse(BaseModel):
    title: str
    artist: str
    album: str
    scrobbled_at: datetime | None


class NowPlayingResponse(BaseModel):
    playing: bool
    track: NowPlayingTrackResponse | None


class ObsessionDayResponse(BaseModel):
    date: date
    plays: int


class ObsessionResponse(BaseModel):
    id: str
    song_id: int
    title: str
    artist: str
    album: str
    start: date
    end: date
    span_days: int
    strong_days: int
    active_days: int
    plays: int
    peak_day: date
    peak_plays: int
    tier: Literal["obsesion", "racha"]
    score: int
    days: list[ObsessionDayResponse]


class SongTimelineResponse(BaseModel):
    song: SongResponse
    days: list[ObsessionDayResponse]
    episodes: list[ObsessionResponse]
    first_listen: datetime | None
    last_listen: datetime | None
    total_minutes: int
    duration_coverage: float


class DurationBackfillResponse(BaseModel):
    processed: int
    updated: int


class DedupeResponse(BaseModel):
    groups_merged: int
    songs_removed: int
    plays_moved: int
    dry_run: bool


class SleepSongResponse(BaseModel):
    song_id: int
    title: str
    artist: str
    album: str
    plays: int
    total_plays: int
    night_share: float
    minutes: int
    total_minutes: int
    estimated: bool
    score: float


class SleepResponse(BaseModel):
    window_start: int
    window_end: int
    total_plays: int
    night_plays: int
    night_share: float
    night_minutes: int
    duration_coverage: float
    estimated: bool
    nights: int
    top_hour: int | None
    top_artist: str | None
    songs: list[SleepSongResponse]


class RecapSongResponse(BaseModel):
    song_id: int
    title: str
    artist: str
    album: str
    plays: int
    minutes: int
    share: float
    days: int
    longest_streak: int


class RecapArtistResponse(BaseModel):
    artist: str
    plays: int
    minutes: int
    share: float
    songs: int
    top_song: str | None
    top_song_id: int | None


class RecapAlbumResponse(BaseModel):
    album: str
    artist: str
    plays: int
    minutes: int
    top_song: str
    top_song_id: int


class RecapGenreResponse(BaseModel):
    name: str
    weight: int
    share: float


class RecapMonthlyArtistResponse(BaseModel):
    month: str
    artist: str
    plays: int


class RecapProfileResponse(BaseModel):
    key: str
    label: str
    description: str


class RecapResponse(BaseModel):
    since: date
    until: date
    period_days: int
    total_plays: int
    total_minutes: int
    total_hours: float
    estimated_minutes: int
    estimated_hours: float
    duration_coverage: float
    unique_songs: int
    unique_artists: int
    unique_albums: int
    days_listened: int
    longest_streak: int
    top_day: date | None
    top_day_plays: int
    top_hour: int | None
    top_hour_plays: int
    first_play: datetime | None
    first_song: str | None
    first_song_id: int | None
    last_play: datetime | None
    last_song: str | None
    last_song_id: int | None
    top_song: RecapSongResponse | None
    top_song_days: int
    top_song_longest_streak: int
    top_songs: list[RecapSongResponse]
    top_artists: list[RecapArtistResponse]
    top_albums: list[RecapAlbumResponse]
    top_genres: list[RecapGenreResponse]
    monthly_top_artists: list[RecapMonthlyArtistResponse]
    top_obsession: ObsessionResponse | None
    profile: RecapProfileResponse
    sleep: SleepResponse
