---
id: arch-lakehouse
title: Lakehouse Reference Architectures
type: architecture
order: 3
status: available
services: [Azure Data Lake Storage Gen2, Azure Databricks, Unity Catalog, Microsoft Fabric, OneLake, Fabric Lakehouse, Fabric Warehouse, Delta Lake, Apache Iceberg, Microsoft Purview]
lessons: [m3-lakehouse-medallion]
summary: Databricks on ADLS Gen2, Fabric on OneLake, and the hybrid that shares one copy of data between them.
---

# Lakehouse Reference Architectures

```mermaid
flowchart LR
  subgraph A["Option A · Databricks"]
    a1[("ADLS Gen2<br/>Delta tables")] <--> a2["Databricks<br/>jobs · SQL warehouse"]
    a3["Unity Catalog"] -.- a1
  end
  subgraph B["Option B · Fabric"]
    b1[("OneLake<br/>Delta tables")] <--> b2["Lakehouse · Warehouse<br/>notebooks · pipelines"]
    b2 --> b3["Power BI Direct Lake"]
  end
  a1 -. "OneLake shortcut (Option C: hybrid)" .-> b1
  pv["Purview"] -.- A & B
```

| | Option A | Option B | Option C |
|---|---|---|---|
| Best for | Engineering/ML-heavy teams | BI-centric, low-ops | Both audiences, one copy |
| Storage | Your ADLS Gen2 | OneLake | ADLS Gen2 + shortcuts |
| Governance | Unity Catalog | Fabric + Purview | Both; decide which is authoritative |

Read next: [Lakehouse lesson](../docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md) · [Decision 2](../ARCHITECTURE_DECISION_GUIDE.md#decision-2-azure-databricks-microsoft-fabric-both-or-synapse)
