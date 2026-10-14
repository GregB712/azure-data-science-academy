#!/usr/bin/env bash
# Lab 01 · Step 0 · Preflight checks. Run in: WSL / Ubuntu.
# Read-only: creates nothing in Azure.
set -uo pipefail

pass=0; failc=0
check() {  # check "description" command...
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then printf '  \033[32mPASS\033[0m %s\n' "$desc"; pass=$((pass+1));
  else printf '  \033[31mFAIL\033[0m %s\n' "$desc"; failc=$((failc+1)); fi
}

echo "Environment"
check "running inside WSL (kernel mentions microsoft)" grep -qi microsoft /proc/version
check "working directory is on the Linux filesystem (not /mnt/c)" bash -c '[[ "$PWD" != /mnt/* ]]'
check "python3 >= 3.10" python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'
check "python3 venv module available" python3 -c 'import venv'
check "git installed" git --version
check "Azure CLI installed (az)" az version

echo "Azure sign-in"
if az account show -o none 2>/dev/null; then
  printf '  \033[32mPASS\033[0m signed in as %s\n' "$(az account show --query user.name -o tsv)"
  printf '       subscription: %s (%s)\n' "$(az account show --query name -o tsv)" "$(az account show --query id -o tsv)"
  printf '       tenant:       %s\n' "$(az account show --query tenantId -o tsv)"
  pass=$((pass+1))
else
  printf '  \033[33mSKIP\033[0m not signed in (run: az login --use-device-code)\n'
fi

echo "Clock (token errors in WSL are often clock drift after sleep)"
if command -v curl >/dev/null; then
  remote=$(curl -sI https://management.azure.com 2>/dev/null | awk -F': ' 'tolower($1)=="date"{print $2}' | tr -d '\r')
  if [[ -n "$remote" ]]; then
    drift=$(( $(date -u +%s) - $(date -u -d "$remote" +%s) ))
    drift=${drift#-}
    if (( drift < 120 )); then printf '  \033[32mPASS\033[0m clock drift %ss\n' "$drift"; pass=$((pass+1));
    else printf '  \033[31mFAIL\033[0m clock drift %ss (fix: sudo hwclock -s, or wsl --shutdown in PowerShell)\n' "$drift"; failc=$((failc+1)); fi
  else
    printf '  \033[33mSKIP\033[0m could not reach management.azure.com to compare clocks\n'
  fi
fi

echo
echo "passed=$pass failed=$failc"
(( failc == 0 ))
