import { useMemo, useState } from 'react'

import { ActivityCharts } from './components/ActivityCharts'
import { Filters } from './components/Filters'
import { StatsCards } from './components/StatsCards'
import { SyncButton } from './components/SyncButton'
import { TopArtistsList } from './components/TopArtistsList'
import { TopSongsList } from './components/TopSongsList'
import { useStats, useTopArtists, useTopSongs } from './hooks/useCanciones'

type Tab = 'songs' | 'artists' | 'activity'

export default function App() {
  const [tab, setTab] = useState<Tab>('songs')
  const [limit, setLimit] = useState(25)
  const [year, setYear] = useState('')
  const [artist, setArtist] = useState('')
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  const yearNumber = year ? Number(year) : undefined

  const songFilters = useMemo(
    () => ({
      limit,
      year: yearNumber,
      artist: artist.trim() || undefined,
    }),
    [limit, yearNumber, artist],
  )

  const songsQuery = useTopSongs(songFilters)
  const artistsQuery = useTopArtists(15, yearNumber)
  const statsQuery = useStats(yearNumber)

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type })
    window.setTimeout(() => setToast(null), 5000)
  }

  return (
    <div className="app">
      <div className="app__glow" aria-hidden="true" />

      <header className="header">
        <div>
          <p className="header__eyebrow">Last.fm · Spotify · YouTube</p>
          <h1>Canciones más escuchadas</h1>
          <p className="header__subtitle">
            Tu historial de scrobbles, ordenado por reproducciones.
          </p>
        </div>
        <SyncButton onMessage={showToast} />
      </header>

      <StatsCards stats={statsQuery.data} isLoading={statsQuery.isLoading} />

      <Filters
        limit={limit}
        year={year}
        artist={artist}
        onLimitChange={setLimit}
        onYearChange={setYear}
        onArtistChange={setArtist}
      />

      <nav className="tabs" aria-label="Secciones">
        <button
          type="button"
          className={tab === 'songs' ? 'tabs__btn tabs__btn--active' : 'tabs__btn'}
          onClick={() => setTab('songs')}
        >
          Top canciones
        </button>
        <button
          type="button"
          className={tab === 'artists' ? 'tabs__btn tabs__btn--active' : 'tabs__btn'}
          onClick={() => setTab('artists')}
        >
          Top artistas
        </button>
        <button
          type="button"
          className={tab === 'activity' ? 'tabs__btn tabs__btn--active' : 'tabs__btn'}
          onClick={() => setTab('activity')}
        >
          Actividad
        </button>
      </nav>

      <main className="panel">
        {tab === 'songs' && (
          <TopSongsList
            songs={songsQuery.data}
            isLoading={songsQuery.isLoading}
            isError={songsQuery.isError}
          />
        )}
        {tab === 'artists' && (
          <TopArtistsList artists={artistsQuery.data} isLoading={artistsQuery.isLoading} />
        )}
        {tab === 'activity' && (
          <ActivityCharts stats={statsQuery.data} isLoading={statsQuery.isLoading} />
        )}
      </main>

      {toast && (
        <div className={`toast toast--${toast.type}`} role="status">
          {toast.message}
        </div>
      )}
    </div>
  )
}
