import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, type RangeParams } from '../services/api'
import type { TopSongsFilters } from '../types/api'

export function useTopSongs(filters: TopSongsFilters) {
  return useQuery({
    queryKey: ['top-songs', filters],
    queryFn: () => api.getTopSongs(filters),
  })
}

export function useTopArtists(limit: number, range: RangeParams = {}) {
  return useQuery({
    queryKey: ['top-artists', limit, range],
    queryFn: () => api.getTopArtists(limit, range),
  })
}

export function useStats(range: RangeParams = {}) {
  return useQuery({
    queryKey: ['stats', range],
    queryFn: () => api.getStats(range),
  })
}

export function useObsessions(range: RangeParams = {}) {
  return useQuery({
    queryKey: ['obsessions', range],
    queryFn: () => api.getObsessions(range),
  })
}

export function useSongTimeline(songId: number | null) {
  return useQuery({
    queryKey: ['song-timeline', songId],
    queryFn: () => api.getSongTimeline(songId as number),
    enabled: songId !== null,
  })
}

export function useRecap(range: RangeParams) {
  return useQuery({
    queryKey: ['recap', range],
    queryFn: () => api.getRecap(range),
  })
}

export function useSleep(range: RangeParams, limit: number) {
  return useQuery({
    queryKey: ['sleep', range, limit],
    queryFn: () => api.getSleep(range, limit),
  })
}

export function useSync() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.sync,
    onSuccess: () => {
      queryClient.invalidateQueries()
    },
  })
}
