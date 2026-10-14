---
id: m2-m4-data-engineering-roadmap
title: "Modules 2 and 4 Roadmap: Cloud Storage, Data Access and Pipelines"
module: 2
type: module-overview
order: 0
status: planned
tags: [blob-storage, adls-gen2, adlfs, pyarrow, azure-sql, data-factory, fabric-data-factory, databricks-jobs, pyspark, cdc, etl, elt]
prerequisites: [m1-azure-fundamentals]
related: [m3-lakehouse-medallion, lab-01-azure-setup, architecture-decision-guide]
summary: Planned lessons for storage access patterns from Python and SQL (Module 2) and for orchestration, Spark processing, incremental ingestion/CDC and pipeline testing (Module 4).
---

# Modules 2 and 4 Roadmap: Cloud Storage, Data Access and Pipelines

**Status: planned.** Module 3's lakehouse lesson already contains the core medallion pipeline; these modules widen the storage and orchestration skills around it.

## Module 2: Cloud Storage and Data Access (planned)

| # | Lesson | Key content | Official docs |
|---|---|---|---|
| 2.1 | Blob vs ADLS Gen2 | Hierarchical namespace, `blob` vs `dfs` endpoints, access tiers, lifecycle policies | [ADLS Gen2 intro](https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-introduction) |
| 2.2 | RBAC and ACLs | How RBAC and POSIX ACLs are evaluated together; per-directory access for domains | [Access control model](https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-access-control-model) |
| 2.3 | Python access | `azure-storage-file-datalake`, `adlfs`/`fsspec` with pandas and PyArrow, delta-rs with `abfss://` | [Python SDK for ADLS Gen2](https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-directory-file-acl-python) |
| 2.4 | File formats and layout | CSV vs JSON vs Parquet, compression, partitioned datasets, file sizing | [Best practices](https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-best-practices) |
| 2.5 | Azure SQL Database | Serverless tier, Entra authentication from Python (`pyodbc`/`mssql-python`), when to use it | [Azure SQL Database](https://learn.microsoft.com/azure/azure-sql/database/sql-database-paas-overview) |

**Lab 02 (planned):** upload the synthetic retail raw files to `bronze`, read Parquet/Delta with pandas through `adlfs` using `DefaultAzureCredential`, compare partitioned layouts, and load reference data into a serverless Azure SQL Database with auto-pause.

## Module 4: Data Pipelines and Scalable Processing (planned)

| # | Lesson | Key content |
|---|---|---|
| 4.1 | ETL vs ELT, batch vs streaming | Where transformations run and why lakehouses favour ELT |
| 4.2 | Azure Data Factory and Fabric Data Factory | Pipelines, copy activity, triggers, parameters, retries, monitoring |
| 4.3 | Databricks Jobs and PySpark | Porting `medallion.py` to PySpark, job clusters vs serverless, Lakeflow Declarative Pipelines expectations |
| 4.4 | Incremental ingestion and CDC | Watermarks, Auto Loader, Delta change data feed, SCD type 2 |
| 4.5 | Testing pipelines | Unit tests for transformations, contract tests, data diffing, idempotency tests |
| 4.6 | Choosing tools | Applying the [decision guide](../../ARCHITECTURE_DECISION_GUIDE.md#decision-6-orchestration-and-integration) |

**Lab 04 (planned):** orchestrate Bronze→Silver→Gold with ADF (or a Databricks job) on a schedule, replace full Silver reprocessing with change-data-feed-based incremental processing, and add failure alerts.
