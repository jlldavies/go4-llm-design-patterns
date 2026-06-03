# V19 — Fallback / Graceful Degradation

> When the primary execution path fails — a model errors, a circuit breaker trips, a bound is hit, a tool refuses — switch to a pre-declared degraded path (simpler model, cached answer, deterministic rule, or human escalation) instead of returning an error to the user.

**Also Known As:** Graceful Degradation, Circuit-Breaker Fallback, Failover, Degraded-Mode Path, Recovery Lane.

**Classification:** Category V — Reliability · Band V-B Operational Reliability · the *recovery* counterpart to V9 — V9 detects and halts; V19 declares what runs instead.

---

## Intent

Make every failure mode of the primary path land on a *named, pre-declared, cheaper* execution path so the system answers something useful instead of an error, while loudly signalling that it has degraded.

## Motivation

V9 Bounded Execution stops the runaway: the iteration cap fires, the cost cap fires, the wall-clock cap fires, the consecutive-error counter from V11 fires. V9 is the brake. But a brake is not a destination — once V9 halts the loop, *something* still has to be returned to the caller. The same applies to every other failure surface: the model rate-limits, the provider returns 503, a tool times out, a guardrail rejects the output, V15 LLM-as-Judge fails the answer. Without a declared fallback path, all of these collapse into the same outcome — an exception bubbles up and the user sees a 500. The agent fails *loudly* rather than *gracefully*.

The pattern is the software engineering convention transferred intact: the **circuit-breaker fallback** (Nygard 2007, Netflix Hystrix 2012, Resilience4j 2017). For every primary call, declare what runs when the primary cannot. The fallback is *not* a retry of the same thing — that is V9's domain (cap the retries) and the LLM-gateway routers' domain (try another endpoint of the same model). The fallback is a *structurally different, cheaper, more predictable* path: a smaller model that answers fewer queries adequately; a cached response from the last successful invocation; a deterministic rule that handles the common case; a templated "we couldn't complete this, here's what we know" reply; a hand-off to a human. The system tells the user the answer is degraded and tells the operator the primary failed.

This is *distinct* from K5 Adaptive RAG's fallback. K5's fallback is corpus-side: retrieval returned bad context, so re-retrieve, reformulate, or hit web search. V19's fallback is *system-side*: the primary execution path — model, agent, tool, whole pipeline — failed, so run a *different pipeline*. K5 lives inside one Generator session and recovers the data fed into it; V19 lives outside the whole agent and recovers the answer entirely. They compose — K5 handles the retrieval failure, V19 handles the case where K5 itself cannot complete.

## Applicability

Use V19 when:

- the primary path has known, frequent failure modes — rate limits, timeouts, provider outages, V9 caps, guardrail rejections, V15 judge failures;
- the user-facing contract requires *an answer* — silently returning an error is worse than returning a degraded answer with a disclaimer;
- a cheaper / simpler / cached / deterministic path can answer at least a subset of queries adequately;
- the system is in production and the cost of a hard failure (a 500, a stuck workflow, a human waiting) exceeds the cost of a degraded answer.

Do not use when:

- the task is one where wrong answers are worse than no answers (medical dosing, legal directives, irreversible actions) — there, **V1 Human-in-the-Loop** is the only valid fallback;
- there is no genuinely cheaper / more reliable alternative path — a "fallback" that calls the same model with the same prompt is not a fallback, it is a retry, which belongs to the gateway router and **V9**;
- the failure being papered over is a *bug* the team should fix — V19 then becomes a quiet excuse for never repairing the primary;
- the fallback would silently produce wrong answers users cannot detect (no disclaimer surface, no degraded-state signal) — that is **A5 Output-Only Guardrails** in another costume.

## Decision Criteria

V19 is right when the primary path has measurable failure modes, a degraded path actually exists, and the user is better served by *something* than by an error.

**1. Inventory the failure modes.** List every way the primary path can fail to produce a usable answer:
- *Provider failures* — 5xx, rate limits, content-policy refusals, timeouts.
- *V9 cap breaches* — iteration, cost, wall-clock, consecutive-error.
- *V15 judge failures* — final-output rejected on faithfulness, safety, or format.
- *Tool failures* — sandbox timeout, MCP server down, downstream API 500.
- *Inner-pattern failures* — K5 fallback chain exhausts itself, R7 Reflexion converges on a bad answer.

