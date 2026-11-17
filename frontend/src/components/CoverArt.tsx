import type { CSSProperties } from 'react'

import { coverSeed, useArtwork } from '../hooks/useArtwork'
import { initials } from '../utils/format'

type CoverSize = 'xs' | 'sm' | 'md' | 'lg' | 'hero'

interface CoverArtProps {
  artist: string
  title: string
  size?: CoverSize
  round?: boolean
  src?: string | null
  className?: string
}

export function CoverArt({
  artist,
  title,
  size = 'md',
  round = false,
  src,
  className,
}: CoverArtProps) {
  const resolved = useArtwork(artist, title)
  const url = src !== undefined ? src : resolved
  const style = coverSeed(artist || title, title)

  return (
    <span
      className={`cover cover--${size}${round ? ' cover--round' : ''}${className ? ` ${className}` : ''}`}
      style={style as CSSProperties}
    >
      <span className="cover__fallback">{initials(artist || title)}</span>
      {url ? (
        <img
          src={url}
          alt=""
          loading="lazy"
          decoding="async"
          onError={(event) => {
            event.currentTarget.style.display = 'none'
          }}
        />
      ) : null}
      <span className="cover__shine" aria-hidden="true" />
    </span>
  )
}
