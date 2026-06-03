# I5 — Agent Card

> Publish a machine-readable description of an agent — identity, skills, endpoint, auth, capabilities — at a well-known URL, so other agents can discover and verify it without out-of-band configuration.

**Also Known As:** Agent Manifest, Capability Declaration, Well-Known Agent Descriptor, AgentCard (A2A protocol term).

**Classification:** Category VI — Integration · the *discovery* primitive of the category — agents-finding-agents, as distinct from I2/I3's tools-being-found by an agent · prerequisite to **I6 A2A Delegation**.

---

## Intent

Make an agent self-describing on the open web: serve a stable JSON document at a well-known path that names its identity, skills, endpoint, authentication, and protocol version, so other agents can locate it, verify compatibility, and call it without hard-coded configuration.

## Motivation

When a system has more than one agent — especially when those agents come from different vendors, teams, or organisations — orchestrators must answer two questions before delegating any work. *Which agent can do this task?* And *how do I talk to it?* Without a standard, both answers live in bespoke configuration: a YAML file the orchestrator reads, a hand-maintained registry, hard-coded URLs in code. Every new agent is a deploy on the orchestrator side; every capability change risks silent skew between what the orchestrator thinks the agent does and what the agent actually does.

The same problem was solved for the web long ago by RFC 8615 well-known URIs: a fixed path (`/.well-known/…`) at which a service self-describes for any client that knows the scheme. Google's A2A protocol (announced April 2025, donated to the Linux Foundation June 2025) applies that move to agents. An A2A-compliant agent serves a JSON document — an *Agent Card* — at `/.well-known/agent-card.json`. The card names the agent, lists its skills with input/output schemas, points to its service URL, declares authentication, and states which protocol versions it speaks. Any A2A client can fetch it, decide whether to trust and call this agent, and discover changes by re-fetching.

The pattern's unique contribution is to make agent identity and capability *queryable by URL*. It is not a tool description — that is I2 / I3 / MCP, which describe operations exposed to a single agent. The Agent Card describes the agent itself, to other agents. The grain is different: I3 says "here are the tools this MCP server exposes"; I5 says "here is the agent, and here are the skills it offers as an A2A peer". Without I5 there is no first move in a multi-agent ecosystem — I6 A2A Delegation has nothing to delegate *to* until it can find and verify the executor.

## Applicability

Use I5 when:

- multiple agents — particularly from different teams, vendors, or organisations — must find each other dynamically;
- the agent is designed to receive tasks from *other agents*, not only from human users (an A2A server, in protocol terms);
- the system implements or plans to implement **I6 A2A Delegation**, the Agent2Agent protocol, or any of its peers (ACP, ANP);
- capability versioning matters and you want compatibility checks before invocation rather than at failure time;
- the agent participates in an agent registry, marketplace, or directory.

Do not use I5 when:

- the agent is consumed only by human users via a UI — there is no agent peer to read the card. Use **I1 Direct API Call** or the relevant UI integration;
- the agent exposes *tools* (not skills) to a single calling LLM — that is **I3 MCP Server**'s remit, not I5's;
- the system has exactly one agent and no plans to add a second — the card is overhead with no consumer. Re-evaluate when a second agent appears;
- you can guarantee the orchestrator and the executor will always ship together as one codebase — use **O15 Agent Handoff** for the intra-system handoff and skip the discovery layer entirely.

## Decision Criteria

I5 is right when more than one agent exists, they may be developed independently, and capability discovery must work without manual orchestrator configuration.

**1. Count the agents and their origins.** How many distinct agents will need to find each other? From how many independently-deployed codebases?
- 1 agent, or N agents all in one deploy $\to$ no I5 yet; revisit if a second team or vendor enters. For intra-deploy handoff use **O15 Agent Handoff**.
- 2+ agents across 2+ deploys $\to$ I5 is the discovery layer; configure-by-URL beats configure-by-YAML.
- N agents across an open ecosystem $\to$ I5 is mandatory, paired with a registry.

