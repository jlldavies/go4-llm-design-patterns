# O18 — Cache-Warmed Worker Pool

> Before dispatching parallel workers, establish and warm a stable shared context as a provider-cached prefix — so every worker in the pool reads its common setup from the KV cache rather than independently re-paying the prefill cost for identical tokens.

**Also Known As:** Primed Agent Pool, Prefix-Warm Fan-Out, Shared Context Warming.

**Classification:** Category IV — Orchestration · Band IV-B Agentic patterns · a cache-engineering refinement of O4 Parallelization and O6 Orchestrator-Workers. Sits between those patterns and the provider API; invisible to the task logic but material to cost and latency at scale.

---

## Intent

Design the shared context given to all parallel workers as a single stable, cacheable prefix; fire a warm-up call (or time the first worker call) to establish that prefix in the provider KV cache; then dispatch all remaining workers within the cache TTL — so the shared portion of each worker's prompt is served from cache at ~10% of the normal prefill cost rather than re-computed independently for each worker.

## Motivation

**O4 Parallelization** is the right pattern when sub-tasks can run concurrently. But O4 says nothing about the cost structure of how those parallel workers are instantiated. The naive implementation launches N workers with N identical or near-identical prompt prefixes — the same system instructions, the same role definition, the same tool schemas, the same domain context — and each pays full prefill cost for those shared tokens independently.

**The mechanistic problem.** Prefill cost is $O(n^2)$ in sequence length (mechanism 2). For a 3,000-token shared prefix and 10 workers, the naive approach pays $10 \times O(3000^2)$ prefill compute for tokens that are identical across all workers. Provider prefix caching (mechanism 5) exists precisely to eliminate this redundancy: the KV state tensor $[L \times n \times n_\text{kv} \times d_\text{head}]$ for the stable prefix is stored after the first request and served to subsequent requests at approximately 10% of the normal input token cost. But prefix caching only fires reliably when the shared prefix is explicitly designed as a stable unit, when the minimum threshold is met (1,024 tokens for Anthropic), and when all workers fire within the TTL window (~5 minutes for Anthropic).

**The gap.** O4 tells you to run in parallel. O6 tells you how to structure the orchestration. Neither tells you how to design your prompt prefixes so that the shared content is cached rather than re-computed for every worker. Cache-Warmed Worker Pool fills this gap: it is the cache-engineering discipline that makes parallel fan-out economical at scale.

**When the economics are compelling.** Consider a system prompt of 2,000 tokens (system instructions + persona + tools) shared across 20 parallel workers. Without cache warming, each worker pays full input token cost for 2,000 tokens = 40,000 token-equivalents of prefill. With cache warming (one write + 19 cache reads at 10%): 2,000 (write at ~125%) + 19 × 200 (reads at ~10%) = 2,500 + 3,800 = 6,300 token-equivalents. The saving is approximately 85% on the shared prefix portion — pure infrastructure cost, no quality tradeoff.

## Applicability

Use Cache-Warmed Worker Pool when:

- you are running O4 Parallelization or O6 Orchestrator-Workers with a pool of workers that share a substantial common prompt prefix;
- the shared prefix exceeds the provider minimum for prefix caching (1,024 tokens for Anthropic);
- all workers will be dispatched within the provider TTL window (~5 minutes for Anthropic);
- the shared prefix is stable — it does not change between the warm-up call and the worker calls, and it does not vary across workers.

Do not use it when:

- the shared prefix is below the caching minimum threshold — the warm-up overhead is wasted below ~1,024 tokens;
- workers require meaningfully different system prompts — if more than the final per-task delta varies across workers, there is no stable shared prefix to cache;
- the worker dispatch is spread over time exceeding the TTL — if workers fire over 10 minutes, the cache will have expired for the later ones; use **O8 Loop Agent** with fresh per-call prefills instead;
- the system runs a single worker per task and never fans out — the single call pays its own prefill; no caching dividend is available.

## Decision Criteria

**1. Measure the shared prefix size.** Count the tokens in the content that is identical across all workers: system prompt, persona, tool schemas, domain context, any shared preamble. If this is < 1,024 tokens: skip this pattern, the cache minimum is not met. If this is 1,024–5,000 tokens: moderate benefit; worth applying when N > 3 workers. If this is > 5,000 tokens: significant benefit; apply whenever N ≥ 2.

