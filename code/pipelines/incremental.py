"""Incremental processing, change data feed and SCD type 2 (delta-rs, no Spark).

Module 3's medallion reprocesses *all* of Bronze on every run - simple and
idempotent, but wasteful as data grows. Module 4 replaces that with:

- ``silver_incremental``: a **high-watermark** Bronze->Silver step that processes
  only rows ingested since the last run, then MERGEs them into Silver. Re-running
  with no new data is a no-op (idempotent).
- ``change_feed``: read a Delta table's **change data feed** (inserts/updates/
  deletes since a version), the mechanism Databricks/Spark use for incremental
  and CDC pipelines.
- ``scd2_upsert``: **slowly changing dimension type 2** - keep history by closing
  the old row and opening a new current one when attributes change.

Run (WSL / Python), from code/:
    python -m pipelines.incremental --lake ../data/lake
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from lakehouse_local import medallion, quality

CONTRACTS = medallion.CONTRACTS
SALES_KEYS = medallion.SALES_KEYS


# --------------------------------------------------------------------------- watermark

def _watermark_path(lake: str, name: str) -> str:
    return os.path.join(lake, "_state", f"{name}.json")


def load_watermark(lake: str, name: str = "silver_sales") -> str:
    """Return the last processed Bronze ``_ingested_at`` ('' if none yet)."""
    p = _watermark_path(lake, name)
    if os.path.exists(p):
        return json.loads(Path(p).read_text())["last_ingested_at"]
    return ""


def save_watermark(lake: str, value: str, name: str = "silver_sales") -> None:
    p = Path(_watermark_path(lake, name))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"last_ingested_at": value}), encoding="utf-8")


# --------------------------------------------------------------------------- incremental silver

def silver_incremental(lake: str, max_quarantine_ratio: float = 0.05) -> dict:
    """Process only Bronze pos_sales rows newer than the watermark into Silver."""
    so = medallion.storage_options(lake)
    bronze = medallion.read_table(lake, "bronze/pos_sales")
    wm = load_watermark(lake)
    new = bronze[bronze["_ingested_at"] > wm] if wm else bronze
    if new.empty:
        return {"rows_in": 0, "rows_valid": 0, "rows_processed": 0, "watermark": wm, "skipped": True}

    # De-duplicate the new batch on the business key (latest ingestion wins).
    new = new.sort_values("_ingested_at").drop_duplicates(subset=SALES_KEYS, keep="last")

    contract = quality.load_contract(CONTRACTS / "sales.pos_sales.v1.yaml")
    cols = quality.contract_columns(contract)
    refs = _reference_sets(lake)
    valid, _, report = quality.validate(new[cols + ["_ingested_at"]], contract, refs, max_quarantine_ratio)
    if not report.passed:
        raise RuntimeError("Incremental Silver quality gate failed; nothing written.\n" + report.summary())

    valid = valid.astype({"units_sold": "int64", "promo_discount_pct": "int64", "on_promotion": "bool",
                          "stockout": "bool", "store_id": "object", "product_id": "object"})
    valid["stock_on_hand_open"] = valid["stock_on_hand_open"].astype("float64")
    valid["sales_year"] = pd.to_datetime(valid["date"]).dt.year.astype("int64")
    valid = valid.rename(columns={"_ingested_at": "_bronze_ingested_at"})

    uri = medallion.table_uri(lake, "silver/sales")
    arrow = pa.Table.from_pandas(valid, preserve_index=False)
    if not medallion.table_exists(lake, "silver/sales"):
        write_deltalake(uri, arrow, partition_by=["sales_year"], storage_options=so)
    else:
        (DeltaTable(uri, storage_options=so)
         .merge(arrow, predicate=" AND ".join(f"t.{k} = s.{k}" for k in SALES_KEYS),
                source_alias="s", target_alias="t")
         .when_matched_update_all().when_not_matched_insert_all().execute())

    new_wm = str(new["_ingested_at"].max())
    save_watermark(lake, new_wm)
    return {"rows_in": int(len(new)), "rows_valid": int(len(valid)),
            "rows_processed": int(len(valid)), "watermark": new_wm, "skipped": False}


def _reference_sets(lake: str) -> dict[str, set]:
    """Referential sets from Silver dims if they exist (else referential rules skip)."""
    refs: dict[str, set] = {}
    if medallion.table_exists(lake, "silver/stores"):
        refs["stores.store_id"] = set(medallion.read_table(lake, "silver/stores")["store_id"])
    if medallion.table_exists(lake, "silver/products"):
        refs["products.product_id"] = set(medallion.read_table(lake, "silver/products")["product_id"])
    return refs


# --------------------------------------------------------------------------- change data feed

def change_feed(path: str, starting_version: int = 0, storage_options: dict | None = None) -> pd.DataFrame:
    """Read a Delta table's change data feed from ``starting_version``.

    Returns rows with a ``_change_type`` column (insert / update_preimage /
    update_postimage / delete) plus ``_commit_version`` and ``_commit_timestamp``.
    The table must have been written with ``delta.enableChangeDataFeed=true``.
    """
    dt = DeltaTable(path, storage_options=storage_options)
    reader = dt.load_cdf(starting_version=starting_version)  # arro3 stream
    return pa.RecordBatchReader.from_stream(reader).read_all().to_pandas()


# --------------------------------------------------------------------------- SCD type 2

def scd2_upsert(current: pd.DataFrame, updates: pd.DataFrame, keys: list[str],
                attributes: list[str], asof: str,
                effective_from: str = "effective_from", effective_to: str = "effective_to",
                is_current: str = "is_current") -> pd.DataFrame:
    """Apply a new snapshot to a type-2 dimension, preserving history.

    For each key in ``updates``: unchanged -> no-op; changed -> close the current
    row (``effective_to = asof``, ``is_current = False``) and open a new current
    row; new key -> insert a current row. Returns the full dimension.
    """
    current = current.copy()
    out_rows = [current]
    open_mask = current[is_current] if is_current in current else pd.Series(True, index=current.index)

    for _, upd in updates.iterrows():
        key_match = (current[keys] == upd[keys].values).all(axis=1) & open_mask.fillna(False)
        existing = current[key_match]
        changed = existing.empty or not (existing.iloc[0][attributes] == upd[attributes]).all()
        if not changed:
            continue
        if not existing.empty:
            idx = existing.index[0]
            current.loc[idx, effective_to] = asof
            current.loc[idx, is_current] = False
        new_row = {**{k: upd[k] for k in keys}, **{a: upd[a] for a in attributes},
                   effective_from: asof, effective_to: None, is_current: True}
        out_rows.append(pd.DataFrame([new_row]))

    result = pd.concat(out_rows, ignore_index=True)
    return result.drop_duplicates().reset_index(drop=True)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Incremental Bronze->Silver (high-watermark)")
    p.add_argument("--lake", default="../data/lake")
    p.add_argument("--max-quarantine-ratio", type=float, default=0.05)
    a = p.parse_args(argv)
    print("silver_incremental:", json.dumps(silver_incremental(a.lake, a.max_quarantine_ratio), default=str))


if __name__ == "__main__":
    main()
