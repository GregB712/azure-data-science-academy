"""Capstone end-to-end integration test: the whole local platform in one run.

Chains every stage the course builds - generate -> medallion (Bronze/Silver/Gold)
-> data-product registry -> train+backtest -> score -> monitor - on a tiny
synthetic dataset, asserting the pieces wire together and the final forecast
product is produced and contract-valid. Local only; no Azure. From code/:
    python -m pytest tests/test_capstone_end_to_end.py
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pytest

from forecasting import monitor
from forecasting.score import run as score_run
from forecasting.train import load_gold
from forecasting.train import run as train_run
from lakehouse_local import medallion
from retail_data.generate import Config, generate


@pytest.fixture(scope="module")
def platform(tmp_path_factory):
    root = tmp_path_factory.mktemp("capstone")
    raw, lake = root / "raw", str(root / "lake")
    model_dir = root / "model"

    # Stage 1 (data) + Stage 2 (lakehouse)
    summary = generate(Config(out=raw, n_stores=3, n_products=6, start=date(2024, 1, 1),
                              end=date(2024, 4, 30), seed=42, dq_defect_rate=0.004))
    medallion.bronze_ingest(raw, lake)
    report = medallion.silver_transform(lake, max_quarantine_ratio=0.05)
    gold_stats = medallion.gold_build(lake)

    gold = f"{lake}/gold/weekly_demand_features"
    # Stage 4 (train + backtest)
    train_metrics = train_run(argparse.Namespace(
        data=gold, output=str(model_dir), n_estimators=40, learning_rate=0.1,
        num_leaves=15, min_child_samples=5, n_splits=2, horizon=4,
        experiment="capstone", mlflow_uri=None))
    # Stage 5 (score -> demand_forecast product)
    forecast_table = f"{lake}/gold/demand_forecast"
    score_run(argparse.Namespace(
        data=gold, model=str(model_dir / "model" / "model.txt"), output=forecast_table,
        model_version="capstone", scoring_input=None,
        contract=str(Path(__file__).resolve().parents[1] / "contracts" / "forecasting.demand_forecast.v1.yaml")))

    return {"lake": lake, "gold": gold, "forecast_table": forecast_table,
            "model_dir": model_dir, "summary": summary, "silver_report": report,
            "gold_stats": gold_stats, "train_metrics": train_metrics}


def test_lakehouse_built(platform):
    assert platform["silver_report"].passed
    assert platform["gold_stats"]["weekly_demand_features"] > 0


def test_model_trained_and_beats_naive(platform):
    agg = platform["train_metrics"]["aggregate"]
    assert agg["wape"] > 0
    assert agg["mase"] < 1.0                         # beats the naive baseline


def test_forecast_product_produced(platform):
    assert (platform["model_dir"] / "metrics.json").exists()
    forecast = load_gold(platform["forecast_table"])
    assert len(forecast) == 18                       # 3 stores x 6 products, next week
    assert (forecast["forecast_units"] >= 0).all()
    assert list(forecast.columns) == ["week_start", "store_id", "product_id",
                                      "forecast_units", "model_version", "scored_at"]


def test_monitoring_runs_on_the_platform(platform):
    gold_df = load_gold(platform["gold"])
    drift = monitor.feature_drift(gold_df, gold_df)   # self vs self -> no drift
    assert drift["n_drifted"] == 0
    acc = monitor.accuracy_report(load_gold(platform["forecast_table"]), gold_df)
    assert acc["matched"] == 0                        # forecast week has no actuals yet
    decision = monitor.retrain_decision(acc, drift)
    assert decision["retrain"] is False
