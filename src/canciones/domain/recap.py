"""Resumen tipo Wrapped calculado a partir de las reproducciones."""

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from canciones.domain.normalization import normalize_artist, normalized_key
from canciones.domain.obsessions import ObsessionEpisode, detect_obsessions


@dataclass
class RecapSong:
    song_id: int
    title: str
    artist: str
    album: str
    plays: int
    minutes: int
    share: float
    days: int
    longest_streak: int


@dataclass
class RecapArtist:
    artist: str
    plays: int
    minutes: int
    share: float
    songs: int
    top_song: str | None
    top_song_id: int | None


@dataclass
class RecapAlbum:
    album: str
    artist: str
    plays: int
    minutes: int
    top_song: str
    top_song_id: int


@dataclass
class RecapMonthlyArtist:
    month: str
    artist: str
    plays: int


@dataclass
class RecapProfile:
    key: str
    label: str
    description: str


@dataclass
class Recap:
    since: date
    until: date
    period_days: int
    total_plays: int
    total_minutes: int
    total_hours: float
    estimated_minutes: int
    estimated_hours: float
    duration_coverage: float
    unique_songs: int
    unique_artists: int
    unique_albums: int
    days_listened: int
    longest_streak: int
    top_day: date | None
    top_day_plays: int
    top_hour: int | None
    top_hour_plays: int
    first_play: datetime | None
    first_song: str | None
    first_song_id: int | None
    last_play: datetime | None
    last_song: str | None
    last_song_id: int | None
    top_song: RecapSong | None
    top_song_days: int
    top_song_longest_streak: int
    top_songs: list[RecapSong]
    top_artists: list[RecapArtist]
    top_albums: list[RecapAlbum]
    monthly_top_artists: list[RecapMonthlyArtist]
    profile: RecapProfile
    top_obsession: ObsessionEpisode | None


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFD", (value or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _local_date(value: datetime, tz: ZoneInfo) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(tz).date()


def _local_hour(value: datetime, tz: ZoneInfo) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(tz).hour


def _longest_streak(days: list[date]) -> int:
    ordered = sorted(set(days))
    if not ordered:
        return 0
    best = current = 1
    for previous, day in zip(ordered, ordered[1:]):
        if (day - previous).days == 1:
            current += 1
        else:
            current = 1
        best = max(best, current)
    return best


def _minutes(seconds: int) -> int:
    return round(seconds / 60)


