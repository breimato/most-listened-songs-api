from typing import Protocol

from canciones.domain.models import ListeningEvent, PlatformSong


class SourceIngestor(Protocol):
    def parse(self, file_path: str) -> list[tuple[PlatformSong, ListeningEvent]]:
        """Parse a platform export file and return (song, event) pairs."""
        ...
