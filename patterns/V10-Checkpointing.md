# V10 — Checkpointing

> Persist the agent's complete working state to an external durable store at every meaningful step, so any failure, interruption, or human pause can be resumed — or rolled back — from the last known-good snapshot rather than restarted from zero.

**Also Known As:** State Snapshot, Agent State Persistence, Savepoint, Durable Execution (when paired with replay), Pause-and-Resume State.

**Classification:** Category V — Reliability · the recovery pattern that turns long-running agents from "best-effort" into "resumable" — required by V1 (Human-in-the-Loop) for meaningful pauses, by V9 (Bounded Execution) for graceful termination, and by O15 (Agent Handoff) for state transfer.

---

## Intent

Externalise the agent's working state to a durable store at each step boundary, so failures, terminations, and human pauses become resumable events instead of restart-from-zero events.

## Motivation

An agent running a multi-hour task — a research run, a code-modification session, a long planning chain — accumulates state at every step: the plan, the partial results, the tool-call history, the working memory, the position in the loop. If that state lives only in the process's memory, a single crash, timeout, network blip, or human-approval pause wipes the lot. The next run starts from zero, re-pays every token cost already spent, and is not guaranteed to make the same choices.

Three production scenarios force the issue:

- **Failure recovery.** A tool call times out at step 17 of 20. Without a checkpoint at step 16, the work of steps 1–16 is lost and the agent must redo them — often non-deterministically, sometimes diverging from the original trajectory and producing a different (and possibly worse) outcome.
- **Human-in-the-loop pauses (V1).** The agent reaches a decision point that requires human approval. Approval may take hours or days. The process cannot stay resident for that long. The mechanistic reason is that the model's KV cache — the 4D tensor [num_layers $\times$ seq_len $\times$ num_kv_heads $\times$ d_head] that stores the computed key-value pairs for the current session — exists only in GPU memory during an active inference session and is not persisted between API calls (mechanism 3). Each new invocation starts with an empty cache and pays full prefill cost on the context provided. Checkpointing externalises the agent's *application state* (plan, partial results, position in the loop) so that a fresh invocation can reconstruct where it left off, even though it cannot recover the prior KV cache state. Without checkpointing, V1 is theoretical; with it, the agent simply suspends, the state lives in a database, and resumption is a fresh load.
- **Bounded-execution termination (V9).** The agent hits its iteration or cost cap. Without a checkpoint, the work done up to the cap is discarded — bounded execution becomes a pure-loss circuit breaker. With a checkpoint, the cap is a *pause*, not a *drop*, and a human (or a higher budget) can resume.

The 12-Factor Agents framework names both halves of this problem: Factor 5 ("Unify execution state and business state") and Factor 6 ("Launch/Pause/Resume with simple APIs"). Database savepoints, workflow orchestrators (Temporal, DBOS, Restate), and Kubernetes job-checkpointing all solve the same underlying problem in their own domains. V10 is what they look like when the running process is an LLM agent loop.

The pattern's defining move is to make state **explicit, serialisable, and external**. The agent function itself stays stateless (that is V12 Stateless Reducer's job); state lives in a store keyed by session ID and is reloaded fresh on every invocation.

## Applicability

Use Checkpointing when:

- the agent runs long enough that failure or interruption is realistic (multi-step plans, long-horizon research, multi-turn human-in-the-loop workflows);
- V1 (Human-in-the-Loop) is on the table — meaningful pauses are not possible without it;
- V9 (Bounded Execution) is in force — checkpointing is what makes a hit limit recoverable instead of pure loss;
- O15 (Agent Handoff) is required — the state must be serialised to transfer between agents;
- partial completion has value — losing the work done before a failure is genuinely costly.

Do not use it when:

- the agent is a single-shot, sub-second call where failure simply means retry from the original prompt — V10 is overhead for no benefit; rely on **V9 Bounded Execution** alone for cost control;
- the task is genuinely stateless (a classifier, a translator, a structured-output extractor) — there is nothing to checkpoint; ensure **V12 Stateless Reducer** holds and stop there;
- the state is so large or unserialisable that snapshotting dominates step cost — refactor the agent toward V12 first (externalise the heavy state to its natural store) before adding V10 on top.

