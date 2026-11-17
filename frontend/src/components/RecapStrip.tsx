import type { CSSProperties } from 'react'

import type { RecapPeriod } from '../utils/recaps'
import { recapStatusLabel } from '../utils/recaps'

interface RecapStripProps {
  recaps: RecapPeriod[]
  onOpenRecap: (recap: RecapPeriod) => void
}

export function RecapStrip({ recaps, onOpenRecap }: RecapStripProps) {
  const visible = recaps.filter((recap) => recap.status !== 'upcoming').slice(0, 3)
  if (!visible.length) return null

  return (
    <div className="recap-strip" aria-label="Recaps de temporada">
      {visible.map((recap) => (
        <button
          key={recap.id}
          type="button"
          className="recap-chip"
          onClick={() => onOpenRecap(recap)}
          style={
            {
              '--recap-from': recap.palette.from,
              '--recap-to': recap.palette.to,
            } as CSSProperties
          }
        >
          <span className="recap-chip__dot" aria-hidden="true" />
          <span className="recap-chip__text">
            <span className="recap-chip__label">{recap.label}</span>
            <span className="recap-chip__status">{recapStatusLabel(recap.status)}</span>
          </span>
        </button>
      ))}
    </div>
  )
}
