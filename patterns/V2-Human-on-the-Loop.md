# V2 — Human-on-the-Loop

> Let the agent act autonomously within its scope while a human watches the trace in real time, ready to interrupt, redirect, or override — so oversight stays continuous without blocking every step.

**Also Known As:** Monitoring Mode, Supervisory Control, HOTL, Brake-Pedal Oversight.

**Classification:** Category V — Reliability · Band V-A Safety and Security · the *supervisory* counterpart to V1 — oversight without blocking.

---

## Intent

Preserve meaningful human oversight over an autonomous agent without paying V1's per-action latency: the agent proceeds; the human watches a live trace and can pull the brake.

## Motivation

V1 Human-in-the-Loop blocks: the agent stops at every checkpoint and a human approves before it continues. For irreversible, high-stakes, or novel actions that is the right architecture — the latency is the point. But the same blocking design, applied to a long-running autonomous workflow over reversible, routine, well-understood actions, destroys exactly the autonomy that made the agent worth deploying. A V1 gate on every routine action collapses into rubber-stamping (a documented failure mode of V1) — the human is technically in the loop, but is no longer paying attention.

What is needed for those workflows is not less oversight but a different *shape* of oversight. Aviation solved this problem decades ago with **human supervisory control** (Sheridan; Parasuraman, Sheridan & Wickens 2000): the pilot does not fly the aircraft turn by turn, the autopilot flies it, and the pilot monitors instruments and intervenes when the autopilot operates outside acceptable parameters. The 12-Factor Agents framing carries the same shape into agent design — "launch/pause/resume" with traces that a human can read while the agent runs (HumanLayer, 2025). Anthropic's agent-autonomy guidance notes the same drift: as operators gain experience with an agent, they shift from approving each action to monitoring the trace and intervening when needed. V2 names that mode and treats it as a first-class design choice, not an informal relaxation of V1.

The pattern's defining commitment is that *oversight is continuous, not gated*. The human is present throughout, watching, but action does not depend on their approval. Three structural pieces follow from that commitment: a **trace** the human can actually read in real time (without it, supervision is fiction); a **monitor** — automated and/or human — that detects threshold violations, anomalies, or drift; and an **interrupt path** that can pause execution and hand control back. Without all three, V2 is theatre — autonomous action dressed up as oversight.

V2 is *not* a safer or relaxed V1. It is the correct architecture for a different risk profile. Choosing V2 because V1 seems slow — when the action is irreversible — is the canonical anti-pattern (see Conflicts §10 below).

## Applicability

Use V2 when:

- the actions are **reversible** — they can be undone, retried, or rolled back without lasting harm;
- the agent operates within **established, well-understood** parameters with a measured track record (V16 Offline Eval has set a baseline; V17 Online Eval is in production);
- the workflow is **long-running** or high-frequency, so V1's per-step latency would defeat its purpose;
- a **readable trace** (V14 Trajectory Logging) exists — without it there is nothing for the supervisor to watch;
- the **interrupt mechanics** are real — there is an engineered pause point, not just a "kill the process" lever.

Do not use V2 when:

- the action is **irreversible, high-blast-radius, or novel** — use **V1 Human-in-the-Loop**;
- there is **no trace infrastructure** — instrument with **V14 Trajectory Logging** first, then add V2;
- the agent has **never been evaluated** against the action class — use **V16 Offline Evaluation** to baseline before granting autonomy;
- the monitor itself is **untested or uncalibrated** — false-negatives in HOTL are worse than V1's latency, because they create the *illusion* of supervision; build the monitor against V17 signals first;
- the workflow runs entirely **unattended** with no human in any reasonable response window — that is not V2, that is autonomy without oversight; gate it with **V9 Bounded Execution** and **V7 AgentSpec** instead, or restore **V1** for the dangerous actions.

## Decision Criteria

V2 is right when the actions are reversible, the agent is calibrated, and V1's blocking latency would dissolve the workflow's value.

**1. Reversibility test.** Classify every action type the agent can take by reversibility: undo-able in seconds, undo-able with effort, or irreversible. If **any action** in the autonomous scope is irreversible, route it through **V1 Human-in-the-Loop**; V2 covers the rest. A V2 agent with one buried irreversible action is a V1-appropriate agent in disguise.

