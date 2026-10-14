"""Detect breaking changes between two versions of a data contract.

A data product's output contract is a promise to consumers. This check runs in
the producing domain's CI: if a change is breaking for consumers, the contract's
MAJOR version must be bumped (and in practice the old version kept alive for a
deprecation window). Non-breaking additions need at least a MINOR bump.

Rules (consumer's point of view):
  breaking      column removed or renamed
  breaking      logicalType changed
  breaking      column changed from required to optional (consumers may now see nulls)
  breaking      primary key changed
  breaking      a quality rule on an existing column was removed (weaker guarantee)
  breaking      SLA weakened (latency/frequency value increased)
  non-breaking  optional column added
  non-breaking  column changed from optional to required (stronger guarantee)
  non-breaking  quality rule added
  breaking      required column added *is not* breaking for readers, but it is for
                anyone who writes to the table; we treat it as non-breaking here.

Run (WSL, from code/):
    python data_mesh/contract_compat.py contracts/sales.pos_sales.v1.yaml \
        contracts/proposals/sales.pos_sales.v1.1-proposal.yaml
Exit code 1 means the proposed version number does not reflect the change.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Change:
    kind: str  # "breaking" | "non-breaking"
    message: str


def _load(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _props(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p["name"]: p for p in contract["schema"][0]["properties"]}


def _rules(prop: dict[str, Any]) -> set[str]:
    return {json.dumps(q, sort_keys=True) for q in prop.get("quality", []) or []}


def _sla(contract: dict[str, Any]) -> dict[str, tuple[float, str]]:
    return {s["property"]: (float(s["value"]), s.get("unit", "")) for s in contract.get("slaProperties", []) or []}


def diff(old: dict[str, Any], new: dict[str, Any]) -> list[Change]:
    changes: list[Change] = []
    po, pn = _props(old), _props(new)
    for name, p in po.items():
        if name not in pn:
            changes.append(Change("breaking", f"column '{name}' removed or renamed"))
            continue
        q = pn[name]
        if p.get("logicalType") != q.get("logicalType"):
            changes.append(Change("breaking", f"column '{name}' type {p.get('logicalType')} -> {q.get('logicalType')}"))
        if p.get("required") and not q.get("required"):
            changes.append(Change("breaking", f"column '{name}' is no longer required"))
        if not p.get("required") and q.get("required"):
            changes.append(Change("non-breaking", f"column '{name}' is now required"))
        if bool(p.get("primaryKey")) != bool(q.get("primaryKey")):
            changes.append(Change("breaking", f"primary key membership of '{name}' changed"))
        removed = _rules(p) - _rules(q)
        added = _rules(q) - _rules(p)
        if removed:
            changes.append(Change("breaking", f"quality rule(s) removed/changed on '{name}': {sorted(removed)}"))
        if added:
            changes.append(Change("non-breaking", f"quality rule(s) added on '{name}'"))
    for name in pn.keys() - po.keys():
        changes.append(Change("non-breaking", f"column '{name}' added"
                              + (" (required: breaking for writers)" if pn[name].get("required") else "")))
    so, sn = _sla(old), _sla(new)
    for prop, (val, unit) in so.items():
        if prop in sn and sn[prop][1] == unit and sn[prop][0] > val and prop in ("latency", "frequency"):
            changes.append(Change("breaking", f"SLA '{prop}' weakened {val}{unit} -> {sn[prop][0]}{unit}"))
    return changes


def required_bump(changes: list[Change]) -> str:
    if any(c.kind == "breaking" for c in changes):
        return "major"
    if changes:
        return "minor"
    return "none"


def actual_bump(old_version: str, new_version: str) -> str:
    o = [int(x) for x in old_version.split(".")]
    n = [int(x) for x in new_version.split(".")]
    if n[0] > o[0]:
        return "major"
    if n[0] == o[0] and n[1] > o[1]:
        return "minor"
    if n[:2] == o[:2] and n[2] > o[2]:
        return "patch"
    return "none"


def check(old_path: str | Path, new_path: str | Path) -> tuple[bool, list[Change], str, str]:
    old, new = _load(old_path), _load(new_path)
    changes = diff(old, new)
    need, got = required_bump(changes), actual_bump(old["version"], new["version"])
    order = {"none": 0, "patch": 1, "minor": 2, "major": 3}
    ok = order[got] >= order[need]
    return ok, changes, need, got


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Data contract compatibility check")
    ap.add_argument("old")
    ap.add_argument("new")
    a = ap.parse_args(argv)
    ok, changes, need, got = check(a.old, a.new)
    for c in changes:
        print(f"{c.kind.upper():13} {c.message}")
    print(f"required bump: {need}; proposed bump: {got} -> {'OK' if ok else 'REJECTED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
