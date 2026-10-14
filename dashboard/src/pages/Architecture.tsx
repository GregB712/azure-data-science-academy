import { useMemo } from 'react'
import MarkdownView from '../components/MarkdownView'
import { DocLink, Empty, StatusBadge } from '../components/ui'
import { content } from '../content/load'
import { parseServiceCatalog } from '../lib/catalog'
import { docHref } from '../lib/links'
import { slugify } from '../lib/slug'

export default function Architecture({ selected }: { selected: string | null }) {
  const diagrams = content.docs.filter((d) => d.type === 'architecture').sort((a, b) => a.path.localeCompare(b.path))
  const services = useMemo(() => {
    const cat = content.byId.get('service-catalog')
    return new Map(parseServiceCatalog(cat?.body ?? '').map((s) => [s.slug, s]))
  }, [])
  const current = diagrams.find((d) => d.id === selected) ?? diagrams[0]

  return (
    <div className="page arch-page">
      <h1>Architecture explorer</h1>
      <p className="muted">
        Reference architectures for the academy. Pick a view; the panel lists the Azure services it uses (open one for its role, cost and
        caveats) and the lessons that explain it.
      </p>
      <div className="tabs" role="tablist" aria-label="Architecture views">
        {diagrams.map((d) => (
          <a key={d.id} role="tab" aria-selected={d.id === current?.id} className={`tab ${d.id === current?.id ? 'active' : ''}`} href={`#/architecture?v=${d.id}`}>
            {d.title}
            {d.status === 'planned' ? ' (planned)' : ''}
          </a>
        ))}
      </div>
      {!current ? (
        <Empty>No architecture views found in diagrams/.</Empty>
      ) : (
        <div className="with-aside">
          <article>
            <div className="doc-meta">
              <StatusBadge status={current.status} />
              <a className="small" href={docHref(current.route)}>Open as a page</a>
            </div>
            <MarkdownView body={current.body} path={current.path} />
          </article>
          <aside className="aside">
            <section className="panel">
              <h2>Services in this view</h2>
              {current.services.length === 0 && <Empty>No services listed.</Empty>}
              <ul className="service-list">
                {current.services.map((name) => {
                  const s = services.get(slugify(name))
                  return (
                    <li key={name}>
                      {s ? <a href={`#/services?s=${s.slug}`}>{s.name}</a> : <span className="missing-link">{name}</span>}
                      {s?.fields['Kind'] && <span className="small muted"> · {s.fields['Kind']}</span>}
                    </li>
                  )
                })}
              </ul>
            </section>
            {current.lessons.length > 0 && (
              <section className="panel">
                <h2>Explained in</h2>
                <ul>
                  {current.lessons.map((id) => (
                    <li key={id}><DocLink id={id} /></li>
                  ))}
                </ul>
              </section>
            )}
          </aside>
        </div>
      )}
    </div>
  )
}
