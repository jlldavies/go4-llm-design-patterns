# V7 — AgentSpec / Declarative Governance

> Specify the agent's operating rules — its permissions, prohibitions, and obligations — as an external declarative artefact, and enforce them at runtime in a policy engine that runs *outside* the LLM and cannot be overridden by prompt manipulation.

**Also Known As:** Policy-Driven Agent, Runtime Governance, Deontic Control, Declarative Policy Engine, Programmable Privilege Control. The agent equivalent of a Unix capability system or an OPA-style policy decision point.

**Classification:** Category V — Reliability · Band V-A Safety and Security · the *deterministic, external* governance layer; the hard-enforcement counterpart to the soft, in-prompt **S9 Constitutional Framing**, and the outer boundary required by **H5 Constitutional Self-Alignment**.

---

## Intent

Place the agent's hard rules in code outside the model, expressed in a declarative policy artefact, and have an independent runtime engine check every proposed action against that policy — so the rules survive prompt manipulation, produce an audit record, and can be changed without redeploying the model.

## Motivation

Anything an agent must *never* do — exfiltrate classified data, send an external email when handling restricted content, call a destructive tool without confirmation, exceed a per-session spending cap — needs an enforcement mechanism that is independent of the model's behaviour. The pervasive failure mode is to put these rules in the prompt and call the system governed. That is **S9 Constitutional Framing**: a soft, in-prompt set of principles applied through the model's own language reasoning. S9 is genuinely useful for the cases requiring interpretation (judgement calls, values, style, broad ethics), but it is *probabilistic*: an adversarial input can talk the model out of its constitution (Perez & Ribeiro 2022; the jailbreak literature), and there is no deterministic record of what was permitted and why. Treating S9 as the enforcement boundary is the governance equivalent of putting the bouncer's instructions on a sign at the door and hoping the patrons read them. The negation-failure literature (NeQA; the pink-elephant effect) shows model self-restraint fails systematically on the prohibition cases that matter most.

V7 externalises and hardens this layer. The rules live in a declarative artefact — YAML, a domain-specific language, a `.rail` file, a Rego policy — that compliance and security can read directly. A policy engine independent of the LLM intercepts every proposed tool call, every state transition, every outbound communication, and evaluates it against the declared rules. The deontic vocabulary used by the published frameworks (AgentSpec; the Architecting Agentic Communities catalogue) is precise: **PERMIT** (this action is allowed under these conditions), **PROHIBIT** (this action is blocked, conditionally or unconditionally), **OBLIGATE** (this action is *required* when these conditions hold), and **WAIVE** (a scoped, audited exception to a PROHIBIT). The check runs every time; the decision is deterministic for the rules the spec covers; and every check writes to **V14 Trajectory Logging** with the matched rule and the input it was evaluated against. The analogy is precise: S9 is the employee told the rules verbally; V7 is the employee whose badge literally cannot open certain doors.

V7 is fundamentally distinct from **V5 Guardrail Layering** and from **S9 Constitutional Framing** along two axes. From V5: V5 is the *structure* of placing checks at the four I/O boundaries (input, pre-tool-call, post-tool-call, output); V7 is the *declarative policy artefact* that those checks consult. V5 without V7 hardcodes rules in guard code (per-tool ad hoc); V7 without V5 has nowhere to fire (the engine has rules but no enforcement seams). They compose: V5 is the *where*, V7 is the *what*. From S9: S9 is in-prompt, probabilistic, interpretive; V7 is out-of-prompt, deterministic for what it covers, enumerable. They are not alternatives — they are the soft/hard layered pair (CONFLICTS.md CRITICAL 3). In safety-critical systems both are mandatory: S9 catches the cases V7 did not anticipate; V7 catches the cases S9 was talked out of.

## Applicability

Use V7 when:

