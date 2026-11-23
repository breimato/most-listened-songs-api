from datetime import datetime, timezone
from urllib.error import URLError

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from canciones.adapters.db.models import Base, PlayDB, SongDB
from canciones.adapters.db.session import get_session
from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor
from canciones.config import settings
from canciones.domain.models import NowPlayingTrack
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


def test_sync_without_credentials_uses_neutral_copy(client):
    response = client.post("/api/v1/sync")

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "LASTFM" not in detail
    assert "Last.fm" not in detail
    assert "credenciales" in detail.lower()


def test_sync_message_is_brand_neutral(client, monkeypatch):
    from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

    monkeypatch.setattr(
        LastFMAPIIngestor,
        "fetch_recent",
        lambda self, from_ts=None: [],
    )

    response = client.post("/api/v1/sync")

    assert response.status_code == 200
    message = response.json()["message"]
    assert "Last.fm" not in message
    assert "reproducciones nuevas" in message


def test_sync_service_error_is_brand_neutral(client, monkeypatch):
    from urllib.error import URLError

    from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

    def fail(self, from_ts=None):
        raise URLError("boom")

    monkeypatch.setattr(LastFMAPIIngestor, "fetch_recent", fail)

    response = client.post("/api/v1/sync")

    assert response.status_code == 502
    assert "Last.fm" not in response.json()["detail"]


def test_recap_empty_period_uses_neutral_copy(client):
    response = client.get("/api/v1/recap")

    assert response.status_code == 404
    assert response.json()["detail"] == "No hay reproducciones en este periodo."


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


def test_obsessions_and_song_timeline(client, db_session):
    song = _add_song(db_session, "joe|closer", "Closer", "Joe Inoue", "Closer")
    song.duration_seconds = 180
    for day in range(1, 8):
        for hour in range(3):
            _add_play(db_session, song, datetime(2026, 6, day, 10 + hour))
    db_session.commit()

    response = client.get("/api/v1/obsessions")
    assert response.status_code == 200
    episodes = response.json()
    assert len(episodes) == 1
    episode = episodes[0]
    assert episode["title"] == "Closer"
    assert episode["tier"] == "obsesion"
    assert episode["strong_days"] == 7
    assert episode["plays"] == 21
    assert episode["start"] == "2026-06-01"
    assert episode["end"] == "2026-06-07"
    assert len(episode["days"]) == 7

    timeline = client.get(f"/api/v1/songs/{song.id}/timeline")
    assert timeline.status_code == 200
    data = timeline.json()
    assert data["song"]["title"] == "Closer"
    assert data["song"]["plays"] == 21
    assert len(data["days"]) == 7
    assert len(data["episodes"]) == 1
    assert data["first_listen"].startswith("2026-06-01")
    assert data["total_minutes"] == 63
    assert data["duration_coverage"] == 1.0

    missing = client.get("/api/v1/songs/999999/timeline")
    assert missing.status_code == 404


