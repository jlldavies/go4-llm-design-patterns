# O10 — Swarm / Mesh

> Let peer agents hand control to each other directly — each active agent decides which peer takes over next — so coordination emerges from local handoff decisions rather than from a central supervisor.

**Also Known As:** Peer-to-Peer Agents, Decentralised Agents, Agent Mesh, Network of Agents, Multi-Agent Handoff Network.

**Classification:** Category IV — Orchestration · Band IV-B Agentic Patterns · a *decentralised* coordination pattern — there is no root supervisor; the currently-active agent is, transiently, the coordinator.

---

## Intent

Coordinate a fleet of specialised agents without a central orchestrator, by giving each agent the authority to hand control to any peer it deems better suited to the current step.

## Motivation

O6 Orchestrator-Workers and O7 Supervisor Hierarchy both centralise the *what-next* decision: a single supervisor (or a tree of them) reads the state and dispatches. That central node is also the central bottleneck — its context fills, its model becomes the single point of failure, and every routing decision pays its latency tax. Where the topology of the work is itself a network — customer-support flows where billing routes to refunds routes to retention; coding agents where the researcher hands to the implementer hands to the reviewer; role-played dialogues where speakers swap turn-taking — a tree is the wrong shape and a hub-and-spoke makes the hub the dumbest part of the system.

The swarm move is to remove the supervisor and embed the routing decision inside each agent. The currently-active agent owns the conversation; when its specialisation is exhausted or another agent fits better, it calls a *handoff tool* naming the peer that should take over and the context that peer needs. Control transfers; the new agent inherits the relevant state and continues. There is no one looking down at the whole system at any moment — each agent only sees the conversation up to its turn and decides locally whether to act or hand off.

