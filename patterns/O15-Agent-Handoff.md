# O15 — Agent Handoff

> Transfer control of an in-progress interaction from one agent to another within the same system, passing a structured state package — intent, entities, actions taken, goal, trace ID — so the receiving agent continues coherently without restarting or re-asking.

**Also Known As:** Context Transfer, Agent-to-Agent Transfer (intra-system), Conversation Handoff, Transfer Tool, Swarm Handoff.

**Classification:** Category IV — Orchestration · Band IV-C Specialised Coordination · the *intra-system* control-transfer pattern — moves a live conversation between agents in the same deployment, distinct from I6 A2A Delegation's cross-vendor protocol.

---

## Intent

Move a live interaction from one agent to another inside the same system without losing context, so the user does not repeat themselves and the receiving agent starts from the conversation's true state — not from zero, and not from a noisy transcript.

## Motivation

Multi-agent systems frequently need to switch which agent is "driving" a conversation mid-flight. A triage agent recognises a billing question and wants the billing agent to take over. A general assistant hits a domain it does not handle and needs the specialist. A voice agent must pass to a text agent. In every case the receiving agent needs *enough* context to continue, but not *all* of it.

Two naive options both fail. **Pass the entire transcript** and the receiver drowns in turns it does not care about — its specialist prompt is diluted, tokens are wasted, and any tool state, partial extraction, or commitment made by the previous agent is buried in narrative. **Pass a free-text summary** and the receiver loses the structured evidence that made the previous decisions valid: which entities were extracted, which tools were already invoked with what outcomes, which goal the user actually stated. The user then notices — the receiving agent asks for the order number again, or repeats a refund check that has already succeeded.

The pattern is a *structured* handoff package. Not the transcript, not a summary — a typed object the sending agent constructs (or the framework constructs from session state) and the receiving agent consumes as its initial context: detected intent, extracted entities, actions already taken (with outcomes), the user's stated goal, any outstanding tool state, and a trace ID linking back to the full history if needed. The receiver should treat the handoff package as a stable prefix: it is loaded once and defines the receiver's starting state. If the package schema is stable across handoffs, provider-level prefix caching can amortise the prefill cost on repeated handoff calls of the same type — e.g. all billing-agent handoffs share the same structure prefix, which the provider caches and serves at ~10% of normal input token cost (mechanism 5). (Mechanism 5.) OpenAI's Swarm made this primitive canonical: a handoff is a tool call that returns the next agent, and the framework carries the conversation forward. The Agents SDK that replaced Swarm kept the primitive and added explicit `input_filter` and `on_handoff` hooks so the package can be shaped, audited, and reduced before it reaches the receiver.

The boundary against I6 A2A Delegation matters: I6 is the cross-vendor protocol (HTTP, agent cards, status streams, network trust). O15 is the in-process move (function call returning an agent, shared memory, same trace). They share an interface intent — "another agent should take this" — but live at different layers; I6 is the wire format, O15 is the orchestration primitive. In a cross-system call, O15 wraps I6 as transport.

## Applicability

Use when:

- The system has multiple agents and a conversation may need to switch between them mid-interaction.
- Specialist routing is determined dynamically by conversation state, not by a fixed up-front classifier (which would be O3 Routing).
- The receiving agent needs structured evidence — extracted entities, action outcomes, tool state — not just a chat history.
- Voice-to-text, automated-to-human, or general-to-specialist escalation is part of the design.

Do not use when:

- Routing can be decided once at the entry point — use **O3 Routing**.
- The work is fixed-sequence with no live conversation to transfer — use **O2 Prompt Chaining**.
- A central orchestrator should remain in control rather than delegating the conversation itself — use **O6 Orchestrator-Workers**.
- The transfer crosses a vendor or trust boundary — use **I6 A2A Delegation** as the transport (often wrapped by O15 inside each system).
- Sub-tasks need a fresh isolated context, with the parent retaining control — use **O17 Agent Isolation**.

## Decision Criteria

O15 is right when the live conversation must move between specialised agents in the same system and the receiver needs structured continuity, not a transcript dump.