- the agent operates in a regulated industry (healthcare, finance, legal, defense, critical infrastructure) and compliance must be *provable*, not "the prompt says so";
- the deployment is enterprise-scale and IT / security must control agent capability independent of any prompt the application team writes;
- the agent is multi-tenant or multi-role, and rules differ per tenant / per role in ways the prompt cannot reliably distinguish;
- a published audit trail of policy decisions is required by law or contract (EU AI Act Article 9 risk-management evidence; SOC 2; HIPAA);
- the action surface includes irreversible or high-blast-radius operations (data deletion, financial transactions, external communications, code execution against production) that cannot rely on probabilistic self-restraint;
- the agent crosses any two of the **V3 Lethal Trifecta** conditions — V7 is one of the named mitigations because it can enforce the third condition's absence deterministically.

Do not use when:

- the requirements are interpretive — judgement calls, broad ethics, style, taste — and cannot be reduced to enumerable rules; use **S9 Constitutional Framing** instead and accept the probabilistic ceiling;
- the agent is a personal-scale prototype with no compliance surface and a single trusted user — V7's authoring and engine cost will not amortise;
- the rule set is so small (one or two prohibitions) that the cost of standing up a policy engine exceeds the cost of a hardcoded check in the guard layer; use **V5 Guardrail Layering** with inline rules;
- policy authoring expertise is unavailable — a misconfigured V7 produces a *false* sense of governance, which is worse than no V7 (the failure mode below: WAIVE proliferation, gap-default-to-allow).

## Decision Criteria

V7 is right when rules are enumerable, enforcement must be deterministic, and a written audit of policy decisions is required.

**1. Score the enumerability of the requirement.** Can the rule be written as a structured predicate over (action name, parameters, context attributes)? — *"PROHIBIT `send_email` when `context.classification == restricted`"*. If yes, V7 is the right layer. If the rule is *"be respectful of user wellbeing"*, it is interpretive — use **S9 Constitutional Framing** and accept that S9 is probabilistic. The split is load-bearing: V7 carries the *letter*; S9 carries the *spirit*. In safety-critical systems you need both (CONFLICTS.md CRITICAL 3).

**2. Score the audit and compliance surface.** Does a human reviewer (compliance, security, regulator, customer auditor) need to read *the rules themselves*, not the prompt, not the code? Does an incident response need to answer *"why did the agent do X?"* with *"because rule R-014 PERMITTED it under condition C"*? If yes, V7 is the right layer — the policy artefact and the V14 trajectory together are the audit object. If no audit surface exists, V7's cost is unjustified.

**3. Score adversarial exposure.** How exposed is the system to prompt injection, untrusted content, or user manipulation? S9 alone is *probabilistic* — a sufficient prompt can talk the model out of its constitution. V7 is *deterministic for the rules it covers* — the engine checks the action regardless of what the model "intends". High exposure (open-internet, untrusted document processing, V3 Trifecta cases) makes V7 non-negotiable; low exposure (internal, single-trusted-user, no untrusted content) makes S9-only defensible.

**4. Cost the policy infrastructure.** V7 is real infrastructure. Plan for: (a) a policy DSL or schema (AgentSpec, Rego, NeMo Colang, Invariant rules, OPA, or a custom YAML); (b) an engine that intercepts the agent's action stream and evaluates rules with millisecond latency (AgentSpec's measured overhead is in the millisecond range; Progent reports similar); (c) a waiver workflow with explicit authorisation and scope; (d) integration with **V14** so every decision is logged with the matched rule and the inputs. If any of (a)–(d) cannot be staffed, V7 will degrade into nominal governance (the failure mode below).

**5. Pick a build path.** Three options trade authoring cost for power:
- *Per-tool allow-lists with parameter constraints* — small inline policies expressed as code (a Python function the **V5 Pre-Call Guard** calls). Fast to ship; doesn't scale beyond ~20 rules.
- *DSL-based runtime enforcement* — **AgentSpec** (Wang et al. 2025, arXiv 2503.18666), **Progent** (Shi et al. 2025, arXiv 2504.11703), **Invariant** rules, **NeMo Guardrails** Colang. Purpose-built for LLM agent policies; integrate with LangChain, OpenAI Agents SDK, MCP.
- *General policy engine* — **Open Policy Agent / Rego** (CNCF). Most powerful, language-agnostic, the standard authorisation engine in cloud-native systems; you write the agent-specific adapter. Heaviest authoring cost; the standard for organisations that already run OPA elsewhere.

