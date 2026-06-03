# V11 — Error Compaction

> Replace raw errors in the agent's working context with compact, dedup-aware summaries that preserve the diagnostic signal at a fraction of the token cost.

**Also Known As:** Compact Errors (12-Factor Agents Factor 9), Error Context Management, Failure Summarisation, Error Digest, Stack-Trace Compaction.

**Classification:** Category V — Reliability · Band V-B Operational Reliability · an *in-context* curation pattern specific to the error stream; the error-domain counterpart of K6 Context Compression.

---

## Intent

Keep the cumulative weight of errors, exceptions, and tool failures inside the agent's context window small enough that the agent retains the diagnostic signal but does not lose attention or budget to repeated raw tracebacks.

## Motivation

Agents that loop — code executors, tool callers, retry-driven workflows — generate errors as a normal part of operation. A capable LLM can read an exception, infer the cause, and adjust on the next turn; that self-correcting move is a major reason agentic loops work at all. But raw errors are *expensive*: a Python traceback is 200–500 tokens, an HTTP error body can be 1–10 KB, and a long debugging session that re-appends the same kind of failure for ten turns will spend a quarter of its window on error text alone. The signal-to-noise ratio collapses.

The naive fix — drop errors entirely — loses the self-healing behaviour the agent depends on. The naive opposite — append every raw error verbatim — fills the window with noise and degrades model attention to the rest of the task. Neither extreme is right. The pattern is to *transform* each error on arrival: extract the type, the root cause, the location, and any prior-attempt context, then write that as a compact line and replace the raw form in the active context. The agent still sees what failed and why; the tokens go away. Deduplication is the second half: when the same error type recurs with the same root cause, increment a counter rather than re-stating the digest, and escalate (to **V9 Bounded Execution** or **V1 Human-in-the-Loop**) once a threshold is hit.

The mechanistic account is twofold: (1) as error tokens accumulate toward the middle of a long context, they occupy positions where the learned attention weights assign the weakest recall probability — the u-shaped attention distribution documented in Liu et al. 2024 (mechanism 4) means error text in the middle is both abundant and under-attended; (2) repeated identical error spans activate strong induction-head-style completion patterns that make the model more likely to continue the error pattern rather than reason about it.

This is structurally adjacent to **K6 Context Compression** but not the same pattern. K6 compresses *general history* — turns, tool outputs, retrieved context — on a window-pressure trigger. V11 compresses the *error stream specifically*, on every error event, with dedup-and-count semantics K6 does not have, and with an escalation hook into V9 / V1 that K6 does not have either. K6 asks *"is the window too full?"*; V11 asks *"did this just fail, and have I seen this failure before?"*.

## Applicability

Use V11 when:

- the agent runs a loop with tool calls, code execution, or external APIs that fail with non-trivial frequency;
- failures produce verbose tracebacks, HTTP error bodies, or compiler output that consume meaningful context;
- the same class of error can recur across turns and would otherwise be re-appended each time;
- you need the agent to keep the self-healing behaviour (read the error, try again) without window inflation.

Do not use when:

- failures are rare and short — append the raw error and move on; the compaction call costs more than it saves;
- the agent must reason from *exact* error text (compiler error rows, security-relevant logs) — there, fall back to **K7 Context Pruning** of *other* spans instead;
- audit detail must survive — V11 is for the *active context*; the full raw form belongs in **V14 Trajectory Logging**, never in lieu of it.

## Decision Criteria

V11 is right when the agent loops, fails routinely, and would otherwise re-spend its context on duplicated error text.

**1. Measure error tonnage.** Across a representative session, what fraction of context tokens are error text? If > 10% the pattern pays. If > 25% it is mandatory. If < 5% the loop is too clean to bother — the overhead is not justified.

**2. Measure recurrence.** Across the same session, how often does the *same* error type recur with the same root cause? If a single class repeats $\geq$ 3 times the deduplicator alone earns the pattern its keep; without recurrence, the compaction-on-arrival half still pays as long as raw errors are large.

**3. Pick the compactor mechanism.** A code-only extractor (regex on exception type + message + top frame) is enough for clean, structured exceptions and costs nothing. An LLM compactor is needed when the error is unstructured — long compiler output, stack-of-stacks across a runtime, prose error bodies — and a one-line digest requires judgement. Default to code; reach for an LLM only when code cannot.

