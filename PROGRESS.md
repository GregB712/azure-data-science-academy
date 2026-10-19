---
id: progress
title: Progress Tracker
type: reference
order: 6
status: available
tags: [progress, tracking]
related: [course-map]
summary: A version-controllable progress log. The dashboard tracks progress in your browser; use this file if you want progress in git.
---

# Progress Tracker

Two ways to track progress:

1. **Dashboard (automatic):** mark lessons complete and tick lab checklist items in the dashboard. State is stored in your browser's `localStorage` (see [README → Progress persistence](README.md#progress-persistence-and-its-limits)). Use **Export progress** in the dashboard to save a JSON backup, and **Import** to restore it on another browser or machine.
2. **This file (manual, versioned):** tick the boxes below and commit. Useful if you work across machines or want a portfolio trail.

## Module 1: Azure fundamentals
- [ ] Read [Azure fundamentals](docs/azure-fundamentals/01-azure-fundamentals.md)
- [ ] Completed the knowledge check
- [ ] Completed the independent exercise (team subscription/RG/RBAC design)
- [ ] Completed [Lab 01](labs/lab-01-azure-setup/README.md) (or tasks 1-3 + offline verification)

## Module 3: Lakehouse and data mesh
- [ ] Read [Lakehouse + medallion](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md)
- [ ] Ran the local medallion pipeline and the tests
- [ ] Exercise Part A (stockout Gold table, revenue rule, late correction)
- [ ] Exercise Part B (three architecture scenarios)
- [ ] Read [Data mesh](docs/data-mesh/01-data-mesh.md)
- [ ] Ran registry validate / impact and the contract compatibility check
- [ ] Data mesh exercises 1-5
- [ ] Completed [Lab 03](labs/lab-03-lakehouse/README.md)

## Module 5: Azure Machine Learning
- [ ] Read [Workspace, compute and costs](docs/azure-machine-learning/01-workspace-compute-and-costs.md)
- [ ] Read [Jobs, data and tracking](docs/azure-machine-learning/02-jobs-data-and-tracking.md)
- [ ] Read [Sweeps, components and pipelines](docs/azure-machine-learning/03-sweeps-components-and-pipelines.md)
- [ ] Ran the local backtest (WAPE ~0.23, MASE < 1) and compared runs in `mlflow ui`
- [ ] Completed [Lab 05](labs/lab-05-model-training/README.md) (tasks 1-4 local; 5-7 optional on Azure)

## Module 6: Model management and deployment
- [ ] Read [Model registry and release](docs/azure-machine-learning/04-model-registry-and-release.md)
- [ ] Read [Batch endpoints and the forecast product](docs/azure-machine-learning/05-batch-endpoints.md)
- [ ] Read [Online endpoints and FastAPI](docs/azure-machine-learning/06-online-endpoints-and-fastapi.md)
- [ ] Produced `gold/demand_forecast` and ran the FastAPI service locally
- [ ] Completed [Lab 06](labs/lab-06-model-deployment/README.md) (tasks 1-4 local; 5-8 optional; billable endpoints deleted)

## Reference work
- [ ] Wrote my first ADR using the [decision guide](ARCHITECTURE_DECISION_GUIDE.md) template

## Capstone
- [ ] Stage 1 data generated and explored
- [ ] Stage 2 lakehouse running locally
- [ ] Stage 2 lakehouse running on ADLS Gen2
- [ ] Stage 3 contracts for all published products
- [ ] Stage 5 forecast product `gold/demand_forecast` produced and served (Module 6)

## Notes
<!-- Dates, blockers, questions, links to your own repos -->
