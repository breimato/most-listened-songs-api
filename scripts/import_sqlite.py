#!/usr/bin/env python3
"""Import the legacy SQLite data (songs + plays) into the configured database.

Usage:
    python scripts/import_sqlite.py --truncate
    DATABASE_URL=postgresql+psycopg://... python scripts/import_sqlite.py --truncate

The script reads the old ``canciones.db`` file directly with sqlite3 and writes
the rows through the application's SQLAlchemy models, so it works against any
supported target (PostgreSQL or SQLite).
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, func, insert, select

from canciones.adapters.db.models import Base, PlayDB, SongDB
from canciones.adapters.db.session import SessionLocal, engine


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _read_sqlite(path: Path) -> tuple[list[dict], list[dict]]:
    if not path.exists():
        raise SystemExit(f"No existe la base de datos SQLite: {path}")

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        songs = [dict(row) for row in connection.execute(
            "SELECT id, platform_id, title, artist, album FROM songs ORDER BY id"
        )]
        plays = [dict(row) for row in connection.execute(
            "SELECT song_id, played_at FROM plays ORDER BY id"
        )]
    finally:
        connection.close()
    return songs, plays


def import_data(sqlite_path: Path, truncate: bool) -> None:
    songs, plays = _read_sqlite(sqlite_path)
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        existing = session.execute(select(func.count(SongDB.id))).scalar() or 0
        if existing and not truncate:
            raise SystemExit(
                f"El destino ya contiene {existing} canciones. "
                "Usa --truncate para reemplazar los datos."
            )
        if truncate:
            session.execute(delete(PlayDB))
            session.execute(delete(SongDB))
            session.flush()

        id_map: dict[int, int] = {}
        for row in songs:
            result = session.execute(
                insert(SongDB)
                .values(
                    platform_id=row["platform_id"],
                    title=row["title"],
                    artist=row["artist"] or "",
                    album=row["album"] or "",
                )
                .returning(SongDB.id)
            )
            id_map[row["id"]] = result.scalar_one()

        play_rows = []
        skipped = 0
        for row in plays:
            new_song_id = id_map.get(row["song_id"])
            if new_song_id is None:
                skipped += 1
                continue
            play_rows.append(
                {
                    "song_id": new_song_id,
                    "played_at": _parse_datetime(row["played_at"]),
                }
            )

        for start in range(0, len(play_rows), 1000):
            session.execute(insert(PlayDB), play_rows[start : start + 1000])

        session.commit()

    print(
        f"Importadas {len(songs)} canciones y {len(play_rows)} reproducciones "
        f"desde {sqlite_path} ({skipped} reproducciones huérfanas ignoradas)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite",
        default="canciones.db",
        help="Ruta al canciones.db de origen (por defecto: ./canciones.db)",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Vacía songs/plays del destino antes de importar",
    )
    args = parser.parse_args()
    import_data(Path(args.sqlite), truncate=args.truncate)


if __name__ == "__main__":
    try:
        main()
    except sqlite3.Error as exc:
        print(f"Error leyendo SQLite: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
