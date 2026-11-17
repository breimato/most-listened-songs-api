import { useState } from 'react'
import type { CSSProperties } from 'react'

import type { Obsession, ObsessionDay } from '../types/api'
import { formatDayLong, formatDayRange, formatNumber } from '../utils/format'
import { CoverArt } from './CoverArt'
import { IconChevron, IconFlame } from './Icons'

interface ObsessionsViewProps {
  obsessions: Obsession[] | undefined
  isLoading: boolean
  onOpenTimeline: (obsession: Obsession) => void
}

type TierFilter = 'all' | 'obsesion' | 'racha'

const TIER_LABEL: Record<Obsession['tier'], string> = {
  obsesion: 'Obsesión',
  racha: 'Racha',
}

function heatLevel(plays: number): number {
  if (plays <= 0) return 0
  if (plays === 1) return 1
  if (plays <= 3) return 2
  if (plays <= 6) return 3
  return 4
}

function MiniHeat({ days }: { days: ObsessionDay[] }) {
  return (
    <span
      className="mini-heat"
      style={{ '--heat-days': days.length } as CSSProperties}
      aria-hidden="true"
    >
      {days.map((day) => (
        <span
          key={day.date}
          className={`mini-heat__cell mini-heat__cell--${heatLevel(day.plays)}`}
          title={`${formatDayLong(day.date)}: ${day.plays} reproducciones`}
        />
      ))}
    </span>
  )
}

function ObsessionRow({
  obsession,
  onOpen,
}: {
  obsession: Obsession
  onOpen: (obsession: Obsession) => void
}) {
  return (
    <button
      type="button"
      className={`obsession-row obsession-row--${obsession.tier}`}
      onClick={() => onOpen(obsession)}
    >
      <CoverArt artist={obsession.artist} title={obsession.title} size="md" />

      <span className="obsession-row__main">
        <span className="obsession-row__title-line">
          <span className="obsession-row__title">{obsession.title}</span>
          <span className={`tier-badge tier-badge--${obsession.tier}`}>
            <IconFlame size={11} />
            {TIER_LABEL[obsession.tier]}
          </span>
        </span>
        <span className="obsession-row__artist">{obsession.artist}</span>
        <span className="obsession-row__period">
          {formatDayRange(obsession.start, obsession.end)}
        </span>
      </span>

      <span className="obsession-row__heat">
        <MiniHeat days={obsession.days} />
      </span>

      <span className="obsession-row__stats">
        <span>
          <strong>{obsession.strong_days}</strong>/{obsession.span_days} días
        </span>
        <span>
          <strong>{formatNumber(obsession.plays)}</strong> plays
        </span>
        <span className="obsession-row__peak">pico {obsession.peak_plays}</span>
      </span>

      <IconChevron size={16} className="obsession-row__chevron" />
    </button>
  )
}

export function ObsessionsView({
  obsessions,
  isLoading,
  onOpenTimeline,
}: ObsessionsViewProps) {
  const [tier, setTier] = useState<TierFilter>('all')

  if (isLoading) {
    return (
      <div className="obsessions" aria-busy="true">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="obsession-row obsession-row--skeleton">
            <span className="skeleton skeleton--cover" />
            <span className="skeleton skeleton--title" />
            <span className="skeleton skeleton--heat" />
            <span className="skeleton skeleton--plays" />
          </div>
        ))}
      </div>
    )
  }

  const all = obsessions ?? []
  const filtered = tier === 'all' ? all : all.filter((item) => item.tier === tier)
  const groups: Array<{ tier: Obsession['tier']; label: string; items: Obsession[] }> = [
    { tier: 'obsesion', label: 'Obsesiones', items: filtered.filter((i) => i.tier === 'obsesion') },
    { tier: 'racha', label: 'Rachas', items: filtered.filter((i) => i.tier === 'racha') },
  ]

  return (
    <div className="obsessions">
      <div className="obsessions__toolbar">
        <div className="seg" role="group" aria-label="Tipo de episodio">
          {(
            [
              ['all', 'Todas'],
              ['obsesion', 'Obsesiones'],
              ['racha', 'Rachas'],
            ] as Array<[TierFilter, string]>
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={`seg__btn${tier === value ? ' is-active' : ''}`}
              onClick={() => setTier(value)}
              aria-pressed={tier === value}
            >
              {label}
            </button>
          ))}
        </div>
        <p className="obsessions__hint">
          Día fuerte = 2 o más reproducciones de la misma canción.
        </p>
      </div>

      {!filtered.length ? (
        <div className="state">
          <p className="state__title">Todavía no hay episodios</p>
          <p className="state__copy">
            Necesitas al menos una semana escuchando una canción casi todos los
            días y varias veces. Vuelve cuando acumules más historial.
          </p>
        </div>
      ) : (
        groups.map((group) =>
          group.items.length ? (
            <section key={group.tier} className="obsession-group">
              <header className="obsession-group__head">
                <h3>{group.label}</h3>
                <span>{group.items.length}</span>
              </header>
              <div className="obsession-list">
                {group.items.map((obsession) => (
                  <ObsessionRow
                    key={obsession.id}
                    obsession={obsession}
                    onOpen={onOpenTimeline}
                  />
                ))}
              </div>
            </section>
          ) : null,
        )
      )}
    </div>
  )
}
