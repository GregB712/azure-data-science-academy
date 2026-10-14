import { useSyncExternalStore } from 'react'

export interface Route {
  page: string // first path segment: '', 'doc', 'catalog', ...
  rest: string // remainder after the page segment (e.g. a document route)
  params: URLSearchParams
}

export function parseHash(hash: string): Route {
  const h = hash.replace(/^#/, '') || '/'
  const [pathname, query = ''] = h.split('?', 2)
  const parts = pathname.replace(/^\//, '').split('/')
  const page = parts[0] ?? ''
  const rest = decodeURIComponent(parts.slice(1).join('/'))
  return { page, rest, params: new URLSearchParams(query) }
}

const subscribe = (cb: () => void) => {
  window.addEventListener('hashchange', cb)
  return () => window.removeEventListener('hashchange', cb)
}

export function useRoute(): Route {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash, () => '')
  return parseHash(hash)
}

export function navigate(to: string) {
  window.location.hash = to.startsWith('#') ? to.slice(1) : to
}
