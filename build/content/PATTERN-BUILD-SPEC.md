# PATTERN-BUILD-SPEC

The canonical specification for building and auditing a GO4 pattern page.
Established by Category II — Knowledge (K1–K12); every other category must meet this standard.

This document is the **audit path**. A pattern is *complete* when it satisfies every requirement below.

---

## 1. File location

- A pattern lives at `patterns/{ID}-{Name}.md` as a **standalone file** (the canonical entry).
- The category file `patterns/{CATEGORY}.md` holds:
  - the section intro (Lead $\to$ Usage $\to$ Forces $\to$ Structure $\to$ Examples $\to$ See also), and
  - one-line stubs for each pattern pointing to its standalone file.
- Worked exemplars to read before building: **`patterns/K5-Adaptive-RAG.md`** (control pattern with variants and specialist models) and **`patterns/K12-Karpathy-Memory.md`** (newer pattern with two-actor separation). **`patterns/KNOWLEDGE.md`** shows the section intro and stub format.

---

## 2. Required H2 sections, in this order

1. `# {ID} — {Name}` — title line
2. Definition blockquote — one sentence, written as `> …`
3. `**Also Known As:**` — bold inline label
4. `**Classification:**` — bold inline label, naming Category, Band (where applicable), and role within band
5. `---` separator
6. `## Intent` — one sentence
7. `## Motivation` — the problem this pattern uniquely solves; why naive alternatives fail; the unique contribution. ~3 paragraphs.
8. `## Variants` — **only if applicable.** A pattern with named members differing only in content / parameter / policy / implementation. Each variant: bold name, one-sentence differentiator, attribution if applicable, trade-off vs the others.
9. `## Applicability` — `Use when:` bullets and `Do not use when:` bullets. Every "do not use when" names the right fallback pattern by ID.
10. `## Decision Criteria` — see §4.
11. `## Structure` — ASCII diagram of the static shape, fenced as a code block.
12. `## Participants` — see §5.
13. `## Collaborations` — prose walkthrough of how Participants interact.
14. `## Consequences` — bold subheaders **Benefits**, **Costs**, **Risks and failure modes**; bulleted lists under each.
15. `## Implementation Notes` — bulleted prose tuning guidance.
16. `## Implementation Sketch` — see §6.
17. `## Open-Source Implementations` — see §7.
18. `## Known Uses` — deployed systems (distinct from research and from variant repos).
19. `## Related Patterns` — bulleted cross-references using **bolded relationship verbs**: *Refines*, *Refined by*, *Composes with*, *Wraps*, *Sibling of*, *Distinct from*, *Competes with*, *Pairs with*, *Required by*, *Uses*.
20. `## Sources` — papers, primary references, technical reports.

---

## 3. Header triad — required formatting

After the title and before the `---`:

```
# {ID} — {Name}

> {one-sentence definition}.

**Also Known As:** {comma-separated aliases}. (Variants noted in parentheses, with cross-reference to Variants section.)

**Classification:** Category {N} — {Category name} · Band {N-X} {band name} (if applicable) · {one-clause role within the band}.

---
```

---

## 4. Decision Criteria — required substructure

The section that turns "is this right for me?" into a procedure.

- Open with **one sentence** stating when the pattern fits.
- **5 numbered measurements / criteria** (4–6 acceptable), each with:
  - a specific, quantitative-or-categorical test,
  - thresholds (numeric where possible),
  - a named fallback pattern by ID when the test fails.
- A closing **`**Quick test — {pattern name} is the right pattern when:**`** block:
  - 3–5 conjoined conditions (`condition X, and condition Y, and …`),
  - followed by a paragraph naming alternatives if any condition fails.

Example (from K9 Long Context):

```
**Quick test — K9 is the right pattern when:**

- T ≤ ~50% of the nominal window, *and*
- queries per session N ≥ 5 (so caching amortises the prefix), *and*
- the latency budget tolerates a long prefill, *and*
- T does not grow unboundedly during the session.

If any condition fails, choose K1 or one of its refinements. If T is large *and* the queries demand cross-document synthesis or relationship-tracing K1 cannot reach, choose **K3 GraphRAG** or **K4 RAPTOR** rather than just stuffing the window.
```

---

## 5. Participants — required table format

A Markdown table with exactly these four columns:

| Participant | Owns | Input $\to$ Output | Must not |

