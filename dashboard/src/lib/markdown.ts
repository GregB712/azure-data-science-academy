import { Marked, type Tokens } from 'marked'
import type { Content } from '../content/model'
import { highlight } from './hljs'
import { docHref, resolveLink } from './links'
import { stripMd } from './paths'
import { htmlToText, Slugger } from './slug'

const escapeAttr = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

const cache = new Map<string, string>()

function hash(s: string): number {
  let h = 5381
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0
  return h >>> 0
}

/**
 * Render a dossier Markdown file to HTML.
 * - Headings get GitHub-compatible ids and a self-link.
 * - Relative links are rewritten to dashboard routes (see links.ts).
 * - ```mermaid blocks become placeholders that MarkdownView renders lazily.
 * - Code is syntax-highlighted.
 * Content is the course's own trusted Markdown, so inline HTML (e.g. <details>) is kept.
 */
export function renderMarkdown(body: string, path: string, content: Content, inline = false): string {
  const cacheKey = `${inline ? 'i' : 'b'}:${path}:${body.length}:${hash(body)}`
  const hit = cache.get(cacheKey)
  if (hit !== undefined) return hit

  const slugger = new Slugger()
  const route = stripMd(path)
  const md = new Marked({ gfm: true, async: false })
  md.use({
    renderer: {
      heading(this: { parser: { parseInline: (t: Tokens.Generic[]) => string } }, token: Tokens.Heading) {
        const html = this.parser.parseInline(token.tokens)
        const slug = slugger.slug(htmlToText(html).trim())
        return `<h${token.depth} id="${slug}"><a class="anchor" href="${docHref(route, slug)}" aria-label="Link to this section">#</a>${html}</h${token.depth}>\n`
      },
      link(this: { parser: { parseInline: (t: Tokens.Generic[]) => string } }, token: Tokens.Link) {
        const text = this.parser.parseInline(token.tokens)
        const r = resolveLink(token.href, path, content)
        const title = token.title ? ` title="${escapeAttr(token.title)}"` : ''
        if (r.external) return `<a href="${escapeAttr(r.href)}"${title} target="_blank" rel="noopener noreferrer" class="external">${text}</a>`
        const cls = r.missing ? ' class="missing-link" title="Not available in the dashboard"' : ''
        return `<a href="${escapeAttr(r.href)}"${title}${cls}>${text}</a>`
      },
      code(token: Tokens.Code) {
        const lang = (token.lang ?? '').trim().split(/\s+/)[0]
        if (lang === 'mermaid') {
          return `<div class="mermaid-block" data-src="${escapeAttr(token.text)}"><div class="mermaid-loading">Rendering diagram…</div></div>\n`
        }
        const { html, language } = highlight(token.text, lang)
        return `<div class="code-block"><button type="button" class="copy-btn" aria-label="Copy code">Copy</button><pre><code class="hljs language-${language}">${html}</code></pre></div>\n`
      },
    },
  })
  const out = (inline ? md.parseInline(body) : md.parse(body)) as string
  cache.set(cacheKey, out)
  return out
}
