# V3 — Rule of Two / Lethal Trifecta

> Audit every agent for the simultaneous presence of three capabilities — private-data access, untrusted-content exposure, and external communication — and treat any agent that holds all three as unsafe until at least one is broken by a mitigation.

**Also Known As:** Lethal Trifecta Check, Trifecta Audit, Willison's Rule, Dual-Access Prohibition.

**Classification:** Category V — Reliability · Band V-A Safety & Governance · a *detection/audit* pattern — it does not itself mitigate the risk; it identifies where mitigation (V4 Dual LLM, V6 Prompt Injection Shield, or V8 Tool Sandboxing) is mandatory.

---

## Intent

Make the Lethal Trifecta — the unique combination of capabilities that turns ordinary prompt injection into uncontrollable data exfiltration — visible at design time and continuously thereafter, so an agent that holds all three is *never* shipped without a named mitigation in place.

## Motivation

Simon Willison's 2023–2025 observation is the foundation: prompt injection becomes catastrophic only when an agent simultaneously has **(1) access to private data** (your email, your files, your CRM, your codebase), **(2) exposure to untrusted content** (web pages, inbound emails, tool outputs from third-party APIs, user uploads), and **(3) the ability to communicate externally** (send HTTP requests, send email, post to chat, open a PR, render clickable links). Each leg alone is benign. Any two together is manageable. All three simultaneously means an attacker who can put text anywhere the agent reads can extract anything the agent can see, through any channel the agent can write.

The point is that *no code vulnerability is required*. The model is doing what it was built to do — follow instructions in its input. There is no syntactic boundary between "data" and "instructions" in natural language, so any untrusted byte that reaches the same context as private data and an outbound channel is, in principle, a hijacking primitive. CaMeL (Debenedetti et al., 2025) demonstrates the point formally: defending the model from inside the model does not work; the defense has to be architectural, outside the LLM, and the first architectural move is to *recognise the combination*.

That is what V3 is. It is not a mitigation. V4 (Dual LLM), V6 (Prompt Injection Shield), and V8 (Tool Sandboxing) are mitigations — each breaks one leg of the trifecta. V3 is the audit that says *this agent holds all three legs, therefore at least one mitigation is mandatory before deployment*. Without V3, mitigations are applied ad hoc, by whoever happens to remember; with V3, the combination is a design-time gate. This is why it is a distinct pattern from V4/V6/V8: those answer *how to break the trifecta*; V3 answers *whether you have one in the first place*. **An agent passing V3 with all three conditions present has not finished V3 — it has reached the point where V4, V6, or V8 must be brought in.**

## Applicability

Use the Trifecta Audit when:

- you are designing or reviewing any agent that touches user data, third-party content, or outbound channels;
- you are about to add a new tool, MCP server, or data source to an existing agent;
- you are connecting two previously isolated agents (a handoff can compose the trifecta out of two safe halves);
- you are deploying to a regulated or high-stakes domain, where a single successful injection is an incident.

Do not use it when:

- the agent has no private data access at all and never will (e.g. a fully public-facing classifier) — the trifecta is structurally unreachable, and the audit is theatre. Use **V14 Trajectory Logging** and **V5 Guardrail Layering** instead for general safety;
- the agent is a single fixed pipeline with no LLM tool-calling and no dynamic instruction-following — V3 is for *agents*, not for fixed prompts. Use **V5 Guardrail Layering** for input/output safety on a fixed pipeline.

## Decision Criteria

V3 is mandatory the moment an agent could plausibly hold two of the three conditions and might gain the third — including dynamically, through MCP servers or sub-agent calls.

