/** POSIX-style path helpers for repo-relative paths ("docs/lakehouse/x.md"). */

export function dirname(p: string): string {
  const i = p.lastIndexOf('/')
  return i < 0 ? '' : p.slice(0, i)
}

export function normalize(p: string): string {
  const trailing = p.endsWith('/')
  const out: string[] = []
  for (const seg of p.split('/')) {
    if (!seg || seg === '.') continue
    if (seg === '..') out.pop()
    else out.push(seg)
  }
  const joined = out.join('/')
  return trailing && joined ? `${joined}/` : joined
}

/** Resolve `rel` (as written in a Markdown link) relative to the file at `fromFile`. */
export function resolveRelative(fromFile: string, rel: string): string {
  const base = dirname(fromFile)
  return normalize(base ? `${base}/${rel}` : rel)
}

export function stripMd(path: string): string {
  return path.replace(/\.md$/i, '')
}
