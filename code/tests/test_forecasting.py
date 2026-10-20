"""Tests for the Module 5 demand forecasting baseline.

Local only: they generate a tiny synthetic dataset, build the Gold table with
the medallion code, then exercise metrics, temporal splitting and an end-to-end
training run. No Azure resources are touched. Run from code/:  python -m pytest
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from forecasting import backtest, metrics
from forecasting.evaluate import Thresholds, release_decision
from forecasting.features import CATEGORICAL_FEATURES, FEATURE_COLUMNS, TARGET, make_features
from forecasting.train import load_gold, run
from forecasting.validate import validate_gold
from lakehouse_local import medallion
from retail_data.generate import Config, generate


@pytest.fixture(scope="module")
def gold_path(tmp_path_factory) -> str:
    root = tmp_path_factory.mktemp("fc")
    raw, lake = root / "raw", str(root / "lake")
    generate(Config(out=raw, n_stores=3, n_products=6, start=date(2024, 1, 1),
                    end=date(2024, 4, 30), seed=7, dq_defect_rate=0.004))
    medallion.bronze_ingest(raw, lake)
    medallion.silver_transform(lake, max_quarantine_ratio=0.05)
    medallion.gold_build(lake)
    return f"{lake}/gold/weekly_demand_features"


# --------------------------------------------------------------------------- metrics

def test_metric_formulas():
    y = [10.0, 20.0, 30.0]
    p = [12.0, 18.0, 33.0]
    assert metrics.mae(y, p) == pytest.approx(7 / 3)
    assert metrics.wape(y, p) == pytest.approx(7 / 60, rel=1e-5)
    assert metrics.bias(y, p) == pytest.approx(3 / 60, rel=1e-5)  # net over-forecast


def test_bias_sign():
    y = [10.0, 10.0]
    assert metrics.bias(y, [12.0, 12.0]) > 0   # over-forecast
    assert metrics.bias(y, [8.0, 8.0]) < 0     # under-forecast


def test_seasonal_naive_mae():
    assert metrics.seasonal_naive_mae([10, 12, 15, 14], 1) == pytest.approx(2.0)
    assert np.isnan(metrics.seasonal_naive_mae([5], 1))  # too short


# --------------------------------------------------------------------------- backtest

def test_temporal_splits_no_leakage():
    weeks = list(range(20))
    folds = backtest.temporal_splits(weeks, n_splits=3, horizon=4, min_train_weeks=8)
    assert len(folds) == 3
    prev_train = -1
    for train_weeks, test_weeks in folds:
        assert len(test_weeks) == 4
        assert max(train_weeks) < min(test_weeks)          # no leakage
        assert len(train_weeks) > prev_train               # expanding window
        prev_train = len(train_weeks)


def test_temporal_splits_respects_min_train():
    folds = backtest.temporal_splits(list(range(12)), n_splits=5, horizon=4, min_train_weeks=8)
    assert len(folds) == 1                                  # only one fold has >=8 train weeks


# --------------------------------------------------------------------------- features

def test_make_features(gold_path):
    df = make_features(load_gold(gold_path))
    for col in FEATURE_COLUMNS + [TARGET]:
        assert col in df.columns
    for col in CATEGORICAL_FEATURES:
        assert str(df[col].dtype) == "category"
    # sorted by series then time, so lag columns line up
    assert df.equals(df.sort_values(["store_id", "product_id", "week_start"]).reset_index(drop=True))


# --------------------------------------------------------------------------- end to end

def test_train_end_to_end(gold_path, tmp_path):
    out = tmp_path / "model"
    args = argparse.Namespace(
        data=gold_path, output=str(out), n_estimators=30, learning_rate=0.1,
        num_leaves=15, min_child_samples=5, n_splits=2, horizon=4,
        experiment="test", mlflow_uri=None,
    )
    result = run(args)

    assert (out / "metrics.json").exists()
    assert (out / "model" / "model.txt").exists()
    agg = result["aggregate"]
    assert agg["folds"] >= 1
    assert np.isfinite(agg["wape"]) and agg["wape"] > 0
    # metrics.json round-trips and matches the returned object
    saved = json.loads((out / "metrics.json").read_text())
    assert saved["aggregate"]["folds"] == agg["folds"]
    assert saved["n_series"] == 18  # 3 stores x 6 products


# --------------------------------------------------------------------------- validate + gate

def test_validate_gold_passes_contract(gold_path):
    report = validate_gold(gold_path)
    assert report.passed, report.summary()


def test_release_gate_blocks_and_approves():
    good = {"wape": 0.22, "bias": 0.02, "mase": 0.71}
    assert release_decision(good).passed

    # fails every threshold, and the reasons name each one
    bad = {"wape": 0.40, "bias": 0.12, "mase": 1.3}
    decision = release_decision(bad)
    assert not decision.passed
    assert len(decision.reasons) == 3

    # a NaN metric (e.g. backtest could not compute MASE) must block, never pass
    assert not release_decision({"wape": 0.2, "bias": 0.0, "mase": float("nan")}).passed


def test_release_gate_respects_custom_thresholds():
    agg = {"wape": 0.28, "bias": 0.04, "mase": 0.9}
    assert release_decision(agg).passed
    assert not release_decision(agg, Thresholds(wape_max=0.25)).passed
