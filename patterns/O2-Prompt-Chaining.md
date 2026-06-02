# O2 — Prompt Chaining

> Structure a complex task as a fixed sequence of LLM calls where the output of one call becomes the input of the next, with deterministic code — and optional gates — between the steps.

**Also Known As:** Sequential Pipeline, LLM Pipeline, Fixed Workflow, Chain Workflow. (Gated, Conditional, and Fan-out/Fan-in variants noted in Variants.)

**Classification:** Category IV — Orchestration · Band IV-A Workflow Patterns · the most deterministic multi-call orchestration — a fixed chain of LLM steps with code wiring between them, the simplest rung of the orchestration ladder above O1 Single Agent.

---

## Intent

Decompose a task into a known, ordered sequence of LLM calls with deterministic transitions between them, so each step has its own focused setup and can be independently tested, logged, and gated — and so the whole pipeline is predictable in cost and behaviour.

## Motivation

Many real tasks decompose naturally into a fixed order of operations: *extract entities → validate them → look them up → format the response*; *outline → draft → edit → format*; *parse intent → resolve references → generate answer → polish*. The naive way to solve such a task is one big prompt that asks the model to do all four moves at once — anti-pattern **A1 God Prompt**. The model collapses the moves, produces a soft best-effort, and silently drops requirements. **S4 Instruction Decomposition** is the prompt-level fix: number the steps inside one call. S4 works until you need any of *inspection between steps*, *different models per step*, *a quality gate that can abort the chain*, or *logging of intermediate state*. The moment you need a boundary, S4 cannot reach it: every step lives inside one model turn.

Prompt Chaining is the next rung. Each step is its own LLM call with its own setup; the deterministic code between calls is a first-class participant — it transforms, validates, gates, branches, or logs the state that flows from step to step. The chain is **fixed at design time**: the developer writes the sequence; the model does not choose it. That fixedness is the source of all of O2's virtues — predictability, testability, isolated debugging, cheap caching — and all of its limits. When the right sequence of steps depends on the input and cannot be enumerated in advance, the right pattern is no longer O2; it is **O6 Orchestrator-Workers**, where a planner LLM picks the steps at runtime.

The defining claim of O2 is **separation of responsibility across calls**. One step extracts; another step formats; a gate between them checks. Each call has a small, testable contract. Failures localise to a step and to its gate. This is the most deterministic multi-call orchestration pattern there is — and where the task fits, it is the right one. The cost is sequential latency (steps accumulate) and error propagation through the chain if a step's output is bad and no gate catches it.

## Variants

Variants differ in *what code does between steps*:

- **Gated chaining.** A deterministic validator (or an **R20 Chain-of-Verification** check, or a small LLM judge — **V15 LLM-as-Judge**) sits between two steps and can abort, retry, or route the chain on failure. The default for any production chain where step N's output cannot be trusted blindly.
- **Conditional chaining.** A code branch after a step selects which next step to run (a degenerate **O3 Routing** mid-chain). Used when the chain has a small fixed set of forks; if the branching is more than ~2 levels deep, the task probably needs O3 or O6 instead.
- **Fan-out / Fan-in chaining.** A step produces a list; subsequent steps run in parallel over the list (**O4 Parallelization** inside O2); an aggregator step joins. The most common production-grade O2 shape — almost any non-trivial chain has at least one parallel section.

All three are the same pattern — *a fixed chain of LLM calls with deterministic code between them* — differing only in what that code does (validate, branch, or fan out). They compose freely.

## Applicability

Use Prompt Chaining when:

- the sequence of LLM steps is known at design time and does not depend on the input;
- the chain is short enough (~2–7 steps) to be wired by hand and reasoned about end-to-end;
- at least one boundary between steps needs to do real work — inspection, validation, gating, logging, parallel fan-out, or different model settings per step;
- predictable cost, predictable latency, and step-level isolation matter (the failure mode of a single step does not propagate silently);
- each step's output is a structured, well-defined hand-off into the next step's input.

Do not use Prompt Chaining when:

