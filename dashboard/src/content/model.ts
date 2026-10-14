import { asNumber, asString, asStringArray, parseFrontmatter } from '../lib/frontmatter'
import { extractCompletionChecklist, type ChecklistItem } from '../lib/checklist'
import { headingText, Slugger } from '../lib/slug'
import { stripMd } from '../lib/paths'

export type DocType = 'lesson' | 'lab' | 'reference' | 'module-overview' | 'project' | 'architecture' | 'page'

export interface Heading {
  depth: number
  text: string
  slug: string
}

export interface Doc {
  id: string
  path: string // repo-relative, with .md
  route: string // path without .md, used in URLs
  title: string
  type: DocType
  module?: number
  order: number
  status: string
  summary: string
  tags: string[]
  prerequisites: string[]
  related: string[]
  duration?: string
  level?: string
  cost?: string
  azureResources: string[]
  services: string[]
  lessons: string[]
  body: string
  headings: Heading[]
  checklist: ChecklistItem[]
}

export interface Module {
  id: string
  number: number
  title: string
  description: string
  estimatedHours: number
  status: string
  docsPath: string
  labs: string[]
}

export interface Curriculum {
  title: string
  tagline: string
  version: string
  objectives: string[]
  sequence: string
  recommendedPath?: string[]
  modules: Module[]
}

export interface Content {
  curriculum: Curriculum
  docs: Doc[]
  byId: Map<string, Doc>
  byPath: Map<string, Doc>
  files: Map<string, string> // other raw files (code, scripts, templates)
  sequence: Doc[] // learning order for previous/next navigation
}

const KNOWN_TYPES: DocType[] = ['lesson', 'lab', 'reference', 'module-overview', 'project', 'architecture']
const TYPE_RANK: Record<string, number> = { 'module-overview': 0, lesson: 1, lab: 2, project: 3 }

export function extractHeadings(body: string): Heading[] {
  const slugger = new Slugger()
  const out: Heading[] = []
  let inFence = false
  for (const line of body.split(/\r?\n/)) {
    if (/^\s*```/.test(line)) inFence = !inFence
    if (inFence) continue
    const m = /^(#{1,6})\s+(.+?)\s*#*\s*$/.exec(line)
    if (!m) continue
    const text = headingText(m[2])
    out.push({ depth: m[1].length, text, slug: slugger.slug(text) })
  }
  return out
}

export function buildDoc(path: string, src: string): Doc {
  const { data, body } = parseFrontmatter(src)
  const headings = extractHeadings(body)
  const h1 = headings.find((h) => h.depth === 1)
  const fileName = path.split('/').pop() ?? path
  const rawType = asString(data.type, 'page')
  const type = (KNOWN_TYPES as string[]).includes(rawType) ? (rawType as DocType) : 'page'
  return {
    id: asString(data.id, stripMd(path)),
    path,
    route: stripMd(path),
    title: asString(data.title, h1?.text ?? fileName),
    type,
    module: asNumber(data.module),
    order: asNumber(data.order) ?? 99,
    status: asString(data.status, 'available'),
    summary: asString(data.summary),
    tags: asStringArray(data.tags),
    prerequisites: asStringArray(data.prerequisites),
    related: asStringArray(data.related),
    duration: data.duration !== undefined ? asString(data.duration) : undefined,
    level: data.level !== undefined ? asString(data.level) : undefined,
    cost: data.cost !== undefined ? asString(data.cost) : undefined,
    azureResources: asStringArray(data.azure_resources),
    services: asStringArray(data.services),
    lessons: asStringArray(data.lessons),
    body,
    headings,
    checklist: type === 'lab' ? extractCompletionChecklist(body) : [],
  }
}

function learningOrder(a: Doc, b: Doc): number {
  return (
    (a.module ?? 99) - (b.module ?? 99) ||
    (TYPE_RANK[a.type] ?? 9) - (TYPE_RANK[b.type] ?? 9) ||
    a.order - b.order ||
    a.title.localeCompare(b.title)
  )
}

export function buildContent(
  markdown: Record<string, string>,
  rawFiles: Record<string, string>,
  curriculum: Curriculum,
): Content {
  const docs = Object.entries(markdown)
    .map(([path, src]) => buildDoc(path, src))
    .sort((a, b) => a.path.localeCompare(b.path))
  const byId = new Map(docs.map((d) => [d.id, d]))
  const byPath = new Map(docs.map((d) => [d.path, d]))
  const files = new Map(Object.entries(rawFiles))

  // Recommended path first (curriculum.json), then every other learning item in module order.
  const learning = docs.filter((d) => d.type in TYPE_RANK).sort(learningOrder)
  const preferred = (curriculum.recommendedPath ?? []).map((id) => byId.get(id)).filter((d): d is Doc => !!d)
  const seen = new Set(preferred.map((d) => d.id))
  const sequence = [...preferred, ...learning.filter((d) => !seen.has(d.id))]

  return { curriculum, docs, byId, byPath, files, sequence }
}

/** Strip the "../../../" (or similar) prefix Vite glob keys carry, giving repo-relative paths. */
export function toRepoPath(globKey: string): string {
  return globKey.replace(/^(\.\.\/)+/, '')
}
