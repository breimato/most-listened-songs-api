import { IconClose, IconSearch } from './Icons'

type FilterVariant = 'songs' | 'artists' | 'activity'

interface FiltersProps {
  variant: FilterVariant
  limit: number
  year: string
  artist: string
  onLimitChange: (limit: number) => void
  onYearChange: (year: string) => void
  onArtistChange: (artist: string) => void
}

const LIMIT_OPTIONS = [10, 25, 50, 100]

export function Filters({
  variant,
  limit,
  year,
  artist,
  onLimitChange,
  onYearChange,
  onArtistChange,
}: FiltersProps) {
  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: 6 }, (_, i) => currentYear - i)

  return (
    <div className="filters">
      {variant !== 'activity' ? (
        <div className="seg" role="group" aria-label="Cantidad">
          {LIMIT_OPTIONS.map((value) => (
            <button
              key={value}
              type="button"
              className={`seg__btn${limit === value ? ' is-active' : ''}`}
              onClick={() => onLimitChange(value)}
              aria-pressed={limit === value}
            >
              {value}
            </button>
          ))}
        </div>
      ) : null}

      <label className="select-field">
        <span className="visually-hidden">Año</span>
        <select value={year} onChange={(event) => onYearChange(event.target.value)}>
          <option value="">Todos los años</option>
          {years.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>

      {variant === 'songs' ? (
        <div className="search">
          <IconSearch size={17} className="search__icon" />
          <input
            type="search"
            placeholder="Buscar artista"
            aria-label="Filtrar por artista"
            value={artist}
            onChange={(event) => onArtistChange(event.target.value)}
          />
          {artist ? (
            <button
              type="button"
              className="search__clear"
              onClick={() => onArtistChange('')}
              aria-label="Quitar filtro de artista"
            >
              <IconClose size={14} />
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
