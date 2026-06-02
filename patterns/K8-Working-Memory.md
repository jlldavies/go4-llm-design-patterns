# K8 — Working Memory / Scratchpad

> Give the model an explicit, designated region of the context to write intermediate results, plans, and conclusions into, so working state persists across reasoning steps instead of being regenerated or lost.

**Also Known As:** Scratchpad, Cognitive Scratchpad, Agent Notepad, In-Context Working Memory

**Classification:** Category II — Knowledge · Band II-B Context-window management · an *additive* in-context structure — the inverse of K6 and K7's subtractive moves.

---

## Intent

Externalise the model's working state into a persistent, inspectable region of the context, so intermediate results survive from one step to the next within a task.

## Motivation

Within a single context, the model has no working memory other than the text already present. This follows directly from two mechanical facts: (1) the model's weights do not change within a session (mechanism 10) — no information is stored by the forward pass itself; (2) the KV cache records all token computations within the current context but does not persist across API calls (mechanism 3). Anything an intermediate step established is available only if it is still present as text in the token sequence. An intermediate result computed at step 2 is available at step 5 only if it is still there as text. Without a designated place to put such results, two things go wrong:

- **Regeneration.** The model re-derives the same sub-result repeatedly — burning tokens, and risking that the re-derivations disagree.
- **Loss.** Later steps simply proceed without a fact an earlier step had established.

The fix is structural and simple: designate a region of the context — a scratchpad — and have the model write its intermediate state there. Plans, partial results, current hypotheses, a running task list. Each later step reads its own prior conclusions instead of recomputing them. The scratchpad makes working state **persistent** (it survives across steps), **inspectable** (a human or another component can read it), and **singular** (one authoritative copy, not re-derived variants).

This is the inverse of K6 and K7, which *remove* content; K8 *adds* a structure. It is also distinct from the memory patterns K10, K11, and K12, which persist *across or through* sessions — the scratchpad lives and dies within one context. Note that the ReAct reasoning loop is a scratchpad in disguise: its Thought / Action / Observation trace *is* working memory. K8 is the pattern that trace is one instance of.

## Applicability

Use Working Memory when:

- a task has multiple steps that build on each other;
- the task involves planning and the plan needs a stable home;
- the agent runs a ReAct or similar loop where observations accumulate;
- losing an intermediate result would cause an error.

It is unnecessary for single-shot tasks.

## Decision Criteria

K8 is right when a task has multiple steps that build on each other's results and that state needs to persist explicitly within the context.

**1. Count dependent steps.** How many steps in a typical task build on results from earlier steps?
- 1–2 steps: no scratchpad needed — prompt ordering covers it.
- 3–5 dependent steps: K8 starts to pay off.
- 5+ dependent steps: K8 is essentially mandatory.

**2. Recomputation tax.** Without a scratchpad, intermediate results are either regenerated (token cost, inconsistency risk) or lost (errors). Estimate how often later steps need earlier outputs — if frequently, K8 pays for itself by avoiding the regeneration tax.

**3. State shape — typed or free text.** Is the working state structured (a plan, a task list, a partial calculation)? Use a typed scratchpad with an explicit schema. Freeform reasoning? A delimited free-text scratchpad is fine.

**4. Scratchpad growth.** The pad accumulates. Estimate its peak size against the window. If it grows large, pair with **K6** (compress) and **K7** (prune retired entries). The reason: each scratchpad token is an additional K vector in the attention softmax (mechanism 2). As the scratchpad grows, two costs compound: (a) per-step compute rises with n² and (b) older scratchpad entries migrate toward mid-context positions that the model's learned projection matrices under-attend (mechanism 4), causing the model to ignore conclusions it wrote earlier.

**5. Single-agent vs handoff.** If one agent runs all steps in one context, the scratchpad is in-context (K8). If multiple agents share state, the scratchpad must be externalised — that crosses into **K10 / K12** territory.

**Quick test — K8 is the right pattern when:**

- the task has 3+ steps where later steps need earlier results, *and*
- losing or recomputing intermediate state would cause errors or waste tokens, *and*
- one agent runs all steps in one context window, *and*
- the scratchpad can be kept bounded (paired with K6 / K7 if it grows).

If steps are independent, K8 is overhead. If the task is multi-agent or cross-session, you need persistent memory — **K10 / K11 / K12**. If the task is single-shot, no working memory is needed.

## Structure