**1. Conversation continuity test.** Will the user keep talking to "the system" after the transfer, expecting it to remember? **Yes** $\to$ O15. **No, the receiving agent runs in the background and reports back** $\to$ O17 Agent Isolation or O6 Orchestrator-Workers.

**2. Routing dynamism test.** Can the routing decision be made *once* at the front, before any conversation? **Yes** $\to$ O3 Routing. **No, the need to switch emerges mid-conversation from extracted state** $\to$ O15. If you can decide at turn 1, do; O15 pays its cost when the decision must be made at turn 5.

**3. Trust boundary test.** Does the receiving agent live in the same codebase, share the same trace store, run under the same auth? **Yes** $\to$ O15. **No, it is across a vendor / network / org boundary** $\to$ **I6 A2A Delegation** for the transport. O15 is the orchestration primitive; I6 is the wire protocol.

**4. Package size discipline.** Measure the handoff payload. Target: **$\leq$ 10% of the sender's working context** and **all structured fields, no raw transcript spans** beyond a 1–2 turn excerpt. If the package is just "the transcript so far," the pattern has collapsed back to the naive option; tighten the schema or accept that O17 Agent Isolation (fresh context with explicit hand-prepared subset) fits better. The 10% target is mechanically grounded. If the sender has a 20k-token context and the receiving agent inherits all of it, the receiver pays O(n²) attention over 20k tokens even if only 2k tokens are relevant to its role — every token in that inherited context adds pairwise attention cost against all subsequent generated tokens (mechanism 2). The relevant tokens — if they arrived in the middle of the prior conversation — are also geometrically under-attended due to U-shaped recall (mechanism 4). A structured handoff package moves the critical state to the boundary positions of the receiver's context window, where attention is strongest. (Mechanisms 2, 4.)

**5. Audit and reversibility.** Can you, after the fact, identify *which* agent handled *which* turn and replay from the handoff point? Pair with **V14 Trajectory Logging** so every handoff is a logged event with sender, receiver, package, and trace ID — without this, multi-agent conversations become undebuggable. Pair with **V10 Checkpointing** if the receiver may fail and the sender should be able to resume.

**Quick test — O15 is the right pattern when:**

- the conversation must continue with the user after the switch, *and*
- the routing decision emerges from conversation state (not known up front), *and*
- both agents live in the same system / trust boundary, *and*
- a structured package (not the transcript) can carry the necessary continuity.

If routing is up-front, use O3. If the switch is to a sub-task that reports back rather than taking over the conversation, use O17 or O6. If the boundary is cross-vendor, use I6 as transport.

## Structure

