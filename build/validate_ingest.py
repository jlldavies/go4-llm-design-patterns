#!/usr/bin/env python3
"""Validate the generated ingest/ artifact. EXIT 1 on any error.
Run: python3 build/validate_ingest.py"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "ingest"
errors, warnings = [], []

manifest = json.loads((OUT / "ingest.json").read_text(encoding="utf-8"))
ids = {u["id"] for u in manifest["units"]}

# 1. every unit file referenced in the manifest exists
for u in manifest["units"]:
    if not (ROOT / u["file"]).exists():
        errors.append(f"missing unit file: {u['file']}")

# 2. every edge target exists as a unit (patterns) — mechanism refs checked separately
for e in manifest["edges"]:
    if e["to"] not in ids:
        warnings.append(f"edge target not a pattern unit: {e['from']} -> {e['to']} ({e['type']})")

# 3. conflict edges are symmetric
conf = {(e["from"], e["to"]) for e in manifest["edges"] if e["type"] == "conflicts_with"}
for a, b in conf:
    if (b, a) not in conf:
        warnings.append(f"asymmetric conflict: {a} conflicts_with {b} but not reverse")

# 4. canonical paths resolve
for u in manifest["units"]:
    can = u["canonical"].split("#")[0]
    if not (ROOT / can).exists():
        errors.append(f"canonical missing: {u['canonical']}")

# 5. mechanism_refs in range
for u in manifest["units"]:
    for n in u["edges"].get("mechanism_refs", []) if "edges" in u else []:
        if not (1 <= n <= 12):
            errors.append(f"{u['id']}: mechanism_ref out of range: {n}")

# 6. files-vs-manifest 1:1 for pattern units
unit_files = {u["file"].split("/")[-1] for u in manifest["units"]}
disk_pattern_files = {f.name for f in OUT.glob("*.md")
                      if re.match(r'^[A-Z]+\d+-', f.name)}
for extra in disk_pattern_files - unit_files:
    warnings.append(f"pattern file on disk not in manifest: {extra}")

for w in warnings:
    print(f"WARNING: {w}")
if errors:
    print(f"ERROR: {len(errors)} integrity error(s):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
print(f"OK — {len(manifest['units'])} units validated, {len(manifest['edges'])} edges.")
