export interface Song {
  id: number
  title: string
  artist: string
  album: string
  plays: number
}

export interface Artist {
  artist: string
  plays: number
  songs: number
}

export interface Stats {
  total_plays: number
  total_songs: number
  total_artists: number
  plays_by_month: Record<string, number>
  plays_by_hour: Record<string, number>
  top_day: string
  first_listen: string | null
  last_listen: string | null
}

export interface SyncResult {
  imported: number
  skipped: number
  message: string
}

export interface TopSongsFilters {
  limit: number
  year?: number
  artist?: string
  since?: string
  until?: string
}

export interface ObsessionDay {
  date: string
  plays: number
}

export interface Obsession {
  id: string
  song_id: number
  title: string
  artist: string
  album: string
  start: string
  end: string
  span_days: number
  strong_days: number
  active_days: number
  plays: number
  peak_day: string
  peak_plays: number
  tier: 'obsesion' | 'racha'
  score: number
  days: ObsessionDay[]
}

export interface SongTimeline {
  song: Song
  days: ObsessionDay[]
  episodes: Obsession[]
  first_listen: string | null
  last_listen: string | null
}
