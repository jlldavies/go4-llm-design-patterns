#!/usr/bin/env python3
"""
Validate src/SUMMARY.md:
  EXIT 1 if any referenced file is missing from the repo.
  Print WARNING if any patterns/*.md is not listed (orphan).
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SUMMARY = ROOT / "src" / "SUMMARY.md"

refs = re.findall(r'\]\(([^)]+\.md)\)', SUMMARY.read_text())

errors = []
for ref in refs:
    # Check src/ first (after prepare.py), then the repo source location
    if not (ROOT / "src" / ref).exists() and not (ROOT / ref).exists():
        errors.append(ref)

if errors:
    print(f"ERROR: {len(errors)} file(s) referenced in SUMMARY.md not found:")
    for e in errors:
        print(f"  MISSING: {e}")
    sys.exit(1)

# Orphan check — patterns not listed in navigation
listed = set(refs)
orphans = sorted(
    f"patterns/{f.name}"
    for f in (ROOT / "patterns").glob("*.md")
    if f"patterns/{f.name}" not in listed
)
if orphans:
    print(f"WARNING: {len(orphans)} patterns not in SUMMARY.md (won't appear on site):")
    for o in orphans:
        print(f"  {o}")

print(f"OK — {len(refs)} references validated.")
