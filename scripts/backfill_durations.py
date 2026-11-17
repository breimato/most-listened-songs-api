#!/usr/bin/env python3
"""Rellena la duración de las canciones consultando Deezer (y iTunes de respaldo).

Uso:
    DATABASE_URL=postgresql+psycopg://... python scripts/backfill_durations.py
    ... --limit 20 --sleep 0.15
"""

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

from sqlalchemy import func, select

from canciones.adapters.db.models import SongDB
from canciones.adapters.db.session import SessionLocal, create_tables

_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130 Safari/537.36"


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", (value or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def overlap(a: str, b: str) -> float:
    left = set(normalize(a).split())
    right = set(normalize(b).split())
    if not left or not right:
        return 0
    return len(left & right) / max(len(left), len(right))


def match(candidate_artist: str, candidate_title: str, artist: str, title: str) -> bool:
    artist_ok = (
        overlap(candidate_artist, artist) >= 0.6
        or normalize(artist) in normalize(candidate_artist)
        or normalize(candidate_artist) in normalize(artist)
    )
    title_ok = (
        overlap(candidate_title, title) >= 0.6
        or normalize(candidate_title) == normalize(title)
    )
    return artist_ok and title_ok


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def from_deezer(artist: str, title: str) -> int | None:
    query = urllib.parse.urlencode({"q": f"{artist} {title}", "limit": 5})
    data = get_json(f"https://api.deezer.com/search?{query}")
    for item in data.get("data", []):
        if match(
            item.get("artist", {}).get("name", ""),
            item.get("title", ""),
            artist,
            title,
        ):
            duration = item.get("duration")
            if duration:
                return int(duration)
    return None


def from_itunes(artist: str, title: str) -> int | None:
    query = urllib.parse.urlencode(
        {"term": f"{artist} {title}", "entity": "song", "limit": 5, "country": "ES"}
    )
    data = get_json(f"https://itunes.apple.com/search?{query}")
    for item in data.get("results", []):
        if match(item.get("artistName", ""), item.get("trackName", ""), artist, title):
            millis = item.get("trackTimeMillis")
            if millis:
                return int(millis) // 1000
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="Máximo de canciones a procesar")
    parser.add_argument("--sleep", type=float, default=0.12, help="Pausa entre peticiones")
    args = parser.parse_args()

    create_tables()

    with SessionLocal() as session:
        total = session.execute(
            select(func.count(SongDB.id)).where(SongDB.duration_seconds.is_(None))
        ).scalar_one()
        query = (
            select(SongDB)
            .where(SongDB.duration_seconds.is_(None))
            .order_by(SongDB.id)
        )
        if args.limit:
            query = query.limit(args.limit)
        songs = list(session.scalars(query))

        print(f"Pendientes: {total}. Procesando {len(songs)}…", flush=True)
        found = 0

        for index, song in enumerate(songs, 1):
            seconds = None
            try:
                seconds = from_deezer(song.artist, song.title)
            except Exception:
                seconds = None

            if not seconds:
                try:
                    seconds = from_deezer(song.title, song.artist)
                except Exception:
                    seconds = None

            if not seconds:
                try:
                    seconds = from_itunes(song.artist, song.title)
                except Exception:
                    seconds = None

            if seconds and 10 <= seconds <= 6 * 3600:
                song.duration_seconds = seconds
                found += 1
            else:
                song.duration_seconds = 0  # marca como "consultada, sin resultado"

            if index % 25 == 0:
                session.commit()
            if index % 100 == 0 or index == len(songs):
                session.commit()
                print(
                    f"{index}/{len(songs)} · encontradas {found} · última: "
                    f"{song.artist[:30]} — {song.title[:40]}",
                    flush=True,
                )
            time.sleep(args.sleep)

        session.commit()

        with_duration = session.execute(
            select(func.count(SongDB.id)).where(SongDB.duration_seconds > 0)
        ).scalar_one()
        without = session.execute(
            select(func.count(SongDB.id)).where(SongDB.duration_seconds.is_(None))
        ).scalar_one()
        print(
            f"Listo. Con duración: {with_duration}. Sin consultar: {without}. "
            f"Encontradas en esta pasada: {found}.",
            flush=True,
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
