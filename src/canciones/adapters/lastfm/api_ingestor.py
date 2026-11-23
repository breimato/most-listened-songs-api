"""Last.fm API ingestor — polls user.getRecentTracks with cursor-based pagination."""

import calendar
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from canciones.config import settings
from canciones.domain.models import NowPlayingTrack, Song

_API_BASE = "https://ws.audioscrobbler.com/2.0/"
_PAGE_SIZE = 200
_PAGE_DELAY = 0.25  # seconds between pages to be polite with the API


def _text(value) -> str:
    if isinstance(value, dict):
        value = value.get("#text", "")
    return str(value or "")


def _scrobbled_at(entry) -> datetime | None:
    date = entry.get("date", {})
    uts = date.get("uts") if isinstance(date, dict) else None
    if not uts:
        return None
    return datetime.fromtimestamp(int(uts), tz=timezone.utc)


class LastFMAPIIngestor:
    """Polls the Last.fm user.getRecentTracks endpoint incrementally using a cursor."""

    def __init__(self, api_key: str | None = None, username: str | None = None):
        self._api_key = api_key or settings.lastfm_api_key
        self._username = username or settings.lastfm_username

    def fetch_recent(self, from_ts: int | None = None) -> list[tuple[Song, datetime]]:
        """Fetch all scrobbles since ``from_ts`` (UTC unix timestamp).

        The caller passes the newest stored play (``MAX(plays.played_at)``), so
        the cursor lives in the database instead of a local file. Without a
        cursor the full history is fetched. Returns (Song, played_at) pairs.
        """
        if not self._api_key or not self._username:
            raise ValueError("LASTFM_API_KEY and LASTFM_USERNAME must be set in .env")

        return self._paginate(from_ts=from_ts)

    def fetch_now_playing(self) -> NowPlayingTrack | None:
        """Return the live track or the most recent scrobble."""
        if not self._api_key or not self._username:
            return None

        data = self._fetch_page(page=1, from_ts=None, limit=2)
        tracks = data.get("recenttracks", {}).get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]
        if not tracks:
            return None

        entry = tracks[0]
        title = _text(entry.get("name", ""))
        artist = _text(entry.get("artist", ""))
        album = _text(entry.get("album", ""))
        if not title or not artist:
            return None

        playing = (
            str(entry.get("@attr", {}).get("nowplaying", "")).lower() == "true"
        )
        return NowPlayingTrack(
            title=title,
            artist=artist,
            album=album,
            playing=playing,
            scrobbled_at=None if playing else _scrobbled_at(entry),
        )

    def _paginate(self, from_ts: int | None) -> list[tuple[Song, datetime]]:
        all_pairs: list[tuple[Song, datetime]] = []
        page = 1

        while True:
            data = self._fetch_page(page=page, from_ts=from_ts)
            tracks = data.get("recenttracks", {}).get("track", [])

            # API quirk: single-track response comes as dict, not list
            if isinstance(tracks, dict):
                tracks = [tracks]

            all_pairs.extend(self._parse_tracks(tracks))

            attr = data.get("recenttracks", {}).get("@attr", {})
            total_pages = int(attr.get("totalPages", 1))
            if page >= total_pages:
                break

            page += 1
            time.sleep(_PAGE_DELAY)

        return all_pairs

    def _fetch_page(
        self, page: int, from_ts: int | None, limit: int = _PAGE_SIZE
    ) -> dict:
        params = {
            "method": "user.getRecentTracks",
            "user": self._username,
            "api_key": self._api_key,
            "format": "json",
            "limit": str(limit),
            "page": str(page),
        }
        if from_ts is not None:
            params["from"] = str(from_ts)

        url = _API_BASE + "?" + urllib.parse.urlencode(params)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except (urllib.error.HTTPError, urllib.error.URLError):
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)

    def _parse_tracks(self, tracks: list) -> list[tuple[Song, datetime]]:
        results = []
        for entry in tracks:
            # Skip "now playing" entries — they have no timestamp
            if entry.get("@attr", {}).get("nowplaying"):
                continue

            artist = entry.get("artist", "")
            if isinstance(artist, dict):
                artist = artist.get("#text", "")

            title = entry.get("name", "")

            album = entry.get("album", "")
            if isinstance(album, dict):
                album = album.get("#text", "")

            if not title or not artist:
                continue

            date = entry.get("date", {})
            uts = date.get("uts") if isinstance(date, dict) else None
            if not uts:
                continue

            played_at = datetime.utcfromtimestamp(int(uts))
            platform_id = f"{artist}|{title}".lower()

            song = Song(platform_id=platform_id, title=title, artist=artist, album=album)
            results.append((song, played_at))

        return results


def to_unix_timestamp(value: datetime) -> int:
    """Treat stored naive datetimes as UTC (Last.fm timestamps are UTC)."""
    if value.tzinfo is not None:
        return int(value.timestamp())
    return calendar.timegm(value.utctimetuple())
