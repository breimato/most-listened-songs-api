"""Lista "para dormir": canciones que suenan de noche.

La franja nocturna es 00:00–07:00 en la zona horaria de la app. El ranking
mezcla tiempo real escuchado de noche con el porcentaje de escuchas nocturnas,
para que no gane solo la canción más repetida en general ni una escuchada tres
veces a las 3 de la mañana.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from canciones.domain.normalization import normalize_artist
from canciones.domain.obsessions import PlayRecord

NIGHT_START = 0
NIGHT_END = 7
DEFAULT_MIN_NIGHT_PLAYS = 10
DEFAULT_MIN_NIGHT_SHARE = 0.4


@dataclass
class SleepSong:
    song_id: int
    title: str
    artist: str
    album: str
    plays: int
    total_plays: int
    night_share: float
    minutes: int
    total_minutes: int
    estimated: bool
    score: float


@dataclass
class SleepSummary:
    window_start: int
    window_end: int
    total_plays: int
    night_plays: int
    night_share: float
    night_minutes: int
    duration_coverage: float
    estimated: bool
    nights: int
    top_hour: int | None
    top_artist: str | None
    songs: list[SleepSong]


def _local_datetime(value: datetime, tz: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(tz)


def _is_night(hour: int) -> bool:
    return NIGHT_START <= hour < NIGHT_END


def build_sleep(
    records: list[PlayRecord],
    timezone: str | ZoneInfo = "Europe/Madrid",
    min_night_plays: int = DEFAULT_MIN_NIGHT_PLAYS,
    min_night_share: float = DEFAULT_MIN_NIGHT_SHARE,
    limit: int = 50,
) -> SleepSummary:
    tz = ZoneInfo(timezone) if isinstance(timezone, str) else timezone
    total_plays = len(records)
    if not records:
        return SleepSummary(
            window_start=NIGHT_START,
            window_end=NIGHT_END,
            total_plays=0,
            night_plays=0,
            night_share=0.0,
            night_minutes=0,
            duration_coverage=0.0,
            estimated=False,
            nights=0,
            top_hour=None,
            top_artist=None,
            songs=[],
        )

    known = [
        record
        for record in records
        if (record.duration_seconds or 0) > 0
    ]
    average_seconds = (
        sum(record.duration_seconds or 0 for record in known) / len(known)
        if known
        else 0.0
    )

    groups: dict[int, dict] = {}
    night_dates: set[date] = set()
    night_hours: Counter[int] = Counter()
    night_artists: dict[str, dict] = {}
    total_night_plays = 0
    total_night_known = 0
    total_night_seconds = 0.0

    for record in records:
        local = _local_datetime(record.played_at, tz)
        hour = local.hour
        duration = record.duration_seconds or 0
        group = groups.setdefault(
            record.song_id,
            {
                "title": record.title,
                "artist": record.artist,
                "album": record.album,
                "total_plays": 0,
                "total_seconds": 0.0,
                "night_plays": 0,
                "night_seconds": 0.0,
                "night_known": 0,
                "night_dates": set(),
            },
        )

        group["total_plays"] += 1
        group["total_seconds"] += duration if duration > 0 else average_seconds

        if not _is_night(hour):
            continue

        effective = duration if duration > 0 else average_seconds
        total_night_plays += 1
        total_night_seconds += effective
        if duration > 0:
            total_night_known += 1
        night_dates.add(local.date())
        night_hours[hour] += 1

        group["night_plays"] += 1
        group["night_seconds"] += effective
        group["night_known"] += 1 if duration > 0 else 0
        group["night_dates"].add(local.date())

        artist_key = normalize_artist(record.artist or "")
        artist_group = night_artists.setdefault(
            artist_key,
            {"seconds": 0.0, "plays": 0, "names": Counter()},
        )
        artist_group["seconds"] += effective
        artist_group["plays"] += 1
        artist_group["names"][record.artist or "Desconocido"] += 1

    candidates: list[SleepSong] = []
    for song_id, group in groups.items():
        night_plays = group["night_plays"]
        if night_plays < min_night_plays:
            continue

        night_share = night_plays / group["total_plays"]
        if night_share < min_night_share:
            continue

        night_minutes = round(group["night_seconds"] / 60)
        total_minutes = round(group["total_seconds"] / 60)
        score = (
            night_minutes * night_share
            if night_minutes > 0
            else night_plays * night_share
        )
        candidates.append(
            SleepSong(
                song_id=song_id,
                title=group["title"],
                artist=group["artist"],
                album=group["album"],
                plays=night_plays,
                total_plays=group["total_plays"],
                night_share=round(night_share, 3),
                minutes=night_minutes,
                total_minutes=total_minutes,
                estimated=group["night_known"] < night_plays,
                score=round(score, 1),
            )
        )

    candidates.sort(
        key=lambda song: (song.score, song.minutes, song.plays),
        reverse=True,
    )
    if limit > 0:
        candidates = candidates[:limit]

    top_artist = None
    if night_artists:
        best = max(
            night_artists.values(),
            key=lambda group: (group["seconds"], group["plays"]),
        )
        top_artist = best["names"].most_common(1)[0][0]

    return SleepSummary(
        window_start=NIGHT_START,
        window_end=NIGHT_END,
        total_plays=total_plays,
        night_plays=total_night_plays,
        night_share=round(total_night_plays / total_plays, 3),
        night_minutes=round(total_night_seconds / 60),
        duration_coverage=round(
            total_night_known / total_night_plays, 3
        )
        if total_night_plays
        else 0.0,
        estimated=total_night_known < total_night_plays,
        nights=len(night_dates),
        top_hour=night_hours.most_common(1)[0][0] if night_hours else None,
        top_artist=top_artist,
        songs=candidates,
    )
