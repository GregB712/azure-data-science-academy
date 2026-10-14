---
id: architecture-decision-guide
title: Architecture Decision Guide
type: reference
order: 3
status: available
tags: [architecture, decisions, comparison, databricks, fabric, synapse, azure-ml, foundry, orchestration]
related: [m3-lakehouse-medallion, m3-data-mesh, service-catalog, glossary]
summary: Decision tables and scenario walkthroughs for choosing storage, table formats, analytics platforms, orchestration, compute, ML platforms, serving options, vector stores and operating models on Azure.
---

# Architecture Decision Guide

Use this guide when you have to pick between Azure options. Every table states the **deciding factors**, not just features. Each decision ends with a **default for this course** so the labs stay consistent. Product facts are linked to Microsoft documentation in the lessons and in the [Service Catalog](SERVICE_CATALOG.md).

**Factors that decide almost everything**

1. **Workload shape**: SQL/BI, data engineering, ML training, online inference, GenAI.
2. **Data volume and velocity**: GBs on one machine vs TBs needing distributed compute; batch vs streaming.
3. **Team skills and size**: Spark/Python engineers vs SQL/Power BI analysts; one team vs many domains.
4. **Governance requirements**: PII, column-level security, lineage, audit, data residency.
5. **Interoperability**: other clouds/engines that must read the same data.
6. **Cost model**: pay-per-use vs reserved capacity; tolerance for idle cost; ops effort.
7. **Existing estate**: what is already deployed and who supports it.

---

## Decision 1: Lake, warehouse or lakehouse?

| If you need… | Lean towards | Why |
|---|---|---|
| Cheap storage of raw, varied data (files, logs, images) for future use | **Data lake** (ADLS Gen2) as the substrate | Any format, cheapest per GB |
| Mostly structured data, SQL analysts, high-concurrency BI, little Python | **Warehouse** (Fabric Warehouse, or SQL warehouse on a lakehouse) | Mature SQL, modelling, security |
| BI *and* data science *and* engineering on the same data, open formats | **Lakehouse** | One copy, many engines, ACID on open files |
| Strict transactional OLTP | Neither: **Azure SQL Database / PostgreSQL / Cosmos DB** | Analytical systems are not OLTP |

**Course default:** lakehouse on Delta Lake with medallion layers; warehouse-style serving for Gold. See [the lakehouse lesson](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md).

---

## Decision 2: Azure Databricks, Microsoft Fabric, both, or Synapse?

| Factor | Azure Databricks | Microsoft Fabric | Azure Synapse Analytics |
|---|---|---|---|
| Delivery model | PaaS workspace in your subscription; compute VMs in your subscription (classic) or Databricks-managed (serverless) | SaaS in your Microsoft 365/Fabric tenant | PaaS workspace |
| Primary strength | Engineering-heavy Spark, ML/MLOps, streaming, fine-grained governance (Unity Catalog), multi-cloud | Unified analytics SaaS around OneLake and Power BI, low-ops, business self-service | Existing SQL pool and Spark estates |
| Storage | Your ADLS Gen2 (managed or external) | OneLake (plus shortcuts to ADLS/S3) | ADLS Gen2 + dedicated pool storage |
| Governance | Unity Catalog (grants, row/column security, lineage, audit) | Workspace/item permissions, OneLake security, domains; Purview integration | Workspace RBAC; Purview |
| BI | Power BI via SQL warehouse; Databricks dashboards | Power BI native (Direct Lake) | Power BI |
| ML | MLflow-native, model serving, feature engineering | Fabric Data Science (MLflow-based), or Azure ML | Azure ML |
| Billing | DBUs + VMs (classic) or serverless DBUs; storage separate | Capacity (F SKU, capacity units) shared by all workloads; pause/resume on Azure F SKUs | Per pool type |
| Ops effort | Medium (clusters, policies; less with serverless) | Low (SaaS), but capacity management matters | Medium |
| Choose when | You have data engineers/ML engineers, large or complex pipelines, need multi-cloud or Unity Catalog's controls | Your organisation is Power BI–centric, wants a single SaaS, predictable capacity cost | You already run it; plan for its evolution |

**Both (hybrid)** is common: Databricks for engineering/ML writing Delta to ADLS Gen2; Fabric for BI and business self-service via shortcuts or Unity Catalog mirroring; Purview across both. Pay attention to duplicate governance (Unity Catalog *and* Fabric permissions) and decide which system is authoritative for access.

**Synapse:** remains supported; Microsoft's new analytics investment is focused on Fabric and Microsoft publishes Synapse→Fabric migration guidance *(inference from product direction; verify for your timeline)*. Don't start greenfield projects on Synapse without a specific reason.

**Course default:** the labs run locally and on ADLS Gen2 first (cheapest), then show both Databricks and Fabric variants. Capstone default: ADLS Gen2 + Delta + Azure ML, with Fabric/Databricks as optional extensions.

---

## Decision 3: Where do the bytes live?

