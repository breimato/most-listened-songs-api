import type { CSSProperties } from 'react'

import type { RecapPeriod } from '../utils/recaps'
import { recapStatusLabel } from '../utils/recaps'
import { relativeTime } from '../utils/format'
import { IconChart, IconFlame, IconMic, IconMoon, IconMusic, IconSparkle } from './Icons'

export type Tab = 'songs' | 'artists' | 'activity' | 'obsessions' | 'sleep'

interface SidebarProps {
  tab: Tab
  onTab: (tab: Tab) => void
  recaps: RecapPeriod[]
  onOpenRecap: (recap: RecapPeriod) => void
  totalPlays?: number
  lastListen?: string | null
}

const NAV = [
  { id: 'songs' as const, label: 'Canciones', icon: IconMusic },
  { id: 'obsessions' as const, label: 'Obsesiones', icon: IconFlame },
  { id: 'artists' as const, label: 'Artistas', icon: IconMic },
  { id: 'sleep' as const, label: 'Para dormir', icon: IconMoon },
  { id: 'activity' as const, label: 'Actividad', icon: IconChart },
]

export function Sidebar({
  tab,
  onTab,
  recaps,
  onOpenRecap,
  totalPlays,
  lastListen,
}: SidebarProps) {
  const visibleRecaps = recaps.filter((recap) => recap.status !== 'upcoming').slice(0, 3)

  return (
    <aside className="sidebar" aria-label="Navegación principal">
      <button type="button" className="brand" onClick={() => onTab('songs')}>
        <span className="brand__mark" aria-hidden="true">
          <i />
          <i />
          <i />
          <i />
        </span>
        <span className="brand__text">
          <span className="brand__name">GroBeats FM</span>
          <span className="brand__sub">Tu historial musical</span>
        </span>
      </button>

      <nav className="nav" aria-label="Secciones">
        {NAV.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              type="button"
              className={`nav__item${tab === item.id ? ' is-active' : ''}`}
              onClick={() => onTab(item.id)}
              aria-current={tab === item.id ? 'page' : undefined}
            >
              <Icon />
              {item.label}
            </button>
          )
        })}
      </nav>

      <section className="recaps" aria-label="Recaps de temporada">
        <div className="recaps__head">
          <span>Recaps</span>
          <IconSparkle size={16} />
        </div>

        {visibleRecaps.length ? (
          <div className="recaps__list">
            {visibleRecaps.map((recap) => (
              <button
                key={recap.id}
                type="button"
                className="recap-link"
                onClick={() => onOpenRecap(recap)}
                style={
                  {
                    '--recap-from': recap.palette.from,
                    '--recap-to': recap.palette.to,
                  } as CSSProperties
                }
              >
                <span className="recap-link__dot" aria-hidden="true" />
                <span className="recap-link__text">
                  <span className="recap-link__label">{recap.label}</span>
                  <span className="recap-link__range">{recap.range}</span>
                </span>
                <span
                  className={`recap-link__status${recap.status === 'available' ? ' is-new' : ''}`}
                >
                  {recapStatusLabel(recap.status)}
                </span>
              </button>
            ))}
          </div>
        ) : (
          <p className="recaps__empty">
            Los recaps aparecen al terminar cada temporada.
          </p>
        )}
      </section>

      <div className="sidebar__bottom">
        <div className="sidebar__fact">
          <span className="sidebar__fact-label">Reproducciones</span>
          <span className="sidebar__fact-value">
            {totalPlays !== undefined ? new Intl.NumberFormat('es-ES').format(totalPlays) : '—'}
          </span>
        </div>
        <div className="sidebar__fact">
          <span className="sidebar__fact-label">Última escucha</span>
          <span className="sidebar__fact-value sidebar__fact-value--small">
            {relativeTime(lastListen ?? null)}
          </span>
        </div>
      </div>
    </aside>
  )
}
