# GroBeats FM — Reproductor en directo y nueva identidad

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Renombrar la app a GroBeats FM, renovar su tipografía y añadir un reproductor inferior con vinilo que muestra la canción en directo o la última escucha.

**Architecture:** El backend expone `GET /api/v1/now-playing`, que consulta Last.fm desde el servidor y devuelve `playing` + `track`, con `scrobbled_at` en UTC. El frontend lo consulta cada 30 s con React Query y lo pinta en un dock fijo. La identidad se centraliza en tokens CSS y en textos de UI, sin tocar claves internas de almacenamiento.

**Tech Stack:** Python 3.12, FastAPI, pytest, React 19, Vite 6, TypeScript, React Query, Vitest, CSS.

**Spec:** `docs/superpowers/specs/2026-11-23-grobeat-fm-player-design.md`

## Global Constraints

- La marca visible es **GroBeats FM**. No debe quedar “Last.fm” ni “Scrobbles” en textos visibles.
- El reproductor no reproduce audio ni muestra controles falsos, progreso o minutaje inventado.
- El estado en directo solo se afirma con `playing=true` y sin más de 60 s de error de conexión.
- `scrobbled_at` del nuevo endpoint se serializa en UTC con offset explícito; no se refactorizan las demás fechas.
- El dock mide 84 px en escritorio y 68 px en móvil, va sobre la nav móvil de 62 px y usa `z-index: 35`.
- La tipografía es Bricolage Grotesque (titulares) + Instrument Sans (texto), desde Google Fonts.
- Se mantienen las claves `localStorage` (`scrobbles:*`) y los nombres internos.
- Cada tarea termina con su test/build en verde y un commit propio.

## Review Focus

- **Fuga de la fuente:** un toast, error de API o tarjeta PNG sigue diciendo Last.fm. Cubierto por los tests de copy de la Task 2 y el grep de la Task 5.
- **Hora incorrecta:** la última escucha se convierte como hora local cuando el backend manda UTC. Cubierto por el test de serialización UTC de la Task 1 y el estado en pausa de la Task 3.
- **Falso directo:** un fallo de red deja el vinilo girando y “EN VIVO” indefinidamente. Cubierto por los tests de `resolveNowPlayingState` de la Task 3.
- **Solape en móvil:** el dock tapa la nav, el último contenido o el toast. Cubierto por la revisión responsive de la Task 6.
- **Región viva ruidosa:** el `aria-live` anuncia el tiempo relativo cada 30 s. Cubierto por la estructura del componente en la Task 3 y la revisión de accesibilidad de la Task 6.

---

### Task 1: Endpoint de canción en directo

**Files:**
- Modify: `src/canciones/domain/models.py`
- Modify: `src/canciones/adapters/lastfm/api_ingestor.py`
- Modify: `src/canciones/api/schemas.py`
- Modify: `src/canciones/api/router.py`
- Create: `tests/test_now_playing.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `settings.lastfm_api_key`, `settings.lastfm_username`, `LastFMAPIIngestor._fetch_page`.
- Produces:
  - `NowPlayingTrack(title: str, artist: str, album: str = "", playing: bool = False, scrobbled_at: datetime | None = None)`
  - `LastFMAPIIngestor.fetch_now_playing() -> NowPlayingTrack | None`
  - `GET /api/v1/now-playing -> {"playing": bool, "track": {"title": str, "artist": str, "album": str, "scrobbled_at": str | null} | null}`

- [ ] **Step 1: Write the failing parser tests**

Create `tests/test_now_playing.py`:

```python
from datetime import datetime, timezone

from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor
from canciones.config import settings
from canciones.domain.models import NowPlayingTrack


def _payload(track: dict) -> dict:
    return {"recenttracks": {"track": [track]}}


def test_fetch_now_playing_returns_live_track(monkeypatch):
    ingestor = LastFMAPIIngestor(api_key="key", username="user")
    monkeypatch.setattr(
        ingestor,
        "_fetch_page",
        lambda **kwargs: _payload(
            {
                "name": "Voto En Blanco",
                "artist": {"#text": "El Jincho"},
                "album": {"#text": "Single"},
                "@attr": {"nowplaying": "true"},
            }
        ),
    )

    track = ingestor.fetch_now_playing()

    assert track == NowPlayingTrack(
        title="Voto En Blanco",
        artist="El Jincho",
        album="Single",
        playing=True,
        scrobbled_at=None,
    )


