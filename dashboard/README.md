# Dashboard

Local web app for the Azure Data Science Academy. It renders the Markdown dossier in the parent folder; it has no content of its own and no backend.

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # tsc + vite build -> dist/
npm run preview    # http://localhost:4173
npm test           # vitest: lib units + checks against the real dossier
```

Requires Node.js 20.19+. Run the commands from this folder: `vite.config.ts` allows Vite to read the parent academy folder.

## Pages

| Route | Page |
|---|---|
| `#/` | Dashboard: objectives, recommended path, module cards with progress, recently opened, quick links |
| `#/catalog` | Searchable, filterable list of every document |
| `#/doc/<path>` | Lesson/lab/reference page: metadata, mark complete, prerequisites and related links, table of contents, lab checklist panel, previous/next |
| `#/labs` | Lab tracker with checklist progress (planned labs listed from `curriculum.json`) |
| `#/architecture` | Architecture explorer: diagrams with the services and lessons behind them |
| `#/services` | Service lookup parsed from `SERVICE_CATALOG.md` |
| `#/glossary` | Glossary parsed from `GLOSSARY.md` |
| `#/search?q=` | Full-text search by section (MiniSearch, built in the browser) |
| `#/progress` | Progress by module, export/import/reset |
| `#/file/<path>` | Read-only code and script viewer, folder listings |

## Code layout

- `src/content/`: loads Markdown with `import.meta.glob` and builds the content model (`model.ts`).
- `src/lib/`: Markdown rendering, link rewriting, slugs, search, progress store, router, theme.
- `src/components/`, `src/pages/`: UI.
- `src/test/`: tests. `fixtures.ts` builds the same content model from the files on disk with Node's `fs`.

Progress is stored in `localStorage` (`adsa.progress.v1`); see the main README section "Progress persistence and its limits".
