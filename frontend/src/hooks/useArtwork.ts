import { useEffect, useState } from 'react'

const STORAGE_KEY = 'scrobbles:covers:v1'
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

function normalize(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9 ]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function tokens(value: string): Set<string> {
  return new Set(normalize(value).split(' ').filter(Boolean))
}

function overlap(a: string, b: string): number {
  const left = tokens(a)
  const right = tokens(b)
  if (!left.size || !right.size) return 0
  let shared = 0
  for (const token of left) {
    if (right.has(token)) shared += 1
  }
  return shared / Math.max(left.size, right.size)
}

function matches(candidateArtist: string, candidateTitle: string, artist: string, title: string): boolean {
  const artistMatch =
    overlap(candidateArtist, artist) >= 0.6 ||
    normalize(candidateArtist).includes(normalize(artist)) ||
    normalize(artist).includes(normalize(candidateArtist))
  const titleMatch =
    overlap(candidateTitle, title) >= 0.6 ||
    normalize(candidateTitle) === normalize(title)
  return artistMatch && titleMatch
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

async function fromItunes(artist: string, title: string): Promise<string | null> {
  const query = encodeURIComponent(`${artist} ${title}`)
  const response = await fetch(
    `https://itunes.apple.com/search?term=${query}&entity=song&limit=3&country=ES`,
  )
  if (!response.ok) return null
  const data = (await response.json()) as {
    results?: Array<{ trackName: string; artistName: string; artworkUrl100?: string }>
  }
  const hit = data.results?.find((item) =>
    matches(item.artistName, item.trackName, artist, title),
  )
  return hit?.artworkUrl100?.replace('100x100bb', '600x600bb') ?? null
}

const inflight = new Map<string, Promise<string | null>>()

async function resolveCover(artist: string, title: string): Promise<string | null> {
  const key = keyFor(artist, title)
  const cached = loadStore()[key]
  if (cached && Date.now() - cached.ts < 1000 * 60 * 60 * 24 * 60) {
    return cached.url
  }
  const running = inflight.get(key)
  if (running) return running

  const task = withSlot(async () => {
    let url: string | null = null
    try {
      url = await fromItunes(artist, title)
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
