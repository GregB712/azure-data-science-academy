/**
 * Pure helpers for moving progress between the store and Clerk user metadata.
 * No Clerk imports here so the logic stays unit-testable in a plain node env.
 */
import { emptyState, parseState, type ProgressState } from '../lib/progress'

// Clerk's unsafeMetadata has an ~8 KB budget; keep the saved payload under it.
const MAX_BYTES = 7000

/** Read progress out of `user.unsafeMetadata.progress` (an object, or a JSON string). */
export function deserializeProgress(meta: unknown): ProgressState {
  if (meta == null) return emptyState()
  const text = typeof meta === 'string' ? meta : JSON.stringify(meta)
  return parseState(text)
}

/** Prepare progress for saving, dropping the (ephemeral) recent list if near the size cap. */
export function serializeProgress(s: ProgressState): ProgressState {
  if (JSON.stringify(s).length > MAX_BYTES) return { ...s, recent: [] }
  return s
}

export function isEmptyProgress(s: ProgressState): boolean {
  return Object.keys(s.completed).length === 0 && Object.keys(s.checklist).length === 0
}

/** Merge two progress states; on conflict `primary` wins. Used to migrate local → account. */
export function mergeProgress(primary: ProgressState, secondary: ProgressState): ProgressState {
  const checklist: ProgressState['checklist'] = {}
  for (const id of new Set([...Object.keys(secondary.checklist), ...Object.keys(primary.checklist)])) {
    checklist[id] = { ...(secondary.checklist[id] ?? {}), ...(primary.checklist[id] ?? {}) }
  }
  const recent = [...primary.recent, ...secondary.recent]
    .filter((r, i, a) => a.findIndex((x) => x.id === r.id) === i)
    .slice(0, 8)
  return {
    version: 1,
    completed: { ...secondary.completed, ...primary.completed },
    checklist,
    recent,
  }
}
