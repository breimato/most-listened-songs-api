---
version: 1
slug: "src-app-tsx"
primary_target: "src/App.tsx"
related_targets: []
---

# Superficie: dashboard de scrobbles

Modo: Operate. Un único usuario. Éxito: entender su música de un vistazo y recibir recaps de temporada.

## Direction contract

THESIS: Una sala de escucha personal, no un panel de tarjetas. La portada y el número 1 mandan; el recap estacional es la memoria propia que ningún dashboard genérico tiene. Se rechaza la rejilla de tarjetas y el hero-métrica.

OWN-WORLD: Fondo casi negro (#0a0a0b) con sidebar negra; elevación #141416 y hairlines blancas al 9%; verde #1ed760 solo para el foco, el ranking y los recaps; texto #f7f7f5 y #a7a7a3; Figtree 400-800; radios 6/10/16; carátulas reales de Deezer con fallback generado; iconos SVG de trazo 1.7; números tabulares.

STORY: Abro y veo mi #1 con su portada, mis totales y la lista; puedo cambiar a artistas o actividad; cuando termina una temporada, la campana me avisa y abro el recap.

FIRST VIEWPORT: Shell de sidebar 264px + topbar; en el área principal, hero de 300-340px con la carátula del #1 a 168px, título en Figtree 800 a 44-52px, artista y badge verde de reproducciones, fondo con la portada desenfocada y un degradado oscuro; debajo, una franja de totales separada por hairlines; después el encabezado de lista con filtros y las primeras filas.

FORM: dirección fijada por el brief (Spotify), puesta 1 de 1; sin roll.
seed: none (unavailable)

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
