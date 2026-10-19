#!/usr/bin/env bash
# Deploy the FastAPI forecast service to Azure Container Apps with a managed
# identity that reads the lakehouse by identity (no keys). Scale-to-zero keeps
# idle cost near nothing. Not executed in the course build.
#
# Where: WSL, signed in with `az login`. Edit the variables, then run.
set -euo pipefail

RG=rg-adsa-ml
LOCATION=westeurope
ACR=craadsa$RANDOM              # globally unique
ENVNAME=cae-adsa
APP=demand-forecast-api
ACCOUNT="<yourStorageAccount>"
LAKE="abfss://lakehouse@${ACCOUNT}.dfs.core.windows.net/retail"

# 1) Build and push the image (build context is the academy code/ folder).
az acr create -g "$RG" -n "$ACR" --sku Basic --admin-enabled false
az acr build -r "$ACR" -t "$APP:1" -f labs/lab-06-model-deployment/service/Dockerfile ./code

# 2) Create the Container Apps environment and the app with a system-assigned identity.
az containerapp env create -g "$RG" -n "$ENVNAME" -l "$LOCATION"
az containerapp create -g "$RG" -n "$APP" --environment "$ENVNAME" \
  --image "$ACR.azurecr.io/$APP:1" --registry-server "$ACR.azurecr.io" \
  --system-assigned --ingress external --target-port 8000 \
  --min-replicas 0 --max-replicas 3 \
  --env-vars "FORECAST_TABLE=${LAKE}/gold/demand_forecast" "GOLD_TABLE=${LAKE}/gold/weekly_demand_features"

# 3) Grant the app's managed identity data-plane read on the lake (no keys).
PRINCIPAL=$(az containerapp show -g "$RG" -n "$APP" --query identity.principalId -o tsv)
SCOPE=$(az storage account show -g "$RG" -n "$ACCOUNT" --query id -o tsv)
az role assignment create --assignee-object-id "$PRINCIPAL" --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" --scope "$SCOPE"

echo "Service URL:"
az containerapp show -g "$RG" -n "$APP" --query properties.configuration.ingress.fqdn -o tsv
echo "Cleanup:  az containerapp delete -g $RG -n $APP --yes"
