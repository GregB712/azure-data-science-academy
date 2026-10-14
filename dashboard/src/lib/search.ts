import MiniSearch from 'minisearch'
import type { Content, Doc } from '../content/model'
import { markdownToPlain, Slugger, headingText } from './slug'

export interface SectionRecord {
  id: string
  docId: string
  route: string
  title: string
  heading: string
  slug: string
  type: string
  text: string
  tags: string
}

/** Split a document into sections at h2/h3 so search results can link straight to a section. */
export function sectionsOf(doc: Doc): SectionRecord[] {
  const out: SectionRecord[] = []
  const slugger = new Slugger()
  let heading = doc.title
  let slug = ''
  let buf: string[] = []
  let fence = false
  const flush = () => {
    const text = markdownToPlain(buf.join('\n'))
    if (text || slug === '') {
      out.push({
        id: `${doc.id}#${slug || 'top'}#${out.length}`,
        docId: doc.id,
        route: doc.route,
        title: doc.title,
        heading,
        slug,
        type: doc.type,
        text: slug === '' ? `${doc.summary} ${text}` : text,
        tags: doc.tags.join(' '),
      })
    }
    buf = []
  }
  for (const line of doc.body.split(/\r?\n/)) {
    if (/^\s*```/.test(line)) fence = !fence
    const m = !fence && /^(#{1,6})\s+(.+?)\s*#*\s*$/.exec(line)
    if (m) {
      const text = headingText(m[2])
      const s = slugger.slug(text) // keep slug numbering identical to the renderer
      if (m[1].length <= 3) {
        flush()
        heading = m[1].length === 1 ? doc.title : text
        slug = m[1].length === 1 ? '' : s
        continue
      }
    }
    buf.push(line)
  }
  flush()
  return out
}

export function buildSearchIndex(content: Content): MiniSearch<SectionRecord> {
  const index = new MiniSearch<SectionRecord>({
    fields: ['title', 'heading', 'text', 'tags'],
    storeFields: ['docId', 'route', 'title', 'heading', 'slug', 'type', 'text'],
    searchOptions: { boost: { title: 3, heading: 2, tags: 2 }, prefix: true, fuzzy: 0.15, combineWith: 'AND' },
  })
  index.addAll(content.docs.flatMap(sectionsOf))
  return index
}

export function snippet(text: string, query: string, radius = 90): string {
  const terms = query.toLowerCase().split(/\s+/).filter((t) => t.length > 1)
  const lower = text.toLowerCase()
  let pos = -1
  for (const t of terms) {
    pos = lower.indexOf(t)
    if (pos >= 0) break
  }
  if (pos < 0) return text.slice(0, radius * 2) + (text.length > radius * 2 ? '…' : '')
  const start = Math.max(0, pos - radius)
  const end = Math.min(text.length, pos + radius)
  return (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '')
}
