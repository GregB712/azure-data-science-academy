import { useEffect, type RefObject } from 'react'

/**
 * Drag-to-dismiss for the mobile navigation drawer.
 *
 * - The drawer tracks the pointer 1:1 from wherever it was grabbed.
 * - A 10px hysteresis decides between a horizontal drag and a vertical scroll,
 *   so the sidebar still scrolls normally.
 * - Dragging past the open edge rubber-bands instead of hard-stopping.
 * - On release, the gesture's velocity is projected forward (the same
 *   exponential deceleration scroll views use) to decide whether to close,
 *   so a short flick closes it and a slow half-drag can still snap back.
 * - Releasing hands back to the CSS transition, which starts from the current
 *   on-screen position, so there is no jump.
 */

const LOCK_THRESHOLD = 10
const DECELERATION = 0.998

/** Distance a flick would travel before coming to rest, in px. */
export function project(velocityPxPerSec: number, rate = DECELERATION): number {
  return ((velocityPxPerSec / 1000) * rate) / (1 - rate)
}

/** Progressive resistance past a boundary. */
export function rubberband(overshoot: number, dimension: number, constant = 0.55): number {
  return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot))
}

export function useDrawerGesture(ref: RefObject<HTMLElement | null>, open: boolean, onClose: () => void) {
  useEffect(() => {
    const el = ref.current
    if (!el || !open) return
    const backdrop = document.querySelector<HTMLElement>('.backdrop')
    const isDrawer = () => getComputedStyle(el).position === 'fixed'

    let id: number | null = null
    let startX = 0
    let startY = 0
    let mode: 'pending' | 'drag' | 'scroll' = 'pending'
    let history: { x: number; t: number }[] = []
    let width = 0

    const offsetFor = (clientX: number) => {
      const dx = clientX - startX
      return dx > 0 ? rubberband(dx, width) : dx
    }

    const apply = (x: number) => {
      el.style.transform = `translateX(${x}px)`
      if (backdrop) backdrop.style.opacity = String(Math.max(0, Math.min(1, 1 + x / width)))
    }

    const release = () => {
      el.style.transition = ''
      el.style.transform = ''
      if (backdrop) {
        backdrop.style.transition = ''
        backdrop.style.opacity = ''
      }
    }

    const down = (e: PointerEvent) => {
      if (id !== null || !isDrawer() || (e.pointerType === 'mouse' && e.button !== 0)) return
      id = e.pointerId
      startX = e.clientX
      startY = e.clientY
      mode = 'pending'
      width = el.getBoundingClientRect().width
      history = [{ x: e.clientX, t: e.timeStamp }]
    }

    const move = (e: PointerEvent) => {
      if (e.pointerId !== id) return
      const dx = e.clientX - startX
      const dy = e.clientY - startY
      if (mode === 'pending') {
        if (Math.hypot(dx, dy) < LOCK_THRESHOLD) return
        if (Math.abs(dx) > Math.abs(dy)) {
          mode = 'drag'
          el.setPointerCapture(e.pointerId)
          el.style.transition = 'none'
          if (backdrop) backdrop.style.transition = 'none'
          el.classList.add('dragging')
        } else {
          mode = 'scroll'
          return
        }
      }
      if (mode !== 'drag') return
      history.push({ x: e.clientX, t: e.timeStamp })
      if (history.length > 6) history.shift()
      apply(offsetFor(e.clientX))
    }

    const up = (e: PointerEvent) => {
      if (e.pointerId !== id) return
      id = null
      if (mode !== 'drag') return
      el.classList.remove('dragging')
      // Velocity from the last ~100ms of movement, not just the final event.
      const last = history[history.length - 1]
      const first = history.find((h) => last.t - h.t <= 100) ?? history[0]
      const dt = last.t - first.t
      const velocity = dt > 0 ? ((last.x - first.x) / dt) * 1000 : 0
      const x = offsetFor(e.clientX)
      const projected = x + project(velocity)
      release()
      if (e.type !== 'pointercancel' && projected < -width / 2) onClose()
      // Swallow the click that would otherwise land on a link after a drag.
      const swallow = (ev: Event) => { ev.stopPropagation(); ev.preventDefault() }
      el.addEventListener('click', swallow, { capture: true, once: true })
      setTimeout(() => el.removeEventListener('click', swallow, { capture: true }), 0)
    }

    el.addEventListener('pointerdown', down)
    el.addEventListener('pointermove', move)
    el.addEventListener('pointerup', up)
    el.addEventListener('pointercancel', up)
    return () => {
      el.removeEventListener('pointerdown', down)
      el.removeEventListener('pointermove', move)
      el.removeEventListener('pointerup', up)
      el.removeEventListener('pointercancel', up)
      release()
    }
  }, [ref, open, onClose])
}