## Decision Criteria

V10 is right when the cost of losing in-progress work, or the inability to pause for review, exceeds the cost of snapshot storage and serialisation.

**1. Measure expected work-loss without it.** Estimate the agent's mean-time-to-failure (MTTF) and mean task duration (T). If T $\geq$ 10% $\times$ MTTF, work loss without checkpointing is material. Below 1%, V10 is overhead; **V9 Bounded Execution** alone is enough. Note that prefix caching (mechanism 5) can recover some of the prefill cost if a stable, lengthy system prompt is re-sent on resume — configure the checkpoint load to prepend the full system prompt before the restored state to allow the provider to serve it from cache.

**2. Pause requirement.** Is V1 (Human-in-the-Loop) required for any action in the agent's repertoire? If yes, V10 is mandatory — there is no other way to pause a stateful agent without dropping its state. No pause requirement and no V1 dependency $\to$ V10 is optional.

**3. Checkpoint granularity.** Choose where the snapshot boundary sits:
   - **Every step** — strongest recovery; highest write cost. Default for high-stakes, low-throughput agents.
   - **Significant events** (tool call, plan revision, human gate) — balanced; the usual production choice.
   - **Periodic** (every N steps or every X seconds) — cheapest; loses up to N steps on failure. Acceptable for low-stakes high-throughput agents.
   If the choice is unclear, start at *significant events* and tune from measured loss.

**4. Serialisability check.** Can the agent's full state be expressed as a JSON-serialisable (or equivalent) object? If not, the agent has hidden state — fix that first via **V12 Stateless Reducer**. Trying to checkpoint a stateful agent leaks state silently between runs.

**5. Restore-tested-or-theoretical.** Snapshots that are never restored are write-only and indistinguishable from a bug. Decision criterion: have you executed at least one restore from a checkpoint in test, end-to-end, in this session? If not, V10 is unverified — closer to liability than safety net. Pair with **V18 Agent Simulation** for systematic restore tests.

**Quick test — V10 is the right pattern when:**

- the task is long enough that failure costs real work (T $\geq$ 10% of MTTF), *and*
- pause-for-review or graceful termination is a real requirement (V1 or V9 in play), *and*
- the agent's state is — or can be made — fully serialisable, *and*
- a restore path has been exercised, not just designed.

If the task is short-lived and self-contained, skip V10 and bound it with V9 alone. If state is not serialisable, fix that via **V12 Stateless Reducer** before adding V10. If you have V10 but no human will ever pause and no V9 cap will fire, the snapshots are dead weight — confirm there is a recovery path that actually uses them.

## Structure

```
  Agent invocation (session_id, input)
         │
         ▼
   ┌──── Load: state ← Checkpoint Store[session_id] ────┐
   │                                                     │
   │     (V12) Agent(state, input) → (output, state')    │
   │                                                     │
   │     Save: Checkpoint Store[session_id] ← state'     │
   │                                                     │
   └─────────────────────────────────────────────────────┘
                          │
              ┌───────────┼───────────────┬──────────────┐
              ▼           ▼               ▼              ▼
          continue      pause            fail        terminate
         (next step)  (V1 wait)     (rollback to    (V9 cap hit)
                                    last good)
                                                       │
                                                       ▼
                                                resume later
                                                from state'
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **State Serialiser** | turning the in-memory agent state into a durable representation | live state object $\to$ bytes / JSON / row | leak references to in-process resources (open sockets, file handles, secrets) — those do not survive serialisation and corrupt the snapshot. |
| **Checkpoint Store** | durable, external storage of snapshots keyed by session and step | (session_id, step, state) $\to$ ack; (session_id, step?) $\to$ state | be in-process memory. An in-memory checkpointer is a development convenience, not a production component. |
| **Checkpoint Policy** | deciding *when* to checkpoint (every step, significant event, periodic) | step event $\to$ save or skip | be the agent itself. If the agent decides when to checkpoint, it can quietly skip the snapshot before a risky action. |
| **State Loader** | hydrating a fresh agent invocation from a stored snapshot | (session_id, step?) $\to$ state | mutate the snapshot during load — the store is the source of truth; the loader returns a copy. |
| **Restore Verifier** *(optional but recommended)* | confirming that a loaded snapshot reproduces the prior agent state correctly | loaded state + expected hash/invariants $\to$ ok/fail | be skipped in production. Silent restore corruption is worse than no checkpoint at all. |
| **Agent Function** | producing `(output, state')` from `(state, input)` — pure, stateless | (state, input) $\to$ (output, state') | hold any state of its own. This is V12 Stateless Reducer's job, and the only way V10 stays clean. |

