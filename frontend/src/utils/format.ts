export function formatNumber(value: number): string {
  return new Intl.NumberFormat('es-ES').format(value)
}

export function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('es-ES', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(iso))
}

export function formatShortDate(iso: string | null): string {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('es-ES', {
    day: 'numeric',
    month: 'short',
  }).format(new Date(iso))
}

export function formatMonth(key: string): string {
  const [year, month] = key.split('-')
  const date = new Date(Number(year), Number(month) - 1, 1)
  return new Intl.DateTimeFormat('es-ES', {
    month: 'short',
  })
    .format(date)
    .replace('.', '')
}

export function formatMonthLong(key: string): string {
  const [year, month] = key.split('-')
  const date = new Date(Number(year), Number(month) - 1, 1)
  return new Intl.DateTimeFormat('es-ES', {
    month: 'long',
    year: 'numeric',
  }).format(date)
}

export function formatRange(since: string, until: string): string {
  const a = new Date(since)
  const b = new Date(until)
  const fmt = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short' })
  const yearFmt = new Intl.DateTimeFormat('es-ES', { year: 'numeric' })
  return `${fmt.format(a)} – ${fmt.format(b)} ${yearFmt.format(b)}`
}

export function formatDayRange(start: string, end: string): string {
  const a = new Date(`${start}T12:00:00`)
  const b = new Date(`${end}T12:00:00`)
  const fmt = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short' })
  const yearFmt = new Intl.DateTimeFormat('es-ES', { year: 'numeric' })
  if (a.getFullYear() === b.getFullYear()) {
    return `${fmt.format(a)} – ${fmt.format(b)} ${yearFmt.format(b)}`
  }
  return `${fmt.format(a)} ${yearFmt.format(a)} – ${fmt.format(b)} ${yearFmt.format(b)}`
}

export function formatDayLong(value: string): string {
  return new Intl.DateTimeFormat('es-ES', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
  }).format(new Date(`${value}T12:00:00`))
}

export function relativeTime(iso: string | null): string {
  if (!iso) return 'Sin datos'
  const then = new Date(iso).getTime()
  const minutes = Math.round((Date.now() - then) / 60_000)
  if (minutes < 1) return 'ahora mismo'
  if (minutes < 60) return `hace ${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `hace ${hours} h`
  const days = Math.round(hours / 24)
  if (days < 30) return `hace ${days} d`
  return formatDate(iso)
}

export function dayLabel(day: string): string {
  const labels: Record<string, string> = {
    Monday: 'Lunes',
    Tuesday: 'Martes',
    Wednesday: 'Miércoles',
    Thursday: 'Jueves',
    Friday: 'Viernes',
    Saturday: 'Sábado',
    Sunday: 'Domingo',
  }
  return labels[day] ?? day
}

export function hourLabel(hour: number): string {
  return `${String(hour).padStart(2, '0')}:00`
}

export function initials(value: string): string {
  const clean = value.trim()
  if (!clean) return '?'
  const words = clean.split(/\s+/)
  if (words.length === 1) return clean.slice(0, 2).toUpperCase()
  return `${words[0][0]}${words[1][0]}`.toUpperCase()
}
