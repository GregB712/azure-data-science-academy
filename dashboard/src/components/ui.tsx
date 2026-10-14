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

export function CompletionMark({ doc }: { doc: Doc }) {
  const s = useProgress()
  return isComplete(doc, s) ? (
    <span className="done-mark" title="Completed" aria-label="Completed">
      ✓
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
