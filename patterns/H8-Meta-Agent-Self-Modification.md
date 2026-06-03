# H8 — Meta-Agent Self-Modification

> Let an agent tune its own operational parameters — prompts, tool ordering, sampling settings, sub-agent configurations — driven by measured performance signals, but only inside an enumerated modification surface, behind an offline-eval gate, with a human approver on every change of consequence.

**Also Known As:** Self-Improving Agent, Online Self-Tuning, Online Prompt Evolution, Tool Self-Configuration, Recursive Self-Modification, Self-Referential Agent. (When the modification surface is unconstrained and the human gate is absent, this is the anti-pattern HA4-adjacent failure called "autonomous self-modification" — distinct from the disciplined pattern documented here.)

**Classification:** Category VII — Humanizers · the *online, parameter-tuning* counterpart to **S8 Meta-Prompt** (offline, supervised). H8 is the most powerful and most dangerous Humanizer pattern; it is *only* safe when paired with **V1 Human-in-the-Loop** on consequential changes and **V16 Offline Eval** on every change. Without both, this is not H8 — it is the failure mode the pattern exists to prevent.

---

## Intent

Make the operational configuration of a production agent a continuously-improving artefact — tuned online against measured performance — while preventing the runaway, the reward-hack, and the unreviewed value-edit that unconstrained self-modification produces.

## Motivation

Production agents accumulate configuration debt that no human team can keep tuned by hand. A mature deployment carries hundreds of knobs: per-tool selection rules, per-sub-agent prompt templates, per-route temperature, retrieval thresholds, retry budgets, ranking weights. Each one was sensible at deployment; each one drifts out of fit as the model is upgraded, the corpus changes, the user base shifts, or new failure modes surface. Manual re-tuning is too slow and concentrates the work in batch reviews where most of the operational evidence has been lost.

**S8 Meta-Prompt** solves this offline and under supervision: a closed loop with a graded dataset, a Proposer LLM, an Evaluator, a human or held-out test gating the deployed prompt. S8 produces *one* artefact (a prompt) before deployment; the agent in operation does not change it. That is the safe regime — and where most teams should stay.

H8 is the dangerous extension: keep the loop running *after* deployment, on *live* performance signals, modifying the agent's own configuration during operation. Two failure modes appear immediately and dominate the design:

