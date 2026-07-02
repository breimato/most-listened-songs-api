interface FiltersProps {
  limit: number
  year: string
  artist: string
  onLimitChange: (limit: number) => void
  onYearChange: (year: string) => void
  onArtistChange: (artist: string) => void
}

const LIMIT_OPTIONS = [10, 25, 50, 100]

export function Filters({
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
      <label className="filter-field">
        <span>Top</span>
        <select value={limit} onChange={(e) => onLimitChange(Number(e.target.value))}>
          {LIMIT_OPTIONS.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>

      <label className="filter-field">
        <span>Año</span>
        <select value={year} onChange={(e) => onYearChange(e.target.value)}>
          <option value="">Todos</option>
          {years.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>

      <label className="filter-field filter-field--grow">
        <span>Artista</span>
        <input
          type="search"
          placeholder="Filtrar por artista…"
          value={artist}
          onChange={(e) => onArtistChange(e.target.value)}
        />
      </label>
    </div>
  )
}
