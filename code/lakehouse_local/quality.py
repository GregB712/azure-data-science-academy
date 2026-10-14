"""Contract-driven data quality checks.

Reads a (simplified) ODCS v3 data contract and validates a pandas DataFrame
against it. Row-level failures are split into a quarantine frame with a reason,
so Silver tables only contain rows that honour the contract. Table-level rules
(uniqueness, row count) are reported as check results.

This is deliberately small and dependency-light so you can read all of it.
In production you would typically use Databricks/Lakeflow expectations,
Microsoft Purview Data Quality, Great Expectations, Soda or pandera, and keep
the *contract* as the source of truth that those tools are configured from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

LOGICAL_TO_PANDAS = {
    "string": "string",
    "integer": "Int64",
    "number": "float64",
    "boolean": "boolean",
    "date": "date",
}


@dataclass
class CheckResult:
    rule: str
    target: str
    passed: bool
    failed_rows: int = 0
    detail: str = ""
    level: str = "row"  # "row" rules quarantine rows; "table" rules gate the whole batch


@dataclass
class ValidationReport:
    contract_id: str
    rows_in: int
    rows_valid: int
    rows_quarantined: int
    checks: list[CheckResult] = field(default_factory=list)
    max_quarantine_ratio: float = 0.01

    @property
    def quarantine_ratio(self) -> float:
        return self.rows_quarantined / self.rows_in if self.rows_in else 0.0

    @property
    def passed(self) -> bool:
        """A batch passes when every table-level rule passes and the share of
        quarantined rows stays under the agreed threshold. Row-level failures on
        their own do not fail the batch; they are isolated in quarantine."""
        tables_ok = all(c.passed for c in self.checks if c.level == "table")
        return tables_ok and self.quarantine_ratio <= self.max_quarantine_ratio

    def summary(self) -> str:
        lines = [f"contract={self.contract_id} in={self.rows_in} valid={self.rows_valid} "
                 f"quarantined={self.rows_quarantined} ({self.quarantine_ratio:.3%}) "
                 f"batch={'PASSED' if self.passed else 'FAILED'}"]
        for c in self.checks:
            mark = "PASS" if c.passed else ("FAIL" if c.level == "table" else "QUAR")
            lines.append(f"  [{mark}] {c.rule:<12} {c.target:<28} failed_rows={c.failed_rows} {c.detail}")
        return "\n".join(lines)


def load_contract(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _cast(series: pd.Series, logical_type: str) -> tuple[pd.Series, pd.Series]:
    """Cast a column to the contract's logical type. Returns (casted, cast_failed_mask)."""
    if series.dtype == object or pd.api.types.is_string_dtype(series):
        series = series.replace("", pd.NA)  # Bronze stores missing values as empty text
    raw_null = series.isna()
    if logical_type == "date":
        casted = pd.to_datetime(series, errors="coerce").dt.date
    elif logical_type == "integer":
        num = pd.to_numeric(series, errors="coerce")
        non_int = num.notna() & (num % 1 != 0)
        casted = num.where(~non_int).astype("Int64")
    elif logical_type == "number":
        casted = pd.to_numeric(series, errors="coerce").astype("float64")
    elif logical_type == "boolean":
        mapping = {"true": True, "false": False, "1": True, "0": False}
        casted = series.astype("string").str.lower().map(mapping).astype("boolean")
    else:
        casted = series.astype("string")
    failed = casted.isna() & ~raw_null
    return casted, failed


def validate(df: pd.DataFrame, contract: dict[str, Any],
             references: dict[str, set[str]] | None = None,
             max_quarantine_ratio: float = 0.01) -> tuple[pd.DataFrame, pd.DataFrame, ValidationReport]:
    """Validate df against the first schema object in the contract.

    references maps "table.column" -> allowed values, for referential rules.
    Returns (valid_rows, quarantined_rows, report).
    """
    references = references or {}
    schema = contract["schema"][0]
    props = schema["properties"]
    out = df.copy()
    reasons = pd.Series("", index=out.index, dtype="string")
    checks: list[CheckResult] = []

    def flag(mask: pd.Series, reason: str, rule: str, target: str, detail: str = "") -> None:
        nonlocal reasons
        mask = mask.fillna(False).astype(bool)
        reasons = reasons.where(~mask, reasons + reason + ";")
        checks.append(CheckResult(rule, target, passed=not mask.any(), failed_rows=int(mask.sum()), detail=detail))

    missing = [p["name"] for p in props if p["name"] not in out.columns]
    if missing:
        raise ValueError(f"Input is missing contract columns: {missing}")

    for p in props:
        name, ltype = p["name"], p.get("logicalType", "string")
        casted, cast_failed = _cast(out[name], ltype)
        out[name] = casted
        flag(cast_failed, f"{name}:type", "type", name, f"expected {ltype}")
        if p.get("required"):
            flag(out[name].isna() & ~cast_failed, f"{name}:null", "notNull", name)
        for q in p.get("quality", []) or []:
            rule = q["rule"]
            col = out[name]
            if rule == "range":
                bad = pd.Series(False, index=out.index)
                if "mustBeGreaterThan" in q:
                    bad |= col <= q["mustBeGreaterThan"]
                if "mustBeGreaterThanOrEqualTo" in q:
                    bad |= col < q["mustBeGreaterThanOrEqualTo"]
                if "mustBeLessThan" in q:
                    bad |= col >= q["mustBeLessThan"]
                if "mustBeLessThanOrEqualTo" in q:
                    bad |= col > q["mustBeLessThanOrEqualTo"]
                flag(bad & col.notna(), f"{name}:range", "range", name)
            elif rule == "pattern":
                rx = re.compile(q["pattern"])
                bad = col.notna() & ~col.astype("string").fillna("").map(lambda v: bool(rx.match(v)))
                flag(bad, f"{name}:pattern", "pattern", name, q["pattern"])
            elif rule == "referential":
                ref = q["reference"]
                if ref not in references:
                    checks.append(CheckResult("referential", name, passed=True, detail=f"skipped: no reference '{ref}'"))
                    continue
                bad = col.notna() & ~col.isin(references[ref])
                flag(bad, f"{name}:referential", "referential", name, ref)
            else:
                raise ValueError(f"Unsupported rule '{rule}' on {name}")

    is_bad = reasons != ""
    valid = out[~is_bad].copy()
    quarantined = df[is_bad].copy()
    quarantined["_reject_reason"] = reasons[is_bad].str.rstrip(";")

    for q in schema.get("quality", []) or []:
        if q["rule"] == "unique":
            dup = valid.duplicated(subset=q["columns"], keep=False)
            checks.append(CheckResult("unique", ",".join(q["columns"]), passed=not dup.any(),
                                      failed_rows=int(dup.sum()), level="table"))
        elif q["rule"] == "rowCount":
            n = len(valid)
            ok = n > q.get("mustBeGreaterThan", -1)
            checks.append(CheckResult("rowCount", schema["name"], passed=ok, detail=f"rows={n}", level="table"))

    report = ValidationReport(contract.get("id", "?"), len(df), len(valid), len(quarantined), checks,
                              max_quarantine_ratio)
    return valid, quarantined, report


def contract_columns(contract: dict[str, Any]) -> list[str]:
    return [p["name"] for p in contract["schema"][0]["properties"]]