If you cannot list at least three with measured rates, you do not yet know enough to design a fallback — instrument first (**V14 Trajectory Logging**, **V17 Online Eval**) and revisit.

**2. Match each failure to a fallback class.** Pick from a small, declared menu:
- **Cheaper model** — same task, smaller / faster / cheaper model; correct when the failure is capacity (rate limit, cost cap).
- **Cached answer** — last known good response for an equivalent input; correct when the failure is transient and the input is repeated or near-repeated.
- **Deterministic rule** — a hand-coded heuristic that handles the common case; correct when the task has a long tail of trivial inputs and you want to bypass the model entirely on outage.
- **Templated reply** — a static "we couldn't complete this — here's what we know" message with whatever partial state survives; correct when no useful answer is possible but the channel still needs a response.
- **Human escalation** — route the unanswered task to a human queue; correct when the answer matters more than the latency and **V1 Human-in-the-Loop** can absorb the volume.

Every failure mode in §1 must name one of these. An unhandled failure mode is a gap.

**3. Cost the degraded path.** The fallback must be cheaper *and* faster than the primary on the failing path. A "fallback" that costs more is not a fallback — it is an upgrade tier and belongs in front of the primary, not behind it. Measure: p50/p95 latency and unit cost of the fallback vs the primary; the fallback should be at least 2$\times$ cheaper or 2$\times$ faster (typically both) or the design is wrong.

**4. Wire the degraded-state signal.** The user must know the answer is degraded; the operator must know the primary failed. Two outputs, never one. If the system returns a fallback indistinguishable from a primary answer, you have built a *silent failure factory*: V14 must log the fallback invocation, the response must carry a degraded-state marker (header, field, prefix line), and **V17 Online Eval** must alarm when fallback rate crosses a threshold (5% sustained is a common operating bound; tune from data).

**5. Bound the fallback itself.** A fallback that itself fails must not cascade. Either it terminates in a templated reply (no further fallback), or it escalates to **V1**, or it returns a typed error. *Fallback chains deeper than two levels are an anti-pattern* — they hide the real failure behind layers of decreasingly useful answers.

**Quick test — V19 is the right pattern when:**

- the primary path has known failure modes the team has measured, *and*
- a structurally different and genuinely cheaper / more reliable path exists for at least a subset of queries, *and*
- a degraded-state signal can be surfaced to user and operator, *and*
- the fallback is bounded (no cascade), with **V9**, **V14**, and **V17** in place.

If the primary path is reliable enough that fallback rate would be < 1%, V19 is over-engineering — fix the rare failures directly. If the only "fallback" available is "same model again", you want gateway retries (LiteLLM / Portkey / OpenRouter), not V19. If wrong answers are worse than no answers, **V1 Human-in-the-Loop** replaces V19 as the only safe degraded path.

## Structure

