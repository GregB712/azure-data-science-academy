"""Tests for the Module 6 scoring step (gold/demand_forecast product).

Local only: generate a tiny dataset, build Gold, fit a small model, then score.
Run from code/:  python -m pytest tests/test_scoring.py
"""
from __future__ import annotations

from datetime import date

import lightgbm as lgb
import pandas as pd
import pytest

from forecasting import score as scoring
from forecasting.features import FEATURE_COLUMNS, make_features
from forecasting.train import DEFAULT_PARAMS, fit_model, load_gold
from lakehouse_local import medallion
from retail_data.generate import Config, generate


@pytest.fixture(scope="module")
def gold_and_model(tmp_path_factory):
    root = tmp_path_factory.mktemp("score")
    raw, lake = root / "raw", str(root / "lake")
    generate(Config(out=raw, n_stores=3, n_products=6, start=date(2024, 1, 1),
                    end=date(2024, 4, 30), seed=11, dq_defect_rate=0.004))
    medallion.bronze_ingest(raw, lake)
    medallion.silver_transform(lake, max_quarantine_ratio=0.05)
    medallion.gold_build(lake)
    gold = load_gold(f"{lake}/gold/weekly_demand_features")
    model = fit_model(make_features(gold), dict(DEFAULT_PARAMS), num_boost_round=30)
    return {"lake": lake, "gold": gold, "model": model}


def test_scoring_frame_is_one_row_per_series_next_week(gold_and_model):
    gold = gold_and_model["gold"]
    frame = scoring.build_scoring_frame(gold)
    n_series = gold.groupby(["store_id", "product_id"], observed=True).ngroups
    assert len(frame) == n_series == 18
    for col in FEATURE_COLUMNS:
        assert col in frame.columns
    # the scored week is strictly after every observed week (no leakage)
    assert pd.to_datetime(frame["week_start"]).min() > pd.to_datetime(gold["week_start"]).max()


def test_score_produces_contract_valid_forecast(gold_and_model):
    out = scoring.score(gold_and_model["gold"], gold_and_model["model"], model_version="test")
    assert list(out.columns) == scoring.FORECAST_COLUMNS
    assert len(out) == 18
    assert (out["forecast_units"] >= 0).all()           # non-negative demand
    assert out["model_version"].eq("test").all()
    report = scoring._validate(out, scoring.DEFAULT_CONTRACT)
    assert report.passed, report.summary()


def test_contract_catches_negative_forecast(gold_and_model):
    out = scoring.score(gold_and_model["gold"], gold_and_model["model"])
    out.loc[0, "forecast_units"] = -5.0                 # inject a contract violation
    assert not scoring._validate(out, scoring.DEFAULT_CONTRACT).passed


def test_load_model_from_dir(gold_and_model, tmp_path):
    booster = gold_and_model["model"]
    (tmp_path / "model").mkdir()
    booster.save_model(str(tmp_path / "model" / "model.txt"))
    loaded = scoring.load_model(tmp_path)                 # directory, not file
    assert isinstance(loaded, lgb.Booster)
