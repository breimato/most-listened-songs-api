import type { RecapPeriod } from '../utils/recaps'
import { NotificationsBell } from './NotificationsBell'
import { SyncButton } from './SyncButton'
import { IconLogout } from './Icons'
import type { Tab } from './Sidebar'

interface TopBarProps {
  tab: Tab
  recaps: RecapPeriod[]
  unread: number
  onOpenRecap: (recap: RecapPeriod) => void
  onSyncMessage: (message: string, type: 'success' | 'error') => void
  onLock: () => void
}

const TAB_LABEL: Record<Tab, string> = {
  songs: 'Canciones',
  artists: 'Artistas',
  activity: 'Actividad',
}

export function TopBar({
  tab,
  recaps,
  unread,
  onOpenRecap,
  onSyncMessage,
  onLock,
}: TopBarProps) {
  return (
    <header className="topbar">
      <div className="topbar__context">
        <span className="topbar__brand" aria-hidden="true">
          <i />
          <i />
          <i />
          <i />
        </span>
        <span className="topbar__crumb">Tu música</span>
        <span className="topbar__slash" aria-hidden="true">
          /
        </span>
        <span className="topbar__name">Scrobbles</span>
        <span className="topbar__section">{TAB_LABEL[tab]}</span>
      </div>

      <div className="topbar__actions">
        <NotificationsBell
          recaps={recaps}
          unread={unread}
          onOpenRecap={onOpenRecap}
        />
        <SyncButton onMessage={onSyncMessage} />
        <button
          type="button"
          className="icon-btn icon-btn--lock"
          onClick={onLock}
          aria-label="Cerrar sesión"
          title="Cerrar sesión"
        >
          <IconLogout size={18} />
        </button>
      </div>
    </header>
  )
}
