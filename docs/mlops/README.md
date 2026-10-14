---
id: m7-mlops-roadmap
title: "Module 7 Roadmap: MLOps and Production Operations"
module: 7
type: module-overview
order: 0
status: planned
tags: [mlops, ci-cd, github-actions, oidc, bicep, terraform, monitoring, drift, retraining]
prerequisites: [m5-m6-azure-ml-roadmap]
related: [m9-security-roadmap, retail-forecasting-capstone]
summary: Planned lessons for automating the forecasting system end to end - training pipelines, CI/CD with GitHub Actions and OIDC, infrastructure as code, testing, drift and performance monitoring, alerting and retraining.
---

# Module 7 Roadmap: MLOps and Production Operations

**Status: planned.**

## Target architecture

```mermaid
flowchart LR
  dev["PR in GitHub"] --> ci["GitHub Actions CI<br/>pytest · contract checks · bicep lint"]
  ci --> cd["CD (OIDC to Azure)<br/>Bicep deploy · register components"]
  cd --> pipe["Azure ML training pipeline<br/>(scheduled weekly)"]
  gold[("Gold features<br/>Delta")] --> pipe
  pipe --> reg["Model registry"]
  reg -->|"gate: backtest WAPE ≤ champion"| batch["Batch endpoint<br/>weekly forecasts"]
  batch --> fc[("gold/demand_forecast")]
  fc --> mon["Monitoring<br/>data quality · drift · forecast accuracy"]
  mon -->|"alert / retrain condition"| pipe
  mon --> appi["Azure Monitor + App Insights"]
```

## Planned lessons

| # | Lesson | Key content | Official docs |
|---|---|---|---|
| 7.1 | CI for data and ML code | pytest, contract compatibility (`code/data_mesh/contract_compat.py`), linting, data tests | [GitHub Actions for Azure](https://learn.microsoft.com/azure/developer/github/github-actions) |
| 7.2 | OIDC from GitHub to Azure | Workload identity federation, no secrets, least-privilege deployment identity | [Connect from Azure with OpenID Connect](https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect) |
| 7.3 | Infrastructure as code | Bicep modules (from Lab 01's `main.bicep`), what-if in PRs, Terraform comparison | [Bicep](https://learn.microsoft.com/azure/azure-resource-manager/bicep/overview) |
| 7.4 | Training pipelines in production | Schedules, data versioning via Delta versions, lineage to models | [Schedule pipelines](https://learn.microsoft.com/azure/machine-learning/how-to-schedule-pipeline-job) |
| 7.5 | Monitoring and drift | Input data drift, prediction drift, delayed ground truth for forecasts, Azure ML model monitoring | [Model monitoring](https://learn.microsoft.com/azure/machine-learning/concept-model-monitoring) |
| 7.6 | Logging, alerting, incident response | OpenTelemetry, Application Insights, KQL, runbooks | [Azure Monitor](https://learn.microsoft.com/azure/azure-monitor/overview) |
| 7.7 | Retraining policy | Triggers (schedule, drift, accuracy decay), champion/challenger, rollback | — |

## Reuse from what exists

- Tests already in `code/tests/` become the first CI job.
- `contract_compat.py` becomes a required PR check for any change to `code/contracts/`.
- `labs/lab-01-azure-setup/infra/main.bicep` becomes the first IaC module.
