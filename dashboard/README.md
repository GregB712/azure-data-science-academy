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

## Authentication (optional)

Sign in / sign up is provided by [Clerk](https://clerk.com) and is **off by default**. With no key set, the dashboard runs exactly as before: everyone is a guest and progress lives in `localStorage`.

To turn it on:

1. Create a free Clerk application at [dashboard.clerk.com](https://dashboard.clerk.com).
2. Enable the sign-in methods you want: **Email** and the social connections you want under Social connections (e.g. **Google** and **GitHub**). The sign-in/sign-up UI renders whatever you enable automatically, no code change needed.
3. Allow account deletion: **Configure → User & Authentication → Account** → turn on "Allow users to delete their accounts" (this is what powers the Delete account button in the profile).
4. Copy the **Publishable key** (`pk_test_…` / `pk_live_…`, safe to expose in the browser) and set it:
   ```bash
   cp .env.example .env     # then edit VITE_CLERK_PUBLISHABLE_KEY
   ```
5. For the deployed site (Vercel), add `VITE_CLERK_PUBLISHABLE_KEY` as a project environment variable and redeploy. In Clerk, add your production domain and `http://localhost:5173` to the allowed origins.

What auth changes:

- **Guest** (not signed in): progress is kept in memory for the session only and is **not saved**.
- **Signed in**: progress is saved to the user's Clerk profile (`unsafeMetadata`) and syncs across devices. A guest's existing local progress is merged into the account on first sign-in.
- **Profile** (the avatar menu, top right): Clerk's built-in profile shows name and email, changes password (hidden for accounts that only use a social login such as Google or GitHub), and deletes the account. A custom "Progress" tab shows the user's own progress.

No backend or database is added: the publishable key is the only configuration, and progress is stored on the Clerk user.

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

Progress is stored in `localStorage` (`adsa.progress.v1`) when auth is off, in memory only for signed-out guests when auth is on, and in the Clerk user profile when signed in (see "Authentication" above). The store and its persistence target live in `src/lib/progress.ts`; the auth wiring is in `src/auth/`.
