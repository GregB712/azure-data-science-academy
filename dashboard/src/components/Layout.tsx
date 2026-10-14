import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { content } from '../content/load'
import { docHref } from '../lib/links'
import { navigate, useRoute } from '../lib/router'
import { setTheme, useTheme } from '../lib/theme'
import { CompletionMark } from './ui'

const NAV = [
  { href: '#/', label: 'Dashboard', page: '' },
  { href: '#/catalog', label: 'Lesson catalog', page: 'catalog' },
  { href: '#/labs', label: 'Lab tracker', page: 'labs' },
  { href: '#/architecture', label: 'Architecture explorer', page: 'architecture' },
  { href: '#/services', label: 'Service lookup', page: 'services' },
  { href: '#/glossary', label: 'Glossary', page: 'glossary' },
  { href: '#/search', label: 'Search', page: 'search' },
  { href: '#/progress', label: 'My progress', page: 'progress' },
]

const REFERENCE_IDS = [
  'course-map', 'architecture-decision-guide', 'service-catalog', 'glossary',
  'command-cheatsheet', 'official-docs', 'extending-the-academy', 'progress',
]

function Sidebar({ onNavigate }: { onNavigate: () => void }) {
  const route = useRoute()
  const currentRoute = route.page === 'doc' ? route.rest : ''
  const [open, setOpen] = useState<Record<number, boolean>>({ 1: true, 3: true })

  return (
    <nav className="sidebar" aria-label="Course navigation" onClick={(e) => (e.target as HTMLElement).closest('a') && onNavigate()}>
      <a className="brand" href="#/">
        <span className="brand-mark" aria-hidden>A</span>
        <span>
          <strong>Azure Data Science Academy</strong>
          <small>v{content.curriculum.version}</small>
        </span>
      </a>
      <ul className="nav-list">
        {NAV.map((n) => (
          <li key={n.href}>
            <a href={n.href} className={route.page === n.page ? 'active' : ''}>
              {n.label}
            </a>
          </li>
        ))}
      </ul>

      <h2 className="nav-heading">Modules</h2>
      <ul className="nav-tree">
        {content.curriculum.modules.map((m) => {
          const docs = content.docs
            .filter((d) => d.module === m.number)
            .sort((a, b) => (a.type === 'module-overview' ? -1 : 0) - (b.type === 'module-overview' ? -1 : 0) || a.order - b.order)
          const expanded = open[m.number] ?? docs.some((d) => d.route === currentRoute)
          return (
            <li key={m.id}>
              <button
                type="button"
                className="tree-toggle"
                aria-expanded={expanded}
                onClick={() => setOpen({ ...open, [m.number]: !expanded })}
              >
                <span className="chev" aria-hidden>{expanded ? '▾' : '▸'}</span>
                <span className="mod-num">{m.number}</span>
                <span className="mod-title">{m.title}</span>
                {m.status !== 'available' && <span className="mod-status">{m.status}</span>}
              </button>
              {expanded && (
                <ul>
                  {docs.length === 0 && <li className="muted small">Content planned</li>}
                  {docs.map((d) => (
                    <li key={d.id}>
                      <a href={docHref(d.route)} className={d.route === currentRoute ? 'active' : ''}>
                        {d.type === 'lab' ? '🧪 ' : d.type === 'module-overview' ? '🗺 ' : d.type === 'project' ? '🏁 ' : ''}
                        {d.title.replace(/^Lab \d+: /, 'Lab: ')}
                        <CompletionMark doc={d} />
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          )
        })}
      </ul>

      <h2 className="nav-heading">Reference</h2>
      <ul className="nav-list compact">
        {REFERENCE_IDS.map((id) => content.byId.get(id)).filter(Boolean).map((d) => (
          <li key={d!.id}>
            <a href={docHref(d!.route)} className={d!.route === currentRoute ? 'active' : ''}>
              {d!.title}
            </a>
          </li>
        ))}
        <li>
          <a href={docHref('README')}>About this academy (README)</a>
        </li>
      </ul>
    </nav>
  )
}

export default function Layout({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const route = useRoute()
  const theme = useTheme()
  const [q, setQ] = useState('')

  useEffect(() => setMenuOpen(false), [route.page, route.rest])

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (q.trim()) navigate(`#/search?q=${encodeURIComponent(q.trim())}`)
  }

  return (
    <div className={`app ${menuOpen ? 'menu-open' : ''}`}>
      <a className="skip-link" href="#main" onClick={(e) => { e.preventDefault(); document.getElementById('main')?.focus() }}>
        Skip to content
      </a>
      <Sidebar onNavigate={() => setMenuOpen(false)} />
      <div className="backdrop" onClick={() => setMenuOpen(false)} aria-hidden />
      <div className="main-col">
        <header className="topbar">
          <button type="button" className="menu-btn" aria-label="Open navigation" onClick={() => setMenuOpen(!menuOpen)}>
            ☰
          </button>
          <form className="top-search" role="search" onSubmit={submit}>
            <input
              type="search"
              placeholder="Search lessons, labs, services, commands…"
              aria-label="Search the academy"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </form>
          <button
            type="button"
            className="icon-btn"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            title="Toggle theme"
          >
            {theme === 'dark' ? '☀' : '☾'}
          </button>
        </header>
        <main id="main" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  )
}
