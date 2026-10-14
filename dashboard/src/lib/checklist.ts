export interface ChecklistItem {
  key: string
  text: string
}

/** Stable key for a checklist item, computed identically from Markdown source and rendered text. */
export function checklistKey(text: string): string {
  return text
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '')
}

const TASK = /^\s*[-*]\s+\[( |x|X)\]\s+(.*)$/

/** Task-list items under a "## Completion checklist" heading (labs). */
export function extractCompletionChecklist(body: string): ChecklistItem[] {
  const lines = body.split(/\r?\n/)
  const items: ChecklistItem[] = []
  let inSection = false
  let inFence = false
  for (const line of lines) {
    if (/^```/.test(line.trim())) inFence = !inFence
    if (inFence) continue
    if (/^##\s+/.test(line)) {
      inSection = /^##\s+completion checklist\s*$/i.test(line.trim())
      continue
    }
    if (!inSection) continue
    const m = TASK.exec(line)
    if (m) items.push({ key: checklistKey(m[2]), text: m[2].trim() })
  }
  return items
}
