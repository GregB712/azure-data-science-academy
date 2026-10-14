---
id: extending-the-academy
title: Extending the Academy
type: reference
order: 9
status: available
tags: [maintenance, contributing, roadmap]
related: [m5-m6-azure-ml-roadmap, m7-mlops-roadmap, m8-genai-roadmap]
summary: How content is structured and loaded, how to add a lesson or lab so it appears in the dashboard, and the recommended order for extending into Azure ML, MLOps and generative AI.
---

# Extending the Academy

## How the pieces connect

- **Markdown is the source of truth.** Every lesson, lab, reference page and roadmap is a `.md` file with YAML frontmatter.
- **`curriculum.json`** defines modules (title, description, estimated hours, status). Lessons attach to modules through their `module:` frontmatter field.
- **The dashboard** (`dashboard/`) imports every Markdown file under `docs/`, `labs/`, `projects/`, `diagrams/`, `references/` and the root at build time (Vite `import.meta.glob`), parses frontmatter, renders Markdown with Mermaid diagrams, and builds the search index. There is no separate copy of the content.
- **Relative links** between Markdown files work on GitHub/VS Code *and* in the dashboard, which rewrites them to internal routes.
- **Lab checklists** come from the `## Completion checklist` task list in each lab README.
- **Service explorer and glossary** parse `SERVICE_CATALOG.md` (`### Name` + `- **Field:** value`) and `GLOSSARY.md` (`### Term` + `- **Kind:** ...`).

## Add a lesson

1. Copy [`_templates/LESSON_TEMPLATE.md`](_templates/LESSON_TEMPLATE.md) into the right `docs/<topic>/` folder.
2. Fill the frontmatter: unique `id`, `module`, `order`, `status: available` when ready, `prerequisites`/`related` by id.
3. Follow the 14-section format. Cite Microsoft Learn next to product claims. Mark preview features.
4. Put runnable code in `code/` (with tests in `code/tests/`) or in the lab folder.
5. Run the checks below; the dashboard picks the file up automatically.

## Add a lab

1. Copy [`_templates/LAB_TEMPLATE.md`](_templates/LAB_TEMPLATE.md) to `labs/lab-NN-slug/README.md`.
2. List billable resources, cost estimate, cleanup, and a `## Completion checklist` task list.
3. Add the lab id to the module's `labs` array in `curriculum.json`.
4. Document honestly what was tested and what requires a subscription.

## Checks to run

```bash
# WSL, from the academy root
cd code && python -m pytest && cd ..                    # course code
python3 scripts/check_content.py                        # frontmatter, ids, internal links, checklists
cd dashboard && npm test && npm run build && cd ..      # dashboard tests and production build
```

## Recommended extension order

1. **Lab 05 / Module 5** ([roadmap](azure-machine-learning/README.md)): local LightGBM baseline on `gold/weekly_demand_features`, then Azure ML command job + MLflow. This unlocks capstone Stage 4.
2. **Module 6**: batch endpoint writing `gold/demand_forecast`; promote the planned `supply-chain.demand-forecast` product to `published` with a contract.
3. **Module 7** ([roadmap](mlops/README.md)): GitHub Actions running the existing tests and contract checks; OIDC deployment of `main.bicep`.
4. **Module 2 and 4** ([roadmap](storage-and-data-engineering/README.md)): adlfs access patterns, ADF/Databricks orchestration, change-data-feed incremental Silver.
5. **Module 8** ([roadmap](generative-ai/README.md)): RAG and agents over the forecasting product.
6. **Module 9** ([roadmap](security-and-costs/README.md)): private networking, Purview in practice, FinOps.

Before writing each module, re-check product names, SDK versions and CLI commands against Microsoft Learn: the Azure AI and Databricks product names changed in 2025-2026 and will change again.
