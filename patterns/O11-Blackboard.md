# O11 — Blackboard System

> Coordinate specialist agents through a central shared memory they all read and write, with a control unit that activates the next agent based on the board's current state — so coordination emerges from the data rather than from a fixed plan.

**Also Known As:** Shared Memory Board, Global Workspace, bMAS (Blackboard Multi-Agent System), Central Knowledge Accumulator.

**Classification:** Category IV — Orchestration · Band IV-C Specialised Coordination · a *coordination-by-state* pattern — agents are activated by what is on the board, not by a planner that assigns them.

---

## Intent

Replace a fixed plan or a central orchestrator's task assignments with a shared memory whose evolving state, read by a thin control unit, decides which specialist runs next — so the set and order of contributors adapts to what has accumulated, not to what was decreed up front.

## Motivation

Two orchestration patterns sit close to this one and fail at opposite ends.

**O6 Orchestrator-Workers** centralises decomposition in a single LLM that decides, at each step, what sub-tasks to dispatch and to whom. It works when the orchestrator can hold the whole problem and the worker catalogue in its head — true for research, coding, document work at moderate scale. It breaks when the agent catalogue is large or heterogeneous: the orchestrator must "know each agent's expertise" precisely, which becomes infeasible as the population grows or the data lake widens. The bMAS paper (Liu et al., 2025) shows exactly this failure on data-lake discovery and proposes the blackboard as the fix.

**K10 Long-Term Memory** is a shared substrate — agents could in principle write to it and read from it. But K10 is *passive*: it is a store, retrieved by similarity, with no mechanism to *trigger* anyone. Nothing happens to the system when the store changes. A blackboard is the active counterpart: a write *changes which agent fires next.* The store is half the pattern; the **control unit watching the store** is the other half. K10 plus a control loop *is* O11; K10 alone is not.

The blackboard architecture, first formalised in Hearsay-II (Erman et al., 1980) and grounded cognitively in Baars's Global Workspace Theory (1988), resolves both failures with one move. A central memory holds every observation, partial conclusion, and request. Agents — called *knowledge sources* in the classical formulation — *subscribe* to states they can act on; a thin **Control Unit** scans the board and activates whichever subscriber is most relevant to the current state. No agent talks to another agent. No central planner holds the whole problem in one head. The decomposition is the trajectory of the board.

The defining claim is structural: *what runs next is a function of the board's state, not of a plan.* That is what makes O11 distinct from O6 (which plans) and from K10 (which only stores). When the agent population is large and heterogeneous, or when the problem shape is genuinely unknown until evidence accumulates, this state-driven coordination outperforms top-down delegation — empirically, bMAS reports 13–57% improvement in end-to-end success on data-lake discovery over master-slave baselines, with lower token cost (Liu et al., 2025).

The token efficiency comes from context bounding (mechanism 6). Rather than one orchestrator accumulating all partial results in its context, specialists read only their subscribed board slice. The Control Unit reads a structured board summary, not a growing conversation transcript. Each specialist's n² attention cost (mechanism 2) is paid over a targeted board slice, not over the full accumulation. The bMAS lower-token-cost result is structurally explained by this context bounding. (Mechanisms 2, 6.)

## Applicability

Use Blackboard when:

- the agent population is large, heterogeneous, or open — a central planner cannot reliably enumerate "who does what";
- the problem shape is genuinely unknown until evidence accumulates — the right next move depends on what has just been written;
- multiple specialists need to see one another's intermediate conclusions to make their own decisions (mutual context, not isolation);
- the audit trail of *how* a conclusion was reached matters as much as the answer itself.

Do not use it when:

- the sub-task decomposition is knowable up front and adaptive at runtime — use **O6 Orchestrator-Workers**; an LLM planner is simpler than a state-driven control unit;
- the workflow is fixed sequence — use **O2 Prompt Chaining**;
- the sub-tasks are independent and enumerable — use **O4 Parallelization**;
- specialists must not see one another's partial work (privacy, prompt-injection isolation) — use **O17 Agent Isolation**;
- you only need persistent shared knowledge with no triggering behaviour — use **K10 Long-Term Memory** as a passive store.

## Decision Criteria

O11 fits when coordination cannot be planned in advance and the next action genuinely depends on what has accumulated.