- the whole task fits in one prompt and no inter-step inspection is needed — use **S4 Instruction Decomposition** (cheaper, single call);
- the step sequence depends on the input at runtime — use **O6 Orchestrator-Workers** (a planner picks the steps);
- steps are independent and can run in parallel with no ordering — use **O4 Parallelization** directly;
- steps need to be interleaved with tool calls and observations the model decides on — use **R4 ReAct**;
- the task is a classification dispatch into specialised handlers — use **O3 Routing**;
- you need iterative refinement against an evaluator — use **O5 Evaluator-Optimizer**.

## Decision Criteria

O2 is right when the chain is fixed, short, and at least one boundary between steps needs deterministic code.

**1. Enumerate the steps at design time.** Can you list every step the chain will run without seeing the input? If yes — O2. If the step list depends on the input — **O6 Orchestrator-Workers**. The boundary test: would a different input produce a different sequence of steps? Different *values* in the same steps → still O2; different *steps entirely* → O6.

**2. Count the steps.** O2 scales cleanly to ~2–7 LLM calls. Below 2, the chain is just S4 or O1. Above 7, the chain becomes a maintenance burden and should split into sub-chains, hierarchise into **O7 Supervisor Hierarchy**, or be rebuilt as O6. A chain of 3–5 steps is the sweet spot.

**3. Find the boundary work.** What does the code *between* steps actually do? List every transformation, validator, gate, branch, fan-out, or log between steps. If the answer is *nothing — each step just passes its output to the next* — you do not need O2; an **S4** single-prompt step list is cheaper. O2 earns its keep when at least one boundary does real work.

**4. Budget the sequential latency.** Each step is at minimum one network round-trip plus generation time. A 5-step chain on a 2-second-per-step model is a 10-second user wait. Tolerable for batch / offline; often too slow for interactive. If latency budget is tight, look for steps that can be parallelised (**O4** sections inside O2), or compress small sequential steps into one call with **S4**. Each step starts a fresh prefill computation. For a stable system prompt, prefix caching (mechanism 5) amortises most of that cost, because each step's setup is a stable prefix that the provider can serve at ~10% of normal input cost after the first run. The KV cache is per-session and does not carry across calls (mechanism 3), so each step starts a new session and pays its own prefill — but that prefill is cheap on cache hit. The sequential latency is therefore: sum of (cache miss prefill on round 1 + ~10% cache hit cost on subsequent runs + generation time per step). The chain's latency is dominated by generation time, not prefill, after the first run. (Mechanisms 3, 5.)

**5. Plan the gates.** For each inter-step boundary, name the failure mode that gate prevents. A chain with no inter-step validation is *just as fragile as A1 God Prompt* — errors propagate through to the final step and look like the final step's fault. At minimum: one structural validation (schema parse) and one semantic gate (R20 Chain-of-Verification, or V15 LLM-as-Judge) at the highest-leverage boundary.

**Quick test — O2 is the right pattern when:**

- the step sequence is known at design time and does not depend on the input, *and*
- the chain is ~2–7 LLM calls long, *and*
- at least one inter-step boundary does real work (gate, validator, fan-out, branch, log), *and*
- the latency budget tolerates sequential calls.

If the step list depends on the input, choose **O6 Orchestrator-Workers**. If steps are independent and unordered, choose **O4 Parallelization**. If steps need tools mid-sequence chosen by the model, choose **R4 ReAct**. If the whole sequence fits one prompt with no boundary work, drop down to **S4 Instruction Decomposition** — single call, same idea.

## Structure

```
  input
    │
    ▼
  ┌────────────────┐
  │  Step 1 (LLM)  │   configured session — own setup, own model, own prompt
  └───────┬────────┘
          │ output_1
          ▼
   [ code: validate / transform / gate ]    ← inter-step boundary
          │
          ▼
  ┌────────────────┐
  │  Step 2 (LLM)  │
  └───────┬────────┘
          │ output_2
          ▼
   [ code: validate / branch / fan-out ]
          │
          ▼
         ...
          │
          ▼
  ┌────────────────┐
  │  Step N (LLM)  │
  └───────┬────────┘
          │
          ▼
        final output
```

