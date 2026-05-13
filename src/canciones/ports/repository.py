from datetime import datetime
from typing import Protocol

from canciones.domain.models import (
    CanonicalSong,
    ImportLog,
    ListeningEvent,
    ManualLink,
    Platform,
    PlatformSong,
)
from canciones.domain.services import ArtistStats, GeneralStats, SongStats


class Repository(Protocol):
    # Platform songs
    def get_platform_song_by_platform_id(
        self, platform: Platform, platform_id: str
    ) -> PlatformSong | None: ...

    def save_platform_song(self, song: PlatformSong) -> PlatformSong: ...

    def get_platform_songs_needing_enrichment(
        self, platform: Platform, limit: int = 50
    ) -> list[PlatformSong]: ...

    def update_platform_song(self, song: PlatformSong) -> None: ...

    # Canonical songs
    def get_all_canonical_songs(self) -> list[CanonicalSong]: ...

    def save_canonical_song(self, song: CanonicalSong) -> CanonicalSong: ...

    def get_canonical_song(self, song_id: int) -> CanonicalSong | None: ...

    # Listening events
    def save_listening_event(self, event: ListeningEvent) -> ListeningEvent: ...

    def event_exists(
        self, platform_song_id: int, listened_at: datetime
    ) -> bool: ...

    def get_events_for_song(
        self, platform_song_id: int, limit: int = 100, offset: int = 0
    ) -> list[ListeningEvent]: ...

    # Import log
    def get_import_by_hash(self, file_hash: str) -> ImportLog | None: ...

    def save_import_log(self, log: ImportLog) -> ImportLog: ...

    # Stats
    def get_top_songs(
        self,
        limit: int = 50,
        offset: int = 0,
        platform: Platform | None = None,
        artist: str | None = None,
        min_plays: int = 1,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[SongStats]: ...

    def get_top_artists(
        self,
        limit: int = 50,
        offset: int = 0,
        platform: Platform | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[ArtistStats]: ...

    def get_general_stats(
        self,
        platform: Platform | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> GeneralStats: ...

    def get_platform_summary(self) -> list[dict]: ...

    # Matching / linking
    def get_unmatched_songs(
        self, limit: int = 50, offset: int = 0
    ) -> list[PlatformSong]: ...

    def link_song(self, platform_song_id: int, canonical_song_id: int) -> None: ...

    def merge_canonical_songs(self, keep_id: int, merge_id: int) -> None: ...