**2. Confirm the TTL budget.** All workers must fire within ~5 minutes (Anthropic TTL) of the warm-up call. If the fan-out takes longer — because workers are rate-limited, queued, or dispatched sequentially — the later workers will miss the cache. Either batch workers within the TTL window or design the system to re-warm the cache periodically.

**3. Verify prefix stability.** The cache key is the exact token sequence. A single token difference anywhere in the shared prefix invalidates the cache for that position and all subsequent ones. Confirm that the shared prefix is generated deterministically (same tokens every call, not sampled) and does not vary across workers. Dynamic content (the per-worker task delta, retrieved context, user queries) must come *after* the stable shared prefix.

**4. Calculate the break-even.** The warm-up call costs one extra LLM call (minimal, but non-zero latency). The saving per worker is approximately 90% of the shared prefix token cost. Break-even is at approximately N = 2 workers for large shared prefixes; N = 4–5 for small ones. For any realistic fan-out of 5+ workers with a 1,000+ token shared prefix, the pattern pays.

**5. Model size assignment (mechanism 8).** The warm-up call itself is a lightweight operation — it can be a minimal task or even a null-content call whose only purpose is to establish the cache. Use the smallest model that can execute the warm-up task. Worker model selection follows the task complexity of each worker's sub-task.

## Structure

```
                    Shared Prefix (stable — designed as cacheable unit)
                           │
                    ┌──────▼───────┐
                    │  Warm-up     │  (one call, fires first — establishes KV cache)
                    │  call        │  (can be a minimal task or a null call)
                    └──────┬───────┘
                           │ KV cache written at provider
                           │ (within TTL window: ~5 min)
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       ┌────────────┐ ┌─────────┐ ┌────────────┐
       │ Worker 1   │ │Worker 2 │ │ Worker N   │  (all fire simultaneously)
       │ [cached    │ │[cached  │ │ [cached    │  (cache HIT on shared prefix)
       │  prefix +  │ │ prefix +│ │  prefix +  │  (~10% cost on shared tokens)
       │  task_1]   │ │ task_2] │ │  task_N]   │
       └────────────┘ └─────────┘ └────────────┘
              │                         │
              └────────────┬────────────┘
                           ▼
                    Collect results
                    (Synthesis or Orchestrator)

  Shared prefix: stable, deterministic, > min cache threshold.
  Per-worker delta: variable content — appended after the stable prefix.
  Timing: all workers within provider TTL window (~5 min).
```

The structural invariant: the cache boundary is an explicit design constraint, not an afterthought. Every token before the cache boundary must be stable, deterministic, and shared across all workers.

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Shared prefix** (a prompt artefact, not an LLM) | the stable content given to all workers: system prompt, persona, tool schemas, domain context, any fixed preamble | — | vary across workers or between warm-up and worker calls. A single token difference invalidates the cache. |
| **Warm-up call** (one LLM call, optional) | establishing the KV cache for the shared prefix before the worker fan-out | shared prefix + minimal task → cached KV state at provider | perform substantive work that delays the worker fan-out. It should be fast — a routing check, an acknowledgement, or a null call. |
| **Worker pool** (N parallel LLM calls, via O4) | executing per-task sub-tasks with the cached shared prefix | shared prefix (cache HIT) + per-worker task delta → per-task result | modify the shared prefix content — even one word change in the shared section invalidates the cache for all subsequent workers. Per-worker variation goes in the delta, never in the shared prefix. |
| **Fan-out coordinator** (code) | dispatching all workers within the TTL window, verifying timing, collecting results | warm-up completion → simultaneous worker dispatch | spread the worker dispatch over more time than the provider TTL. Late workers re-pay full prefill cost for the shared prefix. |
| **Cache boundary marker** (a prompt design decision, not code) | the exact token position where the stable shared prefix ends and per-worker variable content begins | — | be implicit. The boundary must be explicit — either via provider API cache control markers or by discipline in prompt construction. An implicit boundary is no boundary. |

## Collaborations

The Fan-out Coordinator fires the Warm-up call with the full Shared prefix. This establishes the KV cache at the provider. Within the TTL window, the Coordinator dispatches all N Workers simultaneously (via **O4 Parallelization**), each with the identical Shared prefix followed by their unique per-task delta. Each Worker's request hits the provider cache for the shared portion; only the per-worker delta is prefilled fresh. Workers complete and return results to the Coordinator or directly to the Synthesis step. The warm-up call's result is discarded unless it was designed to do useful work.

