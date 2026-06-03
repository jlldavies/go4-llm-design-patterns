#!/usr/bin/env python3
"""
Validate build/src/SUMMARY.md against the real source files:
  EXIT 1 if any referenced file is missing.
  Print WARNING if any patterns/*.md is not listed in SUMMARY.md (orphan).

SUMMARY refs use the in-book layout (patterns/…, pdf-source/…). The real sources
live at <repo>/patterns/ and build/content/ respectively.
"""

import re
import sys
from pathlib import Path

BUILD = Path(__file__).parent
ROOT = BUILD.parent
SUMMARY = BUILD / "src" / "SUMMARY.md"
CONTENT = BUILD / "content"

refs = re.findall(r'\]\(([^)]+\.md)\)', SUMMARY.read_text())


def source_of(ref: str) -> Path:
    if ref.startswith("patterns/"):
        return ROOT / ref
    if ref.startswith("pdf-source/"):
        return CONTENT / ref[len("pdf-source/"):]
    return BUILD / "src" / ref  # prefix chapters living directly in src/


errors = [r for r in refs if not source_of(r).exists()]
if errors:
    print(f"ERROR: {len(errors)} file(s) referenced in SUMMARY.md not found:")
    for e in errors:
        print(f"  MISSING: {e}  (looked for {source_of(e)})")
    sys.exit(1)

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
