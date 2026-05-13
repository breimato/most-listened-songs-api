import isodate
from googleapiclient.discovery import build

from canciones.config import settings
from canciones.domain.models import PlatformSong


class YouTubeAPIEnricher:
    """Enriches PlatformSong records with metadata from YouTube Data API v3."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.youtube_api_key
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = build("youtube", "v3", developerKey=self.api_key)
        return self._service

    def enrich(self, songs: list[PlatformSong]) -> list[PlatformSong]:
        if not self.api_key:
            return songs

        # Process in batches of 50 (API max)
        for i in range(0, len(songs), 50):
            batch = songs[i : i + 50]
            video_ids = [s.platform_id for s in batch]

            response = (
                self.service.videos()
                .list(
                    part="snippet,contentDetails,statistics",
                    id=",".join(video_ids),
                )
                .execute()
            )

            video_map = {item["id"]: item for item in response.get("items", [])}

            for song in batch:
                item = video_map.get(song.platform_id)
                if not item:
                    continue

                snippet = item.get("snippet", {})
                content = item.get("contentDetails", {})

                song.artist = snippet.get("channelTitle", song.channel)
                song.category = snippet.get("categoryId", "")
                song.thumbnail_url = (
                    snippet.get("thumbnails", {})
                    .get("high", {})
                    .get("url", "")
                )

                duration_iso = content.get("duration", "")
                if duration_iso:
                    try:
                        song.duration_seconds = int(
                            isodate.parse_duration(duration_iso).total_seconds()
                        )
                    except Exception:
                        pass

                song.extra_metadata = {
                    "tags": snippet.get("tags", [])[:10],
                    "view_count": item.get("statistics", {}).get("viewCount"),
                    "like_count": item.get("statistics", {}).get("likeCount"),
                }

        return songs