def test_fetch_now_playing_falls_back_to_last_scrobble(monkeypatch):
    ingestor = LastFMAPIIngestor(api_key="key", username="user")
    monkeypatch.setattr(
        ingestor,
        "_fetch_page",
        lambda **kwargs: _payload(
            {
                "name": "Closer",
                "artist": "Joe Inoue",
                "album": "Closer",
                "date": {"uts": "1795456524"},
            }
        ),
    )

    track = ingestor.fetch_now_playing()

    assert track is not None
    assert track.playing is False
    assert track.scrobbled_at == datetime.fromtimestamp(1795456524, tz=timezone.utc)
    assert track.scrobbled_at.utcoffset() == timezone.utc.utcoffset(None)


def test_fetch_now_playing_without_credentials_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "lastfm_api_key", "")
    monkeypatch.setattr(settings, "lastfm_username", "")

    assert LastFMAPIIngestor().fetch_now_playing() is None
```

- [ ] **Step 2: Run the parser tests and verify they fail**

Run: `pytest tests/test_now_playing.py -v`

Expected: FAIL because `NowPlayingTrack` or `fetch_now_playing` does not exist.

- [ ] **Step 3: Add the dataclass and parser**

In `src/canciones/domain/models.py`, add after `Song`:

```python
@dataclass
class NowPlayingTrack:
    title: str
    artist: str
    album: str = ""
    playing: bool = False
    scrobbled_at: datetime | None = None
```

In `src/canciones/adapters/lastfm/api_ingestor.py`:

- Import `timezone` and `NowPlayingTrack`.
- Add `limit: int = _PAGE_SIZE` to `_fetch_page` and use it in the `limit` param.
- Add `_text(value) -> str` for the `{"#text": ...}` shape.
- Add `_scrobbled_at(entry) -> datetime | None`, using
  `datetime.fromtimestamp(int(uts), tz=timezone.utc)`.
- Implement `fetch_now_playing()`: return `None` without credentials; call
  `_fetch_page(page=1, from_ts=None, limit=2)`; normalize a single dict
  `track` to a list; take the first track; treat
  `str(entry.get("@attr", {}).get("nowplaying", "")).lower() == "true"` as live;
  return `NowPlayingTrack` with `scrobbled_at=None` when live, otherwise the
  parsed UTC timestamp. Return `None` if title or artist is empty.

- [ ] **Step 4: Run the parser tests and verify they pass**

Run: `pytest tests/test_now_playing.py -v`

Expected: PASS.

- [ ] **Step 5: Write the failing endpoint tests**

In `tests/test_api.py`, add imports:

```python
from datetime import datetime, timezone
from urllib.error import URLError

from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor
from canciones.domain.models import NowPlayingTrack
```

Add at the end:

```python
def test_now_playing_endpoint_returns_live_track(client, monkeypatch):
    monkeypatch.setattr(
        LastFMAPIIngestor,
        "fetch_now_playing",
        lambda self: NowPlayingTrack(
            title="Voto En Blanco",
            artist="El Jincho",
            album="Single",
            playing=True,
        ),
    )

    response = client.get("/api/v1/now-playing")

    assert response.status_code == 200
    assert response.json() == {
        "playing": True,
        "track": {
            "title": "Voto En Blanco",
            "artist": "El Jincho",
            "album": "Single",
            "scrobbled_at": None,
        },
    }


def test_now_playing_endpoint_serializes_utc(client, monkeypatch):
    monkeypatch.setattr(
        LastFMAPIIngestor,
        "fetch_now_playing",
        lambda self: NowPlayingTrack(
            title="Closer",
            artist="Joe Inoue",
            album="Closer",
            playing=False,
            scrobbled_at=datetime(2026, 11, 23, 20, 0, tzinfo=timezone.utc),
        ),
    )

    response = client.get("/api/v1/now-playing")

    assert response.status_code == 200
    payload = response.json()
    assert payload["playing"] is False
    assert payload["track"]["scrobbled_at"].startswith("2026-11-23T20:00:00")


