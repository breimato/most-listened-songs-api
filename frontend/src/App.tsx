import { useCallback, useEffect, useMemo, useState } from 'react'

import { ActivityView } from './components/ActivityView'
import { ArtistList } from './components/ArtistList'
import { Filters } from './components/Filters'
import { Hero } from './components/Hero'
import { MobileNav } from './components/MobileNav'
import { ObsessionsView } from './components/ObsessionsView'
import { RecapModal } from './components/RecapModal'
import { RecapStrip } from './components/RecapStrip'
import { Sidebar, type Tab } from './components/Sidebar'
import { SongList } from './components/SongList'
import { SongTimelineModal } from './components/SongTimelineModal'
import { StatsStrip } from './components/StatsStrip'
import { Toast } from './components/Toast'
import { TopBar } from './components/TopBar'
import {
  useObsessions,
  useStats,
  useTopArtists,
  useTopSongs,
} from './hooks/useCanciones'
import type { Obsession, Song } from './types/api'
import { formatNumber } from './utils/format'
import { buildRecaps, type RecapPeriod } from './utils/recaps'

const READ_KEY = 'scrobbles:recaps-read:v1'
const OBS_SEEN_KEY = 'scrobbles:obsessions-seen:v1'

interface AppProps {
  onLock: () => void
}

interface TimelineTarget {
  songId: number
  highlightId?: string | null
}

function loadReadRecaps(): string[] {
  try {
    const raw = localStorage.getItem(READ_KEY)
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

function loadSeenObsessions(): string[] | null {
  try {
    const raw = localStorage.getItem(OBS_SEEN_KEY)
    return raw ? (JSON.parse(raw) as string[]) : null
  } catch {
    return null
  }
}

function isRecentEpisode(end: string): boolean {
  const endTime = new Date(`${end}T23:59:59`).getTime()
  return Date.now() - endTime <= 30 * 24 * 60 * 60 * 1000
}

export default function App({ onLock }: AppProps) {
  const [tab, setTab] = useState<Tab>('songs')
  const [limit, setLimit] = useState(25)
  const [year, setYear] = useState('')
  const [artist, setArtist] = useState('')
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [recapOpen, setRecapOpen] = useState<RecapPeriod | null>(null)
  const [timeline, setTimeline] = useState<TimelineTarget | null>(null)
  const [readRecaps, setReadRecaps] = useState<string[]>(loadReadRecaps)
  const [seenObsessions, setSeenObsessions] = useState<string[] | null>(
    loadSeenObsessions,
  )

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
  const obsessionsQuery = useObsessions({})
  const pageObsessionsQuery = useObsessions({ year: yearNumber })

  const recaps = useMemo(
    () =>
      buildRecaps(
        allStatsQuery.data?.first_listen,
        allStatsQuery.data?.last_listen,
      ),
    [allStatsQuery.data],
  )

  useEffect(() => {
    if (seenObsessions !== null || !obsessionsQuery.data) return
    const all = obsessionsQuery.data.map((obsession) => obsession.id)
    try {
      localStorage.setItem(OBS_SEEN_KEY, JSON.stringify(all))
    } catch {
      // Sin persistencia: se mantiene en memoria.
    }
    setSeenObsessions(all)
  }, [seenObsessions, obsessionsQuery.data])

  const availableRecaps = recaps.filter((recap) => recap.status === 'available')
  const unreadRecaps = availableRecaps.filter(
    (recap) => !readRecaps.includes(recap.id),
  ).length
  const heroRecap =
    availableRecaps.find((recap) => recap.season === 'anio') ??
    availableRecaps[0] ??
    null

  const unreadObsessions = useMemo(() => {
    if (seenObsessions === null) return []
    return (obsessionsQuery.data ?? []).filter(
      (obsession) =>
        !seenObsessions.includes(obsession.id) &&
        isRecentEpisode(obsession.end),
    )
  }, [obsessionsQuery.data, seenObsessions])

  const showToast = useCallback(
    (message: string, type: 'success' | 'error') => setToast({ message, type }),
    [],
  )
  const closeToast = useCallback(() => setToast(null), [])

  const markObsessionSeen = useCallback((id: string) => {
    setSeenObsessions((previous) => {
      const base = previous ?? []
      if (base.includes(id)) return base
      const next = [...base, id]
      try {
        localStorage.setItem(OBS_SEEN_KEY, JSON.stringify(next))
      } catch {
        // Sin persistencia: se mantiene en memoria.
      }
      return next
    })
  }, [])

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

  const openObsession = useCallback(
    (obsession: Obsession) => {
      markObsessionSeen(obsession.id)
      setTimeline({ songId: obsession.song_id, highlightId: obsession.id })
    },
    [markObsessionSeen],
  )

  const openSongTimeline = useCallback((song: Song) => {
    setTimeline({ songId: song.id })
  }, [])

  const closeTimeline = useCallback(() => setTimeline(null), [])

  const songs = songsQuery.data ?? []
  const pool = songsPoolQuery.data ?? []
  const heroSong = songs[0] ?? pool[0]

  const sectionTitle =
    tab === 'songs'
      ? 'Top canciones'
      : tab === 'obsessions'
        ? 'Episodios'
        : tab === 'artists'
          ? 'Top artistas'
          : 'Reproducciones'

  const sectionCopy =
    tab === 'songs'
      ? `${formatNumber(songs.length)} canciones en este periodo`
      : tab === 'obsessions'
        ? `${formatNumber(pageObsessionsQuery.data?.length ?? 0)} episodios detectados`
        : tab === 'artists'
          ? `${formatNumber(artistsQuery.data?.length ?? 0)} artistas en el top`
          : 'Agrupadas por mes y por hora'

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
          unread={unreadRecaps}
          obsessions={unreadObsessions}
          unreadObsessions={unreadObsessions.length}
          onOpenRecap={openRecap}
          onOpenObsession={openObsession}
          onSyncMessage={showToast}
          onLock={onLock}
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
              <h1>
                {tab === 'obsessions'
                  ? 'Tus obsesiones'
                  : tab === 'artists'
                    ? 'Tus artistas más escuchados'
                    : 'Tu actividad'}
              </h1>
              <p>
                {tab === 'obsessions'
                  ? 'Las canciones que se quedaron una temporada: una o dos semanas, casi todos los días y varias veces.'
                  : tab === 'artists'
                    ? 'Quién suena más en tu historial, con sus reproducciones y canciones.'
                    : 'Cuándo escuchas: tus meses y tus horas con más música.'}
              </p>
            </header>
          )}

          {tab !== 'obsessions' ? (
            <StatsStrip stats={statsQuery.data} isLoading={statsQuery.isLoading} />
          ) : null}

          <section className="section" aria-labelledby="section-title">
            <header className="section__head">
              <div className="section__copy">
                <h2 id="section-title">{sectionTitle}</h2>
                <p>{sectionCopy}</p>
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
                onOpenTimeline={openSongTimeline}
              />
            ) : null}

            {tab === 'obsessions' ? (
              <ObsessionsView
                obsessions={pageObsessionsQuery.data}
                isLoading={pageObsessionsQuery.isLoading}
                onOpenTimeline={openObsession}
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

      {timeline ? (
        <SongTimelineModal
          songId={timeline.songId}
          highlightId={timeline.highlightId}
          onClose={closeTimeline}
        />
      ) : null}

      {toast ? (
        <Toast message={toast.message} type={toast.type} onClose={closeToast} />
      ) : null}
    </div>
  )
}
