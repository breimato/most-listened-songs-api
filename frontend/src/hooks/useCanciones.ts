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

export function useSync() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.sync,
    onSuccess: () => {
      queryClient.invalidateQueries()
    },
  })
}
