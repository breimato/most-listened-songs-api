from collections import Counter
from datetime import datetime

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from canciones.adapters.db.models import (
    CanonicalSongDB,
    ImportLogDB,
    ListeningEventDB,
    ManualLinkDB,
    PlatformSongDB,
)
from canciones.domain.models import (
    CanonicalSong,
    ImportLog,
    ListeningEvent,
    ManualLink,
    Platform,
    PlatformSong,
)
from canciones.domain.services import ArtistStats, GeneralStats, SongStats


def _to_platform_song(db: PlatformSongDB) -> PlatformSong:
    return PlatformSong(
        id=db.id,
        canonical_song_id=db.canonical_song_id,
        platform=Platform(db.platform),
        platform_id=db.platform_id,
        title=db.title,
        artist=db.artist,
        channel=db.channel,
        duration_seconds=db.duration_seconds,
        thumbnail_url=db.thumbnail_url or "",
        category=db.category or "",
        extra_metadata=db.extra_metadata or {},
        created_at=db.created_at,
    )


def _to_canonical(db: CanonicalSongDB) -> CanonicalSong:
    return CanonicalSong(
        id=db.id,
        title=db.title,
        artist=db.artist,
        album=db.album or "",
        musicbrainz_id=db.musicbrainz_id,
        created_at=db.created_at,
    )