**Quick test — V7 is the right pattern when:**

- the rules are enumerable as deontic predicates (PERMIT / PROHIBIT / OBLIGATE / WAIVE), *and*
- enforcement must be deterministic and survive prompt manipulation, *and*
- a written audit trail of policy decisions is required by compliance, security, or contract, *and*
- the policy infrastructure can be staffed (authoring, engine, waiver workflow, V14 integration).

If the rule is interpretive rather than enumerable, use **S9 Constitutional Framing** (and accept it is probabilistic). If the rule set is tiny and the audit surface is internal, hardcode the checks inside **V5 Guardrail Layering** Pre-Call Guards. If you need principles that *evolve* across sessions, layer **H5 Constitutional Self-Alignment** *above* V7 — H5 proposes; humans approve; V7 enforces the outer boundary that no proposal may cross (CONFLICTS.md CRITICAL 7).

## Structure

```
                  ┌─────────────────────────────────────────────────┐
                  │       AgentSpec  (declarative artefact)         │
                  │  PERMIT     <action, conditions>                │
                  │  PROHIBIT   <action, conditions>                │
                  │  OBLIGATE   <action, when>                      │
                  │  WAIVE      <prohibit_id, scope, authority>     │
                  └─────────────────────────────────────────────────┘
                                       │
                                       ▼
  Agent ─▶ proposed action ─▶ ┌──────────────────────┐ ─▶ allow / deny / inject / escalate
                              │   Policy Engine      │
                              │ (independent of LLM) │
                              └──────────────────────┘
                                       │
                                       ▼
                                Compliance Log (V14)
                                  • rule matched
                                  • inputs evaluated
                                  • decision + waiver if any
                                       │
                                       ▼
                              On PROHIBIT:  V1 Human-in-the-Loop (optional escalation)
                              On OBLIGATE:  inject mandatory action into the agent's plan
                              On WAIVE:     proceed with audited exception
```

The policy artefact is a separate, versioned file. The engine is a separate process or library. The LLM never reads either — it produces proposed actions, the engine adjudicates. The V14 log is the durable record.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **AgentSpec** | the declarative policy artefact — the rules themselves | — $\to$ a versioned, human-readable bundle of PERMIT / PROHIBIT / OBLIGATE / WAIVE rules with conditions | live inside the prompt or inside the agent's code. The artefact must be a separate, named, versioned file — otherwise compliance cannot read it and the engine has no single source of truth. |
| **Policy Engine** | runtime enforcement | (proposed action + agent context + AgentSpec) $\to$ allow / deny / inject obligation / escalate | depend on the LLM. The engine must be deterministic for the rules it covers; an LLM-based "policy engine" is **V15 LLM-as-Judge** — useful, but not V7. The engine's decisions must be reproducible from inputs alone. |
| **Action Interceptor** | wiring the engine into the agent's execution path | every proposed tool call / outbound action $\to$ engine query | let any action bypass it. A single uninstrumented action path is the failure surface for the whole pattern. The interceptor must cover *all* outbound actions, not just tool calls (state changes, memory writes, external sends). |
| **Waiver Authority** | the audited exception path | (PROHIBIT rule + justification + scope) $\to$ time-bounded waiver token | grant permanent waivers. A waiver without an expiry, a scope, and a named authoriser is the start of governance erosion (the WAIVE-proliferation failure mode). |
| **Compliance Log** | the durable record of every engine decision | (rule, inputs, decision, waiver-if-any, timestamp) $\to$ V14 trajectory entry | drop the matched rule or the inputs. A decision without its evidence is useless for audit and for tuning false positives / false negatives. |
| **Policy Author** *(human role)* | the rules themselves | (regulatory requirements + threat model + product needs) $\to$ AgentSpec updates with review and sign-off | write rules without a review process. Self-authored unreviewed policies are how WAIVE becomes the default and how rule gaps proliferate. |

