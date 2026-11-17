import { useEffect, useState } from 'react'

import { getAccessKey } from '../services/auth'
import { getApiBaseUrl } from '../services/runtimeConfig'

const STORAGE_KEY = 'scrobbles:covers:v2'
const MAX_ENTRIES = 500
const MAX_CONCURRENT = 4

interface StoredCover {
  url: string | null
  ts: number
}

type CoverStore = Record<string, StoredCover>

let store: CoverStore | null = null
let saveTimer: number | undefined

function loadStore(): CoverStore {
  if (store) return store
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    store = raw ? (JSON.parse(raw) as CoverStore) : {}
  } catch {
    store = {}
  }
  return store
}

function persistSoon(): void {
  window.clearTimeout(saveTimer)
  saveTimer = window.setTimeout(() => {
    try {
      const entries = Object.entries(loadStore())
      if (entries.length > MAX_ENTRIES) {
        entries.sort((a, b) => b[1].ts - a[1].ts)
        store = Object.fromEntries(entries.slice(0, MAX_ENTRIES))
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
    } catch {
      // Storage lleno o bloqueado: la caché en memoria sigue funcionando.
    }
  }, 600)
}

function keyFor(artist: string, title: string): string {
  return `${artist.trim().toLowerCase()}|${title.trim().toLowerCase()}`
}

let active = 0
const waiting: Array<() => void> = []

async function withSlot<T>(task: () => Promise<T>): Promise<T> {
  if (active >= MAX_CONCURRENT) {
    await new Promise<void>((resolve) => waiting.push(resolve))
  }
  active += 1
  try {
    return await task()
  } finally {
    active -= 1
    waiting.shift()?.()
  }
}

async function fromApi(artist: string, title: string): Promise<string | null> {
  const params = new URLSearchParams({ artist, title })
  const headers = new Headers()
  const key = getAccessKey()
  if (key) headers.set('Authorization', `Bearer ${key}`)

  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/artwork?${params.toString()}`,
    { headers },
  )
  if (!response.ok) return null
  const data = (await response.json()) as { url?: string | null }
  return data.url ?? null
}

const inflight = new Map<string, Promise<string | null>>()

async function resolveCover(artist: string, title: string): Promise<string | null> {
  const key = keyFor(artist, title)
  const cached = loadStore()[key]
  if (cached) {
    const ttl = cached.url ? 1000 * 60 * 60 * 24 * 60 : 1000 * 60 * 60 * 24
    if (Date.now() - cached.ts < ttl) return cached.url
  }
  const running = inflight.get(key)
  if (running) return running

  const task = withSlot(async () => {
    let url: string | null = null
    try {
      url = await fromApi(artist, title)
    } catch {
      url = null
    }
    loadStore()[key] = { url, ts: Date.now() }
    persistSoon()
    return url
  }).finally(() => inflight.delete(key))

  inflight.set(key, task)
  return task
}

export function peekCover(artist: string, title: string): string | null {
  if (!artist || !title) return null
  return loadStore()[keyFor(artist, title)]?.url ?? null
}

export function useArtwork(artist: string, title: string): string | null {
  const [url, setUrl] = useState<string | null>(() => peekCover(artist, title))

  useEffect(() => {
    if (!artist || !title) {
      setUrl(null)
      return
    }

    const cached = peekCover(artist, title)
    if (cached) {
      setUrl(cached)
      return
    }

    let alive = true
    setUrl(null)
    resolveCover(artist, title).then((resolved) => {
      if (alive) setUrl(resolved)
    })

    return () => {
      alive = false
    }
  }, [artist, title])

  return url
}

export function coverSeed(artist: string, title: string): Record<string, string> {
  const source = `${artist}|${title}`
  let hash = 2166136261
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  const value = hash >>> 0
  const hue = value % 360
  const hueTwo = (hue + 32 + ((value >> 7) % 70)) % 360
  return {
    '--cover-a': `hsl(${hue} 46% 30%)`,
    '--cover-b': `hsl(${hueTwo} 52% 15%)`,
    '--cover-angle': `${(value % 160) + 100}deg`,
  }
}
