# Canciones Mas Escuchadas

Track your most played songs via Last.fm scrobbles. Uses [Pano Scrobbler](https://github.com/kawaiiDango/pano-scrobbler) on Android to capture plays from Spotify, YouTube, and YouTube Music — including loops.

---

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -e .
```

### 2. Configure Last.fm

1. Create a free account at [last.fm](https://www.last.fm)
2. Install **Pano Scrobbler** on Android — connect it to your Last.fm account and enable Spotify, YouTube, YouTube Music
3. Create a free API key at [last.fm/api/account/create](https://www.last.fm/api/account/create)
4. Copy `.env.example` to `.env` and fill in your credentials:

```
LASTFM_API_KEY=your_api_key_here
LASTFM_USERNAME=your_lastfm_username
```

### 3. Sync and start

```bash
python -m canciones sync   # import your scrobble history
python -m canciones serve  # start API at http://127.0.0.1:8000
```

---

## CLI

```bash
python -m canciones sync          # fetch new scrobbles from Last.fm
python -m canciones top           # print top 25 songs in terminal
python -m canciones top --limit 50
python -m canciones serve         # start API server
python -m canciones serve --reload
```

---

## API

Swagger UI at `http://127.0.0.1:8000/docs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/sync` | Fetch new scrobbles from Last.fm |
| `GET` | `/api/v1/songs/top` | Top songs by play count |
| `GET` | `/api/v1/artists/top` | Top artists by play count |
| `GET` | `/api/v1/stats` | General stats (plays by month, hour, etc.) |
| `GET` | `/health` | Health check |

All query endpoints accept optional `since`, `until` (ISO datetime), and `limit`/`offset` parameters.
`/songs/top` also accepts `artist` for filtering.

---

## How it works

```
Android (Pano Scrobbler)
  detects plays in Spotify / YouTube / YouTube Music
       |
       v  scrobbles in real time (including loops)
  Last.fm API
       |
       v  python -m canciones sync
  SQLite (songs + plays tables)
       |
       v
  GET /api/v1/songs/top
```

Each `sync` only fetches scrobbles newer than the last run (cursor in `data/lastfm_cursor.json`). Running sync twice in a row imports 0 duplicates.