def test_now_playing_endpoint_without_credentials_returns_empty(client):
    response = client.get("/api/v1/now-playing")

    assert response.status_code == 200
    assert response.json() == {"playing": False, "track": None}


def test_now_playing_endpoint_handles_service_error(client, monkeypatch):
    def fail(self):
        raise URLError("boom")

    monkeypatch.setattr(LastFMAPIIngestor, "fetch_now_playing", fail)

    response = client.get("/api/v1/now-playing")

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "Last.fm" not in detail
    assert "reproducción" in detail.lower()
```

- [ ] **Step 6: Run the endpoint tests and verify they fail**

Run: `pytest tests/test_api.py -k now_playing -v`

Expected: FAIL with 404 because the route does not exist.

- [ ] **Step 7: Add the schema and route**

In `src/canciones/api/schemas.py`:

```python
class NowPlayingTrackResponse(BaseModel):
    title: str
    artist: str
    album: str
    scrobbled_at: datetime | None


class NowPlayingResponse(BaseModel):
    playing: bool
    track: NowPlayingTrackResponse | None
```

In `src/canciones/api/router.py`, add the schemas to the import and register:

```python
@router.get("/now-playing", response_model=NowPlayingResponse)
def get_now_playing():
    """Canción en directo o última escucha, sin escribir en la base de datos."""
    from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

    try:
        track = LastFMAPIIngestor().fetch_now_playing()
    except (HTTPError, URLError):
        raise HTTPException(
            502,
            "No se pudo consultar el estado de reproducción.",
        )

    if track is None:
        return NowPlayingResponse(playing=False, track=None)

    return NowPlayingResponse(
        playing=track.playing,
        track=NowPlayingTrackResponse(
            title=track.title,
            artist=track.artist,
            album=track.album,
            scrobbled_at=track.scrobbled_at,
        ),
    )
```

- [ ] **Step 8: Run the new tests and the full backend suite**

Run: `pytest tests/test_now_playing.py tests/test_api.py -v`

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add src/canciones/domain/models.py src/canciones/adapters/lastfm/api_ingestor.py src/canciones/api/schemas.py src/canciones/api/router.py tests/test_now_playing.py tests/test_api.py
git commit -m "feat(api): exponer la canción en directo"
```

---

### Task 2: Mensajes visibles sin Last.fm

**Files:**
- Modify: `src/canciones/adapters/lastfm/api_ingestor.py`
- Modify: `src/canciones/api/router.py`
- Modify: `src/canciones/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: the existing `POST /api/v1/sync` and `GET /api/v1/recap`.
- Produces: errors and success messages with no “Last.fm” or `LASTFM_*`, ready to display in a toast.

- [ ] **Step 1: Write the failing copy tests**

In `tests/test_api.py`, replace `test_sync_without_lastfm_credentials` with:

```python
def test_sync_without_credentials_uses_neutral_copy(client):
    response = client.post("/api/v1/sync")

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "LASTFM" not in detail
    assert "Last.fm" not in detail
    assert "credenciales" in detail.lower()


def test_sync_message_is_brand_neutral(client, monkeypatch):
    from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

    monkeypatch.setattr(
        LastFMAPIIngestor,
        "fetch_recent",
        lambda self, from_ts=None: [],
    )

    response = client.post("/api/v1/sync")

    assert response.status_code == 200
    message = response.json()["message"]
    assert "Last.fm" not in message
    assert "reproducciones nuevas" in message


def test_sync_service_error_is_brand_neutral(client, monkeypatch):
    from urllib.error import URLError

    from canciones.adapters.lastfm.api_ingestor import LastFMAPIIngestor

    def fail(self, from_ts=None):
        raise URLError("boom")

    monkeypatch.setattr(LastFMAPIIngestor, "fetch_recent", fail)

    response = client.post("/api/v1/sync")

    assert response.status_code == 502
    assert "Last.fm" not in response.json()["detail"]


