from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
    LASTFM = "lastfm"


@dataclass
class CanonicalSong:
    id: int | None = None
    title: str = ""
    artist: str = ""
    album: str = ""
    musicbrainz_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PlatformSong:
    id: int | None = None
    canonical_song_id: int | None = None
    platform: Platform = Platform.YOUTUBE
    platform_id: str = ""  # YouTube video ID or Spotify track URI
    title: str = ""
    artist: str = ""
    channel: str = ""
    duration_seconds: int | None = None
    thumbnail_url: str = ""
    category: str = ""
    extra_metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ListeningEvent:
    id: int | None = None
    platform_song_id: int = 0
    listened_at: datetime = field(default_factory=datetime.now)
    platform: Platform = Platform.YOUTUBE


@dataclass
class ImportLog:
    id: int | None = None
    filename: str = ""
    file_hash: str = ""
    platform: Platform = Platform.YOUTUBE
    events_imported: int = 0
    imported_at: datetime = field(default_factory=datetime.now)


@dataclass
class ManualLink:
    id: int | None = None
    platform_song_id: int = 0
    canonical_song_id: int = 0
    created_at: datetime = field(default_factory=datetime.now)
