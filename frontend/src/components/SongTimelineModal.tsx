import { useEffect, useRef } from 'react'

import { useSongTimeline } from '../hooks/useCanciones'
import { formatDate, formatDayRange, formatNumber } from '../utils/format'
import { buildComparisons } from '../utils/comparisons'
import { CalendarHeatmap } from './CalendarHeatmap'
import { CoverArt } from './CoverArt'
import { IconClose, IconFlame } from './Icons'

interface SongTimelineModalProps {
  songId: number
  highlightId?: string | null
  onClose: () => void
}

const TIER_LABEL = {
  obsesion: 'Obsesión',
  racha: 'Racha',
} as const

export function SongTimelineModal({
  songId,
  highlightId,
  onClose,
}: SongTimelineModalProps) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const query = useSongTimeline(songId)
  const data = query.data

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

  const episodes = data?.episodes ?? []
  const minutes = data?.total_minutes ?? 0
  const approximate = (data?.duration_coverage ?? 0) < 0.9
  const minutesLabel =
    minutes >= 60
      ? `${new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 }).format(
          Math.round((minutes / 60) * 10) / 10,
        )} h`
      : `${formatNumber(minutes)} min`
  const comparisons = buildComparisons(minutes).slice(0, 3)

  return (
    <div
      className="recap-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <article
        className="timeline-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="timeline-title"
      >
        <header className="timeline-head">
          <CoverArt
            artist={data?.song.artist ?? ''}
            title={data?.song.title ?? ''}
            size="lg"
          />
          <div className="timeline-head__text">
            <h2 id="timeline-title">{data?.song.title ?? 'Cargando…'}</h2>
            <p>{data?.song.artist ?? ''}</p>
            {data?.song.album ? <span>{data.song.album}</span> : null}
          </div>
          <button
            type="button"
            className="icon-btn timeline-close"
            ref={closeRef}
            onClick={onClose}
            aria-label="Cerrar historial"
          >
            <IconClose size={19} />
          </button>
        </header>

        <div className="timeline-body">
          {query.isLoading ? (
            <div className="timeline-loading" aria-busy="true">
              <span className="skeleton skeleton--chart" />
            </div>
          ) : query.isError ? (
            <div className="state">
              <p className="state__title">No se pudo cargar el historial</p>
              <p className="state__copy">Vuelve a intentarlo en un momento.</p>
            </div>
          ) : (
            <>
              <dl className="timeline-stats">
                <div>
                  <dt>Reproducciones</dt>
                  <dd>{formatNumber(data?.song.plays ?? 0)}</dd>
                </div>
                <div>
                  <dt>Minutos escuchados</dt>
                  <dd>
                    {approximate && minutes ? '≈ ' : ''}
                    {minutes ? minutesLabel : '—'}
                  </dd>
                </div>
                <div>
                  <dt>Primera escucha</dt>
                  <dd>{formatDate(data?.first_listen ?? null)}</dd>
                </div>
                <div>
                  <dt>Última escucha</dt>
                  <dd>{formatDate(data?.last_listen ?? null)}</dd>
                </div>
              </dl>

              <section className="timeline-section">
                <h3>Cuándo la escuchaste</h3>
                <CalendarHeatmap
                  days={data?.days ?? []}
                  episodes={episodes}
                  highlightId={highlightId}
                />
              </section>

              {comparisons.length ? (
                <section className="timeline-section">
                  <h3>En ese tiempo…</h3>
                  <ul className="recap-comparisons recap-comparisons--compact">
                    {comparisons.map((comparison) => (
                      <li key={comparison.key} className="recap-comparison">
                        <span className="recap-comparison__label">
                          {comparison.label}
                        </span>
                        <strong>{comparison.value}</strong>
                        <span className="recap-comparison__note">
                          {comparison.note}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <p className="recap-note">
                    Calculado con las duraciones conocidas de esta canción
                    {approximate ? ' (aproximado)' : ''}.
                  </p>
                </section>
              ) : null}

              <section className="timeline-section">
                <h3>Episodios ({episodes.length})</h3>
                {episodes.length ? (
                  <ol className="timeline-episodes">
                    {episodes.map((episode) => (
                      <li
                        key={episode.id}
                        className={`timeline-episode${episode.id === highlightId ? ' is-highlighted' : ''}`}
                      >
                        <span className={`tier-badge tier-badge--${episode.tier}`}>
                          <IconFlame size={11} />
                          {TIER_LABEL[episode.tier]}
                        </span>
                        <span className="timeline-episode__period">
                          {formatDayRange(episode.start, episode.end)}
                        </span>
                        <span className="timeline-episode__meta">
                          {episode.strong_days}/{episode.span_days} días ·{' '}
                          {formatNumber(episode.plays)} plays · pico{' '}
                          {episode.peak_plays}
                        </span>
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="state__copy">
                    Esta canción no llegó a ser una obsesión. Aun así, el mapa de
                    arriba muestra todos sus días de escucha.
                  </p>
                )}
              </section>
            </>
          )}
        </div>
      </article>
    </div>
  )
}
