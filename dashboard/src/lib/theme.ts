import { useSyncExternalStore } from 'react'

export type Theme = 'light' | 'dark'
const KEY = 'adsa.theme'
const listeners = new Set<() => void>()

function systemTheme(): Theme {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function stored(): Theme | null {
  try {
    const v = window.localStorage.getItem(KEY)
    return v === 'light' || v === 'dark' ? v : null
  } catch {
    return null
  }
}

export function currentTheme(): Theme {
  return (document.documentElement.dataset.theme as Theme) || systemTheme()
}

export function initTheme() {
  document.documentElement.dataset.theme = stored() ?? systemTheme()
  window.matchMedia?.('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (!stored()) setTheme(systemTheme(), false)
  })
}

export function setTheme(t: Theme, persist = true) {
  document.documentElement.dataset.theme = t
  if (persist) {
    try {
      window.localStorage.setItem(KEY, t)
    } catch {
      /* storage unavailable: theme applies for this session only */
    }
  }
  listeners.forEach((l) => l())
}

export function useTheme(): Theme {
  return useSyncExternalStore(
    (l) => {
      listeners.add(l)
      return () => listeners.delete(l)
    },
    currentTheme,
    () => 'light' as Theme,
  )
}
