"""A small but real medallion lakehouse using Delta Lake (delta-rs), no Spark needed.

Bronze  raw files landed as-is (all columns as strings) + ingestion metadata,
        append-only, incremental by source file.
Silver  typed, de-duplicated, contract-validated tables. Rows that break the
        contract go to a quarantine table with a reason. Sales are MERGEd
        (upsert) on the business key so re-runs are idempotent.
Gold    consumption-ready products: daily sales by store/category for BI and a
        weekly demand feature table for forecasting.

The lake root can be a local folder or an ADLS Gen2 URI, for example
    abfss://lakehouse@<account>.dfs.core.windows.net/retail
in which case authentication uses your Azure CLI sign-in (no keys).

Run (WSL):
    python medallion.py all --raw ../../data/raw --lake ../../data/lake
    python medallion.py history --lake ../../data/lake --table silver/sales
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake
from deltalake.exceptions import TableNotFoundError

try:  # works both as a package module and as a script
    from . import quality
except ImportError:  # pragma: no cover
    import quality  # type: ignore

HERE = Path(__file__).resolve().parent
CONTRACTS = HERE.parent / "contracts"
SALES_KEYS = ["date", "store_id", "product_id"]


# --------------------------------------------------------------------------- storage

def storage_options(lake: str) -> dict[str, str] | None:
    """Entra ID auth for ADLS Gen2 via the Azure CLI sign-in; None for local paths."""
    if lake.startswith(("abfss://", "az://", "adl://")):
        account = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME") or lake.split("@")[1].split(".")[0]
        return {"azure_storage_account_name": account, "azure_use_azure_cli": "true"}
    return None


def table_uri(lake: str, name: str) -> str:
    return f"{lake.rstrip('/')}/{name}"


def read_table(lake: str, name: str, version: int | None = None) -> pd.DataFrame:
    dt = DeltaTable(table_uri(lake, name), storage_options=storage_options(lake), version=version)
    return dt.to_pandas()


def table_exists(lake: str, name: str) -> bool:
    return DeltaTable.is_deltatable(table_uri(lake, name), storage_options=storage_options(lake))


def _to_arrow(df: pd.DataFrame) -> pa.Table:
    return pa.Table.from_pandas(df, preserve_index=False)


# --------------------------------------------------------------------------- bronze

def bronze_ingest(raw: Path, lake: str) -> dict[str, int]:
    """Land raw files into Bronze. Sales are incremental per source file."""
    now = datetime.now(timezone.utc).isoformat()
    batch = uuid.uuid4().hex[:12]
    so = storage_options(lake)
    stats = {"files_ingested": 0, "rows_ingested": 0, "files_skipped": 0}

    already: set[str] = set()
    if table_exists(lake, "bronze/pos_sales"):
        already = set(read_table(lake, "bronze/pos_sales")["_source_file"].unique())

    for f in sorted(glob.glob(str(raw / "pos_sales" / "*.csv"))):
        name = Path(f).name
        if name in already:
            stats["files_skipped"] += 1
            continue
        df = pd.read_csv(f, dtype=str, keep_default_na=False)  # Bronze keeps raw text
        df["_source_file"] = name
        df["_ingested_at"] = now
        df["_batch_id"] = batch
        write_deltalake(table_uri(lake, "bronze/pos_sales"), _to_arrow(df), mode="append",
                        storage_options=so)
        stats["files_ingested"] += 1
        stats["rows_ingested"] += len(df)

    # Master data: full snapshot each run (small tables), overwrite.
    dims = {
        "bronze/stores": pd.read_csv(raw / "stores.csv", dtype=str, keep_default_na=False),
        "bronze/products": pd.read_json(raw / "products.json", lines=True, dtype=False).astype(str),
        "bronze/calendar": pd.read_csv(raw / "calendar.csv", dtype=str, keep_default_na=False),
    }
    for name, df in dims.items():
        df["_ingested_at"] = now
        write_deltalake(table_uri(lake, name), _to_arrow(df), mode="overwrite", storage_options=so,
                        schema_mode="overwrite")
    return stats


# --------------------------------------------------------------------------- silver

def silver_transform(lake: str, max_quarantine_ratio: float = 0.01) -> quality.ValidationReport:
    so = storage_options(lake)

    stores = read_table(lake, "bronze/stores").drop(columns=["_ingested_at"])
    stores["store_size_sqm"] = pd.to_numeric(stores["store_size_sqm"]).astype("int64")
    stores["latitude"] = pd.to_numeric(stores["latitude"])
    stores["longitude"] = pd.to_numeric(stores["longitude"])
    products = read_table(lake, "bronze/products").drop(columns=["_ingested_at"])
    for c in ("list_price", "price_elasticity", "popularity"):
        products[c] = pd.to_numeric(products[c])
    products["is_perishable"] = products["is_perishable"].str.lower() == "true"
    cal = read_table(lake, "bronze/calendar").drop(columns=["_ingested_at"])
    cal["date"] = pd.to_datetime(cal["date"]).dt.date
    for c in ("day_of_week", "iso_week", "month", "year"):
        cal[c] = pd.to_numeric(cal[c]).astype("int64")
    for c in ("is_weekend", "is_holiday", "stores_closed"):
        cal[c] = cal[c].str.lower() == "true"

    for name, df in {"silver/stores": stores, "silver/products": products, "silver/calendar": cal}.items():
        write_deltalake(table_uri(lake, name), _to_arrow(df), mode="overwrite", storage_options=so,
                        schema_mode="overwrite")

    # Sales: de-duplicate on the business key (latest ingestion wins), then validate.
    raw = read_table(lake, "bronze/pos_sales")
    raw = (raw.sort_values("_ingested_at")
              .drop_duplicates(subset=SALES_KEYS, keep="last"))
    contract = quality.load_contract(CONTRACTS / "sales.pos_sales.v1.yaml")
    cols = quality.contract_columns(contract)
    refs = {"stores.store_id": set(stores["store_id"]), "products.product_id": set(products["product_id"])}
    valid, rejected, report = quality.validate(raw[cols + ["_source_file", "_ingested_at"]], contract, refs,
                                               max_quarantine_ratio)
    if not report.passed:
        raise RuntimeError("Silver quality gate failed; nothing written.\n" + report.summary())

    valid = valid.astype({"units_sold": "int64", "promo_discount_pct": "int64", "on_promotion": "bool",
                          "stockout": "bool", "store_id": "object", "product_id": "object"})
    valid["stock_on_hand_open"] = valid["stock_on_hand_open"].astype("float64")
    valid["sales_year"] = pd.to_datetime(valid["date"]).dt.year.astype("int64")
    valid = valid.drop(columns=["_source_file"]).rename(columns={"_ingested_at": "_bronze_ingested_at"})

    uri = table_uri(lake, "silver/sales")
    if not table_exists(lake, "silver/sales"):
        write_deltalake(uri, _to_arrow(valid), partition_by=["sales_year"], storage_options=so)
    else:
        (DeltaTable(uri, storage_options=so)
         .merge(_to_arrow(valid), predicate=" AND ".join(f"t.{k} = s.{k}" for k in SALES_KEYS),
                source_alias="s", target_alias="t")
         .when_matched_update_all()
         .when_not_matched_insert_all()
         .execute())

    if len(rejected):
        rejected = rejected.astype(str)
        rejected["_quarantined_at"] = datetime.now(timezone.utc).isoformat()
        # Silver re-processes all of Bronze on each run (simple and idempotent at this
        # size), so the quarantine table holds the *current* set of rejected rows.
        # Module 4 replaces this with incremental processing via Delta change data feed.
        write_deltalake(table_uri(lake, "silver/sales_quarantine"), _to_arrow(rejected), mode="overwrite",
                        storage_options=so, schema_mode="overwrite")
    return report


# --------------------------------------------------------------------------- gold

def gold_build(lake: str) -> dict[str, int]:
    so = storage_options(lake)
    sales = read_table(lake, "silver/sales")
    products = read_table(lake, "silver/products")
    stores = read_table(lake, "silver/stores")
    cal = read_table(lake, "silver/calendar")

    s = (sales.merge(products[["product_id", "category"]], on="product_id", how="left")
              .merge(stores[["store_id", "region"]], on="store_id", how="left")
              .merge(cal[["date", "is_holiday"]], on="date", how="left"))

    daily = (s.groupby(["date", "store_id", "region", "category"], as_index=False)
              .agg(units=("units_sold", "sum"), revenue=("revenue", "sum"),
                   promo_lines=("on_promotion", "sum"), stockout_lines=("stockout", "sum")))
    daily["revenue"] = daily["revenue"].round(2)
    write_deltalake(table_uri(lake, "gold/daily_sales_store_category"), _to_arrow(daily), mode="overwrite",
                    storage_options=so, schema_mode="overwrite")

    s["week_start"] = (pd.to_datetime(s["date"]) - pd.to_timedelta(pd.to_datetime(s["date"]).dt.dayofweek, unit="D")).dt.date
    weekly = (s.groupby(["week_start", "store_id", "product_id", "category"], as_index=False)
               .agg(units=("units_sold", "sum"), avg_price=("unit_price", "mean"),
                    promo_days=("on_promotion", "sum"), stockout_days=("stockout", "sum"),
                    holiday_days=("is_holiday", "sum")))
    weekly = weekly.sort_values(["store_id", "product_id", "week_start"])
    g = weekly.groupby(["store_id", "product_id"])["units"]
    weekly["units_lag_1"] = g.shift(1).astype("float64")
    weekly["units_lag_2"] = g.shift(2).astype("float64")
    weekly["units_lag_52"] = g.shift(52).astype("float64")
    weekly["units_roll_mean_4"] = g.transform(lambda x: x.shift(1).rolling(4, min_periods=1).mean())
    weekly["avg_price"] = weekly["avg_price"].round(4)
    for c in ("units", "promo_days", "stockout_days", "holiday_days"):
        weekly[c] = weekly[c].astype("int64")

    contract = quality.load_contract(CONTRACTS / "forecasting.demand_features.v1.yaml")
    _, rejected, report = quality.validate(weekly, contract, max_quarantine_ratio=0.0)
    if not report.passed:
        raise RuntimeError("Gold contract check failed.\n" + report.summary())
    write_deltalake(table_uri(lake, "gold/weekly_demand_features"), _to_arrow(weekly), mode="overwrite",
                    storage_options=so, schema_mode="overwrite")
    return {"daily_sales_store_category": len(daily), "weekly_demand_features": len(weekly)}


# --------------------------------------------------------------------------- cli

def history(lake: str, name: str) -> list[dict]:
    dt = DeltaTable(table_uri(lake, name), storage_options=storage_options(lake))
    return [{k: h.get(k) for k in ("version", "timestamp", "operation", "operationMetrics")} for h in dt.history()]


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Local medallion lakehouse on Delta Lake")
    p.add_argument("step", choices=["bronze", "silver", "gold", "all", "history"])
    p.add_argument("--raw", type=Path, default=Path("data/raw"))
    p.add_argument("--lake", default="data/lake", help="Local path or abfss:// URI")
    p.add_argument("--table", default="silver/sales", help="For 'history'")
    p.add_argument("--max-quarantine-ratio", type=float, default=0.01)
    a = p.parse_args(argv)

    if a.step in ("bronze", "all"):
        print("bronze:", json.dumps(bronze_ingest(a.raw, a.lake)))
    if a.step in ("silver", "all"):
        print(silver_transform(a.lake, a.max_quarantine_ratio).summary())
    if a.step in ("gold", "all"):
        print("gold:", json.dumps(gold_build(a.lake)))
    if a.step == "history":
        for h in history(a.lake, a.table):
            print(json.dumps(h, default=str))


if __name__ == "__main__":
    try:
        main()
    except TableNotFoundError as exc:  # friendlier message for out-of-order steps
        raise SystemExit(f"Table not found ({exc}). Run the earlier medallion step first.")
