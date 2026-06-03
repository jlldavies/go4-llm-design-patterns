# GO4 PDF Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the GO4 PDF across three phases: correct book order and TOC placement (Phase 1), reorganise and write content (Phase 2), and add LaTeX pattern card styling (Phase 3).

**Architecture:** `build_book.py` assembles markdown source files into `book.md` then runs pandoc → XeLaTeX. Phase 1 changes assembly order and TOC placement. Phase 2 edits and creates content files. Phase 3 adds raw LaTeX injection into the build and new `header.tex` definitions. Each phase produces a valid, buildable PDF. `INTRO.md` has already been rewritten and committed.

**Tech Stack:** Python 3, pandoc, XeLaTeX (Charter/Avenir Next fonts), eso-pic, TikZ, xcolor

---

## File Map

### Modified — Phase 1
- `build_book.py` — assembly order, manual TOC injection, remove `--toc` flag

### Modified — Phase 2
- `CHAPTER-0.md` — add 0.0 LLM primer, update preamble tone, update title
- `TAXONOMY-DRAFT.md` — strip to category table + 7 section descriptions only
- `patterns/HUMANIZERS.md` — add cognitive science grounding table
- `patterns/ORCHESTRATION.md` — add scaffold architecture dimensions
- `patterns/SIGNAL.md` — add quick-reference table
- `patterns/KNOWLEDGE.md` — add quick-reference table
- `patterns/REASONING.md` — add quick-reference table
- `patterns/RELIABILITY.md` — add quick-reference table
- `patterns/INTEGRATION.md` — add quick-reference table
- `build_book.py` — inject decision companion files, add Appendix C

### Created — Phase 2
- `OPEN-QUESTIONS.md`
- `APPENDIX-C.md`
- `patterns/SIGNAL-DECISION.md`
- `patterns/KNOWLEDGE-DECISION.md`
- `patterns/REASONING-DECISION.md`
- `patterns/ORCHESTRATION-DECISION.md`
- `patterns/RELIABILITY-DECISION.md`
- `patterns/INTEGRATION-DECISION.md`
- `patterns/HUMANIZERS-DECISION.md`

### Modified — Phase 3
- `header.tex` — eso-pic, tikz, xcolor, stripe definition
- `build_book.py` — inject `\setpatternname`/`\clearpatternname` per pattern

---

## Phase 1 — Skeleton

### Task 1: Restructure build_book.py — assembly order and TOC

**Files:**
- Modify: `build_book.py`

- [ ] **Step 1: Add TOC constant and update assemble()**

After the existing `PAGE_BREAK` constant (line ~157), add:

```python
TOC = "\n```{=latex}\n\\tableofcontents\n\\clearpage\n```\n"
```

Replace the entire `assemble()` function with:

```python
def assemble() -> str:
    parts = []

    # YAML front matter
    parts.append(
        "---\n"
        'title: "The Gang of Four for AI Engineering"\n'
        'subtitle: "A Pattern Catalog for LLM Systems"\n'
        'author: "James Davies"\n'
        'date: "May 2026"\n'
        "---\n"
    )

    # Introduction — before the TOC
    intro = read(ROOT / "INTRO.md")
    parts.append("# Introduction\n")
    parts.append(strip_first_h1(intro))
    parts.append("\n")

    # TOC placed after Introduction
    parts.append(TOC)

    # The Pattern Catalog (TAXONOMY-DRAFT) — strip planning sections
    tax = read(ROOT / "TAXONOMY-DRAFT.md")
    parts.append("# The Pattern Catalog\n")
    parts.append(strip_planning(strip_first_h1(tax)))
    parts.append("\n")

    # Categories
    for chapter_title, intro_file, standalones in CATEGORIES:
        parts.append(f"# {chapter_title}\n")
        intro_text = read(PATTERNS / intro_file)
        intro_body = strip_category_stubs(strip_first_h1(intro_text))
        parts.append(intro_body)
        parts.append("\n")

        for prefix in standalones:
            path = resolve(prefix)
            body = read(path)
            first_line = body.splitlines()[0]
            title = first_line.lstrip("# ").strip()
            parts.append(PAGE_BREAK)
            parts.append(f"## {title}\n")
            rest = strip_first_h1(body)
            parts.append(shift_headings(rest, by=2))
            parts.append("\n")

    # Mechanisms — back-matter reference (formerly Chapter 0)
    parts.append(PAGE_BREAK)
    chapter0 = read(ROOT / "CHAPTER-0.md")
    parts.append("# The Mechanical Foundation\n")
    parts.append(strip_first_h1(chapter0))
    parts.append("\n")

    # Appendix A — Conflicts
    parts.append(PAGE_BREAK)
    parts.append("# Appendix A — Conflicts\n")
    parts.append(strip_first_h1(read(PATTERNS / "CONFLICTS.md")))
    parts.append("\n")

    # Appendix B — References
    parts.append(PAGE_BREAK)
    parts.append("# Appendix B — References\n")
    parts.append(strip_first_h1(read(ROOT / "REFERENCES.md")))
    parts.append("\n")

    return "\n".join(parts)
```

- [ ] **Step 2: Remove `--toc` and `--toc-depth=2` from the pandoc command**

In `main()`, find the `cmd` list and remove these two entries:
```python
        "--toc", "--toc-depth=2",
```

- [ ] **Step 3: Build and verify chapter order**

```bash
cd /Users/james/Library/CloudStorage/Dropbox/Code/GO4
python3 build_book.py
grep -n "^# " book.md | head -20
```

Expected output shows Introduction first, then Pattern Catalog, then the 7 categories, then The Mechanical Foundation, then Appendix A, Appendix B — in that order. No errors from pandoc.

- [ ] **Step 4: Commit**

```bash
git add build_book.py
git commit -m "phase 1: move mechanisms to back, place intro before TOC"
```

---

### Task 2: Update CHAPTER-0.md for back-of-book placement

**Files:**
- Modify: `CHAPTER-0.md`

- [ ] **Step 1: Update the chapter title (line 1)**

```
# The Mechanical Foundation
```

- [ ] **Step 2: Replace the "Why This Chapter Exists" body paragraph**

Find this text (after the `## Why This Chapter Exists` heading):
```
This chapter describes what actually happens inside the model at the matrix and tensor level — so that the mechanism citations throughout the catalog have a derivable foundation rather than a purely empirical one. It goes one level deeper than engineering blog posts and practitioner advice: those sources establish that certain approaches work; this chapter establishes why.
```

Replace with:
```
This chapter derives twelve mechanistic principles from how transformers actually compute — from the attention bilinear form and KV cache structure through to prefix caching economics and subagent context bounding. It is a derivation resource: when a pattern entry cites a mechanism (for example, *mechanism 2 — n² compute cost*), this is where that citation resolves. You do not need to read this chapter to use the catalog. Read it when you want to understand why a pattern's costs are what they are, not just that they are.
```

- [ ] **Step 3: Build and verify**

```bash
python3 build_book.py
grep -A4 "The Mechanical Foundation" book.md | head -8
```

Expected: updated preamble text appears.

- [ ] **Step 4: Commit**

```bash
git add CHAPTER-0.md
git commit -m "phase 1: update mechanisms chapter preamble and title for back-of-book placement"
```

---

## Phase 2 — Content

### Task 3: Create OPEN-QUESTIONS.md and remove from TAXONOMY-DRAFT

**Files:**
- Create: `OPEN-QUESTIONS.md`
- Modify: `TAXONOMY-DRAFT.md`

- [ ] **Step 1: Create OPEN-QUESTIONS.md**

