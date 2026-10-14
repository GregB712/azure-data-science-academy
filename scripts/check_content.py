#!/usr/bin/env python3
"""Content checks for the academy dossier (no third-party packages required).

Checks:
  - frontmatter of lessons/labs/projects/roadmaps/diagrams has the required fields
  - document ids are unique
  - relative links point to existing files, and #anchors match a heading (GitHub slug rules)
  - prerequisites / related / lessons ids exist
  - curriculum.json recommendedPath ids exist; module labs exist or are clearly planned
  - each lab has a "## Completion checklist" task list

Run from the academy root:  python3 scripts/check_content.py
Exit code 0 = no errors (warnings are printed but do not fail).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD_DIRS = ["docs", "labs", "projects", "diagrams", "references"]
SKIP_PARTS = {"node_modules", "dist", ".venv", "__pycache__", "_templates"}
REQUIRED = {
    "lesson": ["id", "title", "type", "module", "status", "summary"],
    "lab": ["id", "title", "type", "module", "status", "duration", "cost"],
    "module-overview": ["id", "title", "type", "module", "status"],
    "project": ["id", "title", "type", "status"],
    "architecture": ["id", "title", "type", "status", "services"],
    "reference": ["id", "title", "type"],
}

errors: list[str] = []
warnings: list[str] = []


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not m:
        return {}, text
    raw, body = m.group(1), text[m.end():]
    try:
        import yaml  # optional; used when installed

        return (yaml.safe_load(raw) or {}), body
    except ImportError:
        pass
    data: dict = {}
    key = None
    for line in raw.splitlines():
        if re.match(r"^\s*-\s+", line) and key:
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(line.split("-", 1)[1].strip().strip("'\""))
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                data[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            elif val == "":
                data[key] = []
            else:
                data[key] = val.strip("'\"")
    return data, body


def strip_inline_md(text: str) -> str:
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("`", "").replace("**", "").replace("__", "").replace("*", "").replace("~~", "")


def slugify(text: str) -> str:
    text = strip_inline_md(text).strip().lower()
    text = "".join(ch for ch in text if ch in " _-" or unicodedata.category(ch)[0] in "LN" or ch.isspace())
    return re.sub(r"\s", "-", text)


def headings(body: str) -> set[str]:
    seen: dict[str, int] = {}
    out = set()
    fence = False
    for line in body.splitlines():
        if re.match(r"^\s*```", line):
            fence = not fence
        if fence:
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if not m:
            continue
        base = slugify(m.group(2))
        if base in seen:
            seen[base] += 1
            out.add(f"{base}-{seen[base]}")
        else:
            seen[base] = 0
            out.add(base)
    return out


def links(body: str):
    fence = False
    for n, line in enumerate(body.splitlines(), 1):
        if re.match(r"^\s*```", line):
            fence = not fence
        if fence:
            continue
        line = re.sub(r"`[^`]*`", "", line)
        for m in re.finditer(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", line):
            yield n, m.group(1)


def main() -> int:
    files = sorted(p for p in ROOT.glob("*.md"))
    for d in MD_DIRS:
        files += sorted(p for p in (ROOT / d).rglob("*.md") if not SKIP_PARTS & set(p.parts))
    docs: dict[Path, tuple[dict, str]] = {}
    for p in files:
        docs[p] = parse_frontmatter(p.read_text(encoding="utf-8"))

    ids: dict[str, Path] = {}
    for p, (fm, _) in docs.items():
        rel = p.relative_to(ROOT).as_posix()
        doc_id = fm.get("id") or rel[:-3]
        if doc_id in ids:
            errors.append(f"duplicate id '{doc_id}': {rel} and {ids[doc_id].relative_to(ROOT).as_posix()}")
        ids[doc_id] = p
        t = fm.get("type")
        for field in REQUIRED.get(t, []):
            if fm.get(field) in (None, "", []):
                errors.append(f"{rel}: frontmatter missing '{field}' (type {t})")
        if fm and t not in REQUIRED:
            warnings.append(f"{rel}: unknown or missing type '{t}'")

    anchors = {p: headings(body) for p, (_, body) in docs.items()}
    for p, (fm, body) in docs.items():
        rel = p.relative_to(ROOT).as_posix()
        for key in ("prerequisites", "related", "lessons"):
            for ref in fm.get(key) or []:
                if ref not in ids:
                    errors.append(f"{rel}: {key} id '{ref}' does not exist")
        for line_no, href in links(body):
            if re.match(r"^[a-z][a-z0-9+.-]*:", href, re.I) or href.startswith("#/"):
                continue
            path_part, _, anchor = href.partition("#")
            target = (p.parent / path_part).resolve() if path_part else p
            if not target.exists():
                errors.append(f"{rel}:{line_no}: broken link '{href}'")
                continue
            if anchor and target.suffix == ".md" and target in anchors and anchor not in anchors[target]:
                errors.append(f"{rel}:{line_no}: anchor '#{anchor}' not found in {target.relative_to(ROOT).as_posix()}")
        if fm.get("type") == "lab":
            m = re.search(r"^## Completion checklist\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
            n = len(re.findall(r"^\s*[-*] \[[ xX]\] ", m.group(1), re.M)) if m else 0
            if n == 0:
                errors.append(f"{rel}: lab has no '## Completion checklist' task list")

    cur = json.loads((ROOT / "curriculum.json").read_text(encoding="utf-8"))
    for ref in cur.get("recommendedPath", []):
        if ref not in ids:
            errors.append(f"curriculum.json: recommendedPath id '{ref}' does not exist")
    for mod in cur["modules"]:
        for lab in mod.get("labs", []):
            if lab not in ids and mod.get("status") == "available":
                errors.append(f"curriculum.json: module {mod['id']} is available but lab '{lab}' does not exist")
            elif lab not in ids:
                warnings.append(f"curriculum.json: lab '{lab}' (module {mod['number']}) is planned, not written yet")
        if not (ROOT / mod["docsPath"]).exists():
            errors.append(f"curriculum.json: docsPath '{mod['docsPath']}' does not exist")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\nChecked {len(docs)} Markdown files: {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
