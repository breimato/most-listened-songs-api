import type {
  Artist,
  Obsession,
  Recap,
  SleepData,
  Song,
  SongTimeline,
  Stats,
  SyncResult,
  TopSongsFilters,
} from '../types/api'
import {
  clearStoredAccessKey,
  getAccessKey,
  notifyUnauthorized,
} from './auth'
import { getApiBaseUrl } from './runtimeConfig'

function apiBase(): string {
  return `${getApiBaseUrl()}/api/v1`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  const key = getAccessKey()
  if (key) headers.set('Authorization', `Bearer ${key}`)

  const response = await fetch(`${apiBase()}${path}`, { ...init, headers })

  if (response.status === 401) {
    clearStoredAccessKey()
    notifyUnauthorized()
    throw new Error('Llave de acceso incorrecta o caducada.')
  }

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Error ${response.status}`)
  }

  return response.json() as Promise<T>
}

export async function checkAccess(key: string): Promise<boolean> {
  const response = await fetch(`${apiBase()}/stats`, {
    headers: { Authorization: `Bearer ${key}` },
  })
  if (response.status === 401) return false
  if (!response.ok) throw new Error(`Error ${response.status}`)
  return true
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

  getObsessions(range: RangeParams = {}) {
    return request<Obsession[]>(`/obsessions${buildQuery(rangeQuery(range))}`)
  },

  getSongTimeline(songId: number, range: RangeParams = {}) {
    return request<SongTimeline>(
      `/songs/${songId}/timeline${buildQuery(rangeQuery(range))}`,
    )
  },

  getRecap(range: RangeParams = {}) {
    return request<Recap>(`/recap${buildQuery(rangeQuery(range))}`)
  },

  getSleep(range: RangeParams = {}, limit = 50) {
    return request<SleepData>(
      `/sleep${buildQuery(rangeQuery(range, { limit }))}`,
    )
  },

  sync() {
    return request<SyncResult>('/sync', { method: 'POST' })
  },

  health() {
    return fetch(`${getApiBaseUrl()}/health`).then((r) => r.ok)
  },
}