The pattern's reliability comes from the separation: the artefact is *only* declarative; the engine is *only* an evaluator; the interceptor is *only* wiring; the log is *only* a record. A monolithic "governance module" that performs all four collapses the audit story — there is no longer a separate artefact a regulator can read.

## Collaborations

The system loads the AgentSpec at startup; the Policy Engine indexes the rules. The Agent runs as normal — receives input, reasons, proposes a tool call or other outbound action. The Action Interceptor catches the proposal and queries the engine with the action name, parameters, and the relevant agent context (user role, data classification, tenant, prior actions). The engine evaluates the rules: if any PROHIBIT matches and no WAIVE applies, the action is blocked; if an OBLIGATE matches, the engine injects the obligated action into the plan (e.g., "before sending external email, OBLIGATE PII-scan tool call"); if only PERMITs apply or no rule matches and the default is allow, the action proceeds. Every decision — including the rule that matched, the inputs evaluated, any waiver invoked, and the verdict — writes to the Compliance Log via V14. On PROHIBIT with no clean alternative, the engine optionally escalates to V1 Human-in-the-Loop — a human reviewer can grant a scoped, time-bounded WAIVE, which the engine then applies and logs. When the policy needs to change, the Policy Author updates the artefact through the review workflow; the new version is deployed to the engine without touching the model or the agent code. The S9 in-prompt constitution remains active throughout — V7 is the *floor*, S9 is the *interpretive ceiling*, and on conflict V7 wins.

## Consequences

**Benefits**
- *Deterministic enforcement* — for the rules the spec covers, the decision is reproducible from inputs and immune to prompt manipulation.
- *Audit-ready* — the policy artefact is the legible compliance object; the V14 log is the decision history. Together they answer "why did the agent do X?".
- *Updateable without redeployment* — policy changes are artefact changes, not model retraining or prompt edits; reviewer cadence is policy-team cadence, not model-release cadence.
- *Survives prompt injection* — the engine does not read user inputs as instructions; an injection that talks the model into a prohibited action is still blocked at the engine. Policy engine evaluation is deterministic code — the same input always produces the same output, with no sampling variance (mechanism 7). This is what makes V7 immune to injection: there is no probability distribution to shift.
- *Separation of concerns* — application developers own the agent; security / compliance owns the policy. Different reviewers; different release trains.
- *Composable per role* — an Orchestrator-Workers (O6) system can have *different* AgentSpec policies per role: privileged orchestrator, quarantined workers (the V4 Dual LLM pattern expressed declaratively).

**Costs**
- *Real infrastructure* — DSL, engine, waiver workflow, V14 integration. AgentSpec and Progent measure latency in milliseconds, but the build cost is in person-months, not hours.
- *Policy authoring is non-trivial* — writing rules that catch real violations without rejecting legitimate actions requires governance expertise. The empirical AgentSpec paper reports ~95% precision / ~71% recall on auto-generated rules; human review of every rule is the norm.
- *Latency at every action* — every tool call passes through the engine; multi-tool turns add measurable overhead.
- *Maintenance burden* — every new tool, every new domain, every new threat class is a policy update. The artefact rots if not maintained.
- *Two-system reasoning* — operators must hold both the prompt's S9 constitution *and* the V7 policy in mind to predict agent behaviour. Drift between the two is a real risk.

**Risks and failure modes**
- *Policy gaps* — the engine only enforces what is enumerated. Unanticipated situations default to allow (or to deny, depending on default-mode), and either default is dangerous if the policy is incomplete. The threat model must be explicit and revisited.
- *WAIVE proliferation* — under deadline pressure, exceptions are granted faster than they are retired. Within a year the policy is mostly waivers; governance is nominal. Mitigation: every WAIVE has an expiry, a named authoriser, and a scheduled review.
- *Default-to-allow on gaps* — the most common configuration error. Mitigation: default-to-deny on safety-critical action classes; require explicit PERMIT for every category that touches user data, external communication, or destructive operations.
- *Policy / constitution drift* — V7 says one thing, S9 says another, the model behaves according to S9 (because it reads the prompt), the engine permits an action S9 would have refused. Both layers must be reviewed together. CONFLICTS.md CRITICAL 3 names this as a governance failure: both must be updated.
- *Theatre* — V7 is deployed, the audit log is written, no one reads it, no one tunes the rules. The same failure as **A15 Untraced Agent** at the policy layer. Mitigation: V17 Online Eval on policy-decision rates (waiver rate, deny rate, OBLIGATE-injection rate) as quality signals.
- *Misconfigured OBLIGATE* — an obligation injected at the wrong condition triggers unwanted actions or infinite loops. OBLIGATE conditions must be tested as rigorously as PROHIBITs.

