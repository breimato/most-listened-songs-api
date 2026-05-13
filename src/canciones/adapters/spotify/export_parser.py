import json
from datetime import datetime
from pathlib import Path

from canciones.domain.models import ListeningEvent, Platform, PlatformSong


class SpotifyExportParser:
    """Parses Spotify extended streaming history JSON export."""

    def parse(self, file_path: str) -> list[tuple[PlatformSong, ListeningEvent]]:
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        results = []

        for entry in data:
            track_uri = entry.get("spotify_track_uri") or entry.get("trackUri", "")
            if not track_uri:
                # Skip podcasts and non-track entries
                continue

            # Extract track ID from URI (spotify:track:XXXX)
            track_id = track_uri.split(":")[-1] if ":" in track_uri else track_uri

            title = entry.get("master_metadata_track_name") or entry.get("trackName", "")
            artist = entry.get("master_metadata_album_artist_name") or entry.get("artistName", "")
            album = entry.get("master_metadata_album_album_name") or entry.get("albumName", "")

            if not title:
                continue

            ms_played = entry.get("ms_played", 0)
            # Skip very short plays (less than 30 seconds)
            if ms_played < 30000:
                continue

            # Timestamp
            time_str = entry.get("ts") or entry.get("endTime", "")
            try:
                listened_at = datetime.fromisoformat(
                    time_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                continue

            song = PlatformSong(
                platform=Platform.SPOTIFY,
                platform_id=track_id,
                title=title,
                artist=artist,
                channel=artist,
                duration_seconds=ms_played // 1000 if ms_played else None,
                extra_metadata={"album": album, "ms_played": ms_played},
            )
            event = ListeningEvent(
                listened_at=listened_at,
                platform=Platform.SPOTIFY,
            )
            results.append((song, event))

        return results
