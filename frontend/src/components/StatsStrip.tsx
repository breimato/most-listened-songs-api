import type { Stats } from '../types/api'
import { formatDate, formatNumber } from '../utils/format'

interface StatsStripProps {
  stats: Stats | undefined
  isLoading: boolean
}

export function StatsStrip({ stats, isLoading }: StatsStripProps) {
  const items = [
    { label: 'Reproducciones', value: stats ? formatNumber(stats.total_plays) : '—' },
    { label: 'Canciones', value: stats ? formatNumber(stats.total_songs) : '—' },
    { label: 'Artistas', value: stats ? formatNumber(stats.total_artists) : '—' },
    {
      label: 'Primera escucha',
      value: stats ? formatDate(stats.first_listen) : '—',
      small: true,
    },
  ]

  return (
    <dl className={`stats-strip${isLoading ? ' is-loading' : ''}`} aria-label="Resumen del periodo">
      {items.map((item) => (
        <div key={item.label} className="stats-strip__item">
          <dt>{item.label}</dt>
          <dd className={item.small ? 'is-small' : undefined}>{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}