```
  System: [task]

  ┌─ SCRATCHPAD ───────────────────────┐
  │ Plan:           …                  │   ◀── model reads at the start of each step,
  │ Step 1 result:  …                  │       writes updated state at the end
  │ Step 2 result:  …                  │
  │ Open questions: …                  │
  └────────────────────────────────────┘

  [ current step ]
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Scratchpad** | the delimited region holding working state | — | be undelimited — if it blends into prose the model treats it as text, not state. |
| **Model** | reading the pad, reasoning, writing it back | pad + step → pad + output | recompute a result the pad already holds, or skip writing its conclusions back. |
| **Scratchpad Manager** *(optional)* | formatting, bounding, persisting the pad | pad → bounded pad | let the pad grow unbounded — apply K6/K7 to it. |

## Collaborations

At each step the model reads the current scratchpad, reasons using the state it finds there, writes its updated conclusions back into the scratchpad, and proceeds. The scratchpad is therefore the single channel through which one step's output reaches the next. When it grows large, the Scratchpad Manager (or K6/K7) keeps it bounded.

## Consequences

**Benefits**
- No recomputation of intermediate results.
- Coherent multi-step behaviour — later steps build on recorded conclusions.
- The state is inspectable and debuggable, and forms a natural audit trail.

**Costs**
- The scratchpad consumes window space, and grows as the task runs.
- It must be managed — K6 and K7 applied to the scratchpad itself.

**Risks and failure modes**
- A stale or wrong scratchpad entry misleads every later step, because the scratchpad is trusted by construction.
- Unbounded scratchpad growth eventually crowds the window.

## Implementation Notes

- Delimit the scratchpad clearly (tags, a fenced block) so the model treats it as *state*, not prose. Mechanically, delimiters work because they create distinctive token patterns in the sequence. The model's attention heads learn to key off structural markers like tags or fenced blocks — they function as position-invariant indexing signals within the learned bilinear attention metric (mechanism 1), helping the model identify the scratchpad region regardless of where it sits in the sequence.
- Instruct an explicit protocol: read at the start of each step, write at the end.
- Cap its size; apply K6 (compress) or K7 (prune) when it grows.
- For structured tasks a *typed* scratchpad — an explicit task list, a plan object — outperforms free text.
- The scratchpad is the natural thing to snapshot for V-category Checkpointing.

## Implementation Sketch

> `LLM` = configured session; `code` = wiring.

**Composition:** A *protocol* around the model's session — *read at start, write at end* — applied per step. The scratchpad itself is bounded by **K6/K7** as it grows, and is the natural unit to snapshot for **V10** Checkpointing.

**The chain (per step):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Render the current scratchpad in its delimited block | `code` | |
| 2 | Compose prompt: scratchpad + current step instruction | `code` | S6 output template |
| 3 | LLM: read the pad, carry out the step, return *updated scratchpad + step output* | `LLM` | Step session |
| 4 | Parse the updated scratchpad from the response; persist it | `code` | |
| 5 | If the scratchpad exceeds its size budget: compress (K6) or prune (K7) | `code` | K6, K7 |

**Skeleton:**

```
run_with_scratchpad(task):
    pad = Scratchpad(plan=task.plan, done=[], open=task.questions)
    for step in task.steps:
        response = Step(pad.render(), step)             # LLM
        pad = pad.update_from(response)                  # code
        if pad.tokens > LIMIT: pad = pad.compress()      # K6 applied to the pad
    return pad.final_answer()
```

**The LLM sessions:**

| Session | Model | Setup — loaded once | Per-call prompt wraps |
|---|---|---|---|
| **Step** | the task's main generalist | role for the task; the **scratchpad protocol**: *"Read the scratchpad below before reasoning. Return the UPDATED scratchpad followed by your output for this step."*; delimiter convention (e.g. `[SCRATCHPAD] … [/SCRATCHPAD]`) | the rendered scratchpad + the current step instruction |

**Specialist-model note.** None — the pattern is a *protocol*, not a special model. Any model that will follow the read-then-update-pad instruction will do. A *typed* scratchpad (a structured task object with an explicit schema) outperforms free text by collapsing the parsing failure surface.

## Open-Source Implementations

- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — the graph `State` object is an explicit, typed working memory threaded between steps; the canonical modern scratchpad.
- **Agent Memory Techniques** — [`github.com/NirDiamant/Agent_Memory_Techniques`](https://github.com/NirDiamant/Agent_Memory_Techniques) — runnable notebooks covering working-memory and scratchpad patterns alongside the long-term variants.

## Known Uses

- ReAct-based agents — the Thought/Action/Observation reasoning trace.
- Planning behaviours in Claude and ChatGPT — explicit plan/todo state.
- Agent frameworks that maintain a visible "plan" or "todo" structure.
- "Scratchpad" prompting, present since the earliest chain-of-thought work.

## Related Patterns

- **Distinct from** K6 Context Compression and K7 Context Pruning — additive structure versus subtractive curation; but K6/K7 are applied *to* the scratchpad when it grows.
- **Distinct from** K10 Long-Term Memory, K11 Observational Memory, and K12 Karpathy Memory — in-context working state versus the three forms of persistence: cross-session flat facts (K10), in-session raw log (K11), and LLM-curated notes (K12).
- **Underlies** R4 ReAct and R3 Plan-and-Solve — their traces and plans are scratchpads.
- **Feeds** V10 Checkpointing — the scratchpad is the state worth snapshotting.

## Sources

- Lilian Weng (2023) — short-term memory via in-context state.
- "Empowering Working Memory for LLM Agents" (arXiv).
