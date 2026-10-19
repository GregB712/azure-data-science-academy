---
id: service-catalog
title: Service Catalog
type: reference
order: 2
status: available
tags: [services, reference, azure]
related: [architecture-decision-guide, glossary]
summary: One entry per Azure service, open-source technology or capability used in the course, with what it is, its role in a data/AI architecture, cost model, gotchas, lessons and official docs.
---

# Service Catalog

Each entry follows the same fields so the dashboard's **Service explorer** can parse and filter them. **Kind** tells you whether something is a native Azure service, a native capability of the platform, open-source technology integrated with Azure, or third-party tooling. Patterns (lakehouse, medallion, data mesh) are *not* services and live in the [Glossary](GLOSSARY.md).

Prices are deliberately described as cost *models*; always confirm current rates with the [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator/).

## Identity, security and cost management

### Microsoft Entra ID
- **Category:** Identity & security
- **Kind:** Native service
- **What it is:** Microsoft's cloud identity directory (formerly Azure Active Directory): users, groups, app registrations, service principals, managed identities, conditional access.
- **Role in the architecture:** Every human and workload authenticates here; groups are the unit of access for data products and environments.
- **Typical DS/AI uses:** `az login` for development, groups for workspace and catalog access, OIDC federation for CI.
- **Cost model:** Free tier included with Azure; premium features (conditional access, PIM) require Entra ID P1/P2 licences.
- **Watch out:** Multiple tenants on one account lead to resources created in the wrong place; check `az account show`.
- **Lessons:** [Azure fundamentals](docs/azure-fundamentals/01-azure-fundamentals.md)
- **Docs:** https://learn.microsoft.com/entra/fundamentals/whatis

### Azure RBAC
- **Category:** Identity & security
- **Kind:** Native capability
- **What it is:** Role-based access control for Azure resources: role definition + principal + scope, inherited downward.
- **Role in the architecture:** Separates control-plane rights (Owner/Contributor) from data-plane rights (Storage Blob Data *, Key Vault Secrets *).
- **Typical DS/AI uses:** Granting a training job's managed identity read access to Gold data; giving yourself data access in a lab.
- **Cost model:** Free.
- **Watch out:** Owner ≠ data access; assignments take minutes to propagate.
- **Lessons:** [Azure fundamentals](docs/azure-fundamentals/01-azure-fundamentals.md), [Lab 01](labs/lab-01-azure-setup/README.md)
- **Docs:** https://learn.microsoft.com/azure/role-based-access-control/overview

### Managed identities
- **Category:** Identity & security
- **Kind:** Native capability
- **What it is:** Entra identities for Azure resources whose credentials Azure manages; system-assigned (lifecycle of the resource) or user-assigned (independent resource).
- **Role in the architecture:** How deployed code (Azure ML compute, Container Apps, Functions, Databricks access connectors) reaches data and secrets without secrets.
- **Typical DS/AI uses:** Batch scoring job reading Gold tables and writing forecasts; FastAPI service calling Foundry models.
- **Cost model:** Free.
- **Watch out:** Use `ManagedIdentityCredential` explicitly in deployed code; pass the client ID for user-assigned identities.
- **Lessons:** [Azure fundamentals](docs/azure-fundamentals/01-azure-fundamentals.md)
- **Docs:** https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview

### Azure Key Vault
- **Category:** Identity & security
- **Kind:** Native service
- **What it is:** Managed store for secrets, keys and certificates with RBAC, auditing, soft delete and purge protection.
- **Role in the architecture:** Holds the secrets you could not eliminate (third-party API keys, legacy connection strings) and customer-managed keys.
- **Typical DS/AI uses:** API keys for external data providers; Databricks secret scopes backed by Key Vault.
- **Cost model:** Per operation (and per key for HSM-backed keys); very cheap at lab scale.
- **Watch out:** Soft-deleted vaults keep the name reserved; purge if you need to reuse it. Prefer RBAC permission model.
- **Lessons:** [Azure fundamentals](docs/azure-fundamentals/01-azure-fundamentals.md)
- **Docs:** https://learn.microsoft.com/azure/key-vault/general/overview