**1. Inventory each leg explicitly.** For each agent instance, list:
- *Private data sources* — any data the user (or another principal) would not consent to leak. Files, email, calendar, CRM rows, code, secrets, prior conversation history.
- *Untrusted content inputs* — any byte stream the agent reads that an attacker could influence. Web pages, inbound email bodies, document uploads, third-party API responses, tool outputs from any tool that itself fetches external data, retrieved chunks from a corpus that ingests external sources.
- *External communication channels* — any outbound action that could move bytes off the local system in a way an attacker could observe. Email send, HTTP requests, web fetches with attacker-controlled URLs, chat messages, PR creation, clickable links rendered in the UI (image fetches especially).

If the inventory is unclear, the audit has not been done.

**2. Score the matrix.** Map the agent against a 2×2×2 risk matrix:
- 0 legs present → no constraint.
- 1 leg present → standard operation; **V5 Guardrail Layering** and **V14 Trajectory Logging** suffice.
- 2 legs present → elevated monitoring; **V14 Trajectory Logging** is mandatory, and the third leg must be designed against (no MCP servers that would add it; no tool discovery that would acquire it). Add **V13 Tool Budget** to cap the dynamic acquisition surface.
- 3 legs present → **TRIFECTA**. The agent must not ship without at least one of **V4 Dual LLM**, **V6 Prompt Injection Shield**, or **V8 Tool Sandboxing**, *and* runtime monitoring (V14 + V17) to detect the combination if it is acquired dynamically.

**3. Test dynamic acquisition.** Inspect each integration that can expand capability at runtime — MCP servers (I3), tool discovery, sub-agent handoff (A14 Trust Handoff), retrieved tools (RAG-MCP), plugin systems. For each, ask: *can loading this introduce a leg the agent did not have at design time?* If yes, that integration triggers a re-audit. Score on the *post-load* capability set, not the start-up one.

**4. Pick the mitigation by which leg is cheapest to break.** Once the trifecta is confirmed:
- *Cannot remove private data* (it is the product) → break leg 2 with **V4 Dual LLM** (route untrusted content to a Quarantined LLM) or **V6 Prompt Injection Shield** (treat untrusted content as tainted; gate downstream actions).
- *Cannot remove untrusted content* (it is the input) → break leg 3 with **V8 Tool Sandboxing** (no outbound network from the agent that touches untrusted content) or with policy enforcement (**V7 AgentSpec**: PROHIBIT external comms while tainted).
- *Cannot remove external comms* (it is the deliverable, e.g. an email assistant) → break leg 2 hard with **V4 Dual LLM**; the Privileged side composes the message, the Quarantined side never sees outbound channels.

**5. Re-audit on every capability change.** A clean V3 audit ages. Every new tool, new MCP server, new sub-agent, new data source, new model swap, every prompt change that broadens scope — re-run V3. The most common V3 failure is "the audit was done once" (see Failure modes).

**Quick test — V3 is the right pattern when:**

- the agent has at least one of {private data, untrusted content, external comms} and might gain a second, *and*
- the consequences of silent data exfiltration are non-trivial (any user-data, any commercial system, any regulated domain), *and*
- there is more than one integration surface (tools, MCP, sub-agents) where capability can change without a code change, *and*
- a human can be held accountable for the design-time decision (so the audit has an owner).

If the agent has *zero* legs and structurally never will, V3 is unneeded — apply **V5 Guardrail Layering** and **V14 Trajectory Logging** for general safety. If the trifecta is confirmed, V3 is *necessary but not sufficient* — proceed to **V4**, **V6**, or **V8** as the actual mitigation; V3 alone does not protect anything, it only identifies the requirement.

## Structure

