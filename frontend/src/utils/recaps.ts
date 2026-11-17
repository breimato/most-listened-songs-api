import { formatRange } from './format'

export type Season = 'verano' | 'otono' | 'invierno' | 'primavera' | 'anio'
export type RecapStatus = 'available' | 'in-progress' | 'upcoming'

export interface RecapPalette {
  from: string
  to: string
  accent: string
}

export interface RecapPeriod {
  id: string
  season: Season
  label: string
  title: string
  shortLabel: string
  since: string
  until: string
  availableFrom: string
  status: RecapStatus
  range: string
  palette: RecapPalette
}

const PALETTES: Record<Season, RecapPalette> = {
  verano: { from: '#ff9f43', to: '#ff5e62', accent: '#ffb26b' },
  otono: { from: '#d97a37', to: '#8a3d1f', accent: '#f0a35e' },
  invierno: { from: '#5b8def', to: '#25346b', accent: '#8fb3ff' },
  primavera: { from: '#3ddc84', to: '#0f7a43', accent: '#7cf0a8' },
  anio: { from: '#1ed760', to: '#0a5c2b', accent: '#1ed760' },
}

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

function day(year: number, month: number, dayOfMonth: number, endOfDay = false): string {
  return `${year}-${pad(month)}-${pad(dayOfMonth)}T${endOfDay ? '23:59:59' : '00:00:00'}`
}

function lastDayOfFebruary(year: number): number {
  return new Date(year, 2, 0).getDate()
}

interface Candidate {
  season: Season
  label: string
  title: string
  shortLabel: string
  since: string
  until: string
  availableFrom: string
}

function candidatesForYear(year: number): Candidate[] {
  return [
    {
      season: 'primavera',
      label: `Primavera ${year}`,
      title: 'Tus temas de primavera',
      shortLabel: 'Primavera',
      since: day(year, 3, 1),
      until: day(year, 5, 31, true),
      availableFrom: day(year, 6, 1),
    },
    {
      season: 'verano',
      label: `Verano ${year}`,
      title: 'Tus temas del verano',
      shortLabel: 'Verano',
      since: day(year, 6, 1),
      until: day(year, 8, 31, true),
      availableFrom: day(year, 9, 1),
    },
    {
      season: 'otono',
      label: `Otoño ${year}`,
      title: 'Tus temas del otoño',
      shortLabel: 'Otoño',
      since: day(year, 9, 1),
      until: day(year, 11, 30, true),
      availableFrom: day(year, 12, 1),
    },
    {
      season: 'invierno',
      label: `Invierno ${year}/${String(year + 1).slice(-2)}`,
      title: 'Tus temas del invierno',
      shortLabel: 'Invierno',
      since: day(year, 12, 1),
      until: day(year + 1, 2, lastDayOfFebruary(year + 1), true),
      availableFrom: day(year + 1, 3, 1),
    },
    {
      season: 'anio',
      label: `Año ${year}`,
      title: 'Tus temas del año',
      shortLabel: 'Año',
      since: day(year, 1, 1),
      until: day(year, 12, 31, true),
      availableFrom: day(year, 12, 1),
    },
  ]
}

function statusOf(candidate: Candidate, now: Date): RecapStatus {
  const availableFrom = new Date(candidate.availableFrom)
  if (now >= availableFrom) return 'available'
  const since = new Date(candidate.since)
  const until = new Date(candidate.until)
  if (now >= since && now <= until) return 'in-progress'
  return 'upcoming'
}

export function buildRecaps(
  firstListen: string | null | undefined,
  lastListen: string | null | undefined,
  now = new Date(),
): RecapPeriod[] {
  if (!firstListen || !lastListen) return []

  const first = new Date(firstListen)
  const last = new Date(lastListen)
  const lastYear = Math.max(now.getFullYear(), last.getFullYear())
  const recaps: RecapPeriod[] = []

  for (let year = first.getFullYear(); year <= lastYear; year += 1) {
    for (const candidate of candidatesForYear(year)) {
      const since = new Date(candidate.since)
      const until = new Date(candidate.until)
      if (until < first || since > last) continue

      const overlapStart = since > first ? since : first
      const overlapEnd = until < last ? until : last
      const periodMs = until.getTime() - since.getTime()
      const coverage =
        periodMs > 0 ? (overlapEnd.getTime() - overlapStart.getTime()) / periodMs : 0
      const status = statusOf(candidate, now)

      // Una temporada con muy pocos días de histórico no merece un recap:
      // evita el "primavera" de dos semanas cuando empiezas a escrobbear.
      if (status === 'available' && coverage < 0.5) continue

      recaps.push({
        ...candidate,
        id: `${candidate.season}-${year}`,
        status,
        range: formatRange(candidate.since, candidate.until),
        palette: PALETTES[candidate.season],
      })
    }
  }

  const order: Record<RecapStatus, number> = {
    available: 0,
    'in-progress': 1,
    upcoming: 2,
  }

  return recaps.sort((a, b) => {
    if (order[a.status] !== order[b.status]) return order[a.status] - order[b.status]
    if (a.status === 'available') {
      return new Date(b.availableFrom).getTime() - new Date(a.availableFrom).getTime()
    }
    if (a.status === 'in-progress') {
      return new Date(b.since).getTime() - new Date(a.since).getTime()
    }
    return new Date(a.availableFrom).getTime() - new Date(b.availableFrom).getTime()
  })
}

export function nextRecap(recaps: RecapPeriod[]): RecapPeriod | null {
  return recaps.find((recap) => recap.status === 'upcoming') ?? null
}

export function recapStatusLabel(status: RecapStatus): string {
  if (status === 'available') return 'Nuevo'
  if (status === 'in-progress') return 'En curso'
  return 'Próximamente'
}
