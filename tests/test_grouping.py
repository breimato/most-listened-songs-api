from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from canciones.adapters.db.models import Base, PlayDB, SongDB
from canciones.adapters.db.repository import SQLiteRepository


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def _add_song_with_plays(session, platform_id, title, artist, album, play_count):
    song = SongDB(platform_id=platform_id, title=title, artist=artist, album=album)
    session.add(song)
    session.flush()
    for i in range(play_count):
        session.add(PlayDB(song_id=song.id, played_at=datetime(2024, 1, 1, 0, i % 60)))
    session.flush()
    return song


def test_versions_merge_into_one_top_entry(session):
    _add_song_with_plays(session, "joe|closer", "Closer", "Joe Inoue", "Closer", 10)
    _add_song_with_plays(session, "joe|closer remix", "Closer (Remix)", "Joe Inoue", "Single", 5)
    _add_song_with_plays(session, "joe|closer rem", "Closer - Remastered", "Joe Inoue", "Deluxe", 3)

    repo = SQLiteRepository(session)
    top = repo.get_top_songs(limit=10)

    assert len(top) == 1
    entry = top[0]
    assert entry.play_count == 18
    # Representative is the variant with most plays.
    assert entry.title == "Closer"


def test_distinct_songs_stay_separate(session):
    _add_song_with_plays(session, "a|one", "Song One", "Artist", "", 4)
    _add_song_with_plays(session, "a|two", "Song Two", "Artist", "", 2)

    repo = SQLiteRepository(session)
    top = repo.get_top_songs(limit=10)

    assert len(top) == 2
    assert top[0].title == "Song One"
    assert top[0].play_count == 4


def test_stats_count_normalized_songs(session):
    _add_song_with_plays(session, "joe|closer", "Closer", "Joe Inoue", "Closer", 2)
    _add_song_with_plays(session, "joe|closer remix", "Closer (Remix)", "Joe Inoue", "Single", 1)

    repo = SQLiteRepository(session)
    stats = repo.get_stats()

    assert stats.total_plays == 3
    assert stats.total_songs == 1
    assert stats.total_artists == 1
