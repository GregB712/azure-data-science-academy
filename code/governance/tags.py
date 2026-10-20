"""Required-tag policy checker - the local analogue of an Azure Policy tag rule.

Azure Policy can *audit*, *deny* or *modify/append* resources that lack required
tags. This mirrors the audit/deny decision locally so you can validate tags in
CI before deployment (Module 7). A policy maps each required tag name to either
None (any value allowed) or a set of allowed values.

Run (WSL / Python), from code/:
    python -m governance.tags
"""

from __future__ import annotations

# The course's required-tag policy: every resource carries these.
DEFAULT_TAG_POLICY: dict[str, set[str] | None] = {
    "project": None,                               # any value
    "env": {"dev", "test", "prod", "lab"},         # constrained set
    "owner": None,
    "cost-center": None,
}


def check_tags(resource_tags: dict[str, str] | None,
               policy: dict[str, set[str] | None] = DEFAULT_TAG_POLICY) -> list[str]:
    """Return a list of policy violations ('' empty list means compliant)."""
    tags = resource_tags or {}
    violations: list[str] = []
    for name, allowed in policy.items():
        if name not in tags or tags[name] in (None, ""):
            violations.append(f"missing required tag '{name}'")
        elif allowed is not None and tags[name] not in allowed:
            violations.append(f"tag '{name}'='{tags[name]}' not in {sorted(allowed)}")
    return violations


def main() -> None:
    examples = [
        {"project": "adsa", "env": "prod", "owner": "greg", "cost-center": "ds"},
        {"project": "adsa", "env": "staging", "owner": "greg"},   # bad env, missing cost-center
    ]
    for tags in examples:
        v = check_tags(tags)
        print(tags, "->", "COMPLIANT" if not v else v)


if __name__ == "__main__":
    main()