**1. Count the specialists.** How many distinct agents would a planner need to know about? **$\leq$ 5–10** $\to$ an O6 Orchestrator can hold the catalogue; an LLM planner is simpler. **> 10**, heterogeneous, or open-ended $\to$ an orchestrator's expertise model collapses; O11's volunteer / control-unit selection scales better.

**2. Test plan-ability.** Can you write the sub-task list before seeing the input? Yes $\to$ **O2 Prompt Chaining** or **O4 Parallelization**. No, but a smart LLM could plan it once given the input $\to$ **O6 Orchestrator-Workers**. No, and the plan must keep changing as evidence accumulates $\to$ O11.

**3. Score the inter-agent dependency.** Does specialist B's contribution depend on what specialist A *wrote*? Yes $\to$ O11 (the board is the medium). No, contributions are independent $\to$ O4 Parallelization. If only the synthesiser needs to see everyone's work, O6 is sufficient.

**4. Cost the control loop.** O11 adds a Control-Unit decision per cycle (typically one small LLM call or rule-based scan). Cycles per problem $\times$ cost per scan must be cheaper than the alternative. If the control LLM is mid-tier and 5–20 cycles resolve most problems, the budget is usually favourable; the bMAS paper reports lower total token cost than master-slave baselines on its benchmarks.

**5. Termination discipline.** Pair with **V9 Bounded Execution** — set a hard cap on cycles. An emergent loop without a cap can ping-pong specialists indefinitely. Pair with **V14 Trajectory Logging** — the board *is* the trajectory; persist it.

**Quick test — O11 is the right pattern when:**

- the specialist population is too large or heterogeneous for an orchestrator to plan over, *and*
- the next move genuinely depends on what has just been written to the shared state, *and*
- specialists need to see one another's partial work to do their own job, *and*
- the cycle count can be bounded (V9) and the trajectory logged (V14).

If only one or two of those hold, prefer **O6 Orchestrator-Workers** — it is simpler, more debuggable, and gives the same dynamic decomposition for moderate-scale agent pools. If you only need a shared store with no triggering, use **K10 Long-Term Memory** directly.

## Structure

```
                       ┌─────────────────────────────────────┐
                       │            BLACKBOARD               │
                       │  ┌─────────────┐  ┌───────────────┐ │
                       │  │  public     │  │  private      │ │
                       │  │  entries    │  │  scratchpads  │ │
                       │  └─────────────┘  └───────────────┘ │
                       └────────▲────────────────▲───────────┘
                                │ read/write     │ read/write
                                │                │
        ┌───────────────────────┼────────────────┼───────────┐
        │                       │                │           │
        ▼                       ▼                ▼           ▼
    Agent A             Agent B            Agent C    …  Agent N
   (planner)           (retriever)        (critic)     (specialists)
        ▲                       ▲                ▲           ▲
        │                       │                │           │
        └───────────────────────┼────────────────┴───────────┘
                                │ activate
                       ┌────────┴────────┐
                       │  CONTROL UNIT   │ ◀── reads board state,
                       │  (scan + pick)  │      picks next agent,
                       └─────────────────┘      stops when done (V9)
```

Agents do not call each other. Every contribution lands on the board; every activation comes from the Control Unit's read of the board.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Blackboard** | the shared state — public entries, per-agent private scratchpads, an append-only log | reads/writes from any agent $\to$ updated state | be edited in place without leaving an audit entry; conflate public broadcast with private working notes. |
| **Board schema** | the structure of an entry (kind, author, references, timestamp) | — $\to$ editable shape | be unenforced — schema-free entries make the Control Unit's job impossible. |
| **Control Unit** | the *activate-which-agent-next* decision | current board state + agent catalogue $\to$ next agent to fire (or HALT) | execute the task itself, or plan multiple steps ahead. A planning Control Unit is just an O6 Orchestrator with extra steps. |
| **Specialist Agents** | one bounded competence each (planner, retriever, critic, domain expert, synthesiser) | board slice they subscribe to $\to$ new entries | call each other directly; they communicate only via the board. They also must not write outside their declared competence. |
| **Subscription / trigger rules** | the mapping from board states to eligible agents | board state $\to$ subset of agents that can fire | be hard-wired as a fixed sequence — that collapses O11 back into O2 Prompt Chaining. |
| **Termination predicate** | the *we are done* test (and the *we are stuck* test) | board state $\to$ halt / continue / fail | be missing. Without it, the loop runs until V9's cap fires every time. |

