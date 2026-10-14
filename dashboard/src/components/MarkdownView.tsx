import { useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import { content } from '../content/load'
import { checklistKey } from '../lib/checklist'
import { renderMarkdown } from '../lib/markdown'
import { progressStore, useProgress } from '../lib/progress'
import { useTheme } from '../lib/theme'

let diagramCounter = 0

interface Props {
  body: string
  path: string // repo-relative source path, for link resolution
  docId?: string // enables interactive task-list checkboxes
  scrollTo?: string | null
  inline?: boolean
  className?: string
}

/** Renders dossier Markdown: highlighted code with copy buttons, Mermaid diagrams, interactive checklists. */
export default function MarkdownView({ body, path, docId, scrollTo, inline, className }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const html = useMemo(() => renderMarkdown(body, path, content, inline), [body, path, inline])
  const theme = useTheme()
  const progress = useProgress()

  // The HTML is set imperatively, not via dangerouslySetInnerHTML, so that
  // re-renders (e.g. a progress update) never replace rendered diagrams.
  useLayoutEffect(() => {
    if (ref.current) ref.current.innerHTML = html
  }, [html])

  // Mermaid: lazy-load the library only when a page has diagrams. Blocks are
  // looked up again after the async import, because the page may have
  // re-rendered in the meantime.
  useEffect(() => {
    if (!ref.current?.querySelector('.mermaid-block')) return
    let cancelled = false
    import('mermaid').then(async ({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'strict',
        theme: theme === 'dark' ? 'dark' : 'default',
        fontFamily: 'inherit',
        flowchart: { htmlLabels: true, curve: 'basis' },
      })
      const blocks = Array.from(ref.current?.querySelectorAll<HTMLElement>('.mermaid-block') ?? [])
      for (const block of blocks) {
        if (cancelled) return
        const src = block.dataset.src ?? ''
        try {
          const { svg } = await mermaid.render(`mmd-${++diagramCounter}`, src)
          if (!cancelled) block.innerHTML = svg
        } catch (err) {
          if (!cancelled) {
            const pre = document.createElement('pre')
            pre.className = 'mermaid-error'
            pre.textContent = `Diagram could not be rendered: ${(err as Error).message}\n\n${src}`
            block.replaceChildren(pre)
          }
        }
      }
    })
    return () => {
      cancelled = true
    }
  }, [html, theme])

  // Copy buttons and interactive checklists (event delegation).
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const onClick = (e: MouseEvent) => {
      const btn = (e.target as HTMLElement).closest<HTMLButtonElement>('.copy-btn')
      if (!btn) return
      const code = btn.parentElement?.querySelector('code')?.textContent ?? ''
      navigator.clipboard?.writeText(code).then(
        () => {
          btn.textContent = 'Copied'
          setTimeout(() => (btn.textContent = 'Copy'), 1200)
        },
        () => (btn.textContent = 'Select & copy'),
      )
    }
    const onChange = (e: Event) => {
      const input = e.target as HTMLInputElement
      if (!docId || input.type !== 'checkbox') return
      const li = input.closest('li')
      if (li) progressStore.setChecklist(docId, checklistKey(li.textContent ?? ''), input.checked)
    }
    el.addEventListener('click', onClick)
    el.addEventListener('change', onChange)
    return () => {
      el.removeEventListener('click', onClick)
      el.removeEventListener('change', onChange)
    }
  }, [docId])

  // Reflect stored checklist state into the rendered checkboxes.
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const done = docId ? progress.checklist[docId] ?? {} : {}
    el.querySelectorAll<HTMLInputElement>('li > input[type="checkbox"]').forEach((input) => {
      if (!docId) return
      input.disabled = false
      const li = input.closest('li')
      input.checked = !!done[checklistKey(li?.textContent ?? '')]
      li?.classList.add('task-item')
    })
  }, [html, docId, progress])

  useEffect(() => {
    if (!scrollTo) return
    const target = ref.current?.querySelector(`#${CSS.escape(scrollTo)}`)
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [html, scrollTo])

  const Tag = inline ? 'span' : 'div'
  return <Tag ref={ref as never} className={`${inline ? '' : 'markdown'} ${className ?? ''}`} />
}