**2. Blast-radius test.** For each action class, estimate the worst-case impact of an unmonitored error: data corruption, external comms sent, money moved, systems modified. V2 is appropriate only at **low blast radius** — where a bad action can be reversed before serious harm. High blast radius $\to$ V1.

**3. Calibration evidence.** Does the agent have a measured error rate on this action class, from **V16 Offline Eval** and ideally **V17 Online Eval**? Threshold: an action class with no eval baseline does not yet qualify for V2 — the supervisor has no priors to monitor against. If error rate or drift is unknown, use V1 until it is known.

**4. Latency-vs-value test.** What is the *workflow value* of allowing the agent to continue without blocking? If V1 latency is acceptable for the user and workload, V1 wins — it is the safer default. V2 earns its place only when V1 latency demonstrably destroys the workflow (long-running pipelines, high-frequency processing, time-sensitive monitoring loops). "V1 feels slow" is not the test; "V1 makes this workflow impossible" is.

**5. Monitor-and-interrupt readiness.** Three pieces must be in place before V2 ships: (a) a **trace** instrumented per **V14 Trajectory Logging** that a human can actually follow in real time; (b) a **monitor** — human, automated thresholds, or both — with named trigger conditions; (c) an **interrupt mechanism** that pauses cleanly and hands state to the supervisor (pairs with **V10 Checkpointing**). Missing any of the three $\to$ not yet ready for V2.

**Quick test — V2 is the right pattern when:**

- every action in the autonomous scope is reversible and low-blast-radius, *and*
- the agent has a measured baseline on this action class (V16, ideally V17), *and*
- V1's per-action latency would materially defeat the workflow, *and*
- trace, monitor, and interrupt are all engineered — not aspirational.

If any action is irreversible or high-blast-radius, partition the action set and gate those actions with **V1 Human-in-the-Loop** — the rest can run V2. If trace or monitor are missing, build **V14 Trajectory Logging** first; V2 without V14 is supervision in name only. If the agent has never been baselined, use **V16 Offline Eval** before granting autonomy.

## Structure

```
                     ┌──────────────── trace stream (V14) ──┐
                     │                                       ▼
  Agent → action ──► Trace ──► action ──► Trace ──► action ──► Trace ──► ...
                                                                 │
                                                                 ▼
                                                    ┌──── Monitor ────┐
                                                    │ thresholds      │
                                                    │ anomalies       │
                                                    │ human attention │
                                                    └────────┬────────┘
                                                             │
                                       trigger fires? ───────┤
                                                             │
                                                  ┌──────────┴────────────┐
                                                  ▼                       ▼
                                            INTERRUPT                  continue
                                                  │
                                                  ▼
                                      pause at next safe point (V10)
                                                  │
                                                  ▼
                                      Human Supervisor reviews state
                                                  │
                              ┌──── redirect / override / abort ────┐
                              ▼                                       ▼
                         resume with edits                       terminate
```

The trace is continuous; the monitor is asynchronous; the agent does not block on the supervisor. Control returns to the human only when a trigger fires — the rest of the time the human is watching, not gating.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Agent** | autonomous execution within scope | task + state $\to$ actions | hold any action class that has not been explicitly admitted to its autonomous scope; expanding scope at runtime breaks the calibration that V2 rests on. |
| **Trace Emitter** *(V14)* | a continuous, structured, human-readable trace of every step | step events $\to$ trace stream | be silent on anomalies; a sparse or summarised trace defeats real-time supervision. The trace V2 needs is denser than the audit trace V14 produces by default. |
| **Monitor** | watching the trace for triggers | trace stream + thresholds $\to$ trigger events | absorb everything quietly; a monitor that never fires is indistinguishable from no monitor. Calibration against V17 signals is mandatory, not optional. |
| **Interrupt Handler** | cleanly pausing the agent on trigger | trigger event $\to$ paused state at next safe point | abort mid-action — pause at the next checkpoint (V10) so resume is possible; hard kills lose state. |
| **Human Supervisor** | reviewing paused state and directing continuation | paused state $\to$ resume / redirect / abort | be the monitor *and* the supervisor on a long shift — alert fatigue is the dominant failure mode; rotate or alarm-tier. |
| **State Store** *(V10)* | durable checkpoints the supervisor can edit before resume | agent state $\to$ resumable snapshot | be in-memory only; without external persistence, an interrupt loses the work it was trying to save. |

