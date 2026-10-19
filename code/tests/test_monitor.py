"""Tests for the Module 7 monitoring module (drift + accuracy). Local only."""
from __future__ import annotations

import numpy as np
import pandas as pd

from forecasting import monitor


def test_psi_zero_for_same_distribution():
    rng = np.random.default_rng(0)
    x = rng.normal(size=5000)
    assert monitor.psi(x, x) < 0.01


def test_psi_detects_shift():
    rng = np.random.default_rng(1)
    ref = rng.normal(loc=0, size=5000)
    shifted = rng.normal(loc=3, size=5000)          # a clear mean shift
    assert monitor.psi(ref, shifted) > monitor.DRIFT_THRESHOLD


def test_categorical_psi():
    ref = ["a"] * 80 + ["b"] * 20
    same = ["a"] * 79 + ["b"] * 21
    flipped = ["a"] * 20 + ["b"] * 80
    assert monitor.categorical_psi(ref, same) < 0.05
    assert monitor.categorical_psi(ref, flipped) > monitor.DRIFT_THRESHOLD


def test_feature_drift_flags_only_shifted_columns():
    rng = np.random.default_rng(2)
    n = 4000
    ref = pd.DataFrame({"units_lag_1": rng.normal(10, 2, n), "avg_price": rng.normal(5, 1, n)})
    cur = pd.DataFrame({"units_lag_1": rng.normal(10, 2, n), "avg_price": rng.normal(9, 1, n)})
    report = monitor.feature_drift(ref, cur, columns=["units_lag_1", "avg_price"])
    assert report["drifted"] == ["avg_price"]
    assert report["psi"]["avg_price"] > report["psi"]["units_lag_1"]


def _forecast_actuals():
    keys = {"week_start": ["2025-01-06"] * 3, "store_id": ["S1", "S1", "S2"],
            "product_id": ["P1", "P2", "P1"]}
    forecast = pd.DataFrame({**keys, "forecast_units": [10.0, 20.0, 30.0]})
    actuals = pd.DataFrame({**keys, "units": [12.0, 18.0, 33.0]})
    return forecast, actuals


def test_accuracy_report_matches_and_scores():
    forecast, actuals = _forecast_actuals()
    rep = monitor.accuracy_report(forecast, actuals, wape_max=0.30)
    assert rep["matched"] == 3 and rep["coverage"] == 1.0
    assert rep["wape"] == round(7 / 63, 4)          # (|2|+|2|+|3|) / (12+18+33)
    assert rep["retrain_recommended"] is False


def test_accuracy_report_no_actuals_yet():
    forecast, actuals = _forecast_actuals()
    actuals["week_start"] = "2099-01-01"            # no overlap (future forecast)
    rep = monitor.accuracy_report(forecast, actuals)
    assert rep["matched"] == 0 and rep["retrain_recommended"] is False
    assert "delayed ground truth" in rep["note"]


def test_retrain_decision_combines_signals():
    assert monitor.retrain_decision({"retrain_recommended": False}, {"n_drifted": 0})["retrain"] is False
    d = monitor.retrain_decision({"retrain_recommended": True, "wape": 0.4, "wape_max": 0.3},
                                 {"n_drifted": 1, "drifted": ["avg_price"]})
    assert d["retrain"] is True and len(d["reasons"]) == 2