```
                       ┌──────────────────────────────────────────┐
                       │   Agent under design / under review      │
                       └──────────────────┬───────────────────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │  Trifecta Auditor     │
                              │  (design time +       │
                              │   on every change)    │
                              └───────────┬───────────┘
                                          │ inventories
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
   ┌─────────────────┐         ┌──────────────────────┐       ┌──────────────────┐
   │ Private data    │         │ Untrusted content    │       │ External comms   │
   │ access?         │         │ exposure?            │       │ capability?      │
   └────────┬────────┘         └──────────┬───────────┘       └────────┬─────────┘
            │                             │                            │
            └─────────────────────────────┼────────────────────────────┘
                                          ▼
                              ┌───────────────────────┐
                              │   Score the matrix    │
                              │   (0 / 1 / 2 / 3 legs)│
                              └───────────┬───────────┘
                                          │
                ┌─────────────────────────┼──────────────────────────┐
                ▼                         ▼                          ▼
        0–1 legs:                 2 legs:                     3 legs (TRIFECTA):
        standard ops              V14 mandatory               BLOCK deploy until
        + V5 guardrails           + V13 tool cap              V4 / V6 / V8 applied
                                  + design against            + Runtime Monitor
                                    the third leg               (V14 + V17)

                              ┌───────────────────────┐
                              │  Runtime Monitor      │
                              │  watches for          │
                              │  dynamic acquisition  │
                              │  (new MCP, new tool)  │
                              └───────────────────────┘
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Capability Inventory** | the authoritative list of data sources, untrusted inputs, and outbound channels for the agent | agent spec + integration manifest → three explicit lists | be implicit. An inventory inferred from code-reading rather than declared in writing is the single most common audit failure — the leg that gets missed is always the one no one wrote down. |
| **Trifecta Auditor** | the leg-count and the verdict | three lists → score (0/1/2/3) + required mitigation | sign off on a 3-leg agent without naming a specific V4/V6/V8 application. "We'll add safety later" is the failure mode. |
| **Risk Matrix** | the rule mapping leg-count to required pattern | leg count → required reliability patterns | drift. The matrix is policy; if it loosens informally ("two legs but the third is unlikely") it stops protecting anything. |
| **Mitigation Linker** | the named, traceable reference from the audit verdict to the mitigation pattern actually deployed | verdict + mitigation spec → audit record | declare mitigation generically ("we use V4 somewhere") — the link must name *which* boundary V4 sits on, *which* LLM is Privileged and which is Quarantined, *what* content type is treated as untrusted. |
| **Runtime Monitor** | detection of *dynamic* acquisition of a third leg after deployment | runtime trace (V14) → alert when leg-count transitions from 2 to 3 | rely on the design-time audit alone. MCP server loading, tool discovery, and sub-agent handoff can compose the trifecta without any code change. |

The five responsibilities are deliberately separated so the audit produces a *paper trail*, not a vibe. The Inventory and the Auditor are independent so the auditor cannot quietly redefine what counts as private data; the Risk Matrix is fixed policy, not advisory; the Mitigation Linker forces the audit to name a real mechanism; the Runtime Monitor closes the loop on the fact that capability is now a runtime variable, not just a build-time one.

## Collaborations

The flow runs at two timescales. At **design time**: an agent specification (intended data sources, intended tools, intended outbound capability) is handed to the Capability Inventory, which produces three explicit lists. The Trifecta Auditor counts the legs and consults the Risk Matrix. If the count is 3, the audit fails closed: the Mitigation Linker insists on a named V4 / V6 / V8 instance — *not* "we use V4" but "the assistant-side LLM is Privileged, sees raw email metadata only; the parser-side LLM is Quarantined, processes email bodies and emits validated structured output via a JSON schema." The audit record is committed alongside the agent's spec.

At **runtime**: V14 Trajectory Logging emits a stream of tool calls, data accesses, and outbound actions. The Runtime Monitor watches for transitions — a tool call to a newly-loaded MCP server that grants external HTTP, a sub-agent handoff that brings in untrusted content the parent had been shielded from, a retrieval pattern that newly indexes attacker-influenced sources. On transition to a 3-leg state, the Monitor alerts (V17 Online Eval) and, depending on policy (V7 AgentSpec), can block the offending action or surface to a human (V1). Schema tokens for newly-loaded MCP tools enter the agent context window directly; a large tool manifest can displace earlier trifecta-prevention instructions to mid-context positions where attention recall is geometrically weakest (mechanism 4; mechanism 2). The V13 Tool Budget cap on schema tokens is the correct co-mitigation.

The pattern composes upward: it is the audit that **V4**, **V6**, **V7**, and **V8** all assume someone has done. They each break a different leg and so each presupposes that the leg-count is known.

## Consequences

**Benefits**
- Surfaces the single most catastrophic class of agent vulnerability at design time, in a form that is checkable on paper, not only in production.
- Forces the team to *name* their mitigation rather than gesture at it: the audit record contains "V4 applied at boundary X" or it does not pass.
- Makes capability changes visible: any new MCP server, tool, or handoff that would change the leg-count triggers a re-audit by policy, not by hope.
- Cheap. The audit is a checklist plus a runtime monitor; it does not add per-call cost like V4 / V8 do.

**Costs**
- Audit discipline is a permanent overhead — it is not a one-shot task. The cost is in the meeting time and the runbook, not in the runtime.
- Requires an owner: someone accountable for re-running the audit on every capability change. Without an owner, the audit ages out within weeks.
- Tension with rapid integration: every new MCP server is a re-audit, which slows down "just add this tool" requests by design.

**Risks and failure modes**
- *Audit performed once and never updated.* The dominant failure. The agent shipped clean; six months later, three MCP servers and a sub-agent handoff have been added, and no one re-counted the legs.
- *Implicit inventory.* The "private data" list omits the chat history (it does feel like private data, but it was never written down as such), or the "untrusted content" list omits tool outputs (those felt like first-party — but the tool itself reads the public web).
- *Mitigation gestured at, not specified.* The audit says "V4 applies" without naming which content goes to which LLM and what the validation layer enforces. At review time, it turns out the Quarantined LLM was wired to the same database the Privileged one uses.
- *Dynamic acquisition unnoticed.* A capability is acquired at runtime through MCP discovery or RAG-MCP-style tool retrieval, and the Runtime Monitor either does not exist or does not know how to interpret the new tool's capability.
- *Sub-agent compositional trifecta.* Agent A is safe (legs 1 + 2, no comms). Agent B is safe (legs 2 + 3, no private data). A handoff that lets B act on A's data composes a 3-leg system out of two 2-leg agents. The audit must be per-system, not per-agent.
- *Over-broad "untrusted".* Every byte is technically attacker-influenceable; if everything is untrusted, nothing is. The leg has to be defined with a realistic threat model, not the empty set of "all input could be malicious."

## Implementation Notes

- Write the inventory in the agent's spec / README, not in tickets — it has to be the durable artifact. A capability matrix table is more legible than prose.
- Tie the re-audit to the change-management process: any PR that adds an integration (tool, MCP server, data source, outbound channel) cannot merge without an updated audit row.
- Treat the Quarantined-side definition seriously. "Untrusted" should be a content-origin label that propagates with the data — taint tracking. If you cannot say which bytes are tainted, you cannot run the audit.
- Where MCP is used (I3), the audit must enumerate which *specific* server is loaded; never audit against "MCP" in the abstract. Tools acquired through MCP discovery (RAG-MCP, dynamic loading) need a per-load re-check.
- A two-leg agent is the sweet spot for a lot of products. Resist the pressure to add the third leg "just for convenience"; instead, route the third-leg-needing action through a separate agent with a controlled handoff.
- Combine with **V7 AgentSpec** for the strongest form: the leg-count and required mitigation are encoded as policy rules the runtime engine enforces, not honour-system documentation.
- Sub-agent handoffs (O15) need the audit per-pair, not per-agent. The "trust handoff" anti-pattern (A14) is exactly an unaudited cross-agent composition.
- Pair with **V14 Trajectory Logging** from day one — without traces, the Runtime Monitor has no signal to watch. Without **V17 Online Eval** consuming those traces, alerts do not fire.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V3 is mostly *governance* — a checklist plus a policy-engine check — with an optional LLM step for triage / scoring at audit time. It chains with **V4 / V6 / V8** (the mitigations it routes to), with **V7 AgentSpec** (where the matrix can be encoded as policy), with **V14 Trajectory Logging** + **V17 Online Eval** (the runtime monitor's data source and alerting), and with **V1 Human-in-the-Loop** (the escalation when the audit fails).

**The chain — design-time audit:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Pull the agent's spec, tool list, MCP manifest, and data-source list | `code` | |
| 2 | Generate / refresh the three-leg Capability Inventory (private data, untrusted inputs, outbound channels) | `LLM` *(or human-led table)* | Auditor session |
| 3 | Score the leg-count against the Risk Matrix | `code` | Risk Matrix policy |
| 4 | Branch: 0–1 legs → standard ops; 2 legs → enforce V14 + V13; 3 legs → block until mitigation linked | `code` | |
| 5 | (if 3 legs) Verify a specific V4 / V6 / V8 application is named, with boundary and content type | `code` | V4 / V6 / V8 |
| 6 | Emit the audit record into the agent spec / policy store (V7 if used) | `code` | V7 AgentSpec |

**The chain — runtime monitoring:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| R1 | Tap V14 trace stream (tool calls, data reads, outbound actions) | `code` | V14 Trajectory Logging |
| R2 | Map each event to a leg (data-read → leg 1; untrusted-source read → leg 2; outbound action → leg 3) | `code` | |
| R3 | Detect transition from 2-leg to 3-leg state for the current session / agent | `code` | |
| R4 | On transition: alert (V17) + apply policy (V7 — block / require approval) + surface to V1 if configured | `code` | V7, V17, V1 |

**Skeleton:**

```
audit(agent_spec):                                       # design time
    inv = build_inventory(agent_spec)                    # LLM (or rule)  — Auditor session, see below
    score = legcount(inv)                                # code
    if score <= 1: return PASS_STANDARD                  # standard ops
    if score == 2: require([V14, V13]); return PASS_ELEVATED
    if score == 3:
        mit = find_named_mitigation(agent_spec)          # code
        if not mit: return BLOCK                         # not deployable
        if not links_specifically(mit, inv): return BLOCK
        write_audit_record(agent_spec, inv, mit)         # to V7 policy store
        return PASS_TRIFECTA_WITH_MITIGATION

