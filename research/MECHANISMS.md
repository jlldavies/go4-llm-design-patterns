# Mechanisms & Evidence — Why the AI Design Patterns Work

*A first-principles companion to the GO4 catalogue. Status: research synthesis, 2026-06-01.*

---

## Why this document exists

The prompt-engineering / agent-design literature — including talks by senior Anthropic
engineers — is rich in **qualitative advice** ("clean the data room first", "prompt skills
not Claude", "save the script") but thin on **mechanistic rationale**. Because model
behaviour is emergent, the advice rarely traces back to the interpretation layers that
produce it, so it reads as folklore: *do this, get that*, with no theory of why.

This document does the back-translation. For each durable pattern it states the
**folk-claim**, the **mechanism** that produces it, the **evidence** (graded), and the
**GO4 pattern** it underwrites. It is deliberately honest about where the mechanism is
real and where the field is just reporting what empirically works (see *Where the "why"
runs out*).

**This is research, not yet an integration decision.** Whether this becomes a new field in
`PATTERN-BUILD-SPEC.md` or a standalone appendix is deferred — see [doc-system note](#relationship-to-the-rest-of-go4).

---

## Relationship to Chapter 0

Chapter 0 (*How the Machine Works*) contains the full tensor-level derivations for all twelve mechanisms: the bilinear form, RoPE as SO(d_head) Lie group action, the KV cache 4D structure, prefix caching economics, and the storage hierarchy. The entries below follow the folk-claim → mechanism → evidence → GO4 link format established in this document. For the mathematical derivation underlying any claim, see Chapter 0 §0.1–§0.4.

Mechanism citation syntax: patterns cite mechanisms as **(mechanism N)** where N is the section number in Chapter 0. This document provides the folk-claim framing; Chapter 0 provides the derivation.

---

### How to read the evidence grades

| Grade | Meaning |
|---|---|
| **A** | Mechanism is published (Anthropic engineering/docs or peer-reviewed) and directly supports the claim. |
| **B** | Empirically strong and Anthropic-endorsed, but the mechanistic pathway is only partly characterised. |
| **C** | Plausible mechanism, mostly inference; little direct evidence. |
| **⚠ emergent** | The pattern works empirically but *why* is not derived from first principles. Flagged, not hidden. |

Verification status of citations is recorded at the [end](#citation-verification-status).

---

## The mechanistic spine

### 1. "Prompt skills, not Claude" / progressive disclosure — **A**

**Folk-claim.** Don't write a fresh mega-prompt each time; package repeatable procedure
into a *skill* and let the model pull it in.

**Mechanism.** The context window is a **finite attention budget**, not free storage. A
skill is loaded in three levels of *progressive disclosure*: (1) a ~100-token metadata
description, always present, just enough for the model to decide *whether* the skill is
relevant; (2) the full `SKILL.md` instructions, loaded only when triggered; (3) bundled
resource files, read only when referenced. This separates **decision cost** (cheap, always
paid) from **execution cost** (paid only on use), so the knowledge bundled behind a skill
is "effectively unbounded" without taxing every unrelated turn.

**Evidence.** Anthropic, *Equipping agents for the real world with Agent Skills* — verbatim:
"This metadata is the **first level** of *progressive disclosure*… without loading all of
it into context"; the body is "the **second level**… loaded… into context" on relevance;
linked files are "the **third level** (and beyond)… only as needed"; and "the amount of
context that can be bundled into a skill is effectively unbounded." (Verified by fetch.)

**GO4 link.** INTEGRATION (I-series) tool/skill patterns; the discovery-vs-execution split
is itself a KNOWLEDGE-series context-budget pattern.

---

### 2. "Clean the data room first" / source inventory before drafting — **A**

**Folk-claim.** Before asking for the deliverable, make the agent build a source inventory,
conflict log, missing-context list, and duplicates report. Dumping the raw mess into one
prompt produces confident, blended, hallucination-prone output (the Sullivan & Cromwell
failure mode).

**Mechanism.** Three compounding effects of long, noisy context:

- **Finite attention budget.** "Like humans… LLMs have an 'attention budget' that they
  draw on when parsing large volumes of context." Every added token dilutes the share
  available to the tokens that matter.
- **n² dilution.** The transformer lets "every token… attend to every other token… This
  results in n² pairwise relationships for n tokens." As n grows, signal is spread thinner.
- **Lost-in-the-middle.** Recall is U-shaped: strong at the start and end of context, weak
  in the middle, with material accuracy loss for mid-context facts (Liu et al. 2024).

So dumping messy, contradictory sources forces **two jobs in one pass** — *work out what is
canonical* **and** *write* — and the model silently smooths conflicts to finish the job.
Externalising the inventory/conflict/missing-context artefacts first keeps each subsequent
task's context **small and high-signal**, which is the stated goal of context engineering:
"finding the smallest possible set of high-signal tokens that maximize the likelihood of
some desired outcome… context must be treated as a finite resource with diminishing
marginal returns."

**Evidence.** Anthropic, *Effective context engineering for AI agents* (all quotes above
verified by fetch); Liu et al. 2024, *Lost in the Middle* (arXiv:2307.03172); secondary:
*Context rot* (understandingai.org).

**GO4 link.** This *is* the KNOWLEDGE (K-series) context-engineering cluster. The
data-room workflow is the operating procedure those patterns imply.

---

### 3. "Save the script / use code, not the model" — **B+**

**Folk-claim.** When the model keeps re-deriving the same transformation, have it write the
code once, save it in the skill, and re-run it thereafter.

**Mechanism.** Executed code is **deterministic** — same input, same output — whereas token
generation is **stochastic sampling** from a probability distribution. Routing a repeatable
operation to a saved script trades sampling variance and token cost for cheap, repeatable
compute, and keeps intermediate results *out of the context window* (they live in the
execution environment; only the final result returns). One Anthropic example reports a
~98.7% token reduction (150k → 2k) by treating tool calls as code rather than in-context
exchanges.

**Why B+ not A.** The determinism argument is sound and Anthropic-endorsed, but the
*magnitude* of the reliability gain on real tasks is reported empirically (case studies),
not derived. The principle is solid; the numbers are situational.

**Evidence.** Anthropic, *Writing effective tools for AI agents*; *Code execution with MCP*.

**GO4 link.** INTEGRATION (I-series) tool design; RELIABILITY (V-series) where determinism
is used to bound failure modes.

---

### 4. "Skills compound — write it down so a future Claude reuses it" — **A**

**Folk-claim.** A skill "gets smarter every session": Claude on day 30 is better than on
day 1 because learnings accrue.

**Mechanism — and the important correction.** There is **no weight update**. The model does
not learn from your sessions. The compounding is entirely **externalised memory**: artefacts
(`CLAUDE.md`, `MEMORY.md`, skill folders, saved scripts) that are *re-loaded into context*
at the start of later sessions. "Anything that Claude writes down can be used [by] a future
version of itself" is literally true — and the "itself" is a fresh context window
re-reading files, not an updated network. This matters for design: the compounding is only
as good as the retrievability and signal-density of what you wrote down. Nothing accrues
that isn't captured in a file.

**Evidence.** Anthropic, *Claude Code memory* (CLAUDE.md / auto-memory loaded into the
system prompt each session); *Memory tool* (externalised `/memory` directory, read/written
as files — progressive disclosure applied to persistent state).

**GO4 link.** HUMANIZERS (H-series) longitudinal-continuity / memory patterns. The
correction ("no weights change") is exactly the kind of mechanistic claim those patterns
should carry.

---

### 6. 'Prefix caching: prompt engineering is cache engineering' — **A**

**Folk-claim.** Build your system prompt as a stable, consistent block. Don't vary it across calls. The first call is expensive; subsequent calls are cheap.

**Mechanism.** Provider-level KV cache reuse stores the KV state tensor $[L \times n \times n_{\text{kv}} \times d_{\text{head}}]$ for a stable prompt prefix. Re-sending identical tokens (byte-for-byte) within the TTL window injects cached states, skipping prefill. The savings follow directly from the $O(n^2)$ prefill cost (mechanism 2 in Chapter 0): Anthropic specifics — minimum 1,024 tokens, TTL approximately 5 minutes, cache reads at ~10% of normal input cost, cache writes at ~125%. Single-token variation in the prefix invalidates the cache for that position and all subsequent positions.

**Evidence.** Anthropic, *Prompt Caching* (docs.anthropic.com). Grade A: savings derivable from the O(n²) prefill cost; operational specifics are provider policy (Grade B).

**GO4 link.** New pattern O18 Cache-Warmed Worker Pool; K9 Long Context; H1 Identity Persistence; S2 Few-Shot static variant vs dynamic cost difference.

---

### 5. "Context engineering > prompt engineering" (the umbrella) — **A**

**Folk-claim.** Wordsmithing the instruction matters less than people think; what matters
is the whole configuration of context.

**Mechanism.** System prompt, tools, few-shot examples, memory, and conversation history all
**compete for one finite window**. Their *selection and arrangement* steers behaviour more
than the phrasing of any single instruction, because the model conditions on the entire
window at once. The discipline is curation under a token budget — "the smallest set of
high-signal tokens" — not rhetoric.

**Evidence.** Anthropic, *Building effective agents* (start simple, add structure only when
needed); *Effective context engineering for AI agents*.

**GO4 link.** The thesis that motivates the whole KNOWLEDGE category and reframes SIGNAL
(prompting) as one input among several.

---

### 7. 'Use subagents for complex tasks; small models for simple ones' — **A/B**

**Folk-claim.** Don't try to do everything in one big context. Spawn subagents. Use routing models for classification.

**Mechanism.** Two derivable facts: (1) Multi-agent decomposition bounds seq_len per agent, bounding the $O(n^2)$ attention compute per agent (mechanism 6 in Chapter 0). The orchestrator accumulates compact results; workers accumulate only their sub-task reasoning. Without isolation (O17 Agent Isolation), the bound is defeated and context grows as if it were a single agent. (2) Generation step cost scales with model size. Simple tasks (routing, classification, lookup) do not require large model capacity (mechanism 8). A 7B model for routing costs an order of magnitude less than a 70B model for the same decision.

**Evidence.** Mechanism (1): Grade A, derivable from n² cost. Mechanism (2): Grade A for direction, Grade B for capacity thresholds.

**GO4 link.** O6 Orchestrator-Workers; O3 Routing; O17 Agent Isolation; O18 Cache-Warmed Worker Pool.

---

### Supporting mechanism — why examples work at all (few-shot) — **A**

**Folk-claim.** Showing 2–3 worked examples beats describing the task abstractly.

**Mechanism.** In-context learning is, in significant part, a learned **induction-head**
circuit: a two-step attention pattern ("previous-token head" → "induction head") that
performs **match-and-copy / completion** of the form `[A][B] … [A] → [B]`. Few-shot examples
supply prior instances for this circuit to pattern-match and continue. The capability is a
*circuit that emerges during training*, not explicit instruction-following — which is why
examples are mechanically privileged over abstract description.

**Evidence.** Olsson et al. 2022, *In-context learning and induction heads*
(transformer-circuits.pub). *Note:* the page returned HTTP 403 to the fetcher this session,
so the quote was not re-verified live; the result is well established in the interpretability
literature. Treat as A, re-verify the exact wording before publication.

**GO4 link.** SIGNAL (S-series) few-shot / example-selection patterns.

---

## Mapping the two transcripts onto the existing catalogue

The two source transcripts in `GO4/` are not new patterns — they are popular restatements
of clusters GO4 already has. The work is to **backfill the "why"**, not to add entries.

| Transcript claim | GO4 home | Mechanism to backfill |
|---|---|---|
| Data room / source inventory / conflict log / missing-context / duplicates (Transcript 2) | **KNOWLEDGE (K-series)** | §2 — attention budget, n², lost-in-the-middle |
| Skills = description + instructions + tools; progressive disclosure (Transcript 1) | **INTEGRATION (I-series)** + tool design | §1 — three-level loading, decision-vs-execution cost |
| Save the script / code is deterministic (Transcript 1) | **INTEGRATION / RELIABILITY** | §3 — determinism vs sampling |
| Skills compound across sessions (Transcript 1) | **HUMANIZERS (H-series)** | §4 — externalised memory, no weight update |
| Composable not monolithic skills (Transcript 1) | **ORCHESTRATION (O-series)** | composability = bounded contexts that coordinate; ties to §5 |

Most GO4 patterns already populate "Open-Source Implementations" and "Known Uses". What they
generally lack is a **mechanistic justification with citations and an explicit
emergent/unproven flag.** That gap is what this synthesis fills.

---

## Where the "why" runs out

These patterns work empirically but the mechanism is **not** derived. Label them honestly in
any pattern that depends on them — calling something a mechanism when it is an observation is
the exact failure this catalogue is trying to avoid.

1. **Why progressive disclosure doesn't confuse the model.** ⚠ We can show it saves tokens;
   we *cannot* mechanistically explain why deferring information loading doesn't degrade the
   model's planning. Observed, not derived.
2. **Optimal context ordering.** ⚠ "system → memory → tools → history" is recommended from
   testing, not from an attention-level account of why that order wins.
3. **Skill trigger heuristics / ideal description length.** ⚠ How finely to scope a skill and
   how long its description should be is heuristically tuned; no published optimum.
4. **Magnitude of tool-description sensitivity.** Strong empirics (SWE-bench gains from
   description edits) but an incomplete attention-level account of *why* small wording
   changes move results so much. (B, trending toward "empirical".)
5. **In-context learning beyond induction heads.** ⚠ Induction heads explain simple
   match-and-copy; how ICL works for complex semantic, compositional, or novel-domain tasks
   is genuinely open in interpretability.

A useful editorial rule for GO4: **a pattern may only claim a mechanism at grade A/B; claims
that would be C or ⚠ must be written as "observed behaviour", with the open question named.**

---

## Relationship to the rest of GO4

- This document is the consolidated *research*. The decision on **how** it integrates into
  the book — a new `Evidence & Mechanism` field in `PATTERN-BUILD-SPEC.md` vs. a standalone
  appendix that patterns link to — is **deferred by design** (research first).
- The same mechanisms in §2 and §5 are the diagnosis behind the document-system work; see
  `../doc-system/DESIGN.md`. WS1 explains *why* a consistency-by-LLM-memory pipeline decays;
  WS2 is the cure.

---

## Citation verification status

| Source | Claim used | Verified this session |
|---|---|---|
| *Effective context engineering for AI agents* (Anthropic) | attention budget; n²; lost-in-context; smallest high-signal set; finite resource | ✅ fetched, quotes confirmed |
| *Equipping agents for the real world with Agent Skills* (Anthropic) | three-level progressive disclosure; unbounded bundled context | ✅ fetched, quotes confirmed |
| *In-context learning and induction heads* (Olsson et al. 2022) | induction-head match-and-copy → ICL | ⚠ page 403 to fetcher; claim well-established, re-verify wording before publishing |
| *Lost in the Middle* (Liu et al. 2024, arXiv:2307.03172) | U-shaped recall, mid-context loss | not re-fetched; widely cited primary result |
| *Writing effective tools for AI agents* / *Code execution with MCP* (Anthropic) | determinism vs sampling; token reduction | not re-fetched this session; from research pass |
| *Claude Code memory* / *Memory tool* (Anthropic) | externalised memory, no weight update | not re-fetched this session; from research pass |

Full bibliography appended to `../REFERENCES.md`.