| Option | Use when | Avoid when |
|---|---|---|
| **ADLS Gen2** (storage account with hierarchical namespace) | Analytics data you control: networking, keys, regions, lifecycle; Databricks external/managed storage; Azure ML data | You only use Fabric and want zero storage administration |
| **OneLake** | Data for Fabric workloads; tenant-wide sharing with shortcuts | You need storage-account-level controls (custom firewall, CMK per account) not offered for OneLake |
| **Blob Storage without HNS** | Unstructured app data, ML artefacts, static content, Azurite-based local emulation | Analytics with directory operations or POSIX ACLs |
| **Azure SQL Database** | Small operational datasets, app backends, reference data with constraints | Large analytical scans |

**Course default:** ADLS Gen2 (Lab 01), with OneLake covered in Module 3.

---

## Decision 4: Delta Lake or Apache Iceberg?

| Choose Delta Lake when | Choose Iceberg when |
|---|---|
| You are on Azure Databricks and/or Fabric (both default to Delta) | Key producers/consumers are Iceberg-native (Snowflake, Trino, Flink, AWS) |
| You want the simplest path with Azure tooling | You need Iceberg-specific features such as partition evolution across many engines |
| Python single-node access via `deltalake` (delta-rs) is useful | You already run an Iceberg REST catalog |

Interop narrows the gap: OneLake can expose Delta tables to Iceberg readers and vice versa via metadata virtualisation (with documented limits), and Databricks offers Iceberg compatibility features. **Course default:** Delta Lake.

---

## Decision 5: Single-node Python or Spark?

| Data size / shape | Tool | Where on Azure |
|---|---|---|
| Fits in memory (≲ tens of GB), one machine | pandas, Polars, DuckDB, delta-rs | Laptop/WSL, Azure ML compute instance or job, Fabric Python notebook |
| Larger than memory but single-node friendly (columnar scans) | DuckDB, Polars streaming | Same, bigger VM |
| Hundreds of GB to TB+, wide joins, many files, streaming | **Spark** | Databricks, Fabric Spark, Synapse Spark, Azure ML serverless Spark |

Rule: **don't start a Spark cluster for a 2 GB table.** Startup time and per-node cost outweigh benefits. Many forecasting feature pipelines fit comfortably on one large VM.

**Course default:** pandas + delta-rs locally; PySpark examples shown for Databricks/Fabric.

---

## Decision 6: Orchestration and integration

| Tool | Best at | Not ideal for |
|---|---|---|
| **Azure Data Factory** | Low-code data movement from 90+ connectors, hybrid (self-hosted IR), scheduling across Azure services | Complex transformation logic (delegate to Spark/SQL) |
| **Fabric Data Factory** (pipelines, Dataflow Gen2) | Same patterns natively inside Fabric workspaces | Orchestrating non-Fabric estates broadly |
| **Lakeflow Jobs** (Databricks, formerly Workflows) | Orchestrating notebooks, Python wheels, SQL, declarative pipelines inside Databricks | Moving data from many SaaS sources (use connectors/ADF) |
| **Azure ML pipelines** | Reproducible ML training/inference DAGs with versioned components | General ETL |
| **GitHub Actions / Azure DevOps** | CI/CD: testing, deploying infrastructure, models and pipelines | Production data scheduling |
| **Azure Functions / Logic Apps / Event Grid** | Event-driven glue (file arrived → trigger job) | Long-running heavy compute |

**Course default:** local CLI runs → ADF or Lakeflow Jobs for data (Module 4) → Azure ML pipelines for training (Module 5) → GitHub Actions for CI/CD (Module 7).

---

## Decision 7: Where to do ML?

| Option | Choose when |
|---|---|
| **Azure Machine Learning** | You want a dedicated ML platform: managed compute, environments, components/pipelines, model registry, managed online and batch endpoints, responsible AI tooling; engine-agnostic data access |
| **Databricks ML (MLflow, Model Serving)** | Data and features already live in Databricks with Unity Catalog governance; Spark-scale feature engineering; one platform for data + ML |
| **Fabric Data Science** | Fabric-centric organisations; MLflow-based experiments and models next to OneLake data; simpler scoring patterns (e.g. batch PREDICT) |

All three use **MLflow** concepts, which keeps your tracking code portable. **Course default:** Azure ML (Modules 5–7), reading Gold Delta tables from ADLS Gen2.

---

## Decision 8: Serving predictions

| Pattern | Azure option | When |
|---|---|---|
| Scheduled batch scoring (forecasts per week) | Azure ML **batch endpoints** or pipeline jobs; Databricks job; Fabric notebook | Default for demand forecasting: cheap, simple, scale-to-zero |
| Real-time, managed | Azure ML **managed online endpoints**; Databricks Model Serving | Latency-sensitive predictions with built-in scaling, blue/green |
| Real-time, own API | **FastAPI** on **Azure Container Apps** (scale-to-zero) or App Service | Custom business logic, multiple models, existing FastAPI skills |
| Large-scale, platform control | AKS | You already run Kubernetes and need its control |

Watch out: managed online endpoints bill per instance while deployed, even with no traffic. **Course default:** batch first; an online endpoint or Container Apps FastAPI service as an optional stage.