**2. Map who calls whom.** Is the agent called by other *agents* (machine consumers reading JSON) or by *humans / a UI* (consumers reading a webpage)?
- Agent-to-agent $\to$ I5 (and **I6 A2A Delegation** to actually call).
- Human-to-agent only $\to$ I5 unnecessary; skip.
- LLM-inside-one-agent calls tools $\to$ that is **I2 Function Call** or **I3 MCP Server**, not I5.

**3. Cost the maintenance.** The card must stay in sync with the deployed agent or it actively misleads. Is the card generated from the running deployment (live endpoint) or hand-maintained?
- Generated $\to$ safe; the card is a projection of current code.
- Hand-maintained $\to$ expect drift; institute a CI check that the card matches the agent's actual skill registry before merge.

**4. Verify the trust model.** Other agents will read this card and trust its claims. How is the card authenticated?
- HTTPS only $\to$ bare minimum; the certificate proves the *domain*, not the *claims*.
- Signed card or signed-skills $\to$ consider for production; mitigates the *spoofed card* failure mode.
- Sensitive-action skills $\to$ never trust the card alone. The caller verifies, then calls — and the call itself carries authentication.

**5. Pick the path discipline.** The A2A spec mandates `/.well-known/agent-card.json` (the older drafts used `/.well-known/agent.json`; treat that as legacy). Use the current path; serving the legacy path as an alias is harmless.

**Quick test — I5 is the right pattern when:**

- two or more independently-deployed agents must call each other, *and*
- the call is agent-to-agent (machine reading JSON, not human reading a UI), *and*
- you are implementing — or about to implement — **I6 A2A Delegation** or a peer protocol, *and*
- the card can be generated from the running deployment, not hand-maintained drift-bait.

If only one agent exists, or the consumer is a human UI, skip I5. If the consumer is *one* LLM calling tools inside one agent, that is **I2 / I3**, not I5. If two agents share a codebase and a deploy, **O15 Agent Handoff** is the lighter pattern; reach for I5 when the deploy boundary actually separates them.

## Structure

