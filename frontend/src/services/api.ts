import type { Artist, Song, Stats, SyncResult, TopSongsFilters } from '../types/api'
import { getApiBaseUrl } from './runtimeConfig'

function apiBase(): string {
  return `${getApiBaseUrl()}/api/v1`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, init)

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

export interface RangeParams {
  year?: number
  since?: string
  until?: string
}

function rangeQuery(range: RangeParams, extra: Record<string, string | number | undefined> = {}) {
  if (range.since || range.until) {
    return { ...extra, since: range.since, until: range.until }
  }
  if (range.year) {
    return {
      ...extra,
      since: `${range.year}-01-01T00:00:00`,
      until: `${range.year}-12-31T23:59:59`,
    }
  }
  return extra
}

export const api = {
  getTopSongs(filters: TopSongsFilters) {
    return request<Song[]>(
      `/songs/top${buildQuery(
        rangeQuery(filters, {
          limit: filters.limit,
          artist: filters.artist,
        }),
      )}`,
    )
  },

  getTopArtists(limit: number, range: RangeParams = {}) {
    return request<Artist[]>(
      `/artists/top${buildQuery(rangeQuery(range, { limit }))}`,
    )
  },

  getStats(range: RangeParams = {}) {
    return request<Stats>(`/stats${buildQuery(rangeQuery(range))}`)
  },

  sync() {
    return request<SyncResult>('/sync', { method: 'POST' })
  },

  health() {
    return fetch(`${getApiBaseUrl()}/health`).then((r) => r.ok)
  },
}
