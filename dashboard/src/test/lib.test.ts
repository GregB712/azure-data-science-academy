import { describe, expect, it } from 'vitest'
import { parseFrontmatter } from '../lib/frontmatter'
import { checklistKey } from '../lib/checklist'
import { slugify, Slugger } from '../lib/slug'
import { resolveRelative } from '../lib/paths'
import { parseHash } from '../lib/router'
import { emptyState, parseState } from '../lib/progress'
import { deserializeProgress, isEmptyProgress, mergeProgress, serializeProgress } from '../auth/metadata'

describe('frontmatter', () => {
  it('parses YAML frontmatter and returns the body', () => {
    const { data, body } = parseFrontmatter('---\nid: x\ntags: [a, b]\nmodule: 3\n---\n# Title\n')
    expect(data).toMatchObject({ id: 'x', tags: ['a', 'b'], module: 3 })
    expect(body.trim()).toBe('# Title')
  })
  it('handles files without frontmatter', () => {
    expect(parseFrontmatter('# Hi').data).toEqual({})
  })
})

describe('slugs (GitHub-compatible)', () => {
  it('matches GitHub for common headings', () => {
    expect(slugify('1. Learning objectives')).toBe('1-learning-objectives')
    expect(slugify('OneLake vs ADLS Gen2')).toBe('onelake-vs-adls-gen2')
    expect(slugify('Lake → Warehouse / Lakehouse')).toBe('lake--warehouse--lakehouse')
    expect(slugify('Progress persistence and its limits')).toBe('progress-persistence-and-its-limits')
  })
  it('numbers duplicates like GitHub', () => {
    const s = new Slugger()
    expect([s.slug('Setup'), s.slug('Setup'), s.slug('Setup')]).toEqual(['setup', 'setup-1', 'setup-2'])
  })
})

describe('paths and routing', () => {
  it('resolves relative links', () => {
    expect(resolveRelative('docs/lakehouse/01-x.md', '../data-mesh/01-data-mesh.md')).toBe('docs/data-mesh/01-data-mesh.md')
    expect(resolveRelative('README.md', './labs/lab-01-azure-setup/README.md')).toBe('labs/lab-01-azure-setup/README.md')
  })
  it('parses hash routes', () => {
    const r = parseHash('#/doc/docs/lakehouse/01-x?s=medallion')
    expect(r.page).toBe('doc')
    expect(r.rest).toBe('docs/lakehouse/01-x')
    expect(r.params.get('s')).toBe('medallion')
    expect(parseHash('').page).toBe('')
  })
})

describe('checklist keys', () => {
  it('ignore link targets and punctuation so source and rendered text agree', () => {
    expect(checklistKey('[ ] Ran [the script](scripts/01.sh) — OK!')).toBe(checklistKey('Ran the script — OK!'))
  })
})

describe('progress state', () => {
  it('rejects bad or foreign JSON', () => {
    expect(parseState('nope')).toEqual(emptyState())
    expect(parseState('{"version":2}')).toEqual(emptyState())
    expect(parseState(null)).toEqual(emptyState())
  })
  it('keeps valid state', () => {
    const s = parseState('{"version":1,"completed":{"a":"2026-01-01"},"checklist":{},"recent":[]}')
    expect(s.completed.a).toBe('2026-01-01')
  })
})

describe('account progress metadata', () => {
  it('reads progress from a metadata object or JSON string, or empty', () => {
    const obj = { version: 1, completed: { a: '2026-01-01' }, checklist: {}, recent: [] }
    expect(deserializeProgress(obj).completed.a).toBe('2026-01-01')
    expect(deserializeProgress(JSON.stringify(obj)).completed.a).toBe('2026-01-01')
    expect(deserializeProgress(undefined)).toEqual(emptyState())
    expect(deserializeProgress(null)).toEqual(emptyState())
  })

  it('detects empty progress regardless of recent history', () => {
    expect(isEmptyProgress(emptyState())).toBe(true)
    expect(isEmptyProgress({ ...emptyState(), recent: [{ id: 'x', at: 'now' }] })).toBe(true)
    expect(isEmptyProgress({ ...emptyState(), completed: { a: 'd' } })).toBe(false)
    expect(isEmptyProgress({ ...emptyState(), checklist: { a: { k: true } } })).toBe(false)
  })

  it('merges local into account with local winning on conflict', () => {
    const local = { version: 1 as const, completed: { a: 'L', b: 'L' }, checklist: { d: { k1: true } }, recent: [{ id: 'a', at: 't2' }] }
    const account = { version: 1 as const, completed: { a: 'A', c: 'A' }, checklist: { d: { k2: true }, e: { k3: true } }, recent: [{ id: 'z', at: 't1' }] }
    const m = mergeProgress(local, account)
    expect(m.completed).toEqual({ a: 'L', b: 'L', c: 'A' })
    expect(m.checklist.d).toEqual({ k1: true, k2: true })
    expect(m.checklist.e).toEqual({ k3: true })
    expect(m.recent.map((r) => r.id)).toEqual(['a', 'z'])
  })

  it('drops recent history when the payload is near the size cap', () => {
    const recent = Array.from({ length: 8 }, (_, i) => ({ id: 'x'.repeat(2000) + i, at: '2026-01-01T00:00:00Z' }))
    const big = { version: 1 as const, completed: {}, checklist: {}, recent }
    expect(serializeProgress(big).recent).toEqual([])
    const small = { ...emptyState(), completed: { a: '2026-01-01' } }
    expect(serializeProgress(small)).toBe(small)
  })
})
