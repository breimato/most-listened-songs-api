from typing import Protocol

from canciones.domain.models import PlatformSong


class MetadataEnricher(Protocol):
    def enrich(self, songs: list[PlatformSong]) -> list[PlatformSong]:
        """Enrich songs with metadata from platform API. Returns updated songs."""
        ...