The split between *Agent Function* and *Checkpoint Store* is the discipline of the pattern. The agent never persists anything itself; the framework around it does. Conflating the two — letting the agent "remember" between calls — is the failure mode that turns V10 into theatre.

## Collaborations

A new step begins. The framework loads the current state from the Checkpoint Store under the session ID (`State Loader`) and hands it to the stateless Agent Function (V12) along with the input. The agent computes its output and a new state. The framework asks the Checkpoint Policy whether *this* step is a save point; if yes, the State Serialiser produces a durable representation and the Checkpoint Store persists it under `(session_id, step+1)`. The output goes back to the caller; the loop continues, pauses (V1 waiting for a human), or terminates (V9 cap hit, error, or completion). On any later resumption — minutes, hours, days later — the same session ID loads the last checkpoint and the loop continues exactly from there. On a detected failure, the framework rolls back to the prior known-good checkpoint and either retries or surfaces to V1 for human triage. V14 (Trajectory Logging) records the checkpoint write and load events as part of the audit trail.

## Consequences

**Benefits**
- Long-running tasks survive process failures, deploys, and network blips.
- V1 pauses become trivial — the agent simply suspends; resumption is a fresh load.
- V9 cap hits become recoverable — bounded termination saves the work done up to the cap.
- O15 Agent Handoff is a serialise-and-transmit of the checkpoint, not a special protocol.
- Debugging gains time-travel — a snapshot can be loaded into a sandbox and the next step replayed under a debugger.

**Costs**
- Storage and write latency at every checkpoint boundary.
- Serialisation discipline: every field in the state must be representable in the store's format.
- The Checkpoint Store becomes infrastructure to own — backups, retention, schema migration as the agent evolves.
- Versioning: when the agent's state shape changes, old checkpoints may be unloadable without a migration path.

**Risks and failure modes**
- *Untested restore.* Snapshots are written but never loaded; the first time a restore is needed, it fails silently or wrong.
- *Checkpoint corruption.* A bad write makes the latest snapshot unusable; without a chain of older snapshots, the work is lost anyway.
- *Hidden state leaks.* The agent quietly carries state in module variables or singletons; restored snapshots disagree with live execution.
- *Storage single point of failure.* The Checkpoint Store goes down; no agent can start or resume.
- *Version drift.* The agent code is upgraded; checkpoints written by the old version cannot be read by the new — and there is no migration script.
- *Snapshot bloat.* Each checkpoint contains the entire history because the state was never trimmed; storage and load latency compound.

## Implementation Notes

