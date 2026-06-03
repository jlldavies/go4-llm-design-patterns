#!/usr/bin/env python3
"""Plain-assert tests for linkify.py. Run: python3 site/test_linkify.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from linkify import linkify_mechanisms, linkify_conflicts

mech = lambda t: linkify_mechanisms(t, lambda n: f'[{n}](#m{n})')
conf = lambda t: linkify_conflicts(
    t,
    lambda n: f'[Appendix A, Critical {n}](#critical-{n})',
    lambda: '[Appendix A](#appendix-conflicts)',
)

def eq(got, want):
    assert got == want, f"\n  got:  {got!r}\n  want: {want!r}"

# --- mechanisms ---
eq(mech("see mechanism 2 here"), "see mechanism [2](#m2) here")
eq(mech("(mechanism 2)"), "(mechanism [2](#m2))")
eq(mech("mechanisms 2 and 3"), "mechanisms [2](#m2) and [3](#m3)")
eq(mech("mechanism 2, 6 apply"), "mechanism [2](#m2), [6](#m6) apply")
eq(mech("mechanism 7 — strong"), "mechanism [7](#m7) — strong")
eq(mech("mechanism 10 and 12"), "mechanism [10](#m10) and [12](#m12)")
eq(mech("Mechanism 4 leads"), "Mechanism [4](#m4) leads")
eq(mech("`mechanism 2`"), "`mechanism 2`")
eq(mech("## mechanism 2 heading"), "## mechanism 2 heading")
eq(mech("[mechanism 2](x)"), "[mechanism 2](x)")
eq(mech("```\nmechanism 2\n```"), "```\nmechanism 2\n```")
eq(mech("the mechanistic basis"), "the mechanistic basis")

# --- conflicts ---
eq(conf("see CONFLICTS.md CRITICAL 3"), "see [Appendix A, Critical 3](#critical-3)")
eq(conf("in CONFLICTS.md, CRITICAL 3"), "in [Appendix A, Critical 3](#critical-3)")
eq(conf("in CONFLICTS.md."), "in [Appendix A](#appendix-conflicts).")
eq(conf("CONFLICTS.md CRITICAL 7 says"), "[Appendix A, Critical 7](#critical-7) says")
eq(conf("read CLAUDE.md and AGENTS.md"), "read CLAUDE.md and AGENTS.md")
eq(conf("`see CONFLICTS.md`"), "`see CONFLICTS.md`")
eq(conf("[x](../patterns/CONFLICTS.md#critical-3)"),
   "[x](../patterns/CONFLICTS.md#critical-3)")

print("ALL LINKIFY TESTS PASSED")