- 3+ rows; typical pattern has 4–8.
- Names bolded; *(optional)* marker where applicable.
- **Owns** = the one responsibility this participant holds.
- **Input $\to$ Output** = what it consumes and what it produces.
- **Must not** = the prohibition that prevents the pattern's most common failure mode. This column is where the page earns its keep — vague *Must nots* are a failure of the audit.

---

## 6. Implementation Sketch — required substructure

The section that makes the chaining of LLM steps and code wiring honest.

1. **Framing note** (blockquote): `> LLM = configured session (model + setup + per-call prompt); code = wiring.`
   (K5 carries a longer canonical explainer; others use the short reminder.)
2. **Composition** line: bold label, name the GO4 patterns this one chains with and the role each plays.
3. **The chain** table — columns `# / Step / Kind / Draws on`. `Kind` is `code` or `LLM` (or `LLM (or rule)` for optional-LLM steps). Patterns chained through this step are named in `Draws on`.
4. **Skeleton** — fenced code block, wiring only. Every line that is an LLM call carries an inline `# LLM` marker; every `code` line is unmarked. Patterns invoked are named in comments (`# K1 retriever`, `# K2 reformulation`, `# V9 bound`).
5. **The LLM sessions** table — columns `Session / Model / Setup — loaded once, before first call / Per-call prompt wraps`. Every `LLM` step in the chain has a row here.
6. **Specialist-model note** — paragraph. If a specialist (fine-tune, classifier, long-context-required, prompt-caching-required) is needed, name it as a build dependency. If none, say "None — a capable generalist suffices" and (where useful) name the prompt artifact that does the heavy lifting.

---

## 7. Open-Source Implementations — discipline

- Every GitHub URL **must be verified** in this session (web-search confirmation) before inclusion. Do not invent URLs.
- If no canonical project exists, say so honestly:
  > "{Pattern name} is an architecture / emerging pattern, not a library — there is no canonical project. The relevant references are: …"
  and point to provider cookbooks, surveys, or the nearest production embodiment.
- Distinguish from **Known Uses** (deployed production systems) and **Sources** (papers).
- Format each entry: `**Name** — [\`github.com/org/repo\`](https://github.com/org/repo) — short description of what it offers.`

---

## 8. Cross-pattern reference conventions

**Canonical numbering source:** `TAXONOMY-DRAFT.md` is the ground truth for every pattern ID and name. Confirm there before citing any cross-reference. Standalone pattern files in `patterns/` are authoritative *only when their ID matches TAXONOMY-DRAFT.md*; legacy/orphan standalone files with stale numbering must not be trusted.

Quick reference for the most-cited cross-band patterns (verify against `TAXONOMY-DRAFT.md` if in any doubt):
- **R3** Plan-and-Solve · **R4** ReAct · **R5** ReWOO · **R7** Reflexion · **R8** Self-Refine · **R13** CodeAct · **R17** Self-Consistency Voting · **R18** Graph of Thoughts · **R19** Step-Back Prompting · **R20** Chain-of-Verification
- **O2** Prompt Chaining · **O3** Routing · **O4** Parallelization · **O5** Evaluator-Optimizer · **O6** Orchestrator-Workers · **O7** Supervisor Hierarchy · **O11** Blackboard · **O17** Agent Isolation
- **V1** Human-in-the-Loop · **V9** Bounded Execution · **V10** Checkpointing · **V14** Trajectory Logging · **V15** LLM-as-Judge

- Reference patterns by their **current GO4 ID** (e.g. `K5 Adaptive RAG`), never by legacy / variant names (no `K5 Self-RAG`, no `K6 Corrective RAG`, no `K2 HyDE`).
- Demoted variants (Self-RAG, Corrective RAG, HyDE, episodic/semantic/procedural memory) appear ONLY inside the parent pattern's Variants section.
- Every "do not use when" item names the **named fallback** pattern by ID.
- Cross-category references are encouraged and should use the right neighbour:
  - Signal-layer setup: **S3 Persona**, **S5 Constraint Framing**, **S6 Output Template**, **S9 Constitutional Framing**.
  - Reliability: **V9 Bounded Execution** (for any loop), **V10 Checkpointing**, **V14 Trajectory Logging**, **V15 LLM-as-Judge**.
  - Reasoning: **R4 ReAct**, **R7 Reflexion**.
  - Orchestration: **O4 Parallelization**, **O6 Orchestrator-Workers**, **O17 Agent Isolation**.

---

## 9. The fundamentality test

Before settling that a pattern earns its number, check:

