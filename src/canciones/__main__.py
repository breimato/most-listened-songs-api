"""CLI entry point: python -m canciones <command>"""

import argparse
import sys

from canciones.adapters.db.repository import CancionesRepository
from canciones.adapters.db.session import SessionLocal, create_tables


def cmd_serve(args):
    import uvicorn
    uvicorn.run("canciones.main:app", host=args.host, port=args.port, reload=args.reload)


def cmd_sync(args):
    create_tables()
    session = SessionLocal()
    repo = CancionesRepository(session)

    try:
        from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor, to_unix_timestamp

        last_played = repo.get_last_played_at()
        from_ts = to_unix_timestamp(last_played) + 1 if last_played else None
        pairs = LastFMAPIIngestor().fetch_recent(from_ts=from_ts)
        imported, skipped = repo.import_scrobbles(pairs)

        session.commit()
        print(f"Imported {imported} scrobbles ({skipped} already known).")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        session.close()


def cmd_dedupe(args):
    create_tables()
    session = SessionLocal()
    repo = CancionesRepository(session)

    try:
        result = repo.merge_duplicate_songs(dry_run=args.dry_run)
        session.commit()
        action = "Se fusionarían" if result.dry_run else "Fusionadas"
        print(
            f"{action} {result.groups_merged} canciones "
            f"({result.songs_removed} filas duplicadas, "
            f"{result.plays_moved} reproducciones movidas)."
        )
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        session.close()


def cmd_top(args):
    create_tables()
    session = SessionLocal()
    repo = CancionesRepository(session)

    try:
        songs = repo.get_top_songs(limit=args.limit)
        if not songs:
            print("No data yet. Run: python -m canciones sync")
            return
        for i, s in enumerate(songs, 1):
            print(f"{i:3d}. {s.title} — {s.artist} ({s.play_count} plays)")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(prog="canciones", description="Canciones Mas Escuchadas")
    sub = parser.add_subparsers(dest="command")

    p_serve = sub.add_parser("serve", help="Start the API server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    p_sync = sub.add_parser("sync", help="Fetch new scrobbles from Last.fm")
    p_sync.set_defaults(func=cmd_sync)

    p_top = sub.add_parser("top", help="Show top songs")
    p_top.add_argument("--limit", type=int, default=25)
    p_top.set_defaults(func=cmd_top)

    p_dedupe = sub.add_parser(
        "dedupe", help="Merge scrobbles that are the same song"
    )
    p_dedupe.add_argument("--dry-run", action="store_true")
    p_dedupe.set_defaults(func=cmd_dedupe)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
