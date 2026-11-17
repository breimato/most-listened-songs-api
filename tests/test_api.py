from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from canciones.adapters.db.models import Base, PlayDB, SongDB
from canciones.adapters.db.session import get_session
from canciones.config import settings
from canciones.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _add_song(session, platform_id, title, artist, album=""):
    song = SongDB(platform_id=platform_id, title=title, artist=artist, album=album)
    session.add(song)
    session.flush()
    return song


def _add_play(session, song, played_at):
    session.add(PlayDB(song_id=song.id, played_at=played_at))
    session.flush()


@pytest.fixture()
def seeded(db_session):
    ghost = _add_song(db_session, "justin bieber|ghost", "Ghost", "Justin Bieber", "Justice")
    closer = _add_song(db_session, "joe inoue|closer", "Closer", "Joe Inoue", "Closer")
    remix = _add_song(db_session, "joe inoue|closer remix", "Closer (Remix)", "Joe Inoue", "Single")

    _add_play(db_session, ghost, datetime(2024, 1, 10, 20, 0))
    _add_play(db_session, ghost, datetime(2024, 2, 11, 21, 30))
    _add_play(db_session, closer, datetime(2025, 3, 1, 10, 0))
    _add_play(db_session, closer, datetime(2025, 3, 1, 10, 5))
    _add_play(db_session, remix, datetime(2025, 3, 2, 11, 0))
    db_session.commit()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_top_songs_empty(client):
    r = client.get("/api/v1/songs/top")
    assert r.status_code == 200
    assert r.json() == []


def test_stats_empty(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    assert r.json()["total_plays"] == 0


def test_top_songs_are_grouped_by_normalized_title(client, seeded):
    r = client.get("/api/v1/songs/top")
    assert r.status_code == 200
    songs = r.json()
    assert len(songs) == 2
    # Both "Closer" variants merge into one entry with 3 plays.
    assert songs[0]["title"] == "Closer"
    assert songs[0]["plays"] == 3
    assert songs[1]["title"] == "Ghost"
    assert songs[1]["plays"] == 2


def test_top_songs_artist_filter(client, seeded):
    r = client.get("/api/v1/songs/top", params={"artist": "justin"})
    assert r.status_code == 200
    songs = r.json()
    assert len(songs) == 1
    assert songs[0]["artist"] == "Justin Bieber"


def test_top_songs_year_filter(client, seeded):
    r = client.get("/api/v1/songs/top", params={"year": 2025})
    assert r.status_code == 200
    songs = r.json()
    assert len(songs) == 1
    assert songs[0]["title"] == "Closer"
    assert songs[0]["plays"] == 3


def test_top_artists(client, seeded):
    r = client.get("/api/v1/artists/top")
    assert r.status_code == 200
    artists = r.json()
    assert {a["artist"] for a in artists} == {"Justin Bieber", "Joe Inoue"}
    joe = next(a for a in artists if a["artist"] == "Joe Inoue")
    # Two song variants, but only one normalized song.
    assert joe["songs"] == 2
    assert joe["plays"] == 3


def test_stats(client, seeded):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_plays"] == 5
    assert data["total_songs"] == 2
    assert data["total_artists"] == 2
    assert data["plays_by_month"]["2024-01"] == 1
    assert data["plays_by_month"]["2025-03"] == 3
    assert data["top_day"] == "2025-03-01"
    assert data["first_listen"].startswith("2024-01-10")
    assert data["last_listen"].startswith("2025-03-02")


def test_sync_without_lastfm_credentials(client):
    r = client.post("/api/v1/sync")
    assert r.status_code == 400
    assert "LASTFM" in r.json()["detail"]


def test_access_key_protects_api(client, monkeypatch):
    monkeypatch.setattr(settings, "access_key", "s3cret")

    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/stats").status_code == 401
    assert (
        client.get("/api/v1/stats", headers={"Authorization": "Bearer nope"}).status_code
        == 401
    )
    assert (
        client.get(
            "/api/v1/stats", headers={"Authorization": "Bearer s3cret"}
        ).status_code
        == 200
    )
    assert (
        client.get("/api/v1/stats", headers={"X-Api-Key": "s3cret"}).status_code == 200
    )

    preflight = client.options(
        "/api/v1/stats",
        headers={
            "Origin": "https://breimato.es",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "https://breimato.es"
