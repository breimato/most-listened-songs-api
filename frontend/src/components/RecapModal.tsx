import { useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'

import { useRecap } from '../hooks/useCanciones'
import type { Obsession, Recap } from '../types/api'
import type { RecapPeriod } from '../utils/recaps'
import {
  formatDate,
  formatDayLong,
  formatDayRange,
  formatNumber,
  hourLabel,
} from '../utils/format'
import { buildComparisons, COMPARISON_SOURCES } from '../utils/comparisons'
import { shareRecapCard } from '../utils/shareCard'
import { CoverArt } from './CoverArt'
import {
  IconCheck,
  IconClose,
  IconCopy,
  IconDownload,
  IconFlame,
  IconMoon,
  IconSparkle,
} from './Icons'

interface RecapModalProps {
  recap: RecapPeriod
  onClose: () => void
  onOpenObsession?: (obsession: Obsession) => void
  onOpenSleep?: () => void
}

const TIER_LABEL = {
  obsesion: 'Obsesión',
  racha: 'Racha',
} as const

function formatHours(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)} min`
  const rounded = Math.round(hours * 10) / 10
  return `${new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 }).format(rounded)} h`
}

function formatMinutes(minutes: number): string {
  if (!minutes) return '—'
  if (minutes < 60) return `${minutes} min`
  const hours = minutes / 60
  return `${new Intl.NumberFormat('es-ES', {
    maximumFractionDigits: hours >= 10 ? 0 : 1,
  }).format(hours)} h`
}

function monthLabel(value: string): string {
  const [year, month] = value.split('-')
  return new Intl.DateTimeFormat('es-ES', { month: 'short' })
    .format(new Date(Number(year), Number(month) - 1, 1))
    .replace('.', '')
}

function pct(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function RecapModal({
  recap,
  onClose,
  onOpenObsession,
  onOpenSleep,
}: RecapModalProps) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const [copied, setCopied] = useState(false)
  const [sharing, setSharing] = useState(false)
  const [shared, setShared] = useState('')
  const query = useRecap({ since: recap.since, until: recap.until })
  const data: Recap | undefined = query.data

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

  const hours = data
    ? data.duration_coverage >= 0.9
      ? data.total_hours
      : data.estimated_hours
    : 0
  const approximate = Boolean(data && data.duration_coverage < 0.9)

  const copySummary = async () => {
    if (!data) return
    const topSong = data.top_song
    const topArtist = data.top_artists[0]
    const lines = [
      `${recap.title} · ${recap.label}`,
      recap.range,
      '',
      approximate ? `≈ ${formatHours(hours)} de música` : `${formatHours(hours)} de música`,
      `${formatNumber(data.total_plays)} reproducciones · ${formatNumber(data.unique_artists)} artistas · ${formatNumber(data.unique_songs)} canciones`,
      `${data.days_listened} días con música · racha de ${data.longest_streak} días`,
      '',
      topSong
        ? `Canción: ${topSong.title} — ${topSong.artist} (${formatNumber(topSong.plays)} plays, ${topSong.days} días)`
        : '',
      topArtist
        ? `Artista: ${topArtist.artist} (${formatNumber(topArtist.plays)} plays)`
        : '',
      data.top_albums[0]
        ? `Álbum: ${data.top_albums[0].album} — ${data.top_albums[0].artist}`
        : '',
      data.top_genres.length
        ? `Géneros: ${data.top_genres.map((genre) => genre.name).join(', ')}`
        : '',
      data.sleep?.songs.length
        ? `Para dormir: ${data.sleep.songs[0].title} — ${data.sleep.songs[0].artist} (${pct(data.sleep.songs[0].night_share)} de noche)`
        : '',
      `Perfil: ${data.profile.label}`,
    ].filter(Boolean)

    try {
      await navigator.clipboard.writeText(lines.join('\n'))
    } catch {
      const area = document.createElement('textarea')
      area.value = lines.join('\n')
      document.body.appendChild(area)
      area.select()
      document.execCommand('copy')
      area.remove()
    }

    setCopied(true)
    window.setTimeout(() => setCopied(false), 2200)
  }

  const handleShare = async () => {
    if (!data) return
    setSharing(true)
    try {
      const result = await shareRecapCard(data, recap)
      setShared(result === 'shared' ? 'Compartido' : 'PNG descargado')
    } catch {
      setShared('No se pudo generar')
    } finally {
      setSharing(false)
      window.setTimeout(() => setShared(''), 2600)
    }
  }

  return (
    <div
      className="recap-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <article
        className="recap-sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="recap-title"
        style={
          {
            '--recap-from': recap.palette.from,
            '--recap-to': recap.palette.to,
          } as CSSProperties
        }
      >
        <header className="recap-hero">
          <button
            type="button"
            className="icon-btn recap-close"
            ref={closeRef}
            onClick={onClose}
            aria-label="Cerrar recap"
          >
            <IconClose size={19} />
          </button>

          <h2 className="recap-hero__title" id="recap-title">
            {recap.title}
          </h2>
          <p className="recap-hero__meta">
            {recap.label} · {recap.range}
          </p>

          <div className="recap-hero__figures">
            <span className="recap-figure">
              <strong>{approximate ? '≈ ' : ''}{formatHours(hours)}</strong>
              <span>de música</span>
            </span>
            <span className="recap-figure">
              <strong>{data ? formatNumber(data.total_plays) : '—'}</strong>
              <span>reproducciones</span>
            </span>
            <span className="recap-figure">
              <strong>{data ? formatNumber(data.unique_artists) : '—'}</strong>
              <span>artistas</span>
            </span>
          </div>

          {approximate ? (
            <p className="recap-hero__note">
              Calculado con el {pct(data?.duration_coverage ?? 0)} de las
              duraciones conocidas; el resto es una estimación.
            </p>
          ) : null}
        </header>

        <div className="recap-body">
          {query.isLoading ? (
            <div className="recap-loading" aria-busy="true">
              <span className="skeleton skeleton--chart" />
              <span className="skeleton skeleton--chart" />
            </div>
          ) : query.isError || !data ? (
            <div className="state">
              <p className="state__title">No se pudo calcular el recap</p>
              <p className="state__copy">Vuelve a intentarlo en un momento.</p>
            </div>
          ) : (
            <>
              <dl className="recap-stats">
                <div>
                  <dt>Horas de música</dt>
                  <dd>
                    {approximate ? '≈ ' : ''}
                    {formatHours(hours)}
                  </dd>
                </div>
                <div>
                  <dt>Reproducciones</dt>
                  <dd>{formatNumber(data.total_plays)}</dd>
                </div>
                <div>
                  <dt>Artistas</dt>
                  <dd>{formatNumber(data.unique_artists)}</dd>
                </div>
                <div>
                  <dt>Canciones</dt>
                  <dd>{formatNumber(data.unique_songs)}</dd>
                </div>
                <div>
                  <dt>Días con música</dt>
                  <dd>{data.days_listened}</dd>
                </div>
                <div>
                  <dt>Racha más larga</dt>
                  <dd>{data.longest_streak} días</dd>
                </div>
              </dl>

              {data.top_song ? (
                <section className="recap-section">
                  <h3>Tu canción del periodo</h3>
                  <div className="recap-feature">
                    <CoverArt
                      artist={data.top_song.artist}
                      title={data.top_song.title}
                      size="lg"
                    />
                    <div className="recap-feature__text">
                      <p className="recap-feature__title">{data.top_song.title}</p>
                      <p className="recap-feature__artist">{data.top_song.artist}</p>
                      {data.top_song.album ? (
                        <p className="recap-feature__album">{data.top_song.album}</p>
                      ) : null}
                      <p className="recap-feature__line">
                        La escuchaste <strong>{data.top_song.days} días</strong>, con
                        una racha de{' '}
                        <strong>{data.top_song.longest_streak} días seguidos</strong>.
                      </p>
                      <div className="recap-chips">
                        <span>{formatNumber(data.top_song.plays)} plays</span>
                        <span>{formatMinutes(data.top_song.minutes)}</span>
                        <span>{pct(data.top_song.share)} del periodo</span>
                      </div>
                    </div>
                  </div>
                </section>
              ) : null}

              {data.top_artists[0] ? (
                <section className="recap-section">
                  <h3>Tu artista del periodo</h3>
                  <div className="recap-feature recap-feature--artist">
                    <CoverArt
                      artist={data.top_artists[0].artist}
                      title={data.top_artists[0].top_song ?? ''}
                      size="lg"
                      round
                    />
                    <div className="recap-feature__text">
                      <p className="recap-feature__title">
                        {data.top_artists[0].artist}
                      </p>
                      <p className="recap-feature__line">
                        {formatNumber(data.top_artists[0].plays)} reproducciones ·{' '}
                        {formatMinutes(data.top_artists[0].minutes)} ·{' '}
                        {pct(data.top_artists[0].share)} de tu música
                      </p>
                      {data.top_artists[0].top_song ? (
                        <p className="recap-feature__album">
                          Tu canción: {data.top_artists[0].top_song}
                        </p>
                      ) : null}
                    </div>
                  </div>
                </section>
              ) : null}

              <section className="recap-section">
                <h3>Top 5 canciones</h3>
                <ol className="recap-rows">
                  {data.top_songs.map((song, index) => (
                    <li key={song.song_id} className="recap-row">
                      <span className="recap-row__rank">
                        {String(index + 1).padStart(2, '0')}
                      </span>
                      <CoverArt artist={song.artist} title={song.title} size="sm" />
                      <span className="recap-row__main">
                        <span className="recap-row__title">{song.title}</span>
                        <span className="recap-row__meta">
                          {song.artist} · {song.days} días
                        </span>
                      </span>
                      <span className="recap-row__stats">
                        <strong>{formatNumber(song.plays)}</strong> plays
                        <span>{formatMinutes(song.minutes)}</span>
                      </span>
                    </li>
                  ))}
                </ol>
              </section>

              <section className="recap-section">
                <h3>Top 5 artistas</h3>
                <ol className="recap-rows">
                  {data.top_artists.map((artist, index) => (
                    <li key={artist.artist} className="recap-row">
                      <span className="recap-row__rank">
                        {String(index + 1).padStart(2, '0')}
                      </span>
                      <CoverArt
                        artist={artist.artist}
                        title={artist.top_song ?? ''}
                        size="sm"
                        round
                      />
                      <span className="recap-row__main">
                        <span className="recap-row__title">{artist.artist}</span>
                        <span className="recap-row__meta">
                          {formatMinutes(artist.minutes)} · {pct(artist.share)}
                        </span>
                      </span>
                      <span className="recap-row__stats">
                        <strong>{formatNumber(artist.plays)}</strong> plays
                      </span>
                    </li>
                  ))}
                </ol>
              </section>

              {data.top_albums.length ? (
                <section className="recap-section">
                  <h3>Top 5 álbumes</h3>
                  <ol className="recap-rows">
                    {data.top_albums.map((album, index) => (
                      <li key={`${album.album}-${album.artist}`} className="recap-row">
                        <span className="recap-row__rank">
                          {String(index + 1).padStart(2, '0')}
                        </span>
                        <CoverArt
                          artist={album.artist}
                          title={album.top_song}
                          size="sm"
                        />
                        <span className="recap-row__main">
                          <span className="recap-row__title">{album.album}</span>
                          <span className="recap-row__meta">{album.artist}</span>
                        </span>
                        <span className="recap-row__stats">
                          <strong>{formatNumber(album.plays)}</strong> plays
                          <span>{formatMinutes(album.minutes)}</span>
                        </span>
                      </li>
                    ))}
                  </ol>
                </section>
              ) : null}

              {data.top_genres.length ? (
                <section className="recap-section">
                  <h3>Tus géneros</h3>
                  <div className="recap-genres">
                    {data.top_genres.map((genre) => (
                      <span key={genre.name} className="recap-genre">
                        <span className="recap-genre__name">{genre.name}</span>
                        <span className="recap-genre__bar" aria-hidden="true">
                          <i style={{ width: `${Math.max(4, genre.share * 100)}%` }} />
                        </span>
                        <span className="recap-genre__share">{pct(genre.share)}</span>
                      </span>
                    ))}
                  </div>
                  <p className="recap-note">Según los tags de artista de Last.fm.</p>
                </section>
              ) : null}

              <section className="recap-section">
                <h3>Momentos</h3>
                <dl className="recap-facts">
                  <div>
                    <dt>Día más musical</dt>
                    <dd>{data.top_day ? formatDayLong(data.top_day) : '—'}</dd>
                    <span>{data.top_day_plays} reproducciones</span>
                  </div>
                  <div>
                    <dt>Hora favorita</dt>
                    <dd>
                      {data.top_hour !== null ? hourLabel(data.top_hour) : '—'}
                    </dd>
                    <span>{data.top_hour_plays} reproducciones</span>
                  </div>
                  <div>
                    <dt>Primera canción</dt>
                    <dd>{data.first_song ?? '—'}</dd>
                    <span>{formatDate(data.first_play)}</span>
                  </div>
                  <div>
                    <dt>Última canción</dt>
                    <dd>{data.last_song ?? '—'}</dd>
                    <span>{formatDate(data.last_play)}</span>
                  </div>
                </dl>
              </section>

              {data.sleep.songs.length ? (
                <section className="recap-section">
                  <h3>Para dormir</h3>
                  <div className="recap-sleep">
                    <p className="recap-sleep__lead">
                      <IconMoon size={16} />
                      {pct(data.sleep.night_share)} de tus escuchas fueron entre
                      las 00:00 y las 07:00 · {data.sleep.estimated ? '≈ ' : ''}
                      {formatMinutes(data.sleep.night_minutes)} de música
                      nocturna.
                    </p>
                    <ol className="recap-sleep__list">
                      {data.sleep.songs.slice(0, 3).map((song, index) => (
                        <li key={song.song_id} className="recap-sleep__item">
                          <span className="recap-sleep__rank">
                            {index === 0 ? <IconMoon size={13} /> : index + 1}
                          </span>
                          <span className="recap-sleep__title">
                            {song.title}
                            <small>{song.artist}</small>
                          </span>
                          <span className="recap-sleep__share">
                            {pct(song.night_share)} noche
                          </span>
                        </li>
                      ))}
                    </ol>
                    {onOpenSleep ? (
                      <button
                        type="button"
                        className="btn btn--ghost recap-sleep__action"
                        onClick={onOpenSleep}
                      >
                        Ver ranking completo
                      </button>
                    ) : null}
                  </div>
                </section>
              ) : null}

              <section className="recap-section">
                <h3>Lo que dan de sí</h3>
                <ul className="recap-comparisons">
                  {buildComparisons(Math.round(hours * 60))
                    .slice(0, 5)
                    .map((comparison) => (
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
                  Cálculos con{' '}
                  {COMPARISON_SOURCES.map((source, index) => (
                    <span key={source.label}>
                      <a href={source.url} target="_blank" rel="noreferrer">
                        {source.label}
                      </a>
                      {index < COMPARISON_SOURCES.length - 1 ? ' y ' : ''}
                    </span>
                  ))}
                  . Supuestos: curso de 40 h, libro de 90.000 palabras a 250 ppm,
                  película de 2 h, caminar 5 km/h, dormir 8 h.
                </p>
              </section>

              {data.top_obsession ? (
                <section className="recap-section">
                  <h3>Tu obsesión del periodo</h3>
                  <div className="recap-obsession">
                    <CoverArt
                      artist={data.top_obsession.artist}
                      title={data.top_obsession.title}
                      size="sm"
                    />
                    <div className="recap-obsession__body">
                      <span className="recap-obsession__title">
                        {data.top_obsession.title}
                      </span>
                      <span className="recap-obsession__meta">
                        {data.top_obsession.artist} ·{' '}
                        {formatDayRange(
                          data.top_obsession.start,
                          data.top_obsession.end,
                        )}{' '}
                        · {data.top_obsession.strong_days}/
                        {data.top_obsession.span_days} días ·{' '}
                        {formatNumber(data.top_obsession.plays)} plays
                      </span>
                    </div>
                    <span
                      className={`tier-badge tier-badge--${data.top_obsession.tier}`}
                    >
                      <IconFlame size={11} />
                      {TIER_LABEL[data.top_obsession.tier]}
                    </span>
                    {onOpenObsession ? (
                      <button
                        type="button"
                        className="btn btn--ghost recap-obsession__button"
                        onClick={() => {
                          onClose()
                          onOpenObsession(data.top_obsession as Obsession)
                        }}
                      >
                        Ver historial
                      </button>
                    ) : null}
                  </div>
                </section>
              ) : null}

              <section className="recap-section">
                <h3>Tu perfil</h3>
                <div className="recap-profile">
                  <span className="recap-profile__icon" aria-hidden="true">
                    <IconSparkle size={20} />
                  </span>
                  <div>
                    <p className="recap-profile__label">{data.profile.label}</p>
                    <p className="recap-profile__description">
                      {data.profile.description}
                    </p>
                  </div>
                </div>
                <p className="recap-note">
                  Perfil calculado con tus hábitos de escucha, no con géneros.
                </p>
              </section>

              {data.monthly_top_artists.length ? (
                <section className="recap-section">
                  <h3>Tu artista, mes a mes</h3>
                  <div className="recap-months">
                    {data.monthly_top_artists.map((month) => (
                      <span key={month.month} className="recap-month">
                        <span className="recap-month__label">
                          {monthLabel(month.month)}
                        </span>
                        <span className="recap-month__artist">{month.artist}</span>
                      </span>
                    ))}
                  </div>
                </section>
              ) : null}
            </>
          )}
        </div>

        <footer className="recap-foot">
          <div className="recap-foot__actions">
            <button
              type="button"
              className="btn btn--ghost"
              onClick={copySummary}
              disabled={!data}
            >
              {copied ? <IconCheck size={17} /> : <IconCopy size={17} />}
              {copied ? 'Copiado' : 'Copiar resumen'}
            </button>
            <button
              type="button"
              className="btn btn--ghost"
              onClick={handleShare}
              disabled={!data || sharing}
            >
              <IconDownload size={17} />
              {sharing ? 'Generando…' : shared || 'Compartir PNG'}
            </button>
          </div>
          <button type="button" className="btn btn--primary" onClick={onClose}>
            Cerrar
          </button>
        </footer>
      </article>
    </div>
  )
}
