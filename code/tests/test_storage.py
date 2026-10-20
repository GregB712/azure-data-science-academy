"""Tests for the Module 2 Parquet I/O helpers. Local only (no Azure)."""
from __future__ import annotations

import pandas as pd
import pytest

from storage import parquet_io


def _df() -> pd.DataFrame:
    return pd.DataFrame({
        "region": ["North", "North", "South", "South", "West"],
        "store_id": ["S1", "S2", "S3", "S4", "S5"],
        "units": [10, 20, 30, 40, 50],
        "revenue": [1.5, 2.5, 3.5, 4.5, 5.5],
    })


def test_single_file_round_trip(tmp_path):
    df = _df()
    path = str(tmp_path / "data.parquet")
    parquet_io.write_parquet(df, path)
    back = parquet_io.read_parquet(path)
    pd.testing.assert_frame_equal(df, back)


def test_partitioned_write_and_partition_pruning(tmp_path):
    df = _df()
    out = str(tmp_path / "ds")
    parquet_io.write_parquet(df, out, partition_cols=["region"])
    # Hive-style partition folders exist
    assert (tmp_path / "ds" / "region=North").is_dir()
    assert (tmp_path / "ds" / "region=South").is_dir()
    # full read preserves all rows
    assert len(parquet_io.read_parquet(out)) == 5
    # predicate pushdown returns only the matching partition
    north = parquet_io.read_parquet(out, filters=[("region", "==", "North")])
    assert len(north) == 2 and set(north["store_id"]) == {"S1", "S2"}


def test_column_projection(tmp_path):
    path = str(tmp_path / "data.parquet")
    parquet_io.write_parquet(_df(), path)
    cols = parquet_io.read_parquet(path, columns=["store_id", "units"])
    assert list(cols.columns) == ["store_id", "units"]


def test_dataset_stats(tmp_path):
    out = str(tmp_path / "ds")
    parquet_io.write_parquet(_df(), out, partition_cols=["region"])
    stats = parquet_io.dataset_stats(out)
    assert stats["rows"] == 5
    assert stats["files"] >= 3          # one file per region partition
    assert stats["total_mb"] >= 0


def test_adls_storage_options():
    opts = parquet_io.adls_storage_options("myaccount")
    assert opts == {"account_name": "myaccount", "anon": False}
    with pytest.raises(ValueError):
        parquet_io.adls_storage_options(None)
