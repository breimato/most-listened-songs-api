# GroBeats FM — reproductor en directo, marca y tipografía

## Intención

La página deja de presentarse como “Scrobbles” y pasa a ser **GroBeats FM**.
Además del ranking histórico, se comporta como una radio personal: un dock
inferior fijo muestra qué suena ahora, con un vinilo que gira y la portada como
etiqueta. El objetivo es que la web se sienta como una app propia y bonita, no
como un visor de Last.fm.

El motivo es tanto estético como de marca: la página se comparte, y las
referencias visibles a Last.fm y el nombre “Scrobbles” rompen esa sensación de
producto propio.

## Objetivos

- Rebranding completo de la interfaz a **GroBeats FM**.
- Reproductor fijo inferior con vinilo, portada, estado, título, artista y
  tiempo relativo.
- Estado en directo cuando Last.fm reporta una reproducción activa.
- Cuando no hay reproducción activa, mostrar la última escucha de forma
  honesta (“Última escucha · hace X”).
- Nueva tipografía: **Bricolage Grotesque** en titulares + **Instrument Sans**
  en texto y datos.
- Cero menciones visibles a Last.fm, incluyendo toasts, estados vacíos, acceso y
  tarjeta PNG para compartir.
- Comportamiento cuidado en móvil, teclado y `prefers-reduced-motion`.

## No objetivos

- Reproducir audio real o añadir controles de play/pausa.
- Cambiar el pipeline de scrobbles, la base de datos o la lógica de rankings.
- Rediseñar todas las vistas: se cambian tokens, tipografía, marca y se añade
  el reproductor.
- Exponer la API key de Last.fm al navegador.
- Renombrar clases internas, variables de entorno o claves de `localStorage`
  que no se ven.

## Anti-objetivos

- Un falso reproductor con barra de progreso, minutaje o botones que no hacen
  nada.
- Un vinilo girando cuando no hay música sonando.
- Sustituir Last.fm por GroBeats FM solo en algunos textos y dejar otros.
- Romper la tarjeta para compartir, el acceso con llave o el build estático.
- Convertir el dock en un estorbo que tape contenido o la navegación móvil.

## Restricciones

- Frontend React 19 + Vite + TypeScript; backend FastAPI + SQLAlchemy.
- Todas las rutas `/api/v1/*` pasan por `ACCESS_KEY`.
- Last.fm sigue siendo la fuente interna de datos; el navegador nunca habla con
  Last.fm directamente.
- La web se publica como build estático en SiteGround y la API vive en el
  cluster.
- Google Fonts es la fuente de tipografía.
- El reproductor debe funcionar aunque falle Last.fm: la página no puede
  romperse por un endpoint caído.

## Enfoques considerados

### 1. Datos del “ahora suena”

1. **Endpoint en vivo en el backend (elegido).** `GET /api/v1/now-playing`
   consulta Last.fm desde el servidor, distingue `nowplaying` y cae a la última
   escucha. Es el único modo de saber qué suena de verdad sin exponer la API key.
2. **Última escucha de la base de datos (descartado).** El cron sincroniza cada
   15 minutos; el dock llegaría tarde y no podría distinguir “en vivo” de
   “última escucha”.
3. **Llamada directa del navegador a Last.fm (descartado).** Expondría la API
   key y añadiría problemas de CORS.

### 2. Colocación del reproductor

1. **Dock inferior fijo, tipo Spotify (elegido).** Se lee al instante, está
   presente en todas las pestañas y es lo que más se parece a un reproductor.
2. **Tarjeta en la sidebar (descartado).** Solo existe en escritorio y pierde
   protagonismo; en móvil desaparece.
3. **Tarjeta dentro del hero (descartado).** Compite con el nº 1 y desaparece al
   cambiar de pestaña.
4. **Mini-player flotante (descartado).** Tapa contenido y se siente como un
   widget, no como parte de la app.

### 3. Tipografía