- Does it have a **distinct Intent, Forces resolution, Participants, and Structure**?
- Or does it decompose into another pattern plus an adaptor / prompt / parameter / data-shape choice?
- If it decomposes, it is a **Variant** of the parent or a **removal candidate**.

Established merges (use as reference cases):
- **K2 Query Transformation** absorbed HyDE (HyDE = K1 + a Signal-layer prompt step). HyDE is now a K2 variant.
- **K5 Adaptive RAG** absorbed Self-RAG and Corrective RAG (both = K1 + an evaluator + a control branch). They are now K5 variants.
- **K10 Long-Term Memory** absorbed Episodic + Semantic + Procedural (identical store/retrieve/inject mechanism, different content). They are now K10 variants.
- **K12 Karpathy Memory** was added because the LLM-curator structure is structurally distinct from K10 (vector store) and K11 (raw log) — a different Participant (the Curator) and a different read pattern.
- **O17 Agent Isolation** moved from Knowledge (K13) to Orchestration because the mechanism is sub-agent delegation, not context curation.

---

## 10. Conflicts that must be raised back to the main agent

Sub-agents working a pattern **must not** decide any of the following unilaterally. Surface them and stop:

1. A pattern that fails the fundamentality test — recommend merge / variant / removal.
2. A pattern that overlaps another so heavily one should subsume the other.
3. A pattern that, on close reading of the canonical reference, is materially different from how the existing draft describes it.
4. A pattern requiring renumbering because of a merge / split / addition.
5. A pattern whose Open-Source Implementations cannot be verified at all (no canonical references, and the existing draft cited URLs cannot be confirmed).

Each surfaced item should include: pattern ID, the conflict, the evidence, and a recommended resolution.

---

## 11. Audit checklist (for the audit agent)

For each pattern file, audit reports PASS/FAIL per dimension. Any FAIL on 1–10 = page **incomplete**; return to the build agent with a specific gap list.

1. **Required H2 sections** — all sections from §2 present, in the right order. Variants present iff the pattern has named variants.
2. **Header triad** — definition blockquote, AKA, Classification all present and correctly formatted (see §3).
3. **Decision Criteria** — opening sentence + 4–6 numbered measurements with thresholds and named fallbacks + Quick test with conjoined conditions + closing fallback paragraph (see §4).
4. **Participants table** — exactly the four columns, 3+ rows, each row has a substantive *Must not* (see §5).
5. **Implementation Sketch** — framing note + Composition line + chain table + Skeleton with `# LLM` markers + LLM sessions table + Specialist-model note (see §6).
6. **Open-Source Implementations** — verified URLs **or** honest "no canonical project" note with appropriate substitutes (see §7).
7. **Cross-reference currency** — no legacy IDs, no demoted variant names used as patterns, every "do not use when" names a fallback by ID (see §8).
8. **Internal consistency** — claims in different sections agree; the Structure diagram matches the Collaborations text; Variants in §8 of the page match those named in AKA and Decision Criteria.
9. **Cross-page references valid** — every pattern ID named exists in the current taxonomy.
10. **Length** — 150–250 lines as a rough envelope. Outside this range is non-blocking but should be noted.

The audit agent should also flag, for surface back to main, anything matching §10.

---

## 12. Build agent's job, step by step

1. **Read this spec in full.**
2. **Read the worked exemplars** — at minimum `patterns/K5-Adaptive-RAG.md`. For memory patterns also read `K12-Karpathy-Memory.md`.
3. **Read the current draft** for the pattern in `patterns/{CATEGORY}.md` and any standalone file that already exists.
4. **Apply the fundamentality test (§9).** If the pattern fails it, *stop and surface the recommendation* — do not build the page.
5. **Verify any GitHub URLs** for Open-Source Implementations via web search before writing them.
6. **Write the file** `patterns/{ID}-{Name}.md` to the full spec.
7. **Report**: pattern ID, file path, any §10 conflicts to raise, any spec dimensions you found ambiguous.

## 13. Audit agent's job, step by step

1. **Read this spec in full.**
2. **Read the target file** `patterns/{ID}-{Name}.md`.
3. **Run the §11 checklist.** Report PASS or FAIL per dimension.
4. If FAIL on 1–7: return a specific gap list for re-build.
5. If FAIL on 8–9 only: minor inconsistencies the audit agent may fix in place; document what was fixed.
6. If a §10 conflict surfaces: report it; do not resolve.
7. Final report: pattern ID, file path, PASS / FAIL per dimension, any fixes applied, any conflicts surfaced.
