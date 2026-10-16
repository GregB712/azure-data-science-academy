/**
 * Clerk integration, kept behind a single flag so the dashboard runs with or
 * without authentication:
 *  - VITE_CLERK_PUBLISHABLE_KEY set   -> auth active (sign in/up, account profile,
 *    progress saved to the account).
 *  - not set                         -> auth off; the app behaves exactly as before,
 *    with progress in this browser's localStorage. This keeps the repo runnable
 *    out of the box without a Clerk account.
 */
import { useState, type ReactNode } from 'react'
import {
  ClerkProvider,
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  UserButton,
  useUser,
} from '@clerk/clerk-react'
import { ProgressBar } from '../components/ui'
import { content } from '../content/load'
import { moduleDocs, progressFor, useProgress } from '../lib/progress'
import ProgressSync from './ProgressSync'

const KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined
export const CLERK_ENABLED = Boolean(KEY)
const BANNER_KEY = 'adsa.authprompt'

export function AuthProvider({ children }: { children: ReactNode }) {
  if (!CLERK_ENABLED) return <>{children}</>
  return (
    <ClerkProvider publishableKey={KEY!} afterSignOutUrl="/">
      <ProgressSync />
      {children}
    </ClerkProvider>
  )
}

/** Sign in / up buttons (signed out) or the account menu (signed in). In the top bar. */
export function AuthControls() {
  if (!CLERK_ENABLED) return null
  return (
    <div className="auth-controls">
      <SignedOut>
        <SignInButton mode="modal">
          <button type="button" className="ghost">Sign in</button>
        </SignInButton>
        <SignUpButton mode="modal">
          <button type="button" className="primary">Sign up</button>
        </SignUpButton>
      </SignedOut>
      <SignedIn>
        <UserButton afterSignOutUrl="/">
          <UserButton.UserProfilePage label="Progress" labelIcon={<span aria-hidden>📊</span>} url="progress">
            <ProfileProgress />
          </UserButton.UserProfilePage>
        </UserButton>
      </SignedIn>
    </div>
  )
}

/** Dismissible, non-blocking prompt for signed-out visitors. "Guest" just dismisses it. */
export function GuestBanner() {
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(BANNER_KEY) === 'dismissed'
    } catch {
      return false
    }
  })
  if (!CLERK_ENABLED || dismissed) return null
  const dismiss = () => {
    try {
      localStorage.setItem(BANNER_KEY, 'dismissed')
    } catch {
      /* ignore */
    }
    setDismissed(true)
  }
  return (
    <SignedOut>
      <div className="auth-banner" role="region" aria-label="Save your progress">
        <p>
          <strong>Save your progress.</strong>{' '}
          <span className="small">Create an account (email, Google or GitHub) to keep your ticks across devices. Browsing as a guest works too, but nothing is saved.</span>
        </p>
        <div className="auth-banner-actions">
          <SignUpButton mode="modal">
            <button type="button" className="primary">Sign up</button>
          </SignUpButton>
          <SignInButton mode="modal">
            <button type="button" className="ghost">Sign in</button>
          </SignInButton>
          <button type="button" className="ghost" onClick={dismiss}>Check the guide as guest</button>
        </div>
      </div>
    </SignedOut>
  )
}

/** The custom "Progress" tab inside the Clerk account profile. */
function ProfileProgress() {
  const { user } = useUser()
  const s = useProgress()
  const overall = progressFor(content.docs, s)
  const name = user?.fullName || user?.firstName || 'Learner'
  const email = user?.primaryEmailAddress?.emailAddress ?? ''
  return (
    <div className="profile-progress">
      <h1>Your progress</h1>
      <p className="small muted">Signed in as {name}{email ? ` · ${email}` : ''}</p>
      <ProgressBar pct={overall.pct} label="Overall progress" />
      <p className="small">{overall.done} of {overall.total} available lessons, labs and projects complete ({overall.pct}%).</p>
      <table className="table">
        <thead><tr><th>Module</th><th>Done</th></tr></thead>
        <tbody>
          {content.curriculum.modules.map((m) => {
            const p = progressFor(moduleDocs(content, m.number), s)
            return (
              <tr key={m.id}>
                <td>{m.number}. {m.title}</td>
                <td>{p.total ? `${p.done}/${p.total} (${p.pct}%)` : '–'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
