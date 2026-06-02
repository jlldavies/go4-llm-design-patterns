# V1 — Human-in-the-Loop

> Insert mandatory human review and approval at defined decision boundaries before the agent proceeds — the agent *blocks* until a human approves, rejects, or modifies the plan.

**Also Known As:** HITL, Approval Gate, Human Checkpoint, Mandatory Review Gate. (V1 is distinct from — and in direct tension with — V2 Human-on-the-Loop; see Related Patterns.)

**Classification:** Category V — Reliability · Band V-A Safety and Security · the *blocking* oversight pattern — the agent cannot proceed past the checkpoint without a human verdict.

---

## Intent

Make the agent halt at the boundary of any action whose cost-of-error exceeds the cost-of-delay, surface the planned action to a human in interpretable form, and resume only on an explicit verdict — so that irreversible, novel, or high-blast-radius actions never execute autonomously.

## Motivation

Autonomous agent failure is the dominant production risk for agentic systems. The Composio AI Agent Report (2025) finds 88% of agent projects never reach production, and the most-cited cause is that fully autonomous behaviour in high-stakes contexts destroys value rather than creating it. The pattern that solves this — at the cost of latency — is to block the agent at chosen boundaries until a human approves the next step.

Naive alternatives all fail in characteristic ways. Trusting the model's own confidence score is unreliable: confident-but-wrong is the modal failure mode of capable LLMs. This is not a calibration quirk — token generation is stochastic sampling from a probability distribution, and high probability mass on a token is not equivalent to epistemic certainty; the model has no privileged access to the correctness of its own outputs (mechanism 7). Output-only guardrails (anti-pattern A5) catch a fraction of bad actions but miss the ones the model was trained or prompted to phrase acceptably. Logging without blocking (V14 alone) produces excellent post-incident forensics on damage that has already happened. A monitoring-only architecture (V2 Human-on-the-Loop) is correct for reversible routine actions but wrong for irreversible ones — by the time a human sees the alert, the email has been sent or the row has been deleted.

V1's unique contribution is that the agent *cannot proceed*. This is not a UX preference about how autonomous the agent feels. It is an architectural property tied to a specific class of actions: those whose blast radius exceeds what an after-the-fact correction can recover. Sending external communications, financial transactions, deleting data, modifying production systems, applying self-modifications to the agent's own principles or code — these are V1 territory by their reversibility profile, regardless of how reliable the agent has shown itself to be on adjacent tasks. The mapping is per-action, not per-agent: the same agent can be V1-gated on `send_email` and V2-monitored on `draft_reply`.

## Applicability

Use V1 when:

- the action is **irreversible** — sending external communications, financial transactions, deleting data, modifying production systems, publishing public content;
- the action is **novel** — outside the agent's evaluated operating envelope (V16 Offline Eval coverage gap);
- the **blast radius is high** — error affects systems, users, or counterparties beyond the agent's own scope;
- a regulatory regime mandates human oversight (EU AI Act Article 14, sector-specific compliance);
- the action is **self-modifying** — required by H5 (Constitutional Self-Alignment) and H8 (Meta-Agent Self-Modification) with no exception;
- the agent itself has flagged uncertainty above a calibrated threshold.

Do not use V1 when:

- the action is **reversible and routine** — choose **V2 Human-on-the-Loop**, which monitors without blocking;
- latency would defeat the purpose — V2 with strong V14 logging and V17 monitoring covers low-blast-radius high-volume actions;
- the action is fully deterministic and policy-checked — **V7 AgentSpec / Declarative Governance** with PROHIBIT rules can enforce the constraint without human in the loop;
- the action is internal to the agent's reasoning — checkpointing every thought is theatre. Gate at the *external action* boundary, not at every reasoning step.

## Decision Criteria

V1 is right when an autonomous error in this specific action type would cost more than the delay of waiting for a human verdict.

**1. Reversibility test.** Classify the action: can its effect be undone within the same session by another tool call? If **NO**, V1. If **YES** and the undo is cheap, V2 is acceptable. Threshold: an action whose reversal requires another party's cooperation (sending email, posting to public channels, executing a trade) is *not* reversible by the agent and is V1 territory.

