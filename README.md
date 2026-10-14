# Azure Data Science Academy

A self-paced course for designing, building, deploying and operating data science and AI systems on Microsoft Azure. It is written for an experienced data scientist or AI engineer working on Windows 11 with WSL2/Ubuntu, VS Code, Python and Jupyter. It does not teach Python or introductory ML.

There are three connected parts, all in this folder:

1. **The dossier**: Markdown lessons, labs, reference pages and diagrams. It reads fine on its own, in VS Code or on GitHub.
2. **The dashboard** (`dashboard/`): a local web app that renders the dossier and adds navigation, search, explorers and progress tracking. It reads the Markdown files directly and has no second copy of the content.
3. **The hands-on curriculum**: runnable code (`code/`), labs (`labs/`) and a retail demand forecasting capstone (`projects/`).

## What is in version 0.1

| Area | Status | Where |
|---|---|---|
| Course roadmap and sequence | ✅ Written | [COURSE_MAP.md](COURSE_MAP.md), [curriculum.json](curriculum.json) |
| Module 1: Azure fundamentals lesson | ✅ Written (14-part format) | [docs/azure-fundamentals](docs/azure-fundamentals/01-azure-fundamentals.md) |
| Module 3: lake, warehouse, lakehouse, medallion, Delta/Iceberg, Databricks vs Fabric, OneLake vs ADLS | ✅ Written | [docs/lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md) |
| Module 3: data mesh (principles, products, contracts, governance, domain map) | ✅ Written | [docs/data-mesh](docs/data-mesh/01-data-mesh.md) |
| Architecture decision guide | ✅ Written | [ARCHITECTURE_DECISION_GUIDE.md](ARCHITECTURE_DECISION_GUIDE.md) |
| Service catalog (31 entries) and glossary (68 terms) | ✅ Written | [SERVICE_CATALOG.md](SERVICE_CATALOG.md), [GLOSSARY.md](GLOSSARY.md) |
| Lab 01: secure Azure setup from WSL | ✅ Runnable (scripts, Bicep, Python verifier) | [labs/lab-01-azure-setup](labs/lab-01-azure-setup/README.md) |
| Lab 03: local medallion lakehouse and data products | ✅ Runnable, no Azure needed | [labs/lab-03-lakehouse](labs/lab-03-lakehouse/README.md) |
| Course code: data generator, Delta medallion pipeline, contracts, product registry | ✅ Runnable, 15 tests | [code/](code/) |
| Dashboard | ✅ Runnable | `dashboard/` (see [Run the dashboard](#run-the-dashboard)) |
| Modules 2, 4, 5–9 | 📝 Roadmaps (scope, lessons, labs, design), not full lessons yet | [docs/](docs/) |
| Capstone | 🟡 Stages 1–3 implemented by the course code; stages 4–6 planned | [projects/retail-demand-forecasting](projects/retail-demand-forecasting/README.md) |
| Diagrams | ✅ 4 available, 📝 3 planned (ML lifecycle, MLOps, RAG) | [diagrams/](diagrams/) |

The extension path to Azure ML, MLOps and generative AI is laid out in [docs/EXTENDING.md](docs/EXTENDING.md) and in each module roadmap.

## Quick start

All commands below run in the **WSL / Ubuntu terminal** unless a step says otherwise. Keep the folder on the Linux filesystem (for example `~/src/azure-data-science-academy`), not under `/mnt/c/...`, because file access across the Windows boundary is much slower.

### Read

Open [COURSE_MAP.md](COURSE_MAP.md) in VS Code (`Ctrl+Shift+V` for the preview), or start the dashboard.

### Run the dashboard

Requires **Node.js 20.19 or newer** (`node --version`). Install it in WSL with [nvm](https://github.com/nvm-sh/nvm) or your package manager.

```bash
cd dashboard
npm install
npm run dev          # http://localhost:5173 , reloads when you edit any Markdown file
```

Other commands:

```bash
npm run build        # type-check and build a static site into dashboard/dist/
npm run preview      # serve the built site at http://localhost:4173
npm test             # unit tests plus checks against the real dossier (links, ids, checklists)
```

WSL2 forwards `localhost` to Windows, so open the URL in your Windows browser. The built site in `dist/` is static: any static file server works, and nothing is sent anywhere.

### Run the course code

```bash
cd code
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                       # 15 tests
python retail_data/generate.py --out ../data/raw --seed 42
python lakehouse_local/medallion.py all --raw ../data/raw --lake ../data/lake
```

Then follow [Lab 03](labs/lab-03-lakehouse/README.md). For Azure work, start with [Lab 01](labs/lab-01-azure-setup/README.md), which checks prerequisites before creating anything.

### Check the content after editing

```bash
python3 scripts/check_content.py      # frontmatter, unique ids, links and anchors, checklists
cd dashboard && npm test
```

## Directory structure

```text
azure-data-science-academy/
├── README.md                     this file
├── COURSE_MAP.md                 sequence, modules, cost overview
├── curriculum.json               modules, objectives, recommended path (drives the dashboard)
├── ARCHITECTURE_DECISION_GUIDE.md
├── SERVICE_CATALOG.md            parsed by the dashboard's service lookup
├── GLOSSARY.md                   parsed by the dashboard's glossary
├── PROGRESS.md                   manual, git-friendly progress log
├── docs/                         lessons and module roadmaps, templates, EXTENDING.md
├── labs/                         lab-01-azure-setup, lab-03-lakehouse
├── projects/                     retail-demand-forecasting capstone
├── diagrams/                     architecture views (Mermaid), used by the architecture explorer
├── references/                   command cheat sheet, official docs index
├── code/                         generator, lakehouse, contracts, data mesh registry, tests
├── scripts/check_content.py      content checks
└── dashboard/                    Vite + React + TypeScript app
```

### How the dashboard loads content

At build time (and live in `npm run dev`) Vite's `import.meta.glob` pulls in every Markdown file under the root, `docs/`, `labs/`, `projects/`, `diagrams/` and `references/`, plus code and script files for the read-only code viewer. Each file's YAML frontmatter (`id`, `title`, `type`, `module`, `status`, `prerequisites`, `related`, ...) gives the catalog, sidebar, previous/next order and links. Lab checklists come from each lab's `## Completion checklist` section. Relative links in the Markdown are rewritten to dashboard routes, so the same links work in VS Code, on GitHub and in the dashboard. To add content, see [docs/EXTENDING.md](docs/EXTENDING.md).

## Progress persistence and its limits

The dashboard stores progress (completed items, lab checklist ticks, recently opened pages) in the browser's `localStorage` under the key `adsa.progress.v1`. There is no backend, account or cloud storage. That keeps it private and simple, with these limits:

- **Per browser and per origin.** Chrome and Edge keep separate progress, and so do `http://localhost:5173` (dev) and `http://localhost:4173` (preview).
- **Cleared with site data.** Clearing browsing data, or using a private window, starts empty.
- **Not synced** across machines.
- If the browser blocks storage, the dashboard keeps progress in memory for that tab and shows a warning.

Use **My progress → Export JSON** to back up or move progress, and **Import JSON** to restore it. If you want progress in git, use [PROGRESS.md](PROGRESS.md) instead.

## Troubleshooting

| Problem | Fix |
|---|---|
| `npm install` or `vite` fails with syntax or engine errors | Node is too old. Vite 7 needs Node 20.19+ or 22.12+. |
| Dev server shows `The request url ... is outside of Vite serving allow list` | Run `npm run dev` from inside `dashboard/`. `vite.config.ts` allows the parent academy folder; moving `dashboard/` elsewhere breaks this. |
| Dashboard or Python is very slow | The folder is under `/mnt/c`. Move it into the Linux filesystem (`~/`). |
| `Port 5173 is already in use` | Vite picks the next free port and prints it, or stop the other process. |
| A diagram shows "Diagram could not be rendered" | The Mermaid source in that Markdown file has a syntax error; the message and source are shown in place. |
| Progress disappeared | Different browser, origin or cleared site data. Import your last export. |
| Windows browser cannot reach `localhost:5173` | Run `npm run dev -- --host` and use the WSL IP address (`hostname -I`). |

## Safety and costs

- No credentials are stored in this repository. Azure code uses Entra ID through your `az login` session (`AzureCliCredential`/`DefaultAzureCredential`) and storage accounts with shared-key access disabled.
- Every lab states its cost, the resources it creates, and cleanup steps. Budgets in Azure only alert; they never stop spending, so run cleanup.
- Every command block says where it runs: WSL, PowerShell, Azure Cloud Shell, or Python.

## What was verified, and what was not

Verified in the build environment (Linux, Python 3.13, Node 22):

- Course code tests (15) and Lab 01 Python tests (7) pass; the generator and pipeline produce the numbers quoted in the lessons.
- `scripts/check_content.py` finds no broken internal links, anchors or ids.
- Every Azure CLI command in Lab 01 was parsed by Azure CLI 2.91 without errors, and the lab scripts were run end to end against a stub `az`. `main.bicep` builds and lints with Bicep 0.48.
- The dashboard type-checks, its tests pass, it builds, and its main pages were opened in headless Chromium (see `dashboard/README.md`).

Not verified:

- **Nothing was run against a real Azure subscription**, Databricks workspace, Fabric capacity or Purview account. Azure steps are written from current Microsoft documentation and cited inline, but you are the first to run them.
- External links were not checked automatically (the build environment could not reach learn.microsoft.com directly).
- Microsoft Fabric trial terms could not be re-checked at writing time; confirm the current trial length and capacity on the [Fabric trial page](https://learn.microsoft.com/fabric/fundamentals/fabric-trial) before relying on it.
