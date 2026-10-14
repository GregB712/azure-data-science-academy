---
id: arch-azure-service-map
title: Azure Data & AI Service Map
type: architecture
order: 1
status: available
services: [Microsoft Entra ID, Azure RBAC, Azure Key Vault, Azure Data Lake Storage Gen2, OneLake, Azure Data Factory, Azure Databricks, Microsoft Fabric, Microsoft Purview, Azure Machine Learning, Microsoft Foundry, Azure AI Search, Azure Container Apps, Azure Monitor and Application Insights]
lessons: [m1-azure-fundamentals, m3-lakehouse-medallion]
summary: How the main Azure services relate across identity, storage, processing, governance, ML, GenAI and serving.
---

# Azure Data & AI Service Map

```mermaid
flowchart TB
  subgraph ID["Identity & security (cross-cutting)"]
    entra["Microsoft Entra ID"]
    rbac["Azure RBAC · managed identities"]
    kv["Key Vault"]
  end
  subgraph ING["Ingestion & orchestration"]
    adf["Azure Data Factory"]
    fdf["Fabric Data Factory"]
    eh["Event Hubs"]
  end
  subgraph STO["Storage"]
    adls[("ADLS Gen2")]
    ol[("OneLake")]
    sql[("Azure SQL Database")]
  end
  subgraph PROC["Processing & analytics"]
    dbx["Azure Databricks<br/>+ Unity Catalog"]
    fab["Microsoft Fabric<br/>Lakehouse · Warehouse"]
  end
  subgraph GOV["Catalog & governance"]
    pv["Microsoft Purview"]
  end
  subgraph ML["ML & AI"]
    aml["Azure Machine Learning"]
    fnd["Microsoft Foundry"]
    srch["Azure AI Search"]
  end
  subgraph SERVE["Serving & operations"]
    aca["Container Apps (FastAPI)"]
    mon["Azure Monitor · App Insights"]
    pbi["Power BI"]
  end
  sql --> adf
  eh --> dbx
  adf --> adls
  fdf --> ol
  adls <--> dbx
  ol <--> fab
  adls -. shortcut .-> ol
  dbx --> aml
  adls --> aml
  aml --> aca
  fnd --> aca
  srch --> aca
  fab --> pbi
  pv -. scans .- adls & dbx & fab
  aca --> mon
  entra --- rbac
```

**Reading the map:** solid arrows are data flow; dotted lines are references or governance. Every arrow is authenticated by Entra ID and authorised by RBAC or the platform's own permissions (Unity Catalog, Fabric workspaces).

Read next: [Azure fundamentals](../docs/azure-fundamentals/01-azure-fundamentals.md) · [Service Catalog](../SERVICE_CATALOG.md) · [Decision guide](../ARCHITECTURE_DECISION_GUIDE.md)
