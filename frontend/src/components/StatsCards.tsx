import type { Stats } from '../types/api'
import { dayLabel, formatDate, formatNumber } from '../utils/format'

interface StatsCardsProps {
  stats: Stats | undefined
  isLoading: boolean
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  const items: Array<{
    label: string
    value: string | number | undefined
    text?: boolean
  }> = [
    { label: 'Reproducciones', value: stats?.total_plays },
    { label: 'Canciones', value: stats?.total_songs },
    { label: 'Artistas', value: stats?.total_artists },
    { label: 'Día favorito', value: stats ? dayLabel(stats.top_day) : undefined, text: true },
  ]

  return (
    <section className="stats-grid" aria-label="Resumen">
      {items.map((item) => (
        <article key={item.label} className="stat-card">
          <p className="stat-card__label">{item.label}</p>
          <p className="stat-card__value">
            {isLoading
              ? '…'
              : item.text
                ? String(item.value ?? '—')
                : formatNumber(Number(item.value ?? 0))}
          </p>
        </article>
      ))}
      {stats && (
        <article className="stat-card stat-card--wide">
          <p className="stat-card__label">Periodo</p>
          <p className="stat-card__value stat-card__value--small">
            {formatDate(stats.first_listen)} → {formatDate(stats.last_listen)}
          </p>
        </article>
      )}
    </section>
  )
}
