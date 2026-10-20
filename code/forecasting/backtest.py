"""Temporal (rolling-origin) backtesting splits.

Random k-fold cross-validation leaks the future into the past and flatters a
forecaster badly. We instead split on time: every test week is strictly later
than every training week in the same fold. The window *expands* (each fold
keeps all earlier history) which matches how the model is retrained in
production as new weeks arrive.

``temporal_splits`` works on the sorted unique week-start dates, so it is
independent of how many product-store series exist on each date.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd


def temporal_splits(
    weeks: Iterable,
    n_splits: int = 4,
    horizon: int = 4,
    min_train_weeks: int = 8,
) -> list[tuple[list, list]]:
    """Return ``n_splits`` (train_weeks, test_weeks) folds over the ordered weeks.

    - ``horizon``: number of consecutive weeks in each test block (the forecast
      horizon being evaluated).
    - ``min_train_weeks``: the earliest fold must train on at least this many
      weeks, otherwise fewer folds are returned.
    - Folds are anchored at the end of the series so the last fold tests the most
      recent ``horizon`` weeks; earlier folds step back ``horizon`` weeks each.

    Guarantees: within a fold, ``max(train_weeks) < min(test_weeks)`` (no
    leakage) and the window expands (``train_weeks`` of a later fold is a
    superset of an earlier fold's).
    """
    ordered = sorted(pd.unique(pd.Series(list(weeks))))
    n = len(ordered)
    folds: list[tuple[list, list]] = []
    for k in range(n_splits):
        test_end = n - k * horizon
        test_start = test_end - horizon
        if test_start < min_train_weeks:
            break
        train_weeks = ordered[:test_start]
        test_weeks = ordered[test_start:test_end]
        folds.append((list(train_weeks), list(test_weeks)))
    folds.reverse()  # chronological order: earliest training window first
    return folds
