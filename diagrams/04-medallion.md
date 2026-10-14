---
id: arch-medallion
title: Medallion Architecture (Retail Example)
type: architecture
order: 4
status: available
services: [Delta Lake, Azure Data Lake Storage Gen2, Azure Databricks, Microsoft Fabric]
lessons: [m3-lakehouse-medallion, m3-data-mesh]
summary: The Bronze, Silver and Gold tables the course pipeline actually builds, with quality gates between layers.
---

# Medallion Architecture (Retail Example)

These are the exact tables produced by [`code/lakehouse_local/medallion.py`](../code/lakehouse_local/medallion.py).

```mermaid
flowchart LR
  r1["raw/pos_sales/*.csv"] --> b1
  r2["raw/stores.csv · products.json · calendar.csv"] --> b2
  subgraph Bronze
    b1["pos_sales<br/>text + _source_file + _ingested_at<br/>append, incremental by file"]
    b2["stores · products · calendar<br/>snapshot overwrite"]
  end
  subgraph Silver
    s1["sales<br/>typed · deduped · MERGE on key<br/>partitioned by sales_year"]
    q["sales_quarantine<br/>_reject_reason"]
    s2["stores · products · calendar (typed)"]
  end
  subgraph Gold
    g1["daily_sales_store_category"]
    g2["weekly_demand_features<br/>lags 1, 2, 52 · rolling mean 4"]
  end
  b1 -->|"contract: sales.pos_sales v1<br/>gate: quarantine ≤ 1%"| s1
  b1 -.->|rejected rows| q
  b2 --> s2
  s1 & s2 --> g1
  s1 & s2 -->|"contract: demand_features v1"| g2
```

Medallion is a **data organisation pattern**, not a product feature.

Read next: [Lakehouse lesson §3.7](../docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md#37-the-medallion-architecture)