This is structurally distinct from O7. In O7 the supervisor never executes work; it only decides. In O10 the agent that executes is the same agent that decides where to send the work next — *executor* and *router* collapse into one role per turn. That single difference changes the participant set, the failure modes, and the debugging story. Honest caveat: O10 is the **least production-proven** of the orchestration patterns. The current evidence base is libraries that *implement* the topology (LangGraph Swarm, the now-superseded OpenAI Swarm, CAMEL's role-playing) plus customer-support and role-play demos; published evidence of large-scale peer-to-peer production deployments is thin. Many systems labelled "swarm" in the wild are actually O7 with lightweight coordination. The pattern earns its number because the structure is distinct and reproducible — not because the deployment evidence is yet on par with O6 or O7.

## Applicability

Use when:

- the task topology is naturally a graph, not a tree — flows where any specialist can hand to any other (customer support, role-played dialogue, multi-stage creative pipelines with cycles);
- the set of specialisations is small (typically 2–8 agents) and well-named, so each agent can reasonably know which peer to hand to;
- routing depends on conversational *content* the active agent already holds, so passing the decision to a separate supervisor would just duplicate work;
- the failure cost of a missed handoff is low — the user can be re-routed, the conversation can recover.

Do not use when:

- the task has a single owning goal and a clear decomposition into sub-goals — use **O7 Supervisor Hierarchy** (or **O6 Orchestrator-Workers** if one level suffices);
- you need a single agent accountable for the final synthesis — swarms have no synthesiser by construction; use **O6**;
- agents must coordinate over shared accumulating state rather than via direct handoffs — use **O11 Blackboard System**;
- the routing is a fixed sequence — use **O2 Prompt Chaining**;
- the routing is a one-shot classification — use **O3 Routing** with specialised handlers;
- you cannot afford the debugging cost of decentralised control flow — most teams cannot; default to **O7**.

## Decision Criteria

O10 is right when the work is genuinely peer-to-peer in shape, the specialist set is small, and the team is willing to pay the debugging cost.

**1. Confirm the topology is a graph, not a tree.** List the legal transitions between agents. If they form a DAG with one root, you have O7 dressed up. If you have cycles (A $\to$ B $\to$ A $\to$ C $\to$ A) or any-to-any handoffs, the topology is genuinely a mesh. If every legal handoff actually goes through some "default" agent first, that default is a supervisor — switch to **O7**.

**2. Bound the agent count.** Each agent needs to know enough about each peer to route to it. The handoff-decision context grows with the square of agent count (every agent must consider every peer). Practical ceiling: **$\leq$ 8 specialised agents**. Beyond this, routing accuracy collapses and the supervisor's-eye view becomes necessary; switch to **O7**.

The routing-decision complexity grows with the number of peers each agent must reason over, and this compounds with the attention mechanism's own quadratic cost over sequence length (mechanism 2). Each active agent's context contains the conversation history (growing with turns) plus a peer-list description growing with agent count. A 10-agent swarm with a 50-turn conversation means each turn's active agent processes a context containing peer descriptions for 9 other agents, all embedded in a long shared history. The learned bilinear form Q_α K^α must discriminate which peer is relevant from an increasingly crowded K-space (mechanism 1). (Mechanisms 1, 2.)

**3. Score the routing-decision content.** Does the *active* agent already hold the information needed to choose the next agent? If yes — the user just said something that the active agent's specialisation can recognise as out-of-scope — O10 is natural. If a separate piece of context is needed (whole-task state, cross-agent coordination), the routing belongs in a supervisor; switch to **O7** or **O11**.

**4. Cost the debugging story.** O10 traces are graphs of handoffs, not call trees. A failed conversation can have been corrupted by any agent on the path. Confirm **V14 Trajectory Logging** is in place *before launch* — including which agent held control at each turn, why each handoff fired, and the context that transferred. Without V14 a swarm is operationally opaque.

**5. Loop and budget discipline.** Handoff cycles (A $\to$ B $\to$ A $\to$ B $\to$ …) are the catastrophic failure mode — agents bounce a hard request between specialisations none can solve. Pair with **V9 Bounded Execution** on (a) total turns, (b) handoffs per turn, and (c) cycle detection — if the same agent reactivates without progress, escalate to a human or fall back.

**Quick test — O10 is the right pattern when:**

- the legal handoff graph has cycles or any-to-any edges (not a tree), *and*
- specialist count is $\leq$ 8 and each peer's role is namable in one sentence, *and*
- the routing decision is recognisable from the active agent's own context, *and*
- V14 logging and V9 cycle-detection bounds are in place before launch.

If any condition fails, fall back. The default fallback is **O7 Supervisor Hierarchy** — almost all production "multi-agent with handoffs" workloads run cleaner as O7. If the coordination is over shared state rather than handoff messages, **O11 Blackboard System**. If a single classification suffices, **O3 Routing**. If you want the swarm topology but cannot pay the debugging tax, run **O6 Orchestrator-Workers** with the orchestrator imitating handoffs through explicit dispatches.

## Structure

```
       ┌─────────────────────────────────────────────────────────┐
       │  Shared conversation state (history + active-agent ptr) │
       └─────────────────────────────────────────────────────────┘
                              ▲
              read / write    │    read / write
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
       ┌─────────┐       ┌─────────┐       ┌─────────┐
       │ Agent A │◀────▶│ Agent B │◀────▶│ Agent C │
       │ (role)  │ hand-│ (role)  │ hand-│ (role)  │
       │ + hand- │ off  │ + hand- │ off  │ + hand- │
       │ off tool│ tool │ off tool│ tool │ off tool│
       └─────────┘       └─────────┘       └─────────┘

  At any moment, exactly one agent holds control. That agent either
  responds to the user or invokes handoff_to(<peer>) — control then
  transfers and the new agent's session takes over the next turn.
  No supervisor watches; the active-agent pointer in the shared state
  is the only "who is in charge" signal.
```

The handoff graph (which agent may hand to which) is the design-time artefact. The actual path through it is decided turn-by-turn by whoever holds control.

The shared conversation state grows monotonically with turns — this is the primary scaling risk. Unlike O17-isolated workers whose contexts are discarded after the task, swarm agents carry the full conversation history in their KV cache computation on every turn (mechanism 3). This makes O10 intrinsically more latency-sensitive to conversation length than O6+O17, where each worker's context is bounded regardless of prior turns. (Mechanisms 2, 3.)

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Peer Agent** *(one per specialisation)* | executing within its specialisation **and** deciding when to hand off | conversation state + user turn $\to$ response *or* handoff call | reach outside its specialisation to "help" with another agent's work — that is exactly what handoff is for. A peer that answers questions it should hand off destroys the routing structure. |
| **Handoff Tool** *(one per agent, lists its legal targets)* | the routing primitive — names the receiving peer and the context to transfer | `handoff_to(peer, brief)` $\to$ control transfer | be free-form ("transfer to whoever") — every handoff call must name a specific peer, or the routing structure dissolves into ad hoc forwarding. |
| **Shared State** | the conversation history and the active-agent pointer | reads / writes from all agents | be private to one agent — the next agent must see what happened, or every handoff resets the context. |
| **Handoff Graph** *(design artefact, enforced at tool registration)* | the legal peer-to-peer edges | static configuration $\to$ tool definitions | be implicit — undocumented "any agent may call any agent" produces cycles you cannot reason about. The graph is the contract. |
| **Trajectory Logger** *(required, not optional)* | the per-turn record of holder, action, handoff target, and reason | every turn $\to$ linked trace | be optional. A swarm without V14 has no "who did what when" view, and incidents become unrecoverable. |
| **Cycle Governor** *(required, not optional)* | detects handoff cycles, total-turn caps, and handoffs-per-turn caps | running trace $\to$ continue / escalate | be set only on total turns. Cycle detection is the load-bearing rule — A $\to$ B $\to$ A $\to$ B without progress is the primary failure. (See V9.) |

The pattern's load-bearing rule: **the handoff tool is the only legal cross-agent communication.** Any other mechanism (agents writing to each other's prompts, agents calling each other as functions, agents sharing private memory) collapses the structure and re-creates an implicit supervisor or an unauditable mesh.

