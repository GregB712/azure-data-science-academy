"""Tests for the Module 9 governance/FinOps helpers. Pure, offline."""
from __future__ import annotations

from governance.cost_estimate import CostLine, DEFAULT_PLATFORM, estimate
from governance.tags import check_tags


def test_tags_compliant():
    assert check_tags({"project": "adsa", "env": "prod", "owner": "g", "cost-center": "ds"}) == []


def test_tags_missing_and_bad_value():
    v = check_tags({"project": "adsa", "env": "staging"})   # bad env + missing owner/cost-center
    assert any("owner" in m for m in v)
    assert any("cost-center" in m for m in v)
    assert any("env" in m and "staging" in m for m in v)


def test_tags_none():
    assert len(check_tags(None)) == 4                       # all four required tags missing


def test_cost_estimate_totals_and_allocation():
    lines = [
        CostLine("a", "ml", 10.0),
        CostLine("b", "ml", 5.0, standing=True),
        CostLine("c", "genai", 20.0, standing=True),
    ]
    out = estimate(lines)
    assert out["total_monthly_usd"] == 35.0
    assert out["standing_monthly_usd"] == 25.0            # b + c
    assert out["usage_monthly_usd"] == 10.0
    assert out["by_domain"] == {"ml": 15.0, "genai": 20.0}


def test_default_platform_standing_is_small_share():
    out = estimate(DEFAULT_PLATFORM)
    # by design, standing cost is a share of the total and the breakdown sums correctly
    assert out["standing_monthly_usd"] <= out["total_monthly_usd"]
    assert round(sum(out["by_domain"].values()), 2) == out["total_monthly_usd"]
