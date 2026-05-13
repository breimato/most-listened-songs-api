import csv
import json
from datetime import datetime
from pathlib import Path

from canciones.domain.models import ListeningEvent, Platform, PlatformSong


class LastFMExportParser:
    """
    Parses Last.fm data exports.

    Supports two formats:
    - CSV export from last.fm/user/USERNAME/library (columns: uts, utc_time, artist, artist_mbid, album, album_mbid, track, track_mbid)
    - JSON export from some third-party tools
    """

    def parse(self, file_path: str) -> list[tuple[PlatformSong, ListeningEvent]]:
        path = Path(file_path)
        suffix = path.suffix.lower()
        content = path.read_text(encoding="utf-8")

        if suffix == ".json":
            return self._parse_json(content)
        return self._parse_csv(content)

    def _parse_csv(self, content: str) -> list[tuple[PlatformSong, ListeningEvent]]:
        results = []
        reader = csv.DictReader(content.splitlines())

        for row in reader:
            track = row.get("track", "").strip()
            artist = row.get("artist", "").strip()
            album = row.get("album", "").strip()

            if not track or not artist:
                continue

            # Timestamp: prefer unix timestamp, fallback to utc_time string
            listened_at = None
            uts = row.get("uts", "").strip()
            if uts and uts.isdigit():
                listened_at = datetime.utcfromtimestamp(int(uts))
            else:
                utc_time = row.get("utc_time", "").strip()
                for fmt in ("%d %b %Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d %b %Y, %H:%M"):
                    try:
                        listened_at = datetime.strptime(utc_time, fmt)
                        break
                    except ValueError:
                        continue

            if not listened_at:
                continue

            # Use "artist - track" as platform_id since Last.fm has no video ID
            platform_id = f"{artist}|{track}".lower()

            song = PlatformSong(
                platform=Platform.LASTFM,
                platform_id=platform_id,
                title=track,
                artist=artist,
                channel=artist,
                extra_metadata={"album": album, "mbid": row.get("track_mbid", "")},
            )
            event = ListeningEvent(
                listened_at=listened_at,
                platform=Platform.LASTFM,
            )
            results.append((song, event))

        return results

    def _parse_json(self, content: str) -> list[tuple[PlatformSong, ListeningEvent]]:
        data = json.loads(content)
        results = []

        # Support common JSON formats from Last.fm API / exports
        tracks = data if isinstance(data, list) else data.get("recenttracks", {}).get("track", [])

        for entry in tracks:
            artist = entry.get("artist", "")
            if isinstance(artist, dict):
                artist = artist.get("#text", artist.get("name", ""))
            track = entry.get("name", entry.get("track", ""))
            album = entry.get("album", "")
            if isinstance(album, dict):
                album = album.get("#text", "")

            if not track or not artist:
                continue

            # Skip currently playing (no timestamp)
            attr = entry.get("@attr", {})
            if attr.get("nowplaying"):
                continue

            date = entry.get("date", {})
            uts = date.get("uts") if isinstance(date, dict) else None
            listened_at = None
            if uts:
                listened_at = datetime.utcfromtimestamp(int(uts))
            if not listened_at:
                continue

            platform_id = f"{artist}|{track}".lower()
            song = PlatformSong(
                platform=Platform.LASTFM,
                platform_id=platform_id,
                title=track,
                artist=artist,
                channel=artist,
                extra_metadata={"album": album},
            )
            event = ListeningEvent(
                listened_at=listened_at,
                platform=Platform.LASTFM,
            )
            results.append((song, event))

        return results