### Azure Policy
- **Category:** Governance & cost
- **Kind:** Native service
- **What it is:** Rules evaluated against resource configurations (audit, deny, modify, deploy-if-not-exists), assigned at management group, subscription or RG scope.
- **Role in the architecture:** Computational governance for infrastructure: allowed regions, required tags, no public storage, private endpoints required.
- **Typical DS/AI uses:** Enforcing that every ML workspace has public network access disabled in prod.
- **Cost model:** Free for Azure resources.
- **Watch out:** Enterprise policies can block lab commands; read the error's policy name.
- **Lessons:** Module 9 (planned)
- **Docs:** https://learn.microsoft.com/azure/governance/policy/overview

### Microsoft Cost Management
- **Category:** Governance & cost
- **Kind:** Native service
- **What it is:** Cost analysis, budgets, alerts, exports and recommendations for Azure spending.
- **Role in the architecture:** Visibility and alerting per subscription, RG and tag (domain, product, environment).
- **Typical DS/AI uses:** Budget alerts on lab RGs; cost per data product via tags.
- **Cost model:** Free for Azure usage.
- **Watch out:** Budgets alert but never stop spending; cost data lags 8–24 hours.
- **Lessons:** [Azure fundamentals](docs/azure-fundamentals/01-azure-fundamentals.md), [Lab 01](labs/lab-01-azure-setup/README.md)
- **Docs:** https://learn.microsoft.com/azure/cost-management-billing/costs/overview-cost-management

## Storage

### Azure Blob Storage
- **Category:** Storage
- **Kind:** Native service
- **What it is:** Object storage in a storage account: containers of blobs, access tiers (hot, cool, cold, archive), lifecycle policies.
- **Role in the architecture:** Unstructured data, model artefacts, raw files; the substrate for ADLS Gen2.
- **Typical DS/AI uses:** Azure ML default datastore, document corpora for RAG.
- **Cost model:** GB-month by tier and redundancy + per-operation transactions + egress.
- **Watch out:** Disable shared-key and public access; cooler tiers charge more for reads and have minimum retention.
- **Lessons:** [Azure fundamentals](docs/azure-fundamentals/01-azure-fundamentals.md), Module 2 (planned)
- **Docs:** https://learn.microsoft.com/azure/storage/blobs/storage-blobs-introduction

### Azure Data Lake Storage Gen2
- **Category:** Storage
- **Kind:** Native service
- **What it is:** Blob Storage with the **hierarchical namespace** enabled: real directories, atomic renames, POSIX-style ACLs, `dfs` endpoint (`abfss://`).
- **Role in the architecture:** Primary analytics storage for lakehouses on Databricks, Synapse, Azure ML; can be referenced from Fabric via shortcuts.
- **Typical DS/AI uses:** Bronze/Silver/Gold Delta tables; training data; batch forecast outputs.
- **Cost model:** Blob pricing for the HNS account type (capacity + transactions, with some HNS-specific metadata/operation charges).
- **Watch out:** HNS must be chosen at creation (or via an upgrade process); ACLs and RBAC interact (RBAC evaluated first).
- **Lessons:** [Lab 01](labs/lab-01-azure-setup/README.md), [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md)
- **Docs:** https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-introduction

### OneLake
- **Category:** Storage
- **Kind:** Native service (part of Microsoft Fabric)
- **What it is:** Fabric's single, tenant-wide data lake built on ADLS Gen2 technology; workspaces appear as containers and items as folders; tabular data stored as Delta Parquet.
- **Role in the architecture:** The storage layer for every Fabric workload; shortcuts unify data from ADLS Gen2, S3 and other OneLake locations without copying.
- **Typical DS/AI uses:** Fabric notebooks and Data Science experiments over Lakehouse tables; Power BI Direct Lake.
- **Cost model:** Storage billed per GB with Fabric; compute comes from the Fabric capacity.
- **Watch out:** One per tenant; security is Fabric workspace/item based, not Azure RBAC on a storage account.
- **Lessons:** [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md)
- **Docs:** https://learn.microsoft.com/fabric/onelake/onelake-overview

### Azure SQL Database
- **Category:** Storage
- **Kind:** Native service
- **What it is:** Managed SQL Server engine (PaaS) with serverless and provisioned tiers.
- **Role in the architecture:** Operational/reference data, app backends, small marts; a source for CDC and Fabric mirroring.
- **Typical DS/AI uses:** Storing forecast overrides from planners; feature lookups for small online services.
- **Cost model:** vCore or DTU per hour (serverless bills per second of use with auto-pause) + storage.
- **Watch out:** Use Entra authentication; serverless auto-pause has resume latency.
- **Lessons:** Module 2 (planned)
- **Docs:** https://learn.microsoft.com/azure/azure-sql/database/sql-database-paas-overview

