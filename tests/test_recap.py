from datetime import date, datetime

from canciones.domain.obsessions import PlayRecord
from canciones.domain.recap import build_recap


def record(song_id, title, artist, album, day, hour=12, duration=180):
    return PlayRecord(
        song_id=song_id,
        title=title,
        artist=artist,
        album=album,
        played_at=datetime(2026, 6, day, hour, 0),
        duration_seconds=duration,
    )


def test_recap_totals_and_rankings():
    records = [
        record(1, "Closer", "Joe Inoue", "Closer", day) for day in (1, 2, 3)
    ] + [
        record(2, "Iris", "Goo Goo Dolls", "Dizzy Up The Girl", 2, duration=200)
    ]

    recap = build_recap(
        records,
        period_start=date(2026, 6, 1),
        period_end=date(2026, 6, 3),
    )

    assert recap.total_plays == 4
    assert recap.total_minutes == 12  # (3*180 + 200) / 60
    assert recap.total_hours == 0.2
    assert recap.duration_coverage == 1.0
    assert recap.unique_songs == 2
    assert recap.unique_artists == 2
    assert recap.unique_albums == 2
    assert recap.days_listened == 3
    assert recap.longest_streak == 3
    assert recap.top_song.title == "Closer"
    assert recap.top_song.plays == 3
    assert recap.top_song.days == 3
    assert recap.top_song_longest_streak == 3
    assert recap.top_artists[0].artist == "Joe Inoue"
    assert recap.top_albums[0].album == "Closer"
    assert recap.first_song == "Closer"
    assert recap.profile.key in {"loopero", "equilibrado", "constante"}


def test_recap_night_profile():
    records = [record(1, "Night", "Artist", "Album", day, hour=23) for day in (1, 2, 3)]

    recap = build_recap(records)

    assert recap.profile.key == "nocturno"
    assert "22:00" in recap.profile.description


def test_recap_streak_with_gap():
    records = [record(1, "Song", "Artist", "Album", day) for day in (1, 2, 4)]

    recap = build_recap(records)

    assert recap.days_listened == 3
    assert recap.longest_streak == 2


def test_recap_counts_unknown_durations():
    records = [
        record(1, "Known", "Artist", "Album", 1, duration=180),
        record(2, "Unknown", "Artist", "Album", 1, duration=None),
    ]

    recap = build_recap(records)

    assert recap.total_plays == 2
    assert recap.duration_coverage == 0.5
    assert recap.total_minutes == 3
    assert recap.estimated_minutes == 6
