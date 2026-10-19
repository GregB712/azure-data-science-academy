"""Validate the Gold feature table against its data contract before training.

This is the first step of the training pipeline (validate -> train -> evaluate).
It reuses the same contract-driven checker as the lakehouse Silver/Gold gates
(``lakehouse_local.quality``) so the pipeline enforces exactly the contract in
``code/contracts/forecasting.demand_features.v1.yaml`` -- no second definition
of "valid" to drift out of sync.

Run (WSL / Python), from code/:
    python -m forecasting.validate --data ../data/lake/gold/weekly_demand_features
Exit code 0 = contract satisfied; 1 = failed (nothing should train on bad data).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lakehouse_local import quality

from .train import load_gold

DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "forecasting.demand_features.v1.yaml"


def validate_gold(data: str, contract_path: str | Path = DEFAULT_CONTRACT) -> quality.ValidationReport:
    df = load_gold(data)
    contract = quality.load_contract(contract_path)
    cols = quality.contract_columns(contract)
    _, _, report = quality.validate(df[cols], contract, max_quarantine_ratio=0.0)
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate the Gold table against its contract")
    p.add_argument("--data", required=True, help="Path/URI of the Gold Delta table")
    p.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    p.add_argument("--output", default=None, help="Optional folder for a validation marker (pipeline step)")
    args = p.parse_args(argv)

    report = validate_gold(args.data, args.contract)
    print(report.summary())
    if args.output:
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        (out / "validation.json").write_text(
            json.dumps({"passed": report.passed, "rows_valid": report.rows_valid}, indent=2),
            encoding="utf-8")
    if not report.passed:
        print("CONTRACT FAILED: refusing to train on data that breaks the contract.", file=sys.stderr)
        return 1
    print("CONTRACT OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
