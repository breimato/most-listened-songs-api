"""Group scrobbles that belong to the same song and resolve new variants."""

from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher

from canciones.domain.models import Song
from canciones.domain.normalization import (
    canonical_artist,
    canonical_title,
    feature_tokens,
    songs_match,
)


@dataclass
class MergeResult:
    groups_merged: int = 0
    songs_removed: int = 0
    plays_moved: int = 0
    dry_run: bool = False


def duplicate_groups(songs: list[Song]) -> list[list[Song]]:
    """Cluster songs that represent the same recording.

    Exact keys cover the vast majority of variants. A second pass within each
    canonical artist catches small differences that normalization cannot know
    about (for example romanization or a one-character typo). Feature credits
    are checked at cluster level: "Royalty (con Neoni)" and "Royalty (con EKE)"
    must not be joined through a third, feature-less "Royalty".
    """
    by_id = {song.id: song for song in songs if song.id is not None}
    if not by_id:
        return []

    parent = {song_id: song_id for song_id in by_id}
    cluster_features = {
        song_id: feature_tokens(song.artist, song.title)
        for song_id, song in by_id.items()
    }

    def find(song_id: int) -> int:
        root = song_id
        while parent[root] != root:
            root = parent[root]
        while parent[song_id] != root:
            parent[song_id], song_id = root, parent[song_id]
        return root

    def union(first_id: int, second_id: int) -> None:
        first_root = find(first_id)
        second_root = find(second_id)
        if first_root == second_root:
            return
        first_features = cluster_features[first_root]
        second_features = cluster_features[second_root]
        if (
            first_features
            and second_features
            and not (first_features & second_features)
        ):
            return
        parent[second_root] = first_root
        cluster_features[first_root] = first_features | second_features

    by_artist: dict[str, list[Song]] = defaultdict(list)
    for song in by_id.values():
        by_artist[canonical_artist(song.artist)].append(song)

    for bucket in by_artist.values():
        for index, first in enumerate(bucket):
            for second in bucket[index + 1 :]:
                if songs_match(
                    first.artist,
                    first.title,
                    second.artist,
                    second.title,
                ):
                    union(first.id, second.id)

    grouped: dict[int, list[Song]] = defaultdict(list)
    for song_id, song in by_id.items():
        grouped[find(song_id)].append(song)

    return [group for group in grouped.values() if len(group) > 1]


class SongCatalog:
    """In-memory index used while importing scrobbles."""

    def __init__(self, songs: list[Song]):
        self._by_platform: dict[str, Song] = {}
        self._by_artist: dict[str, list[Song]] = defaultdict(list)
        for song in songs:
            self.add(song)

    def add(self, song: Song) -> None:
        if song.platform_id:
            self._by_platform[song.platform_id] = song
        self._by_artist[canonical_artist(song.artist)].append(song)

    def find(self, song: Song) -> Song | None:
        exact = self._by_platform.get(song.platform_id)
        if exact is not None:
            return exact

        best: Song | None = None
        best_score = 0.0
        for candidate in self._by_artist.get(canonical_artist(song.artist), []):
            if not songs_match(
                song.artist,
                song.title,
                candidate.artist,
                candidate.title,
            ):
                continue

            first = canonical_title(song.artist, song.title)
            second = canonical_title(candidate.artist, candidate.title)
            score = (
                1.0
                if first == second
                else SequenceMatcher(None, first, second).ratio()
            )
            if score > best_score or (
                score == best_score
                and best is not None
                and (candidate.id or 0) < (best.id or 0)
            ):
                best = candidate
                best_score = score

        return best