def test_recap_endpoint(client, db_session):
    song = _add_song(db_session, "joe|closer", "Closer", "Joe Inoue", "Closer")
    song.duration_seconds = 180
    for day in range(1, 8):
        for hour in range(2):
            _add_play(db_session, song, datetime(2026, 6, day, 10 + hour))
    db_session.commit()

    response = client.get(
        "/api/v1/recap",
        params={
            "since": "2026-06-01T00:00:00",
            "until": "2026-06-07T23:59:59",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_plays"] == 14
    assert data["total_minutes"] == 42
    assert data["total_hours"] == 0.7
    assert data["duration_coverage"] == 1.0
    assert data["top_song"]["title"] == "Closer"
    assert data["top_song"]["days"] == 7
    assert data["top_song_longest_streak"] == 7
    assert data["top_artists"][0]["artist"] == "Joe Inoue"
    assert data["top_albums"][0]["album"] == "Closer"
    assert data["profile"]["key"] == "loopero"
    assert data["top_genres"] == []
    assert data["first_play"].startswith("2026-06-01")


def test_dedupe_endpoint_merges_variants(client, seeded, db_session):
    response = client.post("/api/v1/maintenance/dedupe")
    assert response.status_code == 200
    data = response.json()
    assert data["groups_merged"] == 1
    assert data["songs_removed"] == 1
    assert data["plays_moved"] == 1
    assert data["dry_run"] is False

    songs = client.get("/api/v1/songs/top").json()
    assert songs[0]["title"] == "Closer"
    assert songs[0]["plays"] == 3


def test_dedupe_dry_run_endpoint_keeps_variants(client, seeded, db_session):
    response = client.post("/api/v1/maintenance/dedupe?dry_run=true")
    assert response.status_code == 200
    data = response.json()
    assert data["groups_merged"] == 1
    assert data["dry_run"] is True

    songs = client.get("/api/v1/songs/top").json()
    assert len(songs) == 2


def test_sleep_endpoint(client, db_session):
    night = _add_song(db_session, "x|night", "Night Song", "Artist", "")
    for minute in range(10):
        _add_play(
            db_session,
            night,
            datetime(2026, 1, 10, 0, minute),
        )
    day = _add_song(db_session, "x|day", "Day Song", "Artist", "")
    _add_play(db_session, day, datetime(2026, 1, 10, 12, 0))
    db_session.commit()

    response = client.get("/api/v1/sleep")
    assert response.status_code == 200
    data = response.json()
    assert data["window_start"] == 0
    assert data["window_end"] == 7
    assert data["night_plays"] == 10
    assert data["total_plays"] == 11
    assert data["songs"][0]["title"] == "Night Song"
    assert data["songs"][0]["plays"] == 10
    assert data["songs"][0]["night_share"] == 1.0


def test_recap_includes_sleep_summary(client, seeded):
    response = client.get(
        "/api/v1/recap",
        params={"since": "2024-01-01T00:00:00", "until": "2026-12-31T23:59:59"},
    )
    assert response.status_code == 200
    sleep = response.json()["sleep"]
    assert sleep["window_start"] == 0
    assert sleep["window_end"] == 7
    assert "night_plays" in sleep
    assert isinstance(sleep["songs"], list)


def test_artwork_endpoint(client, monkeypatch):
    from canciones.api import router as router_module

    monkeypatch.setattr(
        router_module,
        "find_cover",
        lambda artist, title: "https://example.com/cover.jpg",
    )
    response = client.get(
        "/api/v1/artwork", params={"artist": "Joe Inoue", "title": "Closer"}
    )
    assert response.status_code == 200
    assert response.json() == {"url": "https://example.com/cover.jpg"}

    monkeypatch.setattr(router_module, "find_cover", lambda artist, title: None)
    response = client.get("/api/v1/artwork", params={"artist": "Desconocido"})
    assert response.status_code == 200
    assert response.json() == {"url": None}


def test_durations_backfill_endpoint(client, db_session, monkeypatch):
    from canciones.api import router as router_module

    song = _add_song(db_session, "x|duration", "Duration", "Artist", "Album")
    db_session.commit()

    monkeypatch.setattr(
        router_module,
        "find_duration",
        lambda artist, title: 200,
    )
    response = client.post("/api/v1/durations/backfill")
    assert response.status_code == 200
    assert response.json() == {"processed": 1, "updated": 1}

    db_session.expire_all()
    assert db_session.get(SongDB, song.id).duration_seconds == 200


def test_now_playing_endpoint_returns_live_track(client, monkeypatch):
    monkeypatch.setattr(
        LastFMAPIIngestor,
        "fetch_now_playing",
        lambda self: NowPlayingTrack(
            title="Voto En Blanco",
            artist="El Jincho",
            album="Single",
            playing=True,
        ),
    )

    response = client.get("/api/v1/now-playing")

    assert response.status_code == 200
    assert response.json() == {
        "playing": True,
        "track": {
            "title": "Voto En Blanco",
            "artist": "El Jincho",
            "album": "Single",
            "scrobbled_at": None,
        },
    }


def test_now_playing_endpoint_serializes_utc(client, monkeypatch):
    monkeypatch.setattr(
        LastFMAPIIngestor,
        "fetch_now_playing",
        lambda self: NowPlayingTrack(
            title="Closer",
            artist="Joe Inoue",
            album="Closer",
            playing=False,
            scrobbled_at=datetime(2026, 11, 23, 20, 0, tzinfo=timezone.utc),
        ),
    )

    response = client.get("/api/v1/now-playing")

    assert response.status_code == 200
    payload = response.json()
    assert payload["playing"] is False
    assert payload["track"]["scrobbled_at"].startswith("2026-11-23T20:00:00")


def test_now_playing_endpoint_without_credentials_returns_empty(client):
    response = client.get("/api/v1/now-playing")

    assert response.status_code == 200
    assert response.json() == {"playing": False, "track": None}


def test_now_playing_endpoint_handles_service_error(client, monkeypatch):
    def fail(self):
        raise URLError("boom")

    monkeypatch.setattr(LastFMAPIIngestor, "fetch_now_playing", fail)

    response = client.get("/api/v1/now-playing")

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "Last.fm" not in detail
    assert "reproducción" in detail.lower()
