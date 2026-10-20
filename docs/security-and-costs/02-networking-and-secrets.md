---
id: m9-networking-secrets
title: "Network Isolation and Secrets: Private Endpoints and Key Vault"
module: 9
type: lesson
order: 2
duration: 2h reading + 1h hands-on
level: advanced
status: available
tags: [private-endpoint, private-link, private-dns, managed-vnet, key-vault, managed-identity, customer-managed-keys]
prerequisites: [m9-landing-zones, m1-azure-fundamentals]
related: [m9-governance-finops, m5-azure-ml-workspace, m8-rag-search]
summary: Take the platform off the public internet with private endpoints and private DNS, isolate Azure ML, Foundry and AI Search, and manage the few remaining secrets in Key Vault with RBAC, rotation and customer-managed keys.
---

# Network Isolation and Secrets: Private Endpoints and Key Vault

> **Where this fits.** The course's labs use public endpoints protected by identity - cheap and simple. Enterprises add a network layer so traffic never traverses the public internet. This lesson is that layer: private endpoints + DNS, and the small amount of secret management that remains once everything authenticates by identity.

## 1. Lesson overview and learning objectives

By the end you can:

- Explain **private endpoints**, **Private Link** and the **private DNS** that makes them work.
- Take storage, Azure ML, Foundry and AI Search off the public internet.
- Use the **Azure ML managed VNet** for compute.
- Manage secrets in **Key Vault** with RBAC, rotation and customer-managed keys - and need fewer secrets.

## 2. Prerequisites