## Data integration and streaming

### Azure Data Factory
- **Category:** Data integration
- **Kind:** Native service
- **What it is:** Managed data integration: pipelines, copy activity with many connectors, mapping data flows, triggers, self-hosted integration runtime for on-premises sources.
- **Role in the architecture:** Ingests source data into Bronze and orchestrates Databricks/SQL/Azure ML activities.
- **Typical DS/AI uses:** Nightly POS extract copy; triggering a scoring pipeline after Gold refresh.
- **Cost model:** Per activity run, per data integration unit-hour for copies, per vCore-hour for data flows.
- **Watch out:** Data flows spin up Spark clusters (cost and startup time); keep heavy logic in Spark/SQL engines.
- **Lessons:** Module 4 (planned)
- **Docs:** https://learn.microsoft.com/azure/data-factory/introduction

### Fabric Data Factory
- **Category:** Data integration
- **Kind:** Native service (part of Microsoft Fabric)
- **What it is:** Data Factory experience inside Fabric: pipelines, Dataflow Gen2 (Power Query), copy jobs, mirroring.
- **Role in the architecture:** Ingestion and orchestration for Fabric lakehouses and warehouses.
- **Typical DS/AI uses:** Loading Bronze tables in a Fabric Lakehouse; scheduling notebooks.
- **Cost model:** Consumes Fabric capacity units.
- **Watch out:** Not identical to Azure Data Factory feature-for-feature; check connector and feature availability.
- **Lessons:** Module 4 (planned)
- **Docs:** https://learn.microsoft.com/fabric/data-factory/data-factory-overview

### Azure Event Hubs
- **Category:** Streaming
- **Kind:** Native service
- **What it is:** Managed event streaming with a Kafka-compatible endpoint; partitions, consumer groups, capture to storage.
- **Role in the architecture:** Ingestion of high-volume events (clickstream, IoT, POS events) into streaming pipelines and Bronze.
- **Typical DS/AI uses:** Real-time sales events for intraday demand sensing.
- **Cost model:** Throughput/processing units or capacity units per hour + ingress events.
- **Watch out:** Provisioned throughput bills while idle.
- **Lessons:** Module 4 (planned)
- **Docs:** https://learn.microsoft.com/azure/event-hubs/event-hubs-about

## Analytics platforms

### Azure Databricks
- **Category:** Analytics platform
- **Kind:** Native service (first-party Azure service built on the Databricks platform)
- **What it is:** Managed Spark-based lakehouse platform: notebooks, jobs, SQL warehouses, declarative pipelines, MLflow, model serving, Unity Catalog governance.
- **Role in the architecture:** Data engineering and ML engine over Delta tables in ADLS Gen2.
- **Typical DS/AI uses:** Feature pipelines with PySpark, large-scale training, batch scoring, streaming.
- **Cost model:** Databricks Units (DBU) by workload type + underlying VMs for classic compute; serverless bills DBUs only.
- **Watch out:** All-purpose clusters without auto-termination; product names changed in 2025 (Lakeflow), check current docs.
- **Lessons:** [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md), [Data mesh](docs/data-mesh/01-data-mesh.md)
- **Docs:** https://learn.microsoft.com/azure/databricks/introduction/

### Unity Catalog
- **Category:** Catalog & governance
- **Kind:** Native capability (Azure Databricks)
- **What it is:** Governance layer for data and AI in Databricks: `catalog.schema.object` namespace, grants, row filters and column masks, lineage, audit, managed and external tables and volumes.
- **Role in the architecture:** Platform-level access control and lineage; catalogs per domain in a mesh.
- **Typical DS/AI uses:** Governing feature tables and registered models; lineage from source to model.
- **Cost model:** Included with Databricks.
- **Watch out:** Enabled automatically for workspaces created after 9 Nov 2023; older workspaces may still use the legacy Hive metastore.
- **Lessons:** [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md), [Data mesh](docs/data-mesh/01-data-mesh.md)
- **Docs:** https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/

