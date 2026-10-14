---
id: arch-data-mesh
title: Data Mesh on Azure
type: architecture
order: 2
status: available
services: [Microsoft Purview, Azure Databricks, Unity Catalog, Microsoft Fabric, OneLake, Microsoft Entra ID, Azure Data Lake Storage Gen2]
lessons: [m3-data-mesh]
summary: Domains publishing governed data products on a shared self-serve platform with federated governance.
---

# Data Mesh on Azure

```mermaid
flowchart TB
  subgraph Domains["Domains own data products"]
    direction LR
    s["Sales<br/>pos-transactions · store-directory"]
    sc["Supply chain<br/>product-catalog · demand-features · demand-forecast"]
    f["Finance<br/>revenue-reconciliation"]
    c["Customer analytics<br/>loyalty-segments"]
  end
  s -->|contract v1| sc
  s --> f
  s --> c
  subgraph Platform["Self-serve platform"]
    p1["IaC templates · CI checks · storage/catalog per domain"]
  end
  subgraph Gov["Federated computational governance"]
    g1["Purview: governance domains, data products, DQ, access requests"]
    g2["Unity Catalog / Fabric: grants, masks, shortcuts"]
    g3["Policies as code: registry.py, contract_compat.py, Azure Policy"]
  end
  Platform -.-> Domains
  Gov -.-> Domains
```

Data mesh is an **operating model and architecture**, not an Azure service. The services provide the building blocks; contracts, templates and policy-as-code are yours to build.

Read next: [Data mesh lesson](../docs/data-mesh/01-data-mesh.md)
