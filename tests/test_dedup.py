from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from canciones.adapters.db.models import Base, PlayDB, SongDB
from canciones.adapters.db.repository import CancionesRepository
from canciones.domain.dedup import SongCatalog, duplicate_groups
from canciones.domain.models import Song
from canciones.domain.normalization import songs_match


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = Session()
    try:
        yield db
    finally:
        db.close()


def _add_song(
    session,
    platform_id,
    title,
    artist,
    play_count,
    album="",
    duration=0,
):
    song = SongDB(
        platform_id=platform_id,
        title=title,
        artist=artist,
        album=album,
        duration_seconds=duration,
    )
    session.add(song)
    session.flush()
    for index in range(play_count):
        session.add(
            PlayDB(
                song_id=song.id,
                played_at=datetime(2024, 1, 1)
                + timedelta(minutes=song.id * 100 + index),
            )
        )
    session.flush()
    return song


def test_closer_variants_are_one_group():
    songs = [
        Song(id=1, title="Closer", artist="Joe Inoue"),
        Song(id=2, title="CLOSER　-NARUTO オープニング ver.-", artist="Joe Inoue"),
        Song(
            id=3,
            title="CLOSER　-NARUTO オープニング ver.- - Closer (Naruto Opening Ver.)",
            artist="Joe Inoue",
        ),
        Song(id=4, title="Closer", artist="Joe Inoue Official English"),
        Song(id=5, title="Closer to the Edge", artist="Joe Inoue"),
    ]

    groups = duplicate_groups(songs)

    assert len(groups) == 1
    assert {song.id for song in groups[0]} == {1, 2, 3, 4}


def test_different_recordings_with_same_title_stay_apart():
    songs = [
        Song(id=1, title="Royalty (con Neoni)", artist="EGZOD"),
        Song(id=2, title="Royalty (con EKE)", artist="EGZOD"),
        Song(id=3, title="Royalty", artist="EGZOD"),
        Song(id=4, title="Ending 2 (Castellano) 4K", artist="One Piece"),
        Song(id=5, title="Opening 2 (Castellano) 4K", artist="One Piece"),
        Song(
            id=6,
            title="Quevedo: Bzrp Music Sessions, Vol. 52/66",
            artist="Bizarrap",
        ),
        Song(
            id=7,
            title="Daddy Yankee: Bzrp Music Sessions, Vol. 0/66",
            artist="Bizarrap",
        ),
    ]

    groups = duplicate_groups(songs)
    grouped = {song.id for group in groups for song in group}

    # "Royalty" without a credit may join one of the two, never both.
    assert not ({1, 2} <= grouped)
    assert 4 not in grouped or 5 not in grouped
    assert not ({6, 7} <= grouped)


def test_songs_match_allows_feature_vs_solo():
    assert songs_match(
        "Hellberg",
        "The Girl (feat. Cozi Zuehlsdorff)",
        "Hellberg",
        "The Girl",
    )
    assert not songs_match(
        "EGZOD",
        "Royalty (con Neoni)",
        "EGZOD",
        "Royalty (con EKE)",
    )


def test_songs_match_ignores_romanization_spacing():
    assert songs_match(
        "NICO Touches the Walls",
        "Niwakaamenimomakezu (Album Mix)",
        "NICO Touches the Walls",
        "Niwaka Ame Nimo Makezu",
    )
    assert songs_match(
        "NICO Touches the Walls",
        "ニワカ雨ニモ負ケズ - Niwaka Ame Nimo Makezu",
        "NICO Touches the Walls",
        "Niwakaamenimomakezu (Album Mix)",
    )
    assert songs_match(
        "Ado",
        "私は最強 (ウタ from ONE PIECE FILM RED)",
        "Ado",
        "私は最強",
    )
    assert songs_match(
        "KANA-BOON",
        "シルエット-TV SIZE- - Silhouette TV Size",
        "KANA-BOON",
        "シルエット - Silhouette",
    )
    assert not songs_match(
        "Ado",
        "新時代 (ウタ from ONE PIECE FILM RED)",
        "Ado",
        "私は最強 (ウタ from ONE PIECE FILM RED)",
    )
    assert not songs_match(
        "One Piece",
        "Ending 2 (Castellano) 4K",
        "One Piece",
        "Opening 2 (Castellano) 4K",
    )


