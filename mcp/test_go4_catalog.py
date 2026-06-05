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

# ── Task 2: find ──────────────────────────────────────────────────────────────
from go4_catalog import find
r = find("multi-agent orchestrator workers", limit=5, index=idx)
ids = [c["id"] for c in r]
assert "O6" in ids, ids          # Orchestrator-Workers should surface
assert all(set(c) == {"id","title","category","when_to_use"} for c in r)
r2 = find("retrieval augmented generation vector", limit=3, index=idx)
assert any(c["id"].startswith("K") for c in r2), r2   # a Knowledge pattern
assert len(find("zzzznotarealterm", index=idx)) == 0

# ── Task 3: get_pattern ───────────────────────────────────────────────────────
from go4_catalog import get_pattern
p = get_pattern("R4", index=idx)
eq(p["id"], "R4"); eq(p["title"], "ReAct")
assert "R5" in p["edges"]["conflicts_with"], p["edges"]
assert p["canonical"] == "patterns/R4-ReAct.md", p["canonical"]
assert p["description"], p          # non-empty digest description
assert p["key_points"], p           # at least one key point
eq(get_pattern("ZZ9", index=idx), {"error": "unknown pattern 'ZZ9'"})

# ── Task 4: get_decision + conflict_notes ─────────────────────────────────────
from go4_catalog import get_decision, conflict_notes
d = get_decision("reasoning")
eq(d["category"], "Reasoning")
assert "ReAct" in d["decision_guide"] or "R4" in d["decision_guide"], d
assert "error" in get_decision("nope")
cn = conflict_notes("R4")
withs = [c["with"] for c in cn]
assert "R5" in withs, cn          # R4 conflicts with R5 (Critical 1 + registry)

print("ALL CATALOG TESTS PASSED")
