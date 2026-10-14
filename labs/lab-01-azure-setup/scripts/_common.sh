#!/usr/bin/env bash
# Shared helpers for Lab 01 scripts. Sourced, not executed.
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$LAB_DIR/lab.env"
STATE_FILE="$LAB_DIR/.lab-state"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Run: cp $LAB_DIR/lab.env.example $ENV_FILE  and edit it." >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"
[[ -f "$STATE_FILE" ]] && source "$STATE_FILE"

: "${AZ_LOCATION:?set AZ_LOCATION in lab.env}"
: "${AZ_RESOURCE_GROUP:?set AZ_RESOURCE_GROUP in lab.env}"
: "${STORAGE_PREFIX:?set STORAGE_PREFIX in lab.env}"
: "${OWNER_TAG:?set OWNER_TAG in lab.env}"

info()  { printf '\033[1;34m[info]\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m[ ok ]\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
fail()  { printf '\033[1;31m[fail]\033[0m %s\n' "$*" >&2; exit 1; }

require_login() {
  az account show -o none 2>/dev/null || fail "Not signed in. Run: az login --use-device-code"
  if [[ -n "${AZ_SUBSCRIPTION_ID:-}" ]]; then
    az account set --subscription "$AZ_SUBSCRIPTION_ID"
  fi
  SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
  SUBSCRIPTION_NAME="$(az account show --query name -o tsv)"
  export SUBSCRIPTION_ID SUBSCRIPTION_NAME
}

confirm() {
  # Skip the prompt with ASSUME_YES=1 (for re-runs you have already reviewed)
  [[ "${ASSUME_YES:-0}" == "1" ]] && return 0
  read -r -p "$1 [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]] || fail "Aborted by user."
}

save_state() {  # save_state KEY VALUE  -> persisted for later scripts
  touch "$STATE_FILE"
  grep -v "^$1=" "$STATE_FILE" > "$STATE_FILE.tmp" || true
  echo "$1=$2" >> "$STATE_FILE.tmp"
  mv "$STATE_FILE.tmp" "$STATE_FILE"
}

TAGS=(project=adsa lab=lab-01 env=lab "owner=$OWNER_TAG" "expires=$(date -u -d '+30 days' +%Y-%m-%d)")
