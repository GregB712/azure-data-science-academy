"""Tests for the data product registry and contract compatibility checker."""
from pathlib import Path

import yaml

from data_mesh import contract_compat, registry

CODE = Path(__file__).resolve().parents[1]


def test_registry_has_no_errors():
    findings = registry.validate(registry.load_products())
    assert [f for f in findings if f.level == "error"] == []


def test_registry_warns_about_published_products_without_contracts():
    findings = registry.validate(registry.load_products())
    assert any("no data contract" in f.message and f.product == "sales.store-directory" for f in findings)


def test_impact_analysis_finds_transitive_consumers():
    affected = registry.downstream(registry.load_products(), "sales.pos-transactions")
    assert {"supply-chain.demand-features", "supply-chain.demand-forecast",
            "finance.revenue-reconciliation", "sales.daily-sales-summary"} <= set(affected)


def test_cycle_is_detected(tmp_path):
    for a, b in (("x.a", "x.b"), ("x.b", "x.a")):
        (tmp_path / f"{a}.yaml").write_text(yaml.safe_dump({
            "id": a, "name": a, "domain": "x", "type": "aggregate", "status": "draft", "version": "0.1.0",
            "owner": "o", "description": "d", "classification": "internal",
            "input_ports": [{"product": b}], "output_ports": [{"name": "delta", "contract": None}]}))
    findings = registry.validate(registry.load_products(tmp_path))
    assert any("cycle" in f.message for f in findings)


def test_proposal_with_rename_is_rejected_as_minor():
    ok, changes, need, got = contract_compat.check(
        CODE / "contracts/sales.pos_sales.v1.yaml",
        CODE / "contracts/proposals/sales.pos_sales.v1.1-proposal.yaml")
    assert not ok and need == "major" and got == "minor"
    assert any("stockout" in c.message and c.kind == "breaking" for c in changes)


def test_adding_optional_column_is_minor(tmp_path):
    c = yaml.safe_load((CODE / "contracts/sales.pos_sales.v1.yaml").read_text())
    c["version"] = "1.1.0"
    c["schema"][0]["properties"].append({"name": "channel", "logicalType": "string", "required": False})
    p = tmp_path / "v11.yaml"
    p.write_text(yaml.safe_dump(c))
    ok, _, need, got = contract_compat.check(CODE / "contracts/sales.pos_sales.v1.yaml", p)
    assert ok and need == "minor" and got == "minor"
