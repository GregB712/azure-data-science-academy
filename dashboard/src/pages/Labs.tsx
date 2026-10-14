import { content } from '../content/load'
import { ProgressBar, StatusBadge } from '../components/ui'
import { checklistDone, isComplete, useProgress } from '../lib/progress'
import { docHref } from '../lib/links'

export default function Labs() {
  const s = useProgress()
  const labs = content.docs.filter((d) => d.type === 'lab').sort((a, b) => (a.module ?? 0) - (b.module ?? 0))
  const existing = new Set(labs.map((l) => l.id))
  const planned = content.curriculum.modules.flatMap((m) => m.labs.filter((id) => !existing.has(id)).map((id) => ({ id, module: m })))

  return (
    <div className="page">
      <h1>Lab tracker</h1>
      <p className="muted">
        Hands-on labs with prerequisites, Azure resources, cost, checklists and cleanup. Tick items here or inside the lab; both stay in sync.
        A lab counts as complete when every checklist item is ticked or you mark it complete.
      </p>
      <div className="grid cards">
        {labs.map((lab) => {
          const done = checklistDone(lab, s)
          const pct = lab.checklist.length ? Math.round((100 * done) / lab.checklist.length) : 0
          return (
            <article key={lab.id} className="card lab-card">
              <header>
                <span className="pill">Module {lab.module}</span>
                <StatusBadge status={isComplete(lab, s) ? 'completed' : lab.status} />
              </header>
              <h3><a href={docHref(lab.route)}>{lab.title}</a></h3>
              <p className="small">{lab.summary}</p>
              <dl className="facts small">
                {lab.duration && (<><dt>Duration</dt><dd>{lab.duration}</dd></>)}
                {lab.cost && (<><dt>Cost</dt><dd>{lab.cost}</dd></>)}
                {lab.azureResources.length > 0 && (<><dt>Resources</dt><dd>{lab.azureResources.join(', ')}</dd></>)}
                {lab.prerequisites.length > 0 && (<><dt>Prerequisites</dt><dd>{lab.prerequisites.map((p) => content.byId.get(p)?.title ?? p).join(', ')}</dd></>)}
              </dl>
              <ProgressBar pct={pct} label={`${lab.title} checklist`} />
              <p className="small muted">{done}/{lab.checklist.length} checklist items</p>
            </article>
          )
        })}
        {planned.map(({ id, module }) => (
          <article key={id} className="card lab-card planned">
            <header>
              <span className="pill">Module {module.number}</span>
              <StatusBadge status="planned" />
            </header>
            <h3>{id.replace(/^lab-(\d+)-/, 'Lab $1: ').replace(/-/g, ' ')}</h3>
            <p className="small muted">Planned for {module.title}. See the module roadmap for its design.</p>
          </article>
        ))}
      </div>
    </div>
  )
}
