from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Song:
    id: int | None = None
    platform_id: str = ""  # "{artist}|{title}".lower()
    title: str = ""
    artist: str = ""
    album: str = ""


@dataclass
class Play:
    id: int | None = None
    song_id: int = 0
    played_at: datetime = field(default_factory=datetime.now)


@dataclass
class SongStats:
    song_id: int
    title: str
    artist: str
    album: str
    play_count: int


@dataclass
class ArtistStats:
    artist: str
    play_count: int
    song_count: int


@dataclass
class GeneralStats:
    total_plays: int
    total_songs: int
    total_artists: int
    plays_by_month: dict
    plays_by_hour: dict
    top_day: str
    first_listen: datetime | None
    last_listen: datetime | None
