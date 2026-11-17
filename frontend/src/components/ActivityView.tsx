import type { Stats } from '../types/api'
import {
  formatDate,
  formatMonth,
  formatMonthLong,
  formatNumber,
  hourLabel,
} from '../utils/format'

interface ActivityViewProps {
  stats: Stats | undefined
  isLoading: boolean
}

function topDayLabel(day: string): string {
  if (!day) return '—'
  const date = new Date(`${day}T12:00:00`)
  if (Number.isNaN(date.getTime())) return day
  return new Intl.DateTimeFormat('es-ES', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
  }).format(date)
}

export function ActivityView({ stats, isLoading }: ActivityViewProps) {
  if (isLoading) {
    return (
      <div className="activity" aria-busy="true">
        <div className="skeleton skeleton--chart" />
        <div className="skeleton skeleton--chart" />
      </div>
    )
  }

  if (!stats) return null

  const months = Object.entries(stats.plays_by_month)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-12)

  const hours = Array.from({ length: 24 }, (_, hour) => ({
    hour,
    plays: Number(stats.plays_by_hour[String(hour)] ?? 0),
  }))

  const maxMonth = Math.max(...months.map(([, plays]) => plays), 1)
  const maxHour = Math.max(...hours.map((entry) => entry.plays), 1)
  const peakHour = hours.reduce((best, entry) => (entry.plays > best.plays ? entry : best), hours[0])
  const periodTotal = months.reduce((sum, [, plays]) => sum + plays, 0)

  return (
    <div className="activity">
      <section className="chart-block">
        <header className="chart-block__head">
          <h2>Por mes</h2>
          <p>
            {formatNumber(periodTotal)} reproducciones en los últimos {months.length} meses
          </p>
        </header>

        {months.length ? (
          <div className="chart chart--months" role="img" aria-label="Reproducciones por mes">
            {months.map(([month, plays]) => {
              const height = Math.max(2, (plays / maxMonth) * 100)
              return (
                <div key={month} className="chart__col">
                  <span className="chart__value">{formatNumber(plays)}</span>
                  <span className="chart__track">
                    <span className="chart__fill" style={{ height: `${height}%` }} />
                  </span>
                  <span className="chart__label" title={formatMonthLong(month)}>
                    {formatMonth(month)}
                  </span>
                </div>
              )
            })}
          </div>
        ) : (
          <p className="state__copy">Sin datos mensuales.</p>
        )}
      </section>

      <section className="chart-block">
        <header className="chart-block__head">
          <h2>Por hora</h2>
          <p>Tu hora punta es las {hourLabel(peakHour.hour)}</p>
        </header>

        {hours.some((entry) => entry.plays > 0) ? (
          <div className="chart chart--hours" role="img" aria-label="Reproducciones por hora">
            {hours.map(({ hour, plays }) => {
              const height = Math.max(2, (plays / maxHour) * 100)
              return (
                <div key={hour} className="chart__col">
                  <span className="chart__value">{formatNumber(plays)}</span>
                  <span className="chart__track">
                    <span
                      className="chart__fill chart__fill--hour"
                      style={{ height: `${height}%` }}
                    />
                  </span>
                  <span className="chart__label">
                    {hour % 3 === 0 ? hourLabel(hour).slice(0, 2) : ''}
                  </span>
                </div>
              )
            })}
          </div>
        ) : (
          <p className="state__copy">Sin datos por hora.</p>
        )}
      </section>

      <dl className="facts">
        <div>
          <dt>Día con más música</dt>
          <dd>{topDayLabel(stats.top_day)}</dd>
        </div>
        <div>
          <dt>Primera escucha</dt>
          <dd>{formatDate(stats.first_listen)}</dd>
        </div>
        <div>
          <dt>Última escucha</dt>
          <dd>{formatDate(stats.last_listen)}</dd>
        </div>
        <div>
          <dt>Total</dt>
          <dd>{formatNumber(stats.total_plays)}</dd>
        </div>
      </dl>
    </div>
  )
}
