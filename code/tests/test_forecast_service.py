"""Tests for the Module 6 FastAPI forecast service.

Local only: builds a tiny lake + model, writes the demand_forecast table, then
drives the app with FastAPI's TestClient. Run from code/:
    python -m pytest tests/test_forecast_service.py
"""
from __future__ import annotations

import argparse
from datetime import date

import pytest
from fastapi.testclient import TestClient

from forecasting import score as scoring
from forecasting.train import run as train_run
from lakehouse_local import medallion
from retail_data.generate import Config, generate


@pytest.fixture(scope="module")
def client(tmp_path_factory, monkeypatch_module):
    root = tmp_path_factory.mktemp("svc")
    raw, lake = root / "raw", str(root / "lake")
    generate(Config(out=raw, n_stores=2, n_products=4, start=date(2024, 1, 1),
                    end=date(2024, 4, 30), seed=13, dq_defect_rate=0.004))
    medallion.bronze_ingest(raw, lake)
    medallion.silver_transform(lake, max_quarantine_ratio=0.05)
    medallion.gold_build(lake)

    gold = f"{lake}/gold/weekly_demand_features"
    out = root / "model"
    train_run(argparse.Namespace(data=gold, output=str(out), n_estimators=30, learning_rate=0.1,
                                 num_leaves=15, min_child_samples=5, n_splits=2, horizon=4,
                                 experiment="test", mlflow_uri=None))
    model_file = str(out / "model" / "model.txt")
    forecast_table = f"{lake}/gold/demand_forecast"
    scoring.run(argparse.Namespace(data=gold, model=model_file, output=forecast_table,
                                   model_version="test", scoring_input=None,
                                   contract=str(scoring.DEFAULT_CONTRACT)))

    monkeypatch_module.setenv("FORECAST_TABLE", forecast_table)
    monkeypatch_module.setenv("GOLD_TABLE", gold)
    monkeypatch_module.setenv("MODEL_PATH", model_file)
    from forecast_service.app import create_app
    return TestClient(create_app())


@pytest.fixture(scope="module")
def monkeypatch_module():
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_get_precomputed_forecast(client):
    r = client.get("/forecast/S001/P0001")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "precomputed"
    assert body["forecast_units"] >= 0


def test_get_forecast_unknown_series_404(client):
    assert client.get("/forecast/S999/P9999").status_code == 404


def test_on_demand_score_accepts_whatif_overrides(client):
    base = client.post("/score", json={"store_id": "S001", "product_id": "P0001"})
    assert base.status_code == 200 and base.json()["source"] == "on-demand"
    assert base.json()["forecast_units"] >= 0
    # what-if overrides are accepted and return a valid, non-negative forecast
    promo = client.post("/score", json={"store_id": "S001", "product_id": "P0001",
                                        "promo_days": 7, "avg_price": 3.5})
    assert promo.status_code == 200
    assert promo.json()["forecast_units"] >= 0


def test_on_demand_rejects_out_of_range_promo(client):
    # pydantic validation: promo_days must be within 0..7
    assert client.post("/score", json={"store_id": "S001", "product_id": "P0001",
                                       "promo_days": 9}).status_code == 422


def test_on_demand_unknown_series_404(client):
    assert client.post("/score", json={"store_id": "S999", "product_id": "P9999"}).status_code == 404