```markdown
# GO4 — Open Questions and Research Gaps

*Living document. Not included in the PDF build.*

---

## Open Questions and Research Gaps

1. **Long-running agent session coherence**: No consensus on preventing context drift over hours/days
2. **Agent trust hierarchies**: How does Agent B verify that instructions from Agent A are legitimate? (V3 partially addresses; V4 for data; nothing for instruction provenance)
3. **Agent versioning and compatibility**: When a tool or sub-agent is updated, how do orchestrators handle the change?
4. **Cost-aware pattern selection**: Dynamic switching between R5 (ReWOO) and R4 (ReAct) based on runtime cost signals
5. **Cross-model composition**: No established patterns for mixing models from different providers in one pipeline
6. **O10 (Swarm) production viability**: No consensus on when peer-to-peer emerges, vs degrade to O7
7. **Multi-agent consistency**: Per-agent K10 stores create divergent memory; shared substrates are proposed but not standardised
8. **Prompt injection at orchestration layer**: V6 patterns are ad hoc; CaMeL is promising but not widely adopted
9. **Evaluation for long-horizon tasks**: V16/V17 evaluate per-interaction; no consensus on task-completion evals for multi-hour agent runs
10. **Should there be a Category 0**: "When not to use AI" — currently embedded in anti-patterns A2 and A13
11. **Humanizer identity continuity across model upgrades**: When the base model changes, does the agent's accumulated identity survive? No established pattern.
12. **Lesson library poisoning**: H2 (Episodic Self-Improvement) is vulnerable to adversarially-induced wrong lessons persisting across sessions — no defense pattern yet
13. **Constitutional evolution convergence**: Does H5 converge to a stable set of principles or continue drifting? What terminates the evolution?
14. **Authentic vs. simulated identity**: Philosophical question with practical implications — does H1 create genuine continuity or a performance of continuity? Matters for trust calibration.
15. **Cross-agent humanizer state**: If multiple agent instances run simultaneously, how do they share (or isolate) H1–H10 state without racing?

---

## Next Steps

- [ ] Cross-pattern conflict and tension map (patterns/CONFLICTS.md)
- [ ] Build explicit relationship graph: what composes, what conflicts, what requires what
- [ ] Add code examples (Python + TypeScript) for key patterns
- [ ] Define formal "forces" for each pattern
- [ ] Consider POSA format as alternative to GoF for non-OOP patterns
- [ ] Workshop "Category 0: When Not to Use AI"
- [ ] Map each pattern to SDLC phase
- [ ] Add empirical evidence table (quantified results vs. qualitative only)
```

- [ ] **Step 2: Remove Open Questions section from TAXONOMY-DRAFT.md**

Delete from `## Open Questions and Research Gaps` to the end of the file (everything from line ~423 onward). The file should end after the `## Cognitive Science Grounding` section's closing `---`.

- [ ] **Step 3: Verify build still passes**

```bash
python3 build_book.py
echo "Exit: $?"
```

Expected: exit 0.

- [ ] **Step 4: Commit**

```bash
git add OPEN-QUESTIONS.md TAXONOMY-DRAFT.md
git commit -m "phase 2: extract open questions + next steps to OPEN-QUESTIONS.md"
```

---

### Task 4: Create APPENDIX-C.md and strip TAXONOMY-DRAFT to overview only

**Files:**
- Create: `APPENDIX-C.md`
- Modify: `TAXONOMY-DRAFT.md`

- [ ] **Step 1: Create APPENDIX-C.md**

Extract the Anti-Pattern Registry and Pattern Composition Examples sections from TAXONOMY-DRAFT verbatim:

```markdown
# Appendix C — Anti-Patterns and Composition Examples

## Anti-Pattern Registry

| # | Anti-Pattern | Description | Costs | Better Alternative |
|---|---|---|---|---|
| A1 | **God Prompt** | All instructions in one massive prompt | Attention dilution; maintenance nightmare | Decompose with O2/O6 |
| A2 | **Over-Agentification** | Agentic loops when deterministic code suffices | Cost; latency; brittleness | O2 (Prompt Chaining) or just write code |
| A3 | **Uncontrolled Recursion** | Reflection/planning loops with no exit condition | Runaway cost; stuck agents | V9 (Bounded Execution) |
| A4 | **Agent Sprawl** | Proliferating agents without ownership or governance | Inconsistency; undebuggable | V14 (Trajectory Logging) + V1 (H-in-the-L) |
| A5 | **Output-Only Guardrails** | Safety checks only on final output | Intermediate failures propagate | V5 (Guardrail Layering) at all 4 points |
| A6 | **Vibe-Checking as Testing** | Subjective assessment replacing eval frameworks | No regression detection | V15 (LLM-as-Judge) + V16 (Offline Eval) |
| A7 | **Context Hoarding** | Never pruning context; dumping everything in | Token waste; attention degradation; cost | K6/K7 (Compress/Prune) or O17 (Agent Isolation) |
| A8 | **Synchronous Everything** | Running independent sub-tasks sequentially | Unnecessary latency | O4 (Parallelization) |
| A9 | **Stateful Reducer** | Hidden agent state not reflected in business state | Bugs; replay failure; debugging hell | V12 (Stateless Reducer) + V10 (Checkpoint) |
| A10 | **Silent Failure** | Agent fails quietly; no error surfaced | Data loss; cascading failures | V1 + V14 + V10 |
| A11 | **Framework Lock-in** | Choosing LangChain/heavy framework first | Abstraction ceiling; debugging difficulty; cost opacity | Own your control flow |
| A12 | **Tool Proliferation** | Adding tools without tool budget management | Context overflow; selection accuracy collapse | V13 (Tool Budget) + I4 (CLI first) |
| A13 | **Pilot Simplification** | Clean data/sandbox in pilot; assume production is similar | 88% production failure rate | Data realism in pilots; governance from day 1 |
| A14 | **Trust Handoff** | Agent trusts instructions from other agents without verification | Prompt injection cascading | V3 (Rule of Two) + V4 (Dual LLM) |
| A15 | **Untraced Agent** | No observability; no audit trail | Debugging takes hours not minutes; no compliance | V14 (Trajectory Logging) from day 1 |

---

## Pattern Composition Examples

### Example 1: Standard Production Coding Agent (Claude Code, Devin)
`S3 + S4 + K1 + K8 + R4 + O6 + O4 + V1 + V9 + V14 + I2/I3`

### Example 2: Research Agent
`S4 + K10 + R4 + O4 + O8 + V9 + V14`

### Example 3: Safety-Critical Enterprise Agent
`S3 + S9 + K1 + R3 + O6 + V1 + V3 + V4 + V5 + V7 + V8 + V14 + I1`

### Example 4: Customer Support Router
`O3 + O1 + K1 + K11 + V1 + V5 + V17`

### Example 5: Document Analysis Pipeline
`S2 + K6 + O2 + O5 + V5 + V16`

### Example 6: Multi-Agent Research Network
`S3 + K10 + R4 + O7 + O11 + I5 + I6 + V14`

### Example 7: Long-Term Personal Research Assistant
`H1 + H2 + H4 + H7 + H9 + H10 + K11 + R7 + V1`

### Example 8: Autonomous Creative Agent
`H1 + H3 + H6 + H7 + K10 + R4`

### Example 9: Enterprise Process Automation Agent
`H2 + H4 + H5 + H9 + V1 + V7 + V14`
```

- [ ] **Step 2: Strip TAXONOMY-DRAFT.md to category overview only**

The file must be reduced to just the opening preamble and overview table. Replace the entire file content with:

