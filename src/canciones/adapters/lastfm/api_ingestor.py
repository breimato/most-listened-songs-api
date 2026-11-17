"""Last.fm API ingestor — polls user.getRecentTracks with cursor-based pagination."""

import calendar
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime

from canciones.config import settings
from canciones.domain.models import Song

_API_BASE = "https://ws.audioscrobbler.com/2.0/"
_PAGE_SIZE = 200
_PAGE_DELAY = 0.25  # seconds between pages to be polite with the API


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

    def _fetch_page(self, page: int, from_ts: int | None) -> dict:
        params = {
            "method": "user.getRecentTracks",
            "user": self._username,
            "api_key": self._api_key,
            "format": "json",
            "limit": str(_PAGE_SIZE),
            "page": str(page),
        }
        if from_ts is not None:
            params["from"] = str(from_ts)

        url = _API_BASE + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

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