Composition with **O6 Orchestrator-Workers**: the Orchestrator calls serve as the warm-up (the Orchestrator's planning call fires the shared prefix into cache); the subsequent worker dispatches are the fan-out. Timing the Orchestrator call and worker dispatch within the TTL is the key operational constraint.

Composition with **H1 Identity Persistence**: the Genesis State and any stable humanizer content (H7, H9 fixed entries) should be composed into the shared prefix, placed before any session-variable content. This maximises the cached token count and amortises the Genesis State prefill cost across all workers in a fan-out session.

## Consequences

**Benefits**

- Approximately 85–90% reduction in prefill cost for the shared prefix across all workers beyond the first (or the warm-up call).
- Latency reduction: cache hits skip prefill computation for the shared portion, reducing each worker's time-to-first-token proportionally to the shared prefix fraction of the total prompt.
- No quality impact: the model's output is identical whether the KV states came from a fresh prefill or a cache hit — the computation is the same, just reused.
- Scales linearly with N workers: each additional worker costs only the per-task delta plus 10% of the shared prefix. Marginal cost per worker approaches the per-task delta cost as N grows.

**Costs**

- One warm-up call: a small fixed overhead (one API call, minimal task). Amortized across N workers, negligible for N ≥ 3.
- TTL constraint: the entire fan-out must complete within ~5 minutes. Systems with slow or rate-limited dispatch may miss the window for later workers.
- Prompt discipline: the shared prefix must be managed as a first-class artifact — versioned, tested for stability, and guarded against inadvertent variation.
- Cache boundary complexity: the boundary between stable and variable content must be explicit and enforced. Systems that dynamically assemble prompts must ensure the stable portion is generated before the variable portion, every time.

**Risks and failure modes**

- *Cache miss due to prefix variation* — a dynamic element (a timestamp, a run ID, a formatted date) accidentally included in the shared prefix section causes every worker to re-pay full prefill. Audit the shared prefix for non-deterministic content before deployment.
- *TTL expiry mid-fan-out* — sequential dispatch over more than 5 minutes causes later workers to cold-prefill. Mitigation: use `O4 Parallelization` (simultaneous dispatch) or re-warm the cache partway through for very large worker pools.
- *Below-threshold shared prefix* — shared prefix under 1,024 tokens does not qualify for caching; the warm-up call adds latency for no savings. Check the threshold before applying the pattern.
- *Warm-up call latency on critical path* — if the warm-up call is on the critical path (workers cannot start until it completes), the fixed latency overhead may not be acceptable for time-sensitive workloads. Mitigation: run the warm-up as part of a prior stage (e.g., the Orchestrator planning call) rather than as a dedicated step.
- *Provider policy changes* — TTL, minimum thresholds, and pricing are provider policies, not architectural guarantees. Build the system to function correctly (at higher cost) if caching is unavailable, and monitor cache hit rates.

## Implementation Notes

- **Mark the cache boundary explicitly.** Use the provider's API cache control parameter (Anthropic: `cache_control: {"type": "ephemeral"}` at the message or content block level) at the end of the shared prefix. Do not rely on implicit position-based caching — make the boundary a code-level constant.
- **Generate the shared prefix deterministically.** If the shared prefix is assembled programmatically, seed and fix any random elements. Log the shared prefix hash on each run; alert if it changes unexpectedly.
- **Separate stable from variable in prompt construction.** Build the prompt as two distinct components: `shared_prefix` (the cacheable unit, assembled once per session or deployment) and `per_worker_delta` (assembled per worker). Concatenate at dispatch time, not at definition time.
- **Time the fan-out.** Log the timestamp of the warm-up call and the timestamp of the last worker dispatch. Assert that the difference is less than the TTL. In production, alert if the fan-out exceeds 80% of the TTL.
- **Monitor cache hit rates.** Anthropic returns cache hit status in API response metadata. Track the ratio of cache hits to misses per fan-out batch. A hit rate below 80% on a fan-out of 5+ workers indicates prefix variation or TTL expiry — investigate immediately.
- **Compose with H1 for Humanizer stacks.** If workers need a Genesis State or stable persona, include it in the shared prefix rather than injecting it per-worker. The combined stable prefix (system instructions + Genesis State + tool schemas) often exceeds the caching minimum naturally.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**The chain:**

| # | Step | Kind | Notes |
|---|---|---|---|
| 1 | Assemble `shared_prefix` (stable content for all workers) | `code` | Must be deterministic. Log hash. |
| 2 | Assemble N `per_worker_delta` items (one per sub-task) | `code` | Variable content, assembled per worker. |
| 3 | Fire warm-up call: `[shared_prefix + minimal_task]` | `LLM` | Establishes KV cache. Use smallest viable model. |
| 4 | Record warm-up completion timestamp | `code` | TTL clock starts here. |
| 5 | Dispatch all N workers simultaneously: `[shared_prefix + delta_i]` for each i | `LLM × N` (O4) | Fire within TTL window. All share cached prefix. |
| 6 | Assert all dispatches within TTL | `code` | Alert if any worker fires > 0.8 × TTL after warm-up. |
| 7 | Collect results; handle partial failures | `code` | |
| 8 | Synthesise or pass to Orchestrator | `LLM` or `code` | |

**Prompt structure:**

```
[SHARED PREFIX — cache boundary here]
  System instructions          (stable, versioned)
  Role / Persona (S3)          (stable)
  Tool schemas (I2/I3)         (stable — only tools shared by all workers)
  Domain context               (stable — if loaded from a fixed source)
  Constraint framing (S5)      (stable)
  Output template (S6)         (stable — the schema all workers return)

[PER-WORKER DELTA — after the cache boundary]
  Per-worker objective
  Per-worker context (retrieved, dynamic)
  Per-worker task instructions
```

**Session assignments:**

| Call | Model | Setup | Per-call |
|---|---|---|---|
| Warm-up | smallest viable | — | shared_prefix + "acknowledge ready" or minimal task |
| Each worker | sized to task complexity (mechanism 8) | — | shared_prefix + per_worker_delta_i |
| Synthesis (if any) | strong generalist | — | original goal + collected results |

## Known Uses

- **Multi-agent research fan-outs** (Anthropic Claude.ai research system): the LeadResearcher's planning call establishes the system prompt in cache; subsequent subagent calls share the cached system prefix and pay only the per-subquery delta.
- **Batch document processing**: a single system prompt describing the extraction schema is cached; N document-specific calls share the cached schema and pay only per-document content.
- **Parallel eval harnesses**: a shared judge persona and rubric is cached; N completion-to-judge calls share the cached rubric and pay only per-completion content (see **V15 LLM-as-Judge**).
- **Multi-model routing with shared preamble**: when an **O3 Routing** step dispatches to multiple models with a shared routing context, the shared routing preamble can be cached against the primary model's call.

## Related Patterns

- **Composes with O4 Parallelization** — O4 provides the parallel dispatch; O18 provides the cache-engineering discipline over the shared prefix. They are composites, not alternatives.
- **Composes with O6 Orchestrator-Workers** — the Orchestrator planning call can double as the warm-up call. The shared worker context should be designed as the shared prefix.
- **Composes with H1 Identity Persistence** — stable Genesis State and humanizer stack belong in the shared prefix; every worker benefits from the cached identity without re-prefilling it.
- **Composes with V15 LLM-as-Judge** — judge persona and rubric are stable across N judge calls; O18 makes parallel judging economical.
- **Requires O17 Agent Isolation** — workers share the cached prefix but must not share context beyond it. Each worker's per-task reasoning and results are isolated (O17); only the prefix is shared.
- **Distinct from O4 Parallelization** — O4 says "run in parallel." O18 says "design the prefix so parallel workers share cached KV states." O4 is the orchestration decision; O18 is the cache-engineering discipline within that decision.
- **Governed by V9 Bounded Execution** — the warm-up call and worker fan-out must be bounded on count, cost, and time. The TTL constraint is an additional O18-specific bound.
- **Distinct from K9 Long Context** — K9 caches a long stable document corpus in context, then queries it multiple times in one session. O18 caches a stable system prompt prefix across multiple parallel API calls in the same TTL window. Both use mechanism 5; the unit of reuse differs (session vs. call batch).

## Sources

- Anthropic (2025) — "Prompt Caching" documentation. API reference for `cache_control` parameter, minimum token thresholds, TTL, and pricing. [docs.anthropic.com](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching).
- Mechanism 2 — $O(n^2)$ attention compute; this document, Chapter 0 §0.1.
- Mechanism 5 — Prefix caching as cache engineering; this document, Chapter 0 §0.1.
- Mechanism 6 — Subagent decomposition as context bounding; this document, Chapter 0 §0.1.
- Mechanism 8 — Model size matching to task complexity; this document, Chapter 0 §0.2.
- GO4 §O4 Parallelization — the orchestration pattern this one refines.
- GO4 §O6 Orchestrator-Workers — the multi-agent pattern whose fan-out this one optimises.
