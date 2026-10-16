/** Build the same Content object the app builds, but from the files on disk (node fs instead of import.meta.glob). */
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { buildContent, type Curriculum } from '../content/model'

export const ROOT = join(__dirname, '..', '..', '..')
const SKIP = new Set(['node_modules', 'dist', '.venv', '__pycache__', 'dashboard', '.git', 'data'])

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    if (SKIP.has(name) || name.startsWith('.lab-state')) continue
    const p = join(dir, name)
    if (statSync(p).isDirectory()) walk(p, out)
    else out.push(relative(ROOT, p).split('\\').join('/'))
  }
  return out
}

const all = walk(ROOT)
const isMd = (p: string) =>
  p.endsWith('.md') && !p.startsWith('docs/_templates/') && (!p.includes('/') || /^(docs|labs|projects|diagrams|references)\//.test(p))
const isRaw = (p: string) =>
  (/^[^/]+\.json$/.test(p) || p === 'LICENSE' || /^code\/.*\.(py|yaml|yml|txt|ini)$/.test(p) || /^labs\/.*\.(sh|py|bicep|txt|example)$/.test(p) || /^docs\/_templates\/[^/]+\.md$/.test(p))

const read = (p: string) => readFileSync(join(ROOT, p), 'utf8')
export const markdownFiles = Object.fromEntries(all.filter(isMd).map((p) => [p, read(p)]))
export const rawFiles = Object.fromEntries(all.filter(isRaw).map((p) => [p, read(p)]))
export const curriculum = JSON.parse(read('curriculum.json')) as Curriculum
export const content = buildContent(markdownFiles, rawFiles, curriculum)