```markdown
# GO4 Taxonomy

*A pattern language for AI engineering, structured analogously to the Gang of Four.*

---

## The Seven Categories

The original GoF had three categories: Creational, Structural, Behavioural. AI engineering patterns span more distinct concerns:

| Category | Governs | Analogy to GoF |
|---|---|---|
| **I. Signal** | How you shape instructions, personas, and examples | Creational — what gets built from what |
| **II. Knowledge** | What information and memory the model has access to | Structural — how things are assembled and connected |
| **III. Reasoning** | How a model structures its thinking process | Behavioural (individual) |
| **IV. Orchestration** | How agents coordinate, delegate, and interoperate | Behavioural (collective) |
| **V. Reliability** | Safety, cost, governance, observability | Cross-cutting / NFR |
| **VI. Integration** | How agents connect to tools, services, and each other | Infrastructure / Connective tissue |
| **VII. Humanizers** | How agents develop continuity, identity, and adaptive evolution | Emergent / Longitudinal |

---

**Signal patterns** govern how instructions, personas, and examples are shaped before the model sees them — the prompt design surface.

**Knowledge patterns** govern context engineering: what information and memory the model has access to during a task, and how that context is assembled, retrieved, compressed, and persisted.

**Reasoning patterns** govern how a model structures its thinking: chain-of-thought, planning, tool use, reflection, search, and verification.

**Orchestration patterns** govern how multiple inferences and agents are coordinated — chains, routers, parallel workers, hierarchies, and multi-agent collectives.

**Reliability patterns** govern the cross-cutting concerns that production systems cannot omit: safety bounds, cost control, observability, evaluation, and recovery.

**Integration patterns** govern how agents reach the world outside their prompt: deterministic API calls, typed tool calling, standardised protocol servers, and inter-agent delegation.

**Humanizer patterns** govern the longitudinal layer: how agents develop continuity, self-knowledge, and adaptive behaviour across sessions.
```

- [ ] **Step 3: Update build_book.py to add Appendix C**

In the `assemble()` function, after Appendix B, add:

```python
    # Appendix C — Anti-Patterns and Composition Examples
    parts.append(PAGE_BREAK)
    parts.append("# Appendix C — Anti-Patterns and Composition Examples\n")
    parts.append(strip_first_h1(read(ROOT / "APPENDIX-C.md")))
    parts.append("\n")
```

- [ ] **Step 4: Build and verify**

```bash
python3 build_book.py
grep "^# Appendix" book.md
```

Expected: Appendix A, B, and C all appear.

- [ ] **Step 5: Commit**

```bash
git add APPENDIX-C.md TAXONOMY-DRAFT.md build_book.py
git commit -m "phase 2: create APPENDIX-C, strip TAXONOMY-DRAFT to overview"
```

---

### Task 5: Create decision companion files — extracted from TAXONOMY-DRAFT

**Files:**
- Create: `patterns/REASONING-DECISION.md`
- Create: `patterns/ORCHESTRATION-DECISION.md`
- Create: `patterns/INTEGRATION-DECISION.md`

- [ ] **Step 1: Create patterns/REASONING-DECISION.md**

```markdown
# Reasoning Pattern Selection

## Decision Flow

```
Need token efficiency above all?
  → R5 (ReWOO): 5× reduction vs ReAct; plan all tool calls upfront

Need mid-run adaptation to observations?
  → R4 (ReAct): adaptive tool use; each action informs the next

Multi-tool task needing self-debugging?
  → R13 (CodeAct): ~20pp accuracy gain over JSON tool calls

Hard open-ended problem, quality trumps cost?
  → R9 (Tree of Thoughts) or R10 (LATS)

Clear pass/fail criteria and retries are acceptable?
  → R7 (Reflexion): verbal self-critique across retries

Math or numerical computation?
  → R14 (Program of Thoughts): delegate to a deterministic executor

Parallel generation needed to reduce latency?
  → R12 (Skeleton-of-Thought): outline first, fill sections in parallel

Reusable reasoning templates exist for this task type?
  → R11 (Buffer of Thoughts): 12% cost of ToT/GoT

Multi-hop factual question?
  → R6 (Self-Ask): sub-question chains

Quick reasoning improvement with no examples?
  → R1 (Zero-Shot CoT): "think step by step"
```

## Cost Guide

| Pattern | LLM Calls | Relative Cost | Notes |
|---|---|---|---|
| R1 Zero-Shot CoT | 1 | Baseline | Add "think step by step" only |
| R2 Few-Shot CoT | 1 | Low + example tokens | Static examples cache cleanly |
| R3 Plan-and-Solve | 2 | Low | Plan + execute; two clean calls |
| R4 ReAct | N per step | Medium–High | Scales with task complexity |
| R5 ReWOO | 2 total | **5× cheaper than R4** | All tool calls must be independent |
| R6 Self-Ask | 1 + N follow-ups | Medium | Sub-question depth drives cost |
| R7 Reflexion | N × retries | High | Needs measurable success criterion |
| R8 Self-Refine | N iterations | Medium | In-session; no separate judge |
| R9 ToT | N (branching) | Very High | Use when path genuinely unknown |
| R10 LATS | N (tree search) | Highest | Highest quality; highest cost |
| R11 BoT | 1 + template | Low | Templates amortise across calls |
| R12 SoT | 1 + N parallel | Medium | Latency win via parallelism |
| R13 CodeAct | N (with execution) | Medium | Self-debugging loop |
| R14 PoT | 1 + execution | Low | Deterministic computation free |
```

- [ ] **Step 2: Create patterns/ORCHESTRATION-DECISION.md**

```markdown
# Orchestration Pattern Selection

## Primary Decision Flow

```
Is the task solvable with a single LLM call + tools?
  YES → O1 (Single Agent) + appropriate Signal and Reasoning patterns

  NO:
    Does the task decompose into FIXED sequential steps?
      YES → O2 (Prompt Chaining)

    Are there distinct input TYPES needing specialisation?
      YES → O3 (Routing)

    Are sub-tasks INDEPENDENT and can run in parallel?
      YES → O4 (Parallelization)
        + O18 (Cache-Warmed Worker Pool) if workers share a prefix >1024 tokens

      NO → O6 (Orchestrator-Workers) + R4 (ReAct) inside workers
           + O17 (Agent Isolation) — REQUIRED companion to O6

Does output quality matter AND can it be verified objectively?
  YES → O5 (Evaluator-Optimizer) or R7 (Reflexion)

Are there distinct specialised roles exceeding a single context?
  YES → O7 (Supervisor Hierarchy)

Do agents need to share state asynchronously across turns?
  YES → O11 (Blackboard) or K10 (Long-Term Memory shared substrate)
```

## Composition Law

Most production systems are: `O6 + O4 + R4 (per worker) + O17 + O18`

- O6 without O17 loses the n² cost bounding that produces the quality win
- O4 without O18 misses ~85% cost reduction on shared worker context
- O16 (Hybrid Control Flow) describes most real agents — stacked primitives, not a single pattern

## Cost Escalation by Pattern

| Pattern | Relative cost | When justified |
|---|---|---|
| O1 Single Agent | Baseline | Default; increase complexity only when this fails |
| O2 Prompt Chaining | Low | Fixed decomposition; fully testable |
| O3 Routing | Low + classifier | Distinct specialised inputs |
| O4 Parallelization | N× but parallel | Independent sub-tasks; latency matters |
| O5 Evaluator-Optimizer | 2× + loop | Objective quality criterion exists |
| O6 Orchestrator-Workers | High | Dynamic decomposition required |
| O7 Supervisor Hierarchy | Very high | O6 applied recursively; most complex tasks |
```

- [ ] **Step 3: Create patterns/INTEGRATION-DECISION.md**

```markdown
# Integration Pattern Selection

## Decision Flow

```
Does LLM reasoning determine which action to take?
  NO → I1 (Direct API Call): synchronous HTTP, no model involvement

  YES:
    Does a CLI already exist for this tool?
      YES → I4 (CLI Invocation) first — zero schema overhead

    How many tools, and are they shared across agents?
      1–5 tools, single agent → I2 (Function/Tool Call)
      5–20 tools shared across agents → I2 + I3 hybrid
      20+ tools → I3 (MCP Server) with gateway + dynamic discovery

    Do multiple agents from different vendors need to coordinate?
      YES → I5 (Agent Card) for discovery + I6 (A2A Delegation) for execution