```
   Agent service (the I5 publisher)
   ────────────────────────────────
                │
                ├── /.well-known/agent-card.json     ← static path; RFC 8615
                │       returns: AgentCard JSON
                │       (name, version, url, skills[],
                │        capabilities, authentication, protocolVersion)
                │
                └── /api/...  (the actual A2A endpoint the card points to)

   Discovery, by any consumer
   ──────────────────────────
       Consumer agent                       Registry / Catalogue (optional)
            │                                       │
            │  GET .well-known/agent-card.json      │  GET /agents?skill=…
            ▼                                       ▼
       AgentCard JSON ────────────────▶ verify schema, version, skill
            │
            ├── card valid AND skill matches    → proceed to I6 A2A Delegation
            └── card invalid OR mismatch        → refuse / try alternative
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Agent Card document** | the JSON declaration itself — identity, skills, endpoint, auth, protocol version | (none — it is the artefact) $\to$ JSON payload | be a hand-maintained file checked into a repo. The card and the agent must share a single source of truth, or drift is guaranteed. |
| **Card Publisher** | serving the card at `/.well-known/agent-card.json` | request $\to$ AgentCard JSON | serve a *static file* divorced from the running deployment — generate the card from the agent's actual skill registry at request time (or build time, with a CI check that it matches). |
| **Skill descriptor** | the per-skill entry — `id`, `name`, `description`, `inputModes`, `outputModes`, examples | skill registration $\to$ AgentSkill object | omit input/output schemas; without them, the Card Consumer cannot do compatibility checks and falls back to trial-and-error invocation. |
| **Card Consumer** | fetching, validating, and acting on the card | URL $\to$ verified card OR rejection | trust the card's claims as authority for sensitive actions; the card is a *handshake*, not a credential. Sensitive-action authority comes from the auth scheme the card *points to*, not from the card itself. |
| **Skill Registry** *(optional)* | a directory of known agents and their cards | query (skill, domain, vendor) $\to$ set of card URLs | be the only path to discovery — well-known URI must keep working with no registry, or the ecosystem becomes registry-locked. |
| **Card-update signal** *(optional)* | telling consumers a card has changed | deploy event $\to$ cache invalidation | be silent — long TTLs without an invalidation signal mean consumers act on stale capability information. |

Six participants, only one of which (the card itself) is an artefact; the rest are operational concerns. The pattern's reliability hinges on whether the Publisher is generated from the deployment or copied from a file — the most common failure is a card that documents a capability the agent no longer has, or omits one the agent now offers.

## Collaborations

A consumer agent — usually an orchestrator about to delegate — knows or guesses the domain of a candidate executor (`research-agent.example.com`). It performs an HTTPS GET on `/.well-known/agent-card.json`. The Card Publisher generates the response from the agent's live skill registry; the consumer validates the JSON against the AgentCard schema, checks the `protocolVersion` it advertises, and looks for a skill whose `id` and input schema match the task to delegate. If the match holds, the consumer hands off to **I6 A2A Delegation**: it POSTs a task to the agent's declared service URL, presenting the auth scheme the card named. If any check fails — schema mismatch, missing skill, unsupported protocol version, expired TLS — the consumer either tries the next candidate from a Skill Registry or escalates to **V1 Human-in-the-Loop**. Throughout, the consumer logs the card fetch, the validation result, and the chosen executor's identity and version to **V14 Trajectory Logging**, so post-hoc audit can answer "which agent did we call and what did it claim it could do at that moment".

## Consequences

**Benefits**
- Decouples orchestrator deploys from executor deploys — new agents and new skills become discoverable without orchestrator code changes.
- Versioned capability declaration enables compatibility checks *before* invocation, replacing late-failing schema-mismatch errors with early refuse-with-reason.
- Standard well-known path means ecosystem tools (registries, monitors, security scanners) can index agents the same way they index web services.
- Card is human-readable JSON, so the same artefact serves operator inspection, automated discovery, and security audit.

**Costs**
- Maintenance overhead — the card must track the agent or it lies. Generation-from-deployment is the discipline; a hand-edited card is a hazard.
- Adds a small attack surface: an unauthenticated endpoint that names internal capabilities and endpoints. Treat the card's *contents* as semi-public; do not enumerate internal tooling there.
- Adds a discovery round-trip to first invocation latency; cache cards with a TTL (and a way to invalidate them on agent redeploy).

**Risks and failure modes**
- *Card drift* — the card promises a skill the agent no longer implements (or omits one it does); orchestrators delegate based on the lie. Mitigate with CI: card-vs-registry diff on every deploy.
- *Spoofed card* — an attacker stands up an Agent Card claiming the capabilities of a trusted internal agent, at a domain that *looks* right. HTTPS proves the domain; trust the card only inasmuch as you trust the domain.
- *Stale cache* — consumer caches the card with a 24h TTL; agent redeploys with reduced skills; consumer keeps trying the missing skill for 24h. Pair caching with an invalidation signal or a short TTL on first deploys.
- *Static-file fossil* — the card is a file checked into the repo, served by a static handler; it has not been touched in six months while the agent has changed twice. The pattern's most common decay mode.
- *Schema underspecification* — skills lack input/output schemas, so consumers fall back to "try it and see"; the I5+I6 contract collapses into the same trial-and-error that I5 was supposed to prevent.

## Implementation Notes

- Serve the card from a live endpoint generated from the agent's actual skill registry, not a static file. The agent's framework should produce the card; the framework should fail-build if the registry and the served card disagree.
- Use the current path `/.well-known/agent-card.json`. The legacy `/.well-known/agent.json` is documented in older A2A drafts; serving both as aliases is fine but the canonical is `agent-card.json`.
- Include `protocolVersion` and version your card format independently from your agent version. A consumer's compatibility check is `(card protocolVersion ∈ supported set) AND (skill input schema ⊇ task input)`.
- Give every skill a stable `id`, a clear `description`, and explicit `inputModes` / `outputModes`. Add at least one `example` per skill; consumers reading the card programmatically benefit from a concrete shape.
- Treat the card as semi-public. The card names skills and the service URL; it should not enumerate every internal tool, list of model versions, or operational endpoints. What goes on the public card is a deliberate choice — different from what goes on an internal Skill Registry. Write skill descriptions as compact, high-signal tokens. When an orchestrator loads multiple Agent Cards to select an executor, all descriptions enter its context simultaneously. By mechanism 2 (O(n²) attention cost) and mechanism 4 (U-shaped recall), descriptions that bury discriminating information in prose rather than leading with it will be systematically under-attended by the orchestrator model compared to cards that lead with the key capability signal.
- Authentication declared in the card is the scheme the consumer must use when calling the agent (Bearer, OAuth2, etc.). The card is *not itself* an authentication artefact; treat its contents as advertisement, not authority.
- Pair with **V14 Trajectory Logging** — every card fetch, validation result, and version negotiated must end up in the trace; auditing "which executor were we talking to" depends on it.
- Pair with **V6 Prompt Injection Shield** when the card's `description` strings are fed into an LLM-driven orchestrator. The card is *external content*; treat its free-text fields with the same caution as any other untrusted input.
- Where the card supports it, include signed assertions (signed cards, signed skills) — this is the cleanest mitigation for the *spoofed card* failure mode.
- Generate clients from the card's skill schemas where the SDK supports it. Turns capability changes into build-time errors on the consumer side, the way an OpenAPI generator turns API changes into build errors.
- An orchestrator that regularly consults the same set of trusted executor agents can treat those Agent Cards as prefix-cache targets (mechanism 5): the card contents are stable between deployments, making them ideal candidates for provider-level KV state reuse. This converts the card-fetch round-trip from a prefill cost to a ~10% cache-read cost for repeated orchestrator calls against the same executor set.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring. I5 is, like I1, a pattern with **no LLM step inside it** — the publisher generates JSON from code, the consumer parses JSON in code. The LLM may sit upstream (a planner deciding "I need to find an agent that can do X") or downstream (the orchestrator handing the verified card to I6 to actually invoke the agent), but never inside the card-publishing or card-validating path.

**Composition:** I5 is the discovery prerequisite to **I6 A2A Delegation** (the call). It sits underneath **O6 Orchestrator-Workers** and **O7 Supervisor Hierarchy** when those patterns cross deploy boundaries; it is orthogonal to **I3 MCP Server**, which describes tool-level discovery, not agent-level. The card's `description` fields enter LLM-driven planners, so **V6 Prompt Injection Shield** applies to the seam between card and orchestrator-LLM context. **V14 Trajectory Logging** captures every fetch.

**The chain — publish (the agent service):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| P1 | Register skill in the agent's skill registry (build/deploy time) | `code` | — |
| P2 | On `/.well-known/agent-card.json` GET, assemble card from registry | `code` | — |
| P3 | Serve card with `Content-Type: application/json` + cache headers | `code` | — |

**The chain — discover (the consumer):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| D1 | Determine candidate agent domain (config, registry, or planner output) | `code` (or planner `LLM`) | optional planner |
| D2 | GET `https://{domain}/.well-known/agent-card.json` | `code` | I1 Direct API Call (underneath) |
| D3 | Validate JSON against AgentCard schema; check `protocolVersion` | `code` | V20 Schema Validation |
| D4 | Match required skill id + input schema to card's skills | `code` | — |
| D5 | Log fetch + validation result + chosen executor identity | `code` | V14 Trajectory Logging |
| D6 | Hand verified card to **I6 A2A Delegation** for actual invocation | `code` | I6 |

