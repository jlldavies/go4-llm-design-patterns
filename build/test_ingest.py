#!/usr/bin/env python3
"""Plain-assert tests for ingest_lib.py. Run: python3 build/test_ingest.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ingest_lib import unit_id, category_of, title_of, also_known_as, intent_of, mechanism_refs, related_edges, _edge_type


def eq(got, want):
    assert got == want, f"\n  got:  {got!r}\n  want: {want!r}"


# --- ids ---
eq(unit_id("R4-ReAct"), "R4")
eq(unit_id("K13-Retrieval-Bundle"), "K13")
eq(category_of("R4"), "Reasoning")
eq(category_of("H10"), "Humanizers")

eq(mechanism_refs("conditions on mechanism 4; see mechanisms 2 and 3, plus (mechanism 12)."), [2, 3, 4, 12])
eq(mechanism_refs("no citations here"), [])
eq(mechanism_refs("mechanism 99 is out of range"), [])

eq(_edge_type("Sibling of"), "siblings")
eq(_edge_type("Required by"), "requires")
eq(_edge_type("Pairs with"), "composes_with")
eq(_edge_type("Distinct from"), "related")
eq(_edge_type("Totally novel label"), "related")

rp = (
    "## Related Patterns\n"
    "- **Sibling of** **R5 ReWOO** — same problem, opposite trade-off.\n"
    "- **Required by** **V9 Bounded Execution** — never run R4 unbounded.\n"
    "- **Composes with** **K8 Working Memory** — the trajectory is the scratchpad.\n"
    "## Sources\n"
)
e = related_edges(rp, "R4")
eq(e["siblings"], ["R5"])
eq(e["requires"], ["V9"])
eq(e["composes_with"], ["K8"])

R4_HEAD = "# R4 — ReAct\n"
eq(title_of(R4_HEAD), "ReAct")
eq(also_known_as("**Also Known As:** Reason+Act, Think-Act-Observe, the Agent Loop. (Function-calling agents...)"),
   ["Reason+Act", "Think-Act-Observe", "the Agent Loop"])
eq(intent_of("## Intent\n\nLet an agent make its next decision after seeing the result.\n\n## Motivation"),
   "Let an agent make its next decision after seeing the result.")

print("ALL INGEST TESTS PASSED")
