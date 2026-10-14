"""End-to-end tests for the synthetic data generator and local medallion lakehouse.

Run from the code/ folder:  python -m pytest
These tests use only local files; no Azure resources are touched.
"""
from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pytest
from deltalake import DeltaTable, write_deltalake

from lakehouse_local import medallion, quality
from retail_data.generate import Config, easter_sunday, black_friday, generate

CONTRACTS = Path(__file__).resolve().parents[1] / "contracts"


@pytest.fixture(scope="module")
def lake(tmp_path_factory):
    root = tmp_path_factory.mktemp("adsa")
    raw, lake = root / "raw", str(root / "lake")
    summary = generate(Config(out=raw, n_stores=3, n_products=6, start=date(2024, 1, 1),
                              end=date(2024, 4, 30), seed=7, dq_defect_rate=0.004))
    assert summary["sales_files"] == 4
    medallion.bronze_ingest(raw, lake)
    report = medallion.silver_transform(lake, max_quarantine_ratio=0.05)
    medallion.gold_build(lake)
    return {"raw": raw, "lake": lake, "report": report}


def test_holiday_helpers():
    assert easter_sunday(2025) == date(2025, 4, 20)
    assert easter_sunday(2024) == date(2024, 3, 31)
    assert black_friday(2025) == date(2025, 11, 28)


def test_generator_is_deterministic(tmp_path):
    a = generate(Config(out=tmp_path / "a", n_stores=2, n_products=3, end=date(2024, 2, 29), seed=1))
    b = generate(Config(out=tmp_path / "b", n_stores=2, n_products=3, end=date(2024, 2, 29), seed=1))
    assert a == b
    fa = (tmp_path / "a" / "pos_sales" / "pos_sales_2024-02.csv").read_text()
    fb = (tmp_path / "b" / "pos_sales" / "pos_sales_2024-02.csv").read_text()
    assert fa == fb


def test_bronze_is_incremental(lake):
    stats = medallion.bronze_ingest(lake["raw"], lake["lake"])
    assert stats == {"files_ingested": 0, "rows_ingested": 0, "files_skipped": 4}


def test_silver_quarantines_defects_and_keys_are_unique(lake):
    sales = medallion.read_table(lake["lake"], "silver/sales")
    quarantine = medallion.read_table(lake["lake"], "silver/sales_quarantine")
    assert lake["report"].passed
    assert len(quarantine) > 0
    assert set(quarantine["_reject_reason"].str.split(";").explode().str.split(":").str[1]) <= {
        "referential", "range", "null", "type", "pattern"}
    assert not sales.duplicated(medallion.SALES_KEYS).any()
    assert (sales["units_sold"] >= 0).all()
    assert sales["unit_price"].gt(0).all()
    assert "S999" not in set(sales["store_id"])


def test_silver_rerun_is_idempotent(lake):
    before = len(medallion.read_table(lake["lake"], "silver/sales"))
    medallion.silver_transform(lake["lake"], max_quarantine_ratio=0.05)
    after = len(medallion.read_table(lake["lake"], "silver/sales"))
    assert before == after


def test_time_travel(lake):
    dt = DeltaTable(medallion.table_uri(lake["lake"], "silver/sales"))
    assert dt.version() >= 1  # initial WRITE + MERGE from the idempotency test
    v0 = medallion.read_table(lake["lake"], "silver/sales", version=0)
    assert len(v0) == len(dt.to_pandas())


def test_schema_enforcement_rejects_incompatible_append(lake):
    bad = pa.table({"date": ["not-a-date"], "store_id": [1]})
    with pytest.raises(Exception):
        write_deltalake(medallion.table_uri(lake["lake"], "silver/sales"), bad, mode="append")


def test_gold_features_lags(lake):
    w = medallion.read_table(lake["lake"], "gold/weekly_demand_features")
    w = w.sort_values(["store_id", "product_id", "week_start"])
    one = w[(w.store_id == w.store_id.iloc[0]) & (w.product_id == w.product_id.iloc[0])]
    assert pd.isna(one["units_lag_1"].iloc[0])
    assert one["units_lag_1"].iloc[1] == one["units"].iloc[0]
    assert not w.duplicated(["week_start", "store_id", "product_id"]).any()


def test_quality_gate_fails_when_too_many_rows_are_bad():
    contract = quality.load_contract(CONTRACTS / "sales.pos_sales.v1.yaml")
    cols = quality.contract_columns(contract)
    df = pd.DataFrame([{c: "" for c in cols}] * 3)
    _, rejected, report = quality.validate(df, contract, max_quarantine_ratio=0.1)
    assert len(rejected) == 3
    assert not report.passed
