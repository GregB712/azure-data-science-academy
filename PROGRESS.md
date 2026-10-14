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

## Reference work
- [ ] Wrote my first ADR using the [decision guide](ARCHITECTURE_DECISION_GUIDE.md) template

## Capstone
- [ ] Stage 1 data generated and explored
- [ ] Stage 2 lakehouse running locally
- [ ] Stage 2 lakehouse running on ADLS Gen2
- [ ] Stage 3 contracts for all published products

## Notes
<!-- Dates, blockers, questions, links to your own repos -->
