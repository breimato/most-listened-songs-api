from collections import Counter
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from canciones.adapters.db.models import PlayDB, SongDB
from canciones.domain.models import ArtistStats, GeneralStats, Play, Song, SongStats


def _to_song(db: SongDB) -> Song:
    return Song(id=db.id, platform_id=db.platform_id, title=db.title, artist=db.artist, album=db.album)


class SQLiteRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_song_by_platform_id(self, platform_id: str) -> Song | None:
        db = self.session.query(SongDB).filter_by(platform_id=platform_id).first()
        return _to_song(db) if db else None

    def save_song(self, song: Song) -> Song:
        db = SongDB(platform_id=song.platform_id, title=song.title, artist=song.artist, album=song.album)
        self.session.add(db)
        self.session.flush()
        song.id = db.id
        return song

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

        rows = (
            query.group_by(SongDB.id)
            .order_by(func.count(PlayDB.id).desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [
            SongStats(song_id=r.id, title=r.title, artist=r.artist, album=r.album, play_count=r.play_count)
            for r in rows
        ]

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

        song_q = self.session.query(SongDB.id).join(PlayDB, PlayDB.song_id == SongDB.id)
        if since:
            song_q = song_q.filter(PlayDB.played_at >= since)
        if until:
            song_q = song_q.filter(PlayDB.played_at <= until)
        total_songs = song_q.distinct().count()

        artist_q = self.session.query(SongDB.artist).join(PlayDB, PlayDB.song_id == SongDB.id)
        if since:
            artist_q = artist_q.filter(PlayDB.played_at >= since)
        if until:
            artist_q = artist_q.filter(PlayDB.played_at <= until)
        total_artists = artist_q.distinct().count()

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
