"""CLI entry point: python -m canciones <command>"""

import argparse
import sys

from canciones.adapters.db.repository import SQLiteRepository
from canciones.adapters.db.session import SessionLocal, create_tables
from canciones.domain.models import Platform


def cmd_serve(args):
    import uvicorn
    uvicorn.run("canciones.main:app", host=args.host, port=args.port, reload=args.reload)


def cmd_ingest(args):
    create_tables()
    session = SessionLocal()
    repo = SQLiteRepository(session)

    try:
        if args.platform == "youtube":
            from canciones.adapters.youtube.takeout_parser import YouTubeTakeoutParser
            from canciones.api.router import _ingest
            result = _ingest(args.file, Platform.YOUTUBE, YouTubeTakeoutParser(), repo)
        elif args.platform == "spotify":
            from canciones.adapters.spotify.export_parser import SpotifyExportParser
            from canciones.api.router import _ingest
            result = _ingest(args.file, Platform.SPOTIFY, SpotifyExportParser(), repo)
        elif args.platform == "lastfm":
            from canciones.adapters.lastfm.export_parser import LastFMExportParser
            from canciones.api.router import _ingest
            result = _ingest(args.file, Platform.LASTFM, LastFMExportParser(), repo)
        else:
            print(f"Unknown platform: {args.platform}")
            sys.exit(1)

        session.commit()
        print(result.message)
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        session.close()


def cmd_enrich(args):
    create_tables()
    session = SessionLocal()
    repo = SQLiteRepository(session)

    try:
        if args.platform == "youtube":
            from canciones.adapters.youtube.api_enricher import YouTubeAPIEnricher
            enricher = YouTubeAPIEnricher()
            songs = repo.get_platform_songs_needing_enrichment(Platform.YOUTUBE)
            if not songs:
                print("No songs need enrichment.")
                return
            enricher.enrich(songs)
            for song in songs:
                repo.update_platform_song(song)
            session.commit()
            print(f"Enriched {len(songs)} songs.")
        else:
            print(f"Enrichment not supported for: {args.platform}")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        session.close()


def cmd_sync(args):
    create_tables()
    session = SessionLocal()
    repo = SQLiteRepository(session)

    try:
        if args.platform == "lastfm":
            from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

            ingestor = LastFMAPIIngestor()
            pairs = ingestor.fetch_recent()

            events_imported = 0
            events_skipped = 0
            songs_new = 0

            for song_data, event_data in pairs:
                existing = repo.get_platform_song_by_platform_id(
                    song_data.platform, song_data.platform_id
                )
                if existing:
                    platform_song_id = existing.id
                else:
                    saved = repo.save_platform_song(song_data)
                    platform_song_id = saved.id
                    songs_new += 1

                if repo.event_exists(platform_song_id, event_data.listened_at):
                    events_skipped += 1
                    continue

                event_data.platform_song_id = platform_song_id
                repo.save_listening_event(event_data)
                events_imported += 1

            session.commit()
            print(
                f"Imported {events_imported} scrobbles from Last.fm "
                f"({songs_new} new songs, {events_skipped} duplicates skipped)."
            )
        else:
            from canciones.adapters.google_drive.drive_sync import GoogleDriveSync
            from canciones.adapters.youtube.takeout_parser import YouTubeTakeoutParser
            from canciones.api.router import _ingest
            from canciones.config import settings
            from pathlib import Path

            drive = GoogleDriveSync()
            files = drive.find_takeout_files()
            if not files:
                print("No Takeout files found in Google Drive.")
                return

            dest_dir = str(Path(settings.data_dir) / "youtube")
            extracted = drive.download_and_extract(files[0]["id"], dest_dir)
            if not extracted:
                print("No watch-history found in downloaded file.")
                return

            result = _ingest(extracted, Platform.YOUTUBE, YouTubeTakeoutParser(), repo)
            session.commit()
            print(result.message)
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
        plat = Platform(args.platform) if args.platform else None
        stats = repo.get_top_songs(limit=args.limit, platform=plat)
        for i, s in enumerate(stats, 1):
            artist = s.artist or s.channel
            print(f"{i:3d}. {s.title} — {artist} ({s.play_count} plays)")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(prog="canciones", description="Canciones Mas Escuchadas")
    sub = parser.add_subparsers(dest="command")

    # serve
    p_serve = sub.add_parser("serve", help="Start the API server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    # ingest
    p_ingest = sub.add_parser("ingest", help="Import listening history")
    p_ingest.add_argument("platform", choices=["youtube", "spotify", "lastfm"])
    p_ingest.add_argument("file", help="Path to the export file")
    p_ingest.set_defaults(func=cmd_ingest)

    # enrich
    p_enrich = sub.add_parser("enrich", help="Enrich songs with API metadata")
    p_enrich.add_argument("platform", choices=["youtube"])
    p_enrich.set_defaults(func=cmd_enrich)

    # sync
    p_sync = sub.add_parser("sync", help="Sync from Google Drive")
    p_sync.add_argument("platform", choices=["youtube", "lastfm"])
    p_sync.set_defaults(func=cmd_sync)

    # top
    p_top = sub.add_parser("top", help="Show top songs")
    p_top.add_argument("--limit", type=int, default=25)
    p_top.add_argument("--platform", choices=["youtube", "spotify", "lastfm"])
    p_top.set_defaults(func=cmd_top)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
