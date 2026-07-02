import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../services/api'
import type { TopSongsFilters } from '../types/api'

export function useTopSongs(filters: TopSongsFilters) {
  return useQuery({
    queryKey: ['top-songs', filters],
    queryFn: () => api.getTopSongs(filters),
  })
}

export function useTopArtists(limit: number, year?: number) {
  return useQuery({
    queryKey: ['top-artists', limit, year],
    queryFn: () => api.getTopArtists(limit, year),
  })
}

export function useStats(year?: number) {
  return useQuery({
    queryKey: ['stats', year],
    queryFn: () => api.getStats(year),
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
