import { useMemo } from 'react'
import { Empty } from '../components/ui'
import { content } from '../content/load'
import { highlight, languageFor } from '../lib/hljs'
import { docHref, fileHref } from '../lib/links'

function Crumbs({ path }: { path: string }) {
  const parts = path.replace(/\/$/, '').split('/')
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumbs">
      <a href="#/">Home</a>
      {parts.map((p, i) => {
        const sub = parts.slice(0, i + 1).join('/')
        const last = i === parts.length - 1
        return (
          <span key={sub}>
            {' / '}
            {last && !path.endsWith('/') ? <span>{p}</span> : <a href={fileHref(`${sub}/`)}>{p}</a>}
          </span>
        )
      })}
    </nav>
  )
}

export default function FileView({ path }: { path: string }) {
  const text = content.files.get(path)
  const lang = languageFor(path.split('.').pop())
  const html = useMemo(() => (text === undefined ? '' : highlight(text, lang).html), [text, lang])

  if (path.endsWith('/') || text === undefined) {
    const dir = path.replace(/\/$/, '')
    const entries = [
      ...[...content.byPath.values()].filter((d) => d.path.startsWith(`${dir}/`)).map((d) => ({ path: d.path, href: docHref(d.route) })),
      ...[...content.files.keys()].filter((p) => p.startsWith(`${dir}/`)).map((p) => ({ path: p, href: fileHref(p) })),
    ].sort((a, b) => a.path.localeCompare(b.path))
    if (!entries.length) return <div className="page"><h1>Not found</h1><Empty>No file or folder <code>{path}</code> is loaded by the dashboard.</Empty></div>
    return (
      <div className="page">
        <Crumbs path={`${dir}/`} />
        <h1><code>{dir}/</code></h1>
        <p className="muted small">Files in this folder that the dashboard loads. On disk they live under the academy folder at the same path.</p>
        <ul className="file-list">
          {entries.map((e) => (
            <li key={e.path}><a href={e.href}><code>{e.path.slice(dir.length + 1)}</code></a></li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div className="page">
      <Crumbs path={path} />
      <h1><code>{path.split('/').pop()}</code></h1>
      <p className="muted small">
        Read-only view of <code>{path}</code> ({text.split('\n').length} lines). Run and edit it from the academy folder on disk.
      </p>
      <div className="code-block">
        <button
          type="button"
          className="copy-btn"
          onClick={(e) => {
            const btn = e.currentTarget
            navigator.clipboard?.writeText(text).then(() => {
              btn.textContent = 'Copied'
              setTimeout(() => (btn.textContent = 'Copy'), 1200)
            })
          }}
        >
          Copy
        </button>
        <pre className="file-view"><code className={`hljs language-${lang}`} dangerouslySetInnerHTML={{ __html: html }} /></pre>
      </div>
    </div>
  )
}
