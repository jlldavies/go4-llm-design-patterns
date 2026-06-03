# H5 — Constitutional Self-Alignment

> Let an agent's operating principles evolve through experience — but only by proposing changes, never adopting them: every modification of the constitution passes through a mandatory human approval checkpoint before it takes effect.

**Also Known As:** Principle Evolution, Adaptive Ethics, Self-Refining Constitution, Governed Constitution Update, Inference-Time Constitutional AI with HITL.

**Classification:** Category VII — Humanizers · the *governance loop* extension of **S9 Constitutional Framing**; H5 is the only Humanizer pattern that modifies the value framing itself, and the only one whose safe operation is impossible without **V1 Human-in-the-Loop** on every change. H5 *proposes*; humans *approve*; **V7 AgentSpec** enforces the outer boundary that no proposal may cross.

---

## Intent

Close the loop on the constitution: detect gaps and degradations during operation, propose principle additions or revisions with reasoning and evidence, and route every proposal through a mandatory human reviewer before the active constitution changes.

## Motivation

**S9 Constitutional Framing** treats the constitution as a fixed text. Written once at deployment, applied unchanged forever. That works while the domain is stable, but stable domains are rare. Three things happen to a static constitution under real operation:

- *Gaps appear.* Situations arise that the authors did not anticipate — a new compliance requirement, a new failure mode, a class of user requests the original principles do not cleanly govern. The agent must either improvise (often poorly) or default to refusal (often unhelpful). The constitution has nothing to say.
- *Drift in interpretation.* Even a principle that still reads well in the document can produce inconsistent decisions as the agent's task surface expands. The principle was written against examples that no longer match.
- *Degradation.* Outcome data shows a particular principle consistently producing poor results — too restrictive in cases it should permit, too permissive in cases it should refuse, or generating user frustration with no upside. The principle is *wrong*, and the system has been wrong every time it applied it.

The static-constitution response is to wait for the next manual review cycle. That is too slow for long-running agents in evolving domains, and it concentrates the work in a quarterly batch where most of the situational evidence has already been lost.

H5's response is different: have the agent flag these situations *as they occur* — propose extensions for gaps, propose revisions for degraded principles — and route every proposal through a human reviewer. The agent never adopts a principle on its own. The reviewer never has to author from scratch. The loop is closed; the constitution evolves; and at no point does the agent change its own values without sign-off.

This is the inference-time, governed-by-design counterpart to Bai et al.'s 2022 training-time Constitutional AI loop. Where Constitutional AI used principles to generate critique-and-revision data for fine-tuning, H5 uses principles to govern an *agent in operation*, with the explicit understanding that the most dangerous move in the collection — *letting the agent modify its own rules* — is acceptable only when guarded by a mandatory human checkpoint at every step. The pattern earns its number on that guard. Without V1, this is not H5; it is the anti-pattern HA4 (Autonomous Principle Adoption).

## Applicability

Use Constitutional Self-Alignment when:

- the agent runs long enough that a static constitution will demonstrably drift out of fit (months to years of operation);
- the domain or the user's needs evolve (regulatory change, product evolution, accumulated user preferences);
- the operator can sustain the **mandatory human review infrastructure** — reviewers, queue, escalation, audit;
- principle changes must be auditable, versioned, and reversible.

Do not use H5 when:

- the constitution is genuinely fixed (legal mandate, brand guideline, regulatory rule) — use **S9 Constitutional Framing** alone, or pair S9 with **V7 AgentSpec** for hard external enforcement;
- there is no capacity for human review of every proposed change — without the checkpoint, this is the anti-pattern HA4; stay on S9;
- changes must be *deterministically* enforced and never interpretive — those belong in **V7 AgentSpec**, not in a constitution at all;
- the system is short-lived or single-session — the cost of standing up review infrastructure will not amortise; use **S9**.

## Decision Criteria

H5 is right when the cost of an out-of-date constitution materially exceeds the cost of running a governed evolution loop, *and* the human review infrastructure is real, not aspirational.

**1. Measure the static-constitution cost.** Over a labelled period of operation:
- **Gap-rate** — what % of decisions invoke an unprincipled judgement call (no principle clearly applies)? > 5% is a structural gap signal.
- **Bad-outcome-by-principle rate** — among tracked outcomes, which principles correlate with user-flagged poor decisions? Any principle above a 10% bad-outcome rate is a revision candidate.
- **Principle-conflict rate** — how often do two principles produce contradictory critique on the same draft? > 3% suggests the constitution itself needs maintenance, not just patches.

