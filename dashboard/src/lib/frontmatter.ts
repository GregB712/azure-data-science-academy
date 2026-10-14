import yaml from 'js-yaml'

export type Frontmatter = Record<string, unknown>

const FM = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/

/** Split a Markdown file into YAML frontmatter and body. Files without frontmatter are allowed. */
export function parseFrontmatter(src: string): { data: Frontmatter; body: string } {
  const m = FM.exec(src)
  if (!m) return { data: {}, body: src }
  const loaded = yaml.load(m[1])
  const data = loaded && typeof loaded === 'object' && !Array.isArray(loaded) ? (loaded as Frontmatter) : {}
  return { data, body: src.slice(m[0].length) }
}

export function asString(v: unknown, fallback = ''): string {
  if (v === null || v === undefined) return fallback
  return String(v)
}

export function asStringArray(v: unknown): string[] {
  if (Array.isArray(v)) return v.map((x) => String(x))
  if (typeof v === 'string' && v.trim()) return [v]
  return []
}

export function asNumber(v: unknown): number | undefined {
  const n = typeof v === 'number' ? v : typeof v === 'string' ? Number(v) : NaN
  return Number.isFinite(n) ? n : undefined
}
