import math
from collections import Counter
from datetime import datetime

from sqlalchemy import delete, func, update
from sqlalchemy.orm import Session

from canciones.adapters.db.models import PlayDB, SongDB
from canciones.domain.dedup import MergeResult, SongCatalog, duplicate_groups
from canciones.domain.models import ArtistStats, GeneralStats, Play, Song, SongStats
from canciones.domain.normalization import (
    feature_credit_count,
    feature_tokens,
    has_platform_noise,
    normalize_artist,
    normalized_key,
)
from canciones.domain.obsessions import PlayRecord


def _to_song(db: SongDB) -> Song:
    return Song(id=db.id, platform_id=db.platform_id, title=db.title, artist=db.artist, album=db.album)


class CancionesRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_song_by_platform_id(self, platform_id: str) -> Song | None:
        db = self.session.query(SongDB).filter_by(platform_id=platform_id).first()
        return _to_song(db) if db else None

    def get_song(self, song_id: int) -> Song | None:
        db = self.session.get(SongDB, song_id)
        return _to_song(db) if db else None

    def get_all_songs(self) -> list[Song]:
        dbs = self.session.query(SongDB).order_by(SongDB.id).all()
        return [_to_song(db) for db in dbs]

    def import_scrobbles(
        self, pairs: list[tuple[Song, datetime]]
    ) -> tuple[int, int]:
        """Store scrobbles, attaching title/artist variants to one song row."""
        catalog = SongCatalog(self.get_all_songs())
        imported = 0
        skipped = 0

        for song_data, played_at in pairs:
            existing = catalog.find(song_data)
            if existing is not None:
                song_id = existing.id
            else:
                saved = self.save_song(song_data)
                catalog.add(saved)
                song_id = saved.id

            if self.play_exists(song_id, played_at):
                skipped += 1
                continue

            self.save_play(Play(song_id=song_id, played_at=played_at))
            imported += 1

        return imported, skipped

    def merge_duplicate_songs(self, dry_run: bool = False) -> MergeResult:
        """Merge rows that represent the same recording.

        The oldest/most representative row keeps its id and metadata, plays from
        the other rows are moved to it, and the empty rows are deleted.
        """
        rows = (
            self.session.query(SongDB, func.count(PlayDB.id).label("plays"))
            .outerjoin(PlayDB, PlayDB.song_id == SongDB.id)
            .group_by(SongDB.id)
            .all()
        )
        songs = [_to_song(db) for db, _ in rows]
        play_counts = {db.id: count for db, count in rows}
        by_id = {db.id: db for db, _ in rows}
        groups = duplicate_groups(songs)

        if dry_run:
            plays_moved = 0
            for group in groups:
                representative = self._pick_representative(group, by_id, play_counts)
                plays_moved += sum(
                    play_counts[song.id]
                    for song in group
                    if song.id != representative.id
                )
            return MergeResult(
                groups_merged=len(groups),
                songs_removed=sum(len(group) - 1 for group in groups),
                plays_moved=plays_moved,
                dry_run=True,
            )

        result = MergeResult()
        for group in groups:
            candidates = [by_id[song.id] for song in group]
            representative = self._pick_representative(
                group, by_id, play_counts
            )
            self._fill_missing_metadata(representative, candidates, play_counts)

            representative_times = {
                row[0]
                for row in self.session.query(PlayDB.played_at)
                .filter(PlayDB.song_id == representative.id)
                .all()
            }

            for candidate in candidates:
                if candidate.id == representative.id:
                    continue

                candidate_times = [
                    row[0]
                    for row in self.session.query(PlayDB.played_at)
                    .filter(PlayDB.song_id == candidate.id)
                    .all()
                ]
                conflicts = [
                    played_at
                    for played_at in candidate_times
                    if played_at in representative_times
                ]
                if conflicts:
                    self.session.execute(
                        delete(PlayDB)
                        .where(
                            PlayDB.song_id == candidate.id,
                            PlayDB.played_at.in_(conflicts),
                        )
                        .execution_options(synchronize_session=False)
                    )

                moved = self.session.execute(
                    update(PlayDB)
                    .where(PlayDB.song_id == candidate.id)
                    .values(song_id=representative.id)
                    .execution_options(synchronize_session=False)
                ).rowcount
                if moved is None or moved < 0:
                    moved = len(candidate_times) - len(conflicts)

                representative_times.update(
                    played_at
                    for played_at in candidate_times
                    if played_at not in conflicts
                )
                self.session.execute(
                    delete(SongDB)
                    .where(SongDB.id == candidate.id)
                    .execution_options(synchronize_session=False)
                )

                result.plays_moved += moved
                result.songs_removed += 1

            result.groups_merged += 1

        if result.groups_merged:
            self.session.flush()
            self.session.expire_all()
        return result

    @staticmethod
    def _pick_representative(
        group: list[Song],
        by_id: dict[int, SongDB],
        play_counts: dict[int, int],
    ) -> SongDB:
        """Choose the row that best represents the merged song.

        Rows with less than 10% of the group's plays are ignored so a one-off
        lyric video does not become the display title. If the group contains
        feature credits, the representative must keep one: deleting every
        credited variant would lose the feature signature and allow a future
        conflicting recording ("Royalty (con EKE)") to be merged by mistake.
        """
        max_plays = max(play_counts[song.id] for song in group)
        threshold = max(1, math.ceil(max_plays * 0.1))
        candidates = [by_id[song.id] for song in group]
        credited = [
            song
            for song in candidates
            if feature_tokens(song.artist, song.title)
        ]
        if credited:
            eligible = credited
        else:
            eligible = [
                song for song in candidates if play_counts[song.id] >= threshold
            ]

        def score(song: SongDB):
            return (
                0 if has_platform_noise(song.title) else 1,
                0 if feature_credit_count(song.title) > 1 else 1,
                1 if (song.duration_seconds or 0) > 0 else 0,
                1 if (song.album or "").strip() else 0,
                play_counts[song.id],
                -song.id,
            )

        return max(eligible, key=score)

    @staticmethod
    def _fill_missing_metadata(
        representative: SongDB,
        candidates: list[SongDB],
        play_counts: dict[int, int],
    ) -> None:
        ordered = sorted(
            candidates, key=lambda song: play_counts[song.id], reverse=True
        )
        if not (representative.duration_seconds or 0):
            for candidate in ordered:
                if (candidate.duration_seconds or 0) > 0:
                    representative.duration_seconds = candidate.duration_seconds
                    break
        if not (representative.album or "").strip():
            for candidate in ordered:
                if (candidate.album or "").strip():
                    representative.album = candidate.album
                    break

    def get_missing_durations(self, limit: int = 500) -> list[tuple[int, str, str]]:
        rows = (
            self.session.query(SongDB.id, SongDB.title, SongDB.artist)
            .filter(SongDB.duration_seconds.is_(None))
            .order_by(SongDB.id)
            .limit(limit)
            .all()
        )
        return [(row.id, row.title, row.artist) for row in rows]

    def set_song_duration(self, song_id: int, seconds: int) -> None:
        db = self.session.get(SongDB, song_id)
        if db is not None:
            db.duration_seconds = seconds

    def get_play_history(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[PlayRecord]:
        query = self.session.query(
            SongDB.id,
            SongDB.title,
            SongDB.artist,
            SongDB.album,
            SongDB.duration_seconds,
            PlayDB.played_at,
        ).join(PlayDB, PlayDB.song_id == SongDB.id)

        if since is not None:
            query = query.filter(PlayDB.played_at >= since)
        if until is not None:
            query = query.filter(PlayDB.played_at <= until)

        return [
            PlayRecord(
                song_id=row.id,
                title=row.title,
                artist=row.artist,
                album=row.album,
                played_at=row.played_at,
                duration_seconds=row.duration_seconds,
            )
            for row in query.all()
        ]

    def save_song(self, song: Song) -> Song:
        db = SongDB(platform_id=song.platform_id, title=song.title, artist=song.artist, album=song.album)
        self.session.add(db)
        self.session.flush()
        song.id = db.id
        return song

    def get_last_played_at(self) -> datetime | None:
        """Newest stored play, used as the Last.fm sync cursor.

        Keeping the cursor in the database (instead of a local file) makes
        incremental syncs work across containers and replicas.
        """
        return self.session.query(func.max(PlayDB.played_at)).scalar()

    def play_exists(self, song_id: int, played_at: datetime) -> bool:
        return (
            self.session.query(PlayDB)
            .filter_by(song_id=song_id, played_at=played_at)
            .first() is not None
        )

    def save_play(self, play: Play) -> Play:
        db = PlayDB(song_id=play.song_id, played_at=play.played_at)
        self.session.add(db)
        self.session.flush()
        play.id = db.id
        return play

    def get_top_songs(
        self,
        limit: int = 50,
        offset: int = 0,
        artist: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[SongStats]:
        query = (
            self.session.query(
                SongDB.id,
                SongDB.title,
                SongDB.artist,
                SongDB.album,
                func.count(PlayDB.id).label("play_count"),
            )
            .join(PlayDB, PlayDB.song_id == SongDB.id)
        )
        if artist:
            query = query.filter(SongDB.artist.ilike(f"%{artist}%"))
        if since:
            query = query.filter(PlayDB.played_at >= since)
        if until:
            query = query.filter(PlayDB.played_at <= until)

        rows = query.group_by(SongDB.id).all()

        grouped = self._group_by_normalized(rows)
        grouped.sort(key=lambda s: s.play_count, reverse=True)
        return grouped[offset : offset + limit]

    @staticmethod
    def _group_by_normalized(rows) -> list[SongStats]:
        """Merge different versions of the same song into one entry.

        Rows are (id, title, artist, album, play_count). Songs sharing a
        normalized key are summed; the variant with the most plays is used as
        the display representative.
        """
        aggregated: dict[str, SongStats] = {}
        top_variant_plays: dict[str, int] = {}

        for r in rows:
            key = normalized_key(r.artist, r.title)
            existing = aggregated.get(key)
            if existing is None:
                aggregated[key] = SongStats(
                    song_id=r.id,
                    title=r.title,
                    artist=r.artist,
                    album=r.album,
                    play_count=r.play_count,
                )
                top_variant_plays[key] = r.play_count
                continue

            existing.play_count += r.play_count
            if r.play_count > top_variant_plays[key]:
                top_variant_plays[key] = r.play_count
                existing.song_id = r.id
                existing.title = r.title
                existing.artist = r.artist
                existing.album = r.album

        return list(aggregated.values())

    def get_top_artists(
        self,
        limit: int = 50,
        offset: int = 0,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[ArtistStats]:
        query = (
            self.session.query(
                SongDB.artist,
                func.count(PlayDB.id).label("play_count"),
                func.count(func.distinct(SongDB.id)).label("song_count"),
            )
            .join(PlayDB, PlayDB.song_id == SongDB.id)
        )
        if since:
            query = query.filter(PlayDB.played_at >= since)
        if until:
            query = query.filter(PlayDB.played_at <= until)

        rows = (
            query.group_by(SongDB.artist)
            .order_by(func.count(PlayDB.id).desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            ArtistStats(artist=r.artist or "Unknown", play_count=r.play_count, song_count=r.song_count)
            for r in rows
        ]

    def get_stats(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> GeneralStats:
        q = self.session.query(PlayDB)
        if since:
            q = q.filter(PlayDB.played_at >= since)
        if until:
            q = q.filter(PlayDB.played_at <= until)

        total_plays = q.count()

        song_q = (
            self.session.query(SongDB.artist, SongDB.title)
            .join(PlayDB, PlayDB.song_id == SongDB.id)
        )
        if since:
            song_q = song_q.filter(PlayDB.played_at >= since)
        if until:
            song_q = song_q.filter(PlayDB.played_at <= until)
        song_keys = set()
        artist_keys = set()
        for artist_name, title in song_q.distinct().all():
            song_keys.add(normalized_key(artist_name or "", title or ""))
            artist_keys.add(normalize_artist(artist_name or ""))
        total_songs = len(song_keys)
        total_artists = len(artist_keys)

        timestamps = q.with_entities(PlayDB.played_at).all()
        month_counter: Counter[str] = Counter()
        hour_counter: Counter[int] = Counter()
        day_counter: Counter[str] = Counter()
        for (ts,) in timestamps:
            if ts:
                month_counter[ts.strftime("%Y-%m")] += 1
                hour_counter[ts.hour] += 1
                day_counter[ts.strftime("%Y-%m-%d")] += 1

        first = q.order_by(PlayDB.played_at.asc()).first()
        last = q.order_by(PlayDB.played_at.desc()).first()

        return GeneralStats(
            total_plays=total_plays,
            total_songs=total_songs,
            total_artists=total_artists,
            plays_by_month=dict(month_counter.most_common()),
            plays_by_hour=dict(sorted(hour_counter.items())),
            top_day=day_counter.most_common(1)[0][0] if day_counter else "",
            first_listen=first.played_at if first else None,
            last_listen=last.played_at if last else None,
        )
