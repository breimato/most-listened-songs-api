from datetime import datetime
from zoneinfo import ZoneInfo

from canciones.domain.obsessions import PlayRecord
from canciones.domain.sleep import build_sleep

MADRID = ZoneInfo("Europe/Madrid")


def record(song_id: int, title: str, artist: str, played_at: datetime, duration=200):
    return PlayRecord(
        song_id=song_id,
        title=title,
        artist=artist,
        album="",
        played_at=played_at,
        duration_seconds=duration,
    )


def test_sleep_ranking_uses_night_minutes_and_share():
    # Invierno: Madrid = UTC+1. 01:00 local -> 00:00 UTC.
    night = datetime(2026, 1, 10, 0, 0)
    day = datetime(2026, 1, 10, 12, 0)

    records = []
    for _ in range(12):
        records.append(record(1, "Alpha", "Artist A", night, 200))
    for _ in range(2):
        records.append(record(1, "Alpha", "Artist A", day, 200))
    for _ in range(10):
        records.append(record(2, "Beta", "Artist B", night.replace(hour=2), 600))
    for _ in range(9):
        records.append(record(3, "Gamma", "Artist C", night.replace(hour=1), 300))
    records.append(record(3, "Gamma", "Artist C", day, 300))
    for _ in range(10):
        records.append(record(4, "Delta", "Artist D", night.replace(hour=2), 0))

    summary = build_sleep(records, MADRID)

    assert summary.window_start == 0
    assert summary.window_end == 7
    assert summary.total_plays == 44
    assert summary.night_plays == 41
    assert summary.night_share == 0.932
    assert summary.estimated is True
    assert summary.duration_coverage < 1
    assert summary.nights == 1
    assert summary.top_hour == 3
    assert summary.top_artist == "Artist B"

    # Beta (10 plays x 10 min, 100% noche) gana a Delta (estimada) y Alpha.
    assert [song.title for song in summary.songs] == ["Beta", "Delta", "Alpha"]
    beta = summary.songs[0]
    assert beta.plays == 10
    assert beta.night_share == 1.0
    assert beta.minutes == 100
    assert beta.estimated is False
    assert summary.songs[1].estimated is True
    # Gamma tiene 9 escuchas nocturnas: no llega al mínimo de 10.
    assert "Gamma" not in [song.title for song in summary.songs]


def test_sleep_thresholds_are_configurable():
    night = datetime(2026, 1, 10, 0, 0)
    records = [
        record(1, "Song", "Artist", night, 200)
        for _ in range(5)
    ]

    strict = build_sleep(records, MADRID)
    relaxed = build_sleep(
        records,
        MADRID,
        min_night_plays=5,
        min_night_share=0.4,
    )

    assert strict.songs == []
    assert len(relaxed.songs) == 1


def test_sleep_uses_local_timezone_boundaries():
    # 23:30 UTC del día 9 = 00:30 del día 10 en Madrid -> noche.
    # 06:30 UTC = 07:30 en Madrid -> ya no es noche.
    records = [
        record(1, "Song", "Artist", datetime(2026, 1, 9, 23, 30), 200)
        for _ in range(10)
    ] + [
        record(1, "Song", "Artist", datetime(2026, 1, 10, 6, 30), 200)
        for _ in range(5)
    ]

    summary = build_sleep(records, MADRID)

    assert summary.night_plays == 10
    assert summary.total_plays == 15
    assert summary.nights == 1
    assert summary.songs[0].plays == 10


def test_sleep_empty_history():
    summary = build_sleep([], MADRID)

    assert summary.total_plays == 0
    assert summary.night_plays == 0
    assert summary.night_share == 0
    assert summary.songs == []
    assert summary.top_hour is None
    assert summary.top_artist is None