Each `Step` box is its own LLM session — distinct setup, possibly distinct model. Each `[ code ]` block is deterministic wiring the developer owns: at minimum a schema parse, often a validator or gate, sometimes a branch or a parallel fan-out.

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Chain Definition** | the fixed ordered list of steps and the wiring between them | task analysis → declarative chain (steps + gates + branches) | be data-dependent — if the chain depends on the input, this is **O6**, not O2. The chain is committed at design time. |
| **Step Session** *(one per LLM step)* | producing this step's output to its declared contract | step's input → step's structured output | reach across steps — a Step Session sees only its declared input, never the chain's whole state or another step's internals. |
| **State Carrier** | passing the typed payload between steps | step N's output → step N+1's input (often a typed dict or object) | be a free-form blob — vague state is the most common O2 failure. A schema per inter-step boundary is mandatory. |
| **Inter-step Gate** *(per boundary that needs one)* | the verdict on whether step N's output is fit to be step N+1's input | output_N → pass / fail / retry / abort | be silent on failure — a failed gate must surface the failure with the offending payload, not paper over it. |
| **Validator / Transformer** *(per boundary)* | schema parse, type coerce, field rename | raw step output → typed payload for next step | mutate the *meaning* of the data — coercion is structural; semantic changes belong inside a Step. |
| **Branch / Fan-out** *(optional)* | choosing the next step or splitting the chain | gate verdict or output_N → next-step selector or per-item subchain | be a deep decision tree — anything beyond ~2 forks should be **O3 Routing** or **O6**. |
| **Orchestrator (code)** | running the chain — invoke step, pass state, run gates, branch | chain definition + input → final output | be an LLM. The whole point of O2 is that the *orchestration* is code; an LLM picking the next step makes this O6. |

Seven roles, but most chains in practice use four: Chain Definition, Step Sessions, State Carrier, and a code Orchestrator. Gates, Validators, and Branches are the per-boundary participants that earn O2 its reliability margin over S4.

## Collaborations

The Orchestrator (plain code) reads the Chain Definition and runs the steps in order. For each step, it picks the typed slice of state the Step Session needs, invokes that session's LLM call with its loaded setup and per-call prompt, and receives the step's output. A Validator parses the output against its schema — a structural check, code-only. If a boundary has an Inter-step Gate, the gate runs next: a small LLM call (or rule) that grades the output and emits pass / fail / retry / abort. On *pass*, the Orchestrator updates the State Carrier and moves to the next step. On *retry*, the Orchestrator re-invokes the previous step with a feedback signal (bounded by **V9 Bounded Execution**). On *fail*, the chain aborts and surfaces the failure with the offending payload. On a *fan-out* boundary, the Orchestrator splits the state into sub-states and runs the subsequent step in parallel (**O4**) over each, then runs an aggregator step to join. The final step's output is returned. **V14 Trajectory Logging** records every step's input, output, gate verdict, and timing — that log is the chain's debugging substrate.

## Consequences

**Benefits**
- Predictable cost and latency — a fixed chain has a fixed bill and a fixed wall-clock.
- Step-level isolation — each step has its own setup, prompt, and contract; failures localise.
- Cheap testing — each Step Session is a unit; its input and expected output are both typed.
- Cheap debugging — V14's trajectory log shows exactly which step failed and on what input.
- Per-step model choice — small fast models for cheap steps, the strongest model only where it matters.
- Per-step prompt caching — each step's setup caches independently; the chain pays prefill once per step, not once per chain. Prefix caching works because each step's setup (system prompt + task framing) is a stable prefix (mechanism 5). Anthropic's cache hits cost ~10% of normal input token cost with a 5-minute TTL; a chain that runs 1000 times pays prefill only once per TTL interval per step. Critically, each step's KV cache is independent — step 3 does not carry step 1's retrieved documents in its attention computation (mechanism 3). The n² cost of attention is paid over seq_len_per_step, not seq_len_over_all_steps, which is the primary latency win vs a single O1 call that accumulates the whole trajectory (mechanism 2). (Mechanisms 2, 3, 5.)
- Composability — O4 fan-outs and O3 conditional forks slot in without rewriting the chain.

**Costs**
- Sequential latency accumulates — N steps mean N round-trips minimum.
- More wiring — every chain is bespoke code, not a single prompt.
- Each step needs its own prompt artifact, its own setup, its own contract — N times the prompt-authoring work.
- State-carrier discipline — the typed payload at each boundary needs design and maintenance.
- Fixed structure cannot adapt — if a runtime input demands a different sequence, the chain is wrong and the right answer is O6.

