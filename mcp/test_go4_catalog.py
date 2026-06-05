#!/usr/bin/env python3
"""Plain-assert tests for go4_catalog. Run: python3 mcp/test_go4_catalog.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from go4_catalog import parse_frontmatter, load_index


def eq(got, want):
    assert got == want, f"\n  got:  {got!r}\n  want: {want!r}"


eq(parse_frontmatter('---\nid: R4\ntitle: ReAct\nrequires: [V9, V14]\n---\nbody'),
   {"id": "R4", "title": "ReAct", "requires": ["V9", "V14"]})

idx = load_index()
assert len(idx) == 94, f"expected 94 pattern digests, got {len(idx)}"
eq(idx["R4"]["title"], "ReAct")
eq(idx["R4"]["category"], "Reasoning")
assert "R5" in idx["R4"].get("conflicts_with", []), idx["R4"]

print("ALL CATALOG TESTS PASSED")
