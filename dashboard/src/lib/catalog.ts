/** Parse SERVICE_CATALOG.md and GLOSSARY.md into structured entries for the explorers. */
import { slugify } from './slug'

export interface ServiceEntry {
  name: string
  slug: string
  group: string // the "## " section it appears in
  fields: Record<string, string> // Category, Kind, What it is, Role in the architecture, ...
}

export interface GlossaryEntry {
  term: string
  slug: string
  kind: string
  definition: string // Markdown
}

const FIELD = /^\s*-\s+\*\*(.+?):\*\*\s*(.*)$/

function stripCode(body: string): string[] {
  const out: string[] = []
  let fence = false
  for (const line of body.split(/\r?\n/)) {
    if (/^\s*```/.test(line)) {
      fence = !fence
      continue
    }
    if (!fence) out.push(line)
  }
  return out
}

export function parseServiceCatalog(body: string): ServiceEntry[] {
  const entries: ServiceEntry[] = []
  let group = ''
  let current: ServiceEntry | null = null
  for (const line of stripCode(body)) {
    const h2 = /^##\s+(.+)$/.exec(line)
    const h3 = /^###\s+(.+)$/.exec(line)
    if (h2) {
      group = h2[1].trim()
      current = null
    } else if (h3) {
      const name = h3[1].trim()
      current = { name, slug: slugify(name), group, fields: {} }
      entries.push(current)
    } else if (current) {
      const f = FIELD.exec(line)
      if (f) current.fields[f[1].trim()] = f[2].trim()
    }
  }
  return entries
}

export function parseGlossary(body: string): GlossaryEntry[] {
  const entries: GlossaryEntry[] = []
  let current: GlossaryEntry | null = null
  for (const line of stripCode(body)) {
    const h3 = /^###\s+(.+)$/.exec(line)
    if (h3) {
      const term = h3[1].trim()
      current = { term, slug: slugify(term), kind: '', definition: '' }
      entries.push(current)
      continue
    }
    if (!current) continue
    const f = FIELD.exec(line)
    if (f && f[1].trim().toLowerCase() === 'kind') {
      current.kind = f[2].trim()
    } else if (/^\s*-\s+/.test(line)) {
      current.definition = [current.definition, line.replace(/^\s*-\s+/, '')].filter(Boolean).join(' ')
    }
  }
  return entries
}

/** "Azure service (tooling)" -> "Azure service"; used for filter chips. */
export function kindGroup(kind: string): string {
  return kind.replace(/\s*\(.*\)\s*$/, '').trim() || 'Other'
}