| Need | Why | From |
|---|---|---|
| Networking basics (VNet, NSG, private endpoint) | This lesson deepens them | [Module 1](../azure-fundamentals/01-azure-fundamentals.md#37-networking-fundamentals-just-enough-for-now) |
| Managed identities + Key Vault | The identity-first model | [Module 1](../azure-fundamentals/01-azure-fundamentals.md) |
| The platform resources | What we isolate | Modules 2, 5, 6, 8 |

## 3. Core concepts

### 3.1 Private endpoints and Private Link

A **private endpoint** is a network interface with a **private IP in your VNet** that maps to a specific PaaS resource (a storage account, workspace, Foundry resource, search service). Combined with **disabling public network access** on that resource, traffic reaches it over **Private Link** and never traverses the public internet ([Private endpoints](https://learn.microsoft.com/azure/private-link/private-endpoint-overview)).

```mermaid
flowchart LR
  subgraph vnet["Your VNet"]
    client["Compute / Container App"] --> pe["Private endpoint<br/>10.0.1.4"]
  end
  pe -. Private Link .-> svc["Storage / Azure ML / Foundry / AI Search<br/>(public access disabled)"]
  dns["Private DNS zone<br/>privatelink.dfs.core.windows.net"] -. resolves acct.dfs... to 10.0.1.4 .- client
```

### 3.2 Private DNS is the part people miss

A private endpoint only helps if the service's hostname **resolves to the private IP**. That needs a **private DNS zone** (e.g. `privatelink.blob.core.windows.net`, `privatelink.dfs.core.windows.net`, `privatelink.search.windows.net`, `privatelink.api.azureml.ms`) linked to the VNet, with an A record for the resource. Get the DNS wrong and you get public-IP resolution or name-resolution failures - the most common private-endpoint problem. In a landing zone, central DNS is usually provided; standalone, you create and link the zones yourself.

### 3.3 Isolating the platform's services

| Service | Isolation |
|---|---|
| **Storage / ADLS Gen2** | Private endpoints on `blob` and `dfs`; `publicNetworkAccess=Disabled`; shared-key off (Module 1) |
| **Azure ML** | A **managed virtual network** for the workspace; compute (incl. serverless) runs inside it, with "no public IP"; private endpoint to the workspace ([managed VNet](https://learn.microsoft.com/azure/machine-learning/how-to-managed-network)) |
| **Microsoft Foundry / Azure OpenAI** | Private endpoint; disable public access; the AI service reaches it over the VNet |
| **Azure AI Search** | Private endpoint; disable public access; a shared private link for the indexer to reach private data |
| **Key Vault** | Private endpoint; RBAC; firewall |

The Azure ML **managed VNet** is the easy win: Azure manages the network for the workspace and its compute, so you get isolation without hand-building VNets/NSGs for every compute target.

### 3.4 Key Vault and needing fewer secrets

Identity-first design (Module 1) removes most secrets - Storage, Azure SQL, Foundry, AI Search all accept Entra tokens. What remains (third-party API keys, legacy credentials) goes in **Key Vault**:

- **RBAC mode** (not legacy access policies); grant the workload's managed identity **Key Vault Secrets User**; read at startup.
- **Rotation**: rotate secrets on a schedule; apps re-read, so avoid caching forever.
- **Customer-managed keys (CMK)**: encrypt service data with a key you control in Key Vault (for storage, Azure ML, etc.) when compliance requires it - you manage the key lifecycle.
- **Soft-delete/purge protection** on so a deleted vault/secret is recoverable.

([Key Vault overview](https://learn.microsoft.com/azure/key-vault/general/overview))

## 4. Architecture diagrams

See 3.1 (private endpoint + DNS) above - the core picture.

## 5. Azure service mapping

| Need | Service / capability | Type | Where |
|---|---|---|---|
| Private connectivity | Private endpoint + Private Link | Native capability | §3.1 |
| Name resolution | Private DNS zones | Native capability | §3.2 |
| Workspace network isolation | Azure ML managed VNet | Native capability | §3.3 |
| Secrets | Key Vault (RBAC, rotation, CMK) | Native service | §3.4 |
| Keyless auth | Managed identities + Entra | Native capability | [Module 1](../azure-fundamentals/01-azure-fundamentals.md) |

## 6. Step-by-step implementation

```bash
# WSL - disable public access and add a private endpoint to a storage account (dfs)
az storage account update -n <acct> -g <rg> --public-network-access Disabled
az network private-endpoint create -g <rg> --name pe-<acct>-dfs \
  --vnet-name <vnet> --subnet <subnet> \
  --private-connection-resource-id <storage-resource-id> --group-id dfs \
  --connection-name c-<acct>-dfs
# then create/link the private DNS zone privatelink.dfs.core.windows.net and the A record
```

Azure ML managed VNet is configured on the workspace (`--managed-network allow_internet_outbound` or `allow_only_approved_outbound`); Foundry/AI Search follow the same private-endpoint + DNS pattern. Keep the footprint minimal in a lab and delete after (private endpoints and premium SKUs add fixed monthly cost).

## 7. Complete runnable code

This lesson is network/secret configuration (needs Azure); there is no local runnable artifact. The identity-first access it builds on is in [`medallion.py`](../../code/lakehouse_local/medallion.py) (keyless `abfss://`) and [`forecast_service`](../../code/forecast_service/) (managed-identity data access).

## 8. Expected outputs and verification

- `nslookup <acct>.dfs.core.windows.net` from inside the VNet resolves to the **private IP**; from outside it fails or returns no public route. `az storage account show --query publicNetworkAccess` returns `Disabled`.
- **Not run against a subscription in the build**; commands and the DNS requirement follow the Private Link docs.

## 9. Independent exercise

1. List every private DNS zone the platform needs (storage blob+dfs, Azure ML, Foundry, AI Search, Key Vault) and what breaks if each is missing.
2. Decide which platform secrets remain after identity-first design, and how each is stored and rotated.
3. When is a customer-managed key worth the operational overhead, and what do you now own?

## 10. Common errors and troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Resolves to a public IP inside the VNet | Missing/unlinked private DNS zone or A record | Create the `privatelink.*` zone, link the VNet, add the record |
| Private endpoint created but still 403/timeout | Public access not disabled, or wrong subnet/NSG | Disable public access; check subnet and NSG rules |
| Azure ML compute can't reach storage | Managed VNet outbound rule missing | Add an approved outbound rule / private endpoint for the datastore |
| Indexer can't read private data | No shared private link | Configure a shared private link for AI Search |
| App can't read a secret | Identity lacks Key Vault Secrets User (RBAC mode) | Grant the role; wait for propagation |

## 11. Security and cost considerations

- **Security**: private endpoints + disabled public access + identity = defence in depth; least-privilege RBAC on Key Vault; CMK and purge protection where compliance needs them.
- **Cost**: private endpoints bill a **fixed hourly charge each** plus data processing, and some isolation features need premium SKUs - a real standing cost. Use the smallest viable footprint in labs and delete promptly; in production it's a deliberate security/cost trade-off.

## 12. Production best practices

- **Private endpoints + public access disabled** for storage, workspace, Foundry, AI Search, Key Vault.
- **Get private DNS right** - it's the usual failure point.
- **Azure ML managed VNet** for compute isolation without hand-built networking.
- **Identity over secrets**; Key Vault (RBAC) for the rest, rotated; CMK only when required.
- Treat private networking as a **deliberate cost**; don't leave lab endpoints running.

## 13. Knowledge check

1. What two things together take a PaaS resource off the public internet?
2. Why is private DNS essential, and what's the symptom when it's wrong?
3. What does the Azure ML managed VNet give you over building VNets yourself?
4. After identity-first design, what still belongs in Key Vault, and in which mode?

<details>
<summary>Answers</summary>

1. A **private endpoint** (private IP in your VNet via Private Link) **and disabling public network access** on the resource.
2. The hostname must resolve to the **private IP**; without the `privatelink.*` zone/record it resolves to a public IP or fails - the most common private-endpoint problem.
3. Azure manages the workspace's network and its compute (incl. serverless, no public IP), so you get isolation without hand-building VNets/NSGs per compute target.
4. Secrets with **no identity-based alternative** (third-party API keys, legacy creds), stored in **RBAC mode** with the workload's managed identity as Key Vault Secrets User, rotated.

</details>

## 14. Official documentation and further reading

- [Private endpoints](https://learn.microsoft.com/azure/private-link/private-endpoint-overview) · [Private Link + DNS](https://learn.microsoft.com/azure/private-link/private-endpoint-dns)
- [Azure ML managed VNet](https://learn.microsoft.com/azure/machine-learning/how-to-managed-network) · [Secure a workspace](https://learn.microsoft.com/azure/machine-learning/how-to-secure-workspace-vnet)
- [Key Vault overview](https://learn.microsoft.com/azure/key-vault/general/overview) · [Customer-managed keys](https://learn.microsoft.com/azure/storage/common/customer-managed-keys-overview)

**Next:** [Governance, Responsible AI and FinOps](03-governance-responsible-ai-finops.md).