## Implementation Notes

- **Separate the policy artefact from the engine from the agent.** The artefact (YAML / DSL / Rego) lives in its own repo or directory, has its own review process, and its own owners. The engine is a library or service. The agent depends on the engine's API, not on the artefact.
- **Default-deny on safety-critical action classes; default-allow only on the long tail of routine reads.** Default-allow on writes, external comms, and destructive actions is how V7 fails.
- **Every WAIVE has three required fields: expiry, scope, authoriser.** No exceptions. A WAIVE without these is an undocumented permission and the start of governance erosion.
- **Pair with V5 Guardrail Layering as the wiring layer.** V5 is the *where* (four boundaries); V7 is the *what* (the policy). The V5 Pre-Call Guard *consults* the V7 engine; the Output Guard *consults* it for redaction policy. Without V5, V7 has no place to fire; without V7, V5's rules are hardcoded.
- **Pair with V14 for every decision.** A decision without a log is unauditable. The log entry must include the matched rule ID, the inputs evaluated, the verdict, and any waiver invoked.
- **Version the AgentSpec.** Policy changes are deployments; deployments need version IDs, rollback paths, and the same review discipline as code.
- **Test the policy.** Adversarial test suites that probe for policy gaps are the V16 Offline Eval of the policy itself. The AgentSpec paper reports >90% prevention of unsafe executions on code-agent benchmarks when the policy is well-authored; on under-specified policies the number is much lower.
- **For Orchestrator-Workers (O6) systems, differentiate the policy per role.** The orchestrator has different permissions from quarantined workers (the V4 Dual LLM split, declaratively). A single AgentSpec for all agents in an O6 system is a misconfiguration.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V7 chains a declarative AgentSpec with a Policy Engine that the V5 Guardrail layer consults at every boundary. It composes with **V5** (the four-point wiring), **S9 Constitutional Framing** (the soft, in-prompt layer V7 hardens), **V14 Trajectory Logging** (every decision logged), **V1 Human-in-the-Loop** (the escalation target on PROHIBIT-with-no-alternative), **V4 Dual LLM** (V7 is how the Privileged / Quarantined split is declared per role), **H5 Constitutional Self-Alignment** (H5 proposes principles within the space V7 permits), and **V16 Offline Eval / V17 Online Eval** (policy is tested adversarially and monitored in production). It is orthogonal to the agent's reasoning pattern — works with R4 ReAct, R5 ReWOO, R7 Reflexion, or any other.

**The chain — per proposed action:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Agent reasons; emits a proposed action (tool call, output, state change) | `LLM` | Agent session |
| 2 | Action Interceptor captures the proposal + agent context | `code` | V5 Pre-Call Guard wiring |
| 3 | Policy Engine evaluates against AgentSpec | `code` | AgentSpec artefact |
| 4 | Branch — PERMIT / PROHIBIT / OBLIGATE / WAIVE | `code` | |
| 5a | On PROHIBIT — block; optionally escalate to V1 | `code` | V1 |
| 5b | On OBLIGATE — inject the obligated action into the plan | `code` | |
| 5c | On PERMIT (or no match + default-allow) — proceed | `code` | |
| 6 | Tool / action executes | `code` | |
| 7 | *(optional)* Policy Engine re-evaluates the result against post-action rules | `code` | AgentSpec artefact |
| 8 | Every decision + matched rule + inputs $\to$ V14 trajectory entry | `code` | V14 |

**Skeleton** — the wiring; the engine and AgentSpec are configuration, not LLM calls:

```
handle_action(agent_action, agent_ctx, spec, engine):
    decision = engine.evaluate(agent_action, agent_ctx, spec)   # code — deterministic
    log_to_V14(decision, matched_rule=decision.rule, inputs=...)

    match decision.verdict:
        case PERMIT:
            result = execute(agent_action)                      # code
            post = engine.post_evaluate(result, spec)           # code — optional
            log_to_V14(post)
            return result
        case PROHIBIT:
            if decision.escalate:
                waiver = V1_human_review(decision)              # V1 escalation
                if waiver: return retry_with_waiver(agent_action, waiver)
            return blocked(decision.reason)
        case OBLIGATE:
            inject_into_plan(decision.required_action)          # code
            return handle_action(agent_action, agent_ctx, spec, engine)
        case WAIVE:
            assert waiver_valid(decision.waiver)
            return execute(agent_action)
```

**The LLM sessions** — V7's core enforcement path has *no LLM calls*. That is the point: the engine is deterministic. LLMs appear only in adjacent components:

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | the system's main generalist | the standard agent setup (S3, S5, S6, S9 constitution, domain context). V7 is orthogonal to the agent's setup; the engine adjudicates *after* the model proposes. | the per-turn context |
| **Policy Author Assistant** *(optional, build-time)* | strong generalist (e.g. GPT-class) | role: *"you draft AgentSpec rules from a natural-language safety requirement; output the structured rule + the test cases that demonstrate it fires correctly"*; the AgentSpec schema. The AgentSpec artefact itself is a stable, reusable prefix that is loaded identically on every policy engine call — configuring the Policy Author Assistant session with prompt caching on the spec prefix (Anthropic: minimum 1024 tokens, 5-minute TTL) substantially reduces the cost of repeated rule-evaluation passes against a large policy (mechanism 5). | the requirement and any existing rules it must compose with |
| **V1 Reviewer Assistant** *(optional, escalation-time)* | small fast generalist | role: *"you summarise a blocked action and the matched rule for a human reviewer; surface the decision the reviewer needs to make (deny / grant waiver / amend rule)"* | the blocked action, the matched rule, and the agent context |

**Specialist-model note.** V7's hot path needs no LLM and no specialist model — the engine is rule evaluation, not inference. The published frameworks (AgentSpec, Progent, Invariant, NeMo Guardrails, OPA) measure latency in milliseconds because there is no model call. The optional **Policy Author Assistant** at build time is where strong generalists help — auto-generating rules from natural-language requirements (the AgentSpec paper reports ~95% precision / ~71% recall using GPT-class models for this), with human review on every rule before it enters the spec. Do *not* turn the runtime engine itself into an LLM — that is **V15 LLM-as-Judge** as a guard, a related but distinct pattern (V15 is probabilistic and slow; V7 is deterministic and fast, and they compose: a V15 judge can be invoked *as an OBLIGATE'd action* on highest-stakes outputs).

## Open-Source Implementations