```

## Cost Reality

| Pattern | Context overhead | Notes |
|---|---|---|
| I1 Direct API | None | Model not involved; deterministic |
| I2 Function Call | Schema tokens (per tool) | Each tool schema costs attention budget |
| I3 MCP Server | High | GitHub MCP alone: 40,000–55,000 tokens/request |
| I4 CLI Invocation | Near zero | Existing CLI; command string only |
| I5 Agent Card | Minimal (JSON descriptor) | Discovery only; no execution cost |
| I6 A2A Delegation | Per sub-task | Full task delegation; cost of the delegated agent |

**Design tool budgets before choosing integration patterns.** 4–5 MCP servers = 60,000+ context tokens on schemas alone. Apply V13 (Tool Budget) before adding I3 servers.
```

- [ ] **Step 4: Commit**

```bash
git add patterns/REASONING-DECISION.md patterns/ORCHESTRATION-DECISION.md patterns/INTEGRATION-DECISION.md
git commit -m "phase 2: create reasoning, orchestration, integration decision companion files"
```

---

### Task 6: Create decision companion files — new content

**Files:**
- Create: `patterns/SIGNAL-DECISION.md`
- Create: `patterns/KNOWLEDGE-DECISION.md`
- Create: `patterns/RELIABILITY-DECISION.md`
- Create: `patterns/HUMANIZERS-DECISION.md`

- [ ] **Step 1: Create patterns/SIGNAL-DECISION.md**

```markdown
# Signal Pattern Selection

## Decision Flow

```
Start with S1 (Zero-Shot). Upgrade only when you can measure the gap.

Is format control or style matching the core problem?
  → S2 (Few-Shot): static examples if possible; dynamic only if required
    ⚠ Dynamic S2 breaks prefix cache for all upstream stable patterns

Does the task need domain expertise framing or a specific tone?
  → S3 (Persona): bundle with S5/S6/S9 in a single stable system prompt

Are there specific behaviours the model must never exhibit?
  → S5 (Constraint Framing): explicit prohibition list alongside task description

Does a downstream system need consistent structured output?
  → S6 (Output Template): output skeleton in system prompt

Does the task have multiple steps where order matters?
  → S4 (Instruction Decomposition): numbered steps in the instruction

Do values or principles need runtime enforcement?
  → S9 (Constitutional Framing): self-critique loop against explicit principles

Does the prompt itself need to be optimised automatically?
  → S8 (Meta-Prompt): requires V15 (LLM-as-Judge) or R17 as evaluator
    ⚠ Measure cost before using; much more expensive than S1–S6/S9
```

## Caching Guide

S3, S5, S6, and S9 are **setup-band** patterns. Bundle them together in a single stable system prompt — this is the cacheable prefix unit. Provider prefix caching (Anthropic: ~5 min TTL, ~10% cost on cache hits) reduces the cost of this bundle to near-zero for all calls within the TTL window.

| Pattern | Cacheable? | Notes |
|---|---|---|
| S1 Zero-Shot | Yes — full prompt | Cheapest baseline |
| S2 Few-Shot (static) | Yes | Stable prefix; caches cleanly |
| S2 Few-Shot (dynamic/RAG) | **No** | Changes prefix every call; forfeits cache for all upstream patterns |
| S3 Persona | Yes | Bundle with S5, S6, S9 |
| S4 Instruction Decomposition | Yes | Merge into S3 block when possible |
| S5 Constraint Framing | Yes | Bundle with S3, S6, S9 |
| S6 Output Template | Yes | Bundle with S3, S5, S9 |
| S8 Meta-Prompt | Partial | Only meta-prompt prefix caches |
| S9 Constitutional Framing | Yes | Bundle with S3, S5, S6 |
```

- [ ] **Step 2: Create patterns/KNOWLEDGE-DECISION.md**

```markdown
# Knowledge Pattern Selection

## Decision Flow

```
Is this a recurring workflow type with known context requirements?
  → K13 (Retrieval Bundle): specify the exact context bundle BEFORE writing retrieval code
    Prevents the rediscovery problem (up to 85% of token budget on context assembly)

Does the entire working set fit an affordable context window?
  → Benchmark K9 (Long Context) vs K1 (Vanilla RAG) at your actual corpus size
    K9 wins when: corpus fits, queries are diverse, retrieval precision is hard to tune
    K1 wins when: corpus is large, queries are targeted, caching matters

Do you need in-context retrieval?
  Are queries multi-hop or relational? → K3 (GraphRAG)
  Variable abstraction levels required? → K4 (RAPTOR)
  Factuality-critical, possibly stale corpus? → K5 (Adaptive RAG)
  Query/document mismatch suspected? → K2 (Query Transformation) wrapping K1
  Default retrieval: → K1 (Vanilla RAG)

Does the context window need management during a session?
  Remove spent/irrelevant spans (lossless)? → K7 (Context Pruning) — preserves prefix cache
  Summarise overflowing history (lossy)? → K6 (Context Compression)
    ⚠ K6 and K7 invalidate the provider prefix cache
  Agent needs explicit scratchpad? → K8 (Working Memory)

Do you need cross-session memory?
  Flat facts across sessions? → K10 (Long-Term Memory)
  Append-only activity log + prefix caching? → K11 (Observational Memory)
  LLM-curated structured notes? → K12 (Karpathy Memory)
  K11 and K12 are complementary branches of the same memory strategy — run together
```

## Context Budget Guide

| Pattern | Context cost | Cache impact |
|---|---|---|
| K1 Vanilla RAG | Chunks only (variable) | Neutral |
| K2 Query Transformation | 1–3 extra LLM calls | Neutral |
| K3 GraphRAG | High (graph + summaries) | Neutral |
| K4 RAPTOR | Medium (hierarchical summaries) | Neutral |
| K5 Adaptive RAG | +1–2 LLM calls per query | Neutral |
| K6 Context Compression | Saves tokens; **breaks prefix cache** | Cache-busting |
| K7 Context Pruning | Saves tokens; **breaks prefix cache** | Cache-busting |
| K8 Working Memory | Small scratchpad overhead | Neutral if at end of context |
| K9 Long Context | Full corpus in window | High but cacheable |
| K10 Long-Term Memory | Retrieved facts only | Neutral |
| K11 Observational Memory | Append-only log | **Cache-friendly** |
| K12 Karpathy Memory | Dense curated notes | Cacheable if stable |
| K13 Retrieval Bundle | Design-time specification; no runtime cost | Enables caching discipline |
```

- [ ] **Step 3: Create patterns/RELIABILITY-DECISION.md**

```markdown
# Reliability Pattern Selection

## Decision Flow

```
Does the agent take irreversible or high-blast-radius actions?
  YES → V1 (Human-in-the-Loop) at those decision boundaries
  MONITOR only → V2 (Human-on-the-Loop)
  Two independent confirmations required → V3 (Rule of Two)

Does the agent process untrusted external content?
  YES:
    Private data + untrusted content + external comms? → V3 (lethal trifecta check)
    Route untrusted content to quarantined model → V4 (Dual LLM)
    Inject structural defences at prompt boundaries → V6 (Prompt Injection Shield)

Does the agent run in a loop or have no natural exit condition?
  YES → V9 (Bounded Execution) — REQUIRED; hard caps on steps, cost, wall-time
    ⚠ V20 retry loops expand context ~2× per retry; include in V9 token cap calculation

Does the agent generate or execute code?
  YES → V8 (Tool Sandboxing): restrict filesystem, network, clock

Does the agent have more than 10 active tools?
  YES → V13 (Tool Budget): hard limit on active schema tokens
    Tool selection accuracy: 43% at low counts → 14% at high counts (3× degradation)

Does the agent need to recover from partial failure without restart?
  YES → V10 (Checkpointing): replayable state snapshots

Are there multiple safety boundaries (input, tool calls, output)?
  YES → V5 (Guardrail Layering): safety checks at all four points

Is output conformance to a schema required?
  YES → V20 (Schema Validation): validate-and-reask loop
    Bundle with V9: each retry expands context

Is output quality measurable?
  Pre-deployment → V16 (Offline Eval)
  In production → V17 (Online Eval)
  Second model as judge → V15 (LLM-as-Judge)