def test_recap_empty_period_uses_neutral_copy(client):
    response = client.get("/api/v1/recap")

    assert response.status_code == 404
    assert response.json()["detail"] == "No hay reproducciones en este periodo."
```

- [ ] **Step 2: Run the copy tests and verify they fail**

Run: `pytest tests/test_api.py -k "neutral or credentials" -v`

Expected: FAIL because the current messages name Last.fm and the old env vars.

- [ ] **Step 3: Rewrite the visible messages**

- `api_ingestor.py`: `ValueError("Faltan las credenciales del servicio de reproducciones.")`
- `router.py` sync docstring: `"Fetch new plays and store them."`
- `router.py` sync 502: `HTTPException(502, "El servicio de reproducciones no está disponible ahora mismo.")`
- `router.py` sync success: `message=f"{imported} reproducciones nuevas ({skipped} ya conocidas)."`
- `router.py` recap 404: `HTTPException(404, "No hay reproducciones en este periodo.")`
- `main.py`: `title="GroBeats FM API"` and
  `description="Historial musical y reproducciones en directo."`

Do not change the `LastFMAPIIngestor` class name, env vars, or the ingestor's internal docstrings.

- [ ] **Step 4: Run the copy tests and the full backend suite**

Run: `pytest tests/test_api.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/canciones/adapters/lastfm/api_ingestor.py src/canciones/api/router.py src/canciones/main.py tests/test_api.py
git commit -m "fix(api): quitar Last.fm de los mensajes visibles"
```

---

### Task 3: Dock de reproducción en el frontend

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/hooks/useCanciones.ts`
- Create: `frontend/src/utils/nowPlaying.ts`
- Create: `frontend/src/utils/nowPlaying.test.ts`
- Create: `frontend/src/components/NowPlayingDock.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/index.css`
- Test: `frontend/src/utils/nowPlaying.test.ts`

**Interfaces:**
- Consumes: `GET /api/v1/now-playing` from Task 1.
- Produces:
  - `NowPlaying`, `NowPlayingTrack` types.
  - `api.getNowPlaying(): Promise<NowPlaying>`.
  - `useNowPlaying()` React Query hook.
  - `resolveNowPlayingState(data, isLoading, isError, dataUpdatedAt, now): 'loading' | 'live' | 'paused' | 'stale' | 'idle'`.
  - `<NowPlayingDock />` mounted once in `App`.

- [ ] **Step 1: Add Vitest and write the failing state tests**

Run: `npm install -D vitest@^3.0.0` in `frontend/`.
Add to `frontend/package.json` scripts: `"test": "vitest run"`.

Create `frontend/src/utils/nowPlaying.test.ts`:

```ts
import { describe, expect, it } from 'vitest'

import { resolveNowPlayingState } from './nowPlaying'

const live = {
  playing: true,
  track: {
    title: 'Voto En Blanco',
    artist: 'El Jincho',
    album: 'Single',
    scrobbled_at: null,
  },
}

const paused = {
  playing: false,
  track: {
    title: 'Closer',
    artist: 'Joe Inoue',
    album: 'Closer',
    scrobbled_at: '2026-11-23T20:00:00Z',
  },
}

describe('resolveNowPlayingState', () => {
  it('paints loading before the first response', () => {
    expect(resolveNowPlayingState(undefined, true, false, 0, 1_000)).toBe(
      'loading',
    )
  })

  it('paints live while playing', () => {
    expect(resolveNowPlayingState(live, false, false, 1_000, 1_500)).toBe(
      'live',
    )
  })

  it('paints paused with a last scrobble', () => {
    expect(resolveNowPlayingState(paused, false, false, 1_000, 1_500)).toBe(
      'paused',
    )
  })

  it('paints idle without a track', () => {
    expect(
      resolveNowPlayingState(
        { playing: false, track: null },
        false,
        false,
        1_000,
        1_500,
      ),
    ).toBe('idle')
  })

  it('paints stale after 60 seconds without a successful update', () => {
    expect(
      resolveNowPlayingState(live, false, true, 1_000, 61_001),
    ).toBe('stale')
  })

  it('keeps the current state during the first minute of an error', () => {
    expect(
      resolveNowPlayingState(live, false, true, 1_000, 30_000),
    ).toBe('live')
  })
})
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `npm test -- src/utils/nowPlaying.test.ts` in `frontend/`.

Expected: FAIL because `nowPlaying.ts` does not exist.

- [ ] **Step 3: Add the types and implement the state resolver**

In `frontend/src/types/api.ts`, add:

```ts
export interface NowPlayingTrack {
  title: string
  artist: string
  album: string
  scrobbled_at: string | null
}

