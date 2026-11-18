interface IconProps {
  size?: number
  className?: string
}

function svgProps(size: number, className?: string) {
  return {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.7,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
    focusable: false,
    className,
  }
}

export function IconHome({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M3 10.7 12 3l9 7.7V21h-6v-6H9v6H3z" />
    </svg>
  )
}

export function IconMusic({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    </svg>
  )
}

export function IconMic({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <rect x="9" y="2.5" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3.5M8.5 21.5h7" />
    </svg>
  )
}

export function IconChart({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M4 20V11M10 20V4M16 20v-6M22 20H2" />
    </svg>
  )
}

export function IconBell({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M18 8.5a6 6 0 1 0-12 0c0 6.5-2.5 6.5-2.5 8.5h17C20.5 15 18 15 18 8.5Z" />
      <path d="M10.2 20.5a2 2 0 0 0 3.6 0" />
    </svg>
  )
}

export function IconSync({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M21 12a9 9 0 0 0-9-9 8.96 8.96 0 0 0-6.36 2.64M3 12a9 9 0 0 0 9 9 8.96 8.96 0 0 0 6.36-2.64M3 3v6h6M21 21v-6h-6" />
    </svg>
  )
}

export function IconSearch({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m16 16 4.5 4.5" />
    </svg>
  )
}

export function IconClose({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M6 6l12 12M18 6 6 18" />
    </svg>
  )
}

export function IconChevron({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="m9 5 7 7-7 7" />
    </svg>
  )
}

export function IconSparkle({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="m12 2.5 2.1 6.4 6.4 2.1-6.4 2.1-2.1 6.4-2.1-6.4L3.5 11l6.4-2.1z" />
      <path d="M19 16.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z" />
    </svg>
  )
}

export function IconCopy({ size = 18, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <rect x="8.5" y="8.5" width="12" height="12" rx="2.5" />
      <path d="M15.5 8.5v-2a2.5 2.5 0 0 0-2.5-2.5H6a2.5 2.5 0 0 0-2.5 2.5V13A2.5 2.5 0 0 0 6 15.5h2.5" />
    </svg>
  )
}

export function IconArrowUpRight({ size = 18, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M7 17 17 7M8 7h9v9" />
    </svg>
  )
}

export function IconCheck({ size = 18, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="m4.5 12.5 5 5 10-11" />
    </svg>
  )
}

export function IconClock({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5.2l3.4 2" />
    </svg>
  )
}

export function IconLock({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <rect x="4.5" y="10" width="15" height="11" rx="2.5" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </svg>
  )
}

export function IconKey({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <circle cx="8" cy="15" r="4" />
      <path d="m11 12 9-9M17 6l2.5 2.5M14 9l2 2" />
    </svg>
  )
}

export function IconEye({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M2.5 12S6 6 12 6s9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
      <circle cx="12" cy="12" r="2.6" />
    </svg>
  )
}

export function IconEyeOff({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M4 4l16 16M9.8 6.3A9.9 9.9 0 0 1 12 6c6 0 9.5 6 9.5 6a17 17 0 0 1-3.8 4.3M6.2 7.7A16.6 16.6 0 0 0 2.5 12S6 18 12 18a9.8 9.8 0 0 0 3.6-.7" />
      <path d="M10.5 10.5a2.1 2.1 0 0 0 3 3" />
    </svg>
  )
}

export function IconLogout({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M15 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4" />
      <path d="M10 12H3M7 8l-4 4 4 4" />
    </svg>
  )
}

export function IconFlame({ size = 20, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M12 3c.6 3.5-2.6 4.8-2.6 7.7a2.6 2.6 0 0 0 5.2 0c0-1.1-.4-2-1-2.9 2.6 1.4 4.4 4 4.4 6.6a6 6 0 0 1-12 0C6 9.6 9.4 6.3 12 3Z" />
    </svg>
  )
}

export function IconDownload({ size = 18, className }: IconProps) {
  return (
    <svg {...svgProps(size, className)}>
      <path d="M12 3v12M7 10l5 5 5-5M5 21h14" />
    </svg>
  )
}

export function Equalizer({ className }: { className?: string }) {
  return (
    <span className={`eq ${className ?? ''}`} aria-hidden="true">
      <i />
      <i />
      <i />
      <i />
    </span>
  )
}