Six responsibilities; the **Trace Emitter**, **Monitor**, and **Interrupt Handler** are what distinguish V2 from V1 — V1 has none of these because it blocks on the human directly. The **State Store** is shared with V10 and V1; the **Agent** and **Human Supervisor** are shared with V1 but play different roles.

## Collaborations

The Agent runs its workflow autonomously within its admitted scope. As it executes, the Trace Emitter writes structured events into a stream the Monitor and the Human Supervisor both consume. The Monitor watches for named trigger conditions — threshold violations on cost, latency, or error rate; anomalous action sequences; explicit alarm conditions encoded as policy. When no trigger fires, the agent continues uninterrupted; the Human Supervisor watches the trace at whatever cadence the workflow needs (continuously, periodically, on alert). When a trigger fires, the Interrupt Handler signals the Agent to pause at the next safe point, the State Store checkpoints the current state, and the Human Supervisor reviews. The supervisor's options are to resume with edits to the state (redirect), override the next planned action, or abort the run. Without an interrupt, the workflow runs to completion and the trace becomes the audit record (V14).

## Consequences

**Benefits**
- Meaningful oversight without the per-action latency that makes V1 incompatible with long-running or high-frequency workflows.
- Right-sized for calibrated agents acting in reversible, low-blast-radius scopes — the cases where V1 is overhead, not safety.
- Forces the operator to build a real trace and a real monitor — investments that pay back across V14, V17, and incident response.
- The interrupt path means a single supervisor can oversee multiple agent runs in parallel (one trace per pane), rather than blocking on each.

**Costs**
- Heavy engineering investment up front: V14 trace, V17-grade signals for the monitor, a clean interrupt and pause path, V10 checkpointing.
- The monitor itself must be designed, tuned, and maintained — false-positive interrupts waste supervisor attention; false-negatives let bad behaviour through.
- Requires a calibrated agent: V2 is not appropriate for a workflow that has never been baselined.
- At high event volume the Monitor's context grows continuously across a session; the O(n²) attention cost per generation step rises with the number of logged events in context — windowing or compaction of the trace fed to the Monitor is required (mechanism 2, mechanism 11).

**Risks and failure modes**
- *Alert fatigue.* Supervisors stop responding to monitor signals; V2 collapses into autonomous-without-oversight. Mitigation: tiered alarms, rotation, alarm-budget discipline.
- *Wrong-pattern misapplication.* The canonical anti-pattern — choosing V2 for an irreversible action because "the agent is usually right" or "V1 feels slow". The point of V1 is precisely the cases where the agent is not right.
- *Trace-monitor gap.* The trace is rich but the monitor watches the wrong signals; the supervisor sees nothing concerning until the damage is done.
- *Scope creep.* The agent acquires new action types after V2 deployment without re-baselining — the calibration that justified V2 no longer covers what it is doing.
- *Interrupt-mechanism rot.* The pause/resume path was tested at deployment, never since; when triggered for the first time in anger, it fails.

## Implementation Notes

