"""Monitoring for the demand forecasting system: feature drift and forecast accuracy.

Two signals that drive the retraining decision (Module 7):

- **Feature drift**: has the distribution of the model's inputs shifted since
  training? We use the Population Stability Index (PSI) per feature. Rule of
  thumb: PSI < 0.1 no shift, 0.1-0.25 moderate, > 0.25 significant.
- **Forecast accuracy on delayed ground truth**: once the actual units for a
  forecast week are known (weeks later), join predictions to actuals and measure
  realized WAPE/bias. Azure ML's built-in model monitoring covers input/prediction
  drift on collected inference data; *accuracy against delayed actuals* is domain
  logic you own - this is it.

These are pure, testable functions; a scheduled job (or Azure ML model monitor)
calls them and raises the retrain flag. See docs/mlops/08 and 09.

Run (WSL / Python), from code/:
    python -m forecasting.monitor drift --reference <gold_v0> --current <gold_now>
    python -m forecasting.monitor accuracy --forecast <demand_forecast> --actuals <gold_now>
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

from .features import NUMERIC_FEATURES
from .metrics import bias, mae, wape
from .train import load_gold

DRIFT_THRESHOLD = 0.25          # PSI above this = significant drift on a feature
ACCURACY_WAPE_MAX = 0.30        # realized WAPE above this = accuracy decay


def psi(reference, current, bins: int = 10) -> float:
    """Population Stability Index between a reference and current sample.

    Bin edges come from the reference quantiles; returns 0.0 when the reference
    has too few distinct values to bin.
    """
    ref = np.asarray(pd.Series(reference).dropna(), dtype="float64")
    cur = np.asarray(pd.Series(current).dropna(), dtype="float64")
    if ref.size == 0 or cur.size == 0:
        return 0.0
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if edges.size < 2:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    eps = 1e-6
    ref_pct = np.clip(np.histogram(ref, edges)[0] / ref.size, eps, None)
    cur_pct = np.clip(np.histogram(cur, edges)[0] / cur.size, eps, None)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def categorical_psi(reference, current) -> float:
    """PSI over the category frequencies of two samples."""
    ref = pd.Series(reference).astype("string").fillna("<NA>")
    cur = pd.Series(current).astype("string").fillna("<NA>")
    cats = sorted(set(ref.unique()) | set(cur.unique()))
    eps = 1e-6
    ref_pct = np.clip(ref.value_counts().reindex(cats, fill_value=0).to_numpy() / len(ref), eps, None)
    cur_pct = np.clip(cur.value_counts().reindex(cats, fill_value=0).to_numpy() / len(cur), eps, None)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def feature_drift(reference: pd.DataFrame, current: pd.DataFrame,
                  columns: list[str] | None = None,
                  threshold: float = DRIFT_THRESHOLD) -> dict:
    """PSI per feature between a reference and current feature table."""
    columns = columns or [c for c in NUMERIC_FEATURES if c in reference.columns and c in current.columns]
    scores: dict[str, float] = {}
    for col in columns:
        if pd.api.types.is_numeric_dtype(reference[col]):
            scores[col] = round(psi(reference[col], current[col]), 4)
        else:
            scores[col] = round(categorical_psi(reference[col], current[col]), 4)
    drifted = sorted([c for c, s in scores.items() if s > threshold])
    return {"threshold": threshold, "psi": scores, "drifted": drifted, "n_drifted": len(drifted)}


def accuracy_report(forecast: pd.DataFrame, actuals: pd.DataFrame,
                    wape_max: float = ACCURACY_WAPE_MAX) -> dict:
    """Realized accuracy where forecast weeks have known actuals (delayed truth).

    forecast: week_start, store_id, product_id, forecast_units
    actuals:  week_start, store_id, product_id, units
    """
    keys = ["week_start", "store_id", "product_id"]
    f = forecast.copy()
    a = actuals.copy()
    for df in (f, a):
        df["week_start"] = pd.to_datetime(df["week_start"]).dt.date.astype(str)
        df["store_id"] = df["store_id"].astype(str)
        df["product_id"] = df["product_id"].astype(str)
    merged = f.merge(a[keys + ["units"]], on=keys, how="inner")
    coverage = len(merged) / len(f) if len(f) else 0.0
    if merged.empty:
        return {"matched": 0, "coverage": 0.0, "wape": None, "bias": None,
                "retrain_recommended": False,
                "note": "No actuals for the forecast weeks yet (delayed ground truth)."}
    w = wape(merged["units"], merged["forecast_units"])
    return {
        "matched": int(len(merged)),
        "coverage": round(coverage, 4),
        "wape": round(w, 4),
        "bias": round(bias(merged["units"], merged["forecast_units"]), 4),
        "mae": round(mae(merged["units"], merged["forecast_units"]), 4),
        "wape_max": wape_max,
        "retrain_recommended": bool(w > wape_max),
    }


def retrain_decision(accuracy: dict, drift: dict) -> dict:
    """Combine accuracy decay and feature drift into a single retrain trigger."""
    reasons = []
    if accuracy.get("retrain_recommended"):
        reasons.append(f"realized WAPE {accuracy.get('wape')} exceeds {accuracy.get('wape_max')}")
    if drift.get("n_drifted", 0) > 0:
        reasons.append(f"feature drift on {drift['drifted']}")
    return {"retrain": bool(reasons), "reasons": reasons}


# --------------------------------------------------------------------------- cli

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Drift and accuracy monitoring")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("drift", help="Feature drift between two Gold snapshots")
    d.add_argument("--reference", required=True, help="Reference Gold table (e.g. training snapshot)")
    d.add_argument("--current", required=True, help="Current Gold table")

    a = sub.add_parser("accuracy", help="Realized accuracy of forecasts vs actuals")
    a.add_argument("--forecast", required=True, help="gold/demand_forecast table")
    a.add_argument("--actuals", required=True, help="gold/weekly_demand_features table (actual units)")

    args = p.parse_args(argv)
    if args.cmd == "drift":
        report = feature_drift(load_gold(args.reference), load_gold(args.current))
    else:
        report = accuracy_report(load_gold(args.forecast), load_gold(args.actuals))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
