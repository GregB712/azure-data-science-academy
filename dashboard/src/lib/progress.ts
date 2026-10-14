/**
 * Learning progress, persisted in the browser's localStorage.
 * Limits (documented in the README): per browser profile and per origin
 * (http://localhost:5173 and :4173 are different origins), cleared with site
 * data, not synced across machines. Export/import JSON covers backups.
 */
import { useSyncExternalStore } from 'react'
import type { Content, Doc } from '../content/model'

export const STORAGE_KEY = 'adsa.progress.v1'

export interface ProgressState {
  version: 1
  completed: Record<string, string> // docId -> ISO date
  checklist: Record<string, Record<string, boolean>> // docId -> item key -> done
  recent: { id: string; at: string }[]
}

export const emptyState = (): ProgressState => ({ version: 1, completed: {}, checklist: {}, recent: [] })

export function parseState(text: string | null): ProgressState {
  if (!text) return emptyState()
  try {
    const v = JSON.parse(text)
    if (!v || v.version !== 1 || typeof v.completed !== 'object' || typeof v.checklist !== 'object') return emptyState()
    return { version: 1, completed: v.completed ?? {}, checklist: v.checklist ?? {}, recent: Array.isArray(v.recent) ? v.recent : [] }
  } catch {
    return emptyState()
  }
}

function read(): ProgressState {
  try {
    return parseState(window.localStorage.getItem(STORAGE_KEY))
  } catch {
    return emptyState() // storage blocked (private mode, policy): progress lives in memory only
  }
}

let state: ProgressState = typeof window === 'undefined' ? emptyState() : read()
let persistent = true
const listeners = new Set<() => void>()

function commit(next: ProgressState) {
  state = next
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    persistent = true
  } catch {
    persistent = false
  }
  listeners.forEach((l) => l())
}

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key === STORAGE_KEY) {
      state = parseState(e.newValue)
      listeners.forEach((l) => l())
    }
  })
}

export const progressStore = {
  get: () => state,
  isPersistent: () => persistent,
  subscribe(l: () => void) {
    listeners.add(l)
    return () => listeners.delete(l)
  },
  toggleComplete(id: string) {
    const completed = { ...state.completed }
    if (completed[id]) delete completed[id]
    else completed[id] = new Date().toISOString()
    commit({ ...state, completed })
  },
  setChecklist(docId: string, key: string, done: boolean) {
    const items = { ...(state.checklist[docId] ?? {}) }
    if (done) items[key] = true
    else delete items[key]
    commit({ ...state, checklist: { ...state.checklist, [docId]: items } })
  },
  visit(id: string) {
    const recent = [{ id, at: new Date().toISOString() }, ...state.recent.filter((r) => r.id !== id)].slice(0, 8)
    commit({ ...state, recent })
  },
  reset() {
    commit(emptyState())
  },
  exportJSON(): string {
    return JSON.stringify({ ...state, exportedAt: new Date().toISOString() }, null, 2)
  },
  importJSON(text: string): boolean {
    let v: unknown
    try {
      v = JSON.parse(text)
    } catch {
      return false
    }
    if (!v || typeof v !== 'object' || (v as { version?: unknown }).version !== 1) return false
    commit(parseState(text))
    return true
  },
}

export function useProgress(): ProgressState {
  return useSyncExternalStore(progressStore.subscribe, progressStore.get, progressStore.get)
}

// ---------------------------------------------------------------- derived values (pure)

export const TRACKABLE_TYPES = new Set(['lesson', 'lab', 'project'])

export function isTrackable(doc: Doc): boolean {
  return TRACKABLE_TYPES.has(doc.type) && doc.status !== 'planned'
}

export function checklistDone(doc: Doc, s: ProgressState): number {
  const done = s.checklist[doc.id] ?? {}
  return doc.checklist.filter((i) => done[i.key]).length
}

export function isComplete(doc: Doc, s: ProgressState): boolean {
  if (s.completed[doc.id]) return true
  return doc.type === 'lab' && doc.checklist.length > 0 && checklistDone(doc, s) === doc.checklist.length
}

export function progressFor(docs: Doc[], s: ProgressState): { done: number; total: number; pct: number } {
  const items = docs.filter(isTrackable)
  const done = items.filter((d) => isComplete(d, s)).length
  return { done, total: items.length, pct: items.length ? Math.round((100 * done) / items.length) : 0 }
}

export function moduleDocs(content: Content, moduleNumber: number): Doc[] {
  return content.docs.filter((d) => d.module === moduleNumber)
}
