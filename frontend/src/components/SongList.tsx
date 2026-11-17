import type { CSSProperties } from 'react'

import type { Song } from '../types/api'
import { formatNumber } from '../utils/format'
import { CoverArt } from './CoverArt'
import { Equalizer } from './Icons'

interface SongListProps {
  songs: Song[] | undefined
  isLoading: boolean
  isError: boolean
  emptyHint?: string
}

export function SongList({ songs, isLoading, isError, emptyHint }: SongListProps) {
  if (isLoading) {
    return (
      <ol className="song-list" aria-busy="true">
        {Array.from({ length: 8 }).map((_, index) => (
          <li key={index} className="song-row song-row--skeleton">
            <span className="skeleton skeleton--rank" />
            <span className="skeleton skeleton--cover" />
            <span className="skeleton skeleton--title" />
            <span className="skeleton skeleton--album" />
            <span className="skeleton skeleton--plays" />
          </li>
        ))}
      </ol>
    )
  }

  if (isError) {
    return (
      <div className="state">
        <p className="state__title">No se pudo cargar el ranking</p>
        <p className="state__copy">Comprueba que la API esté disponible y vuelve a intentarlo.</p>
      </div>
    )
  }

  if (!songs?.length) {
    return (
      <div className="state">
        <p className="state__title">Todavía no hay canciones</p>
        <p className="state__copy">
          {emptyHint ?? 'Sincroniza con Last.fm para importar tus scrobbles.'}
        </p>
      </div>
    )
  }

  const maxPlays = songs[0]?.plays ?? 1

  return (
    <ol className="song-list">
      <li className="song-list__head" aria-hidden="true">
        <span>#</span>
        <span>Título</span>
        <span>Álbum</span>
        <span className="song-list__head-right">Reproducciones</span>
      </li>
      {songs.map((song, index) => (
        <li key={`${song.id}-${index}`} className="song-row" style={{ '--row': index } as CSSProperties}>
          <span className={`song-row__rank${index < 3 ? ' is-top' : ''}`}>
            {index === 0 ? <Equalizer /> : String(index + 1).padStart(2, '0')}
          </span>
          <div className="song-row__main">
            <CoverArt artist={song.artist} title={song.title} size="sm" />
            <div className="song-row__text">
              <p className="song-row__title">{song.title}</p>
              <p className="song-row__artist">{song.artist}</p>
            </div>
          </div>
          <span className="song-row__album">{song.album || '—'}</span>
          <div className="song-row__plays">
            <span className="song-row__count">{formatNumber(song.plays)}</span>
            <span className="song-row__bar" aria-hidden="true">
              <span style={{ width: `${Math.max(4, (song.plays / maxPlays) * 100)}%` }} />
            </span>
          </div>
        </li>
      ))}
    </ol>
  )
}
