---
id: m5-m6-azure-ml-roadmap
title: "Modules 5-6 Roadmap: Azure Machine Learning and Model Deployment"
module: 5
type: module-overview
order: 0
status: planned
tags: [azure-ml, mlflow, compute, environments, components, endpoints, batch-inference, fastapi]
prerequisites: [m1-azure-fundamentals, m3-lakehouse-medallion]
related: [m7-mlops-roadmap, retail-forecasting-capstone, architecture-decision-guide]
summary: Planned lessons and labs for training, tracking, registering and deploying the demand forecasting model with Azure Machine Learning, building on the Gold feature table from Module 3.
---

# Modules 5-6 Roadmap: Azure Machine Learning and Model Deployment

**Status: planned.** This page is the design for the next build phase, so you can see where the curriculum goes and extend it consistently. Nothing below is implemented yet unless linked.

## Starting point you already have

- Gold feature table `gold/weekly_demand_features` with a data contract ([contract](../../code/contracts/forecasting.demand_features.v1.yaml)), produced locally or on ADLS Gen2 ([lakehouse lesson](../lakehouse/01-lake-warehouse-lakehouse-medallion.md)).
- A storage account with Entra-only auth ([Lab 01](../../labs/lab-01-azure-setup/README.md)).

## Module 5 lessons (planned)

| # | Lesson | Key content | Official docs |
|---|---|---|---|
| 5.1 | Workspace anatomy and costs | Workspace + dependent resources (storage, Key Vault, Container Registry, Application Insights); managed identity of the workspace; what bills when idle | [What is Azure ML](https://learn.microsoft.com/azure/machine-learning/overview-what-is-azure-machine-learning) |
| 5.2 | Compute choices | Compute instance (idle shutdown!), compute clusters (min nodes = 0), serverless compute, quotas | [Compute targets](https://learn.microsoft.com/azure/machine-learning/concept-compute-target) |
| 5.3 | Environments and reproducibility | Curated vs custom environments, conda/Docker, pinning | [Environments](https://learn.microsoft.com/azure/machine-learning/concept-environments) |
| 5.4 | Data assets and datastores | URI file/folder vs MLTable, versioning, reading Delta from ADLS Gen2 with identity | [Data concepts](https://learn.microsoft.com/azure/machine-learning/concept-data) |
| 5.5 | Command jobs with SDK v2 and CLI v2 | `azure-ai-ml` `MLClient`, `command()`, YAML jobs, inputs/outputs | [SDK v2 overview](https://learn.microsoft.com/azure/machine-learning/concept-v2) |
| 5.6 | MLflow tracking | Autolog vs manual logging, metrics/artefacts, comparing runs | [MLflow and Azure ML](https://learn.microsoft.com/azure/machine-learning/concept-mlflow) |
| 5.7 | Sweeps | Hyperparameter search for LightGBM, early termination, cost control | [Hyperparameter tuning](https://learn.microsoft.com/azure/machine-learning/how-to-tune-hyperparameters) |
| 5.8 | Components and pipelines | Reusable components: validate → features → train → evaluate | [Pipelines](https://learn.microsoft.com/azure/machine-learning/concept-ml-pipelines) |

**Lab 05 (planned): model training.** Local baseline first (LightGBM with temporal backtesting on the Gold table, metrics WAPE/MASE/bias), then the same script as an Azure ML command job on serverless compute, tracked with MLflow, followed by a 3-step pipeline. Local alternative: run MLflow locally with `mlflow ui`.

## Module 6 lessons (planned)

| # | Lesson | Key content | Official docs |
|---|---|---|---|
| 6.1 | Model registry | Registering MLflow models, versions, tags, stages via tags/aliases | [Model management](https://learn.microsoft.com/azure/machine-learning/concept-model-management-and-deployment) |
| 6.2 | Batch endpoints | Weekly forecasts at scale, scale-to-zero clusters, outputs to ADLS Gen2 | [Batch endpoints](https://learn.microsoft.com/azure/machine-learning/concept-endpoints-batch) |
| 6.3 | Managed online endpoints | Deployments, blue/green traffic, autoscale, auth (key vs Entra token) | [Online endpoints](https://learn.microsoft.com/azure/machine-learning/concept-endpoints-online) |
| 6.4 | FastAPI forecast service | FastAPI on Azure Container Apps serving precomputed forecasts + on-demand scoring; managed identity | [Container Apps](https://learn.microsoft.com/azure/container-apps/overview) |
| 6.5 | Release criteria | Backtest gates, champion/challenger, input/output validation with the data contract | — |

**Lab 06 (planned): deployment.** Batch endpoint producing `gold/demand_forecast` (the planned `supply-chain.demand-forecast` data product), optional online endpoint, then delete endpoints.

## Cost warnings to carry into these modules

- Compute instances bill until stopped: always configure idle shutdown.
- Compute clusters must use `min_instances=0`.
- Managed online endpoints bill per instance while deployed, even with zero traffic: delete after the lab.
- The workspace creates a Container Registry on first custom environment build; it bills daily.
- GPU quota is often zero on new subscriptions; the forecasting labs are designed to run on CPU.

## How to build these lessons

Use the [lesson template](../_templates/LESSON_TEMPLATE.md) and [lab template](../_templates/LAB_TEMPLATE.md), add the files under this folder and `labs/`, set `status: available` in the frontmatter and in [curriculum.json](../../curriculum.json), and run the checks in [EXTENDING.md](../EXTENDING.md).