The Control Unit and the Specialists are kept as separate sessions. **The Control Unit reads; the Specialists write.** Mixing them — a Specialist that also picks the next agent — is the pattern's most common failure mode: contribution and coordination authority bleed together, and the board becomes whatever the loudest agent decided to make it.

## Collaborations

A problem arrives and is posted as the first public entry on the Blackboard. The Control Unit scans the board: which subscription rules match the current state? Of the eligible Specialists, which is most relevant — by competence, by recency of relevant entries, by what is still missing? It activates one. That Specialist reads the board slice it cares about, does its work in its own context, and writes new entries — public broadcasts everyone can see, plus optional private notes only it will revisit. Control returns to the Control Unit. It rescans, picks again, fires again. The cycle continues until the Termination predicate fires (problem solved, consensus reached, halt requested) or **V9 Bounded Execution** caps the loop. The whole transcript — every read, every write, every activation — is the **V14 Trajectory Logging** record by construction; the board *is* the audit trail.

## Consequences

**Benefits**
- Coordination scales beyond an orchestrator's working-memory limit — the Control Unit needs only the *current* state, not the full plan or every agent's CV.
- Heterogeneous specialists compose without bespoke wiring; adding a new agent is a new subscription rule.
- Contributions are mutually visible — specialists build on each other's partial conclusions instead of working in isolation.
- The board is the trajectory; audit, replay, and post-mortem are inherent.
- Empirically lower token cost than rigid master-slave pipelines on open-ended discovery tasks (bMAS).

**Costs**
- Control-Unit calls per cycle add latency and tokens on the critical path.
- Schema discipline is mandatory — without it, the Control Unit cannot reason over the board reliably.
- Concurrent writes require ordering / locking; the board is a contention point.
- Debugging emergent coordination is harder than debugging an explicit plan.

**Risks and failure modes**
- *Board pollution* — irrelevant or contradictory entries accumulate, degrading every subsequent Control-Unit decision. Mitigate with retention policy and pruning rules.
- *Control-Unit oscillation* — two subscription rules keep ping-ponging between two agents. Mitigate with hysteresis, cycle limits (V9), and a Termination predicate that names "stuck".
- *Schema collapse* — agents write free-form prose into structured fields; the board degrades into noise. Enforce schema at write time.
- *Specialist over-reach* — an agent writes outside its competence (e.g. a retriever offering critiques). Constrain at the Specialist's setup (S5 Constraint Framing).
- *Prompt-injection blast radius* — an attacker landing instructions on the board reaches every subsequent Specialist. If untrusted content can hit the board, partition it via **O17 Agent Isolation**.

## Implementation Notes

- Start with a deliberately small schema: `{kind, author, references, content, timestamp}`. Add structure only when the Control Unit demonstrably misses it.
- Separate **public** entries (visible to all) from **private** scratchpads (visible to one agent). Public is for broadcast; private is for working notes that would clutter every other agent's read.
- The Control Unit can be either an LLM (judgement over the board) or a deterministic rule engine (subscription patterns over schema fields). Start with the rule engine; promote to LLM only when rules cannot capture the next-move decision.
- Bound the loop with **V9** — a hard cap on cycles, and a softer cap on cycles since the last *new* contribution (stuck-detector).
- Treat the board as **V14 Trajectory Logging** material — persist every cycle, including the Control-Unit's reason for the activation it chose. That reason is the highest-value debugging artefact.
- Pair with **K10 Long-Term Memory** when learnings should outlive a single problem — at end of run, distil the board into K10 entries; do not promote the raw board.
- For prompt-injection-sensitive deployments, gate any agent that writes from untrusted sources through a Quarantined Specialist (V4 / O17 Agent Isolation); only sanitised conclusions land on the public board.
- Resist the temptation to let the Control Unit "just answer when it can". A Control Unit that produces content is no longer a Control Unit — it is an O6 Orchestrator.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** O11 chains a **Control Unit** session that reads the board with a population of **Specialist** sessions that write to it, against a structured Blackboard store. It composes with **V9 Bounded Execution** (cap the cycles), **V14 Trajectory Logging** (the board *is* the log), **K10 Long-Term Memory** (distil board $\to$ store at end of run), and **O17 Agent Isolation** when untrusted content reaches the board.