monitor(trace_stream):                                   # runtime
    legs = {1: False, 2: False, 3: False}
    for event in trace_stream:                           # from V14
        legs[classify(event)] = True                     # code
        if sum(legs.values()) == 3 and not audit_authorised_trifecta():
            alert(V17)                                   # code
            enforce(V7_policy)                           # code  — block / require approval
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Auditor** *(optional — the inventory step can be human-led)* | capable generalist (Sonnet-class); audit reasoning is high-stakes, not high-volume | role: *"you are a security auditor classifying agent capabilities against the Lethal Trifecta. List every data source the agent can read, every byte stream it consumes that could be attacker-controlled, and every outbound channel it can write. Be exhaustive; err on the side of including borderline cases as untrusted."*; the three-leg definitions; the agent-spec template the auditor is filling | the agent specification + integration manifest under audit |

**Specialist-model note.** No fine-tuned specialist is required. The audit is mostly deterministic policy: a checklist, a matrix, and a monitor. The optional LLM step (Auditor) benefits from a strong reasoning model because the failure mode is *missing a leg*, not generating one — recall, not precision, is what matters. Place the capability inventory under audit as early in the context as possible; mid-context placement of the audit target degrades the Auditor's ability to surface missed legs (mechanism 4). If the inventory is human-authored (recommended for high-stakes deployments), no LLM is required at all. The runtime monitor is pure code over the V14 trace stream — no LLM in the hot path.

