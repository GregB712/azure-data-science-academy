import { useEffect, useMemo, useState } from 'react'
import MarkdownView from '../components/MarkdownView'
import { Empty } from '../components/ui'
import { content } from '../content/load'
import { parseServiceCatalog } from '../lib/catalog'

const ORDER = ['What it is', 'Role in the architecture', 'Typical DS/AI uses', 'Cost model', 'Watch out', 'Lessons', 'Docs']

export default function Services({ focus }: { focus: string | null }) {
  const doc = content.byId.get('service-catalog')
  const all = useMemo(() => parseServiceCatalog(doc?.body ?? ''), [doc])
  const [q, setQ] = useState('')
  const [category, setCategory] = useState('')
  const [kind, setKind] = useState('')
  const categories = [...new Set(all.map((s) => s.fields['Category'] ?? s.group))].filter(Boolean).sort()
  const kinds = [...new Set(all.map((s) => s.fields['Kind'] ?? ''))].filter(Boolean).sort()

  const needle = q.trim().toLowerCase()
  const shown = all.filter(
    (s) =>
      (!category || (s.fields['Category'] ?? s.group) === category) &&
      (!kind || s.fields['Kind'] === kind) &&
      (!needle || `${s.name} ${Object.values(s.fields).join(' ')}`.toLowerCase().includes(needle)),
  )

  useEffect(() => {
    if (!focus) return
    const t = setTimeout(() => document.getElementById(`svc-${focus}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
    return () => clearTimeout(t)
  }, [focus])

  if (!doc) return <Empty>SERVICE_CATALOG.md was not found.</Empty>
  return (
    <div className="page">
      <h1>Service lookup</h1>
      <p className="muted">
        {all.length} services, tools and open formats used in the academy, each with what it is, its role, cost model and caveats. The source is{' '}
        <a href="#/doc/SERVICE_CATALOG">SERVICE_CATALOG.md</a>.
      </p>
      <div className="filters">
        <input type="search" placeholder="Filter services (e.g. lakehouse, identity, vector)" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Filter services" />
        <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
          <option value="">All categories</option>
          {categories.map((c) => <option key={c}>{c}</option>)}
        </select>
        <select value={kind} onChange={(e) => setKind(e.target.value)} aria-label="Kind">
          <option value="">All kinds</option>
          {kinds.map((k) => <option key={k}>{k}</option>)}
        </select>
      </div>
      <p className="small muted">{shown.length} shown</p>
      {shown.length === 0 && <Empty>No services match.</Empty>}
      <div className="grid service-grid">
        {shown.map((s) => (
          <article key={s.slug} id={`svc-${s.slug}`} className={`card service-card ${focus === s.slug ? 'focused' : ''}`}>
            <header>
              <h3>{s.name}</h3>
              <div className="badges">
                {s.fields['Category'] && <span className="pill">{s.fields['Category']}</span>}
                {s.fields['Kind'] && <span className="pill pill-kind">{s.fields['Kind']}</span>}
              </div>
            </header>
            <dl className="service-fields">
              {ORDER.filter((f) => s.fields[f]).map((f) => (
                <div key={f}>
                  <dt>{f}</dt>
                  <dd><MarkdownView inline body={s.fields[f]} path="SERVICE_CATALOG.md" /></dd>
                </div>
              ))}
            </dl>
          </article>
        ))}
      </div>
    </div>
  )
}