**The chain — one cycle:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Read board + agent catalogue; produce list of eligible agents | `code` | subscription rules |
| 2 | Control Unit picks the next agent (or HALT) | `LLM` (or rule) | Control session |
| 3 | Branch — HALT $\to$ return; otherwise fire the chosen Specialist | `code` | V9 cap |
| 4 | Specialist reads its board slice and contributes | `LLM` | the chosen Specialist's session |
| 5 | Append new entries to the board with schema validation | `code` | schema |
| 6 | Termination check — done? stuck? cycle limit? | `code` (or small `LLM`) | V9 |
| 7 | If not terminal, loop to 1 | `code` | |

**Skeleton:**

```
blackboard_run(problem, agents, board):
    board.append(public_entry(kind="problem", content=problem))    # code
    for cycle in range(MAX_CYCLES):                                 # code  — V9
        eligible = subscriptions.match(board.state(), agents)       # code
        choice   = ControlUnit(board.state(), eligible)             # LLM   → agent name or HALT
        if choice == "HALT": break                                  # code
        slice    = board.slice_for(choice)                          # code
        entries  = Specialist[choice](slice)                        # LLM   — the picked specialist
        board.append_all(schema.validate(entries))                  # code
        if Terminate(board.state()): break                          # code (or small LLM)
    return Synthesise(board.public_entries())                       # LLM (often the Control Unit's final pass, or a separate session)
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Control Unit** | mid-tier generalist (judgement over short structured input) — *or* a deterministic rule engine when subscriptions cover the decision space | role: *"you pick the next agent to act on a shared workspace"*; the agent catalogue (name, competence, when to fire); the schema of board entries; output contract (one agent name or `HALT`); explicit ban on doing the work itself | the current board state (or the schema-projected summary of it) |
| **Specialist (one session per agent)** | varies by competence — small fast for retrievers / critics; main generalist for synthesisers; domain-tuned where available | role for this specialist (S3); its bounded competence (S5 Constraint Framing); the board entry schema (S6 Output Template); the subscription rule that activated it (so it understands *why* it was chosen) | the board slice it subscribed to + the request that activated it |
| **Synthesiser** *(often the Control Unit's final pass)* | the main generalist | role: *"you produce the final answer from the public board entries"*; output contract for the final answer | the public board entries |

**Specialist-model note.** No fine-tune is required, but two structural decisions shape the build:

- **Control Unit and Specialists are separate sessions, always.** Same model is fine; mixing the prompts produces a Specialist that picks itself, or a Control Unit that answers the question. Both kill the pattern.
- **The Control Unit benefits from a long-context model** so that, at high cycle counts, it can see the whole board rather than a lossy summary. The Specialists do not need long context — they only see their subscribed slice. Spend the long-context budget on the coordinator, not the workers. As cycle count rises, the board grows and the Control Unit must reason over more entries. This is the U-shaped recall problem (mechanism 4) applied to a growing board: entries from early cycles are in the middle of the Control Unit's context by the time late cycles run, and are geometrically under-attended. Design the board schema so the Control Unit sees a recency-ordered summary, not the full append-only log, to keep the most relevant recent entries near the context boundary. (Mechanisms 2, 4.)

## Open-Source Implementations

- **Flock** — [`github.com/whiteducksoftware/flock`](https://github.com/whiteducksoftware/flock) — a declarative blackboard multi-agent framework. Agents subscribe to Pydantic-typed data contracts rather than being wired to each other; loose coupling and automatic parallelisation follow. Ships visibility controls, semantic routing, persistent storage, OpenTelemetry tracing. Closest production-quality match to the structure shown above.
- **Agent Blackboard** — [`github.com/claudioed/agent-blackboard`](https://github.com/claudioed/agent-blackboard) — multi-agent coordination for software-engineering tasks with nine specialists communicating through an MCP-based shared knowledge repository; embedding-based retrieval over the board; optional SQLite persistence.
- **bMAS reference (Liu et al., 2025)** — paper at [arxiv.org/abs/2510.01285](https://arxiv.org/abs/2510.01285); the empirical study behind the SOTA-at-lower-cost claim for blackboard-based MAS on data-lake information discovery. No public canonical code release at time of writing; the paper is the spec.
- **Terrarium** — [`arxiv.org/abs/2510.14312`](https://arxiv.org/abs/2510.14312) — a blackboard-based testbed framework for studying multi-agent safety, privacy, and security; useful as a reference design for the security-hardened variant (untrusted content via Quarantined Specialists).

## Known Uses

- **Data-lake information discovery** — the bMAS benchmark setting: a central agent posts data needs to the board; partition-specific and web-retrieval agents volunteer based on capability; the board accumulates evidence until the discovery query is resolved (Liu et al., 2025).
- **Multi-specialist coding agents** — frameworks like Flock and Agent Blackboard run domain specialists (API design, backend, DDD, observability) that contribute to a shared engineering board rather than going through a central planner.
- **Hearsay-II speech understanding** (1976–1980) — the classical reference: blackboard with public hypothesis space, knowledge sources at multiple linguistic levels (phonetic, lexical, syntactic, semantic), scheduler picking the next KS by board state. The architecture every modern blackboard system inherits from.
- **Safety / security testbeds** — Terrarium uses the blackboard precisely because every interaction is logged on the board, making attack-vector studies tractable.

## Related Patterns

- **Distinct from** O6 Orchestrator-Workers — O6 has a planner LLM that *decides* the decomposition; O11 has a Control Unit that *reacts to* the board state. O6 is top-down; O11 is state-driven. For $\leq$ 5–10 specialists with a planable decomposition, prefer O6.
- **Distinct from** K10 Long-Term Memory — K10 is a passive store retrieved by similarity; O11 adds the Control Unit that *triggers* agents on board state. K10 + a control loop = O11; K10 alone is just storage.
- **Distinct from** O2 Prompt Chaining — O2 hard-wires the sequence; O11's sequence is emergent from subscription rules and board state.
- **Pairs with** K10 — distil end-of-run board contents into K10 entries so learnings persist across problems; the board is per-problem, K10 is cross-problem.
- **Pairs with** V14 Trajectory Logging — the board *is* the trajectory record; persistence and audit come for free.
- **Required by** V9 Bounded Execution — without a cycle cap and a stuck-detector, an emergent loop becomes **A3 Uncontrolled Recursion**.
- **Composes with** O17 Agent Isolation — when any board input is untrusted, route it through a Quarantined Specialist first; only sanitised conclusions land on the public board.
- **Composes with** O4 Parallelization — multiple Specialists subscribing to the same state can fire in parallel if their writes do not conflict; Flock makes this the default.
- **Cognitive grounding** — Global Workspace Theory (Baars, 1988): conscious processing as broadcast to a shared workspace from which the next specialist activation is drawn. The Theater of Mind paper makes this mapping explicit.
- **Historical ancestor** — Hearsay-II (Erman et al., 1980): the canonical pre-LLM blackboard system; every participant, structure element, and failure mode listed above has a Hearsay-II antecedent.

## Sources

- Liu et al. (2025) — "LLM-Based Multi-Agent Blackboard System for Information Discovery in Data Science." [arXiv:2510.01285](https://arxiv.org/abs/2510.01285). Reports 13–57% gain in end-to-end success and lower token cost vs master-slave baselines.
- Bo et al. (2025) — "Exploring Advanced LLM Multi-Agent Systems Based on Blackboard Architecture." [arXiv:2507.01701](https://arxiv.org/abs/2507.01701). Dynamic agent selection over a shared workspace; iterative consensus.
- Wei et al. (2025) — "Terrarium: Revisiting the Blackboard for Multi-Agent Safety, Privacy, and Security." [arXiv:2510.14312](https://arxiv.org/abs/2510.14312). Blackboard as a safety / security testbed.
- Erman, L. D., Hayes-Roth, F., Lesser, V. R., Reddy, D. R. (1980) — "The Hearsay-II Speech-Understanding System: Integrating Knowledge to Resolve Uncertainty." *ACM Computing Surveys* 12(2). The canonical pre-LLM blackboard system.
- Baars, B. J. (1988) — *A Cognitive Theory of Consciousness.* Cambridge University Press. Global Workspace Theory — the cognitive grounding the Theater of Mind paper makes explicit for O11.