```
                            ┌──── V14: log invocation + outcome
                            │
        request ──▶ [ Primary Path ]
                          │
                  ┌───────┴────────┐
                 ok               fail
                  │                │
                  ▼          ┌─────┴──────────────────────┐
              Answer         │ Failure Classifier         │
                             │  - provider error?         │
                             │  - V9 cap breach?          │
                             │  - V15 judge reject?       │
                             │  - tool failure?           │
                             └─────┬──────────────────────┘
                                   │
                            (dispatch by class)
                                   ▼
        ┌────────────┬──────────────┬──────────────┬──────────────┐
        │            │              │              │              │
   Cheaper Model  Cached Answer  Deterministic  Templated     V1 Human
                                    Rule         Reply        Escalation
        │            │              │              │              │
        └────────────┴──────────────┴──────────────┴──────────────┘
                                   │
                                   ▼
                       attach degraded-state marker
                                   │
                                   ▼
                            Answer (degraded)
                                   │
                                   └──▶ V17: fallback-rate metric / alarm
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Primary Path** | the normal, full-capability execution | request $\to$ answer or typed failure | swallow its own failures — every failure mode must surface as a typed signal the Classifier can read. |
| **Failure Classifier** | mapping a typed failure to a fallback class | typed failure $\to$ fallback selector | guess at unknown failure types — unknown failure must default to *templated reply + alarm*, never to "try the primary again". |
| **Fallback Path** *(one per class)* | a structurally simpler / cheaper / cached / deterministic execution | request + failure context $\to$ degraded answer | call back into the Primary Path — that is a retry, not a fallback, and creates a cascade. |
| **Degraded-State Marker** | making the degradation visible to the caller | answer $\to$ answer + `degraded: true` field / header / prefix | be omitted because "the user might be confused" — silent fallback is the most common V19 failure mode. |
| **Cascade Guard** | preventing fallback-of-fallback | fallback-failure $\to$ escalate-to-V1 / templated reply | invoke another fallback class — depth-2 maximum; deeper means the design is wrong. |
| **Audit & Alarm** *(V14 + V17)* | recording every invocation and alarming on rate | invocation event $\to$ trace + rolling metric | be optional — a fallback whose rate is not monitored will silently grow until it *is* the primary. |

Six narrow responsibilities. The reliability of V19 comes from the discipline of *one* Classifier (single dispatch), *bounded* fallback depth (no cascade), and *non-optional* state-marking and alarming — without those three, the pattern degrades into "swallow errors silently", which is worse than no fallback at all.

## Collaborations

A request enters the Primary Path. On success, the answer returns and V14 records a clean trace span. On failure, the Primary Path raises a *typed* failure — provider error, V9 cap breach, V15 judge reject, tool failure, K5 chain exhaustion — and the **Failure Classifier** dispatches to one of the declared **Fallback Paths**: a cheaper model, a cached answer, a deterministic rule, a templated reply, or **V1 Human-in-the-Loop** escalation. The fallback produces a degraded answer; the **Degraded-State Marker** attaches the visible signal (header, field, prefix); V14 logs the invocation; V17 increments the rolling fallback-rate metric and alarms if the threshold is crossed. If the fallback itself fails, the **Cascade Guard** does *not* try another fallback — it returns the templated reply or escalates to V1, and the alarm fires. The caller receives the answer, the operator sees the fallback rate climb, and the team can decide whether to repair the primary or accept the degraded mode.

## Consequences

**Benefits**
- Hard failures become soft failures — the system answers something instead of returning a 500.
- Failure modes become *visible* through fallback-rate metrics — primary degradation is measurable, not anecdotal.
- The pattern composes cleanly with the rest of Category V: V9 bounds, V11 compacts, V14 logs, V17 alarms, V19 recovers, V1 escalates.

**Costs**
- Every fallback class is a second pipeline to build, test, and maintain — V16 Offline Eval must cover both primary and fallback paths.
- Cached / deterministic fallbacks go stale; they require freshness policies and periodic re-validation.
- The Degraded-State Marker complicates the response contract — clients must parse and surface it.

**Risks and failure modes**
- *Silent fallback.* The marker is omitted and degraded answers look identical to primary answers; users build trust in answers that are systematically worse than the primary; quality regresses invisibly.
- *Fallback cascade.* The fallback fails, the system calls another fallback, which also fails; each layer hides the underlying failure further from the operator.
- *Fallback as bug-shield.* The team stops fixing primary-path failures because "the fallback handles it"; primary degrades to the point where the fallback *is* the system, but the fallback was never designed to be the primary.
- *Stale cache.* The cached-answer fallback serves a response that was correct three months ago and is now wrong; no freshness signal, no review.
- *No alarm.* Fallback rate rises from 1% to 30% across a quarter; nobody notices because V17 was not wired to V19's invocation count.

## Implementation Notes

- **Start with the gateway layer.** LiteLLM, Portkey, and OpenRouter all ship router-level fallbacks — primary model $\to$ secondary model $\to$ tertiary model — that handle provider-side failures (rate limits, 5xx, content policy) without any custom code. This is the cheapest possible V19 and the right first install. Only build agent-level fallbacks for failures the gateway cannot see (V9 caps, V15 rejects, K5 chain exhaustion).
- **Classify failures at the boundary, not in the agent.** The Failure Classifier should be a thin wrapper around the primary call site — typed exceptions in, fallback selector out. Putting the classifier inside the agent prompt means the same broken model decides what to do about its own brokenness.
- **Cache fallbacks need a freshness policy.** Either a TTL or a "best-before invalidation event" trigger. A cached answer with no freshness check is a wrong-answer factory waiting for the world to change.
- **Deterministic fallbacks must be honest.** A rule-based path that only handles 20% of inputs adequately should fall through to the templated reply on the other 80%, not pretend to answer.
- **Templated replies are the last-line default.** Every V19 design needs one — the case where the primary failed, no cache exists, no rule applies, and human escalation is unavailable. The reply should name the failure category, say what was tried, and give the user an action ("try again in 30s", "contact support", "ask differently").
- **Wire V17 to the fallback rate explicitly.** A separate metric per fallback class. The primary-failure signal is the *rate*, not any individual invocation.
- **Test the fallback in V16 and V18.** A fallback that has never been exercised is not a fallback; it is a hope. V16 should include test cases that force primary failure and verify the fallback answers; V18 simulations should inject provider outages and verify the system stays up.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V19 wraps the **Primary Path** (whatever pattern the agent runs — K1 / K5, R4 / R7, O6, etc.) in a classifier-and-dispatch layer. It draws on **V9 Bounded Execution** (the cap-breach signals it dispatches on), **V11 Error Compaction** (the typed-failure surface), **V14 Trajectory Logging** (audit), **V17 Online Eval** (rate alarm), and **V1 Human-in-the-Loop** (last-line escalation). The fallback classes are mostly `code`; an optional cheaper-model fallback is the one `LLM` step.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Invoke primary path; capture typed result-or-failure | `code` | inner pattern |
| 2 | On success: emit V14 span, return answer | `code` | V14 |
| 3 | On failure: classify failure type | `code` | V9 / V11 / V15 typed signals |
| 4 | Dispatch to fallback class (cheaper model / cache / rule / template / V1) | `code` | |
| 5a | Cheaper-model fallback: invoke smaller model on the same request | `LLM` | Fallback-Model session |
| 5b | Cached / deterministic / templated fallback: serve directly | `code` | |
| 5c | Human-escalation fallback: enqueue to V1 | `code` | V1 |
| 6 | Attach degraded-state marker to answer | `code` | |
| 7 | Emit V14 invocation span; increment V17 fallback-rate metric | `code` | V14, V17 |
| 8 | If fallback also fails: Cascade Guard $\to$ templated reply or V1, alarm | `code` | V1, V17 |

**Skeleton** — the wiring; one `# LLM` line is the cheaper-model fallback, optional:

