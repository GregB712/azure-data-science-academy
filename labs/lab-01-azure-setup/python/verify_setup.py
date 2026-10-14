"""Lab 01 verification: proves control-plane and data-plane access work with Entra ID auth.

Run in: WSL / Ubuntu, inside the lab virtual environment, after
scripts/01_create_resources.sh:

    python python/verify_setup.py            # full check against Azure
    python python/verify_setup.py --offline  # local-only checks (no Azure needed)

What it checks
  local      Python version, SDK imports, Parquet round-trip in memory
  control    Azure CLI credential works; subscription; resource group + tags;
             storage account security settings via ARM (HNS on, shared key off,
             public blob access off, TLS >= 1.2)
  data       writes a small Parquet file to bronze/_lab01/ with your Entra
             identity, reads it back, compares, lists it, deletes it

No secrets are used or stored: authentication comes from `az login`.
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[1]
STORAGE_API_VERSION = "2023-05-01"


@dataclass
class Result:
    group: str
    name: str
    ok: bool
    detail: str = ""


results: list[Result] = []


def record(group: str, name: str, ok: bool, detail: str = "") -> bool:
    results.append(Result(group, name, ok, detail))
    mark = "\033[32mPASS\033[0m" if ok else "\033[31mFAIL\033[0m"
    print(f"  {mark} [{group}] {name}" + (f"  ({detail})" if detail else ""))
    return ok


def parse_env_file(path: Path) -> dict[str, str]:
    """Read KEY=VALUE lines (lab.env, .lab-state). Ignores comments and blanks."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def load_config() -> dict[str, str]:
    cfg = parse_env_file(LAB_DIR / "lab.env")
    cfg.update(parse_env_file(LAB_DIR / ".lab-state"))
    for key in ("AZ_RESOURCE_GROUP", "STORAGE_ACCOUNT", "AZ_SUBSCRIPTION_ID"):
        if os.getenv(key):
            cfg[key] = os.environ[key]
    return cfg


def sample_parquet_bytes() -> bytes:
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.table({
        "date": pa.array(["2025-01-06", "2025-01-06", "2025-01-07"]),
        "store_id": ["S001", "S002", "S001"],
        "product_id": ["P0001", "P0001", "P0002"],
        "units_sold": pa.array([12, 7, 3], type=pa.int32()),
    })
    buf = io.BytesIO()
    pq.write_table(table, buf)
    return buf.getvalue()


def check_local() -> None:
    print("Local")
    record("local", "python >= 3.10", sys.version_info >= (3, 10), sys.version.split()[0])
    for mod in ("azure.identity", "azure.mgmt.resource.resources", "azure.mgmt.resource.subscriptions",
                "azure.storage.filedatalake", "pyarrow"):
        try:
            __import__(mod)
            record("local", f"import {mod}", True)
        except ImportError as exc:
            record("local", f"import {mod}", False, f"{exc}; run pip install -r python/requirements.txt")
    try:
        import pyarrow.parquet as pq

        data = sample_parquet_bytes()
        back = pq.read_table(io.BytesIO(data))
        record("local", "parquet round-trip in memory", back.num_rows == 3, f"{len(data)} bytes")
    except Exception as exc:  # noqa: BLE001
        record("local", "parquet round-trip in memory", False, str(exc))


def check_control_plane(cfg: dict[str, str]):
    from azure.identity import AzureCliCredential
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.resource.subscriptions import SubscriptionClient

    print("Control plane (management.azure.com)")
    cred = AzureCliCredential()
    try:
        cred.get_token("https://management.azure.com/.default")
        record("control", "Azure CLI credential issues a token", True)
    except Exception as exc:  # noqa: BLE001
        record("control", "Azure CLI credential issues a token", False, f"{exc.__class__.__name__}: run az login")
        return None

    subs = list(SubscriptionClient(cred).subscriptions.list())
    sub_id = cfg.get("AZ_SUBSCRIPTION_ID") or next((s.subscription_id for s in subs if s.state == "Enabled"), None)
    record("control", "subscription visible", any(s.subscription_id == sub_id for s in subs), sub_id or "none")
    if not sub_id:
        return None

    rm = ResourceManagementClient(cred, sub_id)
    rg_name = cfg.get("AZ_RESOURCE_GROUP", "")
    try:
        rg = rm.resource_groups.get(rg_name)
        tags = rg.tags or {}
        record("control", f"resource group {rg_name} exists", True, rg.location)
        record("control", "resource group has project/owner/expires tags",
               {"project", "owner", "expires"} <= set(tags), ", ".join(f"{k}={v}" for k, v in tags.items()))
    except Exception as exc:  # noqa: BLE001
        record("control", f"resource group {rg_name} exists", False, exc.__class__.__name__)
        return None

    sa = cfg.get("STORAGE_ACCOUNT")
    if not sa:
        record("control", "storage account name known", False, "run scripts/01_create_resources.sh first")
        return None
    rid = (f"/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/"
           f"Microsoft.Storage/storageAccounts/{sa}")
    res = rm.resources.get_by_id(rid, api_version=STORAGE_API_VERSION)
    props = res.properties or {}
    record("control", "hierarchical namespace enabled (ADLS Gen2)", props.get("isHnsEnabled") is True)
    record("control", "shared key access disabled", props.get("allowSharedKeyAccess") is False)
    record("control", "public blob access disabled", props.get("allowBlobPublicAccess") is False)
    record("control", "minimum TLS 1.2", props.get("minimumTlsVersion") == "TLS1_2")
    return cred, sa


def check_data_plane(cred, account: str, retries: int = 8) -> None:
    import pyarrow.parquet as pq
    from azure.core.exceptions import HttpResponseError
    from azure.storage.filedatalake import DataLakeServiceClient

    print("Data plane (dfs.core.windows.net)")
    svc = DataLakeServiceClient(account_url=f"https://{account}.dfs.core.windows.net", credential=cred)
    fs = svc.get_file_system_client("bronze")
    path = f"_lab01/verify_{int(time.time())}.parquet"
    payload = sample_parquet_bytes()

    for attempt in range(1, retries + 1):
        try:
            fs.get_file_client(path).upload_data(payload, overwrite=True)
            record("data", f"write bronze/{path}", True, f"{len(payload)} bytes")
            break
        except HttpResponseError as exc:
            if exc.status_code == 403 and attempt < retries:
                print(f"    403 (role may still be propagating), retrying in 15s [{attempt}/{retries}]")
                time.sleep(15)
                continue
            record("data", f"write bronze/{path}", False, f"{exc.status_code} {exc.error_code}")
            return

    data = fs.get_file_client(path).download_file().readall()
    table = pq.read_table(io.BytesIO(data))
    record("data", "read back and compare", data == payload and table.num_rows == 3, f"{table.num_rows} rows")
    listed = [p.name for p in fs.get_paths(path="_lab01")]
    record("data", "list directory", path in listed, f"{len(listed)} item(s)")
    fs.get_file_client(path).delete_file()
    record("data", "delete test file", True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="only run local checks")
    a = ap.parse_args(argv)

    check_local()
    if not a.offline:
        cfg = load_config()
        out = check_control_plane(cfg)
        if out:
            check_data_plane(*out)

    failed = [r for r in results if not r.ok]
    print()
    if failed:
        print(f"{len(failed)} CHECK(S) FAILED. See README 'Troubleshooting'.")
        return 1
    print("ALL CHECKS PASSED" + (" (offline mode: Azure not checked)" if a.offline else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
