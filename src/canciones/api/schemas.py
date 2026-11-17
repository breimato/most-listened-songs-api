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
