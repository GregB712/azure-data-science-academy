---
id: command-cheatsheet
title: Command and Snippet Cheat Sheet
type: reference
order: 4
status: available
tags: [azure-cli, python, snippets, reference]
related: [lab-01-azure-setup, m1-azure-fundamentals, m3-lakehouse-medallion]
summary: The commands and code snippets used most often in the course, grouped by task, each labelled with where it runs.
---

# Command and Snippet Cheat Sheet

All commands run in **WSL / Ubuntu** unless marked otherwise.

## Sign-in and context

```bash
az login --use-device-code                     # sign in from WSL
az account list -o table                        # subscriptions you can see
az account set --subscription "<name-or-id>"   # pick one
az account show --query "{name:name, id:id, user:user.name}" -o table
az config set core.output=table                 # optional default output
```

```powershell
# PowerShell (Windows): WSL housekeeping
wsl -l -v            # versions
wsl --shutdown       # restart WSL (fixes clock drift)
```

## Resource groups, tags, cleanup

```bash
az group create -n rg-adsa-labNN -l westeurope --tags project=adsa env=lab owner=<you> expires=2026-12-31
az group list --tag project=adsa -o table       # find course leftovers
az resource list -g rg-adsa-labNN -o table
az group delete -n rg-adsa-labNN --yes --no-wait
az group exists -n rg-adsa-labNN
```

## RBAC

```bash
ME=$(az ad signed-in-user show --query id -o tsv)
az role assignment list --assignee "$ME" --all -o table
az role assignment create --assignee-object-id "$ME" --assignee-principal-type User \
  --role "Storage Blob Data Contributor" --scope <resource-id>
```

## Storage (ADLS Gen2), Entra auth only

```bash
az storage fs list --account-name <acct> --auth-mode login -o table
az storage fs file upload -f bronze -s local.parquet -p path/file.parquet --account-name <acct> --auth-mode login
az storage fs file list -f bronze --path path --account-name <acct> --auth-mode login -o table
az storage account update -n <acct> -g <rg> --allow-shared-key-access false
```

## Python: credentials

```python
from azure.identity import AzureCliCredential, DefaultAzureCredential, ManagedIdentityCredential
cred = AzureCliCredential()                         # local dev after az login
# cred = DefaultAzureCredential()                   # dev convenience; set AZURE_TOKEN_CREDENTIALS=dev
# cred = ManagedIdentityCredential(client_id=...)   # deployed code
```

## Python: ADLS Gen2

```python
from azure.storage.filedatalake import DataLakeServiceClient
svc = DataLakeServiceClient("https://<acct>.dfs.core.windows.net", credential=cred)
fs = svc.get_file_system_client("bronze")
fs.get_file_client("x/y.parquet").upload_data(data_bytes, overwrite=True)
data = fs.get_file_client("x/y.parquet").download_file().readall()
```

## Python: Delta Lake without Spark (delta-rs)

```python
from deltalake import DeltaTable, write_deltalake
write_deltalake("data/lake/silver/t", df, mode="append")                  # local
so = {"azure_storage_account_name": "<acct>", "azure_use_azure_cli": "true"}
write_deltalake("abfss://lakehouse@<acct>.dfs.core.windows.net/t", df, mode="append", storage_options=so)
dt = DeltaTable("data/lake/silver/t"); dt.history(); DeltaTable("data/lake/silver/t", version=0).to_pandas()
dt.optimize.compact(); dt.vacuum(retention_hours=168, dry_run=True)
```

## Course code

```bash
cd code && source .venv/bin/activate
python retail_data/generate.py --out ../data/raw --seed 42
python lakehouse_local/medallion.py all --raw ../data/raw --lake ../data/lake
python lakehouse_local/medallion.py history --lake ../data/lake --table silver/sales
python data_mesh/registry.py validate | list | impact <product-id> | mermaid
python data_mesh/contract_compat.py <old.yaml> <new.yaml>
python -m pytest
```

## Costs

```bash
python labs/lab-01-azure-setup/python/price_check.py --region westeurope       # retail list prices
az consumption budget list --resource-group <rg> -o table                        # preview command group
```

## Unity Catalog grants (Databricks SQL)

```sql
GRANT USE CATALOG ON CATALOG sales TO `grp-supplychain-engineers`;
GRANT USE SCHEMA  ON SCHEMA  sales.products TO `grp-supplychain-engineers`;
GRANT SELECT      ON TABLE   sales.products.pos_sales TO `grp-supplychain-engineers`;
SHOW GRANTS ON TABLE sales.products.pos_sales;
```

## Bicep

```bash
az bicep install                       # or use the bicep CLI
az deployment group what-if -g <rg> -f main.bicep -p key=value
az deployment group create  -g <rg> -f main.bicep -p key=value
```
