#!/usr/bin/env bash
# Lab 01 · Step 2 · Monthly cost budget on the lab resource group, with email alerts
# at 50% and 100% of actual cost and 100% of forecast cost.
# Run in: WSL / Ubuntu. Uses the Consumption Budgets REST API via `az rest`,
# because `az consumption budget create` (preview command group) cannot set
# notifications. Budgets ALERT; they never stop resources.
source "$(dirname "$0")/_common.sh"
require_login
: "${BUDGET_EMAIL:?set BUDGET_EMAIL in lab.env}"
: "${BUDGET_AMOUNT:?set BUDGET_AMOUNT in lab.env}"

BUDGET_NAME="budget-${AZ_RESOURCE_GROUP}"
START="$(date -u +%Y-%m-01)T00:00:00Z"          # must be the first of a month
END="$(date -u -d "$(date -u +%Y-%m-01) +1 year" +%Y-%m-%d)T00:00:00Z"
URL="https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${AZ_RESOURCE_GROUP}/providers/Microsoft.Consumption/budgets/${BUDGET_NAME}?api-version=2023-05-01"

BODY=$(cat <<JSON
{
  "properties": {
    "category": "Cost",
    "amount": ${BUDGET_AMOUNT},
    "timeGrain": "Monthly",
    "timePeriod": { "startDate": "${START}", "endDate": "${END}" },
    "notifications": {
      "actual_50":    { "enabled": true, "operator": "GreaterThanOrEqualTo", "threshold": 50,  "thresholdType": "Actual",     "contactEmails": ["${BUDGET_EMAIL}"] },
      "actual_100":   { "enabled": true, "operator": "GreaterThanOrEqualTo", "threshold": 100, "thresholdType": "Actual",     "contactEmails": ["${BUDGET_EMAIL}"] },
      "forecast_100": { "enabled": true, "operator": "GreaterThan",          "threshold": 100, "thresholdType": "Forecasted", "contactEmails": ["${BUDGET_EMAIL}"] }
    }
  }
}
JSON
)

info "Creating budget '$BUDGET_NAME' of $BUDGET_AMOUNT (billing currency) on $AZ_RESOURCE_GROUP"
az rest --method put --url "$URL" --body "$BODY" -o none
save_state BUDGET_NAME "$BUDGET_NAME"
az rest --method get --url "$URL" --query "{name:name, amount:properties.amount, grain:properties.timeGrain, alerts:keys(properties.notifications)}" -o jsonc
ok "Budget created. Alerts can arrive a day or more after spend; cost data lags 8-24h."
