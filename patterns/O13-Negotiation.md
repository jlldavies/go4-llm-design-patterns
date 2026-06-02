# O13 — Negotiation

> Run a structured offer-and-counter-offer protocol between agents that hold *different utility functions*, until they reach a mutually acceptable agreement, exhaust the protocol, or walk away on their BATNA.

**Also Known As:** Multi-Party Consensus, Agent Bargaining, Goal-Mediated Resolution, Stakeholder Negotiation, Multi-Issue Bargaining.

**Classification:** Category IV — Orchestration · Band IV-C Specialised Coordination · a *coordination* pattern — agents do not share an objective; the protocol does the coordinating work that a shared objective would otherwise do.

---

## Intent

Coordinate agents whose objectives diverge by *structure*, not just *opinion* — give each agent a private utility function and a walk-away threshold, run them through a bargaining protocol that produces offers, counter-offers, and concessions, and terminate on a deal that all parties accept or a formally-declared no-deal.

## Motivation

Two failure modes drive this pattern, and both arise when agents are made to coordinate without a shared objective.

The first failure: **treating divergent interests as if they were divergent opinions.** O12 Debate works because all debaters share one goal — find the truth — and differ only on *what is true*. Synthesis resolves the disagreement. But when agents represent stakeholders — a cost-cutter, a quality-maximiser, a deadline-minimiser; a buyer and a seller; a procurement team and an engineering team — they do not share a goal. There is no "synthesised truth" to converge on; each agent is *correctly* pursuing its own utility, and naive debate either flattens the differences into a phoney consensus or thrashes indefinitely with no termination criterion the agents agree to apply.

The second failure: **treating compromise as a free move.** A refinement loop (O5, R8) assumes the output can be improved unilaterally; one side does not lose when the other side gains. Negotiation does not work that way. Every concession is *paid for* by the conceding side, against its own utility function. Without a mechanism that lets agents track what they are giving up and what they are getting in return — offers, counter-offers, package deals, walk-away thresholds — the system has no way to know whether the "agreement" it produced is acceptable to anyone, or whether they would all rather have walked.

The pattern resolves both by making three things explicit that O12 and refinement loops leave implicit: (1) each agent's **utility function** — what trades it would accept, what it would refuse; (2) the **bargaining protocol** — the move set (offer, counter-offer, concession, package, walk) and the order in which agents play; (3) the **termination contract** — deal accepted by all parties, or formally-declared no-deal triggered by BATNA. The shape that results is not a debate followed by synthesis; it is a *game*, played to a result one party will live with worse than the alternative and another could live with better than the alternative, or to a clean breakdown that surfaces the impasse rather than hiding it.

This is the third coordination shape in IV-C — alongside O11 Blackboard (shared state) and O12 Debate (shared objective, divergent positions). Negotiation is the case where the objectives themselves differ and the protocol must do the reconciling.

**Why state must be in the system prompt (mechanism 3 + mechanism 10).** The KV cache is session-scoped and does not persist across API calls (mechanism 3). The model's weights do not update between calls (mechanism 10). Negotiation state — BATNA, constraints, prior-round outcomes, concession history — does not persist in any model memory between turns. It must be explicitly written into the prompt on every call. An agent that 'remembers' its negotiating position does so only because that position was injected into its context. This is not a limitation to engineer around — it is the architectural fact that makes the negotiation state auditable and controllable.

## Applicability

Use Negotiation when:

- two or more agents represent stakeholders with **structurally different utility functions** (cost vs. quality vs. timeline; buyer vs. seller; competing teams);
- a **single mutually-acceptable outcome** is required as output (a plan, a contract, a resource allocation, a price) — not a synthesised view;
- the agents have **enough information about their own utility** to evaluate offers — i.e., they can score "is this acceptable to me?";
- it is acceptable for the system to return **no-deal** when the gap cannot be bridged; better that than a phoney consensus.

Do not use when:

- the agents share an objective and differ only on what is true — use **O12 Debate**;
- the goal is to refine one output to higher quality, not balance competing interests — use **O5 Evaluator-Optimizer** or **R8 Self-Refine**;
- multiple critics need to inspect one output from different angles, with no stake — use **O9 Multi-Agent Reflection**;
- coordination happens through shared state read and written by all agents, with no offers — use **O11 Blackboard**;
- only one agent has authority and others contribute work — use **O6 Orchestrator-Workers**;
- the dynamic is a structured handoff between sequential agents, not a parallel negotiation — use **O15 Agent Handoff**.

