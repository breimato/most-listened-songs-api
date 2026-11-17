from datetime import datetime
from zoneinfo import ZoneInfo

from canciones.domain.obsessions import PlayRecord, detect_obsessions, local_date


def record(song_id, title, artist, day, hour=12):
    return PlayRecord(
        song_id=song_id,
        title=title,
        artist=artist,
        album="",
        played_at=datetime(2026, 6, day, hour, 0),
    )


def plays_for_days(title, artist, days, per_day=3, song_id=1):
    records = []
    for day in days:
        for hour in range(per_day):
            records.append(record(song_id, title, artist, day, 10 + hour))
    return records


def test_two_week_streak_is_an_obsession():
    records = plays_for_days("Closer", "Joe Inoue", range(1, 15), per_day=3)

    episodes = detect_obsessions(records)

    assert len(episodes) == 1
    episode = episodes[0]
    assert episode.tier == "obsesion"
    assert episode.start.isoformat() == "2026-06-01"
    assert episode.end.isoformat() == "2026-06-14"
    assert episode.span_days == 14
    assert episode.strong_days == 14
    assert episode.plays == 42
    assert len(episode.days) == 14


def test_single_day_spike_is_not_an_obsession():
    records = [
        record(1, "Gracias", "Despistaos", 12, hour) for hour in range(24)
    ] + [
        record(1, "Gracias", "Despistaos", 12, 23) for _ in range(26)
    ]

    assert detect_obsessions(records) == []


def test_four_strong_days_in_a_week_is_a_racha():
    records = []
    for day, count in ((1, 3), (2, 3), (3, 2), (5, 2)):
        for hour in range(count):
            records.append(record(1, "Need You Now", "Lady Antebellum", day, 10 + hour))

    episodes = detect_obsessions(records)

    assert len(episodes) == 1
    assert episodes[0].tier == "racha"
    assert episodes[0].strong_days == 4
    assert episodes[0].plays == 10


def test_versions_are_grouped():
    records = []
    for day in range(1, 8):
        records.append(record(1, "Closer", "Joe Inoue", day, 10))
        records.append(record(2, "Closer (Remix)", "Joe Inoue", day, 11))

    episodes = detect_obsessions(records)

    assert len(episodes) == 1
    assert episodes[0].plays == 14
    assert episodes[0].strong_days == 7


def test_timezone_moves_late_night_plays_to_next_day():
    madrid = ZoneInfo("Europe/Madrid")

    assert local_date(datetime(2026, 6, 1, 23, 30), madrid).isoformat() == "2026-06-02"
    assert local_date(datetime(2026, 1, 1, 23, 30), madrid).isoformat() == "2026-01-02"
