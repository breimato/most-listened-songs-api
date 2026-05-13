from datetime import datetime

from pydantic import BaseModel, Field


class SongResponse(BaseModel):
    platform_song_id: int
    title: str
    artist: str
    channel: str
    platform: str
    platform_id: str
    play_count: int
    canonical_song_id: int | None = None
    thumbnail_url: str = ""
    duration_seconds: int | None = None


class ArtistResponse(BaseModel):
    artist: str
    play_count: int
    song_count: int


class StatsResponse(BaseModel):
    total_plays: int
    total_songs: int
    total_artists: int
    plays_by_platform: dict[str, int]
    plays_by_month: dict[str, int]
    plays_by_hour: dict[int, int]
    top_day: str
    first_listen: datetime | None
    last_listen: datetime | None


class PlatformSummary(BaseModel):
    platform: str
    songs: int
    plays: int


class ListeningEventResponse(BaseModel):
    id: int
    platform_song_id: int
    listened_at: datetime
    platform: str


class IngestRequest(BaseModel):
    file_path: str = Field(description="Path to the export file")


class IngestResponse(BaseModel):
    events_imported: int
    events_skipped: int
    songs_new: int
    message: str


class EnrichResponse(BaseModel):
    songs_enriched: int
    message: str


class LinkRequest(BaseModel):
    platform_song_id: int
    canonical_song_id: int


class MergeRequest(BaseModel):
    keep_id: int
    merge_id: int


class PlatformSongResponse(BaseModel):
    id: int
    platform: str
    platform_id: str
    title: str
    artist: str
    channel: str
    canonical_song_id: int | None = None
    duration_seconds: int | None = None
    thumbnail_url: str = ""


class CanonicalSongResponse(BaseModel):
    id: int
    title: str
    artist: str
    album: str
    musicbrainz_id: str | None = None
    platform_songs: list[PlatformSongResponse] = []
