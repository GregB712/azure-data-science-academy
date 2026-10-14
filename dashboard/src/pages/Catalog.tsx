import { useMemo, useState } from 'react'
import { content } from '../content/load'
import { CompletionMark, StatusBadge, TYPE_LABEL } from '../components/ui'
import { docHref } from '../lib/links'

const TYPES = ['lesson', 'lab', 'module-overview', 'project', 'architecture', 'reference']

export default function Catalog({ params }: { params: URLSearchParams }) {
  const [text, setText] = useState(params.get('q') ?? '')
  const [type, setType] = useState(params.get('type') ?? '')
  const [mod, setMod] = useState(params.get('module') ?? '')
  const [status, setStatus] = useState('')

  const docs = useMemo(() => {
    const t = text.toLowerCase().trim()
    return content.docs
      .filter((d) => d.type !== 'page')
      .filter((d) => !type || d.type === type)
      .filter((d) => !mod || String(d.module ?? '') === mod)
      .filter((d) => !status || d.status === status)
      .filter((d) => !t || `${d.title} ${d.summary} ${d.tags.join(' ')}`.toLowerCase().includes(t))
      .sort((a, b) => (a.module ?? 99) - (b.module ?? 99) || a.order - b.order || a.title.localeCompare(b.title))
  }, [text, type, mod, status])

  const statuses = [...new Set(content.docs.map((d) => d.status))]

  return (
    <div className="page">
      <h1>Lesson catalog</h1>
      <p className="muted">Every lesson, lab, roadmap, architecture view and reference page in the dossier. Filter, then open.</p>
      <div className="filters">
        <input type="search" placeholder="Filter by title, summary or tag" value={text} onChange={(e) => setText(e.target.value)} aria-label="Filter catalog" />
        <select value={type} onChange={(e) => setType(e.target.value)} aria-label="Type">
          <option value="">All types</option>
          {TYPES.map((t) => <option key={t} value={t}>{TYPE_LABEL[t]}</option>)}
        </select>
        <select value={mod} onChange={(e) => setMod(e.target.value)} aria-label="Module">
          <option value="">All modules</option>
          {content.curriculum.modules.map((m) => <option key={m.id} value={m.number}>{m.number}. {m.title}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status">
          <option value="">Any status</option>
          {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <p className="small muted">{docs.length} item(s)</p>
      <div className="catalog-list">
        {docs.map((d) => (
          <a key={d.id} className="catalog-item card" href={docHref(d.route)}>
            <div className="catalog-meta">
              <span className="pill">{TYPE_LABEL[d.type]}</span>
              {d.module !== undefined && <span className="pill">Module {d.module}</span>}
              <StatusBadge status={d.status} />
              {d.duration && <span className="small muted">⏱ {d.duration}</span>}
              <CompletionMark doc={d} />
            </div>
            <strong>{d.title}</strong>
            {d.summary && <span className="small">{d.summary}</span>}
            {d.tags.length > 0 && <span className="tags">{d.tags.slice(0, 8).map((t) => <span key={t} className="tag">#{t}</span>)}</span>}
          </a>
        ))}
      </div>
    </div>
  )
}