## Collaborations

The user's turn arrives at whichever agent currently holds control (initially a designated entry agent). That agent reads the shared conversation state and decides: respond, or hand off. If respond, it writes its reply to the shared state and waits for the next user turn. If hand off, it calls its handoff tool naming a specific peer and the context the peer needs — a structured brief, often through an O15 Agent Handoff schema. The shared state's active-agent pointer flips; the named peer's session is invoked on the next turn and sees the full conversation up to that point plus the handoff brief. The Cycle Governor watches: if the same agent is reactivated within N turns without observable progress, or if total turns or handoffs-per-turn exceed budget, the system escalates (to a human, to a fallback agent, or to a halt). The Trajectory Logger records every handoff with timestamp, source, target, brief, and reason, so a failed conversation can be reconstructed end-to-end.

LangGraph Swarm runs exactly this shape: each agent is a LangGraph node with a `handoff_to_<peer>` tool per legal target; the shared graph state holds conversation history plus the active-agent pointer; on a handoff-tool call the framework rewires the next step to the named peer and continues. The OpenAI Swarm framework (now superseded by the Agents SDK) used the same "function-returns-an-agent" trick — a tool whose return value *is* the next agent — and the Agents SDK keeps the move under a cleaner `handoff()` helper. The topology is the same in all three: peer agents, peer handoffs, shared state, no supervisor.

## Consequences

**Benefits**
- No central bottleneck — each turn pays only the active agent's call cost; no supervisor pre-tax.
- Routing decisions ride on context the active agent already holds, avoiding a duplicate-context supervisor.
- Natural fit for graph-shaped task topologies (customer support, role-play, multi-specialty pipelines with cycles).
- Specialist agents stay small and focused; each only needs to know its own role and which peers it can hand to.

**Costs**
- Debugging is harder than O7 — traces are graphs, not trees; root-causing a bad conversation requires V14 from day one.
- Cycle risk — handoff loops between agents that each think the other should handle the request.
- No single agent owns the goal — synthesis (when needed) must be assigned to a designated agent or grafted on as an O6-ish layer.
- Handoff graph design is itself a hard problem; bad graphs produce dead-end agents or unreachable specialists.
- Production evidence is thinner than for O6 or O7 — most "swarm" deployments quietly degrade to O7.