**Skeleton:**

```
# Publisher side — runs inside the agent service
def serve_agent_card(request):
    skills = agent.skill_registry.list()              # code — live, not a static file
    card = {
        "name": agent.name,
        "version": agent.version,
        "protocolVersion": "a2a/1.0",
        "url": agent.service_url,
        "description": agent.description,
        "skills": [skill.to_a2a() for skill in skills],
        "capabilities": {"streaming": True, "pushNotifications": False},
        "authentication": {"schemes": ["Bearer"]},
        "provider": {"organization": "...", "contact": "..."},
    }
    return json_response(card, cache="max-age=300")    # short TTL or invalidation

# Consumer side — runs inside the orchestrator
def discover_and_verify(domain, required_skill_id, required_input_schema):
    card = http_get(f"https://{domain}/.well-known/agent-card.json")  # code
    validate_schema(card, AGENT_CARD_SCHEMA)            # code — V20
    assert card["protocolVersion"] in SUPPORTED_PROTOCOLS
    skill = next((s for s in card["skills"] if s["id"] == required_skill_id), None)
    if skill is None or not schema_compatible(required_input_schema, skill["input_schema"]):
        log_and_refuse(card, required_skill_id)         # code — V14
        return None
    log_executor_choice(card, skill)                    # code — V14
    return (card, skill)                                # hand to I6
```