**2. Blast-radius test.** Score the maximum harm of a wrong action on a 1–5 scale: (1) ephemeral session-internal, (2) wastes tokens or compute, (3) affects this user's local state, (4) affects external systems or counterparties, (5) regulatory, financial, or reputational damage. **Score ≥ 4 → V1.** Score ≤ 2 → V2 or V7 alone. Score 3 → V2 with V14 + V17.

**3. Novelty test.** Is the action covered by the V16 offline eval suite and within the V17 online quality envelope? If the action is *outside* the evaluated envelope, V1 is required regardless of reversibility — there is no calibration to trust. Threshold: if the action's parameters were not represented in the most recent eval pass, treat as novel.

**4. Coverage by V7.** Is there a deterministic policy rule that already governs this action via **V7 AgentSpec**? If V7 PROHIBIT covers it, V1 is not needed — the policy engine blocks unconditionally, because deterministic rule evaluation has no sampling variance (mechanism 7). If V7 PERMIT covers it but the human still wants discretion, V1 sits *between* PERMIT and execution.

**5. Latency budget.** What is the acceptable wait time for human verdict (seconds, minutes, hours)? If the budget is too tight for any human to respond, the action either needs to be V2-monitored with a hard V9 bound, or *should not be automated at all* — the question being asked is not whether to use V1 but whether to use an agent.

**Quick test — V1 is the right pattern when:**

- the action is irreversible (cannot be undone autonomously by the agent), *and*
- the blast radius is ≥ 4 or the action is novel (outside V16/V17 envelope), *and*
- no V7 deterministic rule already blocks the action, *and*
- the latency budget tolerates a human response.

If the action is reversible and routine, choose **V2 Human-on-the-Loop**. If the action is fully specifiable as a hard rule, choose **V7 AgentSpec** (deterministic, no human required). If the latency budget cannot tolerate any wait, reconsider whether the action should be automated at all — never silently downgrade V1 to V2 to avoid the wait. *(This downgrade is the anti-pattern: see CRITICAL 2 in CONFLICTS.md.)*

## Structure

