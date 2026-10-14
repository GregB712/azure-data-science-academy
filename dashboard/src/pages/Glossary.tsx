import { useEffect, useMemo, useState } from 'react'
import MarkdownView from '../components/MarkdownView'
import { Empty } from '../components/ui'
import { content } from '../content/load'
import { kindGroup, parseGlossary } from '../lib/catalog'

export default function Glossary({ focus }: { focus: string | null }) {
  const doc = content.byId.get('glossary')
  const all = useMemo(() => parseGlossary(doc?.body ?? '').sort((a, b) => a.term.localeCompare(b.term)), [doc])
  const [q, setQ] = useState('')
  const [kind, setKind] = useState('')
  const kinds = [...new Set(all.map((e) => kindGroup(e.kind)))].sort()
  const needle = q.trim().toLowerCase()
  const shown = all.filter(
    (e) => (!kind || kindGroup(e.kind) === kind) && (!needle || `${e.term} ${e.definition}`.toLowerCase().includes(needle)),
  )

  useEffect(() => {
    if (!focus) return
    const t = setTimeout(() => document.getElementById(`term-${focus}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
    return () => clearTimeout(t)
  }, [focus])

  if (!doc) return <Empty>GLOSSARY.md was not found.</Empty>
  return (
    <div className="page">
      <h1>Glossary</h1>
      <p className="muted">
        {all.length} terms. Each is labelled by kind: an Azure service, an open-source technology, a pattern, or a concept. Source:{' '}
        <a href="#/doc/GLOSSARY">GLOSSARY.md</a>.
      </p>
      <div className="filters">
        <input type="search" placeholder="Filter terms" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Filter glossary" />
        <div className="chips" role="group" aria-label="Kind">
          <button type="button" className={`chip ${kind === '' ? 'active' : ''}`} onClick={() => setKind('')}>All</button>
          {kinds.map((k) => (
            <button type="button" key={k} className={`chip ${kind === k ? 'active' : ''}`} onClick={() => setKind(k)}>{k}</button>
          ))}
        </div>
      </div>
      {shown.length === 0 && <Empty>No terms match.</Empty>}
      <dl className="glossary">
        {shown.map((e) => (
          <div key={e.slug} id={`term-${e.slug}`} className={`glossary-entry ${focus === e.slug ? 'focused' : ''}`}>
            <dt>
              <a href={`#/glossary?t=${e.slug}`}>{e.term}</a> {e.kind && <span className="pill pill-kind">{e.kind}</span>}
            </dt>
            <dd><MarkdownView inline body={e.definition} path="GLOSSARY.md" /></dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
