import { useRef, useState } from 'react'
import { DocLink, ProgressBar, StatusBadge } from '../components/ui'
import { content } from '../content/load'
import { moduleDocs, progressFor, progressStore, STORAGE_KEY, useProgress } from '../lib/progress'

export default function ProgressPage() {
  const s = useProgress()
  const file = useRef<HTMLInputElement>(null)
  const [msg, setMsg] = useState('')
  const mode = progressStore.mode()
  const overall = progressFor(content.docs, s)
  const completed = Object.entries(s.completed).sort((a, b) => b[1].localeCompare(a[1]))

  const doExport = () => {
    const blob = new Blob([progressStore.exportJSON()], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `academy-progress-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(a.href)
    setMsg('Progress exported.')
  }
  const doImport = async (f: File | undefined) => {
    if (!f) return
    const ok = progressStore.importJSON(await f.text())
    setMsg(ok ? 'Progress imported.' : 'That file is not a progress export (expected JSON with "version": 1).')
    if (file.current) file.current.value = ''
  }

  return (
    <div className="page">
      <h1>Progress</h1>
      {mode === 'account' && (
        <p className="panel" role="status">Your progress is saved to your account and follows you across devices and browsers.</p>
      )}
      {mode === 'guest' && (
        <p className="warning" role="alert">You are browsing as a guest, so progress is not saved. Sign in to save it to your account. You can still export it below to keep a copy.</p>
      )}
      {mode === 'local' && !progressStore.isPersistent() && (
        <p className="warning" role="alert">This browser is blocking localStorage, so progress will be lost when you close the tab. Export it to keep it.</p>
      )}
      <section className="panel">
        <h2>Overall</h2>
        <ProgressBar pct={overall.pct} label="Overall progress" />
        <p className="small">{overall.done} of {overall.total} available lessons, labs and projects complete ({overall.pct}%). Planned items are not counted.</p>
      </section>

      <section className="panel">
        <h2>By module</h2>
        <table className="table">
          <thead><tr><th>Module</th><th>Status</th><th>Done</th><th style={{ width: '35%' }}>Progress</th></tr></thead>
          <tbody>
            {content.curriculum.modules.map((m) => {
              const p = progressFor(moduleDocs(content, m.number), s)
              return (
                <tr key={m.id}>
                  <td>{m.number}. {m.title}</td>
                  <td><StatusBadge status={m.status} /></td>
                  <td>{p.total ? `${p.done}/${p.total}` : '–'}</td>
                  <td>{p.total ? <ProgressBar pct={p.pct} label={`Module ${m.number}`} /> : <span className="small muted">nothing trackable yet</span>}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Completed</h2>
        {completed.length === 0 ? <p className="muted small">Nothing marked complete yet. Use “Mark complete” on a lesson, or tick a lab’s checklist.</p> : (
          <ul>
            {completed.map(([id, at]) => <li key={id}><DocLink id={id} /> <span className="small muted">{new Date(at).toLocaleDateString()}</span></li>)}
          </ul>
        )}
      </section>

      <section className="panel">
        <h2>Back up, move or reset</h2>
        <div className="button-row">
          <button type="button" onClick={doExport}>Export JSON</button>
          <button type="button" onClick={() => file.current?.click()}>Import JSON…</button>
          <input ref={file} type="file" accept="application/json,.json" hidden onChange={(e) => doImport(e.target.files?.[0])} />
          <button type="button" className="danger" onClick={() => { if (confirm('Reset all progress, checklists and history in this browser?')) { progressStore.reset(); setMsg('Progress reset.') } }}>Reset</button>
        </div>
        {msg && <p className="small" role="status">{msg}</p>}
        <h3>Where progress is stored, and its limits</h3>
        {mode === 'account' ? (
          <ul className="small">
            <li>Progress is saved to your account (in your Clerk user profile) and syncs across devices and browsers.</li>
            <li>Guest progress made before you signed in was merged into your account on first sign-in.</li>
            <li>Deleting your account from the profile menu also deletes this saved progress.</li>
            <li>Ticks in Markdown files on disk (<a href="#/doc/PROGRESS">PROGRESS.md</a>) are a separate, manual record that you can commit to Git.</li>
          </ul>
        ) : mode === 'guest' ? (
          <ul className="small">
            <li>You are not signed in, so progress is kept only in memory for this session and is not saved anywhere.</li>
            <li>Reloading or closing the tab clears it. Sign in to save progress, or Export it below to keep a copy.</li>
            <li>Ticks in Markdown files on disk (<a href="#/doc/PROGRESS">PROGRESS.md</a>) are a separate, manual record that you can commit to Git.</li>
          </ul>
        ) : (
          <ul className="small">
            <li>Progress lives in this browser’s <code>localStorage</code> under the key <code>{STORAGE_KEY}</code>. No server, account or cloud service is involved.</li>
            <li>It is per browser profile and per origin: <code>http://localhost:5173</code> (dev) and <code>http://localhost:4173</code> (preview) keep separate progress.</li>
            <li>Clearing site data, private windows, or another machine all start empty. Use Export/Import to move or back it up.</li>
            <li>Ticks in Markdown files on disk (<a href="#/doc/PROGRESS">PROGRESS.md</a>) are a separate, manual record that you can commit to Git.</li>
          </ul>
        )}
      </section>
    </div>
  )
}
