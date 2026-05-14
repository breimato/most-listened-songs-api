"""Last.fm API ingestor — polls user.getRecentTracks with cursor-based pagination."""

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from canciones.config import settings
from canciones.domain.models import Song

_API_BASE = "https://ws.audioscrobbler.com/2.0/"
_CURSOR_FILE = "data/lastfm_cursor.json"
_PAGE_SIZE = 200
_PAGE_DELAY = 0.25  # seconds between pages to be polite with the API


class LastFMAPIIngestor:
    """Polls the Last.fm user.getRecentTracks endpoint incrementally using a cursor."""

    def __init__(self, api_key: str | None = None, username: str | None = None):
        self._api_key = api_key or settings.lastfm_api_key
        self._username = username or settings.lastfm_username

    def fetch_recent(self) -> list[tuple[Song, datetime]]:
        """Fetch all scrobbles since the last cursor timestamp.

        First run: imports full history. Subsequent runs: only new scrobbles.
        Returns a list of (Song, played_at) pairs.
        """
        if not self._api_key or not self._username:
            raise ValueError("LASTFM_API_KEY and LASTFM_USERNAME must be set in .env")

        from_ts = self._load_cursor()
        pairs = self._paginate(from_ts=from_ts)

        if pairs:
            latest_ts = max(int(played_at.timestamp()) for _, played_at in pairs)
            self._save_cursor(latest_ts + 1)

        return pairs

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

    def _load_cursor(self) -> int | None:
        path = Path(_CURSOR_FILE)
        if path.exists():
            try:
                return json.loads(path.read_text()).get("from_ts")
            except (json.JSONDecodeError, KeyError):
                pass
        return None

    def _save_cursor(self, from_ts: int) -> None:
        path = Path(_CURSOR_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"from_ts": from_ts}))
