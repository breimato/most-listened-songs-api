"""Detección de épocas de obsesión a partir de las reproducciones.

Una obsesión es una ventana de una o dos semanas en la que una canción se
escucha casi todos los días y varias veces. Los picos aislados (por ejemplo,
un bucle de 100 reproducciones en un día) no cuentan por sí solos: la clave es
la consistencia.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from canciones.domain.normalization import normalized_key

# (ventana en días, días "fuertes" mínimos, reproducciones mínimas, nivel)
WINDOWS = (
    (7, 5, 14, "obsesion"),
    (14, 10, 28, "obsesion"),
    (7, 4, 10, "racha"),
    (14, 7, 20, "racha"),
)

TIER_RANK = {"obsesion": 0, "racha": 1}
STRONG_DAY_PLAYS = 2


@dataclass(frozen=True)
class PlayRecord:
    song_id: int
    title: str
    artist: str
    album: str
    played_at: datetime
    duration_seconds: int | None = None


@dataclass
class ObsessionEpisode:
    id: str
    song_id: int
    title: str
    artist: str
    album: str
    start: date
    end: date
    span_days: int
    strong_days: int
    active_days: int
    plays: int
    peak_day: date
    peak_plays: int
    tier: str
    score: int
    days: list[tuple[date, int]]


def local_date(value: datetime, tz: ZoneInfo) -> date:
    """Convierte un timestamp (UTC naive o aware) al día local."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(tz).date()


def _group_records(records: list[PlayRecord], tz: ZoneInfo) -> list[dict]:
    groups: dict[str, dict] = {}

    for record in records:
        key = normalized_key(record.artist or "", record.title or "")
        group = groups.setdefault(
            key,
            {"variants": Counter(), "meta": {}, "days": Counter()},
        )
        group["variants"][record.song_id] += 1
        group["meta"][record.song_id] = (
            record.title,
            record.artist,
            record.album,
        )
        group["days"][local_date(record.played_at, tz)] += 1

    return list(groups.values())


def _candidates(days: list[date], plays_by_day: Counter) -> list[tuple[date, date, str]]:
    candidates: list[tuple[date, date, str]] = []

    for start in days:
        for window, min_strong, min_plays, tier in WINDOWS:
            end = start + timedelta(days=window - 1)
            strong = [
                day
                for day in days
                if start <= day <= end and plays_by_day[day] >= STRONG_DAY_PLAYS
            ]
            plays = sum(plays_by_day[day] for day in strong)
            if len(strong) >= min_strong and plays >= min_plays:
                candidates.append((start, end, tier))

    return candidates


def _merge(candidates: list[tuple[date, date, str]]) -> list[list]:
    merged: list[list] = []
    for start, end, tier in sorted(candidates):
        if merged and start <= merged[-1][1] + timedelta(days=1):
            merged[-1][1] = max(merged[-1][1], end)
            if TIER_RANK[tier] < TIER_RANK[merged[-1][2]]:
                merged[-1][2] = tier
        else:
            merged.append([start, end, tier])
    return merged


def _score(strong_days: int, span_days: int, plays: int) -> int:
    coverage = strong_days / span_days if span_days else 0
    span = min(span_days, 21) / 21
    intensity = min(plays / strong_days, 8) / 8 if strong_days else 0
    volume = min(plays, 150) / 150
    return round(coverage * 45 + span * 25 + intensity * 20 + volume * 10)


def _build_episode(
    group: dict,
    start: date,
    end: date,
    tier: str,
) -> ObsessionEpisode:
    plays_by_day: Counter = group["days"]
    active = [day for day in plays_by_day if start <= day <= end]
    if not active:
        raise ValueError("episode without active days")

    # Las ventanas de detección son una criba, no los límites del episodio:
    # recortamos al primer y último día con reproducciones reales.
    start = min(active)
    end = max(active)

    days_in_range = [day for day in plays_by_day if start <= day <= end]
    strong = [day for day in days_in_range if plays_by_day[day] >= STRONG_DAY_PLAYS]
    if not strong:
        raise ValueError("episode without strong days")

    song_id, _ = group["variants"].most_common(1)[0]
    title, artist, album = group["meta"][song_id]
    span = (end - start).days + 1
    total_plays = sum(plays_by_day[day] for day in days_in_range)
    peak_day = max(days_in_range, key=lambda day: plays_by_day[day])

    return ObsessionEpisode(
        id=f"{song_id}-{start.isoformat()}",
        song_id=song_id,
        title=title,
        artist=artist,
        album=album,
        start=start,
        end=end,
        span_days=span,
        strong_days=len(strong),
        active_days=len(days_in_range),
        plays=total_plays,
        peak_day=peak_day,
        peak_plays=plays_by_day[peak_day],
        tier=tier,
        score=_score(len(strong), span, total_plays),
        days=[
            (start + timedelta(days=offset), plays_by_day.get(start + timedelta(days=offset), 0))
            for offset in range(span)
        ],
    )


def detect_obsessions(
    records: list[PlayRecord],
    timezone_name: str = "Europe/Madrid",
) -> list[ObsessionEpisode]:
    tz = ZoneInfo(timezone_name)
    episodes: list[ObsessionEpisode] = []

    for group in _group_records(records, tz):
        days = sorted(group["days"])
        if not days:
            continue

        candidates = _candidates(days, group["days"])
        if not candidates:
            continue

        for start, end, tier in _merge(candidates):
            try:
                episodes.append(_build_episode(group, start, end, tier))
            except ValueError:
                continue

    episodes.sort(
        key=lambda episode: (
            TIER_RANK.get(episode.tier, 9),
            -episode.score,
            -episode.plays,
        )
    )
    return episodes
