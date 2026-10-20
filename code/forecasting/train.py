"""Train and backtest the weekly demand forecasting model.

Reads the Delta Gold table ``gold/weekly_demand_features``, runs a rolling-origin
temporal backtest with LightGBM, compares against a persistence (naive) baseline,
logs everything to MLflow, then fits a final model on all history and saves it.

The script is deliberately framework-plain so it runs identically:
  - locally:   python -m forecasting.train --data ../data/lake/gold/weekly_demand_features
  - Azure ML:  as a command job whose input mounts the same Delta folder
               (MLflow tracking is auto-configured inside the job).

No secrets: ADLS Gen2 paths authenticate with your Azure CLI sign-in, exactly
like lakehouse_local/medallion.py.

Run (WSL / Python), from the code/ folder with the venv active:
    python -m forecasting.train \
        --data ../data/lake/gold/weekly_demand_features \
        --output ../data/model --n-estimators 300
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from deltalake import DeltaTable

from .backtest import temporal_splits
from .features import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    TARGET,
    make_features,
)
from .metrics import bias, mae, seasonal_naive_mae, wape

DEFAULT_PARAMS = {
    "objective": "tweedie",          # non-negative, over-dispersed counts with many zeros
    "tweedie_variance_power": 1.2,
    "metric": "mae",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.9,
    "bagging_freq": 1,
    "verbosity": -1,
    "seed": 42,
}


# --------------------------------------------------------------------------- data

def _storage_options(path: str) -> dict[str, str] | None:
    """Entra ID auth for ADLS Gen2 via the Azure CLI sign-in; None for local paths."""
    if path.startswith(("abfss://", "az://", "adl://")):
        account = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME") or path.split("@")[1].split(".")[0]
        return {"azure_storage_account_name": account, "azure_use_azure_cli": "true"}
    return None


def load_gold(path: str) -> pd.DataFrame:
    """Load the Gold Delta table at ``path`` (local folder or abfss:// URI)."""
    dt = DeltaTable(path, storage_options=_storage_options(path))
    return dt.to_pandas()


# --------------------------------------------------------------------------- model

def fit_model(train_df: pd.DataFrame, params: dict, num_boost_round: int) -> lgb.Booster:
    dataset = lgb.Dataset(
        train_df[FEATURE_COLUMNS],
        label=train_df[TARGET],
        categorical_feature=CATEGORICAL_FEATURES,
        free_raw_data=False,
    )
    return lgb.train(params, dataset, num_boost_round=num_boost_round)


def predict(model: lgb.Booster, df: pd.DataFrame) -> np.ndarray:
    """Predict non-negative demand."""
    return np.clip(model.predict(df[FEATURE_COLUMNS]), 0.0, None)


def naive_forecast(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    """Persistence baseline: each series' last training week carried forward."""
    last = (train_df.sort_values("week_start")
                    .groupby(["store_id", "product_id"], observed=True)[TARGET]
                    .last())
    keys = list(zip(test_df["store_id"], test_df["product_id"]))
    overall = float(train_df[TARGET].mean())
    return np.array([last.get(k, overall) for k in keys], dtype="float64")


def _mase(train_df: pd.DataFrame, test_df: pd.DataFrame, y_pred: np.ndarray) -> float:
    """Pooled MASE: sum of absolute errors over sum of (n_test * naive scale),
    skipping series whose training history is too short for a naive scale."""
    test = test_df.assign(_pred=y_pred)
    num = den = 0.0
    scales = (train_df.sort_values("week_start")
                      .groupby(["store_id", "product_id"], observed=True)[TARGET]
                      .apply(lambda s: seasonal_naive_mae(s.to_numpy(), 1)))
    for key, grp in test.groupby(["store_id", "product_id"], observed=True):
        scale = scales.get(key, float("nan"))
        if not np.isfinite(scale) or scale <= 0:
            continue
        num += float(np.sum(np.abs(grp[TARGET].to_numpy() - grp["_pred"].to_numpy())))
        den += len(grp) * scale
    return num / den if den > 0 else float("nan")


# --------------------------------------------------------------------------- backtest

def backtest(df: pd.DataFrame, params: dict, num_boost_round: int,
             n_splits: int, horizon: int) -> tuple[list[dict], dict]:
    """Run the rolling-origin backtest. Returns (per-fold rows, aggregate dict)."""
    weeks = df["week_start"].unique()
    folds = temporal_splits(weeks, n_splits=n_splits, horizon=horizon)
    if not folds:
        raise ValueError("Not enough weeks for a backtest; generate more history.")

    rows: list[dict] = []
    for i, (train_weeks, test_weeks) in enumerate(folds):
        train_df = df[df["week_start"].isin(train_weeks)]
        test_df = df[df["week_start"].isin(test_weeks)]
        model = fit_model(train_df, params, num_boost_round)
        y_pred = predict(model, test_df)
        y_true = test_df[TARGET].to_numpy()
        y_naive = naive_forecast(train_df, test_df)
        rows.append({
            "fold": i,
            "train_weeks": len(train_weeks),
            "test_weeks": len(test_weeks),
            "test_rows": int(len(test_df)),
            "wape": wape(y_true, y_pred),
            "bias": bias(y_true, y_pred),
            "mase": _mase(train_df, test_df, y_pred),
            "mae": mae(y_true, y_pred),
            "naive_wape": wape(y_true, y_naive),
            "naive_mae": mae(y_true, y_naive),
        })

    def avg(key: str) -> float:
        vals = [r[key] for r in rows if np.isfinite(r[key])]
        return float(np.mean(vals)) if vals else float("nan")

    aggregate = {
        "folds": len(rows),
        "wape": avg("wape"),
        "bias": avg("bias"),
        "mase": avg("mase"),
        "naive_wape": avg("naive_wape"),
        "skill_vs_naive": 1.0 - (avg("wape") / avg("naive_wape")) if avg("naive_wape") else float("nan"),
    }
    return rows, aggregate


# --------------------------------------------------------------------------- run

def run(args: argparse.Namespace) -> dict:
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    raw = load_gold(args.data)
    df = make_features(raw)
    params = dict(DEFAULT_PARAMS)
    params.update(learning_rate=args.learning_rate, num_leaves=args.num_leaves,
                  min_child_samples=args.min_child_samples)

    rows, aggregate = backtest(df, params, args.n_estimators, args.n_splits, args.horizon)

    # Final model on all history: this is the artifact that gets registered/deployed.
    final_model = fit_model(df, params, args.n_estimators)
    model_dir = output / "model"
    model_dir.mkdir(exist_ok=True)
    final_model.save_model(str(model_dir / "model.txt"))

    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": int(len(df)),
        "n_series": int(df.groupby(["store_id", "product_id"], observed=True).ngroups),
        "weeks": int(df["week_start"].nunique()),
        "params": params,
        "n_estimators": args.n_estimators,
        "aggregate": aggregate,
        "folds": rows,
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")

    _log_to_mlflow(args, params, rows, aggregate, final_model, model_dir)

    print(json.dumps({"aggregate": aggregate, "output": str(output)}, indent=2, default=str))
    return metrics


def _log_to_mlflow(args, params, rows, aggregate, final_model, model_dir) -> None:
    """Best-effort MLflow logging. Inside an Azure ML job the tracking URI and
    experiment are already set, so we do not override them there."""
    try:
        import mlflow
        import mlflow.lightgbm
    except ImportError:  # pragma: no cover - mlflow is a declared dependency
        print("mlflow not installed; skipping experiment logging.")
        return

    in_azure = bool(os.environ.get("AZUREML_RUN_ID"))
    try:
        if not in_azure:
            tracking = args.mlflow_uri or os.environ.get("MLFLOW_TRACKING_URI")
            if not tracking:
                # Keep the familiar ./mlruns folder so learners can just run
                # `mlflow ui`; MLflow 3 gates the file store behind this opt-in.
                os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
                tracking = f"file:{Path(args.output).resolve() / 'mlruns'}"
            mlflow.set_tracking_uri(tracking)
            mlflow.set_experiment(args.experiment)

        ctx = _active_or_new_run(mlflow) if in_azure else mlflow.start_run(run_name="lightgbm-backtest")
        with ctx:
            mlflow.log_params({**params, "n_estimators": args.n_estimators,
                               "n_splits": args.n_splits, "horizon": args.horizon})
            for r in rows:
                for metric in ("wape", "bias", "mase", "naive_wape"):
                    if np.isfinite(r[metric]):
                        mlflow.log_metric(f"fold_{metric}", r[metric], step=r["fold"])
            mlflow.log_metrics({k: v for k, v in aggregate.items()
                                if isinstance(v, float) and np.isfinite(v)})
            try:
                mlflow.lightgbm.log_model(final_model, name="model")
            except TypeError:  # older MLflow signature
                mlflow.lightgbm.log_model(final_model, artifact_path="model")
    except Exception as exc:  # never fail training because of experiment logging
        print(f"MLflow logging skipped ({type(exc).__name__}: {exc}).")


class _active_or_new_run:
    """Context manager that reuses the ambient Azure ML run if one exists."""

    def __init__(self, mlflow_mod):
        self._mlflow = mlflow_mod
        self._started = False

    def __enter__(self):
        run = self._mlflow.active_run()
        if run is None:
            run = self._mlflow.start_run()
            self._started = True
        return run

    def __exit__(self, *exc):
        if self._started:
            self._mlflow.end_run()
        return False


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Backtest and train the weekly demand model")
    p.add_argument("--data", required=True, help="Path/URI of the Gold Delta table")
    p.add_argument("--output", default="../data/model", help="Output dir for model + metrics")
    p.add_argument("--n-estimators", type=int, default=300)
    p.add_argument("--learning-rate", type=float, default=DEFAULT_PARAMS["learning_rate"])
    p.add_argument("--num-leaves", type=int, default=DEFAULT_PARAMS["num_leaves"])
    p.add_argument("--min-child-samples", type=int, default=DEFAULT_PARAMS["min_child_samples"])
    p.add_argument("--n-splits", type=int, default=4)
    p.add_argument("--horizon", type=int, default=4, help="Weeks per test block")
    p.add_argument("--experiment", default="retail-demand-forecasting")
    p.add_argument("--mlflow-uri", default=None, help="Override MLflow tracking URI (local runs)")
    return p


def main(argv: list[str] | None = None) -> None:
    run(build_parser().parse_args(argv))


if __name__ == "__main__":
    main()