```
handle_request(req):
    try:
        ans = primary_path(req)          # code  — inner pattern
        v14.log_success(req, ans)        # code  — V14
        return ans
    except TypedFailure as f:            # code  — V9 / V11 / V15 / tool / K5 typed
        cls = classify(f)                # code  — Failure Classifier
        try:
            if cls == "cheaper_model":
                ans = FallbackModel(req) # LLM   — small model, same task
            elif cls == "cache":
                ans = cache.get_or_none(req)  # code
            elif cls == "rule":
                ans = deterministic_rule(req) # code
            elif cls == "template":
                ans = templated_reply(f)      # code
            elif cls == "human":
                return v1.escalate(req, f)    # code  — V1
            if ans is None:                   # cache miss / rule N/A
                ans = templated_reply(f)
        except Exception as f2:               # Cascade Guard
            v17.alarm("fallback_failed", cls) # code
            return templated_reply(f2) or v1.escalate(req, f2)
        ans = mark_degraded(ans, cls)         # code  — degraded-state marker
        v14.log_fallback(req, cls, ans)       # code  — V14
        v17.increment(cls)                    # code  — V17 rate metric
        return ans
```

**The LLM sessions.** V19 is overwhelmingly wiring. The single optional `LLM` step is the cheaper-model fallback — same task contract, weaker model:

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Fallback Model** *(optional)* | a smaller / faster / cheaper generalist (e.g. Haiku-class behind a Sonnet-class primary, or a 7B–8B open model behind a frontier model) | role identical to the primary's role; output contract identical; an added instruction: *"if you cannot answer confidently, return `INSUFFICIENT` rather than fabricating"* | the request, exactly as the primary received it |

The Fallback Model's setup is *deliberately* the primary's setup — same role, same output contract — so the caller's parser does not have to branch. The added `INSUFFICIENT` escape is what lets the cheaper model honestly refuse the hard subset rather than hallucinate; on `INSUFFICIENT`, the Cascade Guard falls through to the templated reply or V1.