```
  User turn ─▶ Agent A (current driver)
                  │
                  │ decides: "this needs Agent B"
                  ▼
         Handoff tool call → returns Agent B
                  │
                  ▼
         Handoff Package (built by code or hook):
           • detected intent            • actions taken (with outcomes)
           • extracted entities         • outstanding tool state
           • user's stated goal         • trace ID + last turn excerpt
                  │
                  ▼
         input_filter / on_handoff hook
           (shape, redact, log to V14)
                  │
                  ▼
              Agent B (new driver) ─▶ continues with user
                  │
                  └── may hand off again or back to A
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Sending Agent** | recognising the handoff condition and invoking the transfer | conversation state $\to$ handoff tool call | answer the question itself once it has decided to hand off — partial work creates the "two agents both replying" failure mode. |
| **Handoff Tool** | the act of switching driver | tool invocation $\to$ reference to the receiving agent | carry state itself; it is a control-flow signal, not a payload. |
| **Handoff Package** | the typed state passed across | session state $\to$ structured fields (intent, entities, actions, goal, trace ID) | be the raw transcript. A package that is just "the chat so far" defeats the pattern. |
| **Package Builder / `on_handoff` hook** | constructing and filtering the package | session state + handoff event $\to$ reduced package | leak secrets, untrusted user content, or context the receiver should not see — V6 applies. |
| **Receiving Agent** | continuing the conversation from the package | package + next user turn $\to$ response | re-ask the user for anything already in the package. Re-asking is the user-visible failure of the pattern. |
| **Trace Logger** *(V14)* | recording the handoff as an audit event | sender, receiver, package, timestamps $\to$ trajectory record | be optional — without it, multi-agent conversations are undebuggable. |

The handoff is a single logged event with a clean before/after. Two agents are never both driving.

## Collaborations

A user turn arrives at the sending Agent. Mid-reasoning the agent decides the receiving agent is better placed — perhaps it has extracted a refund intent and the refund agent owns that flow. It calls the Handoff Tool, which returns a reference to the receiving Agent. The framework (or the surrounding code) invokes the `on_handoff` hook, which reads the session state and builds the Handoff Package: detected intent, the entities pulled from the conversation, any actions already taken with their outcomes (e.g. "order looked up: #1234, status shipped"), the user's stated goal, outstanding tool state, and the trace ID. The Trace Logger records the event. The receiving Agent's setup is loaded; the package becomes part of its initial context alongside the next user turn. It replies. It may itself hand off again — to a third agent, to a human via V1, or back to the original agent — and the same flow repeats. A bound on handoff depth (V9 Bounded Execution) prevents ping-pong loops.

## Consequences

**Benefits**
- Conversation continuity — the user does not repeat themselves across agent switches.
- Specialised agents stay focused on their domain; routing is dynamic rather than fixed at entry.
- Structured packages are debuggable and replayable; every switch is an audit event.
- Composes cleanly with O3 (entry routing), O6 (orchestrator delegating live conversations), V1 (escalation to human), I6 (cross-system transport).

**Costs**
- Schema work: the package schema must be designed, kept stable as agents change, and tested.
- Extra LLM call to *decide* the handoff (unless the sending agent makes the decision inline).
- Each agent pays a small setup cost; very chatty handoff patterns add latency.

**Risks and failure modes**
- *Package under-specification.* The receiver makes wrong assumptions because the package missed a field. User notices: "didn't I just tell you that?"
- *Package over-specification.* The package is effectively the transcript; the receiver drowns; the pattern's value is lost. Tighten the schema.
- *Ping-pong handoffs.* A and B keep handing off to each other because neither is sure it owns the task. Bound with V9 and surface to V1.
- *Double-reply.* The sender produces an answer *and* hands off; the user sees two replies. Forbid by contract: a handoff terminates the sender's turn.
- *Untrusted-content carry.* User-controlled strings flow through the package into the receiver's prompt unchecked. Apply V6 Prompt Injection Shield to the package builder.
- *Stale tool state.* The sender's open tool call is forgotten across the boundary, leaving an orphan transaction.

## Implementation Notes

- Define the handoff package as a **typed schema** (Pydantic, TypeScript interface, Zod). Free-form dicts drift; types catch under- and over-specification at build time.
- Make the handoff a **tool the sending agent calls**, not an external classifier. The sender knows what it has gathered; let it package it. (This is the Swarm / Agents SDK design.)
- Use the framework's `on_handoff` / `input_filter` hooks (Agents SDK) or an equivalent middleware to **strip the prior agent's internal scratchpad** before the receiver sees it — the receiver should see *evidence*, not the previous agent's reasoning.
- Always log the handoff to **V14 Trajectory Logging** with sender ID, receiver ID, package hash, and trace ID. Without this, "which agent answered turn 7?" is unanswerable.
- Bound handoff depth with **V9 Bounded Execution** — cap how many handoffs a single user turn can trigger, and how many handoffs can occur within a session, to prevent ping-pong.
- For escalation to a human, the receiving "agent" is a queue + UI; the package is the inbox card. The pattern is the same — V1 Human-in-the-Loop names the recipient class.
- Cross-system handoffs wrap O15 around **I6 A2A Delegation** as transport: the local handoff fires, the receiver happens to live on another system, and I6 carries the package over the wire.
- Voice$\to$text and text$\to$voice handoffs are O15 with a media-change step in the hook; the package shape is the same.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** O15 chains a sending **agent session** with a receiving **agent session**, joined by a deterministic *package-builder* step. Routinely composes with **V14 Trajectory Logging** (every handoff is a logged event), **V9 Bounded Execution** (handoff-depth cap), **V6 Prompt Injection Shield** (untrusted user strings in the package), and **V1 Human-in-the-Loop** (when the "receiving agent" is a human queue). When the receiver lives in another system, O15 wraps **I6 A2A Delegation** as the transport.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Sending Agent runs its turn; may call a `handoff_to_<B>` tool | `LLM` | Sender session |
| 2 | Framework intercepts the tool call: it is a control-flow signal, not a normal tool | `code` | |
| 3 | Build the Handoff Package from session state (entities, actions, goal, tool state, trace ID) | `code` (optional `LLM` summariser for free-text fields) | S6 Output Template; V6 filter |
| 4 | Log the handoff event (sender, receiver, package digest, timestamps) | `code` | V14 |
| 5 | Switch the driver; load Receiving Agent's setup; inject the package as initial context | `code` | |
| 6 | Receiving Agent continues with the next user turn | `LLM` | Receiver session |
| 7 | Bound check: handoff depth in this turn $\leq$ N, else escalate | `code` | V9, V1 |

**Skeleton** — wiring only; `# LLM` marks each configured session:

```
on_user_turn(user_msg, session):
    while handoff_depth(session) <= MAX_DEPTH:        # code — V9 bound
        agent = session.current_driver
        out = agent.respond(user_msg, session.history) # LLM — Sender session
        if out.is_handoff:
            pkg = build_package(session, out.handoff)  # code — typed schema
            pkg = sanitize(pkg)                        # code — V6 filter
            log_handoff(agent, out.handoff.target, pkg)# code — V14
            session.current_driver = out.handoff.target
            session.prepend_context(pkg)               # code — into receiver
            continue                                   # loop to next driver
        return out.reply                               # done
    escalate_to_human(session)                         # V1
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Sending Agent** | the specialist generalist for the *sender's* domain | role (S3); the sender's tools, including `handoff_to_<B>` for each valid target; rule that a handoff call *terminates the turn* (no extra reply); criteria for when to hand off | the conversation history within the sender's scope + the new user turn |
| **Receiving Agent** | the specialist generalist for the *receiver's* domain | role (S3); the receiver's tools (no `handoff_to_<A>` unless reverse-handoff is intended); output contract (S6); rule that the **Handoff Package is to be trusted as state, not re-asked** | the Handoff Package + the next user turn |
| **Package Summariser** *(optional)* | small fast generalist | role: "you compress conversation state into a typed handoff package"; the package schema; rule: structured fields only, no narrative | the relevant session state |

**Specialist-model note.** None — capable generalists suffice on both sides. The leverage is in the **package schema** (a Signal-layer S6 artifact) and the framework hook (`on_handoff` / `input_filter`), not in any specialist model. The handoff tool itself is not an LLM step; it is a function call the sender emits, and the framework's interceptor turns it into the control transfer. A specialist *classifier* could replace the sender's judgment about *when* to hand off, but in practice the sender's own reasoning is sufficient (the Swarm / Agents SDK design relies on this) and a separate classifier reintroduces the O3 Routing pattern.

## Open-Source Implementations

- **OpenAI Agents SDK** — [`github.com/openai/openai-agents-python`](https://github.com/openai/openai-agents-python) — the production successor to Swarm; first-class `handoff()` primitive with `on_handoff` callbacks, `input_filter`, typed input schemas, and a recommended `RECOMMENDED_PROMPT_PREFIX` for handoff-aware agents. Canonical reference for the pattern. JS counterpart at [`github.com/openai/openai-agents-js`](https://github.com/openai/openai-agents-js).
- **OpenAI Swarm** — [`github.com/openai/swarm`](https://github.com/openai/swarm) — the original educational implementation that named the handoff primitive (handoff = tool call that returns the next agent). Deprecated in favour of the Agents SDK but remains the clearest explainer.
- **LangGraph Swarm** — [`github.com/langchain-ai/langgraph-swarm-py`](https://github.com/langchain-ai/langgraph-swarm-py) — `create_handoff_tool` and `create_custom_handoff_tool` for LangGraph; handoffs implemented as tools returning `Command` objects that update graph state.
- **LangGraph Supervisor** — [`github.com/langchain-ai/langgraph-supervisor-py`](https://github.com/langchain-ai/langgraph-supervisor-py) — supervisor-coordinated handoffs across a graph of specialised agents.
- **Microsoft Agent Framework** — [`github.com/microsoft/agent-framework`](https://github.com/microsoft/agent-framework) — handoff orchestration is one of the four core workflow patterns (sequential, concurrent, handoff, group); cross-language Python + .NET. Documentation: [Microsoft Learn — Handoff orchestration](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/handoff).
- **LiveKit Agents** — [`github.com/livekit/agents`](https://github.com/livekit/agents) — voice-agent handoffs with realtime-session reuse; multi-agent example at [`examples/voice_agents/multi_agent.py`](https://github.com/livekit/agents/blob/main/examples/voice_agents/multi_agent.py). Companion blog: [The Handoff Pattern for Voice Agents](https://livekit.com/blog/handoff-pattern-voice-agents).

## Known Uses

- **Customer-support triage systems** built on the Agents SDK or LangGraph Swarm — front-line triage agent hands off to billing, refunds, technical, or human, carrying the extracted case state.
- **Voice agents replacing IVR** — LiveKit's handoff pattern explicitly markets itself as the replacement for legacy IVR menus; user speaks naturally, voice agent hands off to specialist voice or text agent.
- **Microsoft Copilot multi-agent workflows** — handoff orchestration in production Copilot apps for routing across specialist agents within the same Copilot deployment.
- **Internal coding-assistant ecosystems** that route between a planner, an implementer, and a reviewer agent within the same session, with state (selected files, draft, test results) passed in the handoff.

## Related Patterns

- **Distinct from** **I6 A2A Delegation** — O15 is *intra-system* control transfer (function call, shared memory, same trace, same trust boundary); I6 is the *inter-system* protocol (HTTP, agent cards, status streams, network trust). When a handoff crosses systems, O15 wraps I6 as transport.
- **Distinct from** **O3 Routing** — O3 decides at the *entry* of an interaction which handler runs; O15 switches drivers *mid-conversation*. O3 is up-front classification; O15 is dynamic transfer.
- **Distinct from** **O17 Agent Isolation** — O17 spawns a sub-agent with a fresh context that returns a *result* to the parent; the user never talks to it. O15 transfers the *driver* of the user-facing conversation. Different shape, different intent.
- **Composes with** **O6 Orchestrator-Workers** — an orchestrator may itself hand off the conversation rather than holding it; the orchestrator's "delegate" can be a handoff or a sub-task call depending on whether the user keeps talking to the worker.
- **Pairs with** **V14 Trajectory Logging** — every handoff is an audit event; without V14, multi-agent conversations are undebuggable.
- **Pairs with** **V9 Bounded Execution** — cap handoff depth to prevent ping-pong loops between agents that each think the other should handle the case.
- **Pairs with** **V1 Human-in-the-Loop** — the "receiving agent" is sometimes a human queue; the handoff package is the inbox card.
- **Uses** **S6 Output Template** — the Handoff Package schema is a Signal-layer artifact that constrains the package builder.
- **Composes with** **V6 Prompt Injection Shield** — user-controlled strings flow through the package into the receiver's prompt and must be filtered at the hook.

## Sources

- OpenAI (2024) — Swarm: "Orchestrating Agents: Routines and Handoffs" cookbook ([developers.openai.com/cookbook/examples/orchestrating_agents](https://developers.openai.com/cookbook/examples/orchestrating_agents)). The canonical articulation of the handoff primitive.
- OpenAI (2025) — Agents SDK documentation: Handoffs ([openai.github.io/openai-agents-python/handoffs](https://openai.github.io/openai-agents-python/handoffs/)) — production-ready evolution with `on_handoff`, `input_filter`, `RECOMMENDED_PROMPT_PREFIX`.
- LangChain (2025) — Multi-agent handoffs documentation ([docs.langchain.com/oss/python/langchain/multi-agent/handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)) — Command-object pattern, transfer tools.
- Microsoft (2025) — Agent Framework Workflows: Handoff orchestration ([learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/handoff](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/handoff)).
- LiveKit (2025) — "The Handoff Pattern for Voice Agents That Replaces IVR Menus" — production-pattern write-up for voice-domain handoffs.
- Augment Code — Agent Handoff Patterns guide; XTrace.ai — AI Agent Context Handoff write-up (referenced in the original O15 draft).
