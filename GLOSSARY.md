---
id: glossary
title: Glossary
type: reference
order: 1
status: available
tags: [glossary, reference, terminology]
related: [service-catalog, architecture-decision-guide]
summary: Azure, data platform and MLOps terminology, each term labelled by kind (Azure service, capability, pattern, open source, concept) so products are never confused with architectures.
---

# Glossary

Every term carries a **Kind** label: *Azure service*, *Azure capability* (feature of a service or the platform), *Pattern* (architecture or organisational approach, not a product), *Open source*, or *Concept*. The dashboard's glossary search parses the `### Term` headings and the `Kind` line.

### ABFS / abfss://
- **Kind:** Concept
- The Azure Blob File System driver and URI scheme for ADLS Gen2 (`abfss://<container>@<account>.dfs.core.windows.net/<path>`); `abfss` is the TLS variant. Used by Spark, delta-rs, adlfs. See [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md).

### ACID transactions
- **Kind:** Concept
- Atomicity, consistency, isolation, durability. Table formats like Delta Lake bring ACID commits to files in object storage.

### Access connector (Azure Databricks)
- **Kind:** Azure capability
- An Azure resource holding a managed identity that Unity Catalog uses to access ADLS Gen2 on behalf of Databricks, without keys.

### Availability zone
- **Kind:** Azure capability
- Physically separate datacenter groups within a region; zone-redundant services survive a zone outage.

### Azure CLI (`az`)
- **Kind:** Azure service (tooling)
- Cross-platform command-line interface for Azure Resource Manager and many data planes. Install inside WSL. See [Lab 01](labs/lab-01-azure-setup/README.md).

### Azure Resource Manager (ARM)
- **Kind:** Azure service
- The control-plane API (`management.azure.com`) behind the portal, CLI, SDKs, Bicep and Terraform.

### Batch endpoint
- **Kind:** Azure capability
- Azure ML endpoint that runs asynchronous scoring jobs over large inputs on compute clusters that scale to zero.

### Bicep
- **Kind:** Azure service (tooling)
- Declarative IaC language for Azure; compiles to ARM templates.