- Build **V14 Trajectory Logging** before V2 is even on the design board; without the trace there is no supervision.
- Calibrate the monitor against **V17 Online Eval** signals — quality drift, safety-guardrail trigger rate, cost/latency outliers — not against intuition. A monitor that fires on signals nobody has measured is noise.
- Tier alarms by blast radius: hard interrupts for safety-critical signals; soft alerts (notification, no pause) for informational drift; periodic summaries for cadence review. A monitor that only knows "pause" will be ignored.
- Pair with **V9 Bounded Execution** for hard caps the monitor cannot override — V2's soft supervision plus V9's hard limits is the production posture.
- Pair with **V10 Checkpointing** so the interrupt can hand the supervisor a coherent state to edit, not a half-executed action.
- Partition the action set: V1 for the irreversible subset, V2 for the rest, even within a single workflow. A blanket V2 over a mixed action set is the classic misapplication.
- Make the interrupt drill routine: trigger it deliberately in staging at least monthly. An interrupt mechanism that has not been exercised will fail when used in earnest.
- Specialist-model dependency: see **Specialist-model note** in the Implementation Sketch below — V2 is not LLM-only; the monitor and interrupt are code, the trace is plumbing.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V2 wraps an autonomous agent loop — typically **R4 ReAct** or an **O6 Orchestrator-Workers** topology — in a supervisory trace-and-interrupt layer. It is built on top of **V14 Trajectory Logging** (the trace), composes with **V10 Checkpointing** (the interrupt's resume state), **V9 Bounded Execution** (the hard limits the monitor cannot override), and **V17 Online Evaluation** (the signal source for the monitor's triggers). Where the monitor itself reasons over the trace, that monitor session can use **V15 LLM-as-Judge** patterns. The agent's own setup is Signal-layer work — a role (**S3**), constraints (**S5**), an output contract (**S6**).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Agent emits a step (action + reasoning) | `LLM` | Agent session |
| 2 | Trace Emitter writes structured event to stream | `code` | V14 |
| 3 | Checkpoint state at safe point | `code` | V10 |
| 4 | Monitor evaluates trigger conditions on the event | `LLM (or rule)` | Monitor session, V15 |
| 5 | Branch — trigger fires? pause; else continue to step 1 | `code` | V9 (also enforces hard limits) |
| 6 | Interrupt Handler pauses agent at next safe point | `code` | |
| 7 | Human Supervisor reviews paused state + recent trace | *(human)* | |
| 8 | Branch — resume / redirect (edit state) / abort | `code` | V10 (state edit) |

**Skeleton** — the wiring only; each `# LLM` line is a configured session, not code:

```
hotl_supervised_run(task):
    state = init_state(task)
    while not done(state):
        event = Agent(state) ─────────────── # LLM   → next action + reasoning
        trace.emit(event)                    # code  — V14
        state = checkpoint(apply(event))     # code  — V10
        trigger = Monitor(event, trace)      # LLM (or rule) — V15-shaped judge
        if trigger:
            pause_at_next_safe_point()       # code
            decision = supervisor_review()   # human, out-of-band
            if decision == ABORT:    return abort(state)
            if decision == REDIRECT: state = decision.edited_state
            # RESUME falls through
        if V9_limits_hit(state):             # code  — hard cap, no override
            return graceful_terminate(state)
    return state.result
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | the system's main generalist | role (S3); the autonomous scope as an explicit action enumeration (S5); the output contract for actions (S6); the trace format it must emit | the current state + the task |
| **Monitor** *(when LLM-based)* | small fast generalist, *or* a tuned classifier; some teams use a stronger judge model when triggers are subtle | role (*"you watch an agent trace and flag interventions per these named conditions"*); the named trigger conditions with thresholds; the output contract (`OK` / `INTERRUPT: {reason}`) | the latest event + a windowed slice of the trace |

The **Human Supervisor** is not an LLM session — they are out-of-band — but the *review surface* they see (paused state + recent trace + monitor reason) is itself a Signal-layer artefact (**S6 Output Template**) and should be designed deliberately, not left as raw JSON.

**Specialist-model note.** V2 is not primarily an LLM pattern — the **Trace Emitter** and **Interrupt Handler** are deterministic code, and the **Monitor** is often a rules engine or a small classifier rather than a generalist call. Where an LLM-based monitor is used, prefer a **strong judge model** over the agent's own model — self-monitoring by the same model is documented to under-fire on its own errors (the "self-similarity bias" noted in the V15 LLM-as-Judge literature). The mechanistic root is that the same learned attention metric (W_Q W_K^T) generates similar probability distributions over similar inputs — a model judging outputs from its own distribution will assign similar probability mass to similar errors the agent makes, causing systematic under-detection (mechanism 1). Where a stable system prompt and monitoring rubric are loaded per event, configuring the monitor for prefix caching (Anthropic: minimum 1024 tokens, 5-minute TTL, ~10% cost on cache hits) substantially reduces per-event scoring cost at the Monitor session (mechanism 5). When the agent runs at high frequency, the Monitor's LLM cost dominates; consider a tiered design — cheap rule checks always-on, LLM-judge invoked only on rule-level suspicion. The trace stream itself benefits from **prompt-caching-capable infrastructure** so the Monitor can score successive events against a stable trace prefix.

## Open-Source Implementations

- **HumanLayer** — [`github.com/humanlayer/humanlayer`](https://github.com/humanlayer/humanlayer) — SDK for adding human-approval and interrupt hooks to agent tool calls; Apache 2.0; supports both V1 (blocking approval) and V2 (async monitoring + interrupt) modes via Slack, email, and web channels.
- **HumanLayer Agent Control Plane** — [`github.com/humanlayer/agentcontrolplane`](https://github.com/humanlayer/agentcontrolplane) — Kubernetes-native scheduler for long-lived outer-loop agents running without continuous supervision; checkpoints state, supports async human-as-tool calls for redirection; the production deployment shape of V2 + V10.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — durable agent execution with graph-level and node-level interrupts, state inspection and editing mid-run, and streaming traces; LangSmith integration provides the trace surface a V2 supervisor needs.
- **12-Factor Agents (reference document)** — [`github.com/humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents) — Factor 6 (Launch/Pause/Resume) is the canonical principles document for V2-shaped agents; not a library but the conceptual reference.

