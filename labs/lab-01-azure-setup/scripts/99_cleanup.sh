#!/usr/bin/env bash
# Lab 01 · Cleanup · Deletes the budget and the whole lab resource group.
# Run in: WSL / Ubuntu. IRREVERSIBLE: all data in the lab storage account is lost.
source "$(dirname "$0")/_common.sh"
require_login

if ! az group exists --name "$AZ_RESOURCE_GROUP" | grep -q true; then
  ok "Resource group $AZ_RESOURCE_GROUP does not exist. Nothing to delete."; exit 0
fi

info "Resources that will be deleted:"
az resource list --resource-group "$AZ_RESOURCE_GROUP" --query "[].{name:name, type:type}" -o table
confirm "Permanently delete resource group '$AZ_RESOURCE_GROUP' in '$SUBSCRIPTION_NAME'?"

if [[ -n "${BUDGET_NAME:-}" ]]; then
  az rest --method delete --url "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${AZ_RESOURCE_GROUP}/providers/Microsoft.Consumption/budgets/${BUDGET_NAME}?api-version=2023-05-01" -o none 2>/dev/null \
    && ok "Budget deleted" || warn "Budget not found or already deleted"
fi

az group delete --name "$AZ_RESOURCE_GROUP" --yes
ok "Resource group deleted."
rm -f "$STATE_FILE"
info "Verify: az group exists --name $AZ_RESOURCE_GROUP   (expect: false)"
