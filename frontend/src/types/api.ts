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
}