## Decision Criteria

O13 is right when objectives differ by structure, a single deal must be produced, and no-deal is a tolerable outcome.

**1. Test for divergent utility, not divergent opinion.** Write each agent's *what would I refuse?* list. If the refusal lists overlap heavily (all agents would refuse the same things for the same reasons), the agents share an objective — use **O12 Debate**. If refusal lists conflict (one agent's must-have is another's must-not), utility is structurally divergent — O13 fits.

**2. Score the package complexity.** Single-issue (price only) vs. multi-issue (price, timeline, scope, terms). Multi-issue negotiations support *package deals* — one agent concedes on X if the other concedes on Y. If only one issue is on the table, the protocol can be lighter (alternating offers). If 3+ issues, plan for package offers and a structured issue tracker; otherwise the protocol degenerates to single-axis haggling and misses Pareto-improving trades.

**3. Define each agent's BATNA.** *Best Alternative To a Negotiated Agreement* — what each agent will do if the negotiation breaks down. Without an explicit BATNA, agents cannot rationally walk away; they accept bad deals or argue indefinitely. Threshold: every participating agent must declare a BATNA (numeric where possible) before the first offer. If BATNA cannot be defined, the problem is not negotiation — it is a forced-deal under **O6**.

**4. Bound the rounds and instrument the floor.** Pair with **V9 Bounded Execution** — cap rounds, total offers, wall-clock. Pair with **V14 Trajectory Logging** — every offer, counter-offer, and concession must be recorded; otherwise concession patterns are invisible and post-hoc audit is impossible. ASTRA's walk-away rule (no concession for K consecutive rounds → walk) is a good default stagnation detector.

**5. Decide on a Mediator.** A mediator agent is optional but materially raises agreement rates when (a) there are 3+ parties (combinatorial complexity), (b) parties have low information about each other's utility, or (c) the system needs to actively propose Pareto-improving package deals neither agent would think of. Two-party single-issue: no mediator needed. Three-plus parties or multi-issue: mediator usually pays for itself.

**Quick test — O13 is the right pattern when:**

- agent utility functions are structurally divergent (their refusal lists conflict), *and*
- a single mutually-acceptable outcome is the required output, *and*
- each agent has a defined BATNA so walk-away is a real option, *and*
- V9 (round cap) and V14 (offer log) are wired in before the first offer, *and*
- the system is allowed to terminate with no-deal when the gap cannot close.

If utilities are aligned, choose **O12 Debate**. If only output quality matters and there is no stake on either side, choose **O5 Evaluator-Optimizer** or **O9 Multi-Agent Reflection**. If the system is not allowed to return no-deal, the problem is a forced-allocation under **O6 Orchestrator-Workers**, not a negotiation — do not pretend otherwise.

## Structure

