import { describe, expect, it } from 'vitest'

import { resolveNowPlayingState } from './nowPlaying'

const live = {
  playing: true,
  track: {
    title: 'Voto En Blanco',
    artist: 'El Jincho',
    album: 'Single',
    scrobbled_at: null,
  },
}

const paused = {
  playing: false,
  track: {
    title: 'Closer',
    artist: 'Joe Inoue',
    album: 'Closer',
    scrobbled_at: '2026-11-23T20:00:00Z',
  },
}

describe('resolveNowPlayingState', () => {
  it('paints loading before the first response', () => {
    expect(resolveNowPlayingState(undefined, true, false, 0, 1_000)).toBe(
      'loading',
    )
  })

  it('paints live while playing', () => {
    expect(resolveNowPlayingState(live, false, false, 1_000, 1_500)).toBe(
      'live',
    )
  })

  it('paints paused with a last scrobble', () => {
    expect(resolveNowPlayingState(paused, false, false, 1_000, 1_500)).toBe(
      'paused',
    )
  })

  it('paints idle without a track', () => {
    expect(
      resolveNowPlayingState(
        { playing: false, track: null },
        false,
        false,
        1_000,
        1_500,
      ),
    ).toBe('idle')
  })

  it('paints stale after 60 seconds without a successful update', () => {
    expect(
      resolveNowPlayingState(live, false, true, 1_000, 61_001),
    ).toBe('stale')
  })

  it('keeps the current state during the first minute of an error', () => {
    expect(
      resolveNowPlayingState(live, false, true, 1_000, 30_000),
    ).toBe('live')
  })
})
