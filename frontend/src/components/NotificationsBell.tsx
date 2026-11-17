import type { CSSProperties } from 'react'

import { useEffect, useRef, useState } from 'react'

import type { RecapPeriod } from '../utils/recaps'
import { nextRecap, recapStatusLabel } from '../utils/recaps'
import { IconBell, IconChevron, IconSparkle } from './Icons'

interface NotificationsBellProps {
  recaps: RecapPeriod[]
  unread: number
  onOpenRecap: (recap: RecapPeriod) => void
}

export function NotificationsBell({ recaps, unread, onOpenRecap }: NotificationsBellProps) {
  const [open, setOpen] = useState(false)
  const wrapper = useRef<HTMLDivElement>(null)

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

  return (
    <div className="notif" ref={wrapper}>
      <button
        type="button"
        className={`icon-btn${open ? ' is-open' : ''}`}
        onClick={() => setOpen((value) => !value)}
        aria-label={unread ? `Novedades (${unread})` : 'Novedades'}
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        <IconBell />
        {unread > 0 ? <span className="icon-btn__dot" aria-hidden="true" /> : null}
      </button>

      {open ? (
        <div className="notif__panel" role="dialog" aria-label="Novedades de temporada">
          <div className="notif__head">
            <span>Novedades</span>
            {unread > 0 ? <span className="notif__count">{unread}</span> : null}
          </div>

          {available.length ? (
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
          ) : (
            <p className="notif__empty">Todo al día. No hay recaps nuevos.</p>
          )}

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
            {new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'long' }).format(
              new Date(upcoming.availableFrom),
            )}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
