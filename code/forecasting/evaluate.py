"""Release gate for the demand model (the evaluate step of the pipeline).

Reads the metrics.json written by ``forecasting.train`` and decides whether the
model is good enough to register/promote. The gate is a *pure* function so the
same rule is testable in isolation and reusable by the Module 6 deployment lab
and the Module 7 CI pipeline.

Default thresholds (documented, not magic): the model must beat the naive
baseline (MASE < 1), keep volume-weighted error under 30% WAPE, and stay close
to unbiased (|bias| <= 5%). Tune these for your own service-level targets.

Run (WSL / Python), from code/:
    python -m forecasting.evaluate --metrics ../data/model/metrics.json
Exit code 0 = passes the gate; 1 = blocked.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Thresholds:
    wape_max: float = 0.30
    abs_bias_max: float = 0.05
    mase_max: float = 1.0


@dataclass
class Decision:
    passed: bool
    reasons: list[str]
    wape: float
    bias: float
    mase: float


def release_decision(aggregate: dict, thresholds: Thresholds | None = None) -> Decision:
    t = thresholds or Thresholds()
    wape = float(aggregate.get("wape", float("nan")))
    bias = float(aggregate.get("bias", float("nan")))
    mase = float(aggregate.get("mase", float("nan")))
    reasons: list[str] = []

    if not math.isfinite(wape) or wape > t.wape_max:
        reasons.append(f"WAPE {wape:.3f} exceeds max {t.wape_max}")
    if not math.isfinite(bias) or abs(bias) > t.abs_bias_max:
        reasons.append(f"|bias| {abs(bias):.3f} exceeds max {t.abs_bias_max}")
    if not math.isfinite(mase) or mase >= t.mase_max:
        reasons.append(f"MASE {mase:.3f} does not beat naive baseline (< {t.mase_max})")

    return Decision(passed=not reasons, reasons=reasons, wape=wape, bias=bias, mase=mase)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Apply the model release gate")
    p.add_argument("--metrics", required=True, help="Path to metrics.json from training")
    p.add_argument("--wape-max", type=float, default=Thresholds.wape_max)
    p.add_argument("--abs-bias-max", type=float, default=Thresholds.abs_bias_max)
    p.add_argument("--mase-max", type=float, default=Thresholds.mase_max)
    p.add_argument("--output", default=None, help="Optional path to write the decision JSON")
    args = p.parse_args(argv)

    aggregate = json.loads(Path(args.metrics).read_text(encoding="utf-8"))["aggregate"]
    decision = release_decision(aggregate, Thresholds(args.wape_max, args.abs_bias_max, args.mase_max))

    print(json.dumps(asdict(decision), indent=2))
    if args.output:
        Path(args.output).write_text(json.dumps(asdict(decision), indent=2), encoding="utf-8")
    if not decision.passed:
        print("RELEASE BLOCKED: " + "; ".join(decision.reasons))
        return 1
    print("RELEASE APPROVED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
