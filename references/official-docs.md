---
id: official-docs
title: Official Documentation Index
type: reference
order: 5
status: available
tags: [documentation, microsoft-learn, references]
related: [service-catalog, glossary]
summary: Curated Microsoft Learn and project documentation links by topic, with notes on what each is good for.
---

# Official Documentation Index

Lessons cite sources inline next to the claims they support. This page is the curated jumping-off list. Links were assembled in October 2026; Microsoft Learn URLs occasionally move, so search the title if one redirects.

## Fundamentals and identity
- [Organize your Azure resources (CAF)](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-setup-guide/organize-resources): hierarchy and naming decisions.
- [Azure RBAC overview](https://learn.microsoft.com/azure/role-based-access-control/overview) and [built-in roles](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles).
- [Credential chains in Azure Identity for Python](https://learn.microsoft.com/azure/developer/python/sdk/authentication/credential-chains): `DefaultAzureCredential` order and production guidance.
- [Managed identities](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview).
- [Install Azure CLI on Linux](https://learn.microsoft.com/cli/azure/install-azure-cli-linux).

## Costs
- [Create and manage budgets](https://learn.microsoft.com/azure/cost-management-billing/costs/tutorial-acm-create-budgets): alerts only; data latency.
- [Azure Retail Prices API](https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices) and [pricing calculator](https://azure.microsoft.com/pricing/calculator/).
- [Azure free account](https://azure.microsoft.com/pricing/free-services).

## Storage
- [ADLS Gen2 introduction](https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-introduction) · [best practices](https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-best-practices) · [access control model](https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-access-control-model).
- [Prevent Shared Key authorization](https://learn.microsoft.com/azure/storage/common/shared-key-authorization-prevent).

## Lakehouse platforms
- Databricks: [lakehouse](https://learn.microsoft.com/azure/databricks/lakehouse/), [medallion](https://learn.microsoft.com/azure/databricks/lakehouse/medallion), [Delta Lake](https://learn.microsoft.com/azure/databricks/delta/), [Unity Catalog](https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/).
- Fabric: [overview](https://learn.microsoft.com/fabric/fundamentals/microsoft-fabric-overview), [OneLake](https://learn.microsoft.com/fabric/onelake/onelake-overview), [shortcuts](https://learn.microsoft.com/fabric/onelake/onelake-shortcuts), [Iceberg in OneLake](https://learn.microsoft.com/fabric/onelake/onelake-iceberg-tables), [domains](https://learn.microsoft.com/fabric/governance/domains), [Lakehouse](https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview), [Warehouse](https://learn.microsoft.com/fabric/data-warehouse/data-warehousing).
- [Azure Synapse Analytics overview](https://learn.microsoft.com/azure/synapse-analytics/overview-what-is).
- Open formats: [Delta Lake](https://docs.delta.io/latest/index.html), [Apache Iceberg](https://iceberg.apache.org/docs/latest/), [delta-rs](https://delta-io.github.io/delta-rs/).

## Governance and data mesh
- [Purview Unified Catalog](https://learn.microsoft.com/purview/unified-catalog) · [governance domains](https://learn.microsoft.com/purview/concept-governance-domain).
- [What is a data mesh? (CAF)](https://learn.microsoft.com/azure/cloud-adoption-framework/scenarios/cloud-scale-analytics/architectures/what-is-data-mesh).
- [Data Mesh Principles and Logical Architecture](https://martinfowler.com/articles/data-mesh-principles.html) (Zhamak Dehghani).
- [Open Data Contract Standard](https://bitol-io.github.io/open-data-contract-standard/).

## ML, MLOps and GenAI
- [What is Azure Machine Learning?](https://learn.microsoft.com/azure/machine-learning/overview-what-is-azure-machine-learning) · [MLflow and Azure ML](https://learn.microsoft.com/azure/machine-learning/concept-mlflow) · [online endpoints](https://learn.microsoft.com/azure/machine-learning/concept-endpoints-online) · [batch endpoints](https://learn.microsoft.com/azure/machine-learning/concept-endpoints-batch).
- [GitHub Actions OIDC to Azure](https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect) · [Bicep](https://learn.microsoft.com/azure/azure-resource-manager/bicep/overview).
- [What is Microsoft Foundry?](https://learn.microsoft.com/azure/ai-foundry/what-is-azure-ai-foundry) · [Azure AI Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search).
- [Azure Architecture Center: data guide](https://learn.microsoft.com/azure/architecture/data-guide/).
