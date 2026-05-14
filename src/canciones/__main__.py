"""CLI entry point: python -m canciones <command>"""

import argparse
import sys

from canciones.adapters.db.repository import SQLiteRepository
from canciones.adapters.db.session import SessionLocal, create_tables
from canciones.domain.models import Play


def cmd_serve(args):
    import uvicorn
    uvicorn.run("canciones.main:app", host=args.host, port=args.port, reload=args.reload)


def cmd_sync(args):
    create_tables()
    session = SessionLocal()
    repo = SQLiteRepository(session)

    try:
        from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

        pairs = LastFMAPIIngestor().fetch_recent()
        imported = 0
        skipped = 0

        for song_data, played_at in pairs:
            existing = repo.get_song_by_platform_id(song_data.platform_id)
            if existing:
                song_id = existing.id
            else:
                song_id = repo.save_song(song_data).id

            if repo.play_exists(song_id, played_at):
                skipped += 1
                continue

            repo.save_play(Play(song_id=song_id, played_at=played_at))
            imported += 1

        session.commit()
        print(f"Imported {imported} scrobbles ({skipped} already known).")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        session.close()


def cmd_top(args):
    create_tables()
    session = SessionLocal()
    repo = SQLiteRepository(session)

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

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