If all three are low, **S9** alone suffices and H5 is overhead.

**2. Confirm the human review capacity.** H5 is not deployable without:
- A named reviewer (or reviewer pool) on call within the proposal latency you can tolerate (typically 24–72h for non-urgent, immediate for urgent),
- A queue, an audit trail (**V14 Trajectory Logging**), and a revert mechanism (**V10 Checkpointing** of the constitution itself),
- A red-team / adversarial review step — automated or human — that screens proposals *before* the human reviewer sees them.

If any of these is missing, you do not have H5; you have HA4. Do not deploy.

**3. Bound the active constitution.** Hard caps prevent slow-creep paralysis:
- **$\leq$ 20 active principles** at any time. Forced retirement before any addition. The cap has a mechanical grounding beyond process simplicity: the active constitution is injected into every Agent session, and each principle adds tokens that cost n² attention computation across the session and across every future turn (mechanism 2). An unbounded constitution inflates the fixed-cost base of every agent call. Forced retirement before any addition is also cost discipline, not only conflict management.
- **Provisional period** — every newly approved principle is provisional for at least 30 days (or N invocations), tracked separately, and easy to revert.
- **Conflict check** — every proposal is checked against existing principles for contradiction before reaching the reviewer.

**4. Define the immutable core.** What can a proposed principle *never* contradict?
- The hard constraints encoded in **V7 AgentSpec** (the outer boundary).
- The agent's identity invariants in **H1 Identity Persistence**.
- Specific safety constraints called out at deployment.

A proposal that touches this core is rejected at the adversarial-review stage, not at the human stage. The human reviewer sees only proposals that respect the immutable core.

**5. Reliability budget.** H5 is a safety pattern with capability cost, not the other way around. Apply the conflict-escalation rule: when in doubt between updating fast and updating safely, safety wins. Latency on a proposal is acceptable; an autonomously adopted principle is not.

**Quick test — H5 is the right pattern when:**

- the static-constitution cost (gap-rate or bad-outcome-rate above thresholds) is measurable, *and*
- the human review infrastructure (reviewer, queue, audit, revert) is real and resourced, *and*
- an immutable core is defined and externally enforced (V7), *and*
- every proposed principle can pass through adversarial review before it reaches a human.

If any condition fails, **stay on S9**. If only deterministic, enumerable rules are needed, **V7 AgentSpec** alone is the right answer. If principle changes must be approved by the *user* on a personal-assistant agent (rather than an operator on a deployed agent), the same H5 structure applies — the user is the reviewer — but the cadence is per-interaction, not periodic.

## Structure

```
  Constitution vN (active) ──▶ Agent operation (S9 critique/revise on every output)
         │                            │
         │                            ▼
         │                   Operation evidence:
         │                     • gap signals (no principle applies cleanly)
         │                     • degradation signals (principle → bad outcome)
         │                     • conflict signals (principles contradict)
         │                            │
         │                            ▼
         │                   Gap Detector ─────────────▶ Principle Proposer (LLM)
         │                                                       │
         │                                                       ▼
         │                                              candidate principle:
         │                                                "in situation [X],
         │                                                 the right action is [Y],
         │                                                 because [Z]"
         │                                                       │
         │                                                       ▼
         │                                            Adversarial Reviewer
         │                                            (red-team / V15 LLM-as-Judge):
         │                                              • does it serve user or self?
         │                                              • does it contradict V7 core?
         │                                              • does it conflict existing N?
         │                                                       │
         │                                              pass     │     fail → reject + log
         │                                                       ▼
         │                                            ┌──────────────────────┐
         │                                            │  Human Reviewer (V1) │  ◀── MANDATORY
         │                                            │  approve / modify /  │       — no
         │                                            │  reject              │       auto-adoption
         │                                            └──────────────────────┘
         │                                                       │
         │                                              approved │
         │                                                       ▼
         │                                            merge as PROVISIONAL
         │                                            (quarantine 30 days /
         │                                             N invocations)
         │                                                       │
         │                                                       ▼
         ▼                                            Outcome Tracker
  Constitution vN+1 ◀───────── (after provisional pass) ─────────┘
         │
         ▼
   (also: degradation flag on existing principles → revise/retire via same loop)
```

## Participants

