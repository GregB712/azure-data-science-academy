/**
 * Content loading. Vite inlines every Markdown file of the dossier (and the
 * course's code files) into the bundle at build time, so the dashboard always
 * shows exactly what is in the folders: there is no second copy to maintain.
 * In `npm run dev`, editing a Markdown file reloads the page.
 */
import curriculumJson from '../../../curriculum.json'
import { buildContent, toRepoPath, type Curriculum } from './model'

const markdown = import.meta.glob(
  [
    '../../../*.md',
    '../../../docs/**/*.md',
    '../../../labs/**/*.md',
    '../../../projects/**/*.md',
    '../../../diagrams/**/*.md',
    '../../../references/**/*.md',
    '!../../../docs/_templates/**',
    '!**/node_modules/**',
  ],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>

const raw = import.meta.glob(
  [
    '../../../*.json',
    '../../../code/**/*.{py,yaml,yml,txt,ini}',
    '../../../labs/**/*.{sh,py,bicep,txt,example}',
    '../../../docs/_templates/*.md',
    '!**/__pycache__/**',
    '!**/.venv/**',
    '!**/node_modules/**',
  ],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>

const rekey = (obj: Record<string, string>) =>
  Object.fromEntries(Object.entries(obj).map(([k, v]) => [toRepoPath(k), v]))

export const content = buildContent(rekey(markdown), rekey(raw), curriculumJson as Curriculum)