**Risks and failure modes**
- *Handoff cycles* — A $\to$ B $\to$ A $\to$ B without progress; the canonical swarm failure. Mitigation: V9 cycle detection on the trace.
- *Greedy retention* — an agent that should hand off keeps answering ("I can probably help with this too"). Mitigation: explicit prompts that name the boundary, plus a coverage audit on which agents are *receiving* handoffs.
- *Orphan specialist* — an agent that no peer ever hands to. Mitigation: review the realised handoff graph against the design graph weekly.
- *Implicit supervisor* — one agent ends up as the default first-contact and the others rarely hand back; the swarm has collapsed to O7 with one supervisor and the rest as workers. If observed, accept the reality and switch to O7.
- *Stale context on handoff* — the receiving agent sees the conversation but not the *why* of the handoff; behaves as if newly invoked. Mitigation: structured handoff brief (S6 + O15), not just "transferring you now".
- *Production drift* — agents added over time without updating the handoff graph; emergent routing becomes unauditable. Mitigation: the handoff graph is a versioned artefact.

## Implementation Notes

- **Default to O7 first.** Build the system as a supervisor over workers; only switch to O10 when the supervisor's role is *purely* routing and routing depends entirely on the active agent's own context. Most teams discover at this point that O7 is still right.
- **Cap the agent count low** — start with 2–4 agents, scale to 8 only if every specialisation is earning its keep. Past 8, routing accuracy degrades.
- **The handoff graph is a first-class artefact.** Draw it, version it, review it. Audit the realised graph against the design weekly — orphan specialists and de-facto supervisors are both visible there.
- **Use O15 Agent Handoff** as the schema for what transfers between agents. Free-form briefs corrupt the receiving agent's context.
- **One handoff tool per agent, listing its legal targets explicitly** — never a single global `transfer_to(any_agent)` tool. The tool-shape encodes the graph.
- **V14 is non-negotiable.** Log: turn number, active agent, action (respond / handoff), target if handoff, brief if handoff, reason. Reconstruct any conversation end-to-end from this log.
- **V9 cycle detection** at handoff layer: same agent reactivated within N turns without progress $\to$ escalate. Total turns and handoffs-per-turn caps in addition.
- **Pair with O17 Agent Isolation** when an agent's specialisation needs a fresh context (e.g., one-shot tools that should not see the full conversation). Most swarm agents do *not* isolate — they need the shared history — but tool-execution sub-tasks within an agent often should.
- **Specialist roles must be namable in one sentence.** If you cannot describe an agent's role and boundary in one sentence, peers will not know when to hand to it.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** O10 chains a fleet of **peer agents** (each typically running **R4 ReAct** internally) over **shared conversation state**, with **O15 Agent Handoff** as the structured transfer mechanism, **V9 Bounded Execution** at the handoff layer (cycle detection + caps), **V14 Trajectory Logging** end-to-end, and **S6 Output Template** for the handoff-brief schema. The handoff *graph* is a design artefact; the per-turn handoff *decision* is the LLM step that makes O10 a pattern.

**The chain — per turn:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Load shared state; identify active agent | `code` | shared state |
| 2 | Active agent processes user turn and decides: respond or hand off | `LLM` | active agent's session |
| 3 | Branch on the decision | `code` | |
| 3a | If respond: write reply, return to user | `code` | |
| 3b | If handoff: construct brief; invoke handoff tool with target peer | `LLM` (tool call) $\to$ `code` | O15 schema |
| 4 | Update active-agent pointer; log the turn (holder, action, target, reason) | `code` | V14 |
| 5 | Cycle Governor checks: same-agent-without-progress / turn cap / handoff cap | `code` | V9 |
| 6 | On next user turn, loop to step 1 with the (possibly new) active agent | `code` | |

**Skeleton** — `run_turn` runs once per user message; the loop across turns is the conversation itself, not a tight inner loop:

```
run_turn(user_msg, shared_state, agents, handoff_graph):
    active = shared_state.active_agent                                 # code
    log_open(active, user_msg)                                          # code — V14

    decision = active.step(shared_state.history, user_msg)              # LLM   — respond or call handoff tool
    shared_state.history.append(active, user_msg, decision)             # code

    if decision.kind == "respond":
        log_close(active, "respond")                                    # code — V14
        return decision.reply

    # decision.kind == "handoff"
    target = decision.target                                            # named peer
    assert target in handoff_graph.targets_of(active.id)                # code — graph enforcement
    brief  = decision.brief                                             # O15 — structured handoff package

    shared_state.active_agent = target                                  # code — flip the pointer
    log_close(active, f"handoff -> {target} : {decision.reason}")       # code — V14

    governor.check(shared_state.history)                                # code — V9: cycles, caps
    # next user turn invokes run_turn again with active=target; no inner loop
    return acknowledge_handoff(target, brief)
```

**The LLM sessions** — every peer agent is configured the same *kind* of session, differing only in role and handoff targets:

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Peer Agent** *(one configured session per role — e.g. Triage, Billing, Refunds, Retention)* | capable generalist sized to the role (small fast for narrow specialists; strong for the entry / triage role that sees novel queries) | role: one-sentence specialisation + boundary; the list of **named peers it may hand to** and a one-sentence summary of each peer's specialisation; the **handoff tool schema** (target peer + brief); when-to-hand-off rules (*"if the request requires X, hand to peer Y"*); response format | the shared conversation history + the current user turn |
| **Handoff Brief Composer** *(optional; usually the Peer Agent emits the brief directly)* | same model as the handing-off agent | role: *"summarise the handoff context for the receiving peer"*; the O15 brief schema | the conversation history + the named target peer |

Concretely, for a **Triage** session in a customer-support swarm with peers `Billing`, `Tech`, and `Cancellation`: the setup loaded once is *"You triage incoming customer messages. If the message concerns invoices, payments, or refunds, call handoff_to_billing. If it concerns a technical issue with the product, call handoff_to_tech. If the customer wants to cancel, call handoff_to_cancellation. Otherwise, answer directly. When handing off, include a one-sentence summary of what the customer needs."* The per-call prompt wraps only the conversation history and the current message. The Billing, Tech, and Cancellation sessions are configured the same way with their own roles and their own (potentially overlapping) handoff target lists.

**Specialist-model note.** No fine-tuned specialist is structurally required. Pragmatic notes: (a) **The entry / triage agent benefits from the strongest available model** — its handoff decisions shape every conversation; mis-routing here cascades. (b) **Downstream specialists can be smaller** once routed — a Refunds agent only needs to be good at refunds. (c) The handoff *graph* is the load-bearing artefact, not any specific model — get the graph wrong and no model choice rescues the pattern.

## Open-Source Implementations

