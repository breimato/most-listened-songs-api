import type { CSSProperties } from 'react'

import type { Obsession, ObsessionDay } from '../types/api'
import { formatDayLong } from '../utils/format'

interface CalendarHeatmapProps {
  days: ObsessionDay[]
  episodes: Obsession[]
  highlightId?: string | null
}

function parseDay(value: string): Date {
  return new Date(`${value}T12:00:00`)
}

function dayKey(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function addDays(value: Date, amount: number): Date {
  const next = new Date(value)
  next.setDate(next.getDate() + amount)
  return next
}

function mondayOf(value: Date): Date {
  const date = new Date(value)
  const weekday = (date.getDay() + 6) % 7
  date.setDate(date.getDate() - weekday)
  date.setHours(12, 0, 0, 0)
  return date
}

function level(plays: number): number {
  if (plays <= 0) return 0
  if (plays === 1) return 1
  if (plays <= 3) return 2
  if (plays <= 6) return 3
  return 4
}

const MONTH_SHORT = new Intl.DateTimeFormat('es-ES', { month: 'short' })
const WEEKDAYS = ['L', 'M', 'X', 'J', 'V', 'S', 'D']

export function CalendarHeatmap({ days, episodes, highlightId }: CalendarHeatmapProps) {
  if (!days.length) {
    return <p className="state__copy">No hay reproducciones en este periodo.</p>
  }

  const ordered = [...days].sort((a, b) => a.date.localeCompare(b.date))
  const counts = new Map(ordered.map((day) => [day.date, day.plays]))
  const first = parseDay(ordered[0].date)
  const last = parseDay(ordered[ordered.length - 1].date)
  const start = mondayOf(first)
  const finalSunday = addDays(mondayOf(last), 6)

  const weeks: Date[][] = []
  for (let cursor = start; cursor <= finalSunday; cursor = addDays(cursor, 7)) {
    weeks.push(Array.from({ length: 7 }, (_, index) => addDays(cursor, index)))
  }

  const highlight = episodes.find((episode) => episode.id === highlightId)
  const highlightStart = highlight ? parseDay(highlight.start) : null
  const highlightEnd = highlight ? parseDay(highlight.end) : null

  const monthLabels: Array<{ label: string; index: number }> = []
  let lastMonth = -1
  weeks.forEach((week, index) => {
    for (const day of week) {
      if (day.getDate() === 1 && day.getMonth() !== lastMonth) {
        monthLabels.push({ label: MONTH_SHORT.format(day), index })
        lastMonth = day.getMonth()
        break
      }
    }
  })
  if (!monthLabels.length || monthLabels[0].index > 0) {
    monthLabels.unshift({ label: MONTH_SHORT.format(first), index: 0 })
  }

  return (
    <figure className="heatmap">
      <div className="heatmap__scroll">
        <div
          className="heatmap__inner"
          style={{ '--heat-weeks': weeks.length } as CSSProperties}
        >
          <div
            className="heatmap__months"
            style={{ gridTemplateColumns: `repeat(${weeks.length}, var(--heat-cell))` }}
          >
            {monthLabels.map((month) => (
              <span
                key={`${month.label}-${month.index}`}
                style={{ gridColumnStart: month.index + 1 }}
              >
                {month.label}
              </span>
            ))}
          </div>

          <div className="heatmap__body">
            <div className="heatmap__weekdays" aria-hidden="true">
              {WEEKDAYS.map((day) => (
                <span key={day}>{day}</span>
              ))}
            </div>

            <div
              className="heatmap__grid"
              style={{ gridTemplateColumns: `repeat(${weeks.length}, var(--heat-cell))` }}
            >
              {weeks.flat().map((day) => {
                const key = dayKey(day)
                const plays = counts.get(key) ?? 0
                const inRange = day >= start && day <= finalSunday
                const isHighlighted =
                  highlightStart !== null &&
                  highlightEnd !== null &&
                  day >= highlightStart &&
                  day <= highlightEnd
                return (
                  <span
                    key={key}
                    className={`heatmap__cell${isHighlighted ? ' is-highlighted' : ''}`}
                    data-level={inRange ? level(plays) : 0}
                    title={`${formatDayLong(key)} · ${plays} reproducciones`}
                  />
                )
              })}
            </div>
          </div>
        </div>
      </div>

      <figcaption className="heatmap__legend">
        <span>Menos</span>
        <span className="heatmap__legend-cells" aria-hidden="true">
          {[0, 1, 2, 3, 4].map((value) => (
            <i key={value} data-level={value} />
          ))}
        </span>
        <span>Más</span>
      </figcaption>
    </figure>
  )
}
