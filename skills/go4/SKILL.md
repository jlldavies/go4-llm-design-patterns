---
name: go4
description: "Use when designing, architecting, planning, or debugging any system with an LLM in it — agents, agent loops, RAG and retrieval, prompt pipelines, multi-agent or subagent orchestration, tool use and MCP, memory and context management, evals, or production guardrails. Trigger BEFORE committing to an approach — choosing how to structure an agent, picking a retrieval architecture, deciding whether to split work across agents, managing context windows or token cost, or adding reliability bounds. Also use when an existing LLM system misbehaves — loops, stalls, cost blowups, hallucination, context overflow, prompt injection. Not for general software design with no LLM involved."
---

# GO4 — LLM engineering design patterns

94 patterns across seven categories, grounded in transformer mechanics. Two jobs: pick the right
pattern, and get its **token economics** right — cost is **not a fixed tier**, it's a function of
how the system is used, and the choice compounds over every call. **Don't read the whole catalog**
— the value is the decision guides and the conflict graph.

## Resolve the catalog root

`GO4` = `$GO4_ROOT` if set → else `../../` from this skill file → else ask. Verify: `ls $GO4/patterns/CONFLICTS.md`.

## Before a big build — ask, then isolate

- **Ask before you plan.** Regime (Step 2) and pattern choice turn on facts usually in the user's
  head: scale / call frequency (once? thousands/day? millions?), cost of being wrong (reversible,
  or irreversible and expensive to redo?), latency / budget / model limits. If a substantial build
  hinges on numbers you'd otherwise guess, ask first — a plan for the wrong regime is worse than one
  question. Skip it for small or fully-specified tasks; don't interrogate.
- **Then isolate.** For a substantial or risky build, recommend the work happen in an isolated fork
  (git worktree/branch, not base) so it can be merged or cleanly reverted. The fork-and-revert
  mechanics are fiddly — use `superpowers:using-git-worktrees` rather than hand-rolling git — and
  flag the merge-or-revert decision up front so work isn't stranded.

## Step 1 — Classify (most designs touch two or three)

| Category | Governs | Reach for it when |
|---|---|---|
| Signal | Prompt shaping | Output format, personas, constraints, few-shot |
| Knowledge | Context engineering | RAG, retrieval, memory, compression, long context |
| Reasoning | Thinking structure | CoT, ReAct, tool loops, self-consistency, reflection |
| Orchestration | Multi-agent coordination | Pipelines, routing, parallelism, subagents, hierarchies |
| Reliability | Production safety | Bounds, logging, evals, human oversight, injection defence |
| Integration | Tool use | Function calling, MCP, CLI, agent-to-agent delegation |
| Humanizers | Cross-session continuity | Identity, persistent memory, self-improvement |

## Step 2 — Identify the cost regime (before naming any pattern)

The same pattern is cheap or ruinous by regime:

| Regime | Signature | Right move | Patterns |
|---|---|---|---|
| **Hot path** | runs thousands–millions of times | shrink & cache every call | K6/K7 · M5 prefix caching · O18 · M8 downshift |
| **Long-running** | one session grows unboundedly (n² prefill kills it) | bound context growth | K6 · K8 · V9 · V10 · M11 |
| **One-shot high-stakes** | runs rarely; correctness dwarfs cost | spend — fan out + verify | O4/O6 + O17 · O5 · V15 (ultracode, below) |

None of the three? Default regime: cheapest pattern that clears the bar. The two levers behind the
table (derivations: `$GO4/build/content/CHAPTER-0.md`): **M2** — doubling context ~4×s prefill cost
(long context is super-linear); **M5** — a byte-stable prefix reused within ~5 min costs ~10%, so
put stable content first, variable last.

## Step 3 — Decision guide as the cost oracle

`$GO4/patterns/<CATEGORY>-DECISION.md` — the decision flow **plus the cost table and composition
laws** (e.g. "O4 without O18 misses ~85% of the shared-prefix saving"). Read it before shortlisting.

## Step 4 — Shortlist digests, carry cost companions

`$GO4/ingest/<ID>-<Name>.md` — dense, with typed `composes_with` / `requires` edges. Carry the cost
companions (O18 for O4, O17 for O6) — several patterns lose their whole cost win without them.
Canonical `$GO4/patterns/<ID>.md` (8k+ tokens) only when implementing.

## Step 5 — Conflict check (mandatory; cheapest ladder first)

1. `conflicts_with` edges in the shortlisted digests — free, already loaded.
2. Cross-category pair → `$GO4/patterns/conflicts/<CATEGORY>.md` (~1k tokens).
3. Full `$GO4/patterns/CONFLICTS.md` (~2.5k) only for a pair the above missed.

Mutually-exclusive pairs and missing prerequisites are the expensive mistakes — never skip this.

## Step 6 — Recommend with the economics (required shape)

In order: pattern IDs + the **regime** chosen for; the **cost model** — per-call driver (context
length / cache) × lifetime multiplier (frequency / fan-out), not a tier; the cheaper alternative
rejected and the threshold that ruled it out; cost companions carried; conflicts checked and resolved.

## When to spend, not save — the ultracode case

For one-shot high-stakes work (a hard architecture call, security-sensitive review, irreversible
migration), token-minimising is wrong: fan out and verify. GO4's form is O4/O6 + O17 + O5/V15.
Claude Code's embodiment is **ultracode** (xhigh reasoning + auto subagent fan-out) and
**`/code-review ultra`** (parallel cloud reviewers, ~$5–20/run). Use it when being wrong costs more
than the tokens — not for routine work: *if you'd hand it to one engineer for an afternoon, don't
summon a swarm.*

## Don't

- Invent pattern IDs — if nothing fits, say so.
- Drop a prerequisite companion (the guides mark them REQUIRED).
- Optimise this reading over the design: the consultation is ~3k tokens once; the design runs for the system's whole life.
