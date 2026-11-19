import { IconChart, IconFlame, IconMic, IconMoon, IconMusic } from './Icons'
import type { Tab } from './Sidebar'

interface MobileNavProps {
  tab: Tab
  onTab: (tab: Tab) => void
}

const ITEMS = [
  { id: 'songs' as const, label: 'Canciones', icon: IconMusic },
  { id: 'obsessions' as const, label: 'Obsesiones', icon: IconFlame },
  { id: 'artists' as const, label: 'Artistas', icon: IconMic },
  { id: 'sleep' as const, label: 'Dormir', icon: IconMoon },
  { id: 'activity' as const, label: 'Actividad', icon: IconChart },
]

export function MobileNav({ tab, onTab }: MobileNavProps) {
  return (
    <nav className="mobile-nav" aria-label="Navegación">
      {ITEMS.map((item) => {
        const Icon = item.icon
        const active = tab === item.id
        return (
          <button
            key={item.id}
            type="button"
            className={`mobile-nav__item${active ? ' is-active' : ''}`}
            onClick={() => onTab(item.id)}
            aria-current={active ? 'page' : undefined}
          >
            <Icon size={21} />
            <span>{item.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
