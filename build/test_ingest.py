#!/usr/bin/env python3
"""Plain-assert tests for ingest_lib.py. Run: python3 build/test_ingest.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ingest_lib import unit_id, category_of, title_of, also_known_as, intent_of


def eq(got, want):
    assert got == want, f"\n  got:  {got!r}\n  want: {want!r}"


# --- ids ---
eq(unit_id("R4-ReAct"), "R4")
eq(unit_id("K13-Retrieval-Bundle"), "K13")
eq(category_of("R4"), "Reasoning")
eq(category_of("H10"), "Humanizers")

R4_HEAD = "# R4 — ReAct\n"
eq(title_of(R4_HEAD), "ReAct")
eq(also_known_as("**Also Known As:** Reason+Act, Think-Act-Observe, the Agent Loop. (Function-calling agents...)"),
   ["Reason+Act", "Think-Act-Observe", "the Agent Loop"])
eq(intent_of("## Intent\n\nLet an agent make its next decision after seeing the result.\n\n## Motivation"),
   "Let an agent make its next decision after seeing the result.")

print("ALL INGEST TESTS PASSED")
