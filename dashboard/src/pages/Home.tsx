import { content } from '../content/load'
import { Icon, ProgressBar, ProgressRing, StatusBadge, TYPE_LABEL } from '../components/ui'
import { docHref } from '../lib/links'
import { isComplete, moduleDocs, progressFor, useProgress } from '../lib/progress'

const QUICK_LINKS: { id: string; label: string; hint: string }[] = [
  { id: 'course-map', label: 'Course map', hint: 'All modules, status and cost-sensitive steps' },
  { id: 'architecture-decision-guide', label: 'Decision guide', hint: '12 decisions + scenarios' },
  { id: 'service-catalog', label: 'Service catalog', hint: 'Every Azure service used' },
  { id: 'lab-01-azure-setup', label: 'First lab', hint: 'Secure Azure setup from WSL' },
  { id: 'retail-forecasting-capstone', label: 'Capstone', hint: 'Retail demand forecasting' },
  { id: 'command-cheatsheet', label: 'Cheat sheet', hint: 'Commands and snippets' },
  { id: 'official-docs', label: 'Official docs', hint: 'Curated Microsoft Learn links' },
  { id: 'extending-the-academy', label: 'Extend', hint: 'Path into ML, MLOps, GenAI' },
]

export default function Home() {
  const s = useProgress()
  const { curriculum } = content
  const overall = progressFor(content.docs, s)
  const path = (curriculum.recommendedPath ?? []).map((id) => content.byId.get(id)).filter((d) => !!d)
  const next = path.find((d) => d && d.status !== 'planned' && !isComplete(d, s))
  const recent = s.recent.map((r) => ({ ...r, doc: content.byId.get(r.id) })).filter((r) => r.doc).slice(0, 5)

  return (
    <div className="page home">
      <section className="hero">
        <div className="hero-copy">
          <h1 className="large-title">{curriculum.title}</h1>
          <p className="lead">{curriculum.tagline}</p>
          <p className="muted">{curriculum.sequence}</p>
        </div>
        <div className="up-next">
          <ProgressRing pct={overall.pct} label="Overall course progress" />
          <div className="up-next-body">
            {next ? (
              <>
                <span className="up-next-kicker">{overall.done === 0 ? 'Start here' : 'Up next'}</span>
                <a className="up-next-title" href={docHref(next.route)}>{next.title}</a>
                <span className="small muted">
                  {TYPE_LABEL[next.type]}
                  {next.duration ? `, ${next.duration}` : ''}
                </span>
              </>
            ) : (
              <span className="up-next-title">Every available item is complete</span>
            )}
            <span className="small muted">
              {overall.done} of {overall.total} available lessons, labs and projects completed.{' '}
              <a href="#/progress">Progress details</a>
            </span>
          </div>
          {next && (
            <a className="btn primary large" href={docHref(next.route)}>
              {overall.done === 0 ? 'Start' : 'Continue'}
            </a>
          )}
        </div>
      </section>

      <section>
        <h2>Learning objectives</h2>
        <ul className="objectives">
          {curriculum.objectives.map((o) => (
            <li key={o}>{o}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Recommended sequence</h2>
        <ol className="sequence">
          {path.map((d, i) => {
            const done = isComplete(d!, s)
            const current = d!.id === next?.id
            return (
              <li key={d!.id} className={`${d!.status === 'planned' ? 'planned' : ''} ${done ? 'done' : ''} ${current ? 'current' : ''}`}>
                <span className="seq-node" aria-hidden>{done ? <Icon name="check" /> : i + 1}</span>
                <div className="seq-body">
                  <a href={docHref(d!.route)} aria-current={current ? 'step' : undefined}>{d!.title}</a>
                  <span className="seq-meta">
                    <span className="muted small">{TYPE_LABEL[d!.type]}</span>
                    {d!.status !== 'available' && <StatusBadge status={d!.status} />}
                    {done && <span className="visually-hidden">Completed</span>}
                  </span>
                </div>
              </li>
            )
          })}
        </ol>
      </section>

      <section>
        <h2>Modules</h2>
        <div className="grid cards">
          {curriculum.modules.map((m) => {
            const docs = moduleDocs(content, m.number)
            const p = progressFor(docs, s)
            const first = docs.sort((a, b) => a.order - b.order).find((d) => d.type !== 'module-overview') ?? docs[0]
            return (
              <article key={m.id} className={`card module-card ${m.status}`}>
                <header>
                  <span className="mod-num big">{m.number}</span>
                  <StatusBadge status={m.status} />
                </header>
                <h3>{first ? <a href={docHref(first.route)}>{m.title}</a> : m.title}</h3>
                <p className="small">{m.description}</p>
                <footer>
                  <span className="small muted"><Icon name="clock" /> {m.estimatedHours} h</span>
                  {p.total > 0 ? (
                    <>
                      <ProgressBar pct={p.pct} label={`Module ${m.number} progress`} />
                      <span className="small muted">{p.done}/{p.total} done</span>
                    </>
                  ) : (
                    <span className="small muted">roadmap only</span>
                  )}
                </footer>
              </article>
            )
          })}
        </div>
      </section>

      <div className="grid two">
        <section>
          <h2>Recently opened</h2>
          {recent.length === 0 ? (
            <p className="muted">Nothing yet. Pages you open are listed here (stored in this browser).</p>
          ) : (
            <ul className="plain-list">
              {recent.map((r) => (
                <li key={r.id}>
                  <a href={docHref(r.doc!.route)}>{r.doc!.title}</a>{' '}
                  <span className="small muted">{new Date(r.at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h2>Quick links</h2>
          <div className="quick-links">
            {QUICK_LINKS.map((q) => {
              const d = content.byId.get(q.id)
              return d ? (
                <a key={q.id} className="quick" href={docHref(d.route)}>
                  <strong>{q.label}</strong>
                  <span className="small muted">{q.hint}</span>
                </a>
              ) : null
            })}
            <a className="quick" href="#/architecture"><strong>Architecture</strong><span className="small muted">Mesh, lakehouse, ML, RAG</span></a>
            <a className="quick" href="#/glossary"><strong>Glossary</strong><span className="small muted">Patterns vs products</span></a>
          </div>
        </section>
      </div>
    </div>
  )
}
