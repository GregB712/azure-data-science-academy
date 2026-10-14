import type { Content } from '../content/model'
import { resolveRelative, stripMd } from './paths'

export interface ResolvedLink {
  href: string
  external: boolean
  missing: boolean
}

export function docHref(route: string, section?: string): string {
  return `#/doc/${route}${section ? `?s=${encodeURIComponent(section)}` : ''}`
}

export function fileHref(path: string): string {
  return `#/file/${path}`
}

/**
 * Turn a link written in a Markdown file into a dashboard route. Relative links
 * keep working on GitHub/VS Code; here they become hash routes to the rendered
 * document, the code viewer, or a folder listing.
 */
export function resolveLink(href: string, fromPath: string, content: Content): ResolvedLink {
  if (/^[a-z][a-z0-9+.-]*:/i.test(href)) return { href, external: true, missing: false }
  if (href.startsWith('#/')) return { href, external: false, missing: false }
  if (href.startsWith('#')) return { href: docHref(stripMd(fromPath), href.slice(1)), external: false, missing: false }

  const [pathPart, anchor] = href.split('#', 2)
  const target = resolveRelative(fromPath, decodeURI(pathPart))
  const doc = content.byPath.get(target)
  if (doc) return { href: docHref(doc.route, anchor), external: false, missing: false }
  if (content.files.has(target)) return { href: fileHref(target), external: false, missing: false }
  const dir = target.replace(/\/$/, '')
  const isDir = [...content.files.keys(), ...content.byPath.keys()].some((p) => p.startsWith(`${dir}/`))
  if (isDir) return { href: fileHref(`${dir}/`), external: false, missing: false }
  return { href: `#/missing?p=${encodeURIComponent(target)}`, external: false, missing: true }
}
