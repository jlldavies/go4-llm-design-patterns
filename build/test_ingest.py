#!/usr/bin/env python3
"""Plain-assert tests for ingest_lib.py. Run: python3 build/test_ingest.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ingest_lib import (unit_id, category_of, title_of, also_known_as, intent_of,
                        mechanism_refs, related_edges, _edge_type, conflict_edges,
                        when_to_use_map, parse_mechanisms,
                        emit_frontmatter, relationship_sentence, wikilink_line,
                        assemble_pattern_unit, strip_first_h1, cost_map)


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

c0 = (
    "### M1 — Attention as a Learned Bilinear Form  {#m1}\n\n#### Grade A\n*text*\n"
    "### M2 — n² Compute and KV Cache Memory Cost  {#m2}\n\n#### Grade A\n*text*\n"
    "### M4 — Lost-in-the-Middle as Q-K Space Geometry  {#m4}\n\n#### Grade B — empirically strong\n*text*\n"
)
ms = parse_mechanisms(c0)
eq(len(ms), 3)
eq(ms[0]["num"], 1)
eq(ms[1]["grade"], "A")
eq(ms[2]["grade"], "B")
eq(ms[0]["slug"], "M1-attention-as-a-learned-bilinear-form")

rows = (
    "| [S1 Zero-Shot](patterns/S1-Zero-Shot.md) | Direct Instruction | Simple, well-defined tasks within model priors |\n"
    "| [R4 ReAct](patterns/R4-ReAct.md) | Reason+Act, Agent Loop | Adaptive tool use; each action informs the next |\n"
)
w = when_to_use_map(rows)
eq(w["S1"], "Simple, well-defined tasks within model priors")
eq(w["R4"], "Adaptive tool use; each action informs the next")

cm = (
    "### Critical 1 — R4 $\\oplus$ R5  {#critical-1}\n"
    "### Critical 2 — V1 $\\leftrightarrow$ V2  {#critical-2}\n"
    "### Critical 3 — S9 H/S V7  {#critical-3}\n"
)
eq(conflict_edges(cm), [("R4", "R5", "conflicts_with"),
                        ("V1", "V2", "conflicts_with"),
                        ("S9", "V7", "composes_with")])

eq(_edge_type("Sibling of"), "siblings")
eq(_edge_type("Required by"), "related")   # Fix 2: demoted from "requires" to "related"
eq(_edge_type("Requires"), "requires")      # Fix 2: "requires" stays as-is
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
eq(e["related"], ["V9"])   # Fix 2: "Required by" now maps to "related"
eq(e["composes_with"], ["K8"])

# Fix 1 + 3: non-bold prose IDs excluded; Note bullet skipped even if it bolds an ID
rp2 = (
    "## Related Patterns\n"
    "- **Sibling of** **R5 ReWOO** — mutually exclusive; unbounded use is anti-pattern A3.\n"
    "- **Note on fundamentality** — **R13 CodeAct** is also a loop but distinct.\n"
    "## Sources\n"
)
eq(related_edges(rp2, "R4"), {"siblings": ["R5"]})

# Fix 2
eq(_edge_type("Required by"), "related")
eq(_edge_type("Requires"), "requires")

R4_HEAD = "# R4 — ReAct\n"
eq(title_of(R4_HEAD), "ReAct")
eq(also_known_as("**Also Known As:** Reason+Act, Think-Act-Observe, the Agent Loop. (Function-calling agents...)"),
   ["Reason+Act", "Think-Act-Observe", "the Agent Loop"])
eq(also_known_as("**Also Known As:** Curated Memory, Self-Edited Memory (Letta's term), Agent-Authored Wiki, Structured Notes Memory"),
   ["Curated Memory", "Self-Edited Memory", "Agent-Authored Wiki", "Structured Notes Memory"])
eq(intent_of("## Intent\n\nLet an agent make its next decision after seeing the result.\n\n## Motivation"),
   "Let an agent make its next decision after seeing the result.")

eq(emit_frontmatter({"id": "R4", "cost": "medium-high", "requires": ["V9", "V14"], "derived": True}),
   "---\nid: R4\ncost: medium-high\nrequires: [V9, V14]\nderived: true\n---")

# Fix 4: quote-containing alias produces valid escaped YAML; plain alias stays unquoted
eq(emit_frontmatter({"also_known_as": ['Human Block', 'the "npm" of AI tools']}),
   '---\nalso_known_as: [Human Block, "the \\"npm\\" of AI tools"]\n---')
eq(relationship_sentence({"requires": ["V9", "V14"], "siblings": ["R5"]}),
   "Requires V9, V14. Sibling of R5.")
eq(wikilink_line({"requires": ["V9"], "siblings": ["R5"]}, {"V9": "V9-Bounded-Execution", "R5": "R5-ReWOO"}),
   "Related: [[V9-Bounded-Execution]] · [[R5-ReWOO]]")

unit = assemble_pattern_unit(
    {"id": "R4", "title": "ReAct", "canonical": "patterns/R4-ReAct.md", "derived": True},
    "ReAct interleaves Thought, Action, Observation.",
    {"requires": ["V9"], "siblings": ["R5"]},
    ["Use when the next call depends on the last result"],
    {"V9": "V9-Bounded-Execution", "R5": "R5-ReWOO"},
)
assert "## Description" in unit and "[[V9-Bounded-Execution]]" in unit, unit
assert "patterns/R4-ReAct.md" in unit, unit
# Fix 6: strengthen assemble_pattern_unit test
assert "## Key points" in unit, unit
assert "Sibling of R5" in unit, unit
assert "[[R5-ReWOO]]" in unit, unit

# Fix 5
eq(category_of("A3"), "Unknown")

eq(strip_first_h1("# Title\n\nBody line"), "Body line")

# Both bullet formats: Format A (targets bold before em-dash) and Format B (targets plain after em-dash)
rp_real = (
    "## Related Patterns\n"
    "- **Sibling of** **R5 ReWOO** — opposite trade-off.\n"
    "- **Sibling of** **R13 CodeAct** — R13 requires **V8 Tool Sandboxing**.\n"
    "- **Required by** **V9 Bounded Execution** — unbounded R4 is anti-pattern **A3**.\n"
    "- **Pairs with** **V14 Trajectory Logging** — undebuggable (**A15**).\n"
    "- **Tool layer** — **I2 Function/Tool Call** for 1-5 tools, **I3 MCP Server** for 5+.\n"
    "## Sources\n"
)
e = related_edges(rp_real, "R4")
eq(e.get("siblings"), ["R5", "R13"])             # V8 excluded (Format A target found pre-dash; post ignored)
eq(e.get("related"), ["V9"])                     # 'Required by' demoted; A3 excluded
eq(e.get("composes_with"), ["V14", "I2", "I3"])  # V14 (Format A) + Tool-layer I2,I3 (Format B); A15 excluded

# Format B test: targets in plain text after em-dash only
rp_b = (
    "## Related Patterns\n"
    "- **Composes with** — K2, K3 apply here.\n"
    "- **Distinct from** — A1 is an anti-pattern; K9 is the alternative.\n"
    "## Sources\n"
)
eb = related_edges(rp_b, "K1")
eq(eb.get("composes_with"), ["K2", "K3"])
eq(eb.get("related"), ["K9"])                    # A1 (anti-pattern) excluded

# Format C test: plain-text target before em-dash (K7 real-world format)
rp_c = (
    "## Related Patterns\n"
    "- **Lossless counterpart of** K6 Context Compression — prune first, compress the rest.\n"
    "- **Composes with** K8 Working Memory — scratchpad pruning.\n"
    "- Implements Anthropic's Select strategy.\n"
    "## Sources\n"
)
ec = related_edges(rp_c, "K7")
eq(ec.get("related"), ["K6"])           # 'Lossless counterpart of' -> default 'related'; plain-text target captured
eq(ec.get("composes_with"), ["K8"])
# third bullet has no bold label -> skipped entirely

# --- cost_map ---
# Spec sample: REASONING-DECISION rows (including the LaTeX 5× cell that must be skipped)
dt = ("| Pattern | LLM Calls | Relative Cost | Notes |\n"
      "|---|---|---|---|\n"
      "| R1 Zero-Shot CoT | 1 | Baseline | x |\n"
      "| R4 ReAct | N per step | Medium–High | x |\n"
      "| R5 ReWOO | 2 total | **5$\\times$ cheaper than R4** | x |\n"
      "| R9 ToT | N | Very High | x |\n")
cm = cost_map([dt])
eq(cm.get("R1"), "baseline")
eq(cm.get("R4"), "medium-high")
eq(cm.get("R9"), "very-high")
eq(cm.get("R5"), None)   # '5× cheaper' has no clean leading enum -> skipped

# Remaining enum values
dt2 = ("| Pattern | LLM Calls | Relative Cost | Notes |\n"
       "|---|---|---|---|\n"
       "| R2 Few-Shot CoT | 1 | Low + example tokens | y |\n"
       "| R3 Plan-and-Solve | 2 | Low | y |\n"
       "| R7 Reflexion | N | High | y |\n"
       "| R10 LATS | N | Highest | y |\n"
       "| R8 Self-Refine | N | Medium | y |\n")
cm2 = cost_map([dt2])
eq(cm2.get("R2"), "low")    # leading word "Low" despite trailing text
eq(cm2.get("R3"), "low")
eq(cm2.get("R7"), "high")
eq(cm2.get("R10"), "highest")
eq(cm2.get("R8"), "medium")

# First-wins: second guide does not override
dt_first = "| Pattern | Relative Cost |\n|---|---|\n| O1 Single Agent | Baseline |\n"
dt_second = "| Pattern | Relative Cost |\n|---|---|\n| O1 Single Agent | High |\n"
eq(cost_map([dt_first, dt_second]).get("O1"), "baseline")
eq(cost_map([dt_second, dt_first]).get("O1"), "high")

# Table with no cost column is skipped entirely
dt_no_cost = "| Pattern | Cacheable? | Notes |\n|---|---|---|\n| S1 Zero-Shot | Yes | x |\n"
eq(cost_map([dt_no_cost]).get("S1"), None)

# Orchestration rows (medium-high via en-dash variant)
dt_orch = ("| Pattern | Relative cost | When justified |\n"
           "|---|---|---|\n"
           "| O1 Single Agent | Baseline | Default |\n"
           "| O2 Prompt Chaining | Low | Fixed decomp |\n"
           "| O6 Orchestrator-Workers | High | Dynamic decomp |\n"
           "| O7 Supervisor Hierarchy | Very high | Recursive |\n")
cmo = cost_map([dt_orch])
eq(cmo.get("O1"), "baseline")
eq(cmo.get("O2"), "low")
eq(cmo.get("O6"), "high")
eq(cmo.get("O7"), "very-high")

print("ALL INGEST TESTS PASSED")