---

## Decision 9: GenAI models and vector search

| Need | Option | Notes |
|---|---|---|
| Hosted LLMs and embeddings with Azure governance | **Microsoft Foundry** (formerly Azure AI Foundry; Azure OpenAI resources can be upgraded to Foundry resources) | Model catalog with OpenAI and other providers' models, agents, evaluation, tracing |
| Enterprise retrieval: hybrid (keyword + vector) search, semantic ranking, built-in chunking/vectorisation | **Azure AI Search** | Most common RAG retriever on Azure; priced per search unit (always-on) |
| Vectors next to operational JSON data | **Azure Cosmos DB** vector search | When the app's data is already in Cosmos DB |
| Vectors next to relational data | **Azure Database for PostgreSQL** with pgvector | When you already run PostgreSQL |
| Vectors on lakehouse tables | Databricks Vector Search | When data and governance live in Databricks |

**Course default:** Foundry models + Azure AI Search (Module 8), with a local vector-store alternative for development.

---

## Decision 10: Centralised platform or data mesh?

| Signal | Points to |
|---|---|
| One data team, < ~10 people, modest number of domains | Centralised (adopt "mesh-ready" practices) |
| Central backlog is the bottleneck; several domains with their own engineers | Data mesh |
| No platform team or budget for one | Centralised; mesh would fragment |
| Strong regulatory need for consistent controls | Either, but mesh requires governance-as-code to be credible |

See [the data mesh lesson](docs/data-mesh/01-data-mesh.md#38-when-mesh-fits-and-when-it-is-unnecessary-complexity).

---

## Decision 11: Environment separation

| Level | Recommended for real projects | Course labs |
|---|---|---|
| Tenant | One per organisation | Yours |
| Subscription | Separate **prod** and **non-prod** (and sandbox) | One subscription |
| Resource group | Per workload per environment (`rg-forecast-dev`, `rg-forecast-prod`) and per lab | One RG per lab, deleted after |
| Data | Separate storage per environment; no prod PII in dev | Synthetic data only |
| Identity | Separate managed identities per environment; humans read-only in prod | Your user + RG-scoped roles |

---

## Decision 12: Notebook, script, pipeline or container?

| Artefact | Use for | Move on when |
|---|---|---|
| **Notebook** | Exploration, EDA, explaining results, prototyping transformations | Code runs more than once, on a schedule, or is reviewed by others |
| **Python script / package with tests** | Repeatable steps (`generate.py`, `medallion.py`) | It must run on cloud compute or be orchestrated |
| **Pipeline job / component** (Azure ML, Lakeflow, ADF) | Scheduled, multi-step, versioned, observable runs | It must serve requests |
| **Container** (Container Apps, AKS, managed endpoint) | Online serving, custom runtimes | — |

---

## Scenario walkthroughs

These answer the exercise in the [lakehouse lesson](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md#9-independent-exercise). Your reasoning matters more than matching.

**Scenario 1: 40-person retailer, Power BI–savvy analysts, no Spark engineers, 200 GB, predictable cost.**
Recommend **Microsoft Fabric** (Option B): Lakehouse + Warehouse in OneLake, Data Factory pipelines and Dataflow Gen2, Power BI Direct Lake, a small F-SKU capacity sized after a trial. 200 GB doesn't need Spark clusters; capacity billing is predictable. Risks: capacity throttling at peak; plan for scheduling heavy jobs off-peak. Mesh: no; adopt product ownership practices inside workspaces.

**Scenario 2: Global retailer, 80 data engineers, 400 TB, ML-heavy forecasting in 30 countries, Databricks skills, strict column-level PII controls.**
Recommend **Azure Databricks + ADLS Gen2 + Unity Catalog** (Option A), possibly with Azure ML for model operations if the organisation standardises on it, and **Purview** as the enterprise catalog. Data mesh is plausible: many domains and engineers; implement catalog-per-domain, contracts in CI and Purview data products. Watch data residency (regional metastores and storage) and cost governance (cluster policies, serverless, tagging per domain).

**Scenario 3: Databricks for engineering, finance lives in Power BI, wants self-service without copies.**
Recommend **hybrid** (Option C): keep Databricks as the producer of Gold Delta tables; expose them to Fabric via OneLake shortcuts to ADLS Gen2 (or Unity Catalog mirroring) and build Direct Lake semantic models; govern access deliberately in both places and register products in Purview. Avoid exporting copies to a separate warehouse.

---

## Architecture Decision Record (ADR) template

Record significant decisions in `projects/<name>/docs/adr/NNNN-title.md`:

```markdown
# NNNN. <Decision title>
Date: YYYY-MM-DD · Status: proposed | accepted | superseded by NNNN

## Context
What problem, constraints (volume, skills, governance, cost), and forces.

## Options considered
1. Option A: pros / cons / cost estimate
2. Option B: ...

## Decision
What we chose and why, referencing the factors above.

## Consequences
What becomes easier, what becomes harder, what we must monitor, when we revisit.
```
