export interface Song {
  id: number
  title: string
  artist: string
  album: string
  plays: number
}

export interface NowPlayingTrack {
  title: string
  artist: string
  album: string
  scrobbled_at: string | null
}

export interface NowPlaying {
  playing: boolean
  track: NowPlayingTrack | null
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
  total_minutes: number
  duration_coverage: number
}

export interface RecapSong {
  song_id: number
  title: string
  artist: string
  album: string
  plays: number
  minutes: number
  share: number
  days: number
  longest_streak: number
}

export interface RecapArtist {
  artist: string
  plays: number
  minutes: number
  share: number
  songs: number
  top_song: string | null
  top_song_id: number | null
}

export interface RecapAlbum {
  album: string
  artist: string
  plays: number
  minutes: number
  top_song: string
  top_song_id: number
}

export interface RecapGenre {
  name: string
  weight: number
  share: number
}

export interface RecapMonthlyArtist {
  month: string
  artist: string
  plays: number
}

export interface RecapProfile {
  key: string
  label: string
  description: string
}

export interface SleepSong {
  song_id: number
  title: string
  artist: string
  album: string
  plays: number
  total_plays: number
  night_share: number
  minutes: number
  total_minutes: number
  estimated: boolean
  score: number
}

export interface SleepData {
  window_start: number
  window_end: number
  total_plays: number
  night_plays: number
  night_share: number
  night_minutes: number
  duration_coverage: number
  estimated: boolean
  nights: number
  top_hour: number | null
  top_artist: string | null
  songs: SleepSong[]
}

export interface Recap {
  since: string
  until: string
  period_days: number
  total_plays: number
  total_minutes: number
  total_hours: number
  estimated_minutes: number
  estimated_hours: number
  duration_coverage: number
  unique_songs: number
  unique_artists: number
  unique_albums: number
  days_listened: number
  longest_streak: number
  top_day: string | null
  top_day_plays: number
  top_hour: number | null
  top_hour_plays: number
  first_play: string | null
  first_song: string | null
  first_song_id: number | null
  last_play: string | null
  last_song: string | null
  last_song_id: number | null
  top_song: RecapSong | null
  top_song_days: number
  top_song_longest_streak: number
  top_songs: RecapSong[]
  top_artists: RecapArtist[]
  top_albums: RecapAlbum[]
  top_genres: RecapGenre[]
  monthly_top_artists: RecapMonthlyArtist[]
  top_obsession: Obsession | null
  profile: RecapProfile
  sleep: SleepData
}
