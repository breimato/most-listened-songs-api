import { useEffect, useRef } from 'react'
import type { CSSProperties } from 'react'

import { useRecap } from '../hooks/useCanciones'
import type { RecapPeriod } from '../utils/recaps'
import { formatNumber } from '../utils/format'
import { CoverArt } from './CoverArt'
import { IconClose, IconSparkle } from './Icons'

interface WrappedLaunchProps {
  recap: RecapPeriod
  onOpen: () => void
  onClose: () => void
}

function formatHours(hours: number): string {
  return `${new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 }).format(
    Math.round(hours * 10) / 10,
  )} h`
}

export function WrappedLaunch({ recap, onOpen, onClose }: WrappedLaunchProps) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const query = useRecap({ since: recap.since, until: recap.until })
  const data = query.data
  const year = recap.label.replace(/^Año\s+/i, '')
  const hours = data
    ? data.duration_coverage >= 0.9
      ? data.total_hours
      : data.estimated_hours
    : 0
  const approximate = Boolean(data && data.duration_coverage < 0.9)

  useEffect(() => {
    closeRef.current?.focus()
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [onClose])

  return (
    <div
      className="wrapped-launch"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <article
        className="wrapped-launch__card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="wrapped-launch-title"
        style={
          {
            '--recap-from': recap.palette.from,
            '--recap-to': recap.palette.to,
          } as CSSProperties
        }
      >
        <div className="wrapped-launch__glow" aria-hidden="true" />
        <button
          type="button"
          className="icon-btn wrapped-launch__close"
          ref={closeRef}
          onClick={onClose}
          aria-label="Cerrar aviso de Wrapped"
        >
          <IconClose size={19} />
        </button>

        <span className="wrapped-launch__badge">
          <IconSparkle size={13} /> Nuevo
        </span>
        <p className="wrapped-launch__year">Wrapped {year}</p>
        <h2 className="wrapped-launch__title" id="wrapped-launch-title">
          Tu año en música
        </h2>
        <p className="wrapped-launch__lead">
          Ya puedes ver el resumen de tu {year}. Y seguirá actualizándose durante
          todo diciembre.
        </p>

        {data?.top_song ? (
          <div className="wrapped-launch__song">
            <CoverArt
              artist={data.top_song.artist}
              title={data.top_song.title}
              size="lg"
            />
            <div className="wrapped-launch__song-text">
              <span className="wrapped-launch__song-label">Tu canción</span>
              <span className="wrapped-launch__song-title">
                {data.top_song.title}
              </span>
              <span className="wrapped-launch__song-artist">
                {data.top_song.artist}
              </span>
            </div>
          </div>
        ) : null}

        <div className="wrapped-launch__stats">
          <span>
            <strong>{data ? `${approximate ? '≈ ' : ''}${formatHours(hours)}` : '—'}</strong>
            de música
          </span>
          <span>
            <strong>{data ? formatNumber(data.total_plays) : '—'}</strong>
            reproducciones
          </span>
          <span>
            <strong>{data ? formatNumber(data.unique_artists) : '—'}</strong>
            artistas
          </span>
        </div>

        <div className="wrapped-launch__actions">
          <button type="button" className="btn btn--primary" onClick={onOpen}>
            Ver mi año
          </button>
          <button type="button" className="btn btn--ghost" onClick={onClose}>
            Ahora no
          </button>
        </div>
      </article>
    </div>
  )
}