```
  Agent → planned action a
            │
            ▼
        [ Gate(a) ]                ← decides: V1, V2, or pass-through
            │
       gate = V1
            ▼
        [ Surface ]                ← human-readable plan + rationale + expected outcome
            │
            ▼
        [ Block & Wait ]           ← state checkpointed (V10); execution paused
            │
       human verdict
            │
   ┌────────┼────────┬─────────────┐
   ▼        ▼        ▼             ▼
 APPROVE  REJECT   MODIFY       ESCALATE
   │      (+reason) (edits a)        │
   │        │         │              ▼
   │        ▼         ▼          higher authority
   │     re-plan  execute a'        gate
   ▼
 execute a
   │
   ▼
  (V14 logs verdict, prompt, plan, outcome)

  Timeout → safe default = ABORT (never proceed)
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Checkpoint Gate** | the decision *whether this action needs V1* | planned action + context → V1 / V2 / pass-through | use model confidence as the sole signal — gate by action class (reversibility, blast radius, novelty), or it will rubber-stamp confident wrong actions. |
| **Plan Surfacer** | producing a human-readable representation of the planned action | tool-call payload + rationale → review artefact (action, why, expected outcome, alternatives) | surface raw JSON or opaque tool arguments — an unreviewable plan is V1 theatre. |
| **Blocker** | halting agent execution at the checkpoint | gate verdict (V1) → paused state via V10 | proceed on timeout — the safe default is always ABORT. |
| **Human Reviewer** | the verdict | review artefact → {APPROVE, REJECT+reason, MODIFY+edits, ESCALATE} | be presented with so many checkpoints they stop reading. The Gate's calibration is the Reviewer's protection. |
| **Modification Channel** | structured edits to the plan | reviewer edits → revised action a' | allow free-text edits that re-enter the agent unchecked — modifications must re-enter the same gate. |
| **Escalation Router** | routing to higher authority when first reviewer cannot decide | review artefact + escalation reason → next-level reviewer | be a dead-end — every escalation must terminate in an explicit verdict or a documented abort. |
| **Audit Recorder** | logging the verdict, prompt, plan, and outcome (delegated to V14) | every checkpoint event → immutable trace | omit the *reason* on REJECT — the reason is the training data for future gate calibration. |

Seven narrow responsibilities. The pattern's correctness lives in the Gate (right things get gated), the Surfacer (the human can actually review), and the Blocker (no execution without verdict). The Audit Recorder is the feedback channel that lets the Gate improve over time.

## Collaborations

The Agent generates a planned action and submits it to the Checkpoint Gate. The Gate classifies the action by its V1 / V2 / pass-through profile (reversibility, blast radius, novelty, V7 coverage). If V1 fires, the Plan Surfacer composes a human-readable artefact — what the action is, why the agent chose it, what outcome is expected, and what reversal looks like if applied wrongly — and the Blocker checkpoints the agent's state via V10 and halts execution. The Human Reviewer responds with one of four verdicts. APPROVE releases the original action to execution. REJECT returns the agent to re-plan, carrying the reviewer's reason as a constraint. MODIFY routes through the Modification Channel: the edited plan re-enters the Gate (it is not allowed to bypass it) and the new action is then surfaced for confirmation if its class has changed. ESCALATE routes the artefact to higher authority through the Escalation Router. On every verdict, the Audit Recorder writes the prompt, plan, verdict, reason, and downstream outcome to the V14 trace. On timeout — no verdict within the budget — the Blocker's safe default is ABORT and a V14 timeout event.

## Consequences

**Benefits**
- Prevents catastrophic autonomous errors on the action classes where they would be most costly.
- Builds operator and user trust by making irreversibility explicit rather than implicit.
- Generates a high-quality calibration signal — every REJECT carries a reason that can refine the Gate and future agent training.
- Satisfies hard regulatory requirements (EU AI Act Article 14) for human oversight on high-risk actions.
- Provides a clean human escape hatch when the agent encounters an action outside its evaluated envelope.

**Costs**
- Adds latency on every gated action — typically seconds to minutes for routine review, longer for escalation.
- Requires a Surfacer good enough to make the plan reviewable in seconds, not a JSON dump.
- Operational cost of a human reviewer in the loop; bottleneck when checkpoint volume is high.
- Checkpointing infrastructure (V10) and audit logging (V14) are prerequisites — V1 without them loses work on every pause.

**Risks and failure modes**
- *Automation bias* — under time pressure, reviewers rubber-stamp every plan. Mitigation: track APPROVE-without-modification rate; if > 95%, the Gate is over-firing or the Surfacer is unreviewable.
- *Checkpoint theatre* — too many gates dull human attention until the one that mattered slides through. Mitigation: calibrate the Gate ruthlessly; demote any action class with repeated unmodified approvals to V2.
- *Too few checkpoints* — only the visible decisions are gated; the agent quietly executes the unrecorded ones. Mitigation: gate by action class (reversibility, blast radius), not by visibility.
- *Silent V2 downgrade* — teams under latency pressure relabel V1 actions as V2 to remove the block. This is the CRITICAL 2 anti-pattern (CONFLICTS.md). Mitigation: the V1/V2 boundary should require explicit governance review, not a runtime config flag.
- *Timeout-to-proceed* — defaulting to "proceed on no response" inverts the pattern. The safe default is always ABORT.
- *Unsurfaceable plan* — actions whose effect cannot be summarised for a human reviewer should be redesigned or refused, not waved through.

## Implementation Notes

- **Gate by action class, not by model confidence.** A confident-but-wrong action is exactly the class V1 exists to catch. The reversibility/blast-radius/novelty triple is the right gate input.
- **The Surfacer is half the pattern.** Plans must be reviewable in under 30 seconds: action, why, expected outcome, what reversal looks like. Raw tool-call JSON is not a review artefact.
- **REJECT must carry a reason.** A reason-less rejection trains nothing. Make the reason field mandatory and surface aggregated rejection reasons as a Gate-calibration signal.
- **MODIFY must re-enter the Gate.** Reviewer edits can change the action's class (a small modification can move it from V1 to V2 or vice versa). Never let a modification bypass the gate.
- **Timeout defaults to ABORT, always.** If the human cannot respond in time, the system does not proceed. If the latency budget is too tight for any human, the action is the wrong fit for V1 — choose V2 with V9 hard bounds, or refuse the automation.
- **Pair with V10 (Checkpointing) and V14 (Trajectory Logging).** Both are prerequisites, not co-options. V10 saves state so the block doesn't lose work; V14 logs the verdict so the calibration loop closes.
- **Track approval-rate-without-modification.** > 95% means automation bias or Gate over-firing. < 50% means the agent's planning quality is the real problem and V1 is masking it.
- **Demote and promote between V1 and V2 deliberately.** When an action class accumulates a long approval history with no modifications, governance review can demote it to V2 with stricter V17 monitoring. When V2 monitoring catches near-misses, promote back to V1. The mapping is reviewed, not set-and-forget.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V1 wraps any agent action that the Checkpoint Gate classifies as V1-required. It composes with **V10 Checkpointing** (state save before block), **V14 Trajectory Logging** (verdict audit), **V7 AgentSpec** (deterministic gate input), and **V9 Bounded Execution** (timeout cap). The Surfacer is a Signal-layer artefact (**S6 Output Template**, **S5 Constraint Framing** for what must be included). Required by **H5 Constitutional Self-Alignment** and **H8 Meta-Agent Self-Modification** for every principle / parameter change.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Agent plans next action | `LLM` | Agent session (outside V1) |
| 2 | Gate classifies the action: V1 / V2 / pass-through | `LLM (or rule)` | Gate session; V7 |
| 3 | Branch — if pass-through or V2, exit V1; else continue | `code` | |
| 4 | Surfacer composes the human-readable review artefact | `LLM` | Surfacer session; S6 |
| 5 | Checkpoint state (V10) and block execution | `code` | V10 |
| 6 | Present artefact to human; wait for verdict (bounded by timeout) | `code` | V9 |
| 7 | Branch on verdict — APPROVE / REJECT / MODIFY / ESCALATE / TIMEOUT | `code` | |
| 8 | On MODIFY: revised action re-enters at step 2 | `code` | |
| 9 | Record verdict, prompt, plan, outcome | `code` | V14 |

**Skeleton** — wiring only:

```
hitl_checkpoint(agent_state, planned_action):
    gate = Gate(planned_action, context=agent_state)   # LLM (or rule) — class V1/V2/pass
    if gate.class != V1:
        return execute_or_monitor(planned_action, gate)  # exits to V2 or pass-through

    artefact = Surfacer(planned_action, agent_state)   # LLM — review artefact
    checkpoint_id = V10_save(agent_state)              # code — checkpoint before block
    verdict = wait_for_human(                          # code — bounded wait
        artefact,
        timeout=budget,
        on_timeout=ABORT                               # safe default is never proceed
    )

    V14_log(checkpoint_id, planned_action, artefact, verdict)  # code — audit

    match verdict:
        APPROVE  → execute(planned_action)
        REJECT   → return_to_agent(reason=verdict.reason)
        MODIFY   → hitl_checkpoint(agent_state, verdict.revised_action)  # re-enter gate
        ESCALATE → route_to(verdict.escalation_target)
        TIMEOUT  → abort_with_log()
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Gate** | small fast generalist, or a deterministic rule engine when the action set is enumerable | role (*"you classify whether a planned agent action requires blocking human review"*); the reversibility / blast-radius / novelty rubric; the V7 PROHIBIT list to cross-check; output contract (one of `V1`, `V2`, `PASS`, with a one-sentence reason) | the planned action and the relevant context |
| **Surfacer** | capable generalist — review quality caps the value of the whole pattern | role (*"you produce a human-readable review artefact for a planned agent action"*); the output template (S6) — fields: action, why, expected outcome, what reversal looks like, alternatives considered; constraints (S5) — no raw JSON; ≤ 200 words; never omit the reversal section | the planned action, the rationale trace from the agent, and the relevant context |