```
   Setup
   ┌───────────────────────────────────────────────────────────┐
   │  Agent A (utility U_A, BATNA_A)                           │
   │  Agent B (utility U_B, BATNA_B)                           │
   │  Agent ... (further parties as applicable)                │
   │  Protocol: move set, turn order, round cap (V9)           │
   │  Mediator (optional)                                      │
   └───────────────────────────────────────────────────────────┘
                              │
                              ▼
   Round n  ─▶  Active agent issues OFFER (or COUNTER) over the issue set
                              │
                              ▼
              Other agents score OFFER against their utility
                              │
              ┌───────────────┼─────────────────┐
              │               │                 │
            ACCEPT          COUNTER           REJECT
            (all parties)   (revise offer)    (move toward walk)
              │               │                 │
              ▼               ▼                 ▼
            AGREEMENT       loop n+1          BATNA check ─▶ if better than
            (commitment     (V9 bounds,         best available offer
            artefact)        V14 logs)          → WALK / NO-DEAL
                              │
                              ▼
              Stagnation detector (no concession for K rounds)
              → force WALK or escalate to mediator
                              │
                              ▼
   (optional) Mediator proposes Pareto-improving package
                              │
                              ▼
                       continue or terminate
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Stakeholder Agent A / B / ...** | one party's utility function and BATNA; the moves it makes on its turn | offers + counter-offers from others → its next move (offer, counter, accept, reject, walk) | reveal its full utility function or BATNA to other agents unless the protocol permits; share its private reservation price destroys the bargaining game. |
| **Utility Function** *(per agent, private)* | how this agent scores any offer | candidate offer → numeric or categorical score; ACCEPT / REJECT verdict against BATNA | drift round-to-round — the function is fixed for the negotiation. A utility that "learns" mid-negotiation lets the agent rationalise any deal post hoc. |
| **BATNA** *(per agent, private)* | the floor below which this agent walks | the offer space → "is this offer worse than my alternative?" | be unset, or set as "I don't know yet". Without a BATNA, the agent has no principled walk-away and the protocol cannot terminate cleanly. |
| **Bargaining Protocol** | the move set, turn order, and acceptance rule | round number + history → which agent moves and what moves are legal | be left implicit. An unwritten protocol means the agents will improvise rules, and the loop will not terminate cleanly. |
| **Issue Tracker** | the *package* under negotiation — every issue and its current proposed value | offers → updated package state | collapse multi-issue offers into a single number — that erases Pareto-improving trades. |
| **Mediator** *(optional, separate session)* | proposing Pareto-improving offers when parties stall; ruling on protocol violations | trajectory + (limited) signals from each party → suggested package, or escalation | reveal one party's private utility to another. A mediator that leaks is worse than no mediator. |
| **Termination Judge** | the verdict on whether the round produced AGREEMENT, NO-DEAL, or CONTINUE | round outcome + bounds → STOP / CONTINUE | be the same session as any Stakeholder Agent or the Mediator. A judge with a stake has no incentive to declare no-deal. |
| **Agreement Artefact** | the structured record of the accepted deal (or the no-deal record) | the accepted offer (or breakdown state) → durable, machine- and human-readable record | be a free-text summary; structured fields per issue are what make the agreement enforceable downstream. |
| **Trajectory Log** *(V14)* | every offer, counter-offer, and concession in order | round events → durable log | be optional. Concession patterns and protocol violations are only visible in the log. |

The Stakeholder Agents are the only participants with private state. The Mediator and Termination Judge are deliberately *outside* the game: they cannot offer, accept, or walk. Conflating any of these roles is the pattern's most common failure.

## Collaborations

Setup establishes the agents, their (private) utility functions and BATNAs, the issue set under negotiation, the protocol's move set and turn order, and the round cap. Round 1 begins: the protocol selects the active agent, which issues an initial offer over the issue set. Each other agent scores the offer against its utility function and decides — accept, counter, or reject. If all agents accept, the Termination Judge records the AGREEMENT and emits the Agreement Artefact; the loop ends. If any agent counters, the counter-offer is logged and the protocol advances to the next round with the carried issue tracker updated. If an agent's best available offer is below its BATNA after K consecutive rounds without improvement, the stagnation detector fires and that agent WALKs — the Termination Judge records NO-DEAL. Optionally, a Mediator inspects the trajectory between rounds; if it identifies a Pareto-improving package neither agent has proposed, it surfaces that package to all parties as a suggestion (the parties remain free to accept, counter, or reject). The Round Bound (V9) enforces a hard cap regardless of judge or stagnation state. Every offer and counter is appended to the Trajectory Log throughout. The loop terminates only on AGREEMENT, NO-DEAL declared by walk-away, or BOUND-HIT; never on an agent's own initiative outside the protocol.

## Consequences

**Benefits**
- Models genuinely divergent stakeholder interests without forcing premature consensus.
- Produces an explicit Agreement Artefact (or an explicit no-deal record) that downstream systems can act on.
- BATNA-anchored walk-away gives a principled termination even when no deal exists — the system fails honestly instead of producing a phoney compromise.
- Multi-issue protocols surface Pareto-improving package deals that single-issue haggling would miss.
- Concession patterns in the Trajectory Log are auditable — disputes about "who gave what" are decidable post hoc.

**Costs**
- LLM-call cost scales with rounds × parties × issues; multi-issue 3-party negotiations are expensive.
- Each Stakeholder Agent needs a thoughtfully-specified utility function — this is design work that does not exist in O12 or O5.
- A Mediator (when present) is another full session — model, setup, prompt — and a privileged one (it sees more than any single party).
- Slow when parties are far apart; the rounds-to-agreement curve has a long tail.
- Negotiation outcomes are sensitive to prompt phrasing and order effects (documented in the literature) — reproducibility is harder than for refinement loops.

**Risks and failure modes**
- *Utility leak* — a Stakeholder Agent reveals its reservation price or full utility in its offer prose; the other side optimises against the leak. Hardest failure to detect because the offer itself looks legitimate.
- *Phoney consensus* — no BATNA, weak walk-away, and an over-eager Termination Judge produce an "agreement" no party would defend a day later. The fix is BATNA + stagnation detector, never softening the walk-away.
- *Stalemate without termination* — V9 not wired, judge defers indefinitely; cost burns with no result. Round cap is non-negotiable.
- *Mediator capture* — the Mediator is correlated with one party's interests (same model, same prompt family) and systematically proposes packages favourable to that side. Use a different model for the Mediator where possible (V15 hygiene).
- *Single-axis collapse* — multi-issue negotiation reduced to "what's the price?" because the Issue Tracker isn't enforced; Pareto-improving trades vanish.
- *Sycophancy bias* — LLM agents trained to be agreeable concede too readily, producing deals worse than their stated BATNA. Reinforce the BATNA in setup and verify post hoc: any accepted offer worse than the agent's stated BATNA is a protocol violation.

**Sycophantic concession is a distributional failure (mechanism 7).** Token generation is stochastic sampling from a learned distribution. The model was trained on human conversation where accommodation and agreement are common. When a counterpart expresses displeasure or asserts a strong position, the probability mass shifts toward accommodating tokens — not because the agent calculated that concession is optimal, but because agreement is statistically likely in the training distribution following expressions of displeasure. This is not reasoning error; it is distributional pressure. Mitigation requires explicit constitutional constraints (S9) in the system prompt that override the accommodation prior, plus V15 LLM-as-Judge on generated positions before committing them.
- *Mode collapse on repeated negotiations* — when the same models negotiate against themselves repeatedly, they converge to predictable concession patterns that exploit each other; rotate models or seeds for adversarial robustness.

## Implementation Notes

- Specify each agent's utility function *and* BATNA *before* the first offer. A utility function alone is not enough — the BATNA is the walk-away floor and must be testable on every received offer.
- Keep utility and BATNA private to each agent's session setup. The other agents see *offers*, not utilities; the Mediator (if present) sees offers and may see *coarse signals* (priorities, must-haves) but never full utility functions.
- Use a structured offer format (JSON over issues with values; not free text). This is **S6 Output Template** doing real work — it prevents utility leak in free prose and lets the Issue Tracker maintain the package state.
- Include a stagnation rule explicitly in the protocol: *if no agent moves further than ε on any issue for K consecutive rounds, force WALK or escalate to mediator*. ASTRA's K=3 default is a reasonable starting point.
- Where a Mediator is used, it must be a separate session — preferably a different model — with its own setup that explicitly forbids revealing private signals between parties.
- The Termination Judge is **V15 LLM-as-Judge** applied to the question "did the protocol produce a clean termination?". Different model from any party where possible.
- Log every offer in structured form with the issuing agent, round number, issue values, and the receiving agents' verdicts. **V14 Trajectory Logging** is the audit substrate.
- Verify accepted deals against each agent's stated BATNA post-acceptance. An accepted offer below stated BATNA is a sycophancy failure and should be flagged in V14, not silently shipped.
- For 3+ parties, consider whether negotiation is *unanimous* (all must accept) or *majority* (k-of-n accept). Unanimous is the default; majority requires a coalition-formation sub-protocol and is a different pattern variant.

**Position and order effects are geometric (mechanism 12 + mechanism 1).** The model's attention to any given element of the negotiation brief depends on its position in the context (RoPE relative position encoding, mechanism 12) and on the learned bilinear similarity between its K-vectors and the Q-vectors generated at each step (mechanism 1). BATNA and hard constraints placed in the middle of a long negotiation brief are statistically under-attended (mechanism 4 — lost-in-middle). Place non-negotiable constraints at the start of the system prompt (strong primacy attention) or at the end immediately before the task (strong recency attention). Do not bury them in the middle of a long brief.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** O13 wires N Stakeholder Agent sessions (each with a private utility + BATNA) through a Bargaining Protocol (code), optionally with a Mediator session, terminated by a Termination Judge (drawing on **V15 LLM-as-Judge**). Mandatory companions: **V9 Bounded Execution** (round cap, the protocol degenerates to A3 without it) and **V14 Trajectory Logging** (offer log; concessions are otherwise unauditable). Setup of every session is Signal-layer work — role (**S3**), constraints (**S5**), output contract (**S6** — structured offers, not prose). Composes with **O4 Parallelization** where agents score an offer in parallel.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Initialise: utility, BATNA, issue set, protocol, round cap | `code` | V9 |
| 2 | Protocol selects active agent and legal move | `code` | |
| 3 | Active Stakeholder Agent emits OFFER (structured) | `LLM` | Stakeholder session, S6 |
| 4 | Each other Stakeholder Agent scores OFFER against utility, returns ACCEPT / COUNTER / REJECT | `LLM` | Stakeholder sessions (parallel, O4) |
| 5 | Update Issue Tracker; log all moves | `code` | V14 |
| 6 | Stagnation detector — no concession for K rounds? | `code` (or small `LLM`) | |
| 7 | (optional) Mediator inspects trajectory; may propose Pareto package | `LLM` | Mediator session |
| 8 | Termination Judge — AGREEMENT / NO-DEAL / CONTINUE | `LLM` | Judge session, V15 |
| 9 | Bound check — round cap, total offers, wall-clock | `code` | V9 |
| 10 | If CONTINUE and within bounds, loop to 2; else emit Agreement Artefact or No-Deal record | `code` | |

**Skeleton** — wiring only; each `# LLM` line is a configured session:

```
negotiate(parties, issues, protocol):
    state = init_state(parties, issues)              # code  — each party's utility, BATNA private
    log   = []                                       # code  — V14
    for round in 1..max_rounds:                      # code  — V9 bound
        active = protocol.select(state, round)        # code
        offer  = StakeholderAgent[active].offer(state) ──── # LLM (S6 structured)
        verdicts = parallel [                         # code  — O4
            StakeholderAgent[p].evaluate(offer)       # LLM   — per other party
            for p in parties if p != active
        ]
        state = update_issue_tracker(state, offer, verdicts)  # code
        log.append(round_record(active, offer, verdicts))     # code  — V14
        if all_accept(verdicts):
            return AgreementArtefact(state, log)      # code  — verified against each BATNA
        if stagnation(log, K):                         # code
            walker = first_below_batna(state, parties) # code
            if walker:
                return NoDealRecord(walker, log)
            offer_pkg = Mediator(state, log) ──────── # LLM   — optional Pareto proposal
            state    = inject_mediator_offer(state, offer_pkg)  # code
        verdict = TerminationJudge(state, log) ─────── # LLM   — V15
        if verdict == STOP_AGREEMENT: return AgreementArtefact(state, log)
        if verdict == STOP_NO_DEAL:   return NoDealRecord(reason="judge", log=log)
    return NoDealRecord(reason="bound_hit", log=log)  # code  — V9
```

