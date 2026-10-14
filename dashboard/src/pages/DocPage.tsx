import { useEffect } from 'react'
import { content } from '../content/load'
import type { Doc } from '../content/model'
import MarkdownView from '../components/MarkdownView'
import { Badge, DocLink, ProgressBar, StatusBadge, TYPE_LABEL } from '../components/ui'
import { checklistDone, isComplete, isTrackable, progressStore, useProgress } from '../lib/progress'
import { docHref, fileHref } from '../lib/links'
import { dirname } from '../lib/paths'
import NotFound from './NotFound'

function sectionStarting(doc: Doc, prefix: string) {
  return doc.headings.find((h) => h.depth === 2 && h.text.startsWith(prefix))
}

function sectionNamed(doc: Doc, re: RegExp) {
  return doc.headings.find((h) => h.depth === 2 && re.test(h.text))
}

function LabPanel({ doc }: { doc: Doc }) {
  const s = useProgress()
  const done = checklistDone(doc, s)
  const pct = doc.checklist.length ? Math.round((100 * done) / doc.checklist.length) : 0
  const files = [...content.files.keys()].filter((p) => p.startsWith(`${dirname(doc.path)}/`))
  const links = [
    sectionNamed(doc, /^prerequisites/i),
    sectionNamed(doc, /^required azure resources/i),
    sectionNamed(doc, /^cost and safety/i),
    sectionNamed(doc, /^step-by-step/i),
    sectionNamed(doc, /^verification criteria/i),
    sectionNamed(doc, /^cleanup/i),
    sectionNamed(doc, /^troubleshooting/i),
  ].filter(Boolean)

  return (
    <div className="panel">
      <h2>Lab tracker</h2>
      <dl className="facts">
        {doc.duration && (<><dt>Duration</dt><dd>{doc.duration}</dd></>)}
        {doc.cost && (<><dt>Cost</dt><dd>{doc.cost}</dd></>)}
        {doc.azureResources.length > 0 && (<><dt>Azure resources</dt><dd>{doc.azureResources.join(', ')}</dd></>)}
      </dl>
      <h3>Completion checklist</h3>
      <ProgressBar pct={pct} label="Lab checklist progress" />
      <p className="small muted">{done}/{doc.checklist.length} done</p>
      <ul className="checklist">
        {doc.checklist.map((item) => {
          const checked = !!s.checklist[doc.id]?.[item.key]
          return (
            <li key={item.key}>
              <label>
                <input type="checkbox" checked={checked} onChange={(e) => progressStore.setChecklist(doc.id, item.key, e.target.checked)} />
                <span>{item.text.replace(/`/g, '')}</span>
              </label>
            </li>
          )
        })}
      </ul>
      <h3>Jump to</h3>
      <ul className="plain-list small">
        {links.map((h) => <li key={h!.slug}><a href={docHref(doc.route, h!.slug)}>{h!.text}</a></li>)}
      </ul>
      {files.length > 0 && (
        <>
          <h3>Code in this lab</h3>
          <ul className="plain-list small mono">
            {files.map((f) => <li key={f}><a href={fileHref(f)}>{f.slice(dirname(doc.path).length + 1)}</a></li>)}
          </ul>
        </>
      )}
    </div>
  )
}

export default function DocPage({ route, section }: { route: string; section: string | null }) {
  const doc = content.docs.find((d) => d.route === route)
  const s = useProgress()

  useEffect(() => {
    if (doc) progressStore.visit(doc.id)
    if (doc && !section) window.scrollTo(0, 0)
  }, [doc?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!doc) return <NotFound what={route} />

  const idx = content.sequence.findIndex((d) => d.id === doc.id)
  const prev = idx > 0 ? content.sequence[idx - 1] : undefined
  const next = idx >= 0 && idx < content.sequence.length - 1 ? content.sequence[idx + 1] : undefined
  const module = content.curriculum.modules.find((m) => m.number === doc.module)
  const toc = doc.headings.filter((h) => h.depth === 2)
  const exercise = sectionStarting(doc, '9.')
  const code = sectionStarting(doc, '7.')
  const complete = isComplete(doc, s)
  const relatedArch = content.docs.filter((d) => d.type === 'architecture' && d.lessons.includes(doc.id))

  return (
    <div className="page doc-page">
      <nav className="breadcrumbs small" aria-label="Breadcrumb">
        <a href="#/">Dashboard</a> /{' '}
        {module ? <a href={`#/catalog?module=${module.number}`}>Module {module.number}: {module.title}</a> : <a href="#/catalog">Catalog</a>} /{' '}
        <span>{TYPE_LABEL[doc.type]}</span>
      </nav>
      <header className="doc-header">
        <div className="doc-meta">
          <span className="pill">{TYPE_LABEL[doc.type]}</span>
          <StatusBadge status={doc.status} />
          {doc.duration && <Badge>⏱ {doc.duration}</Badge>}
          {doc.level && <Badge>{doc.level}</Badge>}
        </div>
        {doc.summary && <p className="lead">{doc.summary}</p>}
        <div className="doc-actions">
          {isTrackable(doc) && (
            <button type="button" className={`btn ${complete ? 'done' : 'primary'}`} onClick={() => progressStore.toggleComplete(doc.id)}>
              {complete ? '✓ Completed (undo)' : 'Mark as complete'}
            </button>
          )}
          {exercise && <a className="btn" href={docHref(doc.route, exercise.slug)}>Exercise</a>}
          {code && <a className="btn" href={docHref(doc.route, code.slug)}>Code</a>}
          <a className="btn ghost small" href={fileHref(doc.path)} title="View the Markdown source">Source</a>
        </div>
        {(doc.prerequisites.length > 0 || doc.related.length > 0 || relatedArch.length > 0) && (
          <div className="doc-links small">
            {doc.prerequisites.length > 0 && (
              <p><strong>Prerequisites:</strong> {doc.prerequisites.map((id, i) => <span key={id}>{i > 0 && ' · '}<DocLink id={id} /></span>)}</p>
            )}
            {doc.related.length > 0 && (
              <p><strong>Related:</strong> {doc.related.map((id, i) => <span key={id}>{i > 0 && ' · '}<DocLink id={id} /></span>)}</p>
            )}
            {relatedArch.length > 0 && (
              <p><strong>Architecture views:</strong> {relatedArch.map((a, i) => <span key={a.id}>{i > 0 && ' · '}<a href={`#/architecture?v=${a.id}`}>{a.title}</a></span>)}</p>
            )}
          </div>
        )}
      </header>

      <div className="doc-grid">
        <article className="doc-body">
          <MarkdownView body={doc.body} path={doc.path} docId={doc.id} scrollTo={section} />
        </article>
        <aside className="doc-aside">
          {doc.type === 'lab' && <LabPanel doc={doc} />}
          {toc.length > 2 && (
            <div className="panel toc">
              <h2>On this page</h2>
              <ul>
                {toc.map((h) => <li key={h.slug}><a href={docHref(doc.route, h.slug)}>{h.text}</a></li>)}
              </ul>
            </div>
          )}
        </aside>
      </div>

      {(prev || next) && (
        <nav className="prev-next" aria-label="Previous and next">
          {prev ? <a className="card" href={docHref(prev.route)}><span className="small muted">← Previous</span><strong>{prev.title}</strong></a> : <span />}
          {next ? <a className="card next" href={docHref(next.route)}><span className="small muted">Next →</span><strong>{next.title}</strong></a> : <span />}
        </nav>
      )}
    </div>
  )
}