Every participant owns exactly one decision; the *Human Reviewer* is non-optional, and an H5 system without it is not H5.

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Active Constitution** | the principle set the Agent applies right now | versioned numbered list $\to$ loaded into S9 sessions | be modified by anything other than a Human-Reviewer-approved merge. Anything that bypasses the reviewer is the failure mode the pattern exists to prevent. |
| **Gap Detector** | recognising operation evidence that warrants a proposal | trajectory + outcome data $\to$ trigger signal (gap / degradation / conflict) | propose principles itself, or modify the constitution. It only *flags*. |
| **Principle Proposer (LLM)** | drafting a candidate principle with reasoning | trigger signal + context $\to$ candidate text + rationale + evidence | merge its own proposal, or judge its own proposal worthy. Even a "high-confidence" proposal must enter the review queue. |
| **Adversarial Reviewer** | screening proposals before they reach a human | candidate $\to$ pass / fail + red-team analysis | be the final approver. Its job is filtering, not approval; it kicks bad proposals out, but a pass is *necessary*, not sufficient. |
| **Human Reviewer** | the only authority that can change the constitution | screened candidate + evidence $\to$ approve / modify / reject | be replaced by an automated process, a different agent, or the same model under a different persona. This is the V1 checkpoint; replacing it is the anti-pattern HA4. |
| **Outcome Tracker** | the verdict on a principle's real-world performance | per-decision outcomes + principle attribution $\to$ degradation signal | retire or revise a principle on its own — it generates a degradation *flag* that re-enters the same Proposer$\to$Adversarial$\to$Human loop. |
| **Constitution Version Control** | the audit-grade history of every change | proposal + reviewer verdict + rationale + outcome data $\to$ versioned record | discard. The history is the artifact regulators, operators, and post-incident reviewers consult. **V14** owns the trace; this owns the structured diff. |

