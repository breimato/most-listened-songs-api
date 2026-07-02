import type { Artist } from '../types/api'
import { formatNumber } from '../utils/format'

interface TopArtistsListProps {
  artists: Artist[] | undefined
  isLoading: boolean
}

export function TopArtistsList({ artists, isLoading }: TopArtistsListProps) {
  if (isLoading) {
    return <div className="panel-state">Cargando artistas…</div>
  }

  if (!artists?.length) {
    return <div className="panel-state">Sin artistas en este periodo.</div>
  }

  const maxPlays = artists[0]?.plays ?? 1

  return (
    <ol className="ranking-list ranking-list--compact">
      {artists.map((item, index) => (
        <li key={item.artist} className="ranking-item">
          <span className="ranking-item__rank">{index + 1}</span>
          <div className="ranking-item__body">
            <div className="ranking-item__header">
              <div>
                <p className="ranking-item__title">{item.artist}</p>
                <p className="ranking-item__subtitle">
                  {formatNumber(item.songs)} canciones
                </p>
              </div>
              <span className="ranking-item__plays">{formatNumber(item.plays)}</span>
            </div>
            <div className="ranking-item__bar ranking-item__bar--accent" aria-hidden="true">
              <span style={{ width: `${(item.plays / maxPlays) * 100}%` }} />
            </div>
          </div>
        </li>
      ))}
    </ol>
  )
}
