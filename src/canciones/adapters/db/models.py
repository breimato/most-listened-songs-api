from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class CanonicalSongDB(Base):
    __tablename__ = "canonical_songs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    artist = Column(String(500), nullable=False, default="")
    album = Column(String(500), default="")
    musicbrainz_id = Column(String(36), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.now)

    platform_songs = relationship("PlatformSongDB", back_populates="canonical_song")

    __table_args__ = (Index("ix_canonical_artist", "artist"),)


class PlatformSongDB(Base):
    __tablename__ = "platform_songs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_song_id = Column(Integer, ForeignKey("canonical_songs.id"), nullable=True)
    platform = Column(String(20), nullable=False)
    platform_id = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    artist = Column(String(500), default="")
    channel = Column(String(500), default="")
    duration_seconds = Column(Integer, nullable=True)
    thumbnail_url = Column(Text, default="")
    category = Column(String(100), default="")
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now)

    canonical_song = relationship("CanonicalSongDB", back_populates="platform_songs")
    listening_events = relationship("ListeningEventDB", back_populates="platform_song")

    __table_args__ = (
        Index("ix_platform_song_lookup", "platform", "platform_id", unique=True),
        Index("ix_platform_song_canonical", "canonical_song_id"),
    )


class ListeningEventDB(Base):
    __tablename__ = "listening_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_song_id = Column(
        Integer, ForeignKey("platform_songs.id"), nullable=False
    )
    listened_at = Column(DateTime, nullable=False)
    platform = Column(String(20), nullable=False)

    platform_song = relationship("PlatformSongDB", back_populates="listening_events")

    __table_args__ = (
        Index("ix_event_song", "platform_song_id"),
        Index("ix_event_listened_at", "listened_at"),
        Index(
            "ix_event_dedup", "platform_song_id", "listened_at", unique=True
        ),
    )


class ImportLogDB(Base):
    __tablename__ = "import_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    platform = Column(String(20), nullable=False)
    events_imported = Column(Integer, default=0)
    imported_at = Column(DateTime, default=datetime.now)


class ManualLinkDB(Base):
    __tablename__ = "manual_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_song_id = Column(
        Integer, ForeignKey("platform_songs.id"), nullable=False
    )
    canonical_song_id = Column(
        Integer, ForeignKey("canonical_songs.id"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.now)
