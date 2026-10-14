"""A minimal data product registry: the "control port" of a data mesh, in miniature.

Each domain describes its data products in a YAML descriptor (see products/).
This tool loads them, enforces global (federated) policies, and answers the
questions a catalog must answer: what exists, who owns it, what does it depend
on, and who is affected if it changes.

In Azure the same role is played by Microsoft Purview Unified Catalog
(governance domains, data products), Unity Catalog and the OneLake catalog.
The descriptors are the kind of metadata you would push into those catalogs
from CI, so the catalog never drifts from what the domains actually ship.

Run (WSL, from code/):
    python data_mesh/registry.py validate
    python data_mesh/registry.py list
    python data_mesh/registry.py impact sales.pos-transactions
    python data_mesh/registry.py mermaid > ../diagrams/generated-product-lineage.mmd
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PRODUCTS_DIR = Path(__file__).resolve().parent / "products"

REQUIRED_FIELDS = ["id", "name", "domain", "type", "status", "version", "owner", "description",
                   "classification", "output_ports"]
ALLOWED_TYPES = {"source-aligned", "aggregate", "consumer-aligned"}
ALLOWED_STATUS = {"planned", "draft", "published", "deprecated", "retired"}
ALLOWED_CLASSIFICATION = {"public", "internal", "confidential", "highly-confidential"}
CLASS_RANK = {c: i for i, c in enumerate(["public", "internal", "confidential", "highly-confidential"])}


@dataclass
class Finding:
    level: str  # "error" | "warning"
    product: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper():7} {self.product:<34} {self.message}"


def load_products(directory: Path = PRODUCTS_DIR) -> dict[str, dict[str, Any]]:
    products: dict[str, dict[str, Any]] = {}
    for f in sorted(directory.glob("*.yaml")):
        with open(f, encoding="utf-8") as fh:
            p = yaml.safe_load(fh)
        p["_file"] = f
        products[p["id"]] = p
    return products


def upstream(p: dict[str, Any]) -> list[str]:
    return [i["product"] for i in p.get("input_ports", []) or [] if "product" in i]


def validate(products: dict[str, dict[str, Any]]) -> list[Finding]:
    """Global policies every domain must follow (federated computational governance)."""
    out: list[Finding] = []
    for pid, p in products.items():
        for field in REQUIRED_FIELDS:
            if p.get(field) in (None, "", []):
                out.append(Finding("error", pid, f"missing required field '{field}'"))
        if p.get("type") not in ALLOWED_TYPES:
            out.append(Finding("error", pid, f"type must be one of {sorted(ALLOWED_TYPES)}"))
        if p.get("status") not in ALLOWED_STATUS:
            out.append(Finding("error", pid, f"status must be one of {sorted(ALLOWED_STATUS)}"))
        if p.get("classification") not in ALLOWED_CLASSIFICATION:
            out.append(Finding("error", pid, "unknown classification"))
        if not str(pid).startswith(f"{p.get('domain', '').split('-')[0]}"):
            out.append(Finding("error", pid, "id must be prefixed with its domain"))

        for port in p.get("output_ports", []) or []:
            contract = port.get("contract")
            if contract:
                path = (p["_file"].parent / contract).resolve()
                if not path.exists():
                    out.append(Finding("error", pid, f"contract file not found: {contract}"))
            elif p.get("status") == "published":
                out.append(Finding("warning", pid, f"published port '{port.get('name')}' has no data contract"))

        for dep in upstream(p):
            if dep not in products:
                out.append(Finding("error", pid, f"depends on unknown product '{dep}'"))
                continue
            d = products[dep]
            if d["status"] in ("deprecated", "retired"):
                out.append(Finding("warning", pid, f"depends on {d['status']} product '{dep}'"))
            if p.get("status") == "published" and d["status"] not in ("published", "deprecated"):
                out.append(Finding("error", pid, f"published product depends on non-published '{dep}'"))
            if CLASS_RANK.get(p.get("classification"), 0) < CLASS_RANK.get(d.get("classification"), 0):
                out.append(Finding("warning", pid, f"classified lower than its input '{dep}' "
                                                    f"({p.get('classification')} < {d.get('classification')}); "
                                                    "confirm sensitive fields are removed"))

    # Cycles make ownership and change impact impossible to reason about.
    state: dict[str, int] = {}

    def visit(n: str, stack: list[str]) -> None:
        state[n] = 1
        for m in upstream(products[n]):
            if m not in products:
                continue
            if state.get(m) == 1:
                out.append(Finding("error", n, "dependency cycle: " + " -> ".join(stack + [m])))
            elif state.get(m) is None:
                visit(m, stack + [m])
        state[n] = 2

    for pid in products:
        if pid not in state:
            visit(pid, [pid])
    return out


def downstream(products: dict[str, dict[str, Any]], pid: str) -> list[str]:
    """All products transitively affected by a change to pid (breadth-first)."""
    affected, frontier = [], [pid]
    while frontier:
        cur = frontier.pop(0)
        for other_id, other in products.items():
            if cur in upstream(other) and other_id not in affected:
                affected.append(other_id)
                frontier.append(other_id)
    return affected


def to_mermaid(products: dict[str, dict[str, Any]]) -> str:
    lines = ["flowchart LR"]
    domains: dict[str, list[str]] = {}
    for pid, p in products.items():
        domains.setdefault(p["domain"], []).append(pid)
    for dom, ids in domains.items():
        lines.append(f'  subgraph {dom.replace("-", "_")}["{dom} domain"]')
        for pid in ids:
            p = products[pid]
            node = pid.replace(".", "_").replace("-", "_")
            style = "" if p["status"] == "published" else " (" + p["status"] + ")"
            lines.append(f'    {node}["{p["name"]}{style}"]')
        lines.append("  end")
    for pid, p in products.items():
        for dep in upstream(p):
            lines.append(f'  {dep.replace(".", "_").replace("-", "_")} --> {pid.replace(".", "_").replace("-", "_")}')
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Data product registry")
    ap.add_argument("command", choices=["validate", "list", "impact", "mermaid"])
    ap.add_argument("product", nargs="?")
    a = ap.parse_args(argv)
    products = load_products()

    if a.command == "validate":
        findings = validate(products)
        for f in findings:
            print(f)
        errors = sum(f.level == "error" for f in findings)
        print(f"{len(products)} products, {errors} errors, {len(findings) - errors} warnings")
        return 1 if errors else 0
    if a.command == "list":
        print(f"{'ID':<34} {'DOMAIN':<20} {'TYPE':<17} {'STATUS':<10} OWNER")
        for pid, p in sorted(products.items()):
            print(f"{pid:<34} {p['domain']:<20} {p['type']:<17} {p['status']:<10} {p['owner']}")
        return 0
    if a.command == "impact":
        if a.product not in products:
            print(f"unknown product {a.product}", file=sys.stderr)
            return 2
        affected = downstream(products, a.product)
        print(f"Changing {a.product} affects {len(affected)} product(s):")
        for pid in affected:
            print(f"  - {pid}  (owner: {products[pid]['owner']}, status: {products[pid]['status']})")
        return 0
    if a.command == "mermaid":
        print(to_mermaid(products))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
