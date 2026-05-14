from datetime import datetime

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