**Specialist-model note.** None. V19's value is in the *classifier-and-dispatch wiring*, not in a stronger LLM. The cheaper-model fallback is by design a *weaker* generalist; the cached / deterministic / templated / human-escalation fallbacks involve no model at all. The smaller model is mechanically appropriate for the fallback task: simpler generative tasks such as templated replies, schema extraction, or classification among a small set of options do not require the full reasoning capacity of a large model (mechanism 8). The value of V19 comes from the task boundary, not from architectural novelty in the fallback path. The temptation to use a *stronger* model as the fallback ("if Sonnet fails, try Opus") is the opposite of the pattern — that is a quality upgrade, not a degradation, and it belongs in front of the primary as a retry tier, not behind it.

Gateway retries are appropriate for transient provider capacity failures (rate limits, 503s) — these are queueing failures, not model-capability failures; the same model will succeed once capacity is restored. V19 fallbacks are for capability failures — the primary model cannot answer the query reliably — which require a structurally different (not just repeated) execution path (mechanism 8).

## Open-Source Implementations

V19 has both gateway-level libraries (where provider fallback is a configuration line) and library-level realisations of the underlying circuit-breaker pattern.

- **LiteLLM Router — Fallbacks** — [`docs.litellm.ai/docs/proxy/reliability`](https://docs.litellm.ai/docs/proxy/reliability) — `fallbacks: [{"gpt-4": ["claude-3-opus"]}]` plus `default_fallbacks`, `content_policy_fallbacks`, and `context_window_fallbacks` as distinct dispatch classes; a near-canonical realisation of the Failure Classifier + Fallback Path participants at the gateway layer.
- **Portkey AI Gateway — Fallbacks** — [`portkey.ai/docs/product/ai-gateway/fallbacks`](https://portkey.ai/docs/product/ai-gateway/fallbacks) — `strategy: { mode: "fallback", on_status_codes: [429, 503] }` with a prioritised `targets` array; fallback targets are composable (each can itself be a load balancer or conditional router) and every invocation is logged for trace.
- **OpenRouter — Model Fallbacks** — [`openrouter.ai/docs/guides/routing/model-fallbacks`](https://openrouter.ai/docs/guides/routing/model-fallbacks) — `models: ["openai/gpt-4o", "anthropic/claude-3-opus", "..."]` priority list; tries the next on error, rate-limit, or content-policy refusal; the response includes the model that was ultimately used so the caller can detect degradation.
- **Not Diamond — Reliability, Fallbacks, and Load-Balancing** — [`docs.notdiamond.ai/docs/fallbacks-and-timeouts`](https://docs.notdiamond.ai/docs/fallbacks-and-timeouts) — `default` parameter names the fallback LLM from the `llm_providers` list; supports per-model max-retries, exponential backoff, and average-rolling-latency fallback; Go SDK at [`github.com/Not-Diamond/go-notdiamond`](https://github.com/Not-Diamond/go-notdiamond).
- **Resilience4j** — [`github.com/resilience4j/resilience4j`](https://github.com/resilience4j/resilience4j) — the modern circuit-breaker library (successor to Netflix Hystrix); `@CircuitBreaker(fallbackMethod = "...")` is the canonical Java articulation of the Primary Path + Fallback Path contract.
- **Netflix Hystrix** *(maintenance mode)* — [`github.com/Netflix/Hystrix`](https://github.com/Netflix/Hystrix) — the original circuit-breaker-with-fallback library (Netflix, 2012); now stable / not actively developed, but the wiki ([`github.com/Netflix/Hystrix/wiki/How-it-Works`](https://github.com/Netflix/Hystrix/wiki/How-it-Works)) remains the canonical explanation of the trip-and-fall-back semantics V19 inherits.

## Known Uses

- **Production LLM gateways** (LiteLLM, Portkey, OpenRouter, Not Diamond) — provider-level fallback is now table stakes; many deployed agent systems install one of these as the only V19 they have, and it handles the majority of provider-side failures.
- **Customer-support and IT agents** — common pattern: primary frontier-model agent $\to$ cheaper model on rate-limit $\to$ cached FAQ lookup on cache hit $\to$ templated "we'll get back to you" + ticket creation on full failure. Each layer logged, each layer measured.
- **Coding agents** (Claude Code, Cursor, similar) — primary code-edit model $\to$ smaller model on quota exhaustion $\to$ "model unavailable, please retry" templated reply; the degraded-state signal is the visible fallback notice in the UI.
- **High-availability conversational systems** — frontier model $\to$ smaller open model $\to$ static FAQ $\to$ human handoff is a well-trodden four-tier stack in enterprise deployments.

## Related Patterns

- **Pairs with** V9 Bounded Execution — V9 stops the runaway; V19 declares what runs in its place. A V9 cap with no V19 destination is a 500 with extra steps.
- **Composes with** V11 Error Compaction — V11 normalises the typed-failure surface (exception type, root cause) that V19's Failure Classifier dispatches on. Together they make failure *legible* (V11) and *actionable* (V19).
- **Composes with** V14 Trajectory Logging — every V19 invocation is a logged span with the fallback class; without V14 the fallback rate is invisible and §10's "silent fallback" failure mode is inevitable.
- **Composes with** V17 Online Evaluation — the fallback-rate metric is the alarm signal that says "the primary is degrading"; without V17 the team learns about the degradation from users.
- **Escalates to** V1 Human-in-the-Loop — V1 is the last-line fallback target when no automated degraded path is acceptable (irreversible actions, safety-critical answers).
- **Distinct from** K5 Adaptive RAG — K5's fallback is *corpus-side* (the retrieval failed; reformulate, broaden, hit the web); V19's fallback is *system-side* (the whole primary path failed; run a different pipeline). They compose: K5 handles bad retrieval inside its own loop, V19 handles the case where K5's loop itself terminates without an answer.
- **Distinct from** gateway retries — LiteLLM / Portkey / OpenRouter *retries* re-call the same model when a transient error occurs; V19 *fallbacks* switch to a structurally different path. Most gateways do both; the configuration distinguishes them (`num_retries` vs `fallbacks`). Use retries for transient transport failures, fallbacks for capacity and quality failures.
- **Inverts** A5 Output-Only Guardrails — A5 (anti-pattern) silently filters bad output at the end; V19 surfaces degradation explicitly to user and operator. A V19 without the Degraded-State Marker collapses into A5.

## Sources

- Nygard (2007) — *Release It! Design and Deploy Production-Ready Software* — the original articulation of the circuit-breaker pattern, including the "fall back to a degraded path" requirement that V19 inherits intact.
- Netflix Hystrix — *How it Works* wiki ([`github.com/Netflix/Hystrix/wiki/How-it-Works`](https://github.com/Netflix/Hystrix/wiki/How-it-Works), 2012-) — the canonical articulation of trip-and-fall-back semantics in production; Hystrix is now in maintenance mode but the design is the reference.
- Resilience4j — *Fallback Methods* ([`resilience4j.readme.io/docs`](https://resilience4j.readme.io/docs/getting-started-3), 2017-) — the modern Java circuit-breaker library; `@CircuitBreaker(fallbackMethod = …)` formalises the Primary + Fallback pairing.
- LiteLLM — *Fallbacks* documentation ([`docs.litellm.ai/docs/proxy/reliability`](https://docs.litellm.ai/docs/proxy/reliability)) — the dominant open-source LLM router; defines the distinct fallback classes (default, content-policy, context-window) V19's Failure Classifier dispatches on.
- Portkey — *Fallbacks* documentation ([`portkey.ai/docs/product/ai-gateway/fallbacks`](https://portkey.ai/docs/product/ai-gateway/fallbacks)) — composable fallback targets and status-code-triggered dispatch.
- OpenRouter — *Model Fallbacks* ([`openrouter.ai/docs/guides/routing/model-fallbacks`](https://openrouter.ai/docs/guides/routing/model-fallbacks)) — priority-list fallback with returned-model attribution as the degraded-state signal.
- Not Diamond — *Reliability, Fallbacks, and Load-Balancing* ([`docs.notdiamond.ai/docs/fallbacks-and-timeouts`](https://docs.notdiamond.ai/docs/fallbacks-and-timeouts)) — routing-based fallback with explicit default-model declaration and timeout semantics.
- Composio AI Agent Report 2025 — 88% production-failure analysis; cost overruns, silent failures, and missing recovery paths cited among top incident categories.
