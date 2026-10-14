---
id: arch-ml-lifecycle
title: Azure ML Lifecycle
type: architecture
order: 5
status: planned
services: [Azure Machine Learning, MLflow, Azure Data Lake Storage Gen2, Azure Container Registry, Azure Monitor and Application Insights]
lessons: [m5-m6-azure-ml-roadmap]
summary: From Gold features to a registered model and batch forecasts with Azure Machine Learning (design for Modules 5-6).
---

# Azure ML Lifecycle (design, Modules 5-6)

```mermaid
flowchart LR
  gold[("Gold features<br/>Delta v N")] --> asset["Data asset<br/>(versioned)"]
  asset --> job["Command job / pipeline<br/>environment + compute"]
  job --> mlflow["MLflow run<br/>params · metrics · artefacts"]
  mlflow --> eval{"Backtest gate<br/>WAPE ≤ champion?"}
  eval -- yes --> reg["Registered model vN"]
  eval -- no --> stop["Keep champion"]
  reg --> be["Batch endpoint<br/>scale to zero"]
  reg --> oe["Online endpoint (optional)"]
  be --> fc[("gold/demand_forecast")]
```

Status: **planned**. See the [Modules 5-6 roadmap](../docs/azure-machine-learning/README.md).
