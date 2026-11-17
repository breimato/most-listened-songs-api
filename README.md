# Canciones Mas Escuchadas

Track your most played songs via Last.fm scrobbles. Uses [Pano Scrobbler](https://github.com/kawaiiDango/pano-scrobbler) on Android to capture plays from Spotify, YouTube, and YouTube Music — including loops.

> Solo se usan **Pano Scrobbler** y **Last.fm**. La app no llama a la API de YouTube ni necesita credenciales de Google (`YOUTUBE_API_KEY`, `GOOGLE_CLIENT_ID`… ya no se usan).

---

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -e .
```

### 1b. Base de datos con Docker (PostgreSQL)

```bash
docker compose up -d       # PostgreSQL en localhost:5433 + API en localhost:8000
```

Para importar el histórico del antiguo `canciones.db`:

```bash
DATABASE_URL='postgresql+psycopg://canciones_user:canciones_pass@localhost:5433/canciones_db' \
  .venv/bin/python scripts/import_sqlite.py --truncate
```

Sin Docker, el proyecto sigue funcionando con SQLite (`DATABASE_URL=sqlite:///canciones.db`).

### 2. Configure Last.fm

1. Create a free account at [last.fm](https://www.last.fm)
2. Install **Pano Scrobbler** on Android — connect it to your Last.fm account and enable Spotify, YouTube, YouTube Music
3. Create a free API key at [last.fm/api/account/create](https://www.last.fm/api/account/create)
4. Copy `.env.example` to `.env` and fill in your credentials:

```
LASTFM_API_KEY=your_api_key_here
LASTFM_USERNAME=your_lastfm_username
```

No hace falta configurar nada de YouTube ni de Google: Pano Scrobbler ya envía las reproducciones a Last.fm y la app solo lee de ahí.

### 3. Sync and start

```bash
python -m canciones sync   # import your scrobble history
python -m canciones serve  # start API at http://127.0.0.1:8000
```

### 4. Frontend (opcional)

```bash
cd frontend
npm install
npm run dev   # http://127.0.0.1:5173
```

El frontend hace proxy de la API al backend en el puerto 8000. Necesitas tener ambos en marcha.

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
| `GET` | `/api/v1/obsessions` | Épocas de obsesión y rachas detectadas |
| `GET` | `/api/v1/songs/{id}/timeline` | Historial diario de una canción y sus episodios |
| `GET` | `/api/v1/recap?since=&until=` | Recap tipo Wrapped del periodo |
| `GET` | `/api/v1/artwork?artist=&title=` | Carátula resuelta en el servidor (Deezer) |
| `GET` | `/health` | Health check |

All query endpoints accept optional `since`, `until` (ISO datetime), and `limit`/`offset` parameters.
`/songs/top` also accepts `artist` for filtering.

### Obsesiones

Una **obsesión** es una ventana de 7 días con al menos 5 días de 2+ reproducciones
(y 14 plays), o de 14 días con al menos 10 días fuertes (y 28 plays). Las
**rachas** son la versión corta: 4 días fuertes en 7 o 7 en 14. Los picos de un
solo día (loops) no cuentan por sí solos. Todo se agrupa por día en
`Europe/Madrid` y las versiones de una misma canción se suman.

- `GET /api/v1/obsessions?since=&until=&tier=all|obsesion|racha`
- `GET /api/v1/songs/{id}/timeline?since=&until`

### Recap tipo Wrapped

`GET /api/v1/recap?since=&until=` devuelve, para cualquier periodo:

- **Horas de música** (a partir de la duración de cada canción) y cobertura de duraciones.
- Reproducciones, artistas, canciones y álbumes únicos.
- **Días con música**, **racha más larga**, día y hora con más escuchas.
- **Top 5 canciones**, **top 5 artistas** y **top 5 álbumes**, con plays y minutos.
- **Tu canción del periodo**: días que la escuchaste y racha máxima seguida.
- **Géneros** aproximados a partir de los tags de artista de Last.fm.
- **Perfil de escucha** (Nocturno, Loopero, Explorador, Constante…).
- **Primera y última canción**, **obsesión del periodo** y **artista nº1 de cada mes**.

Las duraciones se enriquecen una vez con:

```bash
DATABASE_URL='postgresql+psycopg://...' python scripts/backfill_durations.py
```

Las canciones sin duración conocida no se inventan: el total de horas se
extrapola con la duración media de las reproducciones conocidas y la UI lo
marca con `≈` y el porcentaje de cobertura.

No se incluyen datos que la app no tiene: edad musical (años de lanzamiento),
Sound Town, percentiles globales, podcasts/audiolibros ni clips de artistas.

### Acceso

Todas las rutas `/api/v1/*` exigen la llave compartida `ACCESS_KEY` (en `.env`):

```
Authorization: Bearer <ACCESS_KEY>
```

Sin la llave devuelven `401`. `/health` queda público para las probes. La web
pide la llave al entrar y la guarda en el navegador; el CronJob de Kubernetes
la lee del Secret `access-key`. Si `ACCESS_KEY` está vacía, la autenticación se
desactiva (solo para desarrollo local).

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

Each `sync` only fetches scrobbles newer than the last stored play (the cursor is `MAX(plays.played_at)` in the database, so it works across containers). Running sync twice in a row imports 0 duplicates.

---

## Frontend

Interfaz web en `frontend/` (React + Vite + TypeScript):

- **Top canciones** con ranking, portadas reales (iTunes) y filtro por artista
- **Top artistas** con podio de vinilos y ranking completo
- **Actividad** con gráficos por mes y por hora
- **Recaps de temporada** (verano, otoño, invierno, primavera y año) con notificaciones in-app y copia del resumen
- **Recap tipo Wrapped**: horas, días, rachas, top canciones/artistas/álbumes, géneros, perfil y momentos
- **Obsesiones y rachas** con timeline diario y calendario de calor por canción
- Botón **Sincronizar Last.fm** que llama a `POST /api/v1/sync`
- Filtros por cantidad (top 10/25/50/100) y por año

```bash
cd frontend
npm install
npm run dev      # desarrollo
npm run build    # build de producción en frontend/dist
```

---

## Despliegue

| Pieza | Dónde |
|-------|-------|
| API + PostgreSQL | Kubernetes (namespace `youtube`), imagen `ghcr.io/breimato/most-listened-songs-api` |
| Frontend | SiteGround: https://breimato.es/youtube |
| Acceso público a la API | Quick tunnel de Cloudflare -> Traefik -> `youtube.home.arpa` |

### Kubernetes (Flux)

Los manifiestos viven en `breimato/cluster-config` (`apps/youtube` y `clusters/fedora-brei/youtube.yaml`). El workflow de GitHub Actions construye la imagen, la publica en GHCR y actualiza el tag en `cluster-config` con el secret `DEPLOY_REPO_TOKEN` (ya configurado). Flux aplica el cambio en el cluster.

Un CronJob del cluster llama a `POST /api/v1/sync` cada 15 minutos, así que los scrobbles nuevos aparecen solos (Last.fm puede tardar unos minutos en procesarlos).

Crear los Secrets una vez (requiere acceso `kubectl`):

```bash
cd cluster-config
./apps/youtube/install-secrets.sh
```

### Frontend (FTP)

```bash
cd frontend
npm install
npm run deploy:ftp           # build + subida a breimato.es/public_html/youtube
npm run upload:runtime -- https://<tunel>.trycloudflare.com
```

La URL del túnel se publica en `https://breimato.es/youtube/runtime-config.json` para no tener que reconstruir el frontend cuando cambia.

### Quick tunnel

`deploy/quick-tunnel/install.sh` instala dos servicios de usuario systemd:

- `youtube-quick-tunnel.service`: cloudflared contra `http://127.0.0.1:80` con `Host: youtube.home.arpa`.
- `youtube-quick-runtime.service`: espera la URL nueva, verifica `/health` + CORS desde `https://breimato.es` y sube `runtime-config.json` por FTP.

La URL cambia en cada reinicio del túnel; el segundo servicio la republica automáticamente.