1. **Bricolage Grotesque + Instrument Sans (elegido).** Titulares con carácter
   editorial y cuerpo limpio, con buenos números tabulares.
2. **Sora sola (descartado).** Correcta, pero menos contraste y menos
   personalidad.
3. **Space Grotesk (descartado).** Muy vista y menos legible en párrafos largos.
4. **Mantener Figtree (descartado).** No cambia la percepción visual.

## Cómo se construye

### Backend

- Nuevo método en el ingestor de Last.fm:
  `fetch_now_playing() -> NowPlayingTrack | None`.
  - Consulta `user.getRecentTracks` con `limit=2` (sin cursor).
  - Si la primera entrada tiene `@attr.nowplaying`, devuelve la canción con
    `playing=true` y `scrobbled_at=null`.
  - Si no, devuelve la última entrada con fecha, `playing=false`.
  - Si faltan credenciales, devuelve `None` sin lanzar error.
- Nuevo esquema `NowPlayingResponse`:
  - `playing: bool`
  - `track: { title, artist, album, scrobbled_at } | null`
- Nuevo endpoint `GET /api/v1/now-playing`, protegido por la misma dependencia
  de acceso. No escribe en la base de datos.
- Si Last.fm falla, el endpoint responde 502 con un mensaje genérico sin marca
  (“No se pudo consultar el estado de reproducción”). El frontend conserva el
  último dato bueno o oculta el dock si nunca hubo dato.
- `scrobbled_at` se serializa como UTC con offset explícito (`Z` / `+00:00`),
  derivado del `uts` de Last.fm. No se refactorizan en este cambio el resto de
  fechas de la API ni `relativeTime`; el arreglo global de zonas horarias queda
  fuera de alcance.
- Los mensajes que pueden acabar en un toast también forman parte del
  rebranding: sync pasa a “N reproducciones nuevas (M ya conocidas)”, el error
  de servicio pasa a “El servicio de reproducciones no está disponible ahora
  mismo” y la falta de credenciales deja de nombrar variables `LASTFM_*`. El
  404 de recap pasa a “No hay reproducciones en este periodo”.
- Tests: entrada `nowplaying`, última entrada con fecha, ausencia de
  credenciales y endpoint con dependencia simulada.

### Frontend: datos

- Tipos `NowPlaying` y `NowPlayingTrack` en `types/api.ts`.
- `api.getNowPlaying()` en `services/api.ts`.
- `useNowPlaying()` con React Query:
  - `refetchInterval: 30_000`.
  - `staleTime: 15_000`.
  - Sin refresco en segundo plano.
  - `retry: 1`.
  - Mantiene el dato anterior mientras refresca para que el vinilo no
    parpadee.
- Componente `NowPlayingDock` montado en `App` (solo tras el acceso), entre el
  contenido y los modales.
- Política de fallo: si el endpoint falla se mantiene el último dato en
  memoria. Tras 60 s sin ninguna actualización correcta, el dock deja de girar,
  oculta el ecualizador y cambia el estado a “SIN CONEXIÓN”; no se afirma que
  siga sonando. Si el fallo es en la primera carga, el dock no aparece. No se
  persiste el estado en `localStorage`: al recargar se vuelve a consultar.

### Frontend: diseño del dock

- Fijo abajo, alineado a la derecha de la sidebar en escritorio, a todo el ancho
  en móvil.
- Altura ~84 px en escritorio y ~68 px en móvil, por encima de la nav móvil.
- Fondo casi negro translúcido con `backdrop-filter`, línea superior y un lavado
  muy suave de la portada desenfocada.
- Bloque izquierdo: vinilo de ~72 px con surcos concéntricos, brillo, agujero
  central y la portada real como etiqueta. Un brazo fino entra cuando suena y se
  levanta cuando está en pausa.
- Centro: etiqueta de estado (`EN VIVO` con punto pulsante o `ÚLTIMA ESCUCHA`
  con tiempo relativo), título, artista y álbum.