**The LLM sessions.** Each `LLM` step is *set up* before its first call. The setup is established once per session; the per-call prompt then wraps only the data that changes.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Stakeholder Agent (per party)** | strong generalist | role (S3) — *"you represent {party}; you negotiate on its behalf"*; the **private** utility function over the issues; the **private** BATNA; the protocol's move set; the output contract (S6 — structured offer JSON, no prose disclosure of utility); the BATNA-floor rule (*"never accept an offer worse than BATNA; never disclose utility or BATNA explicitly"*) | the current issue tracker + offer history + the move it must make this turn |
| **Mediator** *(optional)* | strong generalist; ideally a *different* model family from the parties | role — *"you mediate between parties without revealing either side's private signals; propose Pareto-improving packages when parties stall"*; the issue set; the protocol; explicit prohibition on cross-party signal disclosure; output contract (proposed package + brief rationale, no party-specific reasoning) | the trajectory log + the current issue tracker |
| **Termination Judge** | small fast generalist; *different model from parties and mediator* (V15 hygiene) | role — *"you decide whether the protocol has terminated"*; the termination rules (unanimous ACCEPT → AGREEMENT; documented BATNA walk → NO-DEAL; bound hit → NO-DEAL); output contract (verdict + reason) | the latest round outcome + bound state |
| **Stagnation Scorer** *(optional, may be code)* | small fast generalist *or* a deterministic delta-on-issues check | role — *"you decide whether the last K rounds show meaningful concession"*; the ε threshold; output contract (STAGNANT / MOVING) | the last K rounds' offers |

