# 🎵 Most Listened Songs API

A personal REST API to track and query your most listened songs across YouTube, Spotify, and Last.fm — with accurate play counts, stats, and cross-platform song matching.

---

## Why?

YouTube's watch history only records *when you opened a video*, not how many times it actually played. This app ingests your raw export data, deduplicates it, enriches it with metadata, and gives you a real picture of your listening habits.

---

## Features

- **Multi-platform** — YouTube (Google Takeout), Spotify, Last.fm
- **Google Drive sync** — auto-detects and downloads new Takeout exports
- **Deduplication** — SHA-256 file hash + event-level dedup, safe to re-import
- **Metadata enrichment** — fills in duration, thumbnail, category via YouTube Data API
- **Cross-platform matching** — fuzzy matching to link the same song across platforms
- **Rich stats** — top songs, top artists, plays by month/hour, streaks
- **REST API + Swagger UI** at `/docs`
- **CLI** for all operations

---

## Stack

- **FastAPI** + Uvicorn
- **SQLite** via SQLAlchemy 2.0
- **Alembic** migrations
- **Pydantic v2**
- **rapidfuzz** for song matching
- **Google Drive API** + OAuth2 for automated Takeout sync

---

## Quick Start

```bash
# 1. Clone and install
git clone <repo>
cd canciones-api
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -e .

# 2. Configure
cp .env.example .env
# Add your YOUTUBE_API_KEY to .env (optional, needed for metadata enrichment)

# 3. Start
python -m canciones serve
# API at http://127.0.0.1:8000
# Swagger UI at http://127.0.0.1:8000/docs
```

---

## Importing Your Data

### YouTube (Google Takeout)

1. Go to [takeout.google.com](https://takeout.google.com)
2. Select only **YouTube and YouTube Music → History**
3. Export as **JSON** (faster) or HTML
4. Place the file anywhere and ingest it:

```bash
python -m canciones ingest youtube path/to/historial-de-reproducciones.html
```

Or via API:
```http
POST /api/v1/ingest/youtube
{ "file_path": "data/youtube/watch-history.json" }
```

### Auto-sync from Google Drive

If you configure Google Takeout to export automatically to Google Drive:

```http
POST /api/v1/sync/youtube
```

The app will find the latest Takeout zip, download it, extract the history, and ingest it — skipping anything already imported.

Setup: place `credentials.json` (OAuth2 Desktop app from Google Cloud Console) in the project root. The first call opens a browser login; afterwards it's fully automatic.

### Spotify

Request your data at [spotify.com/account/privacy](https://www.spotify.com/account/privacy), then:

```bash
python -m canciones ingest spotify path/to/StreamingHistory.json
```

### Last.fm

Export your scrobbles from `last.fm/user/USERNAME/library`, then:

```bash
python -m canciones ingest lastfm path/to/scrobbles.csv
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/songs/top` | Top songs (filters: platform, artist, date range, min plays) |
| `GET` | `/api/v1/songs/{id}` | Song detail |
| `GET` | `/api/v1/songs/{id}/history` | Full listening history for a song |
| `GET` | `/api/v1/artists/top` | Top artists |
| `GET` | `/api/v1/stats` | General stats (plays by month, hour, platform) |
| `GET` | `/api/v1/platforms` | Summary per platform |
| `POST` | `/api/v1/ingest/youtube` | Import Google Takeout file |
| `POST` | `/api/v1/ingest/spotify` | Import Spotify export |
| `POST` | `/api/v1/ingest/lastfm` | Import Last.fm CSV export |
| `POST` | `/api/v1/enrich/youtube` | Enrich metadata via YouTube Data API |
| `POST` | `/api/v1/sync/youtube` | Auto-download from Google Drive and ingest |
| `POST` | `/api/v1/songs/link` | Manually link a song to a canonical entry |
| `POST` | `/api/v1/songs/merge` | Merge two canonical songs |
| `GET` | `/api/v1/songs/unmatched` | Songs without a cross-platform match |

---

## CLI

```bash
python -m canciones serve              # Start API server
python -m canciones ingest youtube <file>
python -m canciones ingest spotify <file>
python -m canciones ingest lastfm <file>
python -m canciones enrich youtube     # Enrich with YouTube API metadata
python -m canciones sync youtube       # Sync from Google Drive
python -m canciones top --limit 25    # Print top songs in terminal
```

---

## Data Limitations

**YouTube watch history is not a play counter.** It records each time you *navigated to* a video — not how many times it looped or autoplayed. A song you had on repeat all night counts as 1 play. For accurate counts, use Spotify or set up Last.fm scrobbling going forward.

---

## Project Structure

```
src/canciones/
  domain/          # Models and business logic
  ports/           # Interfaces (Repository, Ingestor, Enricher)
  adapters/
    db/            # SQLite via SQLAlchemy
    youtube/       # Takeout parser + YouTube API enricher
    spotify/       # Spotify export parser
    lastfm/        # Last.fm CSV/JSON parser
    google_drive/  # OAuth2 + Drive sync
  api/             # FastAPI router, schemas, dependencies
```
