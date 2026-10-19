"""Demand forecasting baseline for the retail capstone (Module 5).

The same code runs three ways, unchanged:
  - locally against the Delta Gold table produced by ``lakehouse_local`` (no Azure),
  - as an Azure Machine Learning command job on serverless compute,
  - as the train step of an Azure ML pipeline.

Keeping one script means the thing you backtest locally is the thing that trains
in the cloud. See ``docs/azure-machine-learning/`` for the lessons that use it.
"""

from .metrics import bias, mae, wape, seasonal_naive_mae
from .features import FEATURE_COLUMNS, CATEGORICAL_FEATURES, TARGET, make_features
from .backtest import temporal_splits

__all__ = [
    "bias",
    "mae",
    "wape",
    "seasonal_naive_mae",
    "FEATURE_COLUMNS",
    "CATEGORICAL_FEATURES",
    "TARGET",
    "make_features",
    "temporal_splits",
]
