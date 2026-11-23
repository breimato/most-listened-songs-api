import type { Artist, Song } from '../types/api'
import { formatNumber } from '../utils/format'
import { CoverArt } from './CoverArt'

interface ArtistListProps {
  artists: Artist[] | undefined
  songsPool: Song[] | undefined
  isLoading: boolean
}

function songsLabel(count: number): string {
  return `${formatNumber(count)} ${count === 1 ? 'canción' : 'canciones'}`
}

function normalize(value: string): string {
  return value.trim().toLowerCase()
}

function findSongForArtist(songs: Song[] | undefined, artist: string): Song | undefined {
  if (!songs?.length) return undefined
  const exact = songs.find((song) => normalize(song.artist) === normalize(artist))
  if (exact) return exact
  return songs.find(
    (song) =>
      normalize(song.artist).includes(normalize(artist)) ||
      normalize(artist).includes(normalize(song.artist)),
  )
}

export function ArtistList({ artists, songsPool, isLoading }: ArtistListProps) {
  if (isLoading) {
    return (
      <div className="artist-podium" aria-busy="true">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="artist-card artist-card--skeleton">
            <span className="skeleton skeleton--vinyl" />
            <span className="skeleton skeleton--title" />
            <span className="skeleton skeleton--plays" />
          </div>
        ))}
      </div>
    )
  }

  if (!artists?.length) {
    return (
      <div className="state">
        <p className="state__title">Sin artistas en este periodo</p>
        <p className="state__copy">Prueba con otro año o vuelve a sincronizar.</p>
      </div>
    )
  }

  const maxPlays = artists[0]?.plays ?? 1
  const podium = artists.slice(0, 3)
  const rest = artists.slice(3)
  const coverFor = (artist: Artist) => findSongForArtist(songsPool, artist.artist)

  return (
    <div className="artists">
      <div className="artist-podium">
        {podium.map((artist, index) => {
          const song = coverFor(artist)
          return (
            <article key={artist.artist} className="artist-card">
              <span className="artist-card__rank">{index + 1}</span>
              <div className="artist-vinyl">
                <CoverArt
                  artist={artist.artist}
                  title={song?.title ?? ''}
                  size="lg"
                  round
                />
              </div>
              <h3 className="artist-card__name">{artist.artist}</h3>
              <p className="artist-card__meta">
                {formatNumber(artist.plays)} reproducciones
              </p>
              <p className="artist-card__songs">{songsLabel(artist.songs)}</p>
            </article>
          )
        })}
      </div>

      {rest.length ? (
        <ol className="artist-list">
          {rest.map((artist, index) => {
            const song = coverFor(artist)
            return (
              <li key={artist.artist} className="artist-row">
                <span className="artist-row__rank">
                  {String(index + 4).padStart(2, '0')}
                </span>
                <CoverArt
                  artist={artist.artist}
                  title={song?.title ?? ''}
                  size="sm"
                  round
                />
                <div className="artist-row__text">
                  <p className="artist-row__name">{artist.artist}</p>
                  <p className="artist-row__meta">
                    {songsLabel(artist.songs)}
                  </p>
                </div>
                <div className="artist-row__plays">
                  <span>{formatNumber(artist.plays)}</span>
                  <span className="artist-row__bar" aria-hidden="true">
                    <span
                      style={{
                        width: `${Math.max(4, (artist.plays / maxPlays) * 100)}%`,
                      }}
                    />
                  </span>
                </div>
              </li>
            )
          })}
        </ol>
      ) : null}
    </div>
  )
}
