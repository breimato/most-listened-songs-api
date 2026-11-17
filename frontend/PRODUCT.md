# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Un único usuario (Breixo) que escucha música en Spotify, YouTube y YouTube Music desde el móvil y el PC. Consulta el dashboard sobre todo al final del día o al cerrar una temporada, para entender qué ha escuchado y recuperar sus temas de cada época.

## Product Purpose

Convertir el historial de scrobbles de Last.fm en un ranking visual de canciones y artistas, con estadísticas de actividad y recaps por temporadas. El éxito es entender de un vistazo qué suena más y revivir "los temas del verano" o "los del año" sin trabajo manual.

## Positioning

Last.fm actúa como agregador único de todos los dispositivos; la app añade una capa propia de recaps estacionales y una presentación musical cuidada que Last.fm no ofrece. No es una red social ni un reproductor.

## Operating Context

- Scrobbling: Pano Scrobbler (Android) y Web Scrobbler (Firefox) → Last.fm.
- Ingesta: `POST /api/v1/sync` (cursor `MAX(plays.played_at)`), manual y por CronJob cada 15 minutos.
- Despliegue: API + PostgreSQL en k3s; frontend estático en https://breimato.es/youtube.
- Uso principal en escritorio; debe funcionar bien en móvil.

## Capabilities and Constraints

- Top canciones y artistas, con filtros de límite, año y artista.
- Resumen: reproducciones, canciones, artistas, día favorito y periodo.
- Actividad: reproducciones por mes y por hora.
- Sincronización manual desde la UI.
- Recaps por temporadas (verano, año, etc.) con notificaciones in-app; se calculan con rangos `since`/`until` de la API.
- Carátulas reales vía iTunes Search API (sin clave, con caché en el navegador); fallback generado si no hay coincidencia.
- Datos reales: ~12.900 reproducciones. No inventar cifras, testimonios ni capacidades.

## Brand Commitments

El usuario fijó una estética "rollo Spotify": fondo oscuro, acento verde, navegación lateral, carátulas protagonistas y tipografía compacta. Es una inspiración, no un clon literal: la identidad propia son los recaps estacionales y la mezcla de plataformas.

## Evidence on Hand

- `canciones.db` y PostgreSQL con 12.909 reproducciones, 3.184 canciones y 1.808 artistas (datos reales).
- API pública en `https://breimato.es/youtube/runtime-config.json` → quick tunnel → cluster.
- Sin logotipo ni fotos de artistas propias; las carátulas se resuelven en tiempo de ejecución.

## Product Principles

1. La música manda: portada, título y artista antes que cualquier cromo.
2. De un vistazo: los totales y el top deben entenderse sin leer párrafos.
3. Memoria estacional: cada temporada deja un recap consultable.
4. Personal y honesto: datos reales, sin métricas inventadas.
5. Silencio visual: el color acento solo señala lo que importa.

## Accessibility & Inclusion

Navegación por teclado, foco visible, contraste AA sobre fondo oscuro y respeto por `prefers-reduced-motion`.