**Risks and failure modes**
- *Garbage-in propagation* — step N produces a malformed output, no gate catches it, step N+1 fails confusingly or, worse, silently produces a plausible-looking wrong answer. Mitigated by per-boundary schema validation and at least one semantic gate.
- *Boundary mismatch* — step N's output schema and step N+1's input schema drift apart over time as prompts evolve. Mitigated by typed State Carrier and contract tests.
- *Step fusion temptation* — the prompt author is tempted to do two steps' work in one to save a call. This regresses O2 to S4 and loses every boundary's gate. If a step is small enough to fuse, it should not be a step.
- *Hidden coupling* — step 5 secretly depends on a field step 2 emitted that step 3 dropped. Defeated by treating the State Carrier as the only inter-step interface.
- *Chain rot* — over time the chain accretes steps as each new requirement bolts on another step. Periodic refactors are required; if the chain has grown past ~7 steps, restructure.
- *No-op chain* — every step just passes its output to the next with no boundary work. The chain should not exist; collapse it to **S4**.

## Implementation Notes

- Define a **typed State Carrier** (Pydantic, dataclass, JSON Schema) for the payload between every pair of steps. Most O2 production bugs are state-carrier bugs.
- Pair every step with an **S6 Output Template** so its output is parseable. Steps that emit free prose are not chainable.
- At minimum one **R20 Chain-of-Verification** or **V15 LLM-as-Judge** gate, at the highest-leverage boundary (usually just before the final generation step or just before any externally visible action).
- Use **V14 Trajectory Logging** from day one — the per-step trace is the chain's only debugging surface. The cost is trivial; without it, you are debugging blind.
- Use **V9 Bounded Execution** for any retry-on-failure boundary. Without a cap, a hard input cascades retries indefinitely.
- Per-step model selection is a major lever — most steps are happy with a small fast model; only the steps that actually need it should use the system's strongest model.
- Prompt caching benefits compound when each step's setup is reused across many runs of the chain. Lay each step's setup out so the prefix is stable.
- Fan-out sections (**O4** inside O2) should be the default for any step that operates over a list — sequential iteration of an LLM call over a list is almost always a mistake.
- If the chain naturally has more than ~7 steps, prefer hierarchical decomposition (one O2 chain calls another) over one long flat chain.
- **A1 vs O2 vs O6** — three rungs on the same ladder. Re-evaluate which rung the task is on whenever a chain grows past 5 steps or starts to branch deeply.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** O2 chains 2–7 Step Sessions with deterministic code between them. It commonly composes with **O4 Parallelization** (fan-out sections inside the chain), **O3 Routing** (a conditional branch mid-chain), **V15 LLM-as-Judge** or **R20 Chain-of-Verification** (the inter-step gate), **V9 Bounded Execution** (retry caps), **V14 Trajectory Logging** (the per-step trace), and **S6 Output Template** (each step's output contract). Where one step is itself a small ordered procedure, that step is internally **S4 Instruction Decomposition**.

**The chain — illustrative 4-step example (extract → validate → enrich → format):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Extract entities from raw input | `LLM` | Extractor session |
| 2 | Parse to typed payload; abort if malformed | `code` | S6 schema |
| 3 | Validate entities against business rules (gate) | `LLM (or rule)` | Validator session, V15 |
| 4 | Branch — invalid → abort with reason; valid → continue | `code` | |
| 5 | Enrich each entity in parallel via lookup | `LLM` | Enricher session (O4 fan-out) |
| 6 | Aggregate enriched entities | `code` | |
| 7 | Format final response to user-facing contract | `LLM` | Formatter session |
| 8 | Parse final output against output schema | `code` | S6 schema |

**Skeleton** — the wiring is the engineering; each `# LLM` line is a configured session:

```
prompt_chain(input):
    log.start_trace()                                  # code — V14

    raw_entities = Extractor(input) ──────────────────── # LLM
    entities = parse_schema(raw_entities)              # code — S6, abort on parse fail

    verdict = Validator(entities) ────────────────────── # LLM (or rule) — V15 gate
    if verdict == FAIL:                                # code — branch
        return abort(verdict.reason)

    enriched = parallel_map(                           # code — O4 fan-out
        lambda e: Enricher(e),                         # LLM (per item)
        entities,
    )
    aggregated = aggregate(enriched)                   # code

    response = Formatter(input, aggregated) ──────────── # LLM
    return parse_schema(response)                      # code — S6
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Extractor** | small fast generalist; extraction is structural, not creative | role (*"you extract entities of the following types from raw text"*); the entity schema (**S6**); few-shot examples (**S2**) demonstrating the extraction; output contract (JSON matching the schema, nothing else) | the raw input text |
| **Validator** *(or rule)* | small fast generalist, optionally a fine-tuned classifier; or a code rule when the rules are deterministic | role (*"you check whether an extracted entity satisfies the following rules"*); the rule list (**S5**); output contract (PASS / FAIL + reason) | one entity (or the entity set) |
| **Enricher** | small fast generalist; per-item, runs in parallel | role (*"given an entity, produce its enrichment fields"*); the enrichment schema (**S6**); the lookup context if needed | one entity at a time |
| **Formatter** | the system's main generalist — this is the user-facing output | role (**S3**); the user-facing format contract (**S6**); tone / persona / constraints (**S5**); the final answer rules | the original input + the aggregated enriched entities |

Concretely, the **Extractor** session's setup loaded once is *"You extract entities of types {schema} from user input. Reply with a single JSON object matching the schema. Emit no prose."* Per call the prompt carries only *"Input: {raw_text}"*. The other three sessions follow the same setup-once, wrap-data-per-call split. Each session caches its setup; the chain pays one prefill per step per cache lifetime, not per chain run.

**Specialist-model note.** None — capable generalists suffice for all four sessions in the illustrative chain. The pattern's lift comes from the *boundaries* between calls (typed state, gates, validators), not from any one call's model. Two structural choices change the chain's economics far more than model choice:

- **Per-step model assignment.** Cheap small models for the structural steps (Extractor, Validator); the strongest available model only on the step that actually needs it (typically the final user-facing Formatter, or wherever the chain's quality bottleneck sits). Mixing model tiers across the chain is a normal and often the best move.
- **Per-step prompt caching.** Each step's setup is its own cacheable prefix. The chain benefits dramatically when each step's setup is laid out so its prefix is stable across runs. A long-context model is almost never needed by O2 itself — long context is a *step-internal* concern (**K9**); the chain pays per step, not for the whole history.

## Open-Source Implementations

- **Anthropic Claude Cookbooks — Prompt Chaining notebook** — [`github.com/anthropics/claude-cookbooks`](https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents) — the canonical reference implementation accompanying the "Building Effective Agents" article (Schluntz & Zhang, 2024). The `patterns/agents/basic_workflows.ipynb` notebook contains the runnable prompt-chaining example.
- **Spring AI — Chain Workflow pattern** — [`github.com/spring-projects/spring-ai-examples`](https://github.com/spring-projects/spring-ai-examples/tree/main/agentic-patterns/chain-workflow) — JVM reference implementation of the Anthropic prompt-chaining pattern; clean illustration of typed state between LLM steps.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — the production-grade substrate for O2 in Python: typed state, explicit nodes, deterministic edges between LLM calls. Workflows-vs-agents docs explicitly cover prompt chaining as the canonical linear graph.
- **LangChain LCEL — RunnableSequence** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — the `|` pipe composition (`prompt | llm | parser | next_prompt | llm | ...`) is the lightest-weight O2 substrate; appropriate when no inter-step gate is needed.
- **Arize Phoenix — LangGraph prompt-chaining tutorial** — [`github.com/Arize-ai/phoenix`](https://github.com/Arize-ai/phoenix/blob/main/tutorials/agents/langgraph/langgraph_promptchaining.ipynb) — runnable notebook walking through O2 on LangGraph with observability wired in (a worked V14 + O2 composition).

## Known Uses

- **Document-processing pipelines** (extract → validate → format) — the canonical production O2 deployment; ubiquitous in legal, financial, and back-office automation.
- **Customer-support intake** — classify-then-extract-then-route chains running before any human or specialist agent sees the ticket.
- **Marketing and content workflows** (outline → draft → critique → edit → format) — the Anthropic cookbook's own demonstration shape.
- **Coding assistants' edit pipelines** — many production coding agents implement file-edit flows as O2 chains (locate → propose edit → validate → apply) before falling back to **R4 ReAct** loops only when the chain cannot complete.
- **RAG question-answering** — retrieve → re-rank → answer → cite is a prompt chain (often with a gate before the final answer step) wrapping inner **K1**–**K5** retrieval patterns.
- **Compliance / KYC workflows** — multi-step verification chains where each step is independently auditable; the gate-able boundary structure is the regulatory selling point.

## Related Patterns

- **Upgrades from** **S4 Instruction Decomposition** — S4 puts an ordered step list inside *one* LLM call; O2 distributes the same step list across *multiple* calls so each step gets its own setup, model, and gate. The S4↔O2 boundary is the prompt-vs-agent scope question made explicit: pick S4 when boundaries are not needed; pick O2 when at least one boundary does real work.
- **Upgrades to** **O6 Orchestrator-Workers** — O2 is fixed at design time; O6 is dynamic at runtime. Use O2 when the step sequence is enumerable up front; use O6 when a planner LLM must pick the steps based on the input. The decision boundary: *"can I enumerate all steps without seeing the input?"* — yes → O2; no → O6.
- **Cousin at agent scope of** **R3 Plan-and-Solve** — R3 is the *planning-then-execution* shape: a Planner LLM produces the step list, an Executor (or chain) runs it. R3's *execution* phase, when the produced plan is followed verbatim, is mechanically an O2 chain. The two patterns diverge at where the chain comes from: R3 generates it; O2 authors it.
- **Composes with** **O4 Parallelization** — almost every non-trivial O2 chain has at least one fan-out section where a step runs in parallel over a list. O4 inside O2 is the default production shape.
- **Composes with** **O3 Routing** — a conditional branch mid-chain is a degenerate O3 step; for more than ~2 forks, lift the routing out to a proper O3 stage.
- **Composes with** **V15 LLM-as-Judge** and **R20 Chain-of-Verification** — the inter-step gate is implemented by one of these.
- **Required by** **V9 Bounded Execution** — any chain with a retry-on-failure boundary needs a hard cap, or a hard input cascades retries.
- **Pairs with** **V14 Trajectory Logging** — the per-step trace is the chain's debugging substrate; V14 is mandatory infrastructure in production O2.
- **Pairs with** **S6 Output Template** — every step's output is the next step's input; each boundary needs a schema, and S6 is how the prompt enforces it.
- **Distinct from** **R4 ReAct** — R4 interleaves reason / act / observe inside one agent's control loop; O2 is a fixed external sequence of LLM calls. R4 chooses what to do next; O2 does not.
- **Distinct from** **O5 Evaluator-Optimizer** — O5 is a *loop* (generator ↔ evaluator until pass); O2 is a *line* (step 1 → step 2 → … → step N). An O5 loop may sit inside one stage of an O2 chain.

## Sources

- Schluntz, E. & Zhang, B. (2024) — "Building Effective Agents." Anthropic engineering blog. The canonical articulation of Prompt Chaining as one of five workflow patterns; foundational reference for this pattern.
- Anthropic — "Chain complex prompts." Claude prompt-engineering documentation. Distinguishes single-prompt step decomposition (S4) from multi-call chaining (O2).
- Spring AI — *Building Effective Agents with Spring AI* (Pollack, 2025). Spring AI Reference; documents the Chain Workflow pattern with a runnable JVM implementation.
- LangChain — "Workflows and agents" documentation (LangGraph). Treats prompt chaining as the canonical workflow shape: linear typed graph of LLM nodes with deterministic edges.
- AWS Prescriptive Guidance — *Agentic AI Patterns*. Sequential workflow / pipeline as the foundational workflow pattern.
- Azure / Microsoft Agent Framework — sequential orchestration patterns documentation.
- arXiv 2604.03515 — *Inside the Scaffold* (2025). Empirical study of production coding agents; documents that linear chains are the substrate underneath most observed scaffolds before they specialise.
- White, J., Fu, Q., Hays, S., et al. (2023) — "A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT." Names the prompt-level antecedent (Recipe Pattern) that O2 generalises across calls.
