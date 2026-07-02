import type { Artist, Song, Stats, SyncResult, TopSongsFilters } from '../types/api'

const API_BASE = '/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Error ${response.status}`)
  }

  return response.json() as Promise<T>
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      search.set(key, String(value))
    }
  }

  const query = search.toString()
  return query ? `?${query}` : ''
}

function yearRange(year?: number) {
  if (!year) return {}
  return {
    since: `${year}-01-01T00:00:00`,
    until: `${year}-12-31T23:59:59`,
  }
}

export const api = {
  getTopSongs(filters: TopSongsFilters) {
    return request<Song[]>(
      `/songs/top${buildQuery({
        limit: filters.limit,
        year: filters.year,
        artist: filters.artist,
      })}`,
    )
  },

  getTopArtists(limit = 25, year?: number) {
    return request<Artist[]>(
      `/artists/top${buildQuery({ limit, ...yearRange(year) })}`,
    )
  },

  getStats(year?: number) {
    return request<Stats>(`/stats${buildQuery(yearRange(year))}`)
  },

  sync() {
    return request<SyncResult>('/sync', { method: 'POST' })
  },

  health() {
    return fetch('/health').then((r) => r.ok)
  },
}
