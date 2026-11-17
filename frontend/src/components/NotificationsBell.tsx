import { useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'

import type { Obsession } from '../types/api'
import type { RecapPeriod } from '../utils/recaps'
import { nextRecap, recapStatusLabel } from '../utils/recaps'
import { formatDayRange } from '../utils/format'
import { IconBell, IconChevron, IconFlame, IconSparkle } from './Icons'

interface NotificationsBellProps {
  recaps: RecapPeriod[]
  unread: number
  obsessions: Obsession[]
  unreadObsessions: number
  onOpenRecap: (recap: RecapPeriod) => void
  onOpenObsession: (obsession: Obsession) => void
}

const TIER_LABEL = {
  obsesion: 'Obsesión',
  racha: 'Racha',
} as const

export function NotificationsBell({
  recaps,
  unread,
  obsessions,
  unreadObsessions,
  onOpenRecap,
  onOpenObsession,
}: NotificationsBellProps) {
  const [open, setOpen] = useState(false)
  const wrapper = useRef<HTMLDivElement>(null)
  const totalUnread = unread + unreadObsessions

  useEffect(() => {
    if (!open) return

    const onPointerDown = (event: MouseEvent) => {
      if (!wrapper.current?.contains(event.target as Node)) setOpen(false)
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }

    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  const available = recaps.filter((recap) => recap.status === 'available')
  const inProgress = recaps.filter((recap) => recap.status === 'in-progress')
  const upcoming = nextRecap(recaps)
  const hasContent = available.length > 0 || obsessions.length > 0

  return (
    <div className="notif" ref={wrapper}>
      <button
        type="button"
        className={`icon-btn${open ? ' is-open' : ''}`}
        onClick={() => setOpen((value) => !value)}
        aria-label={totalUnread ? `Novedades (${totalUnread})` : 'Novedades'}
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        <IconBell />
        {totalUnread > 0 ? <span className="icon-btn__dot" aria-hidden="true" /> : null}
      </button>

      {open ? (
        <div className="notif__panel" role="dialog" aria-label="Novedades">
          <div className="notif__head">
            <span>Novedades</span>
            {totalUnread > 0 ? <span className="notif__count">{totalUnread}</span> : null}
          </div>

          {obsessions.length ? (
            <div className="notif__section">
              <span className="notif__section-label">Obsesiones nuevas</span>
              <div className="notif__list">
                {obsessions.map((obsession) => (
                  <button
                    key={obsession.id}
                    type="button"
                    className="notif-item"
                    onClick={() => {
                      setOpen(false)
                      onOpenObsession(obsession)
                    }}
                  >
                    <span className="notif-item__icon notif-item__icon--obsession" aria-hidden="true">
                      <IconFlame size={18} />
                    </span>
                    <span className="notif-item__body">
                      <span className="notif-item__title">{obsession.title}</span>
                      <span className="notif-item__meta">
                        {obsession.artist} · {formatDayRange(obsession.start, obsession.end)} ·{' '}
                        {TIER_LABEL[obsession.tier]}
                      </span>
                    </span>
                    <IconChevron size={16} />
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {available.length ? (
            <div className="notif__section">
              {obsessions.length ? (
                <span className="notif__section-label">Recaps</span>
              ) : null}
              <div className="notif__list">
                {available.map((recap) => (
                  <button
                    key={recap.id}
                    type="button"
                    className="notif-item"
                    onClick={() => {
                      setOpen(false)
                      onOpenRecap(recap)
                    }}
                    style={
                      {
                        '--recap-from': recap.palette.from,
                        '--recap-to': recap.palette.to,
                      } as CSSProperties
                    }
                  >
                    <span className="notif-item__icon" aria-hidden="true">
                      <IconSparkle size={18} />
                    </span>
                    <span className="notif-item__body">
                      <span className="notif-item__title">{recap.title}</span>
                      <span className="notif-item__meta">
                        {recap.label} · {recap.range}
                      </span>
                    </span>
                    <IconChevron size={16} />
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {!hasContent ? (
            <p className="notif__empty">Todo al día. No hay novedades.</p>
          ) : null}

          {inProgress.length ? (
            <div className="notif__foot">
              <span className="notif__foot-label">En curso</span>
              {inProgress.map((recap) => (
                <span key={recap.id} className="notif__foot-item">
                  {recap.label}
                  <span className="notif__foot-status">{recapStatusLabel(recap.status)}</span>
                </span>
              ))}
            </div>
          ) : null}

          {upcoming ? (
            <div className="notif__next">
              Próximo recap: <strong>{upcoming.label}</strong> ·{' '}
              {new Intl.DateTimeFormat('es-ES', {
                day: 'numeric',
                month: 'long',
              }).format(new Date(upcoming.availableFrom))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