### Bronze / Silver / Gold
- **Kind:** Pattern
- Layers of the medallion architecture: raw replayable data, validated and conformed data, consumption-ready products. See [Lakehouse](docs/lakehouse/01-lake-warehouse-lakehouse-medallion.md#37-the-medallion-architecture).

### Capacity (Fabric)
- **Kind:** Azure capability
- A pool of compute (capacity units, CU) purchased as an F SKU (or trial) that all Fabric workloads in assigned workspaces share.

### CDC (change data capture)
- **Kind:** Concept
- Capturing inserts, updates and deletes from a source database as a stream of changes, enabling incremental ingestion.

### Change data feed (Delta)
- **Kind:** Open source
- Optional Delta Lake feature recording row-level changes per table version, for incremental downstream processing.

### Control plane / data plane
- **Kind:** Concept
- Control plane manages resources (ARM, roles like Owner/Contributor). Data plane accesses the contents (blobs, secrets, model inference; roles like Storage Blob Data Reader). See [Azure fundamentals](docs/azure-fundamentals/01-azure-fundamentals.md#32-control-plane-vs-data-plane-the-single-most-important-idea).

### Data contract
- **Kind:** Pattern
- Machine-readable agreement between a data producer and consumers: schema, semantics, quality guarantees, SLAs, ownership, classification, version. See [Data mesh](docs/data-mesh/01-data-mesh.md#33-data-contracts).

### Data lake
- **Kind:** Pattern
- Storage of data in files in object storage with schema-on-read. On Azure usually implemented with ADLS Gen2 or OneLake.

### Data lakehouse
- **Kind:** Pattern
- Architecture combining open files in a lake with a transactional table format, catalog and governance so BI, engineering and ML share one copy. Not a product (but Fabric has an item *named* Lakehouse).

### Data mesh
- **Kind:** Pattern
- Socio-technical approach with four principles: domain ownership, data as a product, self-serve platform, federated computational governance. Not an Azure service. See [Data mesh](docs/data-mesh/01-data-mesh.md).

### Data observability
- **Kind:** Concept
- Continuous monitoring of data health: freshness, volume, schema, distribution, lineage-aware alerting.

### Data product
- **Kind:** Pattern (and an object in Microsoft Purview Unified Catalog)
- Independently owned, discoverable, contract-backed unit of data with code, metadata and infrastructure. Purview also uses "data product" for a curated group of assets with a use case.

### Data warehouse
- **Kind:** Pattern (and product category)
- Schema-on-write analytical database optimised for SQL and BI; on Azure e.g. Fabric Warehouse, Synapse dedicated SQL pools.

### DBU (Databricks Unit)
- **Kind:** Concept
- Normalised unit of Databricks processing capability billed per second, priced by workload type and tier.

### Delta Lake
- **Kind:** Open source
- Open table format with a transaction log over Parquet files. Default in Azure Databricks and Fabric. See [Service Catalog](SERVICE_CATALOG.md#delta-lake).

### Deletion vectors
- **Kind:** Open source
- Delta Lake feature marking rows as deleted without rewriting data files, making updates/deletes cheaper.

### DefaultAzureCredential
- **Kind:** Azure capability (SDK)
- Credential in `azure-identity` that tries a chain of credential types; convenient for development, replace with a specific credential in production.

### Direct Lake
- **Kind:** Azure capability
- Power BI storage mode in Fabric that reads Delta tables in OneLake directly, without import copies.

### Domain (Fabric)
- **Kind:** Azure capability
- Fabric grouping of workspaces by business area with delegated domain admins and settings; supports mesh-style organisation.

### Domain-driven design (bounded context)
- **Kind:** Concept
- Software design approach that splits a system into contexts with their own models and language; data mesh domains build on it.

### ELT / ETL
- **Kind:** Concept
- Extract-transform-load (transform before loading the target) vs extract-load-transform (land raw, transform inside the platform). Lakehouses favour ELT.

### Endpoint (managed online)
- **Kind:** Azure capability
- Azure ML managed HTTPS endpoint hosting one or more deployments with autoscaling and traffic splitting; bills per instance while deployed.

### Entra ID
- **Kind:** Azure service
- Microsoft's identity platform, formerly Azure Active Directory.

### Federated computational governance
- **Kind:** Pattern
- Data mesh principle: global policies agreed by domain and central representatives, enforced automatically by the platform.

### Foundry (Microsoft Foundry)
- **Kind:** Azure service
- Microsoft's AI app and agent platform, formerly Azure AI Studio and Azure AI Foundry. Azure AI services are now called Foundry Tools.

### Governance domain (Purview)
- **Kind:** Azure capability
- Purview Unified Catalog boundary that aligns governance (glossary, data products, policies) with the organisation.

### Hierarchical namespace (HNS)
- **Kind:** Azure capability
- Storage account option that turns Blob Storage into ADLS Gen2 with real directories and ACLs.

### Idempotency
- **Kind:** Concept
- Running a job twice yields the same result as once. Achieved with MERGE on keys and tracking processed inputs.

### Infrastructure as code (IaC)
- **Kind:** Concept
- Declaring infrastructure in versioned files (Bicep, Terraform) and deploying through automation.

### Key Vault
- **Kind:** Azure service
- Managed secrets, keys and certificates store.

### Landing zone
- **Kind:** Pattern
- Cloud Adoption Framework concept: a pre-configured, governed environment (subscriptions, networking, identity, policy) into which workloads deploy.

### Lineage
- **Kind:** Concept
- Record of how data flows from sources through transformations to tables, reports and models.

### Managed identity
- **Kind:** Azure capability
- Entra identity for an Azure resource with Azure-managed credentials.

### Medallion architecture
- **Kind:** Pattern
- Data organisation pattern using Bronze/Silver/Gold layers. Not a product feature.

### MERGE (upsert)
- **Kind:** Concept
- Statement that updates matching rows and inserts new ones based on a key; the backbone of idempotent Silver tables.

### Mirroring (Fabric)
- **Kind:** Azure capability
- Continuous, managed replication of external databases (e.g. Azure SQL Database, Cosmos DB, Snowflake) into OneLake as Delta tables.

### MLflow
- **Kind:** Open source
- ML lifecycle tooling (tracking, models, registry) supported by Azure ML, Databricks and Fabric.

### OneLake
- **Kind:** Azure service
- Fabric's single tenant-wide data lake built on ADLS Gen2 technology.

### OneLake shortcut
- **Kind:** Azure capability
- A reference in OneLake to data stored elsewhere (OneLake, ADLS Gen2, S3, …) that avoids copying.

### Open Data Contract Standard (ODCS)
- **Kind:** Open source
- Linux Foundation (Bitol) standard YAML format for data contracts. The course uses a simplified form.

### Optimistic concurrency
- **Kind:** Concept
- Writers proceed without locks and check for conflicts at commit time; used by Delta and Iceberg.

### Partitioning
- **Kind:** Concept
- Physically grouping data files by column values (e.g. year) so queries can skip irrelevant files.

### Private endpoint
- **Kind:** Azure capability
- Private IP in your VNet for a PaaS resource, via Azure Private Link.

### Purview Unified Catalog
- **Kind:** Azure capability
- Microsoft Purview's catalog experience with governance domains, data products, glossary terms, data quality, OKRs and access requests.

### RAG (retrieval-augmented generation)
- **Kind:** Pattern
- Grounding LLM responses in retrieved documents or data, typically via vector or hybrid search.

### RBAC (Azure role-based access control)
- **Kind:** Azure capability
- Authorization model: principal + role + scope.

### Resource group
- **Kind:** Azure capability
- Container for resources with a shared lifecycle; deleting it deletes its resources.

### Resource provider
- **Kind:** Azure capability
- Service namespace (e.g. `Microsoft.Storage`) that must be registered in a subscription before use.

### Schema enforcement / schema evolution
- **Kind:** Concept
- Rejecting writes that don't match a table's schema / explicitly allowing compatible schema changes (e.g. adding columns).

### Schema-on-read / schema-on-write
- **Kind:** Concept
- Applying structure when querying (lakes) vs when loading (warehouses).

### Separation of storage and compute
- **Kind:** Pattern
- Storing data independently of engines, so compute scales, stops and is billed separately.

### Service principal
- **Kind:** Azure capability
- The identity of an application in a tenant; managed identities are a special kind.

### SQL analytics endpoint
- **Kind:** Azure capability
- Read-only T-SQL endpoint automatically created for each Fabric Lakehouse.

### SQL warehouse (Databricks)
- **Kind:** Azure capability
- Databricks compute resource for SQL workloads over lakehouse tables. Not the same as a Fabric Warehouse item.

### Subscription
- **Kind:** Azure capability
- Billing, quota and access boundary containing resource groups.

### Tenant
- **Kind:** Concept
- A dedicated Microsoft Entra ID instance for an organisation. A Fabric tenant has exactly one OneLake.

### Time travel
- **Kind:** Concept
- Querying a table as of an earlier version or timestamp; limited by file retention (VACUUM).

### Unity Catalog
- **Kind:** Azure capability (Azure Databricks)
- Databricks governance layer for data and AI with a `catalog.schema.object` namespace, grants, lineage and audit.

### VACUUM
- **Kind:** Open source
- Delta operation that deletes data files no longer referenced by versions within the retention period.

### Workload identity federation
- **Kind:** Azure capability
- Trusting an external OIDC token (e.g. GitHub Actions) to obtain Entra tokens without stored secrets.

### WSL 2
- **Kind:** Concept
- Windows Subsystem for Linux, version 2; runs a real Linux kernel. The course's command environment.
