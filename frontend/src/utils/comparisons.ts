const SMI_HOURLY_EUR = 9.36
const MUSK_2025_GAIN_USD = 305_100_000_000
const MINUTES_PER_YEAR = 365 * 24 * 60
const EUR_PER_USD = 0.92
const COURSE_HOURS = 40
const BOOK_WORDS = 90_000
const WORDS_PER_MINUTE = 250
const MOVIE_HOURS = 2
const WALK_KMH = 5
const SLEEP_HOURS = 8

const nf = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 0 })

export interface Comparison {
  key: string
  label: string
  value: string
  note: string
}

function plural(count: number, one: string, many: string): string {
  return `${nf.format(count)} ${count === 1 ? one : many}`
}

export function buildComparisons(minutes: number): Comparison[] {
  if (minutes < 1) return []

  const hours = minutes / 60
  const muskMillions =
    (minutes * (MUSK_2025_GAIN_USD / MINUTES_PER_YEAR) * EUR_PER_USD) / 1_000_000
  const smi = hours * SMI_HOURLY_EUR
  const courses = Math.floor(hours / COURSE_HOURS)
  const books = Math.floor((hours * 60 * WORDS_PER_MINUTE) / BOOK_WORDS)
  const movies = Math.floor(hours / MOVIE_HOURS)
  const km = Math.round(hours * WALK_KMH)
  const nights = Math.floor(hours / SLEEP_HOURS)

  const items: Comparison[] = [
    {
      key: 'musk',
      label: 'Elon Musk',
      value: `≈ ${nf.format(muskMillions)} M€`,
      note: 'fortuna que habría crecido, según Forbes 2025',
    },
    {
      key: 'smi',
      label: 'Salario mínimo',
      value: `≈ ${nf.format(smi)} €`,
      note: 'horas de trabajo al SMI 2026 (9,36 €/h)',
    },
  ]

  if (courses > 0) {
    items.push({
      key: 'botany',
      label: 'Curso de botánica',
      value: plural(courses, 'curso', 'cursos'),
      note: 'cursos de 40 h',
    })
  }
  if (books > 0) {
    items.push({
      key: 'books',
      label: 'Libros',
      value: plural(books, 'libro', 'libros'),
      note: 'libros de 90.000 palabras a 250 ppm',
    })
  }
  if (movies > 0) {
    items.push({
      key: 'movies',
      label: 'Películas',
      value: plural(movies, 'película', 'películas'),
      note: 'películas de 2 h',
    })
  }
  if (km > 0) {
    items.push({
      key: 'walk',
      label: 'Caminando',
      value: `${nf.format(km)} km`,
      note: 'a 5 km/h',
    })
  }
  if (nights > 0) {
    items.push({
      key: 'sleep',
      label: 'Noches de sueño',
      value: plural(nights, 'noche', 'noches'),
      note: 'de 8 h',
    })
  }

  return items
}

export const COMPARISON_SOURCES = [
  {
    label: 'Forbes 2025',
    url: 'https://www.forbes.com/sites/tylerroush/2025/12/31/elon-musks-net-worth-ends-2025-at-726-billion-more-valuable-than-belgium-oracle-more/',
  },
  {
    label: 'SMI 2026 (BOE)',
    url: 'https://www.boe.es/buscar/act.php?id=BOE-A-2026-3815',
  },
]
