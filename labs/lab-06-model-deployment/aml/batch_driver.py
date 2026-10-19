"""Batch endpoint scoring script (Azure ML calls init() once, run() per mini-batch).

The batch endpoint scores the *scoring-input* matrix (one independent row per
series, written by `forecasting.score --scoring-input`). Each row is stateless,
which is what batch endpoints are good at. run() returns a DataFrame; with
output_action=APPEND_ROW the endpoint collects them into one output file, keys
included.

Not executed in the course build. Requires the forecasting package on the
deployment's code path and the registered MLflow model mounted at
AZUREML_MODEL_DIR.
"""

from __future__ import annotations

import os
from pathlib import Path

import mlflow.lightgbm
import pandas as pd

from forecasting.score import predict_rows

_model = None


def init() -> None:
    global _model
    # The registered MLflow model is mounted here; load the LightGBM Booster.
    model_dir = os.environ["AZUREML_MODEL_DIR"]
    candidates = list(Path(model_dir).rglob("MLmodel"))
    _model = mlflow.lightgbm.load_model(str(candidates[0].parent) if candidates else model_dir)


def run(mini_batch: list[str]) -> pd.DataFrame:
    frames = []
    for file_path in mini_batch:
        df = pd.read_parquet(file_path)          # parquet preserves categorical dtypes/codes
        preds = predict_rows(_model, df)
        out = df[["week_start", "store_id", "product_id"]].copy()
        out["forecast_units"] = preds.round(2)
        frames.append(out)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