Is full observability required (compliance, debugging)?
  YES → V14 (Trajectory Logging): OTel-compatible trace from day 1

Does the agent need declarative policy enforcement outside the prompt?
  YES → V7 (AgentSpec): deterministic policy; not probabilistic like S9
```

## Must-Have Baseline

Every production agent needs at minimum: **V9 + V14**. Add V1 at any irreversible action boundary. Add V5 at any external input boundary.
```

- [ ] **Step 4: Create patterns/HUMANIZERS-DECISION.md**

```markdown
# Humanizer Pattern Selection

## Decision Flow

```
Does the agent run across multiple sessions?
  NO → Humanizer patterns do not apply; use Signal patterns for in-session persona

  YES — start here:
    H1 (Identity Persistence) — PREREQUISITE for all other Humanizer patterns
    Stable identity must exist before it can evolve

    After first failures emerge:
      H2 (Episodic Self-Improvement) — learn from mistakes across sessions
        Requires: K11 or K10 as memory substrate

    After first successes:
      H4 (Procedural Skill Accumulation) — distil successful trajectories into reusable skills
        Complements H2: H2 learns from failure, H4 from success

    As user model grows:
      H7 (Adaptive Persona) — adapt communication style per user
      H10 (Relational Memory) — persist user relationship state
        ⚠ H10 requires explicit user consent and right-to-deletion

    When reasoning loops stall or creativity degrades:
      H3 (Entropy-Driven Curiosity) — autonomous deadlock breaking

    For persistent background reasoning between turns:
      H6 (Continuous Inner Monologue) — separate thinker from responder

    For accurate self-knowledge and capability routing:
      H9 (Observational Identity) — explicit model of own capabilities

    With human governance board and formal oversight:
      H5 (Constitutional Self-Alignment) — evolving principles with mandatory checkpoints
        ⚠ NEVER implement H5 without mandatory human review; alignment risk
```

## Adoption Sequence

| Stage | Patterns | Purpose |
|---|---|---|
| Foundation | H1 | Stable identity across sessions |
| Learning | H2 + H4 | Improve from failure and success |
| Adaptation | H7 + H10 | Serve users better over time |
| Advanced | H3 + H6 + H9 | Autonomous, self-aware operation |
| Governed | H5 | Evolving principles with oversight |

All Humanizer patterns require K11 (Observational Memory) or K10 (Long-Term Memory) as infrastructure. H1 is a prerequisite for all others.

## Anti-Patterns

- **HA1 — Simulated Emotion**: emotional language without genuine affective model (manipulation)
- **HA2 — Unbounded Relationship Depth**: H10 without ethical guardrails → parasocial harm
- **HA3 — Identity Drift**: H7/H10 without H1 → agent becomes whoever the user wants
- **HA4 — Autonomous Principle Adoption**: H5 without human review → alignment risk
- **HA5 — Stale Self-Model**: H9 without decay functions → overconfident outdated self-assessment
```

- [ ] **Step 5: Commit**

```bash
git add patterns/SIGNAL-DECISION.md patterns/KNOWLEDGE-DECISION.md \
        patterns/RELIABILITY-DECISION.md patterns/HUMANIZERS-DECISION.md
git commit -m "phase 2: create signal, knowledge, reliability, humanizer decision companion files"
```

---

### Task 7: Update build_book.py to inject decision companion files

**Files:**
- Modify: `build_book.py`

The build script needs to append each section's decision companion file after its final pattern, before the next chapter.

- [ ] **Step 1: Update the CATEGORIES loop in assemble()**

Replace the categories loop block with:

```python
    # Categories
    for chapter_title, intro_file, standalones in CATEGORIES:
        parts.append(f"# {chapter_title}\n")
        intro_text = read(PATTERNS / intro_file)
        intro_body = strip_category_stubs(strip_first_h1(intro_text))
        parts.append(intro_body)
        parts.append("\n")

        for prefix in standalones:
            path = resolve(prefix)
            body = read(path)
            first_line = body.splitlines()[0]
            title = first_line.lstrip("# ").strip()
            parts.append(PAGE_BREAK)
            parts.append(f"## {title}\n")
            rest = strip_first_h1(body)
            parts.append(shift_headings(rest, by=2))
            parts.append("\n")

        # Decision companion file — appended after section's final pattern
        decision_file = PATTERNS / intro_file.replace(".md", "-DECISION.md")
        if decision_file.exists():
            parts.append(PAGE_BREAK)
            parts.append(strip_first_h1(read(decision_file)))
            parts.append("\n")
```

- [ ] **Step 2: Build and verify all seven decision files appear**

```bash
python3 build_book.py
grep "Pattern Selection" book.md
```

Expected: 7 lines, one per section (Signal Pattern Selection, Knowledge Pattern Selection, etc.).

- [ ] **Step 3: Commit**

```bash
git add build_book.py
git commit -m "phase 2: inject decision companion files at end of each section"
```

---

### Task 8: Add content to section intro files (quick-reference tables, cognitive science, scaffold)

**Files:**
- Modify: `patterns/SIGNAL.md`
- Modify: `patterns/KNOWLEDGE.md`
- Modify: `patterns/REASONING.md`
- Modify: `patterns/ORCHESTRATION.md`
- Modify: `patterns/RELIABILITY.md`
- Modify: `patterns/INTEGRATION.md`
- Modify: `patterns/HUMANIZERS.md`

Each section intro file needs a `## Quick Reference` table added before the per-pattern stubs (which are stripped by the build). The table goes after the existing `## See also` section. HUMANIZERS.md and ORCHESTRATION.md also get additional content blocks.

- [ ] **Step 1: Add quick-reference table to patterns/SIGNAL.md**

Add before the `## S1 — Zero-Shot` stub line:

```markdown
## Quick Reference

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| S1 | **Zero-Shot** | Direct Instruction | Task with no examples; rely on model priors | Simple, well-defined tasks where model knowledge is sufficient |
| S2 | **Few-Shot** | In-Context Learning | Provide examples to demonstrate desired format or behaviour | Format control, style matching, novel task types |
| S3 | **Persona** | Role Prompting | Assign the model an identity to frame knowledge and tone | Expert framing, domain-specific tasks, tone alignment |
| S4 | **Instruction Decomposition** | Step Prompting | Break complex instruction into numbered sequential steps | Multi-step tasks with clear ordering |
| S5 | **Constraint Framing** | Negative Prompting | Define what model must NOT do as prominently as what it should | Safety-sensitive, compliance, avoiding known failure modes |
| S6 | **Output Template** | Template Filling | Provide skeleton of expected output for model to complete | Structured data extraction, consistent formatting |
| S8 | **Meta-Prompt** | Auto-Prompting | Model generates or refines its own prompt | Self-optimising workflows; experimental; cost intensive |
| S9 | **Constitutional Framing** | Constitutional AI | Embed principles the model applies to self-critique | Alignment enforcement, safety-critical contexts |

*S7 (Self-Consistency Voting) relocated to R17 (Reasoning). S10 (Chain of Density) folded into K6 (Context Compression). Both are intentional gaps.*

---
```

- [ ] **Step 2: Add quick-reference table to patterns/KNOWLEDGE.md**

Add before the first `## K` stub line. The table is split by sub-band to match the section structure:

```markdown
## Quick Reference

### II-A — Retrieval

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| K1 | **Vanilla RAG** | Naive RAG | Retrieve relevant chunks at query time | Simple Q&A, static corpora, citations required |
| K2 | **Query Transformation** | HyDE, multi-query | Transform the raw query to retrieve better | Query/document mismatch; ambiguous queries |
| K3 | **GraphRAG** | Graph Retrieval | Index corpus as entity-relationship graph | Multi-hop relational queries; global synthesis |
| K4 | **RAPTOR** | Hierarchical RAG | Index corpus as recursive summary tree | Variable abstraction; hierarchical documents |
| K5 | **Adaptive RAG** | Self-RAG, Corrective RAG | Wrap retrieval in evaluate-and-control loop | Mixed query streams; factuality-critical |
| K13 | **Retrieval Bundle** | Agent Operating Context | Specify exact context bundle before writing retrieval code | Recurring workflows; rediscovery cost measurable |

### II-B — Context-Window Management

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| K6 | **Context Compression** | Summarisation | Summarise context that no longer fits (lossy) | Long-running agents; context overflow |
| K7 | **Context Pruning** | Selective Recall | Remove spent spans without summarising (lossless) | Spent tool outputs; finished sub-task context |
| K8 | **Working Memory** | Scratchpad | Explicit in-context space model writes to itself | Multi-step reasoning; intermediate state |
| K9 | **Long Context** | Context Stuffing | Hold whole working set in a large window | Working set fits; retrieval not justified |

### II-C — Memory

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| K10 | **Long-Term Memory** | Persistent Memory | External store of facts, retrieved by similarity | Cross-session fact storage; preferences |
| K11 | **Observational Memory** | Agent-Centric Memory | Append-only activity log; prefix-cache-friendly | Long-running agents with prefix caching |
| K12 | **Karpathy Memory** | Curated Memory | LLM curates dense structured notes | Read-frequency dominates; structure matters |

---
```

- [ ] **Step 3: Add quick-reference table to patterns/REASONING.md**

Add before the first `## R` stub line:

```markdown
## Quick Reference

| # | Pattern | Also Known As | LLM Calls | Best For |
|---|---|---|---|---|
| R1 | **Zero-Shot CoT** | "Think step by step" | 1 | Quick reasoning improvement; no examples |
| R2 | **Few-Shot CoT** | Exemplar CoT | 1 | Consistent reasoning format with examples |
| R3 | **Plan-and-Solve** | Explicit Planning | 2 | Well-defined multi-step workflows |
| R4 | **ReAct** | Reason+Act Loop | N per step | Exploratory; adaptive; unpredictable paths |
| R5 | **ReWOO** | Reasoning Without Observation | 2 total | Independent tool calls; 5× cheaper than R4 |
| R6 | **Self-Ask** | Decomposition | 1 + N follow-ups | Multi-hop factual questions |
| R7 | **Reflexion** | Verbal Reinforcement | N × retries | Clear pass/fail criteria; retries acceptable |
| R8 | **Self-Refine** | Generate-Critique-Refine | N iterations | General quality improvement; no separate judge |
| R9 | **Tree of Thoughts** | ToT | N (branching) | Hard open-ended; path unknown |
| R10 | **LATS** | Language Agent Tree Search | N (tree search) | Highest quality; highest cost |
| R11 | **Buffer of Thoughts** | BoT | 1 + template | 12% cost of ToT; reusable templates |
| R12 | **Skeleton-of-Thought** | SoT | 1 + N parallel | Parallel generation; latency reduction |
| R13 | **CodeAct** | Executable Code Actions | N (with execution) | Multi-tool; ~20pp accuracy gain over JSON |
| R14 | **Program of Thoughts** | PoT | 1 + execution | Numerical/mathematical tasks |
| R16 | **Talker-Reasoner** | System 1/System 2 | Dual async | Real-time + deliberative combined |
| R17 | **Self-Consistency** | Majority Voting | N samples | Factual tasks; sample and vote |
| R18 | **Graph of Thoughts** | GoT | N (DAG) | Non-linear reasoning; merging thought branches |
| R19 | **Step-Back Prompting** | Abstraction Prompting | 2 | Abstract to principle before answering |
| R20 | **Chain of Verification** | CoVe | 1 + N verifications | Reduce hallucination; verify each claim |

---
```

- [ ] **Step 4: Add quick-reference table and scaffold dimensions to patterns/ORCHESTRATION.md**

Add before the first `## O` stub line:

```markdown
## Quick Reference

### IV-A — Workflow Patterns

| # | Pattern | Also Known As | Intent | Complexity |
|---|---|---|---|---|
| O1 | **Single Agent** | Autonomous Agent | One LLM + tools + system prompt | Low |
| O2 | **Prompt Chaining** | Pipeline | Output of one call feeds the next in fixed order | Low |
| O3 | **Routing** | Classifier-Dispatcher | Classify input → specialist handler | Medium |
| O4 | **Parallelization** | Fan-out Fan-in | Simultaneous independent LLM calls | Medium |

### IV-B — Agentic Patterns

| # | Pattern | Also Known As | Intent | Complexity |
|---|---|---|---|---|
| O5 | **Evaluator-Optimizer** | Generator-Critic | Separate generator and judge; iterative improvement | Medium |
| O6 | **Orchestrator-Workers** | Hub-and-Spoke | Central LLM dynamically delegates to workers | High |
| O7 | **Supervisor Hierarchy** | Hierarchical Agents | Multi-level tree of orchestrators | High |
| O8 | **Loop Agent** | Agentic Loop | Sequence repeats until termination condition | Medium |
| O9 | **Multi-Agent Reflection** | Ensemble Critique | Multiple agents independently critique one output | High |
| O10 | **Swarm** | Peer-to-Peer Agents | No central coordinator; emergent coordination | Very High |

### IV-C — Specialised Coordination

| # | Pattern | Also Known As | Intent | Complexity |
|---|---|---|---|---|
| O11 | **Blackboard** | Shared Workspace | Central shared memory; agents post and consume | High |
| O12 | **Debate and Deliberation** | Devil's Advocate | Agents argue opposing positions before synthesis | High |
| O13 | **Negotiation** | Multi-Party Consensus | Agents with conflicting objectives negotiate | Very High |
| O14 | **SIE** | Single Information Environment | Agents own specific datasets; coordinator routes | Medium |
| O15 | **Agent Handoff** | Context Transfer | Structured state transfer mid-task | Medium |
| O16 | **Hybrid Control Flow** | Primitive Stack | Stacked loop primitives; most real agents | Varies |
| O17 | **Agent Isolation** | Clean Context | Fresh context per sub-task — required companion to O6 | Low overhead |
| O18 | **Cache-Warmed Worker Pool** | Primed Agent Pool | Shared prefix cached before worker fan-out | Low overhead |

---

## Scaffold Architecture Dimensions

*From empirical study of 13 coding agents (arXiv 2604.03515).*

**Five stackable loop primitives:**
1. ReAct loop
2. Generate-test-repair
3. Plan-execute
4. Multi-attempt retry
5. Tree search (MCTS)

Most production agents (11/13 studied) use O16 — multiple primitives stacked, not a single pattern.

**The major architectural fault line:**

- **LLM-as-navigator** (8/13 agents): general tools; LLM decides navigation; simpler but less precise
- **Scaffold-understands-code** (5/13 agents): repository maps, AST indexing, knowledge graphs; more powerful but complex

**Active research frontier (no consensus):** context compaction strategy, state representation format, safety mechanisms for interactive agents.

---
```

- [ ] **Step 5: Add quick-reference table to patterns/RELIABILITY.md**

Add before the first `## V` stub line:

```markdown
## Quick Reference

### V-A — Safety and Security

| # | Pattern | Also Known As | Intent |
|---|---|---|---|
| V1 | **Human-in-the-Loop** | Approval Gate | Block on irreversible, novel, or high-blast-radius actions |
| V2 | **Human-on-the-Loop** | Monitoring Mode | Agent acts autonomously; human monitors and can interrupt |
| V3 | **Rule of Two** | Lethal Trifecta Guard | Flag agents with private data + untrusted content + external comms |
| V4 | **Dual LLM** | Privilege Separation | Quarantined LLM for untrusted data; privileged LLM for actions |
| V5 | **Guardrail Layering** | Defense in Depth | Safety checks at input, pre-call, post-call, and output |
| V6 | **Prompt Injection Shield** | Input Sanitisation | Structural and positional defences against injection |
| V7 | **AgentSpec** | Policy as Code | Declarative, out-of-prompt, deterministic policy enforcement |
| V8 | **Tool Sandboxing** | Isolated Execution | Confine LLM-generated code to restricted environment |

### V-B — Operational Reliability

| # | Pattern | Also Known As | Intent |
|---|---|---|---|
| V9 | **Bounded Execution** | Circuit Breaker | Hard caps on steps, cost, wall-time — required for every loop |
| V10 | **Checkpointing** | State Snapshot | Replayable agent state; recovery without restart |
| V11 | **Error Compaction** | Error Summarisation | Compress errors into compact structured signals |
| V12 | **Stateless Reducer** | Pure Agent | Deterministic, replayable summary of accumulated state |
| V13 | **Tool Budget** | Schema Budget | Limit active schema tokens — every schema token costs n² attention |
| V19 | **Fallback** | Graceful Degradation | Cheaper degraded path for every primary-path failure mode |
| V20 | **Schema Validation** | Structured Output | Validate output against schema; re-prompt on failure |

### V-C — Observability and Evaluation

| # | Pattern | Also Known As | Intent |
|---|---|---|---|
| V14 | **Trajectory Logging** | Agent Tracing | OTel-compatible trace of every call, action, observation |
| V15 | **LLM-as-Judge** | AI Evaluator | Second model evaluates quality against defined rubrics |
| V16 | **Offline Eval** | Regression Testing | Batch evaluation against held-out cases before deployment |
| V17 | **Online Eval** | Production Monitoring | Real-time quality metrics in production |
| V18 | **Agent Simulation** | Sandbox Testing | Simulated environment for pre-deployment stress testing |

---
```

- [ ] **Step 6: Add quick-reference table to patterns/INTEGRATION.md**

Add before the first `## I` stub line:

```markdown
## Quick Reference

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| I1 | **Direct API** | Deterministic Call | Synchronous HTTP; no LLM reasoning | Sub-10ms ops; consistency-critical |
| I2 | **Function/Tool Call** | Schema-Wrapped API | LLM selects and invokes typed function | 1–5 tools; app-specific routing |
| I3 | **MCP Server** | Model Context Protocol | Standardised tool discovery; credential isolation | 5+ tools shared across agents |
| I4 | **CLI Invocation** | Shell Tool | Agent uses existing CLI directly | Tools with existing CLIs (git, docker, gh) |
| I5 | **Agent Card** | Agent Manifest | Self-describing JSON for agent discovery | Multi-agent; A2A interoperability |
| I6 | **A2A Delegation** | Agent-to-Agent | Structured cross-agent task delegation | Multi-vendor agent collaboration |

---
```

- [ ] **Step 7: Add quick-reference table and cognitive science to patterns/HUMANIZERS.md**

Add before the first `## H` stub line. Two blocks:

```markdown
## Quick Reference

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| H1 | **Identity Persistence** | Genesis State | Stable invariant self at position 0 every session | Any multi-session agent |
| H2 | **Episodic Self-Improvement** | Cross-Session Reflexion | Persist verbal self-critiques; improve without weight updates | Recurring task types |
| H3 | **Entropy-Driven Curiosity** | Deadlock Break | Increase temperature or inject stimuli on stagnation | Creative agents; stuck reasoning loops |
| H4 | **Procedural Skill Accumulation** | Skill Library | Distil successful trajectories into reusable skills | Agents with recurring task types |
| H5 | **Constitutional Self-Alignment** | Principle Evolution | Operating principles evolve through experience with human checkpoints | Long-running agents; governed alignment |
| H6 | **Continuous Inner Monologue** | MIRROR | Background reasoning separate from user-facing responses | Persistent assistants; monitoring agents |
| H7 | **Adaptive Persona** | User-Calibrated Style | Communication adapts to observed user preferences | Personal assistants; multi-user systems |
| H8 | **Meta-Agent Self-Modification** | Self-Improving Agent | Agent modifies own operational parameters within governed allowlist | Large-scale production; abundant eval data |
| H9 | **Observational Identity** | Self-Knowledge Model | Explicit model of own capabilities and knowledge state | Multi-session; capability routing |
| H10 | **Relational Memory** | User Model Persistence | Persistent user relationship record with GDPR erasure | Personal assistants; coaching |

---

## Cognitive Science Grounding

Humanizer patterns map to classical cognitive science theories — the convergence suggests the patterns capture something real about how intelligence works over time.

| Pattern | Cognitive Theory | Source |
|---|---|---|
| O11 Blackboard | Global Workspace Theory (Baars) | Explicit in Theater of Mind paper |
| O10 Swarm | Society of Mind (Minsky) | Multi-specialised agents |
| R16 Talker-Reasoner | Dual-Process Theory (Kahneman) | Direct mapping: System 1/2 |
| K10 Long-Term Memory | Tulving / Baddeley memory taxonomy | Episodic, semantic, procedural variants |
| K11 Observational Memory | Extended Mind Thesis (Clark) | External tool as cognitive extension |
| H1 Identity Persistence | Autobiographical memory (Tulving 1985) | Genesis State in Theater of Mind |
| H2 Episodic Self-Improvement | Episodic memory consolidation | Reflexion extended cross-session |
| H3 Entropy-Driven Curiosity | Optimal Arousal / Noradrenergic system | Theater of Mind — entropy monitoring |
| H5 Constitutional Self-Alignment | Moral development (Kohlberg) | Constitutional AI extended to inference |
| H6 Inner Monologue | Vygotskian inner speech | MIRROR / Thinker architecture |
| H7 Adaptive Persona | Theory of Mind (Premack & Woodruff) | User model as cognitive representation |
| H10 Relational Memory | Parasocial relationship theory | HCI research; Skjuve et al. 2021 |

---
```

- [ ] **Step 8: Build and verify tables appear in book.md**

```bash
python3 build_book.py
grep "Quick Reference" book.md | wc -l
```

Expected: 7 (one per section).

```bash
grep "Cognitive Science" book.md
```

Expected: one match in the Humanizer section.

- [ ] **Step 9: Commit**

```bash
git add patterns/SIGNAL.md patterns/KNOWLEDGE.md patterns/REASONING.md \
        patterns/ORCHESTRATION.md patterns/RELIABILITY.md \
        patterns/INTEGRATION.md patterns/HUMANIZERS.md
git commit -m "phase 2: add quick-reference tables and supplementary content to section intros"
```

---

### Task 9: Write the LLM primer in CHAPTER-0.md

**Files:**
- Modify: `CHAPTER-0.md`

- [ ] **Step 1: Add section 0.0 before the existing `## 0.1 — The Inference Primitives` heading**

Insert the following block immediately before `## 0.1 — The Inference Primitives (Mechanisms 1–7)`:

```markdown
## 0.0 — How a Language Model Computes

The mechanisms in this chapter are precise. Before the formalism, here is the conceptual model they build on.

**Tokens.** A language model does not read words. It reads *tokens* — byte-pair encoded substrings that tile any input text. One token is roughly three-quarters of a word in English, though the ratio varies by content type. "context" is one token; "contextualisation" may be three. Every count in this chapter — context window size, KV cache size, input cost — is a token count, not a word count. When a model's context window is 200,000 tokens, that is roughly 150,000 words.

**The context window.** At inference time, the model sees a fixed sequence of tokens: your system prompt, any prior turns, your current message, any retrieved documents. This sequence is the *context*. Every token has a position, and position matters — the model has learned structural priors from training (instructions near the start, user query near the end). The model is stateless between calls: it has no memory of previous requests. The context window is the totality of what it knows for one call.

**A forward pass.** When you send a prompt, the model runs a single forward pass over all input tokens simultaneously. For each layer and each attention head, it computes how much every token should attend to every other token. The final layer's output is a probability distribution over the vocabulary; one token is sampled and appended to the sequence. Then the process repeats: another forward pass, another token. Generation is a loop of single-token predictions, each conditioned on everything before it. This loop is what the patterns in this catalog are engineering around.

**The KV cache.** Running a full forward pass over the growing sequence on every step would be prohibitively slow — by step 500, you would recompute attention over 500 tokens 500 times. Each layer avoids this by caching the *key* and *value* vectors it computed for prior tokens. On the next step, only the new token needs fresh computation; the cached K and V vectors for all prior tokens are reused. This is the KV cache. It grows monotonically — one entry per layer per token, never removed or reordered — which is why its structure appears in the cost reasoning for almost every pattern in this catalog.

**The n² intuition.** During the initial *prefill* — processing all input tokens before generation begins — the model computes attention between every pair of tokens. A prompt twice as long has four times as many pairs: prefill cost scales with the square of sequence length. A 2,000-token prompt costs four times as much to prefill as a 1,000-token prompt. A 4,000-token prompt costs sixteen times as much. Engineers who model token costs as linear are systematically underestimating the cost of long contexts. This quadratic relationship is the mechanical basis for the entire Knowledge category and for the subagent isolation imperative in Orchestration patterns.

---
```

