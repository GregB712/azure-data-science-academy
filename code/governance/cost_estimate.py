"""Monthly cost estimate for the forecasting platform, with per-domain allocation.

A FinOps calculator: you supply each component's monthly cost (from the Azure
pricing calculator or the Retail Prices API - see labs/lab-01-azure-setup/python/
price_check.py), and it totals the bill, separates the **standing** cost (what
you pay even when idle) from the usage cost, and allocates by domain/tag.

IMPORTANT: the amounts in DEFAULT_PLATFORM are ILLUSTRATIVE placeholders to show
the shape of the bill, not real prices. Replace them with current quotes for
your region and SKUs. The point is the method, not the numbers.

Run (WSL / Python), from code/:
    python -m governance.cost_estimate
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostLine:
    name: str
    domain: str
    monthly_usd: float          # supply from the pricing calculator / Retail Prices API
    standing: bool = False      # True if it bills even when idle (e.g. ACR, AI Search)


# Illustrative monthly figures (NOT real prices) to demonstrate the breakdown.
# The design keeps standing cost tiny (ACR + storage); everything else scales to zero.
DEFAULT_PLATFORM: list[CostLine] = [
    CostLine("Serverless training (4 weekly runs)", "ml", 3.0),
    CostLine("Weekly scoring job (scale-to-zero)", "ml", 2.0),
    CostLine("Container Registry (Basic)", "ml", 5.0, standing=True),
    CostLine("ADLS Gen2 storage (Delta tables)", "data", 1.0, standing=True),
    CostLine("Model monitoring (serverless Spark)", "mlops", 4.0),
    CostLine("Log Analytics ingestion", "mlops", 3.0),
    CostLine("Azure AI Search (Basic, if kept)", "genai", 75.0, standing=True),
]


def estimate(lines: list[CostLine]) -> dict:
    """Total the bill, split standing vs usage, and allocate by domain."""
    total = round(sum(l.monthly_usd for l in lines), 2)
    standing = round(sum(l.monthly_usd for l in lines if l.standing), 2)
    by_domain: dict[str, float] = {}
    for l in lines:
        by_domain[l.domain] = round(by_domain.get(l.domain, 0.0) + l.monthly_usd, 2)
    return {
        "total_monthly_usd": total,
        "standing_monthly_usd": standing,     # paid even if nothing runs
        "usage_monthly_usd": round(total - standing, 2),
        "by_domain": by_domain,
        "note": "Illustrative inputs; replace monthly_usd with current prices.",
    }


def main() -> None:
    import json
    print(json.dumps(estimate(DEFAULT_PLATFORM), indent=2))


if __name__ == "__main__":
    main()