class SQLiteRepository:
    def __init__(self, session: Session):
        self.session = session

    # -- Platform songs --

    def get_platform_song_by_platform_id(
        self, platform: Platform, platform_id: str
    ) -> PlatformSong | None:
        db = (
            self.session.query(PlatformSongDB)
            .filter_by(platform=platform.value, platform_id=platform_id)
            .first()
        )
        return _to_platform_song(db) if db else None

    def save_platform_song(self, song: PlatformSong) -> PlatformSong:
        db = PlatformSongDB(
            canonical_song_id=song.canonical_song_id,
            platform=song.platform.value,
            platform_id=song.platform_id,
            title=song.title,
            artist=song.artist,
            channel=song.channel,
            duration_seconds=song.duration_seconds,
            thumbnail_url=song.thumbnail_url,
            category=song.category,
            extra_metadata=song.extra_metadata,
        )
        self.session.add(db)
        self.session.flush()
        song.id = db.id
        return song

    def get_platform_songs_needing_enrichment(
        self, platform: Platform, limit: int = 50
    ) -> list[PlatformSong]:
        rows = (
            self.session.query(PlatformSongDB)
            .filter_by(platform=platform.value)
            .filter(PlatformSongDB.duration_seconds.is_(None))
            .limit(limit)
            .all()
        )
        return [_to_platform_song(r) for r in rows]

    def update_platform_song(self, song: PlatformSong) -> None:
        db = self.session.query(PlatformSongDB).get(song.id)
        if not db:
            return
        db.artist = song.artist
        db.duration_seconds = song.duration_seconds
        db.thumbnail_url = song.thumbnail_url
        db.category = song.category
        db.extra_metadata = song.extra_metadata
        self.session.flush()

    # -- Canonical songs --

    def get_all_canonical_songs(self) -> list[CanonicalSong]:
        rows = self.session.query(CanonicalSongDB).all()
        return [_to_canonical(r) for r in rows]

    def save_canonical_song(self, song: CanonicalSong) -> CanonicalSong:
        db = CanonicalSongDB(
            title=song.title,
            artist=song.artist,
            album=song.album,
            musicbrainz_id=song.musicbrainz_id,
        )
        self.session.add(db)
        self.session.flush()
        song.id = db.id
        return song

    def get_canonical_song(self, song_id: int) -> CanonicalSong | None:
        db = self.session.query(CanonicalSongDB).get(song_id)
        return _to_canonical(db) if db else None

    # -- Listening events --

    def save_listening_event(self, event: ListeningEvent) -> ListeningEvent:
        db = ListeningEventDB(
            platform_song_id=event.platform_song_id,
            listened_at=event.listened_at,
            platform=event.platform.value,
        )
        self.session.add(db)
        self.session.flush()
        event.id = db.id
        return event

    def event_exists(self, platform_song_id: int, listened_at: datetime) -> bool:
        return (
            self.session.query(ListeningEventDB)
            .filter_by(platform_song_id=platform_song_id, listened_at=listened_at)
            .first()
            is not None
        )

    def get_events_for_song(
        self, platform_song_id: int, limit: int = 100, offset: int = 0
    ) -> list[ListeningEvent]:
        rows = (
            self.session.query(ListeningEventDB)
            .filter_by(platform_song_id=platform_song_id)
            .order_by(ListeningEventDB.listened_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            ListeningEvent(
                id=r.id,
                platform_song_id=r.platform_song_id,
                listened_at=r.listened_at,
                platform=Platform(r.platform),
            )
            for r in rows
        ]

    # -- Import log --

    def get_import_by_hash(self, file_hash: str) -> ImportLog | None:
        db = (
            self.session.query(ImportLogDB).filter_by(file_hash=file_hash).first()
        )
        if not db:
            return None
        return ImportLog(
            id=db.id,
            filename=db.filename,
            file_hash=db.file_hash,
            platform=Platform(db.platform),
            events_imported=db.events_imported,
            imported_at=db.imported_at,
        )

    def save_import_log(self, log: ImportLog) -> ImportLog:
        db = ImportLogDB(
            filename=log.filename,
            file_hash=log.file_hash,
            platform=log.platform.value,
            events_imported=log.events_imported,
        )
        self.session.add(db)
        self.session.flush()
        log.id = db.id
        return log

    # -- Stats --

    def get_top_songs(
        self,
        limit: int = 50,
        offset: int = 0,
        platform: Platform | None = None,
        artist: str | None = None,
        min_plays: int = 1,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[SongStats]:
        query = (
            self.session.query(
                PlatformSongDB.id,
                PlatformSongDB.title,
                PlatformSongDB.artist,
                PlatformSongDB.channel,
                PlatformSongDB.platform,
                PlatformSongDB.platform_id,
                PlatformSongDB.canonical_song_id,
                PlatformSongDB.thumbnail_url,
                PlatformSongDB.duration_seconds,
                func.count(ListeningEventDB.id).label("play_count"),
            )
            .join(
                ListeningEventDB,
                ListeningEventDB.platform_song_id == PlatformSongDB.id,
            )
        )

        if platform:
            query = query.filter(PlatformSongDB.platform == platform.value)
        if artist:
            query = query.filter(
                (PlatformSongDB.artist.ilike(f"%{artist}%"))
                | (PlatformSongDB.channel.ilike(f"%{artist}%"))
            )
        if since:
            query = query.filter(ListeningEventDB.listened_at >= since)
        if until:
            query = query.filter(ListeningEventDB.listened_at <= until)

        query = (
            query.group_by(PlatformSongDB.id)
            .having(func.count(ListeningEventDB.id) >= min_plays)
            .order_by(func.count(ListeningEventDB.id).desc())
            .offset(offset)
            .limit(limit)
        )

        return [
            SongStats(
                platform_song_id=r.id,
                title=r.title,
                artist=r.artist,
                channel=r.channel,
                platform=Platform(r.platform),
                platform_id=r.platform_id,
                play_count=r.play_count,
                canonical_song_id=r.canonical_song_id,
                thumbnail_url=r.thumbnail_url or "",
                duration_seconds=r.duration_seconds,
            )
            for r in query.all()
        ]

    def get_top_artists(
        self,
        limit: int = 50,
        offset: int = 0,
        platform: Platform | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[ArtistStats]:
        # Use channel as artist fallback for YouTube
        artist_col = func.coalesce(
            func.nullif(PlatformSongDB.artist, ""), PlatformSongDB.channel
        )

        query = (
            self.session.query(
                artist_col.label("artist"),
                func.count(ListeningEventDB.id).label("play_count"),
                func.count(func.distinct(PlatformSongDB.id)).label("song_count"),
            )
            .join(
                ListeningEventDB,
                ListeningEventDB.platform_song_id == PlatformSongDB.id,
            )
        )

        if platform:
            query = query.filter(PlatformSongDB.platform == platform.value)
        if since:
            query = query.filter(ListeningEventDB.listened_at >= since)
        if until:
            query = query.filter(ListeningEventDB.listened_at <= until)

        query = (
            query.group_by(artist_col)
            .order_by(func.count(ListeningEventDB.id).desc())
            .offset(offset)
            .limit(limit)
        )

        return [
            ArtistStats(
                artist=r.artist or "Unknown",
                play_count=r.play_count,
                song_count=r.song_count,
            )
            for r in query.all()
        ]

    def get_general_stats(
        self,
        platform: Platform | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> GeneralStats:
        event_q = self.session.query(ListeningEventDB)
        if platform:
            event_q = event_q.filter_by(platform=platform.value)
        if since:
            event_q = event_q.filter(ListeningEventDB.listened_at >= since)
        if until:
            event_q = event_q.filter(ListeningEventDB.listened_at <= until)

        total_plays = event_q.count()

        # Distinct songs and artists
        song_q = (
            self.session.query(PlatformSongDB.id)
            .join(
                ListeningEventDB,
                ListeningEventDB.platform_song_id == PlatformSongDB.id,
            )
        )
        if platform:
            song_q = song_q.filter(PlatformSongDB.platform == platform.value)
        if since:
            song_q = song_q.filter(ListeningEventDB.listened_at >= since)
        if until:
            song_q = song_q.filter(ListeningEventDB.listened_at <= until)

        total_songs = song_q.distinct().count()

        artist_col = func.coalesce(
            func.nullif(PlatformSongDB.artist, ""), PlatformSongDB.channel
        )
        artist_q = (
            self.session.query(artist_col)
            .join(
                ListeningEventDB,
                ListeningEventDB.platform_song_id == PlatformSongDB.id,
            )
        )
        if platform:
            artist_q = artist_q.filter(PlatformSongDB.platform == platform.value)
        if since:
            artist_q = artist_q.filter(ListeningEventDB.listened_at >= since)
        if until:
            artist_q = artist_q.filter(ListeningEventDB.listened_at <= until)
        total_artists = artist_q.distinct().count()

        # Plays by platform
        plat_rows = (
            event_q.with_entities(
                ListeningEventDB.platform,
                func.count(ListeningEventDB.id),
            )
            .group_by(ListeningEventDB.platform)
            .all()
        )
        plays_by_platform = {r[0]: r[1] for r in plat_rows}

        # Plays by month and hour — fetch all timestamps
        events = event_q.with_entities(ListeningEventDB.listened_at).all()
        month_counter: Counter[str] = Counter()
        hour_counter: Counter[int] = Counter()
        day_counter: Counter[str] = Counter()
        for (ts,) in events:
            if ts:
                month_counter[ts.strftime("%Y-%m")] += 1
                hour_counter[ts.hour] += 1
                day_counter[ts.strftime("%Y-%m-%d")] += 1

        top_day = day_counter.most_common(1)[0][0] if day_counter else ""

        # First and last listen
        first = event_q.order_by(ListeningEventDB.listened_at.asc()).first()
        last = event_q.order_by(ListeningEventDB.listened_at.desc()).first()

        return GeneralStats(
            total_plays=total_plays,
            total_songs=total_songs,
            total_artists=total_artists,
            plays_by_platform=plays_by_platform,
            plays_by_month=dict(month_counter.most_common()),
            plays_by_hour=dict(sorted(hour_counter.items())),
            top_day=top_day,
            first_listen=first.listened_at if first else None,
            last_listen=last.listened_at if last else None,
        )

    def get_platform_summary(self) -> list[dict]:
        rows = (
            self.session.query(
                PlatformSongDB.platform,
                func.count(func.distinct(PlatformSongDB.id)).label("songs"),
                func.count(ListeningEventDB.id).label("plays"),
            )
            .join(
                ListeningEventDB,
                ListeningEventDB.platform_song_id == PlatformSongDB.id,
            )
            .group_by(PlatformSongDB.platform)
            .all()
        )
        return [
            {"platform": r.platform, "songs": r.songs, "plays": r.plays}
            for r in rows
        ]

    # -- Matching --

    def get_unmatched_songs(
        self, limit: int = 50, offset: int = 0
    ) -> list[PlatformSong]:
        rows = (
            self.session.query(PlatformSongDB)
            .filter(PlatformSongDB.canonical_song_id.is_(None))
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_to_platform_song(r) for r in rows]

    def link_song(self, platform_song_id: int, canonical_song_id: int) -> None:
        db = self.session.query(PlatformSongDB).get(platform_song_id)
        if db:
            db.canonical_song_id = canonical_song_id
            link = ManualLinkDB(
                platform_song_id=platform_song_id,
                canonical_song_id=canonical_song_id,
            )
            self.session.add(link)
            self.session.flush()

    def merge_canonical_songs(self, keep_id: int, merge_id: int) -> None:
        self.session.query(PlatformSongDB).filter_by(
            canonical_song_id=merge_id
        ).update({"canonical_song_id": keep_id})
        self.session.query(CanonicalSongDB).filter_by(id=merge_id).delete()
        self.session.flush()
