from datetime import datetime, timezone

from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor
from canciones.config import settings
from canciones.domain.models import NowPlayingTrack


def _payload(track: dict) -> dict:
    return {"recenttracks": {"track": [track]}}


def test_fetch_now_playing_returns_live_track(monkeypatch):
    ingestor = LastFMAPIIngestor(api_key="key", username="user")
    monkeypatch.setattr(
        ingestor,
        "_fetch_page",
        lambda **kwargs: _payload(
            {
                "name": "Voto En Blanco",
                "artist": {"#text": "El Jincho"},
                "album": {"#text": "Single"},
                "@attr": {"nowplaying": "true"},
            }
        ),
    )

    track = ingestor.fetch_now_playing()

    assert track == NowPlayingTrack(
        title="Voto En Blanco",
        artist="El Jincho",
        album="Single",
        playing=True,
        scrobbled_at=None,
    )


def test_fetch_now_playing_falls_back_to_last_scrobble(monkeypatch):
    ingestor = LastFMAPIIngestor(api_key="key", username="user")
    monkeypatch.setattr(
        ingestor,
        "_fetch_page",
        lambda **kwargs: _payload(
            {
                "name": "Closer",
                "artist": "Joe Inoue",
                "album": "Closer",
                "date": {"uts": "1795456524"},
            }
        ),
    )

    track = ingestor.fetch_now_playing()

    assert track is not None
    assert track.playing is False
    assert track.scrobbled_at == datetime.fromtimestamp(1795456524, tz=timezone.utc)
    assert track.scrobbled_at.utcoffset() == timezone.utc.utcoffset(None)


def test_fetch_now_playing_without_credentials_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "lastfm_api_key", "")
    monkeypatch.setattr(settings, "lastfm_username", "")

    assert LastFMAPIIngestor().fetch_now_playing() is None