export interface NowPlaying {
  playing: boolean
  track: NowPlayingTrack | null
}
```

Create `frontend/src/utils/nowPlaying.ts`:

```ts
import type { NowPlaying } from '../types/api'

export type NowPlayingState = 'loading' | 'live' | 'paused' | 'stale' | 'idle'

export function resolveNowPlayingState(
  data: NowPlaying | undefined,
  isLoading: boolean,
  isError: boolean,
  dataUpdatedAt: number,
  now: number,
): NowPlayingState {
  if (isLoading && !data) return 'loading'
  if (isError && data && dataUpdatedAt > 0 && now - dataUpdatedAt > 60_000) {
    return 'stale'
  }
  if (data?.playing && data.track) return 'live'
  if (data?.track) return 'paused'
  return 'idle'
}
```

- [ ] **Step 4: Run the state tests and verify they pass**

Run: `npm test -- src/utils/nowPlaying.test.ts`

Expected: PASS.

- [ ] **Step 5: Add the API method and hook**

In `frontend/src/services/api.ts`, import `NowPlaying` and add:

```ts
getNowPlaying() {
  return request<NowPlaying>('/now-playing')
},
```

In `frontend/src/hooks/useCanciones.ts`, add:

```ts
export function useNowPlaying() {
  return useQuery({
    queryKey: ['now-playing'],
    queryFn: api.getNowPlaying,
    refetchInterval: 30_000,
    staleTime: 15_000,
    retry: 1,
  })
}
```

- [ ] **Step 6: Create the dock component**

Create `frontend/src/components/NowPlayingDock.tsx` with this contract:

- No props; it calls `useNowPlaying()`, `useArtwork(track?.artist ?? '', track?.title ?? '')` and a local 30 s tick.
- State comes from `resolveNowPlayingState`.
- Return `null` when `isError && !data`; otherwise render a `<section className={`now-playing is-${state}`} aria-label="Reproductor de GroBeats FM">`.
- Layout order: blurred cover wash, vinyl block, center copy, right side.
- Vinyl block: `now-playing__vinyl` > `now-playing__record` (cover as `CoverArt size="sm" round`) + `now-playing__arm` (inline SVG). Add a centered `now-playing__mark` (four bars) when there is no cover.
- Center copy: a `now-playing__live` wrapper with `role="status"` and `aria-live="polite"` containing only the state label, title and artist. The album and relative time stay outside.
- State labels: `EN VIVO`, `ÚLTIMA ESCUCHA`, `SIN CONEXIÓN`, `CONECTANDO`, `GROBEATS FM`.
- Titles: the real title; `Conectando con GroBeats FM…` while loading; `Sin reproducción todavía` when idle.
- Artist: real artist; `Buscando tu última canción` while loading; `Tu historial musical` when idle.
- Right side: the existing `.eq` markup with five `<i>` bars, `aria-hidden`, and a `now-playing__time` outside the live region. Time: `Ahora` when live, `relativeTime(scrobbled_at)` when paused, `Sin conexión` when stale, `—` otherwise.
- Use `dataUpdatedAt` and the 30 s tick to detect staleness; do not add local persistence.
- Decorative elements use `aria-hidden`; there are no buttons and no fake controls.

- [ ] **Step 7: Mount the dock and add the styles**

In `frontend/src/App.tsx`, import `NowPlayingDock` and mount `<NowPlayingDock />` after `</div>` that closes `.workspace`, before the modals.

In `frontend/src/index.css`:

- Add `--now-playing-h: 84px` and `--mobile-nav-h: 62px` to `:root`.
- Add `.now-playing`, `.now-playing__wash`, `__inner`, `__vinyl`, `__record`, `__arm`, `__mark`, `__copy`, `__live`, `__state`, `__state-dot`, `__title`, `__artist`, `__album`, `__side`, `__eq`, `__time`.
- `.now-playing` is `position: fixed; left: var(--sidebar-w); right: 0; bottom: 0; height: var(--now-playing-h); z-index: 35;` with translucent dark background, top hairline and blur.
- `.now-playing__inner` aligns to `width: min(1180px, 100%); margin: 0 auto; padding: 0 36px;` and uses a 72 px / 1fr / auto grid.
- Record: 72 px, concentric groove gradients, 44 px round cover label, center hole. Spin with `vinylSpin` only under `.now-playing.is-live`.
- Tonearm: inline SVG positioned top-right of the vinyl, rotated toward the record when live and lifted when paused, with a 0.5 s transition.
- Wash: blurred cover image at low opacity behind the dock.
- Equalizer: reuse `.eq`, animate only under `.is-live`; dim and pause otherwise.
- Add `@media (max-width: 980px)`: `--mobile-nav-h: calc(62px + env(safe-area-inset-bottom))`, dock `left: 0; bottom: var(--mobile-nav-h);`; `.main` bottom padding includes dock + nav.
- Add `@media (max-width: 760px)`: `--now-playing-h: 68px`, 64 px record, 10 px padding, hide `.now-playing__album`, reduce padding to 16 px, allow truncation on title/artist.
- Add `@media (max-width: 520px)`: hide the vinyl's tonearm if needed, shrink the time text, keep the title visible.
- Raise `.main` bottom padding to clear the dock; raise `.toast` bottom above dock and nav.
- In `@media (prefers-reduced-motion: reduce)`, disable the vinyl and equalizer animations explicitly.
- Ensure `min-width: 0` and `text-overflow: ellipsis` on title and artist.

- [ ] **Step 8: Run the frontend tests and build**

Run: `npm test` and `npm run build` in `frontend/`.

Expected: all tests pass and TypeScript + Vite build succeeds.

- [ ] **Step 9: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/types/api.ts frontend/src/services/api.ts frontend/src/hooks/useCanciones.ts frontend/src/utils/nowPlaying.ts frontend/src/utils/nowPlaying.test.ts frontend/src/components/NowPlayingDock.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat(frontend): añadir reproductor de vinilo en directo"
```

