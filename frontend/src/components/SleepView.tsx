import type { CSSProperties } from 'react'

import type { SleepData } from '../types/api'
import { formatNumber, hourLabel } from '../utils/format'
import { CoverArt } from './CoverArt'
import { IconChart, IconMoon } from './Icons'

interface SleepViewProps {
  data: SleepData | undefined
  isLoading: boolean
  isError: boolean
  onOpenSong: (songId: number) => void
}

function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${Math.round(minutes)} min`
  const hours = minutes / 60
  return `${new Intl.NumberFormat('es-ES', {
    maximumFractionDigits: hours >= 10 ? 0 : 1,
  }).format(hours)} h`
}

function pct(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function SleepView({
  data,
  isLoading,
  isError,
  onOpenSong,
}: SleepViewProps) {
  if (isLoading) {
    return (
      <div className="sleep-state" aria-busy="true">
        <span className="skeleton skeleton--cover" />
        <span className="skeleton skeleton--title" />
        <span className="skeleton skeleton--album" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="state">
        <p className="state__title">No se pudo cargar la lista nocturna</p>
        <p className="state__copy">
          Comprueba que la API esté disponible y vuelve a intentarlo.
        </p>
      </div>
    )
  }

  if (!data?.songs.length) {
    return (
      <div className="state">
        <p className="state__title">Todavía no hay suficientes noches</p>
        <p className="state__copy">
          La lista aparece cuando una canción acumula al menos 10 escuchas
          entre las 00:00 y las 07:00 y al menos el 40% de sus reproducciones
          son nocturnas.
        </p>
      </div>
    )
  }

  const top = data.songs[0]

  return (
    <div className="sleep-view">
      <section className="sleep-hero" aria-labelledby="sleep-hero-title">
        <div className="sleep-hero__glow" aria-hidden="true" />
        <div className="sleep-hero__moon" aria-hidden="true">
          <IconMoon size={30} />
        </div>
        <div className="sleep-hero__copy">
          <p className="sleep-hero__eyebrow">
            Tu canción para dormir · {String(data.window_start).padStart(2, '0')}:00–
            {String(data.window_end).padStart(2, '0')}:00
          </p>
          <h2 className="sleep-hero__title" id="sleep-hero-title">
            {top.title}
          </h2>
          <p className="sleep-hero__artist">{top.artist}</p>
          <p className="sleep-hero__meta">
            {formatNumber(top.plays)} escuchas nocturnas ·{' '}
            {pct(top.night_share)} de sus reproducciones ·{' '}
            {top.estimated ? '≈ ' : ''}
            {formatMinutes(top.minutes)} de noche
          </p>
        </div>
        <CoverArt artist={top.artist} title={top.title} size="lg" />
      </section>

      <dl className="stats-strip sleep-stats">
        <div className="stats-strip__item">
          <dt>Horas de noche</dt>
          <dd>
            {data.estimated ? '≈ ' : ''}
            {formatMinutes(data.night_minutes)}
          </dd>
        </div>
        <div className="stats-strip__item">
          <dt>Reproducciones</dt>
          <dd>{formatNumber(data.night_plays)}</dd>
        </div>
        <div className="stats-strip__item">
          <dt>De tu música</dt>
          <dd>{pct(data.night_share)}</dd>
        </div>
        <div className="stats-strip__item">
          <dt>Noches con música</dt>
          <dd>{formatNumber(data.nights)}</dd>
        </div>
      </dl>

      <div className="sleep-facts">
        {data.top_hour !== null ? (
          <span>
            <IconMoon size={14} /> Tu hora más nocturna: {hourLabel(data.top_hour)}
          </span>
        ) : null}
        {data.top_artist ? (
          <span>
            Tu artista de noche: <strong>{data.top_artist}</strong>
          </span>
        ) : null}
      </div>

      <ol className="sleep-list">
        <li className="sleep-list__head" aria-hidden="true">
          <span>#</span>
          <span>Canción</span>
          <span>Noche</span>
          <span>% nocturno</span>
          <span className="sleep-list__head-right">Horas</span>
          <span />
        </li>
        {data.songs.map((song, index) => (
          <li
            key={song.song_id}
            className="sleep-row"
            style={{ '--row': index } as CSSProperties}
          >
            <span className={`sleep-row__rank${index === 0 ? ' is-top' : ''}`}>
              {index === 0 ? (
                <IconMoon size={15} />
              ) : (
                String(index + 1).padStart(2, '0')
              )}
            </span>
            <div className="sleep-row__main">
              <CoverArt artist={song.artist} title={song.title} size="sm" />
              <div className="sleep-row__text">
                <p className="sleep-row__title">{song.title}</p>
                <p className="sleep-row__artist">{song.artist}</p>
              </div>
            </div>
            <div className="sleep-row__plays">
              <span className="sleep-row__count">
                {formatNumber(song.plays)}
              </span>
              <span className="sleep-row__hint">
                de {formatNumber(song.total_plays)}
              </span>
            </div>
            <div className="sleep-row__share">
              <span className="sleep-row__badge">
                {pct(song.night_share)}
              </span>
              <span className="sleep-row__bar" aria-hidden="true">
                <span
                  style={{
                    width: `${Math.max(4, song.night_share * 100)}%`,
                  }}
                />
              </span>
            </div>
            <span className="sleep-row__minutes">
              {song.estimated ? '≈ ' : ''}
              {formatMinutes(song.minutes)}
            </span>
            <button
              type="button"
              className="sleep-row__timeline"
              onClick={() => onOpenSong(song.song_id)}
              aria-label={`Ver historial de ${song.title}`}
              title="Ver historial"
            >
              <IconChart size={15} />
            </button>
          </li>
        ))}
      </ol>

      <p className="sleep-note">
        Entre las {String(data.window_start).padStart(2, '0')}:00 y las{' '}
        {String(data.window_end).padStart(2, '0')}:00. Solo entran canciones con
        al menos 10 escuchas nocturnas y un 40% de su reproducción en esa franja.
        {data.estimated
          ? ` Las horas con ≈ se estiman con la duración media (${pct(
              data.duration_coverage,
            )} de cobertura nocturna).`
          : ''}
      </p>
    </div>
  )
}
