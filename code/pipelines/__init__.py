"""Pipeline building blocks for Module 4 (Data Pipelines and Scalable Processing).

Incremental Bronze->Silver processing with a high-watermark, a Delta change data
feed demo, and SCD type 2 upserts - all runnable locally on delta-rs, no Spark.
These are the patterns an orchestrator (ADF, Fabric Data Factory, Lakeflow Jobs)
schedules; the lessons show the Spark/cloud equivalents.
"""

from .incremental import (
    change_feed,
    load_watermark,
    save_watermark,
    scd2_upsert,
    silver_incremental,
)

__all__ = [
    "change_feed",
    "load_watermark",
    "save_watermark",
    "scd2_upsert",
    "silver_incremental",
]
