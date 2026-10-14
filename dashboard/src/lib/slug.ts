import { marked } from 'marked'

/** GitHub-compatible heading slug, so anchors work on GitHub, in VS Code and in the dashboard. */
export function slugify(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s_-]/gu, '')
    .replace(/\s/g, '-')
}

export class Slugger {
  private seen = new Map<string, number>()

  slug(text: string): string {
    const base = slugify(text)
    const n = this.seen.get(base)
    if (n === undefined) {
      this.seen.set(base, 0)
      return base
    }
    this.seen.set(base, n + 1)
    return `${base}-${n + 1}`
  }
}

const ENTITIES: Record<string, string> = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'" }

export function htmlToText(html: string): string {
  return html.replace(/<[^>]+>/g, '').replace(/&(amp|lt|gt|quot|#39);/g, (m) => ENTITIES[m] ?? m)
}

/** Plain text of a heading's inline Markdown, as GitHub computes it for slugs. */
export function headingText(rawInline: string): string {
  return htmlToText(marked.parseInline(rawInline, { async: false }) as string).trim()
}

/** Strip Markdown syntax for search indexing and snippets. */
export function markdownToPlain(md: string): string {
  return md
    .replace(/```[a-z]*\n?/gi, '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/<\/?(details|summary)>/g, '')
    .replace(/[`*>#|]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}