def build_recap(
    records,
    timezone_name: str = "Europe/Madrid",
    period_start: date | None = None,
    period_end: date | None = None,
) -> Recap:
    tz = ZoneInfo(timezone_name)
    if period_start and period_end:
        records = [
            record
            for record in records
            if period_start <= _local_date(record.played_at, tz) <= period_end
        ]
    total_plays = len(records)
    if not total_plays:
        raise ValueError("no plays")

    known = [record for record in records if (record.duration_seconds or 0) > 0]
    seconds = sum(record.duration_seconds or 0 for record in known)
    minutes = _minutes(seconds)
    estimated_seconds = (seconds / len(known)) * total_plays if known else 0
    estimated_minutes = _minutes(round(estimated_seconds))
    coverage = round(len(known) / total_plays, 3)

    dates = [_local_date(record.played_at, tz) for record in records]
    date_counts = Counter(dates)
    hour_counts = Counter(_local_hour(record.played_at, tz) for record in records)
    days = sorted(date_counts)

    since = period_start or days[0]
    until = period_end or days[-1]
    period_days = max(1, (until - since).days + 1)

    # Canciones agrupadas por versión normalizada.
    song_groups: dict[str, dict] = {}
    for record in records:
        key = normalized_key(record.artist or "", record.title or "")
        group = song_groups.setdefault(
            key,
            {
                "plays": 0,
                "seconds": 0,
                "days": set(),
                "variants": Counter(),
                "meta": {},
            },
        )
        group["plays"] += 1
        group["seconds"] += record.duration_seconds or 0
        group["days"].add(_local_date(record.played_at, tz))
        group["variants"][record.song_id] += 1
        group["meta"][record.song_id] = (
            record.title,
            record.artist,
            record.album,
        )

    songs: list[RecapSong] = []
    for group in song_groups.values():
        song_id = group["variants"].most_common(1)[0][0]
        title, artist, album = group["meta"][song_id]
        song_days = sorted(group["days"])
        songs.append(
            RecapSong(
                song_id=song_id,
                title=title,
                artist=artist,
                album=album,
                plays=group["plays"],
                minutes=_minutes(group["seconds"]),
                share=round(group["plays"] / total_plays, 3),
                days=len(song_days),
                longest_streak=_longest_streak(song_days),
            )
        )
    songs.sort(key=lambda song: (song.plays, song.minutes), reverse=True)
    song_by_key = {
        normalized_key(song.artist, song.title): song for song in songs
    }

    # Artistas.
    artist_groups: dict[str, dict] = {}
    artist_names: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        key = normalize_artist(record.artist or "")
        group = artist_groups.setdefault(
            key,
            {
                "plays": 0,
                "seconds": 0,
                "songs": Counter(),
                "names": Counter(),
            },
        )
        group["plays"] += 1
        group["seconds"] += record.duration_seconds or 0
        group["songs"][normalized_key(record.artist or "", record.title or "")] += 1
        group["names"][record.artist] += 1
        artist_names[key][record.artist] += 1

    artists: list[RecapArtist] = []
    for group in artist_groups.values():
        top_key = group["songs"].most_common(1)[0][0]
        top_song = song_by_key.get(top_key)
        artists.append(
            RecapArtist(
                artist=group["names"].most_common(1)[0][0],
                plays=group["plays"],
                minutes=_minutes(group["seconds"]),
                share=round(group["plays"] / total_plays, 3),
                songs=len(group["songs"]),
                top_song=top_song.title if top_song else None,
                top_song_id=top_song.song_id if top_song else None,
            )
        )
    artists.sort(key=lambda artist: (artist.plays, artist.minutes), reverse=True)

    # Álbumes (se ignoran los que no tienen nombre).
    album_groups: dict[str, dict] = {}
    for record in records:
        if not (record.album or "").strip():
            continue
        key = f"{normalize_artist(record.artist or '')}|{_normalize_text(record.album)}"
        group = album_groups.setdefault(
            key,
            {
                "plays": 0,
                "seconds": 0,
                "songs": Counter(),
                "album": record.album,
                "artist": record.artist,
            },
        )
        group["plays"] += 1
        group["seconds"] += record.duration_seconds or 0
        group["songs"][normalized_key(record.artist or "", record.title or "")] += 1

    albums: list[RecapAlbum] = []
    for group in album_groups.values():
        top_key = group["songs"].most_common(1)[0][0]
        top_song = song_by_key.get(top_key)
        if top_song is None:
            continue
        albums.append(
            RecapAlbum(
                album=group["album"],
                artist=group["artist"],
                plays=group["plays"],
                minutes=_minutes(group["seconds"]),
                top_song=top_song.title,
                top_song_id=top_song.song_id,
            )
        )
    albums.sort(key=lambda album: (album.plays, album.minutes), reverse=True)

    # Artista nº1 de cada mes.
    monthly: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        month = _local_date(record.played_at, tz).strftime("%Y-%m")
        key = normalize_artist(record.artist or "")
        monthly[month][key] += 1

    monthly_top: list[RecapMonthlyArtist] = []
    for month in sorted(monthly):
        key = monthly[month].most_common(1)[0][0]
        artist_name = artist_names[key].most_common(1)[0][0]
        monthly_top.append(
            RecapMonthlyArtist(
                month=month,
                artist=artist_name,
                plays=monthly[month][key],
            )
        )

    top_artist_share = artists[0].share if artists else 0
    top_song = songs[0] if songs else None
    top_song_share = top_song.share if top_song else 0
    night_plays = sum(
        count for hour, count in hour_counts.items() if hour >= 22 or hour < 6
    )
    morning_plays = sum(count for hour, count in hour_counts.items() if 6 <= hour < 12)
    repeat_rate = total_plays / max(len(song_groups), 1)
    days_share = len(days) / period_days

    if night_plays / total_plays >= 0.4:
        profile = RecapProfile(
            key="nocturno",
            label="Nocturno",
            description=(
                f"El {round(night_plays / total_plays * 100)}% de tus escuchas "
                "fueron entre las 22:00 y las 06:00."
            ),
        )
    elif morning_plays / total_plays >= 0.35:
        profile = RecapProfile(
            key="madrugador",
            label="Madrugador",
            description=(
                f"El {round(morning_plays / total_plays * 100)}% de tus escuchas "
                "fueron antes del mediodía."
            ),
        )
    elif repeat_rate >= 10 or top_song_share >= 0.08:
        profile = RecapProfile(
            key="loopero",
            label="Loopero",
            description=(
                f"Escuchaste una media de {repeat_rate:.1f} veces cada canción. "
                "Cuando te gusta una, la repites."
            ),
        )
    elif len(artist_groups) / total_plays >= 0.3 or top_artist_share < 0.06:
        profile = RecapProfile(
            key="explorador",
            label="Explorador",
            description=(
                "Tu artista más escuchado solo se llevó el "
                f"{round(top_artist_share * 100)}% de tus reproducciones."
            ),
        )
    elif days_share >= 0.8:
        profile = RecapProfile(
            key="constante",
            label="Constante",
            description=(
                f"Escuchaste música el {round(days_share * 100)}% de los días "
                "del periodo."
            ),
        )
    else:
        profile = RecapProfile(
            key="equilibrado",
            label="Equilibrado",
            description="Un poco de todo: sin una obsesión dominante.",
        )

    ordered_dates = sorted(date_counts, key=lambda day: date_counts[day], reverse=True)
    top_day = ordered_dates[0]
    top_hour = hour_counts.most_common(1)[0][0]

    first = min(records, key=lambda record: record.played_at)
    last = max(records, key=lambda record: record.played_at)
    episodes = detect_obsessions(records, timezone_name)

    return Recap(
        since=since,
        until=until,
        period_days=period_days,
        total_plays=total_plays,
        total_minutes=minutes,
        total_hours=round(minutes / 60, 1),
        estimated_minutes=estimated_minutes,
        estimated_hours=round(estimated_minutes / 60, 1),
        duration_coverage=coverage,
        unique_songs=len(song_groups),
        unique_artists=len(artist_groups),
        unique_albums=len(album_groups),
        days_listened=len(days),
        longest_streak=_longest_streak(days),
        top_day=top_day,
        top_day_plays=date_counts[top_day],
        top_hour=top_hour,
        top_hour_plays=hour_counts[top_hour],
        first_play=first.played_at,
        first_song=first.title,
        first_song_id=first.song_id,
        last_play=last.played_at,
        last_song=last.title,
        last_song_id=last.song_id,
        top_song=top_song,
        top_song_days=top_song.days if top_song else 0,
        top_song_longest_streak=top_song.longest_streak if top_song else 0,
        top_songs=songs[:5],
        top_artists=artists[:5],
        top_albums=albums[:5],
        monthly_top_artists=monthly_top,
        profile=profile,
        top_obsession=episodes[0] if episodes else None,
    )