- Derecha: ecualizador de 5 barras animado solo en directo y el tiempo relativo
  (“ahora mismo”, “hace 2 min”) cuando no lo está.
- Estados:
  - Cargando por primera vez: dock discreto con “Conectando con GroBeats FM…”.
  - `playing=true`: vinilo girando, brazo apoyado, `EN VIVO`.
  - `playing=false`: vinilo quieto, brazo levantado, `ÚLTIMA ESCUCHA` + tiempo.
  - Sin datos (`track=null`): “GroBeats FM · Sin reproducción todavía”.
  - Error sin dato previo: no se muestra el dock; la página sigue normal.
- El dock no es un botón ni incluye controles falsos. La portada y el vinilo son
  decorativos (`aria-hidden`); el texto es la fuente de información.
- `role="status"` y `aria-live="polite"` solo envuelven estado, título y artista.
  El tiempo relativo queda fuera de la región viva para que no se anuncie cada
  30 s; solo se anuncia un cambio real de canción o de estado.
- El tiempo relativo se recalcula cada 30 s.
- `prefers-reduced-motion` detiene giro, pulso y ecualizador.

### Frontend: marca

- Sidebar: marca “GroBeats FM” con subtítulo “Tu historial musical”.
- Topbar móvil: “GroBeats FM”.
- Acceso: nombre “GroBeats FM” y subtítulo “Tu historial musical”.
- Título de pestaña: “GroBeats FM — Tus canciones más escuchadas”.
- Meta description: “Tu historial musical, en directo y por temporadas”.
- Hero, estados vacíos, nota de géneros y textos de sincronización sin Last.fm.
- Tarjeta PNG: cabecera “GROBEATS FM” y pie “GroBeats FM”.
- Favicon: mark de vinilo/ecualizador coherente con la marca.
- `DESIGN.md` actualizado con la nueva identidad y el dock.
- Las claves de `localStorage` y los nombres internos se mantienen para no
  invalidar sesiones ni cachés.

### Tipografía

- Google Fonts: Bricolage Grotesque (titulares, 600–800) + Instrument Sans
  (cuerpo, 400–700).
- `--font-display` y `--font-body` en los tokens.
- H1/H2, cifras grandes y marca usan Bricolage; párrafos, listas, controles y
  metadatos usan Instrument Sans.
- La tarjeta para compartir usa Bricolage en titulares y mantiene Instrument
  Sans para etiquetas.
- Se conserva la escala actual; solo cambia la voz tipográfica y se ajusta el
  tracking donde haga falta.

### Ajustes de layout

- `main` gana padding inferior para que el dock no tape la última fila.
- El toast sube por encima del dock y de la nav móvil.
- En móvil, el dock se coloca sobre `.mobile-nav`; ambos comparten el ancho y
  respetan `env(safe-area-inset-bottom)`.
- El dock queda por debajo de modales y toasts, y por encima del contenido.

## Lo que queda a criterio del builder

- Geometría exacta del vinilo, el brazo y los surcos.
- Ritmo y amplitudes del ecualizador.
- Animación de entrada del dock y transición entre estados.
- Copy exacto de los estados vacíos.
- Si en el futuro conviene cachear el endpoint o añadir la canción actual a la
  base de datos; no entra en este cambio.

## Verificación

- `pytest` verde, incluyendo los tests nuevos del endpoint.
- `npm run build` sin errores de TypeScript.
- Revisión visual en escritorio y móvil: dock, vinilo, pausa, sin datos y error.
- `grep` sin “Last.fm” ni “Scrobbles” en textos visibles de `frontend/src`,
  `index.html`, `dist` y en los mensajes de error de la API que se muestran en
  toasts.
- Comprobar que el acceso con llave, la sincronización, los recaps y la tarjeta
  PNG siguen funcionando.
- Comprobar el endpoint real con credenciales: ahora suena y última escucha.
