"""Forecast accuracy metrics for demand forecasting.

All functions take 1-D numpy arrays or pandas Series of the same length and
return plain floats, so they are easy to log to MLflow and to test.

Definitions used in this course (stated explicitly because the same acronym is
used for slightly different formulas elsewhere):

- **WAPE** (weighted absolute percentage error): ``sum|y - yhat| / sum|y|``.
  Preferred over MAPE for demand because it is defined when individual actuals
  are zero (common for slow movers) and it weights by volume.
- **Bias**: ``sum(yhat - y) / sum(y)``, a *signed* number. Positive means the
  model over-forecasts on balance; negative means it under-forecasts.
- **MASE** (mean absolute scaled error): model MAE divided by the in-sample MAE
  of a naive (random-walk) forecast on the *training* series, per
  Hyndman & Koehler (2006). MASE < 1 means the model beats the naive baseline.
  We scale with the one-step naive (m=1) by default; the synthetic history is
  only ~2 years, too short for a stable seasonal (m=52) scale.
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-9


def _arr(x) -> np.ndarray:
    return np.asarray(x, dtype="float64")


def mae(y_true, y_pred) -> float:
    """Mean absolute error."""
    y_true, y_pred = _arr(y_true), _arr(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))


def wape(y_true, y_pred) -> float:
    """Weighted absolute percentage error = sum|e| / sum|y|."""
    y_true, y_pred = _arr(y_true), _arr(y_pred)
    denom = np.sum(np.abs(y_true))
    return float(np.sum(np.abs(y_true - y_pred)) / (denom + _EPS))


def bias(y_true, y_pred) -> float:
    """Signed relative bias = sum(yhat - y) / sum(y). Positive = over-forecast."""
    y_true, y_pred = _arr(y_true), _arr(y_pred)
    denom = np.sum(np.abs(y_true))
    return float(np.sum(y_pred - y_true) / (denom + _EPS))


def seasonal_naive_mae(history, season_length: int = 1) -> float:
    """In-sample MAE of the naive forecast ``y_t = y_{t-season_length}``.

    Used as the MASE denominator. ``history`` must be ordered in time.
    Returns NaN when there are too few points to form a single naive error.
    """
    h = _arr(history)
    if h.size <= season_length:
        return float("nan")
    diffs = np.abs(h[season_length:] - h[:-season_length])
    return float(np.mean(diffs)) if diffs.size else float("nan")
