"""Parquet I/O over local disk or ADLS Gen2, with identity-based auth.

pandas and PyArrow read/write Parquet through fsspec, so the *same* call works
on a local path and on an ``abfss://``/``az://`` URI once you pass the right
storage options. On ADLS Gen2 we authenticate with ``DefaultAzureCredential``
via adlfs (``anon=False``) - your ``az login`` locally, a managed identity in
Azure - never an account key.

Run (WSL / Python), from code/:
    python -m storage.parquet_io ../data/raw/pos_sales ../data/parquet/pos_sales
"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


def adls_storage_options(account: str | None = None) -> dict:
    """fsspec/adlfs options for ADLS Gen2 using DefaultAzureCredential.

    ``anon`` defaults to True in adlfs (public access), so ``anon=False`` is what
    switches it to the DefaultAzureCredential chain. Pass the account name, or set
    AZURE_STORAGE_ACCOUNT_NAME in the environment.
    """
    account = account or os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    if not account:
        raise ValueError("Provide an account name or set AZURE_STORAGE_ACCOUNT_NAME")
    return {"account_name": account, "anon": False}


def write_parquet(df: pd.DataFrame, path: str, *, storage_options: dict | None = None,
                  partition_cols: list[str] | None = None, compression: str = "snappy") -> None:
    """Write a DataFrame to Parquet (a single file, or a partitioned dataset).

    With ``partition_cols`` the output is a directory of ``col=value/`` folders
    (Hive-style), which lets readers prune partitions. Works local or on ADLS.
    """
    if "://" not in path and partition_cols is None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)   # local single-file write
    df.to_parquet(path, engine="pyarrow", compression=compression,
                  partition_cols=partition_cols, index=False,
                  storage_options=storage_options)


def read_parquet(path: str, *, storage_options: dict | None = None,
                 columns: list[str] | None = None, filters=None) -> pd.DataFrame:
    """Read Parquet with optional column projection and predicate pushdown.

    ``columns`` reads only those columns; ``filters`` (PyArrow form, e.g.
    ``[("region", "==", "North")]``) prunes partitions/row groups before loading.
    """
    return pd.read_parquet(path, engine="pyarrow", columns=columns, filters=filters,
                           storage_options=storage_options)


def dataset_stats(path: str, storage_options: dict | None = None) -> dict:
    """Row count, file count and sizing for a Parquet file or dataset (local).

    Teaches the small-files problem: many tiny files are slow to list and read.
    Aim for larger files (roughly 100 MB-1 GB) in production datasets.
    """
    p = Path(path)
    files = [str(p)] if p.is_file() else sorted(glob.glob(str(p / "**" / "*.parquet"), recursive=True))
    total_rows = sum(pq.ParquetFile(f).metadata.num_rows for f in files)
    total_bytes = sum(os.path.getsize(f) for f in files)
    n = len(files)
    return {
        "files": n,
        "rows": total_rows,
        "total_mb": round(total_bytes / 1e6, 3),
        "avg_file_mb": round(total_bytes / 1e6 / n, 3) if n else 0.0,
    }


def _csv_dir_to_parquet(csv_dir: str, out: str) -> int:
    frames = [pd.read_csv(f) for f in sorted(glob.glob(str(Path(csv_dir) / "*.csv")))]
    if not frames:
        raise SystemExit(f"No CSVs under {csv_dir}")
    df = pd.concat(frames, ignore_index=True)
    write_parquet(df, out)
    return len(df)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Convert a folder of CSVs to Parquet and report sizing")
    p.add_argument("csv_dir")
    p.add_argument("out")
    a = p.parse_args(argv)
    rows = _csv_dir_to_parquet(a.csv_dir, a.out)
    print(f"wrote {rows} rows -> {a.out}:", dataset_stats(a.out))


if __name__ == "__main__":
    main()