- **AgentSpec (Wang et al.)** — [`github.com/haoyuwang99/AgentSpec`](https://github.com/haoyuwang99/AgentSpec) — the runtime-enforcement DSL paired with the ICSE'26 paper (Wang et al., arXiv [2503.18666](https://arxiv.org/abs/2503.18666)). Lightweight Python framework; integrates with LangChain; enforcement modes include `stop`, `user_inspection`, corrective invocation, and self-reflection. The most direct embodiment of the V7 pattern as defined here.
- **Progent** — [`github.com/sunblaze-ucb/progent`](https://github.com/sunblaze-ucb/progent) — programmable privilege control for LLM agents (Shi et al., arXiv [2504.11703](https://arxiv.org/abs/2504.11703)). A DSL for fine-grained tool-call privilege policies; reduces AgentDojo attack success rate from 41.2% to 2.2%. Validated against LangChain and the OpenAI Agents SDK.
- **NVIDIA NeMo Guardrails** — [`github.com/NVIDIA-NeMo/Guardrails`](https://github.com/NVIDIA-NeMo/Guardrails) — programmable guardrails toolkit with the Colang DSL for declarative policy across five rail types (input, dialog, output, retrieval, execution). The "execution rails" are V7's enforcement seam; Colang is the policy artefact.
- **Invariant Guardrails** — [`github.com/invariantlabs-ai/invariant`](https://github.com/invariantlabs-ai/invariant) — rule-based contextual guardrails for LLM and MCP-powered agents; Python-inspired matching rules for data-flow, if-this-then-that, and tool-call restrictions; integrated via the Invariant Gateway proxy.
- **Open Policy Agent (OPA) / Rego** — [`github.com/open-policy-agent/opa`](https://github.com/open-policy-agent/opa) — the CNCF-graduated general-purpose policy engine. Not LLM-specific, but the standard authorisation engine in cloud-native systems; the right choice for organisations that already run OPA elsewhere and want one policy substrate for both their services and their agents. You write the agent-specific adapter.
- **Open Agent Spec (Oracle)** — [`github.com/oracle/agent-spec`](https://github.com/oracle/agent-spec) — declarative YAML standard for defining agents and agentic workflows (Open Agent Spec, arXiv [2510.04173](https://arxiv.org/abs/2510.04173)). Broader than V7 (covers the whole agent definition, not only governance), but its guardrail / policy section is a V7-shaped artefact.
- **GuardAgent** — [`github.com/guardagent/code`](https://github.com/guardagent/code) — paired with Xiang et al., arXiv [2406.09187](https://arxiv.org/abs/2406.09187); an LLM-based guard agent that synthesises code-based runtime checks from natural-language safety requests. A hybrid V7 / V15 pattern: LLM authoring of deterministic checks.

## Known Uses

- **Enterprise deployments on AWS Bedrock Guardrails** — managed input/output filtering with topic, content, contextual-grounding, and PII filters expressed declaratively; one of the standard production deployment paths for regulated workloads (finance, healthcare).
- **Microsoft Azure AI Content Safety with Prompt Shields** — declarative content-safety and jailbreak-detection policies enforced server-side across the consumer and enterprise Copilots; the policy artefact and the enforcement engine are distinct, and the latter survives prompt manipulation by design.
- **OpenAI Agents SDK with declarative guardrails** — input, output, and tool guardrails declared as first-class SDK constructs; the production default for agents built on the platform.
- **NeMo Guardrails in regulated production** — financial and healthcare RAG and customer-support deployments using Colang rails for topic restriction, PII redaction, and tool-call gating. The Colang `.co` file is the deployed AgentSpec.
- **Invariant Gateway** in MCP-heavy production deployments — declarative rules enforced as a proxy between the agent and its MCP servers, where the tool surface is large and dynamic.

## Related Patterns

- **Hard / Soft layered with** S9 Constitutional Framing — *the* critical pairing. V7 is hard, specific, external, deterministic; S9 is soft, broad, in-prompt, probabilistic. They are not alternatives — they layer. In safety-critical systems, both are mandatory: V7 carries the *letter* of the rules, S9 carries the *spirit*. On conflict, V7 wins. See CONFLICTS.md CRITICAL 3.
- **Pairs with** V5 Guardrail Layering — V5 is the four-point I/O *wiring*; V7 is the declarative policy *artefact* the wiring consults. V5 without V7 hardcodes rules per-guard; V7 without V5 has no enforcement seam. The two together are the standard production governance posture.
- **Pairs with** V14 Trajectory Logging — every engine decision and its matched rule must be logged. Without V14, V7 has no audit trail; with V14, V7 *is* the audit object.
- **Pairs with** V1 Human-in-the-Loop — the escalation target when the engine emits a PROHIBIT-with-no-clean-alternative; a human can grant a scoped, time-bounded WAIVE.
- **Pairs with** V4 Dual LLM — V7 is how the Privileged / Quarantined split is *declared* per role; a single AgentSpec for all agents in a V4 system is a misconfiguration.
- **Required by** H5 Constitutional Self-Alignment — H5 *proposes* evolving principles; humans approve; V7 enforces the outer boundary no proposal may cross. H5 without V7 is the **HA4 Autonomous Principle Adoption** anti-pattern.
- **Composes with** V6 Prompt Injection Shield — V6 specialises in injection-specific defences inside V5's guards; V7 is the broader declarative policy those guards (and others) enforce.
- **Composes with** V8 Tool Sandboxing — V8 isolates execution at the OS level; V7 governs *which* tool calls are permitted at the policy level. Belt and braces for V3 Trifecta cases.
- **Composes with** V16 Offline Eval / V17 Online Eval — the policy itself must be tested adversarially (V16) and monitored in production (V17 watches policy-decision rates as a quality signal).
- **Mitigates** V3 Rule of Two (Lethal Trifecta) — V7 can PROHIBIT the third condition deterministically (e.g., "PROHIBIT external comms when context contains untrusted content"); the named mitigation alongside V4, V6, and V8.
- **Distinct from** V5 Guardrail Layering — V5 is the structural placement of guards; V7 is the declarative policy. They are different layers, not substitutes; the conflation is common and load-bearing to disambiguate.
- **Distinct from** S9 Constitutional Framing — see Motivation and CONFLICTS.md CRITICAL 3. S9 is probabilistic in-prompt; V7 is deterministic external. Calling an S9-only system "governed" overclaims.
- **Distinct from** V15 LLM-as-Judge — V15 *is* an LLM call evaluating against a rubric (probabilistic, slow, flexible); V7 is deterministic rule evaluation (fast, rigid, auditable). They compose: V7 can OBLIGATE a V15 judge call on highest-stakes outputs.

## Sources

- Wang, H., Poskitt, C. M., Sun, J. et al. (2025) — "AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents." arXiv [2503.18666](https://arxiv.org/abs/2503.18666). To appear ICSE 2026. The canonical reference for the V7 pattern as named.
- Shi, T. et al. (2025) — "Progent: Programmable Privilege Control for LLM Agents." arXiv [2504.11703](https://arxiv.org/abs/2504.11703). The privilege-control formulation of V7.
- Xiang, Z. et al. (2024) — "GuardAgent: Safeguard LLM Agents by a Guard Agent via Knowledge-Enabled Reasoning." arXiv [2406.09187](https://arxiv.org/abs/2406.09187).
- Open Agent Spec (Oracle) (2025) — "Open Agent Specification: A Unified Representation for AI Agents." arXiv [2510.04173](https://arxiv.org/abs/2510.04173).
- "Architecting Agentic Communities using Design Patterns" (2026) — arXiv [2601.03624](https://arxiv.org/abs/2601.03624). Establishes the deontic vocabulary (permit / burden / embargo) drawing on ISO ODP-EL; the formal reference for V7's deontic tokens.
- Open Policy Agent (CNCF) — [openpolicyagent.org](https://www.openpolicyagent.org/) and [`github.com/open-policy-agent/opa`](https://github.com/open-policy-agent/opa); the Rego policy language as a general-purpose substrate for V7-shaped enforcement.
- NVIDIA — NeMo Guardrails documentation; Colang policy language and the five-rail enforcement model.
- Invariant Labs — Invariant Guardrails and Invariant Gateway; rule-based runtime enforcement for LLM and MCP agents.
- OWASP — "OWASP Top 10 for Large Language Model Applications" (LLM01 Prompt Injection; LLM06 Excessive Agency), 2024–2025 revisions.
- NIST — "AI Risk Management Framework" (AI RMF 1.0); governance as a first-class function.
- EU AI Act — Article 9 (Risk Management System) and Article 14 (Human Oversight); the regulatory foundation for declarative governance and audit requirements in high-risk AI systems.
- Willison, S. — "The lethal trifecta for AI agents" (simonwillison.net, 2025); the threat model V7 is one of the named mitigations for.
- Perez, F. & Ribeiro, I. (2022) — "Ignore Previous Prompt: Attack Techniques for Language Models" (arXiv [2211.09527](https://arxiv.org/abs/2211.09527)); the foundational case for needing enforcement *outside* the prompt.