---

### Task 4: Nueva tipografía

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/utils/shareCard.ts`
- Modify: `frontend/DESIGN.md`
- Test: `frontend` build + visual check.

**Interfaces:**
- Consumes: Google Fonts.
- Produces: `--font-display`, `--font-body` and font loading for the UI and the PNG share card.

- [ ] **Step 1: Load the fonts**

In `frontend/index.html`, replace the Figtree link with:

```html
<link
  href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Instrument+Sans:wght@400..700&display=swap"
  rel="stylesheet"
/>
```

- [ ] **Step 2: Add font tokens and display selectors**

In `frontend/src/index.css`:

```css
--font-display: 'Bricolage Grotesque', 'Segoe UI', system-ui, sans-serif;
--font-body: 'Instrument Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
--font: var(--font-body);
```

Add, after the base element rules:

```css
h1, h2, h3, h4,
.brand__name,
.topbar__name,
.gate__name,
.now-playing__title {
  font-family: var(--font-display);
}
```

Keep the current sizes, line heights and letter spacing. Do not change body
copy to the display font.

- [ ] **Step 3: Use both families in the share card**

In `frontend/src/utils/shareCard.ts`:

- Replace `const FONT = 'Figtree, sans-serif'` with
  `const DISPLAY_FONT = "'Bricolage Grotesque', sans-serif"` and
  `const BODY_FONT = "'Instrument Sans', sans-serif"`.
- Use `DISPLAY_FONT` for the big headers, period title, song title, artist
  name, hours and profile/large numbers.
- Use `BODY_FONT` for small labels, metadata, plays, footer and the
  “DE MÚSICA”-style captions.
- Change the one `900` weight to `800` so it exists in Bricolage.
- Keep `await document.fonts.ready` before drawing.

- [ ] **Step 4: Update the design system typography**

In `frontend/DESIGN.md`, replace the single-family Figtree description with
Bricolage Grotesque for display and Instrument Sans for body, noting that
numbers stay tabular and the scale does not change.

- [ ] **Step 5: Build and review**

Run: `npm run build` in `frontend/`.

Expected: build succeeds. Check in the browser that the H1, section titles,
brand and dock title use Bricolage, and that body text and numbers are
Instrument Sans with no layout overflow.

- [ ] **Step 6: Commit**

```bash
git add frontend/index.html frontend/src/index.css frontend/src/utils/shareCard.ts frontend/DESIGN.md
git commit -m "style(frontend): renovar la tipografía"
```

---

### Task 5: Rebranding completo a GroBeats FM

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/components/TopBar.tsx`
- Modify: `frontend/src/components/AccessGate.tsx`
- Modify: `frontend/src/components/Hero.tsx`
- Modify: `frontend/src/components/SongList.tsx`
- Modify: `frontend/src/components/ArtistList.tsx`
- Modify: `frontend/src/components/RecapModal.tsx`
- Modify: `frontend/src/utils/shareCard.ts`
- Modify: `frontend/public/favicon.svg`
- Modify: `frontend/DESIGN.md`
- Modify: `frontend/PRODUCT.md`
- Test: build + grep.

