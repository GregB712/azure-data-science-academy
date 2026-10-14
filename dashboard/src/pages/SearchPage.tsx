import { useMemo, useState } from 'react'
import { Empty, TYPE_LABEL } from '../components/ui'
import { content } from '../content/load'
import { docHref } from '../lib/links'
import { navigate } from '../lib/router'
import { buildSearchIndex, snippet } from '../lib/search'

let index: ReturnType<typeof buildSearchIndex> | null = null
const getIndex = () => (index ??= buildSearchIndex(content))

export default function SearchPage({ query }: { query: string }) {
  const [type, setType] = useState('')
  const [draft, setDraft] = useState(query)
  const results = useMemo(() => {
    const q = query.trim()
    if (!q) return []
    let r = getIndex().search(q)
    if (r.length === 0) r = getIndex().search(q, { combineWith: 'OR' })
    return r
  }, [query])
  const shown = results.filter((r) => !type || r.type === type).slice(0, 60)
  const types = [...new Set(results.map((r) => r.type as string))]

  return (
    <div className="page">
      <h1>Search</h1>
      <form
        className="filters"
        onSubmit={(e) => {
          e.preventDefault()
          navigate(`/search?q=${encodeURIComponent(draft)}`)
        }}
      >
        <input type="search" value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Search every lesson, lab and reference" aria-label="Search" autoFocus />
        <select value={type} onChange={(e) => setType(e.target.value)} aria-label="Type">
          <option value="">All types</option>
          {types.map((t) => <option key={t} value={t}>{TYPE_LABEL[t] ?? t}</option>)}
        </select>
        <button type="submit">Search</button>
      </form>
      {!query.trim() ? (
        <Empty>Type a word or phrase. Search covers the full text of every page, section by section, with prefix and light fuzzy matching.</Empty>
      ) : shown.length === 0 ? (
        <Empty>No results for “{query}”.</Empty>
      ) : (
        <>
          <p className="small muted">{results.length} matching sections{results.length > 60 ? ' (top 60 shown)' : ''}</p>
          <ol className="search-results">
            {shown.map((r) => (
              <li key={r.id}>
                <a href={docHref(r.route as string, (r.slug as string) || undefined)}>
                  <span className="result-title">{r.title as string}</span>
                  {r.heading !== r.title && <span className="result-heading"> › {r.heading as string}</span>}
                </a>
                <span className="pill">{TYPE_LABEL[r.type as string] ?? (r.type as string)}</span>
                <p className="small">{snippet(r.text as string, query)}</p>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  )
}