### Microsoft Fabric
- **Category:** Analytics platform
- **Kind:** Native service (SaaS)
- **What it is:** Unified SaaS analytics platform: Data Factory, Data Engineering (Spark), Data Warehouse, Data Science, Real-Time Intelligence, Power BI, all over OneLake, governed by workspaces and domains.
- **Role in the architecture:** End-to-end analytics for BI-centric organisations; consumption layer in hybrid designs.
- **Typical DS/AI uses:** Lakehouse notebooks, MLflow experiments, Direct Lake reports on forecasts.
- **Cost model:** Capacity (F SKUs, capacity units) billed per hour while running, plus OneLake storage. Free trials are available; check current trial terms.
- **Watch out:** Capacity is shared by all workloads (throttling); pause unused F-SKU capacities.
- **Lessons:** [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md), [Data mesh](docs/data-mesh/01-data-mesh.md)
- **Docs:** https://learn.microsoft.com/fabric/fundamentals/microsoft-fabric-overview

### Fabric Lakehouse
- **Category:** Analytics platform
- **Kind:** Native service (Fabric item)
- **What it is:** A Fabric item with a `Files` area (any files) and a `Tables` area (Delta tables), plus an automatically created read-only SQL analytics endpoint.
- **Role in the architecture:** Where Fabric medallion layers live (often one Lakehouse per layer or per domain).
- **Typical DS/AI uses:** Spark feature engineering and ML on Delta tables.
- **Cost model:** Fabric capacity + OneLake storage.
- **Watch out:** The SQL analytics endpoint is read-only; use a Warehouse for T-SQL writes.
- **Lessons:** [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md)
- **Docs:** https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview

### Fabric Warehouse
- **Category:** Analytics platform
- **Kind:** Native service (Fabric item)
- **What it is:** A Fabric item providing a full T-SQL data warehouse (DDL/DML, transactions) storing data as Delta in OneLake.
- **Role in the architecture:** SQL-first Gold serving and dimensional models.
- **Typical DS/AI uses:** Star schemas for forecast accuracy reporting.
- **Cost model:** Fabric capacity + OneLake storage.
- **Watch out:** Not the same thing as a Databricks *SQL warehouse* (which is compute only).
- **Lessons:** [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md)
- **Docs:** https://learn.microsoft.com/fabric/data-warehouse/data-warehousing

### Azure Synapse Analytics
- **Category:** Analytics platform
- **Kind:** Native service
- **What it is:** Analytics workspace combining serverless and dedicated SQL pools, Spark pools and pipelines.
- **Role in the architecture:** Found in existing estates; migration candidate towards Fabric.
- **Typical DS/AI uses:** Serverless SQL over Parquet; existing dedicated pool warehouses.
- **Cost model:** Dedicated pools per DWU-hour (pause when idle); serverless per TB processed; Spark per vCore-hour.
- **Watch out:** Dedicated SQL pools bill while running even if idle.
- **Lessons:** [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md)
- **Docs:** https://learn.microsoft.com/azure/synapse-analytics/overview-what-is

### Microsoft Purview
- **Category:** Catalog & governance
- **Kind:** Native service (SaaS)
- **What it is:** Data governance, security and compliance suite. Its Unified Catalog provides governance domains, data products, glossary terms, data quality, OKRs, access requests and health management; the Data Map scans sources and captures lineage.
- **Role in the architecture:** Enterprise-wide catalog across ADLS, Databricks, Fabric, SQL and more; the discovery and governance plane of a data mesh.
- **Typical DS/AI uses:** Finding trusted training data; requesting access to a data product; classification of PII.
- **Cost model:** Varies by capability (data map, data quality, scanning); check current Purview pricing and licensing.
- **Watch out:** Catalog quality depends on curation; automate product registration from code.
- **Lessons:** [Data mesh](docs/data-mesh/01-data-mesh.md), [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md)
- **Docs:** https://learn.microsoft.com/purview/unified-catalog

## Machine learning and AI

### Azure Machine Learning
- **Category:** Machine learning
- **Kind:** Native service
- **What it is:** ML platform: workspaces, compute instances and clusters, serverless compute, environments, data assets, components and pipelines, MLflow tracking, model registry, managed online and batch endpoints, responsible AI tools.
- **Role in the architecture:** Training, tracking, registering and serving models from Gold data.
- **Typical DS/AI uses:** LightGBM forecasting training pipeline, hyperparameter sweeps, weekly batch forecasts.
- **Cost model:** The workspace is free; you pay for compute (per VM-hour), associated storage, container registry, Key Vault and Application Insights; endpoints bill per instance while deployed.
- **Watch out:** Compute instances run until stopped (use idle shutdown); low default GPU quota.
- **Lessons:** [Workspace, compute and costs](docs/azure-machine-learning/01-workspace-compute-and-costs.md), [Jobs, data and tracking](docs/azure-machine-learning/02-jobs-data-and-tracking.md), [Sweeps, components and pipelines](docs/azure-machine-learning/03-sweeps-components-and-pipelines.md), [Lab 05](labs/lab-05-model-training/README.md); Modules 6–7 (planned)
- **Docs:** https://learn.microsoft.com/azure/machine-learning/overview-what-is-azure-machine-learning