## Open-Source Implementations

V3 is an *architecture / governance pattern*, not a library — there is no canonical project that ships "the Trifecta Auditor". The relevant references are:

- **CaMeL — `google-research/camel-prompt-injection`** — [`github.com/google-research/camel-prompt-injection`](https://github.com/google-research/camel-prompt-injection) — Google / DeepMind / ETH Zürich research artifact for the paper "Defeating Prompt Injections by Design" (arXiv 2503.18813). Implements capability-based information-flow control that operationalises the V3 → V4 path: data origin is tracked, untrusted data is structurally prevented from influencing control flow. Closest thing to a runtime enforcement of the leg-count.
- **Microsoft Dromedary** — [`github.com/microsoft/dromedary`](https://github.com/microsoft/dromedary) — an AI-agent runtime described as "prompt-injection resistant by design", in the lineage of CaMeL and the Dual LLM pattern.
- **Reversec Labs — design-patterns-for-securing-llm-agents code samples** — [`github.com/ReversecLabs/design-patterns-for-securing-llm-agents-code-samples`](https://github.com/ReversecLabs/design-patterns-for-securing-llm-agents-code-samples) — runnable code samples accompanying the Beurer-Kellner et al. (2025) survey paper, including Action-Selector, Plan-Then-Execute, LLM Map-Reduce, Dual LLM, Code-Then-Execute, and Context-Minimisation patterns.
- **Promptfoo Lethal Trifecta tests** — [`promptfoo.dev/blog/lethal-trifecta-testing/`](https://www.promptfoo.dev/blog/lethal-trifecta-testing/) — eval harness for verifying that an agent does not silently hold all three legs under realistic adversarial inputs. Useful as the V18 (Agent Simulation) component that tests a V3 audit was honest.
- **Willison's reference posts** — [`simonwillison.net/2023/Apr/25/dual-llm-pattern/`](https://simonwillison.net/2023/Apr/25/dual-llm-pattern/) (original Dual LLM pattern), [`simonw.substack.com/p/the-lethal-trifecta-for-ai-agents`](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents) (the named trifecta), [`simonwillison.net/2025/Apr/11/camel/`](https://simonwillison.net/2025/Apr/11/camel/) (CaMeL commentary), [`simonwillison.net/2025/Aug/9/bay-area-ai/`](https://simonwillison.net/2025/Aug/9/bay-area-ai/) (Bay Area AI Security Meetup talk). These are the canonical reference for the pattern and its vocabulary.

## Known Uses

- **Anthropic's published agent design guidance** treats the trifecta as a baseline check before granting agents outbound capability alongside private-data access; the Dual LLM construction is recommended for assistants that touch email or chat plus user data.
- **Google / DeepMind CaMeL** is the production-research embodiment: capability-based information-flow control deployed to defend agent systems where the trifecta is unavoidable.
- **OWASP LLM Top 10 2025** — LLM01 (Prompt Injection) and LLM06 (Excessive Agency) reference the trifecta condition as the structural precondition for catastrophic injection; the OWASP guidance is, in effect, V3 as a checklist.
- **NCC Group** and other agent-security consultancies use the trifecta-inventory step as the opening move in agent threat models — see "Exploring Prompt Injection Attacks" and "Non-Deterministic Nature of Prompt Injection" on nccgroup.com.
- **Hidden Layer, Oso, Airia**, and other agent-security vendors publish trifecta-based assessment frameworks for enterprise agent deployments.
- **MCP server review processes** at multiple labs and vendors treat any new server addition as a re-audit trigger — concretely, "does this server give the agent a third leg?"

## Related Patterns

- **Required by** V4 Dual LLM, V6 Prompt Injection Shield, V8 Tool Sandboxing — each mitigation only knows where to apply itself because V3 has identified the trifecta. Deploying V4/V6/V8 without a V3 audit is guessing at where the boundary should be.
- **Composes with** V7 AgentSpec — the leg-count and mandatory mitigation can be encoded as deontic policy (PROHIBIT outbound while tainted, OBLIGATE V4 routing for agents with three legs) so enforcement is runtime, not honour-system.
- **Composes with** V14 Trajectory Logging + V17 Online Eval — V14 supplies the stream the Runtime Monitor watches; V17 raises the alert when a 2→3 transition is detected.
- **Composes with** V13 Tool Budget — capping the dynamic tool surface reduces the chance of dynamic acquisition of a third leg.
- **Distinct from** V4 / V6 / V8 — V3 is the audit; V4/V6/V8 are the mitigations. V3 alone does not protect anything; V4/V6/V8 alone, applied without an audit, may protect the wrong boundary.
- **Distinct from** V5 Guardrail Layering — V5 is the general input/output safety layer (all four checkpoints). V3 is specifically about the *capability-combination* risk that V5 cannot see, because V5 inspects content, not architecture.
- **Wraps** O15 Agent Handoff and I3 MCP Server — both are integration patterns that can compose or acquire a third leg; the V3 audit must run on the post-composition / post-load capability set, not the pre-load one.
- **Pairs with** V1 Human-in-the-Loop — the safe default when a runtime transition to 3 legs is detected is to pause and require human approval before the next outbound action.
- **Counters** the anti-pattern A14 Trust Handoff — agent-to-agent trust without verification is exactly the cross-agent compositional trifecta the per-system audit is designed to catch.
- **Named after** Simon Willison's framing — *"the lethal trifecta"* (June 2025) is the term of art; *"rule of two"* is the prescriptive form: any two of the three is OK; three is not.

## Sources

- Willison, S. (2023) — "The Dual LLM pattern for building AI assistants that can resist prompt injection" — [`simonwillison.net/2023/Apr/25/dual-llm-pattern/`](https://simonwillison.net/2023/Apr/25/dual-llm-pattern/). The architectural origin of the privileged/quarantined split.
- Willison, S. (2025) — "The lethal trifecta for AI agents" — [`simonw.substack.com/p/the-lethal-trifecta-for-ai-agents`](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents). The naming and clearest statement of the three-leg condition.
- Willison, S. (2025) — "CaMeL offers a promising new direction for mitigating prompt injection attacks" — [`simonwillison.net/2025/Apr/11/camel/`](https://simonwillison.net/2025/Apr/11/camel/). Commentary on the CaMeL paper and its place in the trifecta-defence landscape.
- Debenedetti, E. et al. (2025) — "Defeating Prompt Injections by Design" (CaMeL), arXiv 2503.18813 — [`arxiv.org/abs/2503.18813`](https://arxiv.org/abs/2503.18813). The first formal capability-based defence; an architectural realisation of V3 → V4.
- Beurer-Kellner, L. et al. (2025) — "Design Patterns for Securing LLM Agents against Prompt Injections", arXiv 2506.08837 — [`arxiv.org/abs/2506.08837`](https://arxiv.org/abs/2506.08837). Six design patterns (Action-Selector, Plan-Then-Execute, LLM Map-Reduce, Dual LLM, Code-Then-Execute, Context-Minimisation) — each breaks at least one leg.
- NCC Group — "Exploring Prompt Injection Attacks" and "Non-Deterministic Nature of Prompt Injection" — [`nccgroup.com/us/research-blog/exploring-prompt-injection-attacks/`](https://www.nccgroup.com/us/research-blog/exploring-prompt-injection-attacks/) and [`nccgroup.com/research/non-deterministic-nature-of-prompt-injection/`](https://www.nccgroup.com/research/non-deterministic-nature-of-prompt-injection/). Practitioner threat-model framing for prompt injection in agent systems.
- OWASP — LLM Top 10 for LLM Applications (2025) — LLM01 (Prompt Injection) and LLM06 (Excessive Agency) describe the trifecta condition as a structural risk.
- Perez, F. & Ribeiro, I. (2022) — "Ignore Previous Prompt: Attack Techniques For Language Models". The first systematic study of prompt injection; foundational threat model.
- Saltzer, J. & Schroeder, M. (1975) — "The Protection of Information in Computer Systems". The principle of least privilege, which the trifecta audit operationalises for agents.