**Interfaces:**
- Consumes: the brand name and the copy approved in the spec.
- Produces: zero visible “Last.fm” / “Scrobbles” strings.

- [ ] **Step 1: Replace the visible copy**

Use these exact strings:

- `index.html` title: `GroBeats FM — Tus canciones más escuchadas`
- `index.html` description: `Tu historial musical, en directo y por temporadas.`
- Sidebar: name `GroBeats FM`, sub `Tu historial musical`.
- TopBar: name `GroBeats FM`.
- AccessGate: name `GroBeats FM`, sub `Tu historial musical`.
- Hero fallback hint: `Tu historial musical, al día.`
- Hero empty copy: `Sincroniza tu historial para importar tus reproducciones.`
- SongList empty: `Sincroniza tu historial para importar tus reproducciones.`
- ArtistList empty: `Prueba con otro año o vuelve a sincronizar.`
- RecapModal genre note: `Según los tags de tus artistas.`
- Share card header: `GROBEATS FM`.
- Share card footer right: `GroBeats FM`.
- Keep `breimato.es/youtube` as the footer URL.

- [ ] **Step 2: Replace the favicon**

Replace `frontend/public/favicon.svg` with a vinyl mark:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0a0a0b"/>
  <circle cx="32" cy="32" r="21" fill="none" stroke="#1ed760" stroke-width="2.5"/>
  <circle cx="32" cy="32" r="14.5" fill="none" stroke="#1ed760" stroke-width="1" opacity=".4"/>
  <circle cx="32" cy="32" r="4.5" fill="#1ed760"/>
  <path d="M14 26a21 21 0 0 1 14-12" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".55"/>
</svg>
```

- [ ] **Step 3: Update the design and product docs**

In `frontend/DESIGN.md`:

- Title: `# Design System — GroBeats FM`.
- Direction: a live personal listening room, with the vinyl dock as the signature.
- Components: add **NowPlayingDock** with live/paused/stale states.
- Keep the existing color, shape and movement rules.

In `frontend/PRODUCT.md`:

- Name the product GroBeats FM in the purpose.
- Clarify that it shows what is playing but does not play audio.
- Update the brand commitments to mention the vinyl dock and the new type
  pairing.

- [ ] **Step 4: Build and grep for leaks**

Run in `frontend/`: `npm run build`.

Then run from the repo root:

```bash
grep -rn "Last.fm" frontend/src frontend/index.html frontend/dist || true
grep -rn "Scrobbles" frontend/src frontend/index.html frontend/dist || true
grep -rn "Last.fm" src/canciones/api || true
```

