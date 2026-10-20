"""Tests for Module 4 incremental/CDC building blocks. Local only (delta-rs)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pyarrow as pa
import pytest
from deltalake import DeltaTable, write_deltalake

from lakehouse_local import medallion
from pipelines import incremental
from retail_data.generate import Config, generate


@pytest.fixture()
def lake(tmp_path):
    raw, lake = tmp_path / "raw", str(tmp_path / "lake")
    generate(Config(out=raw, n_stores=2, n_products=4, start=date(2024, 1, 1),
                    end=date(2024, 2, 29), seed=5, dq_defect_rate=0.0))
    medallion.bronze_ingest(raw, lake)
    return lake


def test_incremental_then_idempotent_then_new_batch(lake):
    first = incremental.silver_incremental(lake)
    assert first["skipped"] is False and first["rows_processed"] > 0
    assert medallion.table_exists(lake, "silver/sales")

    # No new Bronze rows -> nothing processed (idempotent).
    second = incremental.silver_incremental(lake)
    assert second["skipped"] is True and second["rows_processed"] == 0

    # Append one genuinely new Bronze row with a later ingestion time.
    bronze = medallion.read_table(lake, "bronze/pos_sales")
    row = bronze.iloc[[0]].copy()
    row["date"] = "2024-03-15"                     # new business key (date)
    row["_ingested_at"] = "2099-01-01T00:00:00+00:00"
    write_deltalake(medallion.table_uri(lake, "bronze/pos_sales"),
                    pa.Table.from_pandas(row, preserve_index=False), mode="append")

    third = incremental.silver_incremental(lake)
    assert third["skipped"] is False and third["rows_processed"] == 1
    assert third["watermark"] == "2099-01-01T00:00:00+00:00"


def test_change_data_feed(tmp_path):
    path = str(tmp_path / "cdf_table")
    df = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
    write_deltalake(path, pa.Table.from_pandas(df, preserve_index=False),
                    configuration={"delta.enableChangeDataFeed": "true"})
    write_deltalake(path, pa.Table.from_pandas(
        pd.DataFrame({"id": [4], "val": ["d"]}), preserve_index=False), mode="append")
    DeltaTable(path).update(updates={"val": "'Z'"}, predicate="id = 1")

    changes = incremental.change_feed(path, starting_version=0)
    assert "_change_type" in changes.columns
    assert "insert" in set(changes["_change_type"])
    # the update produced pre/post images
    assert {"update_preimage", "update_postimage"} & set(changes["_change_type"])


def test_scd2_upsert_closes_and_opens_rows():
    current = pd.DataFrame({
        "product_id": ["P1", "P2"], "list_price": [1.0, 2.0],
        "effective_from": ["2024-01-01", "2024-01-01"],
        "effective_to": [None, None], "is_current": [True, True],
    })
    updates = pd.DataFrame({
        "product_id": ["P1", "P3"], "list_price": [1.5, 9.0], "asof": ["2024-06-01", "2024-06-01"],
    })
    out = incremental.scd2_upsert(current, updates, keys=["product_id"],
                                  attributes=["list_price"], asof="2024-06-01")
    # P1: old row closed, new current row at 1.5
    p1 = out[out["product_id"] == "P1"]
    assert len(p1) == 2
    assert set(p1[~p1["is_current"]]["list_price"]) == {1.0}
    assert set(p1[p1["is_current"]]["list_price"]) == {1.5}
    # P2 unchanged (one current row); P3 inserted as current
    assert len(out[out["product_id"] == "P2"]) == 1
    p3 = out[out["product_id"] == "P3"]
    assert len(p3) == 1 and bool(p3.iloc[0]["is_current"]) is True
