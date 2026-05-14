from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class SongDB(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_id = Column(String(200), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    artist = Column(String(500), default="")
    album = Column(String(500), default="")

    plays = relationship("PlayDB", back_populates="song")

    __table_args__ = (Index("ix_song_artist", "artist"),)


class PlayDB(Base):
    __tablename__ = "plays"

    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    played_at = Column(DateTime, nullable=False)

    song = relationship("SongDB", back_populates="plays")

    __table_args__ = (
        Index("ix_play_dedup", "song_id", "played_at", unique=True),
        Index("ix_play_song", "song_id"),
        Index("ix_play_date", "played_at"),
    )