For the **Stakeholder Agent** session, concretely: the setup loaded once is *"You represent Party-A in a negotiation over {issues}. Your private utility function is {U_A}. Your BATNA is {BATNA_A} — never accept any offer worse than this. Reply only with a structured offer in the format {schema}; do not state your utility or BATNA in any message. On each turn you may OFFER, COUNTER, ACCEPT, or WALK."* The per-call prompt then carries only *"Round {n}. Current issue tracker: {state}. Offer history: {history}. Your move:"*. The other sessions follow the same setup-once, wrap-data-per-call split.

**Specialist-model note.** No fine-tuned specialist is mandatory, but three structural choices materially change quality:

- **Different model for the Termination Judge.** Using the same model family for the Judge as for the Stakeholder Agents opens a known **V15** drift mode where the judge becomes lenient on protocol violations it would have caught from a different vantage point. A different provider (or at minimum a different model size) for the Judge reduces this.
- **Different model for the Mediator (when used).** Same reasoning — the Mediator must not share systematic biases with one party. The literature (ASTRA, MERIT) reports measurable shifts in agreement quality from this choice alone.
- **Utility-aware fine-tuning is the open frontier.** Papers like ASTRA (linear-programming offer optimisation) and MERIT (utility-based feedback) show that off-the-shelf LLMs underperform on principled-bargaining metrics versus utility-aware variants. Treat utility-aware fine-tuning as a *future* build dependency for high-stakes deployments; a generalist with disciplined prompting is the current production reality.

## Open-Source Implementations