**The LLM sessions:** *None inside I5.* The card publisher is code generating JSON from a registry; the card consumer is code validating JSON against a schema. If an LLM-driven planner upstream is deciding *which* agent to look up, that planner is a separate concern (it uses its own session and its own prompt; the result is a domain name handed to step D1). If a downstream orchestrator-LLM consumes the card's free-text fields to decide whether to delegate, treat those fields with **V6 Prompt Injection Shield** — the card's `description` is externally-sourced text once it enters an LLM context.

**Specialist-model note.** None — I5 loads no model. The build dependencies are (i) an AgentCard JSON Schema for validation on the consumer side, (ii) an SDK that can generate cards from a live skill registry on the publisher side (the official `a2a-python` and `a2a-js` SDKs both ship this), and (iii) a CI check that the served card matches the agent's actual capabilities — without that check, the static-file-fossil failure mode is inevitable.

## Open-Source Implementations

- **A2A Protocol — canonical spec** — [`github.com/a2aproject/A2A`](https://github.com/a2aproject/A2A) — the open specification (Apache 2.0; donated by Google to the Linux Foundation, June 2025). `docs/specification.md` defines the AgentCard schema; `docs/topics/agent-discovery.md` defines the `/.well-known/agent-card.json` discovery path per RFC 8615.
- **a2a-python** — [`github.com/a2aproject/a2a-python`](https://github.com/a2aproject/a2a-python) — the official Python SDK; ships `AgentCard` types, a card-serving helper, and a card-fetch client. Implements A2A 1.0 with compat for 0.3.
- **a2a-js** — [`github.com/a2aproject/a2a-js`](https://github.com/a2aproject/a2a-js) — the official JavaScript / TypeScript SDK; same surface as a2a-python for Node and browser-side agents.
- **a2a-samples** — [`github.com/a2aproject/a2a-samples`](https://github.com/a2aproject/a2a-samples) — runnable example agents publishing their Agent Cards and example clients consuming them; the cleanest reference for the end-to-end I5+I6 flow.
- **awesome-a2a** — [`github.com/ai-boost/awesome-a2a`](https://github.com/ai-boost/awesome-a2a) — community index of A2A agents, tools, servers, and clients; useful for surveying the implementation landscape.
- **a2a-go** — [`github.com/a2aserver/a2a-go`](https://github.com/a2aserver/a2a-go) — community Go server implementation; demonstrates card publishing in a language outside the official SDK set.

## Known Uses

- **Google A2A reference deployments** — the A2A specification's sample agents (in `a2a-samples`) publish Agent Cards at `/.well-known/agent-card.json` and discover each other through them; the canonical demonstration of the pattern.
- **Cross-vendor agent pipelines on A2A** — production deployments combining agents from different LLM providers, where each agent advertises its skills via its card and the orchestrator selects executors by skill match. Listed examples in `awesome-a2a` show multi-vendor compositions in research, support, and analytics domains.
- **ADK (Agent Development Kit) A2A integrations** — Google's ADK exposes ADK-built agents as A2A servers with auto-generated Agent Cards from the agent's tool / skill definitions; one of the larger production-grade emitters of the pattern.
- **Agent registries and marketplaces (early)** — emerging directories that index Agent Cards across organisations, providing a registry layer on top of the well-known discovery path. Ecosystem is early; the well-known URI remains the primary discovery mechanism.
- **Internal multi-team agent platforms** — enterprises with multiple agent-owning teams use Agent Cards to let each team's agent be discoverable by any other team's orchestrator, without a central coordination team maintaining a config registry.

## Related Patterns

- **Required by** I6 A2A Delegation — I6 needs a verified Agent Card before it can submit a task. I5 is the discovery step; I6 is the call. The two are co-designed and almost always deployed together.
- **Distinct from** I3 MCP Server — I3 advertises *tools* to *one calling LLM* via the Model Context Protocol; I5 advertises *the agent itself* to *other agents* via A2A. Different grain: I3 is tool-level, I5 is agent-level. A single agent can serve both — an Agent Card for its public skills, an MCP server for its private tools — and the two are complementary, not competing.
- **Pairs with** O6 Orchestrator-Workers — when an orchestrator dynamically selects workers from a set of candidate agents, it reads each candidate's Agent Card to verify capability before delegation.
- **Pairs with** O7 Supervisor Hierarchy — supervisors discover subordinate agents' capabilities via Agent Cards; capability changes propagate without supervisor reconfiguration.
- **Distinct from** O15 Agent Handoff — O15 is the intra-system handoff inside one deploy (shared memory, in-process); I5 is the inter-system discovery prerequisite to I6's inter-system delegation. If two agents always ship together, O15 suffices and I5 is overhead.
- **Pairs with** V7 AgentSpec — the deployed agent's V7 spec and its published Agent Card describe overlapping concerns from different angles (governance constraints vs. capability advertisement); keep them consistent.
- **Pairs with** V14 Trajectory Logging — every card fetch, validation result, and executor-selection decision must end up in the trace, or post-hoc audit cannot reconstruct which agent was called.
- **Pairs with** V6 Prompt Injection Shield — the card's free-text fields (`description`, skill descriptions, `examples`) become external content the moment an orchestrator-LLM reads them. Treat accordingly.
- **Underlies** I1 Direct API Call (transport) — the fetch of `/.well-known/agent-card.json` is itself an I1 call; I5 is the *contract* served over that call.

## Sources

- A2A Protocol Specification — [`a2a-protocol.org/latest/specification`](https://a2a-protocol.org/latest/specification/) — the canonical AgentCard schema and discovery model (current as of 2026).
- A2A Agent Discovery documentation — [`a2a-protocol.org/latest/topics/agent-discovery`](https://a2a-protocol.org/latest/topics/agent-discovery/) — the well-known URI strategy and registry / direct-configuration alternatives.
- IETF RFC 8615 — *Well-Known Uniform Resource Identifiers (URIs)* — the underlying web standard the discovery path follows.
- Linux Foundation — A2A project transfer from Google, June 2025; sister to the Agentic AI Foundation (AAIF, anchoring MCP, AGENTS.md, and Goose) but a distinct project under the Foundation's umbrella.
- Anthropic Model Context Protocol — [`modelcontextprotocol.io`](https://modelcontextprotocol.io) — the complementary tool-level specification (I3); I5 is its agent-level peer.
- IBM / Red Hat — Agent Communication Protocol (ACP), 2025 — message-based peer to A2A; addresses the same agent-to-agent layer with different transport choices.
- Google ADK (Agent Development Kit) — A2A integration documentation showing card auto-generation from agent definitions.