## Known Uses

- **Long-running coding agents** (Claude Code, Cursor, Devin) — operator watches the action trace in real time, allows reversible edits to proceed, interrupts on suspect tool calls; V1 reserved for `rm`, force pushes, deployments.
- **Algorithmic trading and fraud-detection supervision** — agents execute on a stream; risk officers monitor an aggregated trace; circuit breakers and human interrupts gate the high-blast actions.
- **Customer-service autonomous agents** at scale — supervisors monitor a sample of live conversations via dashboards and intervene on quality drift, with V1 gating refunds or account changes.
- **Autonomous research / data-pipeline agents** in production — the long-running V2 + V14 + V17 + H2 stack named in `RELIABILITY.md` §"Long-Running Autonomous Agent".
- **Aviation-derived precedent** — pilot-as-supervisor under modern autopilot (Sheridan; Parasuraman, Sheridan & Wickens) — the operational template the agent-design community has been deliberately importing since 2024.

## Related Patterns

- **Sibling of** **V1 Human-in-the-Loop** — same concern (human oversight), different architecture: V1 blocks; V2 monitors. See Conflicts §10 — choose by action characteristics, not operational preference.
- **Required by** **V14 Trajectory Logging** — V2 is meaningless without a trace the supervisor can watch. V14 is the precondition.
- **Pairs with** **V10 Checkpointing** — the interrupt path needs a coherent state for the supervisor to inspect and edit before resume.
- **Pairs with** **V9 Bounded Execution** — V2's soft supervision plus V9's hard caps is the production posture; V9 catches what the monitor missed.
- **Pairs with** **V17 Online Evaluation** — V17's quality, safety, and cost signals are the natural trigger source for V2's monitor.
- **Uses** **V15 LLM-as-Judge** — when the Monitor is LLM-based, it is a judge over the trace; same evaluator structure.
- **Composes with** **R4 ReAct**, **O6 Orchestrator-Workers**, **O8 Loop Agent** — the autonomous loops V2 wraps.
- **Distinct from** **H6 Continuous Inner Monologue** — H6's "agent watches itself" is internal monitoring; V2 is external. H6 can supplement but not replace V2.
- **Competes with — and partitions against** **V1 Human-in-the-Loop** — the same workflow often needs both: V1 for the irreversible subset of actions, V2 for the rest.

## Sources

- Sheridan, T. B. — foundational work on human supervisory control (1960s–1990s), the operational template HOTL inherits.
- Parasuraman, R., Sheridan, T. B., & Wickens, C. D. (2000) — "A Model for Types and Levels of Human Interaction with Automation" (*IEEE Trans. SMC*) — the canonical taxonomy of human-automation roles.
- 12-Factor Agents, Factor 6 — Launch/Pause/Resume (Dex Horthy, HumanLayer, 2025) — the agent-design articulation of monitor-and-interrupt.
- Anthropic (2025) — "Building Effective Agents" and "Measuring AI Agent Autonomy in Practice" — the shift from per-action approval to trace-monitoring as operators gain experience.
- EU AI Act, Article 14 — human oversight as a flexible requirement scalable by risk; "in-the-loop" and "on-the-loop" both qualify as oversight modes.
- Composio AI Agent Report (2025) — 88% production failure rate; the calibration prerequisite V2 inherits.
- OpenTelemetry GenAI Semantic Conventions (CNCF, 2024–25) — the trace format V2's supervisor consumes.
- Zheng et al. (2023) — "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" — judge-bias literature relevant to LLM-based monitors.
