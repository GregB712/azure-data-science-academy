---
id: m9-security-roadmap
title: "Module 9 Roadmap: Enterprise Architecture, Security and Governance"
module: 9
type: module-overview
order: 0
status: planned
tags: [landing-zones, private-endpoints, key-vault, purview, responsible-ai, tagging, cost-management, azure-policy]
prerequisites: [m1-azure-fundamentals, m3-data-mesh]
related: [m7-mlops-roadmap, architecture-decision-guide]
summary: Planned lessons on landing zones, environment separation, network isolation, secrets, Purview classification and lineage, responsible AI governance, and cost allocation.
---

# Module 9 Roadmap: Enterprise Architecture, Security and Governance

**Status: planned.**

| # | Lesson | Key content | Official docs |
|---|---|---|---|
| 9.1 | Landing zones | Cloud Adoption Framework landing zones, management groups, platform vs application landing zones | [What is a landing zone?](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/) |
| 9.2 | Environment separation | Subscriptions per environment, identities per environment, promotion via CI/CD | [Decision 11](../../ARCHITECTURE_DECISION_GUIDE.md#decision-11-environment-separation) |
| 9.3 | Network isolation | Private endpoints and DNS for storage, Azure ML managed VNet, Foundry, AI Search | [Private endpoints](https://learn.microsoft.com/azure/private-link/private-endpoint-overview) |
| 9.4 | Secrets and keys | Key Vault RBAC, rotation, customer-managed keys | [Key Vault](https://learn.microsoft.com/azure/key-vault/general/overview) |
| 9.5 | Purview in practice | Scanning, classification, lineage, data products, access requests | [Unified Catalog](https://learn.microsoft.com/purview/unified-catalog) |
| 9.6 | Policy as code | Azure Policy for tags, regions, public access; data policies in Unity Catalog | [Azure Policy](https://learn.microsoft.com/azure/governance/policy/overview) |
| 9.7 | Responsible AI and model governance | Model documentation, fairness and error analysis for forecasts, approval workflows | [Responsible AI in Azure ML](https://learn.microsoft.com/azure/machine-learning/concept-responsible-ai) |
| 9.8 | FinOps for data and AI | Tagging strategy, cost allocation per domain/product, reservations and savings plans, idle-resource detection | [Cost Management](https://learn.microsoft.com/azure/cost-management-billing/costs/overview-cost-management) |

Cost note: private endpoints, Firewall and premium SKUs add fixed monthly costs. Labs in this module will default to *audit*-mode policies and show private networking with the smallest viable footprint, deleted immediately after.
