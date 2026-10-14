#!/usr/bin/env bash
# Lab 01 · Step 1 · Create the resource group, an ADLS Gen2 storage account with
# Entra-only auth, your data-plane role, and bronze/silver/gold file systems.
# Run in: WSL / Ubuntu, after `az login`. Idempotent: safe to re-run.
#
# Billable: the storage account (capacity + transactions). With this lab's few MB
# of data the cost is negligible; see README "Cost and safety".
source "$(dirname "$0")/_common.sh"
require_login

info "Subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"
info "Region: $AZ_LOCATION · Resource group: $AZ_RESOURCE_GROUP"
confirm "Create/update lab resources in this subscription?"

info "Registering resource provider Microsoft.Storage (no-op if already registered)"
az provider register --namespace Microsoft.Storage --wait -o none
ok "Microsoft.Storage registered"

info "Creating resource group"
az group create --name "$AZ_RESOURCE_GROUP" --location "$AZ_LOCATION" --tags "${TAGS[@]}" -o none
ok "Resource group $AZ_RESOURCE_GROUP"

if [[ -z "${STORAGE_ACCOUNT:-}" ]]; then
  for _ in 1 2 3 4 5; do
    candidate="${STORAGE_PREFIX}$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')"
    if [[ "$(az storage account check-name --name "$candidate" --query nameAvailable -o tsv)" == "true" ]]; then
      STORAGE_ACCOUNT="$candidate"; break
    fi
  done
  [[ -n "${STORAGE_ACCOUNT:-}" ]] || fail "Could not find an available storage account name"
  save_state STORAGE_ACCOUNT "$STORAGE_ACCOUNT"
fi
info "Storage account: $STORAGE_ACCOUNT"

az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$AZ_RESOURCE_GROUP" \
  --location "$AZ_LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --hns true \
  --allow-shared-key-access false \
  --allow-blob-public-access false \
  --min-tls-version TLS1_2 \
  --https-only true \
  --tags "${TAGS[@]}" \
  -o none
ok "Storage account created (HNS on, shared key off, public blob access off, TLS 1.2+)"

STORAGE_ID="$(az storage account show -n "$STORAGE_ACCOUNT" -g "$AZ_RESOURCE_GROUP" --query id -o tsv)"
save_state STORAGE_ID "$STORAGE_ID"

info "Granting you 'Storage Blob Data Contributor' on the storage account (data plane)"
ME_ID="$(az ad signed-in-user show --query id -o tsv)"
existing="$(az role assignment list --assignee "$ME_ID" --role "Storage Blob Data Contributor" \
            --scope "$STORAGE_ID" --query "length(@)" -o tsv)"
if [[ "$existing" == "0" ]]; then
  az role assignment create --assignee-object-id "$ME_ID" --assignee-principal-type User \
    --role "Storage Blob Data Contributor" --scope "$STORAGE_ID" -o none
  ok "Role assigned (propagation can take a few minutes)"
else
  ok "Role already assigned"
fi

info "Creating file systems bronze, silver, gold (retries while the role propagates)"
for fs in bronze silver gold; do
  for attempt in $(seq 1 20); do
    if [[ "$(az storage fs exists -n "$fs" --account-name "$STORAGE_ACCOUNT" --auth-mode login --query exists -o tsv 2>/dev/null)" == "true" ]]; then
      ok "file system '$fs' exists"; break
    fi
    if az storage fs create -n "$fs" --account-name "$STORAGE_ACCOUNT" --auth-mode login -o none 2>/dev/null; then
      ok "file system '$fs' created"; break
    fi
    (( attempt == 20 )) && fail "Could not create '$fs' after waiting. Check the role assignment."
    warn "not authorised yet for '$fs' (attempt $attempt/20); waiting 15s for RBAC propagation"
    sleep 15
  done
done

echo
ok "Done. Next: scripts/02_create_budget.sh, then python python/verify_setup.py"
