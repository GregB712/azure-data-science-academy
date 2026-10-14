import { describe, expect, it } from 'vitest'
import { parseFrontmatter } from '../lib/frontmatter'
import { checklistKey } from '../lib/checklist'
import { slugify, Slugger } from '../lib/slug'
import { resolveRelative } from '../lib/paths'
import { parseHash } from '../lib/router'
import { emptyState, parseState } from '../lib/progress'

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
