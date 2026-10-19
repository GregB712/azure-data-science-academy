"""Score the trained demand model into the gold/demand_forecast data product.

Produces a one-step-ahead (next-week) forecast per product-store series from the
Gold feature table and the model trained in Module 5. Writes a Delta table that
honours the Demand Forecast contract, so it can be published as the
``supply-chain.demand-forecast`` data product.

Design: the model forecasts one week ahead, so the "scoring frame" is one row
per series with the features of the first unobserved week (lags and rolling
means from history; promotions/holidays assumed absent unless a plan supplies
them). Each row is independent, which is exactly what a **batch endpoint** scores
row-wise - see the Module 6 batch-endpoints lesson. The same function is called
locally here and by the lab's batch scoring driver.

Run (WSL / Python), from code/:
    python -m forecasting.score \
        --data ../data/lake/gold/weekly_demand_features \
        --model ../data/model/model/model.txt \
        --output ../data/lake/gold/demand_forecast
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from deltalake import write_deltalake

from lakehouse_local import quality

from .features import CATEGORICAL_FEATURES, FEATURE_COLUMNS, TARGET
from .train import _storage_options, load_gold

DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "forecasting.demand_forecast.v1.yaml"
FORECAST_COLUMNS = ["week_start", "store_id", "product_id", "forecast_units", "model_version", "scored_at"]
KEYS = ["store_id", "product_id"]


def build_scoring_frame(gold: pd.DataFrame) -> pd.DataFrame:
    """One feature row per series for the first unobserved week.

    Lags and the rolling mean come from each series' history. Calendar/trend
    columns are computed against the *training* data's first week so the trend
    feature continues consistently. Categorical dtypes are pinned to the Gold
    universe so LightGBM's category codes match those seen in training.
    """
    g = gold.copy()
    g["week_start"] = pd.to_datetime(g["week_start"])
    first_week = g["week_start"].min()

    rows: list[dict] = []
    for (store_id, product_id), grp in g.groupby(KEYS, observed=True):
        grp = grp.sort_values("week_start")
        units = grp[TARGET].to_numpy(dtype="float64")
        future_week = grp["week_start"].max() + timedelta(days=7)
        rows.append({
            "week_start": future_week,
            "store_id": store_id,
            "product_id": product_id,
            "category": grp["category"].iloc[-1],
            "avg_price": float(grp["avg_price"].iloc[-1]),
            "promo_days": 0,            # planning inputs; default to none planned
            "stockout_days": 0,         # assume in stock
            "holiday_days": 0,          # a real pipeline joins the forward calendar
            "units_lag_1": units[-1] if len(units) >= 1 else np.nan,
            "units_lag_2": units[-2] if len(units) >= 2 else np.nan,
            "units_lag_52": units[-52] if len(units) >= 52 else np.nan,
            "units_roll_mean_4": float(np.mean(units[-4:])) if len(units) else np.nan,
            "week_of_year": int(future_week.isocalendar().week),
            "month": int(future_week.month),
            "weeks_since_start": int((future_week - first_week).days // 7),
        })

    frame = pd.DataFrame(rows)
    for col in CATEGORICAL_FEATURES:
        frame[col] = pd.Categorical(frame[col].astype(str),
                                    categories=sorted(g[col].astype(str).unique()))
    return frame


def load_model(path: str | Path) -> lgb.Booster:
    """Load a LightGBM Booster from a model.txt file or a directory holding one."""
    p = Path(path)
    if p.is_dir():
        candidates = list(p.rglob("model.txt"))
        if not candidates:
            raise FileNotFoundError(f"No model.txt found under {p}")
        p = candidates[0]
    return lgb.Booster(model_file=str(p))


def predict_rows(model: lgb.Booster, frame: pd.DataFrame) -> np.ndarray:
    """Row-wise non-negative demand prediction for a ready feature frame."""
    return np.clip(model.predict(frame[FEATURE_COLUMNS]), 0.0, None)


def score(gold: pd.DataFrame, model: lgb.Booster, model_version: str = "local") -> pd.DataFrame:
    """Return the demand_forecast rows for the next week per series."""
    frame = build_scoring_frame(gold)
    preds = predict_rows(model, frame)
    out = frame[["week_start", "store_id", "product_id"]].copy()
    out["week_start"] = pd.to_datetime(out["week_start"]).dt.date
    out["store_id"] = out["store_id"].astype(str)
    out["product_id"] = out["product_id"].astype(str)
    out["forecast_units"] = np.round(preds, 2)
    out["model_version"] = str(model_version)
    out["scored_at"] = datetime.now(timezone.utc).isoformat()
    return out[FORECAST_COLUMNS]


def _validate(forecast: pd.DataFrame, contract_path: str | Path) -> quality.ValidationReport:
    contract = quality.load_contract(contract_path)
    cols = quality.contract_columns(contract)
    _, _, report = quality.validate(forecast[cols], contract, max_quarantine_ratio=0.0)
    return report


def run(args: argparse.Namespace) -> pd.DataFrame:
    gold = load_gold(args.data)
    model = load_model(args.model)
    forecast = score(gold, model, args.model_version)

    report = _validate(forecast, args.contract)
    if not report.passed:
        raise RuntimeError("demand_forecast fails its contract.\n" + report.summary())

    write_deltalake(args.output, forecast, mode="overwrite",
                    storage_options=_storage_options(args.output), schema_mode="overwrite")

    if args.scoring_input:
        # Plain parquet matrix for a row-wise batch endpoint (one row per series).
        build_scoring_frame(gold).to_parquet(args.scoring_input, index=False)

    print(f"Wrote {len(forecast)} forecast rows to {args.output} (contract OK). "
          f"mean forecast_units={forecast['forecast_units'].mean():.2f}")
    return forecast


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Score the demand model into gold/demand_forecast")
    p.add_argument("--data", required=True, help="Gold weekly_demand_features Delta table path/URI")
    p.add_argument("--model", required=True, help="model.txt or a directory containing it")
    p.add_argument("--output", required=True, help="Output Delta table path/URI for gold/demand_forecast")
    p.add_argument("--model-version", default="local")
    p.add_argument("--scoring-input", default=None, help="Optional parquet path for the batch-endpoint scoring matrix")
    p.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    return p


def main(argv: list[str] | None = None) -> int:
    try:
        run(build_parser().parse_args(argv))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