Expected: no output from the first two; the third must not find user-visible
messages (internal docstrings are out of scope).

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/src/components/Sidebar.tsx frontend/src/components/TopBar.tsx frontend/src/components/AccessGate.tsx frontend/src/components/Hero.tsx frontend/src/components/SongList.tsx frontend/src/components/ArtistList.tsx frontend/src/components/RecapModal.tsx frontend/src/utils/shareCard.ts frontend/public/favicon.svg frontend/DESIGN.md frontend/PRODUCT.md
git commit -m "feat(frontend): rebrandear la app como GroBeats FM"
```

---

### Task 6: Verificación final

**Files:**
- No production files expected. Fix anything this task uncovers and include it in the final commit.

**Interfaces:**
- Consumes: all previous tasks.
- Produces: evidence that the backend, frontend, responsive layout and live states work.

- [ ] **Step 1: Run the automated suites**

```bash
pytest
cd frontend && npm test && npm run build
```

Expected: pytest green; Vitest green; build green.

- [ ] **Step 2: Start the app locally**

Run in separate background shells:

```bash
ACCESS_KEY= .venv/bin/python -m canciones serve
cd frontend && npm run dev
```

`ACCESS_KEY=` disables auth only for this local check. Open
`http://127.0.0.1:5173` in the browser and seed any key from the console:

```js
localStorage.setItem('scrobbles:access-key', 'demo')
location.reload()
```

- [ ] **Step 3: Check the real endpoint**

```bash
curl -s http://127.0.0.1:8000/api/v1/now-playing
```

Expected: `{"playing": false, "track": {...}}` with the last scrobble, or
`"playing": true` if something is playing. `scrobbled_at` must end in `Z` or
`+00:00`.

- [ ] **Step 4: Review desktop**

- The dock is visible at the bottom, aligned to the right of the sidebar.
- The vinyl is static with the last scrobble, status `ÚLTIMA ESCUCHA`.
- The relative time is plausible for the real scrobble.
- The last content row and the toast are not hidden by the dock.
- Clicking tabs does not unmount or break the dock.
- No console errors.
- The title, brand and headings use Bricolage; body copy uses Instrument Sans.
- Take a screenshot for the final report.

- [ ] **Step 5: Review live and stale visuals**

In the browser console:

```js
const dock = document.querySelector('.now-playing')
dock.classList.add('is-live')
```

Check the vinyl spins, the arm lowers and the equalizer animates. Remove the
class afterwards. Then check the stale copy path by reviewing that the
component shows `SIN CONEXIÓN` after the state resolver returns `stale`
(covered by the Vitest test); do not fake data in a screenshot.

- [ ] **Step 6: Review mobile**

Resize the browser window to 390 px wide if the browser tool allows it. If
not, use the 980 px and 760 px media rules plus a narrow screenshot as
evidence. Verify:

- The dock sits above the 62 px mobile nav.
- The vinyl, title and artist fit; the album is hidden.
- The toast has room above the dock.
- No horizontal scroll.
- The dock is not covered by the nav.

- [ ] **Step 7: Review accessibility**

- Run the browser accessibility snapshot or Lighthouse.
- Confirm the vinyl and equalizer are `aria-hidden`.
- Confirm the live region contains only state, title and artist, not the
  relative time.
- Confirm `prefers-reduced-motion` stops the spin, the pulse and the
  equalizer.
- Confirm there are no buttons or fake controls in the dock.

- [ ] **Step 8: Final grep and status**

```bash
grep -rn "Last.fm" frontend/src frontend/index.html frontend/dist || true
grep -rn "Scrobbles" frontend/src frontend/index.html frontend/dist || true
git status --short
```

Expected: no visible brand leaks and only intended changes. `opencode.json`
may appear as pre-existing untracked work; do not add it.

- [ ] **Step 9: Commit any verification fixes**

If this task required changes, stage only the touched tracked files:

```bash
git add -u
git commit -m "fix: ajustes de verificación de GroBeats FM"
```

Add any new file by explicit path. If nothing changed, no commit is needed.
