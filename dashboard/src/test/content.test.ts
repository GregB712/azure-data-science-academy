import { describe, expect, it } from 'vitest'
import { parseGlossary, parseServiceCatalog } from '../lib/catalog'
import { checklistKey } from '../lib/checklist'
import { resolveLink } from '../lib/links'
import { renderMarkdown } from '../lib/markdown'
import { slugify } from '../lib/slug'
import { buildSearchIndex } from '../lib/search'
import { content, curriculum } from './fixtures'

const linksIn = (body: string) => {
  const out: string[] = []
  let fence = false
  for (const line of body.split('\n')) {
    if (/^\s*```/.test(line)) fence = !fence
    if (fence) continue
    for (const m of line.replace(/`[^`]*`/g, '').matchAll(/\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g)) out.push(m[1])
  }
  return out
}

describe('content model built from the real dossier', () => {
  it('loads the core documents', () => {
    for (const id of ['m1-azure-fundamentals', 'm3-data-mesh', 'm3-lakehouse-medallion', 'lab-01-azure-setup', 'architecture-decision-guide', 'service-catalog', 'glossary', 'course-map', 'README']) {
      expect(content.byId.has(id), id).toBe(true)
    }
  })
  it('has unique ids', () => {
    const ids = content.docs.map((d) => d.id)
    expect(new Set(ids).size).toBe(ids.length)
  })
  it('curriculum recommendedPath and module labs refer to real ids (labs may be planned)', () => {
    for (const id of curriculum.recommendedPath ?? []) expect(content.byId.has(id), id).toBe(true)
    const lab01 = curriculum.modules.find((m) => m.id === 'm1')!
    expect(lab01.labs.every((id) => content.byId.has(id))).toBe(true)
  })
  it('prerequisites and related ids exist', () => {
    for (const d of content.docs) {
      for (const id of [...d.prerequisites, ...d.related]) expect(content.byId.has(id), `${d.path} -> ${id}`).toBe(true)
    }
  })
  it('lab 01 exposes its 10-item completion checklist', () => {
    const lab = content.byId.get('lab-01-azure-setup')!
    expect(lab.checklist).toHaveLength(10)
    expect(new Set(lab.checklist.map((i) => i.key)).size).toBe(10)
  })
  it('every relative link and anchor resolves', () => {
    const problems: string[] = []
    for (const d of content.docs) {
      for (const href of linksIn(d.body)) {
        if (/^[a-z]+:/i.test(href)) continue
        const r = resolveLink(href, d.path, content)
        if (r.missing) problems.push(`${d.path}: ${href}`)
        const anchor = href.includes('#') ? href.split('#')[1] : ''
        if (anchor && !r.missing) {
          const target = href.startsWith('#') ? d : content.byPath.get(r.href.replace(/^#\/doc\//, '').split('?')[0] + '.md')
          if (target && !target.headings.some((h) => h.slug === anchor)) problems.push(`${d.path}: ${href} (anchor)`)
        }
      }
    }
    expect(problems).toEqual([])
  })
})

describe('reference parsers', () => {
  const services = parseServiceCatalog(content.byId.get('service-catalog')!.body)
  it('parses the service catalog', () => {
    expect(services.length).toBeGreaterThanOrEqual(25)
    for (const s of services) {
      expect(s.fields['Kind'], s.name).toBeTruthy()
      expect(s.fields['What it is'], s.name).toBeTruthy()
    }
  })
  it('every service named by an architecture view exists in the catalog', () => {
    const slugs = new Set(services.map((s) => s.slug))
    for (const d of content.docs.filter((x) => x.type === 'architecture')) {
      for (const name of d.services) expect(slugs.has(slugify(name)), `${d.path}: ${name}`).toBe(true)
      for (const id of d.lessons) expect(content.byId.has(id), `${d.path}: ${id}`).toBe(true)
    }
  })
  it('parses the glossary with a kind and definition per term', () => {
    const terms = parseGlossary(content.byId.get('glossary')!.body)
    expect(terms.length).toBeGreaterThanOrEqual(50)
    for (const t of terms) {
      expect(t.kind, t.term).toBeTruthy()
      expect(t.definition, t.term).toBeTruthy()
    }
  })
})

describe('rendering and search', () => {
  it('renders lessons with heading ids, rewritten links and mermaid placeholders', () => {
    const d = content.byId.get('m3-data-mesh')!
    const html = renderMarkdown(d.body, d.path, content)
    expect(html).toContain('id="1-lesson-overview-and-learning-objectives"')
    expect(html).toContain('class="mermaid-block"')
    expect(html).toContain('href="#/doc/')
    expect(html).not.toContain('href="#/missing')
  })
  it('renders checklist items whose text maps back to the stored keys', () => {
    const lab = content.byId.get('lab-01-azure-setup')!
    const html = renderMarkdown(lab.body, lab.path, content)
    const items = [...html.matchAll(/<li><input[^>]*type="checkbox"[^>]*>([\s\S]*?)<\/li>/g)].map((m) => checklistKey(m[1].replace(/<[^>]+>/g, '')))
    for (const i of lab.checklist) expect(items, i.text).toContain(i.key)
  })
  it('finds sections by full text', () => {
    const idx = buildSearchIndex(content)
    expect(idx.search('medallion').length).toBeGreaterThan(0)
    expect(idx.search('DefaultAzureCredential').length).toBeGreaterThan(0)
    expect(idx.search('data contract').some((r) => r.docId === 'm3-data-mesh')).toBe(true)
  })
})
