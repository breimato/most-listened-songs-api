# Design System — Scrobbles

## Direction

Una sala de escucha personal inspirada en Spotify: fondo casi negro, sidebar
propia, carátulas protagonistas y un único verde que señala lo importante. La
identidad propia son los recaps de temporada, no una copia del reproductor.

## Tokens

### Color

| Token | Valor | Uso |
|-------|-------|-----|
| `--bg` | `#0a0a0b` | Fondo de la aplicación |
| `--bg-deep` | `#000` | Sidebar |
| `--bg-elevated` | `#121214` | Controles, tarjetas, modales |
| `--bg-raised` | `#161618` | Popovers y toasts |
| `--bg-hover` | `#1c1c1f` | Hover de filas |
| `--line` | `rgba(255,255,255,.09)` | Hairlines |
| `--line-strong` | `rgba(255,255,255,.16)` | Bordes de foco/controles |
| `--text` | `#f5f5f2` | Texto principal |
| `--text-dim` | `#a3a39e` | Texto secundario |
| `--text-faint` | `#8b8b84` | Metadatos y etiquetas |
| `--green` | `#1ed760` | Acento único: ranking, foco, CTA |
| `--green-bright` | `#1fdf64` | Hover del CTA |
| `--green-deep` | `#0b6b2f` | Gradiente de barras |
| `--green-ink` | `#04160a` | Texto sobre verde |
| `--error` | `#ff6b6b` | Errores |

Temporadas: verano `#ff9f43 → #ff5e62`, otoño `#d97a37 → #8a3d1f`,
invierno `#5b8def → #25346b`, primavera `#3ddc84 → #0f7a43`, año
`#1ed760 → #0a5c2b`.

### Tipografía

- Familia única: **Figtree** (Google Fonts), pesos 400–900.
- H1: `clamp(2.35rem, 4.2vw, 3.75rem)`, 800, `letter-spacing: -0.045em`, `line-height: .98`.
- H2: 21px / 800 / -0.03em; H3 16px / 700.
- Cuerpo 15px; secundario 12–14px; etiquetas 10–11px con tracking `.12em` en mayúsculas.
- Números siempre `font-variant-numeric: tabular-nums`.

### Forma y ritmo

- Radios: 6 (carátulas), 10 (controles/filas), 16 (tarjetas), 20 (hero/modal).
- Sidebar 264px; topbar 66px; contenido máx. 1180px; padding 30px 36px.
- Hueco entre secciones: 30–34px; grupos internos 8–12px.
- Profundidad: sombra difusa `0 24px 70px rgba(0,0,0,.55)`; sin halos de color.

## Componentes

- **Sidebar**: marca con ecualizador, navegación de 3 secciones y lista de recaps con estado (`Nuevo`, `En curso`).
- **Topbar**: breadcrumb, campana con punto de no leído y CTA verde de sincronización.
- **Hero**: H1 editorial + tarjeta del nº 1 con carátula, fondo desenfocado de la carátula y acciones.
- **Stats strip**: cuatro hechos separados por hairlines, sin tarjetas.
- **Filtros**: segmentado 10/25/50/100, selector de año y búsqueda de artista con icono y limpiar.
- **Lista de canciones**: rank, carátula 44px, título/artista, álbum, reproducciones y barra verde.
- **Artistas**: podio de 3 vinilos circulares + lista; el vinilo tiene surcos, anillo y agujero central.
- **Actividad**: barras mensuales y 24 barras horarias con etiqueta de valor al hover y hechos al pie.
- **Recap**: modal con portada degradada por temporada, top 6, artista del periodo y copia del resumen.
- **Notificaciones**: popover con recaps disponibles, temporadas en curso y próximo recap.
- **Toast**: aviso de sincronización con punto de color y cierre.
- **Puerta de acceso**: pantalla de desbloqueo con la marca, campo de llave con mostrar/ocultar, opción de recordar y estado de error.
- **Obsesiones**: lista de episodios (obsesión/racha) con portada, periodo, días fuertes, plays, pico y mini-heatmap; timeline modal con calendario de calor diario y episodios.
- **Recap Wrapped**: hero con horas/plays/artistas, rejilla de métricas, canción y artista del periodo, top 5 canciones/artistas/álbumes, géneros, momentos, obsesión, perfil y artista mes a mes.
- **Carátulas**: resueltas en el backend (Deezer) y servidas como URL; el navegador solo carga la imagen, sin scripts de terceros.

## Movimiento

- Deriva lenta del fondo del hero (24s), revelado del hero al cargar, barras del ecualizador
  en la fila nº 1 y entrada del modal/popover con `cubic-bezier(.22,1,.36,1)`.
- Todo se detiene con `prefers-reduced-motion`.

## Accesibilidad

- Foco visible verde de 2px, `:focus-visible`.
- Contraste AA: cuerpo y metadatos ≥4.5:1; verde sobre negro >10:1.
- Navegación por teclado, `aria-current`, `aria-expanded`, diálogo con `aria-modal`,
  cierre con Escape y bloqueo de scroll.
- Imágenes decorativas con `alt=""`; el texto adyacente nombra la canción.

## Reglas de contenido

- Español, frases cortas, sin signos de admiración.
- Datos reales: no inventar cifras, testimonios ni capacidades.
- Portadas reales vía iTunes con caché local; si no hay coincidencia se usa una
  portada generada determinista con monograma.
- La llave de acceso se pide en la web y nunca se incluye en el bundle.