**4. Set the escalation thresholds.** Decide the consecutive-same-error limit (the 12-Factor reference suggests ~3 attempts of a single tool) and the total-error budget per run. Both must be set, both must escalate — to **V9** for a hard cap, to **V1** for human review. Without thresholds, dedup just hides the loop; it does not break it.

**5. Decide what survives outside the window.** Every raw error compacted away from the active context must be written to **V14 Trajectory Logging** *first*. The audit copy and the in-context copy are different artefacts and the audit copy is not optional. If V14 is not in place, V11 is the wrong pattern to install next — install V14, then V11.

**Quick test — V11 is the right pattern when:**

- the agent loops with tool / code / API calls, *and*
- raw errors materially consume the context window (> 10%), *and*
- the same error class recurs often enough that dedup pays, *and*
- a Trajectory Log (V14) exists so the full raw error survives outside the active context.

If errors are rare or trivial, raw-append suffices. If errors are large but *unique* every time, the dedup half does nothing — the compactor-on-arrival half still pays, but tune the threshold knobs down. If the agent cannot loop at all (V9 caps it at one shot), V11 has nothing to do.

## Structure

```
                            ┌─────────── V14 Trajectory Logging
                            │            (raw error always written here)
   tool / code call ── err ─┤
                            │
                            ▼
                    ┌──── Error Compactor ─────┐
                    │ type · root cause · loc  │
                    │ → 1-line digest          │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                       ┌── Error History ──┐
                       │ recent digests +  │
                       │ counts per class  │
                       └─────────┬─────────┘
                                 │
                  same class? ───┴── new class?
                  count++              append digest
                                 │
                                 ▼
                   threshold exceeded? ──yes──▶ Escalator
                                 │              ├─ V9 Bounded Execution: halt
                                 no             └─ V1 Human-in-the-Loop: review
                                 │
                                 ▼
                       compact error stream
                       returned to agent context
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Error Compactor** | turning a raw error into one diagnostic line | raw exception / traceback / response body $\to$ `[type] at [loc]: [root cause]` digest | drop the root cause to save tokens — a digest without cause is no longer self-healing fuel. |
| **Error History** | the recent compact error stream + a per-class counter | digest $\to$ updated stream (append-or-increment) | re-emit a digest that is already present; the counter is the de-duplicator. |
| **Deduplicator** | classifying a new digest as same-as-previous or new | digest + history $\to$ match / no-match | classify on raw text — match on `(type, location, root-cause-key)`, not on the full string, or near-duplicates leak through. |
| **Escalator** | acting on threshold breach | counts + thresholds $\to$ halt / human signal | absorb the failure silently; threshold breach is the *whole* point of counting. |
| **Audit Sink** *(V14)* | persisting the raw error outside the context | raw error $\to$ trace span | be skipped — the compacted view in context is *additional to*, never *instead of*, the audit copy. |

Five narrow responsibilities. The Compactor only summarises; the History only stores; the Deduplicator only matches; the Escalator only escalates; the Audit Sink only persists. The pattern's reliability comes from that separation — particularly between the Deduplicator (decides "is this new?") and the Escalator (decides "have we seen too many?"). Conflating them produces the most common failure: an agent that quietly retries forever because a counter increments but nothing acts on it.

## Collaborations

A tool call, code execution, or API request fails. The raw error is handed simultaneously to the **Audit Sink** (V14: full fidelity, off the critical context path) and to the **Error Compactor**. The Compactor extracts type, location, root cause, and any prior-attempt context, and emits a one-line digest. The **Deduplicator** compares the digest against the **Error History**: if it matches an existing class on `(type, location, root-cause-key)`, the counter is incremented and no new line is added to the agent's context; if it does not, the digest is appended. The **Escalator** reads the counters: if any class has hit its consecutive-same-error threshold, or if the total error count has hit the run budget, control transfers to **V9** (halt) or **V1** (human review). Otherwise the compact error stream — digests plus counts — is what the agent sees on its next turn, alongside whatever else the working context holds.

## Consequences

**Benefits**
- Cuts error-related token spend by 80–95% in loop-heavy agents — the empirically observed range in code-execution and tool-calling settings. The token savings translate directly to lower O(n²) attention computation on subsequent reasoning steps, since the KV cache grows proportionally to context length (mechanism 2, mechanism 3).
- Preserves self-healing: the agent still reads what failed and why, just in compact form.
- Surfaces recurrence: the per-class counter is itself diagnostic — "tried this 3 times, same error" is information the raw stream buries.
- Provides a clean escalation hook: thresholds give V9 and V1 something concrete to fire on.

**Costs**
- A second component in the loop — adds wiring; with an LLM compactor, adds a small per-error call.
- A bad compactor that drops the wrong detail can erase the line the agent needed to fix the bug.
- Dedup classification keys are a tuning lever — too loose and distinct errors get merged, too tight and the dedup does nothing.

**Risks and failure modes**
- *Lost root cause.* The compactor strips the one detail (a specific line number, a sub-error inside a wrapper) that was the actual fix.
- *Over-merged dedup.* Two different errors hash to the same class; the counter rises while the underlying problem changes; escalation fires on the wrong cause.
- *Silent escalation.* Threshold is hit but the Escalator is unwired; the agent's context says "tried 17 times" and the loop continues anyway.
- *V14 skipped.* The raw error is compacted into oblivion because the audit sink was never wired; post-hoc debugging is impossible.
- *Compactor drift.* An LLM compactor with a weak prompt re-phrases the cause differently each time, defeating dedup.

## Implementation Notes

- Start with a code-only compactor. A regex or structured-exception parser that produces `[ErrorType] at file:line: root_cause_snippet` handles 80% of cases at zero LLM cost. Add an LLM fallback only for the unstructured remainder.
- Define the dedup key explicitly: `(exception_type, file:line, normalised_message)` is a strong default. Normalising the message — stripping numbers, paths, request IDs — is what makes two of the "same" error actually match.
- Carry the count visibly: render in context as `[ConnectionError] at db.query line 42: connection refused (×4)`. The bracketed count is itself a prompt the agent can reason about.
- Decide the threshold once, write it down. The 12-Factor reference value is ~3 consecutive same-class errors $\to$ escalate. Run-total budget is task-specific; cap it.
- Pair V11 with V9 unconditionally. V11 detects recurrence; V9 *acts* on the cap. Without V9 the dedup counter is decoration.
- Pair with V14 unconditionally. The active-context view is for the agent; the audit view is for everyone else.
- For tool wrappers, do the compaction at the wrapper boundary — every tool returns either a result or a compacted error, never a raw traceback up the stack.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V11 wraps the tool / code / API boundary in a compactor-plus-history component. The full raw error fans out to **V14 Trajectory Logging** (audit) and a compact digest fans in to the agent's context. Threshold breach hands off to **V9 Bounded Execution** (halt) or **V1 Human-in-the-Loop** (review).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Tool / code / API call fails; capture raw error | `code` | |
| 2 | Persist the raw error to the trajectory log | `code` | V14 |
| 3 | Extract `(type, location, root_cause)` from the raw error | `code` (`LLM` only if unstructured) | optional Compactor session |
| 4 | Compute dedup key `(type, location, normalised_message)` | `code` | |
| 5 | Match key against Error History; append or increment | `code` | |
| 6 | Check thresholds (consecutive-same, total-budget) | `code` | V9 thresholds |
| 7 | If breached, hand off to V9 (halt) or V1 (review) | `code` | V9 / V1 |
| 8 | Return compact digest stream to the agent | `code` | |

**Skeleton** — wiring only; the `# LLM` line is optional and fires only when the structured extractor cannot parse:

```
on_error(raw_err, history, audit, thresholds, agent_ctx):
    audit.write_raw(raw_err)                           # code  — V14, always
    parsed = structured_extract(raw_err)               # code
    if parsed is None:                                 # code
        parsed = Compactor(raw_err)                    # LLM   — fallback only
    digest = format_digest(parsed)                     # code
    key    = dedup_key(parsed)                         # code
    if key in history:                                 # code
        history[key].count += 1
    else:
        history.append(key, digest)
    if history.breach(thresholds):                     # code
        return escalate_to_v9_or_v1(history)           # code  — V9 / V1
    return render(history, agent_ctx)                  # code
```

**The LLM sessions.** In the strict form, **none** — V11 is overwhelmingly wiring, and that is the point. An *optional* small generalist (the "Compactor") handles unstructured error bodies the parser cannot:

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Compactor** *(optional)* | small fast generalist | role: *"you extract a one-line diagnostic from a raw error"*; output contract: `type · location · root cause` in one short sentence; rule: preserve the specific detail (line, key, field name) that names the cause | the raw error body |

**Specialist-model note.** None. V11 needs no fine-tuned model and no long-context model — both the compactor (when used) and the dedup logic operate on a single error at a time. The pattern's value lives in the **wiring discipline** (compactor at the tool boundary; raw error to V14 *before* compaction; dedup key designed once; thresholds wired to V9 / V1), not in a strong LLM. If anything, the temptation to use a strong general model as a per-error compactor is itself an anti-pattern — it inflates cost and latency for a task a regex usually solves.

