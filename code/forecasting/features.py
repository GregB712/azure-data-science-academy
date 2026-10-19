"""Feature preparation for the weekly demand model.

The Gold table ``gold/weekly_demand_features`` (see the data contract in
``code/contracts/forecasting.demand_features.v1.yaml``) already carries the
expensive-to-compute lag and rolling features. This module turns that table
into the exact matrix the model trains on: it adds a few cheap calendar and
trend columns and fixes dtypes so LightGBM treats identifiers as categoricals
rather than numbers.

No target leakage is introduced here: every engineered column is known at the
start of ``week_start`` (lags and rolling means were shifted when the Gold table
was built, and calendar features are deterministic).
"""

from __future__ import annotations

import pandas as pd

TARGET = "units"

# Identifiers and the category are categorical; LightGBM learns per-level splits
# without one-hot encoding when the column has pandas 'category' dtype.
CATEGORICAL_FEATURES = ["store_id", "product_id", "category"]

# Numeric drivers already present in Gold, plus the calendar/trend columns added
# by make_features(). units_lag_52 is kept even though a short backtest leaves it
# all-NaN: LightGBM handles missing values natively and it matters on full history.
NUMERIC_FEATURES = [
    "avg_price",
    "promo_days",
    "stockout_days",
    "holiday_days",
    "units_lag_1",
    "units_lag_2",
    "units_lag_52",
    "units_roll_mean_4",
    "week_of_year",
    "month",
    "weeks_since_start",
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES
KEY_COLUMNS = ["week_start", "store_id", "product_id"]


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the Gold table with model features and correct dtypes.

    Adds week_of_year, month and a per-dataset weeks_since_start trend index.
    Rows are returned sorted by (store_id, product_id, week_start) so that any
    downstream time-ordered operation is correct.
    """
    out = df.copy()
    out["week_start"] = pd.to_datetime(out["week_start"])

    iso = out["week_start"].dt.isocalendar()
    out["week_of_year"] = iso["week"].astype("int64")
    out["month"] = out["week_start"].dt.month.astype("int64")
    first_week = out["week_start"].min()
    out["weeks_since_start"] = ((out["week_start"] - first_week).dt.days // 7).astype("int64")

    for col in CATEGORICAL_FEATURES:
        out[col] = out[col].astype("category")

    missing = [c for c in FEATURE_COLUMNS + [TARGET] if c not in out.columns]
    if missing:
        raise ValueError(f"Gold table is missing expected columns: {missing}")

    out = out.sort_values(["store_id", "product_id", "week_start"]).reset_index(drop=True)
    return out
