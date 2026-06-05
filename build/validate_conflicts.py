#!/usr/bin/env python3
"""Validate the CONFLICTS split. EXIT 1 on any error. Run: python3 build/validate_conflicts.py"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SUMMARY = ROOT / "patterns" / "CONFLICTS.md"
SUBDIR = ROOT / "patterns" / "conflicts"
errors = []

summary = SUMMARY.read_text(encoding="utf-8")
# 1. all canonical anchors present in the summary (so linkify links resolve)
for n in range(1, 9):
    if f"{{#critical-{n}}}" not in summary:
        errors.append(f"missing anchor #critical-{n} in CONFLICTS.md")
for x in "abcdefghij":
    if f"{{#connection-{x}}}" not in summary:
        errors.append(f"missing anchor #connection-{x} in CONFLICTS.md")
# 2. all 7 subfiles exist and are non-empty
for name in ["SIGNAL", "KNOWLEDGE", "REASONING", "ORCHESTRATION", "RELIABILITY", "INTEGRATION", "HUMANIZERS"]:
    f = SUBDIR / f"{name}.md"
    if not f.exists() or len(f.read_text(encoding="utf-8").strip()) < 50:
        errors.append(f"subfile missing/empty: {name}.md")
# 3. each critical/connection appears exactly once across the subfiles (full prose)
allsub = "\n".join(f.read_text(encoding="utf-8") for f in SUBDIR.glob("*.md"))
for n in range(1, 9):
    c = len(re.findall(rf'^## Critical {n} —', allsub, re.M))
    if c != 1:
        errors.append(f"Critical {n} appears {c}× in subfiles (want 1)")
for x in "ABCDEFGHIJ":
    c = len(re.findall(rf'^## Connection {x} —', allsub, re.M))
    if c != 1:
        errors.append(f"Connection {x} appears {c}× in subfiles (want 1)")
# 4. index block present
if "<!-- BEGIN INDEX -->" not in summary or "<!-- END INDEX -->" not in summary:
    errors.append("CONFLICTS.md index markers missing")

if errors:
    print(f"ERROR: {len(errors)} conflict integrity error(s):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
print(f"OK — conflicts split validated ({SUMMARY.stat().st_size} B summary, 7 subfiles).")
