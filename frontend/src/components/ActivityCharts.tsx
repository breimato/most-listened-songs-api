import type { Stats } from '../types/api'
import { formatMonth, formatNumber, hourLabel } from '../utils/format'

interface ActivityChartsProps {
  stats: Stats | undefined
  isLoading: boolean
}

export function ActivityCharts({ stats, isLoading }: ActivityChartsProps) {
  if (isLoading) {
    return <div className="panel-state">Cargando actividad…</div>
  }

  if (!stats) return null

  const months = Object.entries(stats.plays_by_month)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-12)

  const hours = Object.entries(stats.plays_by_hour)
    .map(([hour, plays]) => ({ hour: Number(hour), plays }))
    .sort((a, b) => a.hour - b.hour)

  const maxMonth = Math.max(...months.map(([, plays]) => plays), 1)
  const maxHour = Math.max(...hours.map((h) => h.plays), 1)

  return (
    <div className="charts">
      <section className="chart-card">
        <h3>Reproducciones por mes</h3>
        {months.length ? (
          <div className="bar-chart bar-chart--months">
            {months.map(([month, plays]) => (
              <div key={month} className="bar-chart__item">
                <div className="bar-chart__bar-wrap">
                  <div
                    className="bar-chart__bar"
                    style={{ height: `${(plays / maxMonth) * 100}%` }}
                    title={`${formatMonth(month)}: ${formatNumber(plays)}`}
                  />
                </div>
                <span className="bar-chart__label">{formatMonth(month)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="panel-state">Sin datos mensuales.</p>
        )}
      </section>

      <section className="chart-card">
        <h3>Reproducciones por hora</h3>
        {hours.length ? (
          <div className="bar-chart bar-chart--hours">
            {hours.map(({ hour, plays }) => (
              <div key={hour} className="bar-chart__item">
                <div className="bar-chart__bar-wrap">
                  <div
                    className="bar-chart__bar bar-chart__bar--accent"
                    style={{ height: `${(plays / maxHour) * 100}%` }}
                    title={`${hourLabel(hour)}: ${formatNumber(plays)}`}
                  />
                </div>
                <span className="bar-chart__label">{hour}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="panel-state">Sin datos por hora.</p>
        )}
      </section>
    </div>
  )
}