def test_catalog_resolves_platform_variants():
    catalog = SongCatalog(
        [Song(id=15, platform_id="joe inoue|closer", title="Closer", artist="Joe Inoue")]
    )

    match = catalog.find(
        Song(
            platform_id="joe inoue|closer -naruto opening ver.-",
            title="CLOSER -NARUTO OPENING VER.-",
            artist="Joe Inoue",
        )
    )
    assert match is not None
    assert match.id == 15

    other = catalog.find(
        Song(
            platform_id="joe inoue|closer to the edge",
            title="Closer to the Edge",
            artist="Joe Inoue",
        )
    )
    assert other is None


def test_merge_duplicates_moves_plays_and_keeps_best_row(session):
    _add_song(
        session,
        "joe inoue|closer",
        "Closer",
        "Joe Inoue",
        10,
        album="Closer",
        duration=208,
    )
    _add_song(
        session,
        "joe inoue|closer tv",
        "CLOSER -NARUTO オープニング ver.-",
        "Joe Inoue",
        2,
    )
    _add_song(
        session,
        "joe inoue official english|closer",
        "Closer",
        "Joe Inoue Official English",
        1,
    )
    _add_song(session, "joe inoue|farther", "Farther", "Joe Inoue", 5)
    session.commit()

    repo = CancionesRepository(session)
    result = repo.merge_duplicate_songs()
    session.commit()

    assert result.groups_merged == 1
    assert result.songs_removed == 2
    assert result.plays_moved == 3

    songs = session.query(SongDB).order_by(SongDB.id).all()
    assert len(songs) == 2
    closer = next(song for song in songs if song.title == "Closer")
    assert closer.artist == "Joe Inoue"
    assert closer.duration_seconds == 208
    assert (
        session.query(func.count(PlayDB.id))
        .filter(PlayDB.song_id == closer.id)
        .scalar()
        == 13
    )


def test_merge_dry_run_does_not_touch_rows(session):
    _add_song(session, "a|closer", "Closer", "Joe Inoue", 3)
    _add_song(session, "a|closer remix", "Closer (Remix)", "Joe Inoue", 1)
    session.commit()

    result = CancionesRepository(session).merge_duplicate_songs(dry_run=True)

    assert result.groups_merged == 1
    assert result.songs_removed == 1
    assert result.dry_run is True
    assert session.query(SongDB).count() == 2
    assert session.query(PlayDB).count() == 4


def test_import_attaches_variant_to_existing_song(session):
    existing = _add_song(
        session, "joe inoue|closer", "Closer", "Joe Inoue", 0, duration=208
    )
    session.commit()

    repo = CancionesRepository(session)
    imported, skipped = repo.import_scrobbles(
        [
            (
                Song(
                    platform_id="joe inoue|closer -naruto opening ver.-",
                    title="CLOSER -NARUTO オープニング ver.-",
                    artist="Joe Inoue",
                ),
                datetime(2024, 2, 2, 12, 0),
            ),
            (
                Song(
                    platform_id="joe inoue|closer to the edge",
                    title="Closer to the Edge",
                    artist="Joe Inoue",
                ),
                datetime(2024, 2, 2, 12, 5),
            ),
        ]
    )
    session.commit()

    assert (imported, skipped) == (2, 0)
    assert session.query(SongDB).count() == 2
    assert (
        session.query(func.count(PlayDB.id))
        .filter(PlayDB.song_id == existing.id)
        .scalar()
        == 1
    )


def test_import_skips_known_play(session):
    existing = _add_song(session, "x|song", "Song", "Artist", 0)
    played_at = datetime(2024, 3, 3, 10, 0)
    session.add(PlayDB(song_id=existing.id, played_at=played_at))
    session.commit()

    repo = CancionesRepository(session)
    imported, skipped = repo.import_scrobbles(
        [(
            Song(platform_id="x|song", title="Song", artist="Artist"),
            played_at,
        )]
    )

    assert (imported, skipped) == (0, 1)