- **Externalise first, then snapshot.** V10 only works on top of V12 Stateless Reducer. If the agent has hidden state, fix V12 before adding V10 — otherwise the snapshots are wrong.
- **Keep snapshots compact.** State should hold what the next step needs, not a full trajectory log. Send full traces to V14 (Trajectory Logging), not into the checkpoint payload.
- **Chain, do not just overwrite.** Keep the last N checkpoints (or a checkpoint per significant event) rather than a single rolling snapshot. Rollback needs more than one point.
- **Test restore in CI.** Every code change to the state schema should run an automated `save → load → assert identical → next step` test. Untested restore is the most common failure mode (see Consequences).
- **Version the schema.** Tag each checkpoint with the agent and state-schema version. Migrations on load are cheap; debugging an unreadable checkpoint in production is not.
- **Choose the store by durability needs.** SQLite for single-process development; Postgres or a dedicated workflow store (Temporal, DBOS, Restate) for production multi-process agents. The LangGraph checkpointer interface decouples the choice from the agent code.
- **Snapshot before risky actions, not just after.** A checkpoint *before* a tool call lets you replay the call deterministically; a checkpoint *after* lets you skip a successful call on resume. Production systems usually want both.
- **Pair with V9 and V14.** V9 triggers the checkpoint before terminating on a cap hit; V14 logs the checkpoint event for audit. Without V9, checkpoints accumulate beyond bound; without V14, you cannot debug *why* a restore happened.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V10 wraps a stateless agent (V12) with a save/load harness against a durable store; it composes with **V9 Bounded Execution** (which triggers a final save before terminating), **V1 Human-in-the-Loop** (which pauses by exiting the loop and resuming on approval), **O15 Agent Handoff** (which serialises through the same checkpoint format), and **V14 Trajectory Logging** (which records the save/load events). The agent itself remains a Reasoning-or-Orchestration pattern unchanged — V10 is structural wiring around it.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Resolve session_id from request | `code` | |
| 2 | Load: state ← Checkpoint Store[session_id] (or initial) | `code` | State Loader |
| 3 | *(optional)* Verify loaded state against invariants/hash | `code` | Restore Verifier |
| 4 | Run one agent step: (state, input) $\to$ (output, state') | `LLM` | V12 Agent Function |
| 5 | Decide: should this step be a checkpoint? | `code` | Checkpoint Policy |
| 6 | If yes: serialise state' $\to$ durable form | `code` | State Serialiser |
| 7 | If yes: write Checkpoint Store[session_id, step+1] ← bytes | `code` | Checkpoint Store |
| 8 | Emit V14 trace event: checkpoint.write / checkpoint.load | `code` | V14 |
| 9 | Branch: continue loop / pause (V1) / terminate (V9) / fail (rollback) | `code` | V1, V9 |

**Skeleton** — the wiring; the only `# LLM` line is the agent step itself:

```
def invoke(session_id, input):
    state = store.load(session_id)                # code  — State Loader
    verify(state)                                 # code  — Restore Verifier (optional)
    while not done(state):
        output, state = agent(state, input)       # LLM   — V12 stateless step
        if policy.should_checkpoint(state):       # code  — Checkpoint Policy
            blob = serialise(state)               # code  — State Serialiser
            store.save(session_id, blob)          # code  — Checkpoint Store
            trace.emit("checkpoint.write", ...)   # code  — V14
        if v9.cap_hit(state) or v1.needs_human(state):
            store.save(session_id, serialise(state))   # final save before exit
            return suspended(output, state)       # caller resumes later
    return output
```

**The LLM sessions.** V10 has *one* LLM step — the agent function itself, and it is the agent already defined by whichever Reasoning/Orchestration pattern is in use (R4 ReAct, R3 Plan-and-Solve, O6 Orchestrator, etc.). V10 does not add LLM calls of its own.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent step** | the host pattern's chosen model | the host pattern's own setup (role, tools, schema) — V10 imposes no setup of its own | the loaded `state` + the current `input`; output must include the updated `state'` (or the host pattern's framework must extract it deterministically) |

**Specialist-model note.** None — V10 needs no specialist. The wiring is entirely deterministic code; the agent step uses whatever model the host pattern requires. The build dependency is *infrastructure*, not a fine-tune: a durable checkpoint store (SQLite/Postgres for self-hosted; LangGraph's checkpointer interface; or a managed workflow engine like Temporal / DBOS / Restate). Choose by durability and operational needs, not model capability.

## Open-Source Implementations

- **LangGraph checkpointers** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — the canonical agent-framework implementation. Defines a checkpointer interface (`BaseCheckpointSaver`) with in-memory, SQLite, and Postgres backends; every LangGraph node automatically writes a checkpoint on completion, making pause/resume and time-travel debugging first-class.
- **Temporal** — [`github.com/temporalio/temporal`](https://github.com/temporalio/temporal) — durable execution platform. Workflows checkpoint after every step; failed workers resume from the last completed step automatically. The closest match to V10 in the broader workflow-orchestration world; increasingly used as the spine of long-running agentic systems.
- **DBOS Transact (Python)** — [`github.com/dbos-inc/dbos-transact-py`](https://github.com/dbos-inc/dbos-transact-py) — durable execution as a Python library: annotated workflow/step functions checkpoint to Postgres; on restart, workflows resume from the last completed step. The lightest-weight production-grade checkpointing layer for Python agents.
- **Restate** — [`github.com/restatedev/restate`](https://github.com/restatedev/restate) — durable-execution platform with consistent state per entity; explicitly markets a "Durable AI Agents" use case. The right choice when the agent is part of a broader distributed system already using durable services.

For agents not built on any of the above, the pattern is straightforward to roll by hand on top of Postgres or any document store — the discipline is in the V12 separation, not the storage choice.

## Known Uses

- **LangGraph-based production agents** (LangChain Inc and downstream) — the default architecture is checkpointer-backed; pause-and-resume is shipped, not bolted on.
- **HumanLayer** and similar HITL platforms — the agent suspends to an inbox; the inbox approval triggers a load-and-resume from the stored checkpoint.
- **Claude Code and Cursor session resumption** — the IDE-agent's "resume session" flow is a V10 in spirit: the session state is persisted to disk and reloaded on a fresh process.
- **Temporal-backed agent services** at companies running long agentic workflows (research summarisation, multi-step automation) — the workflow engine provides the checkpoint layer beneath the LLM logic.

## Related Patterns

- **Composes with** V12 Stateless Reducer — V10 only works cleanly when the agent itself is stateless. V12 makes the snapshot total; V10 makes the snapshot durable. See CONFLICTS CRITICAL 8.
- **Required by** V1 Human-in-the-Loop — a meaningful human pause requires the agent to suspend and resume, which requires a checkpoint.
- **Required by** V9 Bounded Execution — a cap hit without a checkpoint loses the work done up to the cap; V9 calls V10 immediately before terminating.
- **Required by** O15 Agent Handoff — the handoff payload is the serialised checkpoint; the receiving agent loads it as its initial state.
- **Pairs with** V14 Trajectory Logging — V14 logs every checkpoint write and load event; together they give a complete audit trail.
- **Snapshot target overlaps** K8 Working Memory — if the agent uses K8's in-context scratchpad as its working state, the checkpoint serialises that scratchpad. K8 is the natural payload shape for V10.
- **Distinct from** V14 Trajectory Logging — V14 is append-only history *for humans/audit*; V10 is the current state *for the agent*. The trace is not a substitute for the state, and the state is not a substitute for the trace.
- **Distinct from** K10 / K11 / K12 (memory patterns) — those persist *knowledge* across sessions; V10 persists *execution state within or across* a session. K11's log can be one input to a V10 snapshot but is not itself the snapshot.
- **Note on fundamentality** — V10 passes the test: distinct Intent (durable execution state, not knowledge and not audit), distinct Participants (Serialiser, Store, Policy, Loader, Verifier), distinct Structure (load-step-save loop). It is not a variant of V12 (which is a design constraint on the agent function) nor of V14 (which is observability), and the composability tension with V12 (CONFLICTS CRITICAL 8) is resolved by externalising state — confirming V10 is its own pattern.

## Sources

- 12-Factor Agents (Dex Horthy, HumanLayer) — Factor 5 ("Unify execution state and business state") and Factor 6 ("Launch/Pause/Resume with simple APIs"). [`github.com/humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents).
- LangGraph documentation — Checkpointers and Persistence reference.
- Temporal — "Durable Execution" technical documentation; workflow-state persistence model.
- DBOS — "Durable Execution as a Library" technical writeup; Postgres-backed workflow checkpointing.
- Restate — durable-execution platform documentation; "Durable AI Agents" use-case page.
- ANSI SQL — `SAVEPOINT` semantics, the database antecedent of agent-state checkpointing.
- Nygard (2007) — *Release It!* — the broader stability-pattern family that V9 (Circuit Breaker) and V10 (Savepoint) descend from in software engineering practice.
