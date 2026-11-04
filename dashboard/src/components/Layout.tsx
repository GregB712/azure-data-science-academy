import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { AuthControls, GuestBanner } from '../auth/clerk'
import { content } from '../content/load'
import { docHref } from '../lib/links'
import { navigate, useRoute } from '../lib/router'
import { setTheme, useTheme } from '../lib/theme'
import { CompletionMark, Icon } from './ui'
import { useDrawerGesture } from './drawerGesture'

const NAV = [
  { href: '#/', label: 'Dashboard', page: '', icon: 'home' },
  { href: '#/catalog', label: 'Lesson catalog', page: 'catalog', icon: 'books' },
  { href: '#/labs', label: 'Lab tracker', page: 'labs', icon: 'flask' },
  { href: '#/architecture', label: 'Architecture explorer', page: 'architecture', icon: 'layers' },
  { href: '#/services', label: 'Service lookup', page: 'services', icon: 'cloud' },
  { href: '#/glossary', label: 'Glossary', page: 'glossary', icon: 'text' },
  { href: '#/search', label: 'Search', page: 'search', icon: 'search' },
  { href: '#/progress', label: 'My progress', page: 'progress', icon: 'chart' },
]

const DOC_ICON: Record<string, string> = { lab: 'flask', 'module-overview': 'map', project: 'flag' }

const REFERENCE_IDS = [
  'course-map', 'architecture-decision-guide', 'service-catalog', 'glossary',
  'command-cheatsheet', 'official-docs', 'extending-the-academy', 'progress',
]

function Sidebar({ onNavigate, open: drawerOpen }: { onNavigate: () => void; open: boolean }) {
  const route = useRoute()
  const ref = useRef<HTMLElement>(null)
  useDrawerGesture(ref, drawerOpen, onNavigate)
  const currentRoute = route.page === 'doc' ? route.rest : ''
  const [open, setOpen] = useState<Record<number, boolean>>({ 1: true, 3: true })

  return (
    <nav ref={ref} className="sidebar" aria-label="Course navigation" onClick={(e) => (e.target as HTMLElement).closest('a') && onNavigate()}>
      <a className="brand" href="#/">
        <span className="brand-mark" aria-hidden>
          <svg viewBox="0 0 64 64"><path d="M18 46 30 16h6l12 30h-7l-3-8H28l-3 8zm12-14h6l-3-9z" fill="currentColor" /></svg>
        </span>
        <span className="brand-text">
          <strong>Data Science Academy</strong>
          <small>Azure · v{content.curriculum.version}</small>
        </span>
      </a>
      <ul className="nav-list">
        {NAV.map((n) => (
          <li key={n.href}>
            <a href={n.href} className={route.page === n.page ? 'active' : ''} aria-current={route.page === n.page ? 'page' : undefined}>
              <Icon name={n.icon} />
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
                <Icon name="chevron" className="chev" />
                <span className="mod-num">{m.number}</span>
                <span className="mod-title">{m.title}</span>
                {m.status !== 'available' && <span className="mod-status">{m.status}</span>}
              </button>
              {expanded && (
                <ul>
                  {docs.length === 0 && <li className="muted small">Content planned</li>}
                  {docs.map((d) => (
                    <li key={d.id}>
                      <a href={docHref(d.route)} className={d.route === currentRoute ? 'active' : ''} aria-current={d.route === currentRoute ? 'page' : undefined}>
                        <Icon name={DOC_ICON[d.type] ?? 'doc'} />
                        <span className="nav-label">{d.title.replace(/^Lab \d+: /, 'Lab: ')}</span>
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
            <a href={docHref(d!.route)} className={d!.route === currentRoute ? 'active' : ''} aria-current={d!.route === currentRoute ? 'page' : undefined}>
              <span className="nav-label">{d!.title}</span>
            </a>
          </li>
        ))}
        <li>
          <a href={docHref('README')}><span className="nav-label">About this academy</span></a>
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
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => setMenuOpen(false), [route.page, route.rest])

  // The top bar's hairline only appears once content actually slides under it.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Escape always offers a way out of the drawer.
  useEffect(() => {
    if (!menuOpen) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setMenuOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [menuOpen])

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (q.trim()) navigate(`#/search?q=${encodeURIComponent(q.trim())}`)
  }

  return (
    <div className={`app ${menuOpen ? 'menu-open' : ''}`}>
      <a className="skip-link" href="#main" onClick={(e) => { e.preventDefault(); document.getElementById('main')?.focus() }}>
        Skip to content
      </a>
      <Sidebar open={menuOpen} onNavigate={() => setMenuOpen(false)} />
      <div className="backdrop" onClick={() => setMenuOpen(false)} aria-hidden />
      <div className="main-col">
        <header className={`topbar ${scrolled ? 'scrolled' : ''}`}>
          <button type="button" className="menu-btn" aria-label="Open navigation" aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}>
            <Icon name="menu" />
          </button>
          <form className="top-search" role="search" onSubmit={submit}>
            <Icon name="search" className="search-glyph" />
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
            <Icon name={theme === 'dark' ? 'sun' : 'moon'} />
          </button>
          <AuthControls />
        </header>
        <main id="main" tabIndex={-1}>
          <GuestBanner />
          {children}
        </main>
      </div>
    </div>
  )
}
