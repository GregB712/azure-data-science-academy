/**
 * Keeps the progress store in step with the Clerk auth state.
 *  - signed out  -> guest mode: in-memory only, nothing saved.
 *  - signed in   -> account mode: progress read from and written to the user's
 *                   Clerk unsafeMetadata (debounced). On the first sign-in with an
 *                   empty account, this session's guest ticks plus any legacy local
 *                   progress are migrated up, then the legacy local copy is removed.
 * Rendered only when Clerk is configured; returns no UI.
 */
import { useEffect, useRef } from 'react'
import { useUser } from '@clerk/clerk-react'
import { emptyState, parseState, progressStore, STORAGE_KEY, type ProgressState } from '../lib/progress'
import { deserializeProgress, isEmptyProgress, mergeProgress, serializeProgress } from './metadata'

const DEBOUNCE_MS = 800

export default function ProgressSync() {
  const { isLoaded, isSignedIn, user } = useUser()
  const userRef = useRef(user)
  userRef.current = user
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => {
    if (!isLoaded) return

    if (!isSignedIn || !user) {
      progressStore.configure({ mode: 'guest', sink: null, initial: emptyState() })
      return
    }

    const saveToAccount = (s: ProgressState) => {
      clearTimeout(timer.current)
      timer.current = setTimeout(() => {
        const u = userRef.current
        if (!u) return
        // offline or rejected: progress stays in memory for this session
        void u.update({ unsafeMetadata: { ...u.unsafeMetadata, progress: serializeProgress(s) } }).catch(() => {})
      }, DEBOUNCE_MS)
    }

    const account = deserializeProgress((user.unsafeMetadata as { progress?: unknown })?.progress)
    if (!isEmptyProgress(account)) {
      progressStore.configure({ mode: 'account', sink: saveToAccount, initial: account })
    } else {
      const seed = mergeProgress(progressStore.get(), readLegacyLocal())
      progressStore.configure({ mode: 'account', sink: saveToAccount, initial: seed })
      if (!isEmptyProgress(seed)) {
        saveToAccount(seed)
        clearLegacyLocal()
      }
    }

    return () => clearTimeout(timer.current)
    // user.id is stable across metadata updates, so saving does not retrigger this effect.
  }, [isLoaded, isSignedIn, user?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  return null
}

function readLegacyLocal(): ProgressState {
  try {
    return parseState(window.localStorage.getItem(STORAGE_KEY))
  } catch {
    return emptyState()
  }
}

function clearLegacyLocal() {
  try {
    window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}
