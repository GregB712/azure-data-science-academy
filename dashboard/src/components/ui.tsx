import type { ReactNode } from 'react'
import { content } from '../content/load'
import type { Doc } from '../content/model'
import { docHref } from '../lib/links'
import { isComplete, useProgress } from '../lib/progress'

export function Badge({ children, tone = 'neutral', title }: { children: ReactNode; tone?: string; title?: string }) {
  return (
    <span className={`badge badge-${tone}`} title={title}>
      {children}
    </span>
  )
}

const STATUS_TONE: Record<string, string> = {
  available: 'ok',
  'in-progress': 'warn',
  draft: 'warn',
  planned: 'muted',
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={STATUS_TONE[status] ?? 'neutral'}>{status}</Badge>
}

export const TYPE_LABEL: Record<string, string> = {
  lesson: 'Lesson',
  lab: 'Lab',
  reference: 'Reference',
  'module-overview': 'Module roadmap',
  project: 'Project',
  architecture: 'Architecture',
  page: 'Page',
}

export function ProgressBar({ pct, label }: { pct: number; label?: string }) {
  return (
    <div className="progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={label ?? 'Progress'}>
      <div className="progress-fill" style={{ width: `${pct}%` }} />
    </div>
  )
}

/** Circular progress, drawn as a stroke so it stays crisp at any size. */
export function ProgressRing({ pct, size = 88, label }: { pct: number; size?: number; label: string }) {
  const stroke = Math.max(6, Math.round(size / 11))
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  return (
    <svg className="ring" width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`${label}: ${pct}%`}>
      <circle className="ring-track" cx={size / 2} cy={size / 2} r={r} strokeWidth={stroke} />
      <circle
        className="ring-fill"
        cx={size / 2}
        cy={size / 2}
        r={r}
        strokeWidth={stroke}
        strokeDasharray={c}
        strokeDashoffset={c * (1 - Math.min(100, Math.max(0, pct)) / 100)}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle" className="ring-label">
        {pct}%
      </text>
    </svg>
  )
}

const ICONS: Record<string, ReactNode> = {
  home: <path d="M3.5 10.5 12 4l8.5 6.5M6 9v10.5h4.5V14h3v5.5H18V9" />,
  books: <><path d="M4 5.5h4v14H4zM10 5.5h4v14h-4z" /><path d="m16 6.2 3.8-1 3 13.4-3.8 1z" transform="translate(-1.5 0)" /></>,
  flask: <><path d="M9.5 3.5h5M10.5 3.5v5.2L5.2 18a1.6 1.6 0 0 0 1.4 2.5h10.8a1.6 1.6 0 0 0 1.4-2.5l-5.3-9.3V3.5" /><path d="M7.6 14.5h8.8" /></>,
  layers: <><path d="m12 4 8.5 4.5L12 13 3.5 8.5z" /><path d="m3.5 12.5 8.5 4.5 8.5-4.5M3.5 16.3l8.5 4.5 8.5-4.5" /></>,
  cloud: <path d="M7 18.5a4 4 0 0 1-.6-8A5.5 5.5 0 0 1 17 9a4.8 4.8 0 0 1 .5 9.5z" />,
  text: <><path d="M5 19.5 10 5h1l5 14.5M6.8 14.5h7.4" /><path d="M17 12.5h3M17 16h3" /></>,
  search: <><circle cx="10.5" cy="10.5" r="6" /><path d="m15 15 5 5" /></>,
  chart: <><path d="M4.5 19.5h15" /><path d="M7 16v-4M11 16V8M15 16v-6M19 16V5" /></>,
  map: <><path d="m3.5 6.5 5.5-2 6 2 5.5-2v13l-5.5 2-6-2-5.5 2z" /><path d="M9 4.5v13M15 6.5v13" /></>,
  flag: <><path d="M5.5 21V4" /><path d="M5.5 4.5h11l-2.5 4 2.5 4h-11" /></>,
  doc: <><path d="M6.5 3.5h7.5l4 4v13h-11.5z" /><path d="M13.5 3.5v4.5h4.5M9.5 12.5h5M9.5 16h5" /></>,
  chevron: <path d="m9.5 6 6 6-6 6" />,
  check: <path d="m5.5 12.5 4 4 9-9.5" />,
  sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4" /></>,
  moon: <path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z" />,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>,
}

/** A small stroked symbol set in the spirit of SF Symbols. Decorative unless given a label. */
export function Icon({ name, label, className = '' }: { name: keyof typeof ICONS | string; label?: string; className?: string }) {
  return (
    <svg
      className={`icon ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={label ? undefined : true}
      role={label ? 'img' : undefined}
      aria-label={label}
    >
      {ICONS[name]}
    </svg>
  )
}

export function CompletionMark({ doc }: { doc: Doc }) {
  const s = useProgress()
  return isComplete(doc, s) ? (
    <span className="done-mark" title="Completed">
      <Icon name="check" label="Completed" />
    </span>
  ) : null
}

/** Link to a document by id; renders the id itself if it does not exist yet. */
export function DocLink({ id, section }: { id: string; section?: string }) {
  const d = content.byId.get(id)
  if (!d) return <span className="missing-link" title="Not written yet">{id}</span>
  return (
    <a href={docHref(d.route, section)}>
      {d.title}
      {d.status === 'planned' ? ' (planned)' : ''}
    </a>
  )
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>
}
