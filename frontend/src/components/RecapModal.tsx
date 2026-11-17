import type { CSSProperties } from 'react'

import { useEffect, useRef, useState } from 'react'

import { useTopArtists, useTopSongs, useStats } from '../hooks/useCanciones'
import type { RecapPeriod } from '../utils/recaps'
import { formatNumber } from '../utils/format'
import { CoverArt } from './CoverArt'
import { IconCheck, IconClose, IconCopy } from './Icons'

interface RecapModalProps {
  recap: RecapPeriod
  onClose: () => void
}

export function RecapModal({ recap, onClose }: RecapModalProps) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const [copied, setCopied] = useState(false)

  const range = { since: recap.since, until: recap.until }
  const songsQuery = useTopSongs({ limit: 6, ...range })
  const artistsQuery = useTopArtists(1, range)
  const statsQuery = useStats(range)

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

  const songs = songsQuery.data ?? []
  const topArtist = artistsQuery.data?.[0]
  const totalPlays = statsQuery.data?.total_plays

  const copySummary = async () => {
    const lines = [
      `${recap.title} · ${recap.label}`,
      recap.range,
      '',
      ...songs.map(
        (song, index) =>
          `${index + 1}. ${song.title} — ${song.artist} (${formatNumber(song.plays)})`,
      ),
    ]
    const text = lines.join('\n')

    try {
      await navigator.clipboard.writeText(text)
    } catch {
      const area = document.createElement('textarea')
      area.value = text
      document.body.appendChild(area)
      area.select()
      document.execCommand('copy')
      area.remove()
    }

    setCopied(true)
    window.setTimeout(() => setCopied(false), 2200)
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

          <div className="recap-hero__stats">
            <span>
              <strong>{totalPlays !== undefined ? formatNumber(totalPlays) : '—'}</strong>{' '}
              reproducciones
            </span>
            {topArtist ? (
              <span>
                <strong>{topArtist.artist}</strong> fue tu artista
              </span>
            ) : null}
          </div>
        </header>

        <div className="recap-body">
          <h3>Tus canciones</h3>

          {songsQuery.isLoading ? (
            <ol className="recap-songs" aria-busy="true">
              {Array.from({ length: 5 }).map((_, index) => (
                <li key={index} className="recap-song">
                  <span className="skeleton skeleton--rank" />
                  <span className="skeleton skeleton--cover" />
                  <span className="skeleton skeleton--title" />
                </li>
              ))}
            </ol>
          ) : songs.length ? (
            <ol className="recap-songs">
              {songs.map((song, index) => (
                <li key={song.id} className="recap-song">
                  <span className="recap-song__rank">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  <CoverArt artist={song.artist} title={song.title} size="sm" />
                  <span className="recap-song__text">
                    <span className="recap-song__title">{song.title}</span>
                    <span className="recap-song__artist">{song.artist}</span>
                  </span>
                  <span className="recap-song__plays">{formatNumber(song.plays)}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="state__copy">No hay scrobbles en este periodo.</p>
          )}
        </div>

        <footer className="recap-foot">
          <button type="button" className="btn btn--ghost" onClick={copySummary}>
            {copied ? <IconCheck size={17} /> : <IconCopy size={17} />}
            {copied ? 'Copiado' : 'Copiar resumen'}
          </button>
          <button type="button" className="btn btn--primary" onClick={onClose}>
            Cerrar
          </button>
        </footer>
      </article>
    </div>
  )
}