- **LangGraph Swarm (Python)** — [`github.com/langchain-ai/langgraph-swarm-py`](https://github.com/langchain-ai/langgraph-swarm-py) — the active canonical implementation; peer agents with `handoff_to_<peer>` tools, shared state with active-agent pointer, checkpointer-backed memory across turns.
- **LangGraph Swarm (TypeScript)** — [`npmjs.com/package/@langchain/langgraph-swarm`](https://www.npmjs.com/package/@langchain/langgraph-swarm) — JavaScript counterpart with the same primitives.
- **OpenAI Swarm** — [`github.com/openai/swarm`](https://github.com/openai/swarm) — the original educational reference (21k+ stars); now explicitly superseded by the OpenAI Agents SDK. Still the cleanest minimal example of "function returns next agent" as the handoff primitive. Read for the pattern; do not deploy.
- **OpenAI Agents SDK** — [`github.com/openai/openai-agents-python`](https://github.com/openai/openai-agents-python) — the production-grade successor to OpenAI Swarm. Keeps handoffs as a first-class primitive (`handoff()` helper with input filtering and callbacks) while adding tracing, guardrails, sessions, and hosted tools. Supports both peer-handoff and supervisor topologies; O10 is realised by configuring agents with mutual handoff targets and no manager.
- **CAMEL** — [`github.com/camel-ai/camel`](https://github.com/camel-ai/camel) — the role-playing multi-agent framework; peer agents converse in assigned roles (e.g. "user" and "assistant", or domain-specific dyads). The peer-communication primitive matches O10 even though CAMEL's research framing is "communicative agents for mind exploration" rather than production handoff routing.

## Known Uses

- **Customer-support swarms** built on LangGraph Swarm or the OpenAI Agents SDK — triage agent + billing agent + tech agent + cancellation agent, with explicit peer handoffs. The most common documented O10 production shape.
- **LangGraph "Swarm" starter projects and reference architectures** — multi-agent chatbots where specialists hand to specialists without a central supervisor; widely used as a starting template.
- **Role-played dialogue research** (CAMEL and its successors) — peer agents in assigned roles produce conversations used for behavioural study and synthetic data generation.
- **Open-source community projects** layering O10 on top of frameworks above — coding assistants where Researcher hands to Implementer hands to Reviewer, with cycles back to Researcher when verification fails.
- **Honest caveat on prevalence.** Several teams that *describe* their architecture as "swarm" run a single triage agent that does most of the routing — structurally closer to O7 with a thin supervisor. The taxonomy's standing observation holds: peer-to-peer at scale remains rare in production. Most successful swarms are small (2–4 agents), narrow-domain, and conversational.

## Related Patterns

- **Distinct from** O7 Supervisor Hierarchy — O7 has a root that owns the goal and never executes; O10 has no root, and the executor *is* the router. Most production "swarm" claims are actually O7.
- **Distinct from** O6 Orchestrator-Workers — O6 has a central orchestrator with workers that do not route. O10 has peers that route. If a swarm collapses to "one agent does most of the routing", it has become O6.
- **Distinct from** O11 Blackboard System — O11 coordinates over a shared accumulating state with a control unit that activates agents; O10 coordinates over direct handoffs with no controller. They can be combined (peers reading a shared blackboard while handing off to each other), but answer different questions.
- **Distinct from** O3 Routing — O3 is a one-shot classify-and-dispatch at the entry point; O10 is continuous, in-conversation, recursive routing across many turns.
- **Uses** O15 Agent Handoff — the structured-context-transfer mechanism is exactly the primitive O10 builds on. O15 is the per-handoff schema; O10 is the system-level pattern of using it as the *only* coordination move.
- **Composes with** O17 Agent Isolation — within a peer agent, tool-execution sub-tasks can run in fresh contexts; the peer itself reads the shared conversation history.
- **Required by** V9 Bounded Execution — cycle detection at the handoff layer is mandatory, not optional.
- **Required by** V14 Trajectory Logging — without an end-to-end linked trace of holder + action + target + reason, the system is undebuggable.
- **Pairs with** S6 Output Template — the handoff brief schema is a Signal-layer artefact.
- **Pairs with** R4 ReAct — each peer agent typically runs ReAct internally during its turns.
- **Grounded in** Minsky's *Society of Mind* — the cognitive-science precursor: mind as many specialised agents coordinating without a central controller. The framing is the inspiration; production O10 systems are far simpler than the Society-of-Mind agencies Minsky described.

## Sources

- Minsky, M. (1986) — *The Society of Mind.* Simon & Schuster. The foundational framing of mind as a coordinated society of specialised agents without a central controller; the cognitive-science precursor of O10.
- OpenAI (2024) — *Swarm: Educational framework exploring ergonomic, lightweight multi-agent orchestration.* The original peer-handoff library; now superseded by the OpenAI Agents SDK but the clearest minimal articulation of the pattern.
- OpenAI (2025) — *OpenAI Agents SDK.* The production successor; documents handoffs as a first-class primitive supporting both swarm and supervisor topologies.
- LangChain (2025) — *LangGraph Swarm* (Python and TypeScript). The active canonical open-source implementation of peer-handoff multi-agent systems.
- Li et al. (2023) — *CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society.* arXiv 2303.17760. Peer role-playing agents as a research vehicle for multi-agent communication.
- arXiv 2601.03328 — empirical multi-agent system study; documents peer-to-peer as one of the network configurations alongside hierarchical and centralised. Reports hierarchical as the dominant production choice.
- arXiv 2601.03624 — 46-pattern multi-agent catalog; lists peer-to-peer / decentralised coordination as a distinct architectural family.
- Sibyl (2024) and subsequent "jury of agents" work — applications of Society-of-Mind framing to LLM ensembles, sitting between O10 (peer routing) and O9 (multi-agent critique).
