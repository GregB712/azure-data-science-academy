"""Load store reference data into Azure SQL Database with Entra auth (no password).

Reads the synthetic stores.csv and upserts it into a serverless Azure SQL
Database, connecting via pyodbc with a Microsoft Entra access token. This is the
Module 2 passwordless pattern; see docs/storage-and-data-engineering/03-azure-sql.md.

Run (WSL / Python), with ODBC Driver 18 and pyodbc installed, signed in (az login):
    pip install pyodbc azure-identity
    python load_reference_data.py --server <srv>.database.windows.net --database refdata \
        --stores ../../../data/raw/stores.csv

Not executed in the course build (no subscription). The token/connection pattern
follows Microsoft's passwordless Python documentation.
"""

from __future__ import annotations

import argparse
import struct

import pandas as pd

SQL_COPT_SS_ACCESS_TOKEN = 1256   # from msodbcsql.h

DDL = """
IF OBJECT_ID('dbo.store_directory', 'U') IS NULL
CREATE TABLE dbo.store_directory (
    store_id       NVARCHAR(16) NOT NULL PRIMARY KEY,
    region         NVARCHAR(32) NOT NULL,
    city           NVARCHAR(64) NOT NULL,
    store_size_sqm INT          NOT NULL
);
"""


def _token_struct() -> bytes:
    from azure.identity import DefaultAzureCredential
    token = DefaultAzureCredential().get_token("https://database.windows.net/.default").token
    packed = token.encode("utf-16-le")
    return struct.pack(f"<I{len(packed)}s", len(packed), packed)


def main() -> None:
    import pyodbc

    p = argparse.ArgumentParser()
    p.add_argument("--server", required=True, help="<name>.database.windows.net")
    p.add_argument("--database", required=True)
    p.add_argument("--stores", required=True, help="Path to stores.csv")
    args = p.parse_args()

    stores = pd.read_csv(args.stores)[["store_id", "region", "city", "store_size_sqm"]]

    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{args.server},1433;Database={args.database};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
    )
    # No UID/PWD/Authentication in the string: the Entra token carries identity.
    with pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: _token_struct()}) as conn:
        cur = conn.cursor()
        cur.execute(DDL)
        cur.fast_executemany = True
        cur.execute("TRUNCATE TABLE dbo.store_directory;")
        cur.executemany(
            "INSERT INTO dbo.store_directory (store_id, region, city, store_size_sqm) VALUES (?, ?, ?, ?)",
            stores.itertuples(index=False, name=None),
        )
        conn.commit()
        n = cur.execute("SELECT COUNT(*) FROM dbo.store_directory;").fetchone()[0]
        print(f"Loaded {n} store rows into {args.database}.dbo.store_directory")


if __name__ == "__main__":
    main()
