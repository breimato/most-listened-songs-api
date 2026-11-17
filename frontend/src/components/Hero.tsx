import { useArtwork } from '../hooks/useArtwork'
import type { Song, Stats } from '../types/api'
import { formatNumber } from '../utils/format'
import type { RecapPeriod } from '../utils/recaps'
import { CoverArt } from './CoverArt'
import { IconSparkle } from './Icons'

interface HeroProps {
  song: Song | undefined
  stats: Stats | undefined
  recap: RecapPeriod | null
  isLoading: boolean
  onOpenRecap: (recap: RecapPeriod) => void
  onGoArtists: () => void
}

export function Hero({
  song,
  stats,
  recap,
  isLoading,
  onOpenRecap,
  onGoArtists,
}: HeroProps) {
  const backdrop = useArtwork(song?.artist ?? '', song?.title ?? '')

  return (
    <section className="hero" aria-label="Tu música">
      <div className="hero__wash" aria-hidden="true">
        {backdrop ? <img src={backdrop} alt="" /> : null}
      </div>

      <div className="hero__inner">
        <div className="hero__copy">
          <h1 className="hero__title">Tus temas más escuchados</h1>
          <p className="hero__lead">
            Todo lo que suena en tu móvil y en tu PC, ordenado por reproducciones.
          </p>

          <div className="hero__actions">
            {recap ? (
              <button
                type="button"
                className="btn btn--primary"
                onClick={() => onOpenRecap(recap)}
              >
                <IconSparkle size={17} />
                {recap.title}
              </button>
            ) : null}
            <button type="button" className="btn btn--ghost" onClick={onGoArtists}>
              Ver artistas
            </button>
            <span className="hero__hint">
              {stats?.last_listen
                ? `Actualizado con tu última escucha del ${new Intl.DateTimeFormat('es-ES', {
                    day: 'numeric',
                    month: 'long',
                  }).format(new Date(stats.last_listen))}`
                : 'Conectado a Last.fm'}
            </span>
          </div>
        </div>

        <article className={`feature${isLoading ? ' is-loading' : ''}`}>
          {song ? (
            <>
              <div className="feature__cover">
                <CoverArt artist={song.artist} title={song.title} size="hero" src={backdrop} />
                <span className="feature__rank">#1</span>
              </div>
              <div className="feature__text">
                <h2 className="feature__title">{song.title}</h2>
                <p className="feature__artist">{song.artist}</p>
                {song.album ? <p className="feature__album">{song.album}</p> : null}
                <span className="feature__plays">
                  {formatNumber(song.plays)} reproducciones
                </span>
              </div>
            </>
          ) : (
            <div className="feature__empty">
              <p className="feature__empty-title">Tu número 1 aparecerá aquí</p>
              <p className="feature__empty-copy">
                Sincroniza con Last.fm para importar tu historial.
              </p>
            </div>
          )}
        </article>
      </div>
    </section>
  )
}
