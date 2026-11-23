import type { NowPlaying } from '../types/api'

export type NowPlayingState = 'loading' | 'live' | 'paused' | 'stale' | 'idle'

export function resolveNowPlayingState(
  data: NowPlaying | undefined,
  isLoading: boolean,
  isError: boolean,
  dataUpdatedAt: number,
  now: number,
): NowPlayingState {
  if (isLoading && !data) return 'loading'
  if (isError && data && dataUpdatedAt > 0 && now - dataUpdatedAt > 60_000) {
    return 'stale'
  }
  if (data?.playing && data.track) return 'live'
  if (data?.track) return 'paused'
  return 'idle'
}
