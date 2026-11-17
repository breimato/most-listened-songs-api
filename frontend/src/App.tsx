import { useCallback, useMemo, useState } from 'react'

import { ActivityView } from './components/ActivityView'
import { ArtistList } from './components/ArtistList'
import { Filters } from './components/Filters'
import { Hero } from './components/Hero'
import { MobileNav } from './components/MobileNav'
import { RecapModal } from './components/RecapModal'
import { RecapStrip } from './components/RecapStrip'
import { Sidebar, type Tab } from './components/Sidebar'
import { SongList } from './components/SongList'
import { StatsStrip } from './components/StatsStrip'
import { Toast } from './components/Toast'
import { TopBar } from './components/TopBar'
import { useStats, useTopArtists, useTopSongs } from './hooks/useCanciones'
import { formatNumber } from './utils/format'
import { buildRecaps, type RecapPeriod } from './utils/recaps'

const READ_KEY = 'scrobbles:recaps-read:v1'

function loadReadRecaps(): string[] {
  try {
    const raw = localStorage.getItem(READ_KEY)
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

export default function App() {
  const [tab, setTab] = useState<Tab>('songs')
  const [limit, setLimit] = useState(25)
  const [year, setYear] = useState('')
  const [artist, setArtist] = useState('')
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [recapOpen, setRecapOpen] = useState<RecapPeriod | null>(null)
  const [readRecaps, setReadRecaps] = useState<string[]>(loadReadRecaps)

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
  const songsPoolQuery = useTopSongs({ limit: 100, year: yearNumber })
  const artistsQuery = useTopArtists(limit, { year: yearNumber })
  const statsQuery = useStats({ year: yearNumber })
  const allStatsQuery = useStats({})

  const recaps = useMemo(
    () =>
      buildRecaps(
        allStatsQuery.data?.first_listen,
        allStatsQuery.data?.last_listen,
      ),
    [allStatsQuery.data],
  )

  const availableRecaps = recaps.filter((recap) => recap.status === 'available')
  const unread = availableRecaps.filter((recap) => !readRecaps.includes(recap.id)).length
  const heroRecap =
    availableRecaps.find((recap) => recap.season === 'anio') ??
    availableRecaps[0] ??
    null

  const showToast = useCallback(
    (message: string, type: 'success' | 'error') => setToast({ message, type }),
    [],
  )
  const closeToast = useCallback(() => setToast(null), [])

  const openRecap = useCallback((recap: RecapPeriod) => {
    setRecapOpen(recap)
    setReadRecaps((previous) => {
      if (previous.includes(recap.id)) return previous
      const next = [...previous, recap.id]
      try {
        localStorage.setItem(READ_KEY, JSON.stringify(next))
      } catch {
        // Sin persistencia: se mantiene en memoria.
      }
      return next
    })
  }, [])

  const songs = songsQuery.data ?? []
  const pool = songsPoolQuery.data ?? []
  const heroSong = songs[0] ?? pool[0]

  return (
    <div className="shell">
      <Sidebar
        tab={tab}
        onTab={setTab}
        recaps={recaps}
        onOpenRecap={openRecap}
        totalPlays={allStatsQuery.data?.total_plays}
        lastListen={allStatsQuery.data?.last_listen}
      />

      <div className="workspace">
        <TopBar
          tab={tab}
          recaps={recaps}
          unread={unread}
          onOpenRecap={openRecap}
          onSyncMessage={showToast}
        />

        <main className="main">
          <RecapStrip recaps={recaps} onOpenRecap={openRecap} />

          {tab === 'songs' ? (
            <Hero
              song={heroSong}
              stats={statsQuery.data}
              recap={heroRecap}
              isLoading={songsQuery.isLoading}
              onOpenRecap={openRecap}
              onGoArtists={() => setTab('artists')}
            />
          ) : (
            <header className="page-head">
              <h1>{tab === 'artists' ? 'Tus artistas más escuchados' : 'Tu actividad'}</h1>
              <p>
                {tab === 'artists'
                  ? 'Quién suena más en tu historial, con sus reproducciones y canciones.'
                  : 'Cuándo escuchas: tus meses y tus horas con más música.'}
              </p>
            </header>
          )}

          <StatsStrip stats={statsQuery.data} isLoading={statsQuery.isLoading} />

          <section className="section" aria-labelledby="section-title">
            <header className="section__head">
              <div className="section__copy">
                <h2 id="section-title">
                  {tab === 'songs' ? 'Top canciones' : tab === 'artists' ? 'Top artistas' : 'Reproducciones'}
                </h2>
                <p>
                  {tab === 'songs'
                    ? `${formatNumber(songs.length)} canciones en este periodo`
                    : tab === 'artists'
                      ? `${formatNumber(artistsQuery.data?.length ?? 0)} artistas en el top`
                      : 'Agrupadas por mes y por hora'}
                </p>
              </div>

              <Filters
                variant={tab}
                limit={limit}
                year={year}
                artist={artist}
                onLimitChange={setLimit}
                onYearChange={setYear}
                onArtistChange={setArtist}
              />
            </header>

            {tab === 'songs' ? (
              <SongList
                songs={songsQuery.data}
                isLoading={songsQuery.isLoading}
                isError={songsQuery.isError}
                emptyHint={
                  artist
                    ? `No hay canciones de “${artist}” en este periodo.`
                    : undefined
                }
              />
            ) : null}

            {tab === 'artists' ? (
              <ArtistList
                artists={artistsQuery.data}
                songsPool={pool}
                isLoading={artistsQuery.isLoading}
              />
            ) : null}

            {tab === 'activity' ? (
              <ActivityView stats={statsQuery.data} isLoading={statsQuery.isLoading} />
            ) : null}
          </section>
        </main>

        <MobileNav tab={tab} onTab={setTab} />
      </div>

      {recapOpen ? <RecapModal recap={recapOpen} onClose={() => setRecapOpen(null)} /> : null}

      {toast ? (
        <Toast message={toast.message} type={toast.type} onClose={closeToast} />
      ) : null}
    </div>
  )
}