### Microsoft Foundry
- **Category:** Generative AI
- **Kind:** Native service
- **What it is:** Microsoft's platform for building AI apps and agents (formerly Azure AI Studio / Azure AI Foundry): a Foundry resource with projects, a model catalog including OpenAI and other providers' models, Foundry Agent Service, tools, evaluation, tracing and governance. Azure OpenAI resources can be upgraded to Foundry resources.
- **Role in the architecture:** Model hosting and inference (chat, embeddings), agent runtime, evaluation for GenAI services.
- **Typical DS/AI uses:** RAG over product documentation; an agent that explains forecasts to planners.
- **Cost model:** Mostly per token (standard deployments) or provisioned throughput units; tools and search billed separately.
- **Watch out:** Model and feature availability varies by region and deployment type; names changed recently (Azure AI services are now "Foundry Tools"), so match docs to the portal you use (Foundry vs Foundry classic).
- **Lessons:** Module 8 (planned), [roadmap](docs/generative-ai/README.md)
- **Docs:** https://learn.microsoft.com/azure/ai-foundry/what-is-azure-ai-foundry

### Azure AI Search
- **Category:** Generative AI
- **Kind:** Native service
- **What it is:** Search service with full-text, vector and hybrid retrieval, semantic ranking, indexers and integrated vectorisation.
- **Role in the architecture:** Retriever for RAG; enterprise search over documents and data.
- **Typical DS/AI uses:** Indexing chunked documents with embeddings; hybrid search with filters.
- **Cost model:** Per search unit-hour by tier (always on); semantic ranker and AI enrichment billed additionally.
- **Watch out:** Even an idle service bills hourly; the Free tier is limited and not for production.
- **Lessons:** Module 8 (planned)
- **Docs:** https://learn.microsoft.com/azure/search/search-what-is-azure-search

## Application hosting and operations

### Azure Container Apps
- **Category:** Application hosting
- **Kind:** Native service
- **What it is:** Serverless container hosting with autoscaling (including scale to zero), revisions, ingress, jobs and Dapr integration.
- **Role in the architecture:** Hosts FastAPI inference and RAG services; scheduled container jobs.
- **Typical DS/AI uses:** Forecast API reading precomputed forecasts; RAG chat backend.
- **Cost model:** Consumption: per vCPU-second and GiB-second plus requests, with a monthly free grant; dedicated workload profiles billed per node.
- **Watch out:** Min replicas > 0 means continuous billing; cold starts with scale to zero.
- **Lessons:** Module 6 and 8 (planned)
- **Docs:** https://learn.microsoft.com/azure/container-apps/overview

### Azure Container Registry
- **Category:** Application hosting
- **Kind:** Native service
- **What it is:** Private registry for container images and OCI artefacts.
- **Role in the architecture:** Stores images for Azure ML environments, Container Apps and AKS.
- **Typical DS/AI uses:** Custom training and inference images.
- **Cost model:** Per day by tier (Basic/Standard/Premium) + storage.
- **Watch out:** Azure ML creates one per workspace on first image build; it keeps billing after experiments end.
- **Lessons:** [Jobs, data and tracking](docs/azure-machine-learning/02-jobs-data-and-tracking.md), [Lab 05](labs/lab-05-model-training/README.md); Module 6 (planned)
- **Docs:** https://learn.microsoft.com/azure/container-registry/container-registry-intro

### Azure Monitor and Application Insights
- **Category:** Observability
- **Kind:** Native service
- **What it is:** Metrics, logs (Log Analytics workspaces, KQL), alerts, and application performance monitoring with OpenTelemetry-based Application Insights.
- **Role in the architecture:** Observability for pipelines, endpoints and AI apps; alerting on failures, latency, drift signals.
- **Typical DS/AI uses:** Tracing a FastAPI forecasting service; alerting when a batch job fails.
- **Cost model:** Mostly per GB ingested and retained in Log Analytics.
- **Watch out:** Verbose logging can cost more than the service you monitor; set sampling and retention.
- **Lessons:** Module 7 (planned)
- **Docs:** https://learn.microsoft.com/azure/azure-monitor/overview