**Specialist-model note.** No fine-tuned specialist is required, but two structural choices change everything. First, the **Gate must be deterministic where it can be** — when the action set is small and enumerable, a rule engine (or V7) is strictly better than an LLM Gate, because the Gate's failure mode is the pattern's failure mode. When the Gate is an LLM, it is subject to the same stochastic sampling failure as the agent it gates — this is why V7 AgentSpec (deterministic rule engine) is strictly preferable to an LLM Gate for enumerable action sets (mechanism 7). Second, the **Surfacer benefits from the strongest available model** — reviewability is the bottleneck, and the cost is paid once per checkpoint, not once per turn. For agents handling regulated actions (EU AI Act Article 14 high-risk), pair the Gate with V7 AgentSpec rather than relying on the LLM Gate alone.

## Open-Source Implementations

- **LangGraph `interrupt()`** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — the most direct V1 implementation in the major frameworks. The `interrupt()` function pauses graph execution at any node, surfaces a payload to the caller, and resumes only when re-invoked with `Command(resume=...)`. State persistence is built in. See [`docs.langchain.com/oss/python/langgraph/interrupts`](https://docs.langchain.com/oss/python/langgraph/interrupts).
- **HumanLayer** — [`github.com/humanlayer/humanlayer`](https://github.com/humanlayer/humanlayer) — purpose-built for V1: turn any function call into a human-approval gate via Slack, email, or web UI. Companion to the 12-Factor Agents methodology.
- **12-Factor Agents** — [`github.com/humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents) — Factor 6 (*Launch / Pause / Resume*) and Factor 7 (*Contact Humans With Tool Calls*) are the canonical statement of the V1 design.
- **AutoGen `UserProxyAgent`** — [`github.com/microsoft/autogen`](https://github.com/microsoft/autogen) — `human_input_mode="ALWAYS"` makes a user-proxy agent block on every message; `"TERMINATE"` blocks on termination conditions; `"NEVER"` disables V1.
- **CrewAI human input** — [`github.com/crewAIInc/crewAI`](https://github.com/crewAIInc/crewAI) — task-level `human_input=True` flag pauses agent execution on task completion for human review before continuing.

## Known Uses

- **Claude Code** — file edit and command execution gated by an explicit per-action approval (deny / allow once / allow always per session) — V1 with operator-controlled promotion to pass-through within a session.
- **Cursor** — agent-mode edits gated by an apply/reject step before changes touch the user's working tree.
- **Devin** — long-running autonomous coding agent surfaces blocking checkpoints when actions touch external systems or production environments.
- **Enterprise procurement and treasury agents** — financial-transaction agents almost universally route over a defined threshold to a human approver; below threshold, V2-monitored.
- **Email and CRM outreach agents** — outbound message agents that draft autonomously but block on `send` until a human confirms — the canonical V1 split where drafting is V2 and sending is V1.
- **Production deployment bots** — release agents that can plan and stage a deploy autonomously but require human approval to promote to production.

## Related Patterns

- **Distinct from** V2 Human-on-the-Loop — V1 blocks, V2 monitors. The choice is per-action by reversibility / blast radius / novelty, not per-agent by operational preference. *(CRITICAL 2 in CONFLICTS.md.)*
- **Requires** V10 Checkpointing — the agent must save state to wait for the human verdict; V1 without V10 loses work on every pause.
- **Pairs with** V14 Trajectory Logging — every verdict, reason, and outcome belongs in the audit trace; V14 is the calibration channel for the Gate.
- **Pairs with** V9 Bounded Execution — the wait-for-human step needs a timeout bound; the safe default is ABORT, not proceed.
- **Composes with** V7 AgentSpec — deterministic prohibitions are enforced by V7 without human review; V1 sits in the discretionary zone between V7 PERMIT and execution.
- **Required by** H5 Constitutional Self-Alignment — every proposed principle change must be V1-gated; no exception. *(CRITICAL 7 in CONFLICTS.md.)*
- **Required by** H8 Meta-Agent Self-Modification — any significant behavioural modification proposed by an agent about itself must be V1-gated.
- **Tension with** H6 Continuous Inner Monologue — autonomous background thinking that produces actions must route those actions through V1; H6 should produce *insights*, not autonomous actions, unless explicitly scoped and gated.
- **Triggered by** V17 Online Eval — quality drift detected in production fires V1 escalation for at-risk action classes.
- **Pairs with** S6 Output Template + S5 Constraint Framing — the Surfacer's review artefact is a Signal-layer construct with hard structural requirements.

## Sources

- 12-Factor Agents (Dex Horthy / HumanLayer, 2024–25) — Factor 6 (*Launch / Pause / Resume*) and Factor 7 (*Contact Humans With Tool Calls*).
- Anthropic — *Building Effective Agents* (2024–25): checkpoints before irreversible actions as standard agent design.
- LangGraph documentation — `interrupt()` and Command-based resume for V1 implementation; the closest framework match to the pattern shown above.
- Composio AI Agent Report (2025) — 88% production-failure analysis, autonomous-behaviour failure as primary cause.
- EU AI Act (Regulation 2024/1689) Article 14 — mandatory human oversight requirements for high-risk AI systems.
- NIST AI Risk Management Framework (AI RMF 1.0) — human oversight as a first-class risk control.
- ISO/IEC 42001:2023 — AI Management System standard, human oversight clauses.
