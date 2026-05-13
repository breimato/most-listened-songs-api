import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from canciones.adapters.db.models import Base
from canciones.adapters.db.session import get_session
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
    data = r.json()
    assert data["total_plays"] == 0


def test_ingest_youtube_json(client):
    # Create a fake Takeout JSON
    takeout_data = [
        {
            "header": "YouTube",
            "title": "Watched Test Song",
            "titleUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "subtitles": [{"name": "Rick Astley"}],
            "time": "2024-01-15T10:30:00Z",
        },
        {
            "header": "YouTube",
            "title": "Watched Another Song",
            "titleUrl": "https://www.youtube.com/watch?v=abc123def45",
            "subtitles": [{"name": "Some Artist"}],
            "time": "2024-01-15T11:00:00Z",
        },
        {
            "header": "YouTube",
            "title": "Watched Test Song",
            "titleUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "subtitles": [{"name": "Rick Astley"}],
            "time": "2024-01-16T10:30:00Z",
        },
    ]

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(takeout_data, f)
        tmp_path = f.name

    try:
        # Ingest
        r = client.post(
            "/api/v1/ingest/youtube", json={"file_path": tmp_path}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["events_imported"] == 3
        assert data["songs_new"] == 2

        # Re-ingest same file (should be deduplicated by hash)
        r = client.post(
            "/api/v1/ingest/youtube", json={"file_path": tmp_path}
        )
        data = r.json()
        assert data["events_imported"] == 0
        assert "already imported" in data["message"]

        # Check top songs
        r = client.get("/api/v1/songs/top")
        assert r.status_code == 200
        songs = r.json()
        assert len(songs) == 2
        assert songs[0]["play_count"] == 2  # Test Song played twice
        assert songs[0]["title"] == "Test Song"

        # Check stats
        r = client.get("/api/v1/stats")
        data = r.json()
        assert data["total_plays"] == 3
        assert data["total_songs"] == 2

        # Check top artists
        r = client.get("/api/v1/artists/top")
        artists = r.json()
        assert len(artists) == 2
        assert artists[0]["artist"] == "Rick Astley"

        # Check platforms
        r = client.get("/api/v1/platforms")
        platforms = r.json()
        assert len(platforms) == 1
        assert platforms[0]["platform"] == "youtube"

    finally:
        Path(tmp_path).unlink()


def test_ingest_file_not_found(client):
    r = client.post(
        "/api/v1/ingest/youtube", json={"file_path": "/nonexistent.json"}
    )
    assert r.status_code == 404