### Bicep
- **Category:** Infrastructure as code
- **Kind:** Native tooling
- **What it is:** Microsoft's declarative language for Azure Resource Manager deployments, transpiled to ARM JSON.
- **Role in the architecture:** Reproducible environments: storage, identities, role assignments, workspaces.
- **Typical DS/AI uses:** Lab 01's storage account and role assignment; per-domain platform modules.
- **Cost model:** Free.
- **Watch out:** Role assignment names must be deterministic GUIDs (`guid()`), or redeployments fail.
- **Lessons:** [Lab 01](labs/lab-01-azure-setup/README.md), Module 7 (planned)
- **Docs:** https://learn.microsoft.com/azure/azure-resource-manager/bicep/overview

### GitHub Actions
- **Category:** Infrastructure as code
- **Kind:** Third-party tooling (integrates with Azure)
- **What it is:** CI/CD workflows in GitHub; authenticates to Azure with OIDC workload identity federation.
- **Role in the architecture:** Tests, contract checks, IaC deployment, model training/deployment triggers.
- **Typical DS/AI uses:** Running `pytest` and `contract_compat.py` on every PR.
- **Cost model:** Free minutes for public repos; per-minute for private beyond the allowance.
- **Watch out:** Use OIDC, never stored client secrets.
- **Lessons:** Module 7 (planned)
- **Docs:** https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect

## Open formats and open-source

### Delta Lake
- **Category:** Open formats & OSS
- **Kind:** Open source (integrated with Azure)
- **What it is:** Open table format: Parquet data files + `_delta_log` transaction log, giving ACID, schema enforcement/evolution, time travel, MERGE.
- **Role in the architecture:** Default table format for Databricks and Fabric; the course's table format.
- **Typical DS/AI uses:** Reproducible training sets via table versions; idempotent Silver upserts.
- **Cost model:** Free (storage and compute billed by the hosting services).
- **Watch out:** VACUUM removes files needed for time travel beyond the retention period.
- **Lessons:** [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md)
- **Docs:** https://docs.delta.io/latest/index.html

### Apache Iceberg
- **Category:** Open formats & OSS
- **Kind:** Open source (integrated with Azure)
- **What it is:** Open table format with snapshot-based metadata trees and a catalog (often REST) tracking the current table state.
- **Role in the architecture:** Interoperability with Iceberg-native engines; supported in OneLake via metadata virtualisation and in Databricks via compatibility features.
- **Typical DS/AI uses:** Sharing tables with Snowflake or Trino users.
- **Cost model:** Free.
- **Watch out:** Check conversion limits (Parquet only, supported versions) when relying on Delta↔Iceberg virtualisation.
- **Lessons:** [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md)
- **Docs:** https://iceberg.apache.org/docs/latest/

### MLflow
- **Category:** Open formats & OSS
- **Kind:** Open source (integrated with Azure)
- **What it is:** Open-source ML lifecycle tooling: tracking, models, registry, evaluation, GenAI tracing.
- **Role in the architecture:** Common tracking/model format across Azure ML, Databricks and Fabric.
- **Typical DS/AI uses:** Logging forecasting metrics and models; comparing runs.
- **Cost model:** Free; the backing workspace bills.
- **Watch out:** Feature parity differs between hosted MLflow implementations.
- **Lessons:** [Jobs, data and tracking](docs/azure-machine-learning/02-jobs-data-and-tracking.md), [Lab 05](labs/lab-05-model-training/README.md)
- **Docs:** https://learn.microsoft.com/azure/machine-learning/concept-mlflow

### LightGBM
- **Category:** Open formats & OSS
- **Kind:** Open source (integrated with Azure)
- **What it is:** Gradient-boosting framework for tabular data, with native categorical handling and objectives (including Tweedie/Poisson) suited to retail demand counts.
- **Role in the architecture:** The course's demand forecasting model, trained locally and as an Azure ML job on the Gold feature table.
- **Typical DS/AI uses:** Weekly product-store demand forecasting; hyperparameter sweeps over learning rate and tree size.
- **Cost model:** Free; runs on CPU (no GPU required for the course).
- **Watch out:** Squared-error objectives chase a few high-volume series; Tweedie/MAE objectives fit demand better. MASE < 1 means it beats the naive baseline.
- **Lessons:** [Jobs, data and tracking](docs/azure-machine-learning/02-jobs-data-and-tracking.md), [Lab 05](labs/lab-05-model-training/README.md)
- **Docs:** https://lightgbm.readthedocs.io/en/latest/
