import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from rapidfuzz import fuzz

from canciones.domain.models import CanonicalSong, Platform, PlatformSong


# Patterns to strip from titles for matching
_NOISE_PATTERNS = [
    r"\(Official\s*(Music\s*)?Video\)",
    r"\(Official\s*Audio\)",
    r"\(Lyric(s)?\s*Video\)",
    r"\(Lyrics?\)",
    r"\(Visualizer\)",
    r"\(Audio\)",
    r"\(Live\)",
    r"\[Official\s*(Music\s*)?Video\]",
    r"\[Official\s*Audio\]",
    r"\[Lyrics?\]",
    r"ft\.\s*",
    r"feat\.\s*",
    r"\bVEVO\b",
    r"\bHD\b",
    r"\b4K\b",
    r"\bMV\b",
]
_NOISE_RE = re.compile("|".join(_NOISE_PATTERNS), re.IGNORECASE)


def normalize_title(title: str) -> str:
    cleaned = _NOISE_RE.sub("", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"[^\w\s]", "", cleaned).lower()
    return cleaned


class SongMatchingService:
    def __init__(self, threshold: int = 85):
        self.threshold = threshold

    def find_match(
        self, song: PlatformSong, candidates: list[CanonicalSong]
    ) -> CanonicalSong | None:
        norm_title = normalize_title(song.title)
        norm_artist = normalize_title(song.artist or song.channel)

        best_score = 0
        best_match = None

        for candidate in candidates:
            title_score = fuzz.token_sort_ratio(
                norm_title, normalize_title(candidate.title)
            )
            artist_score = fuzz.token_sort_ratio(
                norm_artist, normalize_title(candidate.artist)
            )
            combined = title_score * 0.7 + artist_score * 0.3

            if combined > best_score and combined >= self.threshold:
                best_score = combined
                best_match = candidate

        return best_match

    def create_canonical_from_platform(self, song: PlatformSong) -> CanonicalSong:
        return CanonicalSong(
            title=song.title,
            artist=song.artist or song.channel,
        )


@dataclass
class SongStats:
    platform_song_id: int
    title: str
    artist: str
    channel: str
    platform: Platform
    platform_id: str
    play_count: int
    canonical_song_id: int | None = None
    thumbnail_url: str = ""
    duration_seconds: int | None = None


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
    plays_by_platform: dict[str, int]
    plays_by_month: dict[str, int]
    plays_by_hour: dict[int, int]
    top_day: str
    first_listen: datetime | None
    last_listen: datetime | None