## Open-Source Implementations

V11 is a wiring pattern rather than a library — there is no canonical project named "Error Compaction". The verified references are:

- **12-Factor Agents — Factor 9: Compact Errors into Context Window** — [`github.com/humanlayer/12-factor-agents/blob/main/content/factor-09-compact-errors.md`](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-09-compact-errors.md) — the canonical articulation of the pattern: append errors to the event thread, restructure rather than dump raw, cap consecutive same-error attempts (~3) before escalation.
- **LangGraph `ToolNode` with `handle_tool_errors`** — [`github.com/langchain-ai/langgraph/blob/main/libs/prebuilt/langgraph/prebuilt/tool_node.py`](https://github.com/langchain-ai/langgraph/blob/main/libs/prebuilt/langgraph/prebuilt/tool_node.py) — production embodiment: `handle_tool_errors` parameter intercepts tool exceptions and substitutes a `ToolMessage` (string, exception-type filter, or callable) before the error reaches the model. The compactor-at-the-boundary half of V11, built into the framework.
- **OpenAI Agents SDK exceptions module** — [`openai.github.io/openai-agents-python/ref/exceptions/`](https://openai.github.io/openai-agents-python/ref/exceptions/) — typed `ToolCallError`, `ToolTimeoutError`, `ModelBehaviorError` provide the structured-exception substrate that makes code-only compaction feasible at the SDK boundary.

## Known Uses

- **Claude Code** and similar code-execution agents — compile / runtime errors are caught at the tool wrapper, summarised into a short diagnostic line for the model, and escalated to user review after repeated failure of the same class.
- **LangGraph**-based production agents — the `handle_tool_errors` parameter is the standard install for converting raw tool exceptions into compact `ToolMessage` content before they re-enter the graph.
- **HumanLayer**-pattern agents (the project authoring the 12-Factor reference) — explicit error-counter-per-tool with escalation to human at threshold.
- Production coding agents observed in the "Inside the Scaffold" empirical study — selective error summarisation alongside selective tool-result dropping as a context-management technique.

## Related Patterns

- **Distinct from** K6 Context Compression — K6 compresses *general history* on window-pressure triggers; V11 compresses the *error stream specifically* on every error event, with dedup-and-count semantics and an escalation hook K6 does not have. Same instinct, different scope and trigger.
- **Distinct from** K7 Context Pruning — K7 deletes *spent* spans losslessly (tool outputs already consumed); V11 *transforms* errors at arrival, lossy by design. They compose: prune spent tool outputs with K7, compact remaining errors with V11.
- **Composes with** V14 Trajectory Logging — V11 strips the in-context view; V14 keeps the full audit copy. Both run simultaneously, for different audiences. Installing V11 without V14 destroys post-hoc debuggability.
- **Composes with** V9 Bounded Execution — V11 detects recurrence; V9 acts on it. The threshold-breach hand-off is the contract between them.
- **Composes with** V1 Human-in-the-Loop — the alternative escalation target when threshold breach should pause for review rather than halt.
- **Required by** R13 CodeAct and R14 Program of Thoughts — code-execution agents generate large, repetitive errors as a normal part of the loop; raw-append is not viable, V11 is the default install.
- **Pairs with** O8 Loop Agent and the Reasoning loops (R4 ReAct, R7 Reflexion) — any pattern that loops over tool calls inherits the error-tonnage problem V11 solves.

## Sources

- HumanLayer — *12-Factor Agents*, Factor 9 "Compact Errors into Context Window" (2024–25) — the canonical articulation.
- LangGraph documentation and `prebuilt.ToolNode` source — production reference implementation of error compaction at the tool boundary.
- OpenAI Agents SDK exceptions reference — structured `ToolCallError`, `ToolTimeoutError`, `ModelBehaviorError` types.
- Anthropic — *Building Effective Agents* (2024) — retry-with-context discipline as a foundation of agentic reliability.
- "Inside the Scaffold" empirical study of production coding agents (arXiv) — context-management techniques including selective error summarisation observed in deployed systems.
