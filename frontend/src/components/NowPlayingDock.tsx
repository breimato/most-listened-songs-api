import { useEffect, useState } from 'react'

import { useNowPlaying } from '../hooks/useCanciones'
import { useArtwork } from '../hooks/useArtwork'
import { relativeTime } from '../utils/format'
import { resolveNowPlayingState } from '../utils/nowPlaying'
import { CoverArt } from './CoverArt'

const STATE_LABELS = {
  loading: 'CONECTANDO',
  live: 'EN VIVO',
  paused: 'ÚLTIMA ESCUCHA',
  stale: 'SIN CONEXIÓN',
  idle: 'GROBEATS FM',
} as const

export function NowPlayingDock() {
  const { data, isLoading, isError, dataUpdatedAt } = useNowPlaying()
  const [now, setNow] = useState(() => Date.now())
  const track = data?.track
  const artwork = useArtwork(track?.artist ?? '', track?.title ?? '')

  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), 30_000)
    return () => window.clearInterval(interval)
  }, [])

  const state = resolveNowPlayingState(
    data,
    isLoading,
    isError,
    dataUpdatedAt,
    now,
  )

  if (isError && !data) return null

  const title =
    track?.title ??
    (state === 'loading'
      ? 'Conectando con GroBeats FM…'
      : 'Sin reproducción todavía')
  const artist =
    track?.artist ??
    (state === 'loading'
      ? 'Buscando tu última canción'
      : 'Tu historial musical')
  const time =
    state === 'live'
      ? 'Ahora'
      : state === 'paused'
        ? relativeTime(track?.scrobbled_at ?? null)
        : state === 'stale'
          ? 'Sin conexión'
          : '—'

  return (
    <section
      className={`now-playing is-${state}`}
      aria-label="Reproductor de GroBeats FM"
    >
      <div className="now-playing__wash" aria-hidden="true">
        {artwork ? <img src={artwork} alt="" /> : null}
      </div>

      <div className="now-playing__inner">
        <div className="now-playing__vinyl" aria-hidden="true">
          <div className="now-playing__record">
            <CoverArt
              artist={track?.artist ?? ''}
              title={track?.title ?? ''}
              size="sm"
              round
              src={artwork}
            />
            {!artwork ? (
              <span className="now-playing__mark">
                <i />
                <i />
                <i />
                <i />
              </span>
            ) : null}
          </div>

          <svg
            className="now-playing__arm"
            viewBox="0 0 58 58"
            fill="none"
            focusable="false"
          >
            <circle cx="45" cy="9" r="5" fill="#171719" stroke="currentColor" />
            <circle cx="45" cy="9" r="1.5" fill="currentColor" />
            <path
              d="M45 14L40.5 33L30 43"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M27.5 41.5L32 44L29.5 48.5L25 46L27.5 41.5Z"
              fill="currentColor"
            />
            <path d="M27 47L25.5 49" stroke="currentColor" strokeLinecap="round" />
          </svg>
        </div>

        <div className="now-playing__copy">
          <div className="now-playing__live" role="status" aria-live="polite">
            <div className="now-playing__state">
              <span className="now-playing__state-dot" aria-hidden="true" />
              {STATE_LABELS[state]}
            </div>
            <p className="now-playing__title" title={title}>
              {title}
            </p>
            <p className="now-playing__artist" title={artist}>
              {artist}
            </p>
          </div>
          {track?.album ? (
            <p className="now-playing__album" title={track.album}>
              {track.album}
            </p>
          ) : null}
        </div>

        <div className="now-playing__side">
          <span className="now-playing__eq" aria-hidden="true">
            <span className="eq">
              <i />
              <i />
              <i />
              <i />
              <i />
            </span>
          </span>
          <span className="now-playing__time">{time}</span>
        </div>
      </div>
    </section>
  )
}
