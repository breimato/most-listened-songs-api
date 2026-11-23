import { peekCover } from '../hooks/useArtwork'
import type { Recap } from '../types/api'
import type { RecapPeriod } from './recaps'
import { initials } from './format'
import { buildComparisons } from './comparisons'

const WIDTH = 1080
const HEIGHT = 1350
const DISPLAY_FONT = "'Bricolage Grotesque', sans-serif"
const BODY_FONT = "'Instrument Sans', sans-serif"
const nf = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 0 })

function formatHours(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)} min`
  return `${new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 }).format(
    Math.round(hours * 10) / 10,
  )} h`
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  ctx.beginPath()
  ctx.roundRect(x, y, width, height, radius)
}

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number,
): string[] {
  const words = text.split(' ')
  const lines: string[] = []
  let line = ''
  for (const word of words) {
    const next = line ? `${line} ${word}` : word
    if (ctx.measureText(next).width > maxWidth && line) {
      lines.push(line)
      line = word
    } else {
      line = next
    }
  }
  if (line) lines.push(line)
  return lines
}

async function loadImage(url: string | null): Promise<HTMLImageElement | null> {
  if (!url) return null
  return new Promise((resolve) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = () => resolve(null)
    image.src = url
  })
}

async function renderCard(data: Recap, period: RecapPeriod): Promise<HTMLCanvasElement> {
  await document.fonts.ready

  const canvas = document.createElement('canvas')
  canvas.width = WIDTH
  canvas.height = HEIGHT
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas no disponible')

  const approximate = data.duration_coverage < 0.9
  const hours = approximate ? data.estimated_hours : data.total_hours
  const topSong = data.top_song
  const topArtist = data.top_artists[0]
  const comparisons = buildComparisons(Math.round(hours * 60))
    .filter((comparison) => comparison.key !== 'smi')
    .slice(0, 2)
  const cover = await loadImage(
    topSong ? peekCover(topSong.artist, topSong.title) : null,
  )

  // Fondo
  ctx.fillStyle = '#0a0a0b'
  ctx.fillRect(0, 0, WIDTH, HEIGHT)

  const glow = ctx.createLinearGradient(0, 0, WIDTH, HEIGHT * 0.62)
  glow.addColorStop(0, period.palette.from)
  glow.addColorStop(1, period.palette.to)
  ctx.fillStyle = glow
  ctx.fillRect(0, 0, WIDTH, HEIGHT * 0.52)

  const fade = ctx.createLinearGradient(0, HEIGHT * 0.16, 0, HEIGHT * 0.64)
  fade.addColorStop(0, 'rgba(10,10,11,0)')
  fade.addColorStop(1, '#0a0a0b')
  ctx.fillStyle = fade
  ctx.fillRect(0, 0, WIDTH, HEIGHT * 0.64)

  // Cabecera
  ctx.textBaseline = 'top'
  ctx.fillStyle = 'rgba(255,255,255,0.88)'
  ctx.font = `800 27px ${DISPLAY_FONT}`
  ctx.fillText('GROBEATS FM', 64, 60)

  ctx.textAlign = 'right'
  ctx.fillStyle = 'rgba(255,255,255,0.72)'
  ctx.font = `600 22px ${BODY_FONT}`
  ctx.fillText(period.label.toUpperCase(), WIDTH - 64, 64)
  ctx.textAlign = 'left'

  ctx.fillStyle = '#ffffff'
  ctx.font = `800 62px ${DISPLAY_FONT}`
  const titleLines = wrapText(ctx, period.title, WIDTH - 128).slice(0, 2)
  titleLines.forEach((line, index) => {
    ctx.fillText(line, 64, 128 + index * 68)
  })

  // Portada
  const coverY = 290
  ctx.save()
  roundRect(ctx, 64, coverY, 300, 300, 24)
  ctx.clip()
  if (cover) {
    ctx.drawImage(cover, 64, coverY, 300, 300)
  } else {
    const fallback = ctx.createLinearGradient(64, coverY, 364, coverY + 300)
    fallback.addColorStop(0, period.palette.from)
    fallback.addColorStop(1, period.palette.to)
    ctx.fillStyle = fallback
    ctx.fillRect(64, coverY, 300, 300)
    ctx.fillStyle = 'rgba(255,255,255,0.82)'
    ctx.font = `800 84px ${DISPLAY_FONT}`
    ctx.textAlign = 'center'
    ctx.fillText(initials(topSong?.artist ?? '?'), 214, coverY + 96)
    ctx.textAlign = 'left'
  }
  ctx.restore()

  // Canción
  const textX = 400
  const textWidth = WIDTH - textX - 64
  ctx.fillStyle = 'rgba(255,255,255,0.65)'
  ctx.font = `700 20px ${BODY_FONT}`
  ctx.fillText('TU CANCIÓN', textX, coverY + 6)

  ctx.fillStyle = '#ffffff'
  ctx.font = `800 42px ${DISPLAY_FONT}`
  const songLines = wrapText(ctx, topSong?.title ?? '—', textWidth).slice(0, 2)
  songLines.forEach((line, index) => {
    ctx.fillText(line, textX, coverY + 40 + index * 48)
  })

  ctx.fillStyle = 'rgba(255,255,255,0.8)'
  ctx.font = `600 25px ${BODY_FONT}`
  ctx.fillText(topSong?.artist ?? '', textX, coverY + 142)

  ctx.fillStyle = 'rgba(255,255,255,0.6)'
  ctx.font = `500 21px ${BODY_FONT}`
  if (topSong) {
    ctx.fillText(
      `${nf.format(topSong.plays)} plays · ${topSong.days} días`,
      textX,
      coverY + 180,
    )
  }

  // Horas
  ctx.fillStyle = '#ffffff'
  ctx.font = `800 104px ${DISPLAY_FONT}`
  ctx.fillText(`${approximate ? '≈ ' : ''}${formatHours(hours)}`, 64, 650)

  ctx.fillStyle = 'rgba(255,255,255,0.68)'
  ctx.font = `700 21px ${BODY_FONT}`
  ctx.fillText('DE MÚSICA', 66, 764)

  ctx.fillStyle = 'rgba(255,255,255,0.82)'
  ctx.font = `600 27px ${BODY_FONT}`
  ctx.fillText(
    `${nf.format(data.total_plays)} reproducciones · ${nf.format(data.unique_artists)} artistas`,
    64,
    806,
  )

  // Artista + géneros
  ctx.fillStyle = 'rgba(255,255,255,0.62)'
  ctx.font = `700 19px ${BODY_FONT}`
  ctx.fillText('TU ARTISTA', 64, 876)

  ctx.fillStyle = '#ffffff'
  ctx.font = `800 38px ${DISPLAY_FONT}`
  ctx.fillText(topArtist?.artist ?? '—', 64, 902)

  ctx.fillStyle = 'rgba(255,255,255,0.72)'
  ctx.font = `500 21px ${BODY_FONT}`
  if (topArtist) {
    ctx.fillText(
      `${nf.format(topArtist.plays)} plays · ${formatHours(topArtist.minutes / 60)}`,
      64,
      952,
    )
  }

  if (data.top_genres.length) {
    ctx.fillStyle = 'rgba(255,255,255,0.7)'
    ctx.font = `600 21px ${BODY_FONT}`
    ctx.fillText(
      data.top_genres.slice(0, 3).map((genre) => genre.name).join(' · '),
      64,
      1000,
    )
  }

  ctx.fillStyle = 'rgba(255,255,255,0.55)'
  ctx.font = `500 20px ${BODY_FONT}`
  ctx.fillText(`Perfil: ${data.profile.label}`, 64, 1036)

  // Comparaciones
  let comparisonY = 1100
  for (const comparison of comparisons) {
    ctx.fillStyle = 'rgba(255,255,255,0.55)'
    ctx.font = `600 19px ${BODY_FONT}`
    ctx.fillText(comparison.label, 64, comparisonY)
    ctx.fillStyle = '#1ed760'
    ctx.font = `800 32px ${DISPLAY_FONT}`
    ctx.fillText(comparison.value, 64, comparisonY + 24)
    comparisonY += 82
  }

  // Pie
  ctx.fillStyle = 'rgba(255,255,255,0.42)'
  ctx.font = `500 19px ${BODY_FONT}`
  ctx.fillText('breimato.es/youtube', 64, HEIGHT - 58)

  ctx.textAlign = 'right'
  ctx.fillText('GroBeats FM', WIDTH - 64, HEIGHT - 58)
  ctx.textAlign = 'left'

  return canvas
}

function canvasToBlob(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob)
      else reject(new Error('No se pudo generar el PNG'))
    }, 'image/png')
  })
}

export async function shareRecapCard(
  data: Recap,
  period: RecapPeriod,
): Promise<'shared' | 'downloaded'> {
  const canvas = await renderCard(data, period)
  const blob = await canvasToBlob(canvas)
  const filename = `wrapped-${period.season}-${period.label.replace(/\s+/g, '-').toLowerCase()}.png`

  const shareData = {
    files: [new File([blob], filename, { type: 'image/png' })],
    title: period.title,
    text: `${period.title} · ${period.range}`,
  }

  const navigatorWithShare = navigator as Navigator & {
    canShare?: (data: ShareData) => boolean
    share?: (data: ShareData) => Promise<void>
  }

  if (navigatorWithShare.canShare?.(shareData) && navigatorWithShare.share) {
    await navigatorWithShare.share(shareData)
    return 'shared'
  }

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  return 'downloaded'
}