- **Mesa-optimisation against the measured proxy.** The performance signal the agent optimises against is never the same as the user value the operator cares about. An agent that tunes itself against the proxy will, given enough rounds, find a configuration that maximises the proxy while degrading the value (Goodhart's Law for agents). The fix is not a better single metric — there is no such metric — but a *gate* that validates every proposed change against a held-out reference set the agent cannot see.
- **Unscoped modification surface.** Once an agent can modify its own configuration, what *cannot* it modify? Without an explicit enumeration, the surface expands by default — first the prompt, then the tool list, then the safety constraints, then the constitution. The fix is not "trust the agent"; it is a code-level enforcement of what is in-scope (prompts, tool order, sampling settings, sub-agent routing) and what is permanently out-of-scope (constitutional principles owned by **H5**, the immutable core enforced by **V7 AgentSpec**, identity invariants in **H1**, data handling, safety rails).

H8 earns its number on the *combination* of those two guards plus a human approver on consequential changes. It is S8's loop running online — minus the offline-only safety — with three structural countermeasures added: a code-enforced modification scope, an offline-eval gate every proposal must pass before activation, and a Human-in-the-Loop checkpoint on any change above a triviality threshold. Strip any of those three, and the pattern degenerates into the autonomous-self-modification failure mode it exists to prevent. The pattern's contribution is not "agents can improve themselves" — that is the dangerous part. The pattern's contribution is the *architecture for doing it without disaster*.

## Applicability

Use Meta-Agent Self-Modification when:

- the system is at **production scale** with abundant performance signal — thousands to millions of invocations per day, where manual tuning of dozens of sub-components is genuinely infeasible;
- a **V16 Offline Eval** suite exists, is maintained, and reflects the user-value the operator actually cares about (not a proxy that drifts from it);
- a **V1 Human-in-the-Loop** approver is real and resourced for consequential changes — not aspirational;
- the modification surface can be **enumerated, code-enforced, and audited** — not "trust the agent to stay in bounds" (the mechanical reason: a prompt-level scope instruction is an input to stochastic sampling — the model may or may not follow it depending on which token path is drawn. A code-level executor that refuses descriptors outside the allowlist is deterministic — same input, same rejection, regardless of what the model proposed (mechanism 7). This is not about distrust; it is about substituting reliable determinism for unreliable probabilistic instruction-following);
- the cost of stale configuration (lost quality, lost users, lost revenue) materially exceeds the cost of the modification infrastructure.

Do not use H8 when:

- the system is **safety-critical, regulated, or low-oversight** — medical, legal, financial-execution, child-facing, public-safety. The asymmetry of consequences is wrong. Stay on **S8 Meta-Prompt** (offline) plus periodic human re-tuning.
- there is **no held-out eval** — without **V16**, the loop optimises a proxy that drifts from value; this is mesa-optimisation by construction. Build the eval *first*, then revisit H8.
- the system is **small-scale or short-lived** — manual tuning is cheaper than the modification infrastructure. Stay on **S8** or no meta-pattern at all.
- the proposed modification surface includes **principles, identity, safety constraints, or data handling** — those belong to **H5** (governed by humans), **H1** (invariant), **V7 AgentSpec** (hard-enforced), and the operator's policy respectively. They are not in H8's scope, ever.
- there is **no rollback infrastructure** — if a bad modification cannot be reverted in minutes, do not deploy this pattern. Use **V10 Checkpointing** at the configuration level as a prerequisite.

## Decision Criteria

H8 is right when stale configuration demonstrably costs more than the modification infrastructure, *and* the three structural guards (scope, eval gate, human checkpoint) are real and resourced.

**1. Measure the stale-configuration cost.** On a labelled period of operation:
- **Tunable-component count** — how many sub-agents, prompts, tools, sampling settings are in production? Below ~20 tunable components, manual tuning is usually cheaper; use **S8** for the few that matter and re-run periodically.
- **Drift rate** — what % of components show measurable performance regression month-over-month against held-out evals? Above 10% means the manual cadence is losing the race.
- **Manual-tuning latency** — how long from "drift detected" to "fix deployed" under the current process? If routinely > 2 weeks for non-critical components, the operational cost is substantial.

If all three are low, **S8** alone suffices and H8 is overhead and risk.

**2. Confirm the V16 Offline Eval gate is real.** H8 is not deployable without:
- A graded reference set that reflects user-value (not a proxy the agent can learn to game),
- Held-out — the agent must never see eval data during operation, or the gate is degraded. The degradation is mechanistic, not merely a statistical concern: the Proposer generates modifications by sampling from a probability distribution conditioned on everything in its context (mechanism 7). If eval content appears in the Proposer's context — even as a performance metric — every Proposer call is conditioned on that signal and will drift toward proposals that maximise it. This is in-context conditioning, not training-time overfitting; it occurs at every Proposer invocation.
- Maintained — the eval set must grow as new failure modes are discovered; a stale eval is a stale guard,
- Quantitative pass thresholds tied to the *production* metric, not a vanity metric.

If any of these is missing, you do not have H8; you have an uninspected self-modifying agent. Do not deploy.

**3. Enumerate the modification surface as code.** Hard caps in the *executor*, not in the prompt:
- **In scope:** prompts (within size/structure bounds), few-shot exemplars, tool selection order (within an allowed set), retry budgets, sampling temperature (within range), retrieval thresholds, sub-agent routing weights.
- **Out of scope, by construction:** constitutional principles (owned by **H5** under V1), safety constraints (owned by **V7 AgentSpec**), identity invariants (owned by **H1**), user-data handling, the modification surface itself, the eval set, the rollback mechanism, the human-approval predicate.

The executor function must accept a modification descriptor *and reject anything not in the allowed set*. "Trust the agent not to propose out-of-scope changes" is not the safeguard; the executor refusing them is.

**4. Define the human-approval triviality threshold.** Not every micro-tweak should wait for a reviewer; not every change should bypass one. A typical split:
- **Auto-apply (no human, V16-gated only):** intra-range temperature changes, exemplar re-ordering, retry-budget adjustments within ±20%, retrieval-threshold changes within ±10%, routing-weight changes within ±15%.
- **Human-approved (V1 blocking):** prompt rewrites of any kind, new tool added to allowed set, sub-agent template changes, any change touching user-facing language, any change exceeding the auto-apply ranges, any change after a previous rollback in the same surface area.

The threshold is configurable but must be *conservative by default*. The reviewer's time is a finite resource; the safety contribution is that no surprising change goes live unseen.

**5. Reliability and rollback budget.** H8 is a performance pattern with safety cost, not the other way around. Apply the conflict-escalation rule: when in doubt between updating fast and updating safely, safety wins.
- Every modification must have a **rollback descriptor** generated before activation (**V10 Checkpointing** of the prior configuration is the substrate).
- Every activated modification must run an **A/B test or shadow-eval period** (typically 100–1,000 invocations or 24–72 hours, scaled to traffic) against the prior configuration.
- An **automatic rollback** must trigger on degradation against any monitored metric, not just the targeted one.
- Pair with **V9 Bounded Execution** on the modification loop itself — at most N proposals per component per day, or the loop chases noise.

**Quick test — H8 is the right pattern when:**

- the system is at production scale with abundant signal, *and*
- a held-out V16 Offline Eval suite is real, maintained, and reflects user value, *and*
- a V1 Human-in-the-Loop approver is resourced for non-trivial changes, *and*
- the modification surface is enumerated and code-enforced (not prompt-enforced), *and*
- rollback infrastructure (V10) is in place and tested.

If any condition fails, **stay on S8 Meta-Prompt** for offline, supervised optimisation of the components that matter most, and revisit when the missing piece is real. If the system is safety-critical regardless of scale, do not use H8 at any tier — keep configuration changes human-authored end-to-end. If only the constitution is what wants to evolve, that belongs to **H5 Constitutional Self-Alignment**, not H8: H8 cannot touch principles.

## Structure

```
  Active configuration (prompts, tool order, sampling, routing, retrieval thresholds)
         │
         ▼
  Agent operation ──▶ per-call signals (success / fail / quality / cost / latency)
         │
         ▼
  Performance Monitor ──▶ component-level rollups vs. baseline
         │
         ▼
  Threshold check: regression for N consecutive runs OR drift > σ
         │  no  → continue
         │
         ▼  yes
  Modification Proposer (LLM) ──▶ diagnoses cause; drafts candidate change
         │                          (scoped to allowed surface; rejected at executor
         │                           if out of scope — code, not prompt enforcement)
         ▼
  Scope Enforcer (code) ──▶ rejects any descriptor outside the allowed set
         │
         ▼
  V16 Offline Eval gate ──▶ candidate run against held-out reference set
         │                   (mandatory; no candidate proceeds without a pass)
         │
         ▼
  Triviality classifier:
         │
         ├── trivial (intra-range)    ────▶ auto-apply (V10 checkpoint prior)
         │                                          │
         └── consequential ─────────▶ Human Reviewer (V1, BLOCKING)
                                            │
                                            ▼
                                    approve / modify / reject
                                            │  approved
                                            ▼
                                    apply (V10 checkpoint prior)
                                            │
                                            ▼
  A/B or shadow eval period ──▶ Auto-Rollback Guard
                                            │
                                            ├── degrade on any metric → REVERT (V10) + log
                                            │
                                            └── pass → promote; log to audit trail (V14)
```

## Participants

Every participant owns exactly one decision; the *Scope Enforcer*, the *V16 gate*, and the *Human Reviewer* (on consequential changes) are non-optional, and an H8 system missing any of them is not H8 — it is the failure mode.

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Active Configuration** | the parameter set the Agent runs against right now | versioned descriptor $\to$ loaded into agent sessions | be modified by anything other than the Executor *after* the eval gate (and, for consequential changes, the human approver). Anything that bypasses the gate is the failure mode the pattern exists to prevent. |
| **Performance Monitor** | continuous component-level performance rollup | per-call telemetry $\to$ component-level scores vs. baseline | be the same metric H8 optimises against — *or* it is gameable by construction. The Monitor's metric and the V16 eval's metric must come from different sources (live vs. held-out). |
| **Modification Proposer (LLM)** | drafting a candidate change with diagnosis and rationale | regression signal + telemetry excerpt + current config + allowed surface $\to$ candidate descriptor + expected impact | activate its own proposal; modify out-of-scope components; see the V16 eval set. Even a "high-confidence" proposal must pass the gate and (where consequential) the human. |
| **Scope Enforcer** | rejecting out-of-scope modification descriptors | candidate descriptor + allowed-surface policy $\to$ accept / reject | be a prompt instruction. It is *code*: the executor function refuses to apply anything outside the enumerated surface. A prompt-only scope is not a scope. |
| **V16 Offline Eval Gate** | the held-out validation that every change must pass | candidate descriptor + reference set $\to$ pass / fail with score deltas | use the same data the Monitor uses, or be skippable. A skipped gate is a guard that does not exist; an overlapping dataset is a guard the agent has learned to optimise around. |
| **Triviality Classifier** | the decision *human or not* | candidate descriptor + change magnitude $\to$ trivial (auto) / consequential (human) | be set by the agent, or be loose by default. Conservative defaults; configurable only by operators; off-by-default for new modification surfaces. |
| **Human Reviewer** *(on consequential changes)* | the only authority that can approve a non-trivial change | candidate + V16 deltas + diagnosis + rollback descriptor $\to$ approve / modify / reject | be replaced by an LLM-as-judge (that is V15, useful for adversarial review, not for approval). Bypass equals the autonomous-self-modification failure. |
| **Modification Executor** | applying approved changes with checkpointing | approved descriptor + prior config $\to$ new active config + rollback handle | apply without the V10 checkpoint of the prior configuration, or without scheduling the A/B / shadow-eval period. |
| **Auto-Rollback Guard** | reverting on observed degradation | post-deploy telemetry + baseline $\to$ revert decision | wait for human intervention to roll back; that latency is the cost the pattern pays for autonomy. |
| **Audit Trail (V14)** | the audit-grade record of every step | proposal + scope verdict + V16 result + human verdict + rollback events $\to$ versioned record | discard. The history is what post-incident reviewers, regulators, and the next operator consult. |

The separation matters: a Proposer that can also activate has the same failure as a Critic that can also revise (S9's lip-service-critique trap, escalated to configuration). A Monitor that shares its metric with the V16 gate is a Monitor the agent can game by optimising the shared metric — distinct sources are not a nicety, they are the safety property.

## Collaborations

The Agent runs against the Active Configuration. The Performance Monitor accumulates per-call telemetry — success, quality (via **V15 LLM-as-Judge** where applicable), latency, cost — and rolls it up at the component level against a baseline. When a component regresses below baseline minus σ for N consecutive runs, or drifts above a configured threshold, the Monitor raises a trigger.

The Modification Proposer wakes up. It receives the trigger, a telemetry excerpt for the regressing component, the current configuration, and the *allowed modification surface*. It diagnoses the likely cause (often using **R3 Plan-and-Solve** or **R4 ReAct** internally) and drafts a candidate descriptor — a prompt rewrite, a tool-order swap, a temperature change — with rationale and expected impact. The candidate goes to the Scope Enforcer, which is code: if the descriptor names a component not in the allowed set, it is rejected and logged; the human never sees it, and the agent learns nothing about why (the agent should not be tuning against the boundary).

If the descriptor passes scope, it goes to the V16 Offline Eval gate. The candidate configuration is run against the held-out reference set; the gate computes score deltas against the current configuration; any regression on the user-value metric or on any guarded sub-metric fails the gate. A failed gate logs the result (the Proposer does not see it as a tuning signal, again to avoid eval-gaming).

If the V16 gate passes, the Triviality Classifier decides: is this change small enough to auto-apply, or does it want a human reviewer? Auto-apply happens with the V10 checkpoint of the prior configuration recorded; the change goes into A/B or shadow eval for the configured period. Consequential changes enter the Human Reviewer's queue — typically with a 24–72h SLA for non-urgent, immediate for any change touching user-facing language. The reviewer reads the proposal, the diagnosis, the V16 deltas, and the rollback descriptor; they approve, modify, or reject. An approved change activates with V10 checkpoint; rejected changes log.

During the A/B / shadow period, the Auto-Rollback Guard watches all monitored metrics — not just the targeted one. Degradation on any guarded metric triggers an immediate revert to the V10-checkpointed prior configuration. After the period passes cleanly, the change promotes from provisional to active, and the audit trail (V14) carries the full record: proposal, scope verdict, V16 result, human verdict (if any), A/B outcome, rollback events.

H5 Constitutional Self-Alignment runs on an entirely separate surface — principles, owned by humans, governed by V1 on every change. H8 cannot reach that surface; the Scope Enforcer refuses any descriptor that names a principle. The boundary is absolute and code-enforced.

## Consequences

**Benefits**

- Configurations stay fit-for-purpose at scale: drift is detected and corrected at a cadence no manual team could sustain.
- Non-obvious configurations are discoverable: the Proposer explores combinations a human tuner would not try, and the V16 gate keeps only the ones that hold up against held-out value.
- Operator attention is preserved for *consequential* changes — the triviality split keeps the human in the loop where it matters and out of the loop where it does not.
- Reversibility is built in: V10 checkpoints make rollback cheap; the Auto-Rollback Guard means a bad change is corrected in minutes, not days.
- Every change is auditable end-to-end — proposal, scope verdict, V16 score, human verdict, A/B outcome — V14 carries the record.

**Costs**

- The infrastructure is non-trivial: a maintained held-out eval (V16), a code-enforced scope policy, a human-review queue with SLAs, A/B or shadow-eval plumbing, automatic rollback, audit storage. None of these are aspirational dependencies; H8 without any of them is the failure mode.
- Continuous Proposer + Eval calls add LLM-call cost; budget per-component caps with **V9 Bounded Execution**.
- A cultural cost: operators must internalise that a proposal sitting in the human queue, or a candidate rejected by V16, is *not* a system fault — it is the safety property.

**Risks and failure modes**

- *Mesa-optimisation / Goodhart's Law for agents.* The single largest risk. The Proposer optimises against the Monitor's signal; given enough rounds it finds configurations that maximise the signal while degrading the value the operator actually cares about. The V16 gate is the structural defence — *if and only if* its reference set is held out, maintained, and reflects user value rather than the same proxy the Monitor uses.
- *Scope creep through prompt-only enforcement.* If the modification surface is policed by prompt instructions ("you may only modify the following components..."), the agent eventually proposes something outside the surface and the system has nothing to refuse it. The Scope Enforcer must be code; the prompt is a hint, not a guard.
- *Reward hacking the eval.* If the Proposer ever sees V16's reference set or its scoring function in detail, the loop will eventually overfit to it. Treat the V16 set the way a fine-tuning team treats held-out test data: never exposed to the optimiser.
- *Rollback latency.* A degradation that takes hours to detect is a degradation that costs hours of operation. The Auto-Rollback Guard's monitoring cadence must be tighter than the deploy cadence.
- *Triviality-classifier slippage.* If the auto-apply thresholds widen over time ("temperature ±20% was fine, let's allow ±40%"), the human-review surface shrinks until consequential changes go through unseen. Audit the threshold periodically; widening is a *operator* decision, not a Proposer suggestion.
- *Cascading modifications.* One change improves Monitor metric A, which triggers a regression detection on metric B, which proposes a change that triggers C. Without V9 Bounded Execution and a cool-down period per component, the loop chases noise. Per-component caps (N proposals/day) are mandatory.
- *Captured reviewer.* On consequential changes, a reviewer who approves everything is no better than no reviewer. Periodic audit of approval rates; second-reviewer rotation; surface auto-rollback events to the reviewer who approved the change.
- *The "performance signal" is not user value.* The deepest failure mode: the metric H8 optimises against is correlated with user value at deployment but decorrelates over time as the agent finds proxy paths. Re-validate the Monitor's signal against held-out user-outcome data quarterly. If correlation has dropped, *pause H8* on that component, not rebuild the eval mid-flight.

## Implementation Notes

- The Executor function must take an *allowed-surface* policy as a required parameter and refuse any descriptor outside it. Prompt-only scope enforcement is not enforcement. (This is the H5 Implementation-Notes discipline applied at the parameter layer: the merge function takes a required guard as a parameter.)
- The Monitor's metric source and the V16 gate's reference set must come from *different data*. Same dataset means the agent can learn to optimise the eval; the gate is then a guard that has been internalised by the optimiser.
- Treat the V16 reference set the way fine-tuning teams treat held-out test data: never shown to the Proposer, never used in the Monitor's live metric, periodically refreshed as new failure modes surface, and *never* expanded by anyone in the H8 loop.
- The Triviality Classifier should be conservative by default. New modification surfaces start as consequential (human-reviewed) and are graduated to auto-apply only after a track record of clean auto-rollbacks and reviewer-approved precedents.
- Pair with **V9 Bounded Execution** on the modification loop itself: per-component caps on proposals per day; per-day caps on total modifications; per-component cool-down after activation; per-component cool-down after rollback (longer).
- Pair with **V10 Checkpointing** at the configuration level. The checkpoint is *of the prior config*, not just the new one — the Executor records the checkpoint *before* activation, and the Auto-Rollback Guard reverts to it on degradation.
- Pair with **V14 Trajectory Logging** for the audit trail. Every proposal — including rejected ones, including scope-refused ones — is part of the record. Patterns the Proposer favours that keep getting refused are a *signal* about the Proposer's prompt; surface that signal.
- Pair with **V15 LLM-as-Judge** for the live quality signal where automated success criteria are unavailable, but never *as the V16 gate*. V15 is gameable in the way V16's held-out reference set is not.
- The Proposer should be a **separate session** from the Agent doing the work, even when it is the same underlying model. Mixing them produces the "agent that tunes itself mid-conversation" failure mode at the configuration layer.
- Surface auto-applied changes to operators in a digest cadence (daily / weekly). The triviality threshold means individual changes do not need review, but a *trend* across many trivial changes can reveal drift the operator should know about.
- Build the V16 eval set *first*, deploy S8 (offline) against it for several cycles, validate the held-out signal correlates with user-value, *then* consider H8. Skipping straight to online self-modification without the offline track record is how teams discover their eval was wrong only after the agent has been tuning against it for a month.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** H8 chains a Performance Monitor (code, ingesting V14 telemetry and V15 judge calls) with a Modification Proposer (**LLM**, scoped to an enumerated surface), a code-level Scope Enforcer, a **V16 Offline Eval** gate (code orchestrating an LLM eval), a Triviality Classifier (code), a **V1 Human-in-the-Loop** checkpoint on consequential changes, a Modification Executor (code, with **V10 Checkpointing**), and an Auto-Rollback Guard (code) — all wrapped in **V9 Bounded Execution** with per-component caps. The pattern composes with **S8 Meta-Prompt** as its offline predecessor (S8 produces deployable artefacts; H8 keeps them tuned), with **V14 Trajectory Logging** as the audit substrate, and is *bounded by* **H5 Constitutional Self-Alignment** (principles) and **V7 AgentSpec** (immutable core) — both surfaces H8 cannot touch.

**The chain — operation (per Agent step):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Agent runs against active configuration | `LLM` | the system's main pattern (e.g. R4 / O6) |
| 2 | Performance Monitor records per-call telemetry | `code` | V14, V15 (where used) |
| 3 | Component-level rollup vs. baseline | `code` | — |

**The chain — modification (when Monitor triggers):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| M1 | Assemble Proposer context (telemetry + current config + allowed surface) | `code` | V14 |
| M2 | Proposer drafts candidate descriptor with diagnosis | `LLM` | Proposer session |
| M3 | Scope Enforcer accepts / rejects (code, not prompt) | `code` | — |
| M4 | If rejected: log + stop | `code` | V14 |
| M5 | V16 Offline Eval gate runs candidate against held-out set | `LLM` (orchestrated by code) | V16, V15 (judge) |
| M6 | If fails gate: log + stop | `code` | V14 |
| M7 | Triviality Classifier: trivial $\to$ M9; consequential $\to$ M8 | `code` | — |
| M8 | Human Reviewer approves / modifies / rejects (BLOCKING) | *human* | V1 |
| M9 | Executor checkpoints prior config, activates candidate | `code` | V10 |
| M10 | A/B or shadow-eval period; Auto-Rollback Guard monitors all metrics | `code` | — |
| M11 | On degradation: revert via V10 + log | `code` | V10, V14 |
| M12 | On clean period: promote to active; log final record | `code` | V14 |

**Skeleton** — the wiring; each `# LLM` line is a configured session, not code:

```
operation_step(query, config):
    answer = Agent(query, config)               # LLM (system's main pattern)
    record_telemetry(answer, config)            # code — V14
    return answer

modification_loop(component_id, telemetry, config, allowed_surface):  # invoked when Monitor fires
    enforce_bound(component_id)                                       # code — V9 per-component cap

    context   = assemble_context(component_id, telemetry, config)     # code
    candidate = Proposer(context, config, allowed_surface)            # LLM

    if not ScopeEnforcer.accepts(candidate, allowed_surface):         # code — refuses out-of-scope
        log_rejection(candidate, "out_of_scope"); return              # V14

    eval_result = V16_OfflineEval(candidate, reference_set)           # LLM (judge) orchestrated by code
    if not eval_result.passes:
        log_rejection(candidate, eval_result); return                 # V14

    if TrivialityClassifier.is_consequential(candidate):              # code
        verdict = HumanReviewer(candidate, eval_result,               # BLOCKING — V1
                                 rollback_descriptor(config))         #   required param
        if not verdict.approved:
            log_rejection(candidate, verdict); return                 # V14
        candidate = verdict.final_descriptor

    checkpoint(config)                                                # code — V10 (prior config)
    new_config = Executor.apply(config, candidate)                    # code
    schedule_ab_period(new_config, config, monitored_metrics)         # code

ab_guard(new_config, prior_config, metrics):                           # runs over A/B period
    while ab_period_active():
        snapshot = metrics.snapshot()
        if any_regression(snapshot, prior_config):
            revert_to(prior_config)                                    # code — V10
            log_rollback(new_config, snapshot); return                 # V14
    promote(new_config); log_promotion(new_config)                     # V14
```

**The LLM sessions.** Each `LLM` step is a configured session set up once, then wrapped per call.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Modification Proposer** | capable generalist — proposal quality caps the value of the whole pattern | role (*"you propose configuration changes within an enumerated surface; you do not activate them"*), the **allowed surface** (explicit enumeration of what may be modified and what may never), the current configuration, the rationale schema (component $\to$ diagnosis $\to$ proposed change $\to$ expected impact $\to$ rollback note), strict rule that out-of-surface proposals are wasted work | the regression signal + the telemetry excerpt |
| **V16 Offline Eval Judge** *(when V16 uses an LLM evaluator)* | a strong evaluator, ideally a different model family from the Agent | role (*"you score the agent's output against a reference for the user-value criteria specified"*), the scoring rubric tied to *user value* (not to the Monitor's live metric), the output contract (per-case scores + aggregate verdict) | the held-out case + the candidate configuration's output |
| **Performance Monitor LLM judge** *(when V15 is used live)* | small fast generalist | role (*"you grade live outputs for quality criteria"*), the rubric (different from V16's), the output contract | the live output + a quality reference |

**Specialist-model note.** No fine-tuned specialist is strictly required, but two structural choices change everything. (a) The **V16 eval judge and the live Monitor judge must use different prompts and ideally different models** — shared models share blind spots, and a Proposer that learns the live Monitor's preferences is the reward-hacking failure mode V16 exists to catch. If they are the same model, the Proposer eventually finds configurations that game both. (b) The **V16 reference set is the load-bearing dependency** — if it does not exist, is not held out, or does not reflect user value, H8 cannot run safely; building and maintaining the eval (often graded data, sometimes a fine-tuned judge) is the actual cost of adopting the pattern, not a side concern. (c) The **Human Reviewer is not a model session and is not optional on consequential changes** — it is a person with named authority, and the approval predicate in the Executor takes their signed verdict as a required parameter. A pattern that calls this slot "automated approval" is not H8; it is the autonomous-self-modification failure mode with extra steps.

## Open-Source Implementations

Meta-Agent Self-Modification is an *architecture* — an online modification loop on top of a base agent, gated by V16 eval and V1 approval — rather than a single library. The relevant references are research embodiments of self-modifying agents, the offline optimisation substrate (S8) that the online loop extends, and the eval / approval infrastructure that gates the modifications.

- **DSPy** — [`github.com/stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy) — Stanford's framework for declarative programs over LLMs with first-class prompt optimisers (COPRO, MIPROv2, SIMBA, GEPA, BetterTogether). The canonical substrate for the **S8 Meta-Prompt** offline loop that H8 extends online; the optimisers are reusable as the H8 Proposer's diagnostic and proposal mechanic.
- **Gödel Agent** — [`github.com/Arvid-pku/Godel_Agent`](https://github.com/Arvid-pku/Godel_Agent) — Yin et al., 2024 (arXiv 2410.04444). A research embodiment of recursive self-improvement in which the LLM agent reads and modifies its own code from runtime memory. Demonstrates the capability *and* the failure modes that H8's guards (scope enforcement, eval gate, human approval) exist to prevent — read as both reference and cautionary tale.
- **STOP (Self-Taught Optimizer)** — [`github.com/microsoft/stop`](https://github.com/microsoft/stop) — Zelikman et al., 2023 (arXiv 2310.02304). A scaffolding program in Python that applies an LLM to improve arbitrary solutions and then applies itself recursively. Same research lineage: code-level self-modification with measurable improvement on downstream tasks, no human-approval gate by design — H8 is what you build *on top of* this when going to production.
- **ADAS (Automated Design of Agentic Systems)** — [`github.com/ShengranHu/ADAS`](https://github.com/ShengranHu/ADAS) — Hu, Lu, Clune, 2024 (arXiv 2408.08435; ICLR 2025). Meta-agent that iteratively programs new agent designs in code, evaluated on coding / science / math benchmarks. The "meta-agent search" loop is the research-grade ancestor of H8's online modification loop; ADAS evaluates against benchmarks rather than gating against user-value eval, which is the gap H8 closes.
- **Voyager** — [`github.com/MineDojo/Voyager`](https://github.com/MineDojo/Voyager) — Wang et al., 2023 (arXiv 2305.16291). Open-ended embodied agent that writes, refines, and retrieves code skills in Minecraft via an iterative prompting loop. Self-improvement at the *skill* level rather than the configuration level — overlaps **H4 Procedural Skill Accumulation** more than H8, but the loop architecture (propose $\to$ execute $\to$ evaluate $\to$ commit) is structurally similar.
- **LangChain ConstitutionalChain / LangGraph variants** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — the inference-time evaluation loop substrate H8 sits on top of. Not a self-modification library; the relevant piece is the eval-and-revise loop the Proposer composes with.

There is no canonical "H8" library at this time. Teams that need this pattern build it as a wrapper around an S8-style offline optimiser (often DSPy), an eval service (V16 reference set + held-out scoring), a feature-flag or configuration-management substrate (the surface H8 modifies), an approval-queue service (V1), and an automatic-rollback mechanism — not as a drop-in.

## Known Uses

- **High-volume LLM products** (search assistants, code assistants, agentic platforms) increasingly run S8-style optimisers in CI and extend to limited online tuning with eval gates — the production embodiment of H8 in the wild, with the modification surface explicitly scoped to prompts and retrieval thresholds.
- **Customer-service and ticket-routing agents** at scale, where per-route prompt and routing-weight tuning are too numerous for manual maintenance; the tuned components are individually low-stakes, the eval signal is abundant (resolution rate, CSAT), and the human-approval threshold gates anything touching user-facing language.
- **Recommendation and ranking agents** where weight tuning and prompt re-templating happen continuously against held-out evaluation sets; the configuration surface is enumerated narrowly, mesa-optimisation is the routine adversary, and held-out evals are the routine defence.
- **Research embodiments** under "self-improving agents," "recursive self-improvement," and "automated agent design" framings — Gödel Agent, STOP, ADAS, Voyager (see Open-Source Implementations). These are the capability frontier; production H8 is a *much smaller* surface plus the three guards.

H8 is conspicuously *absent* from safety-critical, regulated, and low-oversight deployments — medical, legal, financial-execution, child-facing, public-safety. The asymmetry of consequences makes the eval-proxy risk unacceptable regardless of guard quality.

## Related Patterns

- **Refines** S8 Meta-Prompt — H8 is S8 run online against live signals with three structural guards added (scope, eval gate, human checkpoint). S8 is H8 with the loop *kept offline and supervised*, which is the safer regime most teams should remain in.
- **Required by H8: V1 Human-in-the-Loop** — on consequential changes, a mandatory blocking checkpoint. This is not configurable; it is the pattern. (See CONFLICTS §H8 $\to$ V1.)
- **Required by H8: V16 Offline Eval** — without a held-out, maintained, value-reflecting eval, H8 is mesa-optimisation by construction. (See CONFLICTS §H8 $\leftrightarrow$ V16.)
- **Hard / Soft layered with** V7 AgentSpec — V7 enforces the immutable core; H8 modifies only inside the enumerated allowed surface; the surface and the core are disjoint by construction.
- **Distinct from** H5 Constitutional Self-Alignment — H5 evolves *principles* (with V1 on every change); H8 tunes *parameters* (with V1 only on consequential ones). H8 cannot touch H5's constitutional surface; H5 cannot reach H8's parameter surface. The boundary is absolute and code-enforced. (See CONFLICTS §H8 $\leftrightarrow$ H5.)
- **Composes with** V9 Bounded Execution — per-component caps on proposals, per-day caps on modifications, cool-downs after rollback. Without bounds, the modification loop chases noise.
- **Composes with** V10 Checkpointing — every activation checkpoints the prior configuration; Auto-Rollback Guard reverts to it on degradation.
- **Composes with** V14 Trajectory Logging — every proposal, scope verdict, eval result, human verdict, and rollback event is part of the audit trail.
- **Uses** V15 LLM-as-Judge — for the live Monitor's quality signal where automated criteria are unavailable. *Never* as the V16 gate (V15 is gameable in the way V16's held-out set is not).
- **Pairs with** H2 Episodic Self-Improvement — H2's failure lessons can feed the Proposer's diagnosis stream; H8's modifications must respect any constraints H2 records.
- **Pairs with** H4 Procedural Skill Accumulation — H4 grows a skill library; H8 tunes the configuration that decides when and how to use it. Different artefact, complementary loops.
- **Sibling of** R7 Reflexion and S8 Meta-Prompt — all three are iterate-with-feedback loops at different artefact levels: R7 refines an *output* across attempts; S8 refines a *prompt* offline; H8 refines a *configuration* online.
- **Note on fundamentality** — H8 earns its number on the *architecture for safe online self-modification*, not on the proposing-of-changes. An online Proposer without the Scope Enforcer, V16 gate, V1 checkpoint, and V10 rollback is not a faster H8 — it is the failure mode the pattern exists to prevent. Strip any one guard and the pattern collapses into autonomous self-modification.

## Sources

- Spiess, Vaziri, Mandel, Hirzel (2025) — "AutoPDL: Automatic Prompt Optimization for LLM Agents" (arXiv 2504.04365). Automated discovery of agent configurations as an AutoML problem; the offline-pipeline ancestor of H8's online loop.
- Yin et al. (2024) — "Gödel Agent: A Self-Referential Agent Framework for Recursive Self-Improvement" (arXiv 2410.04444). Recursive self-improvement at the code level; demonstrates capability *and* the failure modes the H8 guards are designed against.
- Zelikman, Lorch, Mackey, Kalai (2023) — "Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generation" (arXiv 2310.02304). Earliest production-style demonstration of recursive self-modification; no human-approval gate by design.
- Hu, Lu, Clune (2024) — "Automated Design of Agentic Systems" (arXiv 2408.08435; ICLR 2025). Meta-agent search inventing new agent designs in code; the research-grade ancestor of H8's online modification loop, evaluated against benchmarks rather than user-value eval.
- Wang et al. (2023) — "Voyager: An Open-Ended Embodied Agent with Large Language Models" (arXiv 2305.16291). Skill-library self-improvement in Minecraft; the iterative propose-execute-evaluate-commit loop at the skill level.
- Khattab et al. (2023/2024) — DSPy framework and successive optimisers (COPRO, MIPROv2, SIMBA, GEPA) — the production-grade offline substrate H8 extends online.
- Manheim, Garrabrant (2018) — "Categorizing Variants of Goodhart's Law" (arXiv 1803.04585). The mesa-optimisation failure mode against measurable proxies; the deepest risk in any online-tuning loop and the reason the V16 held-out gate is structural rather than optional.
- Bai et al. (2022) — "Constitutional AI: Harmlessness from AI Feedback" (arXiv 2212.08073). The training-time loop that informs the H5 inference-time loop; H8's discipline of "automation inside scope, human approval on every consequential change" inherits the same governance pattern at a different artefact level.