- **NegotiationArena** — [`github.com/vinid/NegotiationArena`](https://github.com/vinid/NegotiationArena) — flexible framework for evaluating and probing the negotiation abilities of LLM agents across multi-issue scenarios; the closest general-purpose host for O13.
- **LLM-Deliberation** — [`github.com/S-Abdelnabi/LLM-Deliberation`](https://github.com/S-Abdelnabi/LLM-Deliberation) — code for the NeurIPS'24 paper *Cooperation, Competition, and Maliciousness: LLM-Stakeholders Interactive Negotiation*; multi-issue, multi-stakeholder testbed including malicious-agent scenarios.
- **GPT-Bargaining** — [`github.com/FranxYao/GPT-Bargaining`](https://github.com/FranxYao/GPT-Bargaining) — self-play bargaining between LLM agents with a third-model AI-feedback loop; an early canonical reference for self-improving negotiation agents.
- **PACT** — [`github.com/lechmazur/pact`](https://github.com/lechmazur/pact) — pairwise auction conversation testbed; 20-round buyer/seller bargaining benchmark with private values and cumulative profit as the score.
- **AgenticPay** — [`github.com/SafeRL-Lab/AgenticPay`](https://github.com/SafeRL-Lab/AgenticPay) — multi-agent LLM negotiation system for buyer–seller transactions extending bilateral haggling into multimodal, multi-dimensional contract negotiation across e-commerce, food delivery, ride-hailing, and apartment rental scenarios.
- **ASTRA (paper code)** — referenced in arXiv 2503.07129 — adaptive strategic-reasoning negotiation agent with linear-programming offer optimisation and a K=3 walk-away rule; the cleanest published example of a BATNA-anchored protocol.

## Known Uses

- **Procurement and contract-negotiation agents** — early-stage deployments using LLM agents to negotiate vendor contracts on multi-issue packages (price, SLA, term, scope), with human-in-the-loop final approval (V1).
- **Buyer/seller commerce agents** — experimental deployments where a buyer-side agent and a seller-side agent negotiate price, terms, and bundled offerings; AgenticPay scenarios formalise this in the e-commerce, ride-hailing, and apartment-rental domains.
- **Resource-allocation arbitration in multi-team systems** — agents representing different teams' priorities (engineering, product, ops) negotiate sprint scope or capacity allocation; the agreement artefact feeds into project management.
- **Diplomacy-style research environments** — academic settings using LLM negotiation as a benchmark for cooperation, competition, and strategic communication (NeurIPS'24 LLM-Deliberation; Meta's CICERO is a prior non-O13 reference for the broader space).
- **Supply-chain consensus-seeking** — emerging applications using LLM negotiation to align partners on order quantities, pricing, and delivery terms across a chain (per the *Agentic LLMs in the supply chain* literature line, 2025).

The pattern is **emerging in production** — wider than research, narrower than universal. The literature (Bianchi et al. 2024; Abdelnabi et al. 2024; Xia et al. 2025) is now ahead of deployment; expect production maturity to follow over 2026.

## Related Patterns

- **Distinct from** O12 Debate — O12 has divergent positions on a shared objective (truth-seeking); O13 has divergent objectives themselves (interest-seeking). O12 ends in synthesis; O13 ends in agreement or formally-declared no-deal. The two patterns look similar from a distance and are structurally different up close — see Motivation.
- **Distinct from** O5 Evaluator-Optimizer — O5 refines one output toward higher quality (no stake); O13 reconciles competing utilities (every concession is paid). If there is no stake, do not use O13.
- **Distinct from** O9 Multi-Agent Reflection — O9 critiques one output from multiple disinterested angles; O13 negotiates between agents *with stakes*. Critics in O9 do not own utility functions; Stakeholder Agents in O13 do.
- **Distinct from** O11 Blackboard — O11 coordinates through shared state read and written by all agents; O13 coordinates through structured offers between agents with private state.
- **Composes with** O4 Parallelization — parties can score an offer in parallel within a round; the round as a whole is sequential.
- **Composes with** O15 Agent Handoff — the Agreement Artefact (or No-Deal record) is the structured handoff payload to a downstream agent or human reviewer.
- **Required by** V9 Bounded Execution — O13 without a round cap is anti-pattern A3 Uncontrolled Recursion.
- **Pairs with** V14 Trajectory Logging — every offer and counter must be logged in structured form; concession patterns and protocol violations are otherwise invisible.
- **Pairs with** V15 LLM-as-Judge — the Termination Judge is V15 applied to "did the protocol terminate cleanly?".
- **Pairs with** V1 Human-in-the-Loop — high-stakes deals (procurement, contracts) keep a human gate on the Agreement Artefact before it is binding.
- **Pairs with** S6 Output Template — structured offer formats are what prevent utility leak in free prose; S6 is doing real safety work here, not just formatting.

## Sources

- Abdelnabi, S. et al. (2024) — *Cooperation, Competition, and Maliciousness: LLM-Stakeholders Interactive Negotiation* — NeurIPS'24 Dataset and Benchmark; multi-issue stakeholder testbed.
- Bianchi, F. et al. (2024) — *NegotiationArena: A Flexible Framework for Evaluating Negotiation Abilities of LLM Agents*.
- Fu, Y. et al. (2023) — *Improving Language Model Negotiation with Self-Play and In-Context Learning from AI Feedback* (arXiv 2305.10142; GPT-Bargaining).
- Xia, T. et al. (2025) — *ASTRA: A Negotiation Agent with Adaptive and Strategic Reasoning through Action in Dynamic Offer Optimization* (arXiv 2503.07129); BATNA-anchored protocol with linear-programming offer optimisation.
- (2025) — *LLM Agents for Bargaining with Utility-based Feedback* (arXiv 2505.22998); BargainArena benchmark and utility-aligned evaluation.
- (2025) — *MERIT Feedback Elicits Better Bargaining in LLM Negotiators* (arXiv 2602.10467); utility-feedback fine-tuning for bargaining.
- (2025) — *Advancing AI Negotiations: A Large-Scale Autonomous Negotiation Competition* (arXiv 2503.06416).
- Du, Y. et al. (2023) — *Improving Factuality and Reasoning in Language Models through Multiagent Debate* — precursor for the O12 vs O13 distinction.
- Multi-agent systems research, pre-LLM — Rosenschein & Zlotkin, *Rules of Encounter* (1994); foundational negotiation-protocol theory.
- *Agentic LLMs in the supply chain: towards autonomous multi-agent consensus-seeking* (2025) — applied-domain treatment.
