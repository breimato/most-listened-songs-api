import type { Song } from '../types/api'
import { formatNumber } from '../utils/format'

interface TopSongsListProps {
  songs: Song[] | undefined
  isLoading: boolean
  isError: boolean
}

export function TopSongsList({ songs, isLoading, isError }: TopSongsListProps) {
  if (isLoading) {
    return <div className="panel-state">Cargando canciones…</div>
  }

  if (isError) {
    return (
      <div className="panel-state panel-state--error">
        No se pudo cargar el ranking. ¿Está el servidor en marcha?
      </div>
    )
  }

  if (!songs?.length) {
    return (
      <div className="panel-state">
        Sin datos todavía. Ejecuta una sincronización con Last.fm para importar scrobbles.
      </div>
    )
  }

  const maxPlays = songs[0]?.plays ?? 1

  return (
    <ol className="ranking-list">
      {songs.map((song, index) => (
        <li key={song.id} className="ranking-item">
          <span className="ranking-item__rank">{index + 1}</span>
          <div className="ranking-item__body">
            <div className="ranking-item__header">
              <div>
                <p className="ranking-item__title">{song.title}</p>
                <p className="ranking-item__subtitle">
                  {song.artist}
                  {song.album ? ` · ${song.album}` : ''}
                </p>
              </div>
              <span className="ranking-item__plays">{formatNumber(song.plays)}</span>
            </div>
            <div className="ranking-item__bar" aria-hidden="true">
              <span style={{ width: `${(song.plays / maxPlays) * 100}%` }} />
            </div>
          </div>
        </li>
      ))}
    </ol>
  )
}