- [ ] **Step 2: Build and verify primer appears**

```bash
python3 build_book.py
grep "0.0 — How a Language Model" book.md
```

Expected: one match.

```bash
grep "byte-pair" book.md
```

Expected: one match confirming the primer content is present.

- [ ] **Step 3: Commit**

```bash
git add CHAPTER-0.md
git commit -m "phase 2: add 0.0 LLM primer to mechanisms chapter"
```

---

## Phase 3 — LaTeX Pattern Card Styling

### Task 10: Update header.tex with stripe definition

**Files:**
- Modify: `header.tex`

- [ ] **Step 1: Replace header.tex content**

```latex
\usepackage{fancyhdr}
\usepackage{eso-pic}
\usepackage{tikz}
\usepackage{xcolor}

% Pattern card stripe colours
\definecolor{patternbg}{HTML}{FDFAEC}
\definecolor{patternsep}{HTML}{333333}

% Stripe state — set per pattern, cleared at section end
\newcommand{\currentpatternname}{}
\newcommand{\setpatternname}[1]{\renewcommand{\currentpatternname}{#1}}
\newcommand{\clearpatternname}{\renewcommand{\currentpatternname}{}}

% Draw pale yellow left stripe + dark hairline + rotated pattern name on every page
\AddToShipoutPictureBG{%
  \ifx\currentpatternname\empty\else
    \begin{tikzpicture}[remember picture, overlay]
      \fill[patternbg]
        ([xshift=-1.8cm]current page text area.north west)
        rectangle
        ([xshift=-0.3cm]current page text area.south west);
      \draw[patternsep, line width=0.4pt]
        ([xshift=-0.3cm]current page text area.north west)
        --
        ([xshift=-0.3cm]current page text area.south west);
      \node[rotate=90, anchor=center, text=patternsep,
            font=\small\sffamily]
        at ([xshift=-1.05cm]current page.center)
        {\currentpatternname};
    \end{tikzpicture}
  \fi
}

% Running headers
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\chaptermark}[1]{\markboth{#1}{}}
\renewcommand{\sectionmark}[1]{\markright{#1}}
\fancyhead[L]{\small\itshape\leftmark}
\fancyhead[R]{\small\itshape\rightmark}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\fancypagestyle{plain}{%
  \fancyhf{}%
  \fancyfoot[C]{\small\thepage}%
  \renewcommand{\headrulewidth}{0pt}%
}
```

- [ ] **Step 2: Test the header compiles (no patterns injected yet)**

```bash
python3 build_book.py
echo "Exit: $?"
```

Expected: exit 0. No stripe visible yet — `\currentpatternname` is always empty at this point.

- [ ] **Step 3: Commit**

```bash
git add header.tex
git commit -m "phase 3: add eso-pic/tikz stripe definition to header.tex"
```

---

### Task 11: Inject pattern name macros in build_book.py

**Files:**
- Modify: `build_book.py`

- [ ] **Step 1: Add helper to extract short pattern label**

Add this function after `shift_headings()`:

```python
def pattern_label(path: Path) -> str:
    """Return 'K7 — Context Pruning' from the first H1 of a pattern file."""
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    title = first_line.lstrip("# ").strip()
    # Title is e.g. "K7 Context Pruning" or "K7 — Context Pruning"
    # Normalise to "K7 — Name" if not already
    import re
    m = re.match(r"([A-Z]\d+)\s+(?:—\s*)?(.+)", title)
    if m:
        return f"{m.group(1)} — {m.group(2)}"
    return title
```

- [ ] **Step 2: Update the pattern loop to inject \setpatternname and \clearpatternname**

Replace the pattern loop inside `assemble()` with the complete final version (includes decision companion injection from Task 7):

```python
        for prefix in standalones:
            path = resolve(prefix)
            body = read(path)
            first_line = body.splitlines()[0]
            title = first_line.lstrip("# ").strip()
            label = pattern_label(path)
            parts.append(PAGE_BREAK)
            # Stripe: set for this pattern
            parts.append(f"\n```{{=latex}}\n\\setpatternname{{{label}}}\n```\n")
            parts.append(f"## {title}\n")
            rest = strip_first_h1(body)
            parts.append(shift_headings(rest, by=2))
            parts.append("\n")

        # Stripe: clear before decision companion (decision pages have no stripe)
        parts.append("\n```{=latex}\n\\clearpatternname\n```\n")

        # Decision companion file — appended after section's final pattern
        decision_file = PATTERNS / intro_file.replace(".md", "-DECISION.md")
        if decision_file.exists():
            parts.append(PAGE_BREAK)
            parts.append(strip_first_h1(read(decision_file)))
            parts.append("\n")
```

This supersedes the loop written in Task 7 — it combines both the decision injection and the stripe injection. If Task 7 has already been applied, replace the loop entirely with this version.

- [ ] **Step 3: Build and verify**

```bash
python3 build_book.py
grep "setpatternname" book.md | head -5
```

Expected: 5 lines showing `\setpatternname{S1 — Zero-Shot}` etc.

```bash
grep "clearpatternname" book.md | wc -l
```

Expected: 7 (one clear per section).

- [ ] **Step 4: Open the PDF and visually confirm the stripe**

Open `GO4.pdf`. Navigate to any individual pattern page (e.g. page ~30 for S1). Expected:
- Pale yellow stripe in the left margin
- Thin dark grey hairline on the right edge of the stripe
- Rotated pattern name (small sans-serif) centred vertically in the stripe
- Main text area unchanged — no overlap with the stripe

Navigate to a section intro page (e.g. the Category I — Signal Patterns opening). Expected: no stripe visible.

- [ ] **Step 5: Commit**

```bash
git add build_book.py
git commit -m "phase 3: inject setpatternname/clearpatternname for pattern card stripe"
```

---

### Task 12: Final build and verify complete PDF

- [ ] **Step 1: Full clean build**

```bash
python3 build_book.py
```

Expected: exit 0, PDF produced without LaTeX errors.

- [ ] **Step 2: Verify book structure**

```bash
grep "^# " book.md
```

Expected output (in order):
```
# Introduction
# The Pattern Catalog
# Category I — Signal Patterns
# Category II — Knowledge Patterns
# Category III — Reasoning Patterns
# Category IV — Orchestration Patterns
# Category V — Reliability Patterns
# Category VI — Integration Patterns
# Category VII — Humanizer Patterns
# The Mechanical Foundation
# Appendix A — Conflicts
# Appendix B — References
# Appendix C — Anti-Patterns and Composition Examples
```

- [ ] **Step 3: Verify key content blocks**

```bash
grep -c "setpatternname" book.md    # expect 94
grep -c "clearpatternname" book.md  # expect 7
grep -c "Quick Reference" book.md   # expect 7
grep "Pattern Selection" book.md    # expect 7 lines
grep "0.0 — How a Language" book.md # expect 1
grep "homage" book.md               # expect 1 (new intro)
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "phase 3: complete — pattern card stripes, all content restructured"
```