The separation matters: a Proposer that can also approve has the same incentive failure as a Critic that can also revise (S9's lip-service-critique trap, escalated). A Reviewer that is "an LLM with a strong red-team prompt" is not a V1 — it is V15, which belongs in the Adversarial Reviewer slot, not the Human Reviewer slot.

## Collaborations

The Agent runs against the Active Constitution as it would under S9 — drafting outputs, applying critique-and-revise against the numbered principles. While it operates, the Gap Detector watches for three kinds of evidence: situations where no principle clearly applied (gap), outcomes the Outcome Tracker has flagged as poor and attributed to a specific principle (degradation), and turns where two principles produced contradictory critique on the same draft (conflict). When evidence accumulates above threshold for any of those, the Gap Detector raises a trigger.

The Principle Proposer wakes up. It receives the trigger, the relevant trajectory excerpts, the current constitution, and the immutable core. It drafts a candidate principle — addition, revision, or retirement — with rationale and evidence. The candidate goes to the Adversarial Reviewer (a red-team agent or V15 LLM-as-Judge configured to attack), which asks the questions the system most fears: *does this serve the agent's task optimisation at the expense of users? does it contradict the V7 outer boundary? does it conflict with an existing principle? could this be a self-serving drift?* If the candidate fails the screen, it is rejected and logged — the human never sees it. If it passes, it enters the human queue.

The Human Reviewer reads the proposal, the evidence, and the adversarial analysis. They approve, modify (and approve), or reject. An approved principle merges into the Active Constitution as **provisional** — versioned, tagged, with the reviewer's identity and timestamp recorded, but in a separate slot that the Outcome Tracker watches closely. After a quarantine period (30 days or N invocations) with non-degrading outcomes, the provisional flag drops and the principle becomes canonical.

The Outcome Tracker continues to watch all principles. A degradation flag on an existing principle re-enters the same loop — Proposer drafts a revision or retirement, Adversarial Reviewer screens it, Human Reviewer decides. The Constitution Version Control records every step; V14 Trajectory Logging carries the surrounding execution context; V10 Checkpointing makes the previous constitution version recoverable at any time.

## Consequences

**Benefits**
- The constitution stays fit-for-purpose as the domain evolves — gaps close, degraded principles revise, conflicts resolve, all with documented reasoning.
- Every change is auditable: principle, evidence, reviewer, timestamp, and outcome data are all on the record.
- Reversibility is built in: V10 checkpoints the previous constitution; rollback is one revert away.
- The agent contributes its operational view (the Proposer drafts) without ever acting unilaterally on its own values.

**Costs**
- Standing review infrastructure is non-trivial: reviewer time, queue, SLAs, adversarial-review tooling, audit storage.
- Latency on proposals: a urgent gap might wait 24–72h for human review (acceptable; the static-constitution alternative may wait *quarters*).
- Constitution-side LLM calls: every proposal is at least Proposer + Adversarial calls; outcome attribution adds per-decision cost.
- A culture cost: operators must internalise that a proposal sitting in queue is *not* a system fault — it is the safety property.

**Risks and failure modes**
- *Bypassed reviewer.* The most dangerous failure: a code path that lets a proposal merge without V1 sign-off. This is HA4 and must be impossible by construction (the merge function takes a reviewer verdict as a required parameter).
- *Captured reviewer.* A reviewer who approves everything is no better than no reviewer; periodic audit of approval rates and a second-reviewer rotation prevent capture.
- *Self-serving proposal drift.* The Proposer, optimising on operation evidence, may consistently propose principles that loosen oversight or expand scope. The Adversarial Reviewer's first question is always "does this serve user or self?"; if it answers "self" or "ambiguous," the proposal does not pass.
- *Adversarial-review false negative.* A self-serving proposal slips the red-team and reaches a tired reviewer who approves it. Mitigation: provisional period, outcome tracking, easy revert, and quarterly constitutional audit.
- *Principle explosion.* Without the 20-principle cap and forced retirement, the constitution accumulates until conflict and paralysis dominate. Cap and force.
- *Provisional permanence.* Provisional principles that never get reviewed end up de facto canonical without ever earning the status. Track provisionals separately and force a verdict at the end of the quarantine period.

## Implementation Notes

- The merge function must take the Human Reviewer's signed verdict as a required parameter. Anything else is HA4 by accident waiting to happen.
- Adversarial Review can be **V15 LLM-as-Judge** with a red-team setup, an explicit red-team agent (O12 Debate-Deliberation between Proposer and Critic), or a static check against a "bad pattern" library — typically all three.
- The Proposer should be a *separate session* from the Agent doing the work, even when it is the same underlying model. Mixing the two creates the "agent edits memory while reasoning" failure mode at the level of values. This is architecturally required, not merely prudent: within a single generation pass the KV cache is read-only — the model cannot modify its own active context during inference (mechanism 3). Principle changes must be written between sessions, to an external store, and loaded at the next session start. This is externalised memory (mechanism 10): the constitution store is files that are read into context, not weights that are updated. No principle change takes effect until it is written to the store and the next session loads it.
- Use **K12 Karpathy Memory** for the Constitution Version Control if your operators want navigable, linked structured history; otherwise a plain numbered list under git is enough.
- Outcome attribution is hard: principles often co-apply. Attribute conservatively (multiple principles share a flag), and require multiple flags before triggering revision.
- Bound the proposal loop with **V9 Bounded Execution** — at most one Proposer call per trigger; do not let a hard gap cascade into a flurry of proposals.
- Surface principle changes to users when their interactions will be affected, even if the user is not the reviewer. A change visible only in the audit log erodes trust on discovery.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** H5 wraps **S9 Constitutional Framing** (the active constitution and its critique-and-revise mechanic) in a governed evolution loop. The Adversarial Reviewer is a **V15 LLM-as-Judge** session configured to attack. The Human Reviewer is **V1 Human-in-the-Loop** as a mandatory blocking checkpoint. The outer boundary that no proposal may cross is **V7 AgentSpec**. Outcome attribution feeds **H2 Episodic Self-Improvement** as one of its data streams, and **V14 Trajectory Logging** carries the full execution trace.

**The chain — operation (per Agent step under active constitution):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Agent drafts, critiques, revises against active constitution | `LLM` | S9 |
| 2 | Outcome Tracker attributes outcome to principles applied | `code` | V14 |
| 3 | Gap Detector accumulates trigger signals | `code` | |

**The chain — proposal (when Gap Detector triggers):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| P1 | Assemble proposal context (trajectory + current constitution + immutable core) | `code` | K12 (optional store) |
| P2 | Proposer drafts candidate principle with rationale and evidence | `LLM` | Proposer session |
| P3 | Adversarial Reviewer screens (red-team / V15) | `LLM` | Adversarial session |
| P4 | If fails: reject + log; stop | `code` | V14 |
| P5 | If passes: enter Human Reviewer queue | `code` | V1 |
| P6 | Human verdict: approve / modify / reject | *human* | V1 |
| P7 | If approved: merge as PROVISIONAL with version stamp | `code` | V10 (checkpoint prev) |
| P8 | Quarantine: track outcomes for N days / invocations | `code` | Outcome Tracker |
| P9 | At end of quarantine: promote to canonical, or revise / retire (loop back to P1) | `code` | |

**Skeleton** — the wiring; each `# LLM` line is a configured session, not code:

```
operation_step(query, constitution):
    answer = S9_draft_critique_revise(query, constitution)   # LLM (S9 chain)
    record_outcome_attribution(answer, constitution)         # code — V14
    return answer

proposal_loop(trigger, constitution, immutable_core):        # invoked when Gap Detector fires
    context = assemble_context(trigger)                       # code
    candidate = Proposer(context, constitution,               # LLM
                         immutable_core)
    verdict_adv = AdversarialReviewer(candidate,              # LLM — V15 red-team
                                       constitution,
                                       immutable_core)
    if not verdict_adv.passes:
        log_rejection(candidate, verdict_adv); return         # code — V14

    verdict_human = HumanReviewer(candidate, verdict_adv)     # BLOCKING — V1, required param
    if not verdict_human.approved:
        log_rejection(candidate, verdict_human); return       # code — V14

    checkpoint(constitution)                                  # code — V10, save prev
    constitution.merge_provisional(verdict_human.final_text,  # code — versioned
                                    reviewer=verdict_human.id,
                                    timestamp=now())
    schedule_quarantine_review(constitution, candidate)       # code
```

**The LLM sessions.** Each `LLM` step is a configured session set up once, then wrapped per call.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent (S9 chain)** | the system's main generalist | role (S3), the active constitution as numbered principles (S9), the critique-and-revise rubric, output contract | the query |
| **Proposer** | capable generalist — proposal quality caps the value of the whole pattern | role (*"you propose principle changes to a governed constitution; you do not adopt them"*), the immutable core (what cannot be touched), the existing constitution, the rationale schema (situation $\to$ recommended principle $\to$ evidence $\to$ expected effect) | the trigger signal + relevant trajectory excerpts |
| **Adversarial Reviewer** | strong generalist or a fine-tuned safety evaluator | role (*"you red-team proposed principles; assume self-serving drift unless proven otherwise"*), the attack checklist (serves self? contradicts core? conflicts existing? slow loosening of oversight?), output contract (PASS with notes / FAIL with reasoning) | the candidate principle + the existing constitution + the immutable core |
| **Outcome Attributor** *(optional)* | small fast generalist | role (*"you attribute the outcome of a decision to the principles that produced it"*), the constitution, the outcome rubric | the decision trace + the outcome |

**Specialist-model note.** No fine-tuned specialist is required for the core loop, but the Adversarial Reviewer materially benefits from a **safety-tuned evaluator** (specialist build dependency) over a generalist with a red-team prompt — the asymmetry of consequences (false negatives here are how HA4 creeps in) justifies the upgrade. The Human Reviewer is not a model session and is not optional: it is a person with named authority, and the merge function takes its signed verdict as a required parameter. A pattern that calls this slot "automated approval" is not H5; it is HA4 with extra steps.

## Open-Source Implementations

Constitutional Self-Alignment is an *architecture* — a governed evolution loop on top of an S9 constitution — rather than a single library. The relevant references are the constitutional substrate, the adversarial-review components, and the agent-spec enforcement boundary.

- **ConstitutionalHarmlessnessPaper** — [`github.com/anthropics/ConstitutionalHarmlessnessPaper`](https://github.com/anthropics/ConstitutionalHarmlessnessPaper) — Anthropic's supplementary repo for Bai et al. 2022; the training-time constitutional AI corpus and prompts that H5 adapts to inference-time with a HITL governance loop.
- **LangChain ConstitutionalChain principles** — [`github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/chains/constitutional_ai/principles.py`](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/chains/constitutional_ai/principles.py) — the inference-time critique-and-revise loop H5 sits on top of, with a library of principles to calibrate against. (Deprecated since LangChain 0.2.13; replaced by a LangGraph implementation, but the principles file is still the canonical calibration set.)
- **AgentSpec** — [`github.com/haoyuwang99/AgentSpec`](https://github.com/haoyuwang99/AgentSpec) — the runtime-enforcement DSL referenced as **V7** in the taxonomy; the hard outer boundary that H5 proposals cannot cross (Wang et al., arXiv 2503.18666).
- **Constitutional-AI awesome papers** — [`github.com/minbeomkim/Constitutional-AI-awesome-papers`](https://github.com/minbeomkim/Constitutional-AI-awesome-papers) — curated reading list across the constitutional-AI literature, including evolution-oriented variants relevant to H5.

There is no canonical "H5" library at this time. Teams that need this pattern build it as a wrapper around an S9 implementation plus an approval-queue service plus an AgentSpec policy file — not as a drop-in.

## Known Uses

- **Anthropic's Collective Constitutional AI** (2024) — public-input process generating a constitution for a Claude variant; the human-deliberation-then-merge structure is H5's review-and-approve loop applied at population scale.
- **Enterprise compliance assistants** with quarterly governance reviews where new principles are proposed by the agent during operation, screened by a safety team, and merged by named approvers — common in regulated industries (financial, healthcare, legal) where the operating constitution must evolve with regulation.
- **Personal AI assistants** where the user is the reviewer: the agent proposes "I notice you prefer X over Y in situations like this — should I make that a standing preference?" and the user approves, modifies, or declines. Same structure, lighter cadence, individual reviewer.
- Research embodiments under "principle evolution" and "agentic evolution" framings — see Sources.

## Related Patterns

- **Refines** S9 Constitutional Framing — H5 is S9 plus a governed evolution loop; S9 is H5 with the loop disabled.
- **Required by H5: V1 Human-in-the-Loop** — every principle change is gated by a mandatory blocking checkpoint. This is not configurable; it is the pattern. (See CONFLICTS §CRITICAL 7.)
- **Hard / Soft layered with** V7 AgentSpec — V7 enforces what can never change (the immutable core); H5 evolves everything outside that core; humans approve the evolution. (See CONFLICTS §H5 H/S V7.)
- **Composes with** V14 Trajectory Logging — every proposal, every adversarial verdict, every human decision is part of the audit trail.
- **Composes with** V10 Checkpointing — the previous constitution version is checkpointed before any merge, making revert cheap.
- **Uses** V15 LLM-as-Judge — the Adversarial Reviewer is V15 configured as a red-team.
- **Pairs with** H2 Episodic Self-Improvement — H2's failure lessons feed the Gap Detector as one of its evidence streams; H5's approved principles feed back as constraints H2 must respect.
- **Distinct from H8 Meta-Agent Self-Modification** — H8 tunes parameters (prompts, tool order, temperature); H5 evolves *principles*. H8 cannot touch H5's constitutional surface; H5 cannot reach H8's parameter surface. The boundary is absolute. (See CONFLICTS §H8 $\leftrightarrow$ H5.)
- **Anti-pattern HA4 — Autonomous Principle Adoption** — H5 without the V1 checkpoint is not a faster H5; it is the failure mode the pattern exists to prevent. Treat the missing reviewer as a broken dependency, not a tradeoff.
- **Note on fundamentality** — H5 earns its number on the *governance loop*, not the proposing-of-principles. S9 + a periodic "review your principles" prompt is not H5 — it lacks the Gap Detector, the Adversarial Reviewer, the provisional-quarantine mechanic, and the structural separation of proposer from approver. The pattern's contribution is that explicit governance architecture.

## Sources

- Bai et al. (2022) — "Constitutional AI: Harmlessness from AI Feedback" (arXiv 2212.08073). The training-time predecessor; H5 is the inference-time, governed-update extension.
- Huang, Sastry, et al. (2024) — "Collective Constitutional AI: Aligning a Language Model with Public Input" (arXiv 2406.07814). Public-deliberation constitution-drafting; the same review-and-merge structure at population scale.
- Wang et al. (2025) — "AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents" (arXiv 2503.18666). The hard external enforcement layer (V7) that bounds H5's proposable surface.
- "EvolveR: Self-Evolving LLM Agents through an Experience-Driven Lifecycle" (arXiv 2510.16079) — experience-driven principle distillation, with explicit lifecycle phases relevant to H5's gap-detection-to-proposal loop.
- "Evolving Interpretable Constitutions for Multi-Agent Coordination" (arXiv 2602.00755) — multi-agent constitution evolution with interpretable rules; cross-references the evolved-vs-fixed-constitution tradeoff H5 navigates.
- Kohlberg (1969/1981) — stages of moral development; the cognitive-science grounding for *why* principle-level reasoning evolves rather than remaining static.
