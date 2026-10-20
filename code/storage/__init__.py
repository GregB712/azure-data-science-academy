"""Storage access helpers for Module 2 (Cloud Storage and Data Access).

Read and write Parquet with pandas/PyArrow, locally or on ADLS Gen2 through
adlfs/fsspec with identity-based auth (no keys). The same functions take a local
path or an ``abfss://`` / ``az://`` URI plus storage options.
"""

from .parquet_io import (
    adls_storage_options,
    dataset_stats,
    read_parquet,
    write_parquet,
)

__all__ = ["adls_storage_options", "dataset_stats", "read_parquet", "write_parquet"]
