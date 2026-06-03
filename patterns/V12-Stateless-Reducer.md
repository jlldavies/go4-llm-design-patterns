# V12 — Stateless Reducer

> Design the agent as a pure function of its inputs — `(state, input) → (output, state')` — with no hidden internal state, so every invocation is reproducible, retryable, parallelisable, and trivially checkpointable.

**Also Known As:** Pure Agent, Functional Agent, Agent-as-Reducer, Agent `foldl`, State-Separation Pattern, 12-Factor Agents Factor 12.

**Classification:** Category V — Reliability · Band V-B Operational Reliability · a *design constraint on the agent function itself* (not a runtime mechanism); the discipline that makes V10 Checkpointing, O4 Parallelization, and clean retry semantics possible.

---

## Intent

Force all agent state to be explicit, external, and passed in — so the agent function itself holds no hidden state between invocations and is, in the functional sense, a pure reducer over its inputs.

## Motivation

Agents acquire state by accident. A class attribute that "just caches" the last tool result; a module-level dictionary that "remembers" which sessions have been initialised; a thread-local that "knows" the current user; a memoised retriever singleton; a global counter that gates a one-time setup. Every one of these makes the agent's behaviour depend on something invisible to the caller. The same `(state_in, input)` no longer produces the same `(output, state_out)` — because the *actual* inputs include hidden state the caller cannot see, control, or replicate.

The consequences compound in production:

- **Retries become non-deterministic.** A retried call runs against subtly different hidden state and produces a different result. The first attempt's partial side effects are no longer recoverable by replay.
- **Parallelisation is unsafe.** Two concurrent invocations share the hidden state; one's mutation corrupts the other. O4 Parallelization and O6 Orchestrator-Workers cease to be safe defaults.
- **Checkpointing leaks.** V10 saves the *visible* state to the store, but the hidden state lives in the process. A restore on a fresh process disagrees with a restore in the original process — and the disagreement is silent.
- **Debugging is archaeology.** A bug that depends on hidden state cannot be reproduced from the recorded inputs alone. V14 Trajectory Logging records everything that mattered *visibly*, and the bug is still not reproducible.

The 12-Factor Agents framework names this as **Factor 12: "Make your agent a stateless reducer."** The functional-programming analogue is exact: `foldl :: (state -> input -> state) -> state -> [input] -> state`. The agent is the step function in a fold; the runtime supplies the seed state and the input stream; the output state of one call is the input state of the next. Redux reducers, Elm's update function, Haskell's `State` monad, and the 12-Factor App's stateless-process principle (Factor 6, "execute the app as one or more stateless processes") are the same move applied at different scales.

The pattern aligns with how LLM inference actually works: the model's weights do not change between invocations (mechanism 10), and the KV cache — the only in-session memory — does not persist across API calls (mechanism 3). Between calls, the agent's only memory is what was explicitly written to external storage. V12's discipline — making state explicit, serialisable, and external — is not just engineering best practice; it is the correct model of the LLM computation substrate.

V12 is not a runtime mechanism. It is a *design constraint on the agent function* — a contract the agent code must keep. The pay-off shows up everywhere else: V10 becomes trivial (there is nothing inside the agent to save), O4 becomes safe (no shared mutable state), retries become deterministic, and tests become possible (the function is fully specified by its inputs).

The pattern's defining claim is asymmetric in the same way K12 Karpathy Memory's is, but at a different layer: *one* discipline at the agent boundary buys *many* reliability properties downstream.

## Applicability

Use Stateless Reducer when:

- the agent will be checkpointed (V10), retried, replayed, or run in parallel (O4, O6);
- agent code will be deployed across multiple processes or containers (any production agent at scale);
- reproducibility from recorded inputs is a requirement (regression testing via V16, debugging from V14 traces);
- the agent participates in O15 Agent Handoff or I6 A2A Delegation — state must serialise across the boundary.

Do not bother (or treat as advisory rather than mandatory) when:

- the agent is a single-shot, sub-second call with no continuation — a chat-completion wrapper with no memory; treat **V9 Bounded Execution** as the live constraint and skip V12 as overhead;
- the "agent" is in fact a stateless transformer already (a classifier, a translator, a structured-output extractor) — V12 already holds; no work to do;
- the codebase has deeply entrenched hidden state and a refactor is genuinely off the table — install **V10 Checkpointing** with an explicit known-broken-on-restore caveat in V14, and budget the V12 refactor as a debt item rather than ignoring it.

## Decision Criteria

V12 is right when any downstream pattern depends on the agent being reproducible from its inputs alone — which, in production, is almost always.

**1. Reproducibility test.** Run the same `(state_in, input)` twice in a fresh process and diff the `(output, state_out)`. They must be byte-equal (modulo declared sources of non-determinism: LLM temperature, RNG seeds, wall-clock timestamps — all of which should themselves be inputs, not hidden). If they diverge, the agent has hidden state. No threshold here — *any* divergence on identical inputs is a V12 violation; fix before adding V10 or O4.

**2. Restart-fidelity test.** Kill the process mid-task; start a fresh process; load the last checkpoint; continue. The trajectory from that point must match what the original process would have produced. If it does not, hidden state lived in the dead process. This is the operational test V10 depends on and V12 makes pass.

**3. Parallel-safety test.** Launch two concurrent invocations against the same starting state with different inputs. Neither's outcome may depend on the other's execution order. If one's hidden mutation corrupts the other, the agent is not V12-compliant and **O4 Parallelization** is unsafe. Fix V12 before parallelising.

**4. State-shape audit.** Can the full state passed to the agent be expressed as a JSON-serialisable (or equivalent) object, with no live references — no open files, no sockets, no database connections, no in-memory caches keyed by session, no closures over module state? If not, the unserialisable piece is hidden state in disguise. Move it out of the agent into an explicit external resource the agent receives a handle to (and re-acquires per invocation, not memoises).

**5. Test reproducibility.** Can the agent be unit-tested by constructing `(state, input)` literals and asserting on `(output, state')` literals, with no fixture setup beyond constructing those literals? If tests require a `setUp` that constructs hidden state, that state belongs in the inputs. V12 makes the agent trivially testable; the test suite is the lever that exposes V12 violations early.

**Quick test — V12 is the right pattern when:**

- the agent will be checkpointed, retried, parallelised, replayed, or handed off (i.e. anything but a single-shot sub-second call), *and*
- the same `(state, input)` produces the same `(output, state')` across processes and across time, *and*
- the agent's full state is serialisable (or can be made so by externalising opaque resources), *and*
- unit tests can be written as input-output literal assertions with no fixture state.

If the agent is genuinely a single-shot transformer with no continuation, V12 already holds trivially — confirm and move on. If reproducibility fails the first test, V12 is *not* satisfied; identify the hidden state and externalise it before installing V10, O4, or O6 on top. If state cannot be serialised at all, the unserialisable piece is the design defect, not V12 — refactor the resource ownership.

## Structure

```
  Framework / runtime                          Agent code (pure)
  ─────────────────────                        ──────────────────
                                                       
  state_in ← Store.load(session_id)                    │
                                                       ▼
                              ┌─── Agent(state, input) → (output, state') ───┐
  input  ←  request           │                                              │
                              │   no module-level mutable state              │
                              │   no instance vars carrying cross-call data  │
                              │   no thread-locals; no singletons            │
                              │   no closures over external mutable state    │
                              │   no memoisation of session-keyed data       │
                              │                                              │
                              └──────────────────────────────────────────────┘
                                                       │
  Store.save(session_id, state')  ◀────────────────────┘
  return output to caller
```

The horizontal split is the discipline: state lives left of the line (framework), the agent function lives right of it (pure). Anything that crosses the line implicitly — a global, a singleton, a memoised cache — is the violation V12 forbids.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Agent Function** | the pure transformation `(state, input) → (output, state')` | explicit `state` + explicit `input` $\to$ explicit `output` + explicit `state'` | hold mutable state of its own (instance vars, class attrs, module globals, thread-locals, memoised caches). Every "convenience" cache is a V12 violation. |
| **State Schema** | the explicit, serialisable shape of `state` | — $\to$ typed structure (Pydantic, dataclass, TypedDict) | contain live references (open connections, file handles, in-process resources) — those do not survive serialisation; they are hidden state in JSON-shaped clothing. |
| **External State Store** | durable storage of `state` between invocations | (session_id, state) $\to$ ack; session_id $\to$ state | be in-process memory in production. An in-memory dict masquerading as a store is hidden state with a method signature. |
| **State Loader** | hydrating `state_in` from the store before each invocation | session_id $\to$ state_in | mutate the store during load. Load is read-only; mutations only happen via Save. |
| **State Writer** | persisting `state_out` to the store after each invocation | (session_id, state_out) $\to$ ack | partially write. Either the whole new state lands atomically, or nothing does — otherwise resumes see torn state. |
| **Resource Resolver** *(optional)* | re-acquiring opaque resources (DB connections, HTTP clients) per invocation from explicit identifiers in `state` | resource_id from state $\to$ live handle | be memoised across invocations in a way the agent can observe. The resolver may pool connections internally; the agent never sees pool state. |

The *Agent Function* is the only participant the application developer writes; everything else is framework. The split between the Function and the Store is the entire pattern. Conflating them — letting the function "just hold onto" anything across calls — is the failure mode V12 exists to prevent.

## Collaborations

A request arrives at the framework with a session identifier and an input. The **State Loader** reads the current `state_in` from the **External State Store**. If `state_in` references opaque resources by identifier (a DB connection ID, an HTTP client config), the **Resource Resolver** materialises them into live handles for this invocation only. The framework hands `(state_in, input)` to the **Agent Function**. The function — written as a pure transformation — produces `(output, state_out)`. It does not write to disk, mutate globals, or stash anything in its module; every effect it intends is encoded in `state_out` or in the `output`'s declared actions. The framework persists `state_out` via the **State Writer**, drops the resolved resources, and returns `output` to the caller. The next invocation — milliseconds later or weeks later, on the same process or a fresh container — repeats the same load-call-save cycle. V10 Checkpointing reuses exactly this loop, snapshotting `state_out` to a durable store; O4 Parallelization launches multiple agent calls knowing none can corrupt the others; V14 Trajectory Logging records the load and save events; V16 Offline Eval reproduces any past trajectory by replaying the same inputs against the same loaded state.

## Consequences

**Benefits**
- **Reproducibility.** Given the same `(state, input)`, the agent produces the same `(output, state')` — debugging from V14 traces becomes possible; V16 regression tests work; V18 simulation environments produce deterministic results.
- **Trivial checkpointing.** V10 has nothing to negotiate with the agent: the state is already external; snapshot it and resume.
- **Safe parallelisation.** O4 and O6 workers can be freely scheduled, retried, and restarted with no shared-mutable-state hazards.
- **Clean retries.** A failed call can be retried by re-loading the prior state and re-calling — no compensating actions to undo hidden side effects.
- **Portable agents.** O15 Agent Handoff and I6 A2A Delegation become "serialise the state and send it" with no special protocol.
- **Testable.** Unit tests are input-output literal pairs; no fixture state, no mocks of hidden globals.

**Costs**
- **State objects grow.** Everything the agent needs across calls must live in the explicit state — including, sometimes, much more than feels elegant. Disciplined trimming is required.
- **Serialisation overhead.** Every step pays for serialise / deserialise on the boundary. Negligible for small state; a tax on large state.
- **Framework complexity.** The Store, Loader, Writer, and Resource Resolver are infrastructure the team must build or adopt. The agent code is simpler; the *system* is not.
- **Resource re-acquisition.** Connections, clients, and authenticated handles must be re-resolved per invocation. Connection pooling at the resolver level recovers most of the lost performance; naïve implementations do not.

**Risks and failure modes**
- *Quiet violation.* A developer adds a "tiny" cache or singleton "just for performance." The agent is no longer V12-compliant; the property holds in tests but fails in production under restart or parallelism. The most common failure of V12 is its silent erosion over time.
- *Closures over module state.* An import-time configuration (`API_KEY = os.environ[...]`) is fine; an import-time *mutable* dict (`SESSIONS = {}`) is a V12 violation hiding as a global. Reviewers must flag module-level mutables specifically.
- *Memoised retrievers and clients.* `@lru_cache` on a function that returns a session-aware object turns the cache itself into hidden state. Resolver-level pooling is fine; agent-visible memoisation is not.
- *Unserialisable state.* Live handles end up in the state object (a DB cursor, an open socket). Serialisation appears to succeed (the object pickles) but cannot restore on a fresh process. Test restore in CI on every state-schema change.
- *State explosion.* The state becomes a junk drawer: every call appends "useful" context until snapshots are megabytes. Pair V12 with active state trimming and route history to V14 instead of the active state.
- *Hidden state via tool side effects.* A tool the agent calls mutates an external system; the agent's behaviour depends on that mutation; the dependency is not in the state object. This is not strictly a V12 violation (side effects are declared via tool calls), but if the agent then *reads* the side effect on a later turn without recording it in the state, it has hidden state by proxy. Discipline: tool results that the agent reasons over later must be folded into the state.

## Implementation Notes

- **Make state a typed object, not a dict.** Pydantic, a dataclass, or a TypedDict gives the schema a name and lets the type checker catch the field-creep that produces state explosion. The schema is itself a build artefact — version it.
- **No module-level mutables in the agent module.** Constants are fine; mutable structures keyed by session, user, or request are V12 violations. Lint for them.
- **No `@lru_cache` on session-aware callables.** Cache *deterministic, identifier-keyed* lookups freely (e.g. `lru_cache` on a token-counting helper). Never cache anything keyed by — or returning — session, user, or request data.
- **Resource handles by reference, not by value.** State stores a *connection id*, not a connection. The Resource Resolver hands the agent a live connection at the start of the call; the connection is released at the end. Pooling happens inside the resolver, invisible to the agent.
- **Test reproducibility in CI.** A single test that runs the agent twice on identical `(state, input)` and asserts byte-equal `(output, state')` is the V12 conformance test. Run it on every PR. The day it starts failing is the day V12 broke.
- **Fold tool results into state explicitly.** When a tool returns a value the agent will reason about on the next turn, *put it in the state object* — do not assume the agent will "remember" it. If the agent remembers it without it being in state, that memory is hidden state.
- **Externalise time and randomness.** Wall-clock timestamps and RNG seeds are inputs, not ambient. Pass them in; do not let the agent call `datetime.now()` or `random.random()` inside the function body. This is what makes the reproducibility test pass.
- **Pair with V10 from day one.** V12 without V10 produces an agent that is reproducible *and discards its state on every call*. V12 + V10 is the production combination; V12 alone is the design constraint that makes V10 clean.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V12 is a design constraint on the agent function itself — it *describes the shape* of the function any Reasoning pattern (R3 Plan-and-Solve, R4 ReAct, R7 Reflexion) or Orchestration pattern (O6 Orchestrator-Workers) implements. It composes with **V10 Checkpointing** (which snapshots the external state V12 keeps explicit), **O4 Parallelization** (safe only when V12 holds), **O15 Agent Handoff** (the handoff payload is the V12 state object), **V14 Trajectory Logging** (which records inputs and state transitions made auditable by V12), and **V16 Offline Eval** (which replays state-input literals against the V12 function to detect regressions). V12 imposes no LLM calls of its own; the chain is the host pattern's.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Resolve session_id and input from the request | `code` | |
| 2 | Load `state_in` from External State Store | `code` | State Loader |
| 3 | Resolve opaque resources referenced in state (DB, HTTP) | `code` | Resource Resolver |
| 4 | Validate `state_in` against the State Schema | `code` | State Schema |
| 5 | Run the agent function: `(state_in, input) → (output, state_out)` | `LLM` | host pattern (R-, O-, etc.) |
| 6 | Validate `state_out` against the State Schema | `code` | State Schema |
| 7 | Persist `state_out` via State Writer (atomic) | `code` | State Writer, V10 |
| 8 | Release resolved resources; return `output` | `code` | Resource Resolver |

**Skeleton** — the wiring; the agent function itself is the `# LLM` line and stays pure inside:

```
def invoke(session_id, input):
    state  = store.load(session_id)               # code  — State Loader
    state  = schema.validate(state)               # code  — State Schema
    res    = resolver.acquire(state.resources)    # code  — Resource Resolver
    try:
        output, state_out = agent(state, input, res)   # LLM  — V12 pure agent step
        state_out = schema.validate(state_out)    # code  — State Schema
        store.save(session_id, state_out)         # code  — State Writer (atomic)
        return output
    finally:
        resolver.release(res)                     # code  — never leak handles

# The agent itself — written as a pure reducer:
def agent(state: AgentState, input: UserInput, res: Resources) -> tuple[Output, AgentState]:
    # No module-level mutables. No instance vars. No memoised caches keyed by session.
    # All effects encoded in (output, state'); resources used through `res`, never cached.
    ...
    return output, state_out
```

**The LLM sessions.** V12 has *one* LLM step — the agent function itself, configured by whichever host pattern is in use (R4 ReAct, R7 Reflexion, O6 Orchestrator, etc.). V12 adds no setup of its own; it constrains *how the function around the LLM call is written*, not the LLM call's prompt.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent step** | the host pattern's chosen model | the host pattern's setup (role, tools, schema) — V12 imposes none of its own | the loaded `state` + the current `input`; the function must return both `output` and the updated `state'`, either directly or via a framework-extracted structured output |

**Specialist-model note.** None — V12 is a code-discipline pattern. There is no specialist model, no fine-tune, no long-context requirement. The build dependency is *engineering discipline plus framework support*: a state schema (Pydantic / dataclass), an external state store (Postgres, SQLite, Redis, or a workflow engine's built-in), a resource resolver (typically the framework's connection pooling), and a CI conformance test for reproducibility. Frameworks that bake this in — LangGraph (channels + reducers + checkpointer), Burr (actions as `State → State`), DBOS / Temporal / Restate (workflow steps with externalised durable state) — make V12 the default; rolling it by hand against a plain LLM SDK is straightforward but requires the discipline above.

## Open-Source Implementations

V12 is a design principle rather than a library — there is no canonical "Stateless Reducer" project. The verified references are frameworks whose architecture *enforces* the discipline:

- **12-Factor Agents — Factor 12: Make your agent a stateless reducer** — [`github.com/humanlayer/12-factor-agents/blob/main/content/factor-12-stateless-reducer.md`](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-12-stateless-reducer.md) — the canonical articulation; explicitly invokes the functional-fold (`foldl`) analogy. The accompanying repo at [`github.com/humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents) is the broader reference.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — channels and reducer functions are first-class: every state field has a declared reducer (`(state, write) -> state`), nodes return state updates rather than mutating, and the checkpointer interface serialises state externally. The closest production embodiment of V12 + V10 together.
- **Burr** — [`github.com/DAGWorks-Inc/burr`](https://github.com/DAGWorks-Inc/burr) — agent actions are explicitly typed as `State → State` reducers; `@action(reads=[...], writes=[...])` declares state dependencies at the function boundary. The most direct functional-reducer expression of V12 in a Python agent framework.
- **DBOS Transact (Python)** — [`github.com/dbos-inc/dbos-transact-py`](https://github.com/dbos-inc/dbos-transact-py) — workflow / step functions checkpoint to Postgres; the durable-execution model treats each step as a resumable unit whose state lives in the database, not the process. Composes V12 (function shape) with V10 (durable state) at the framework layer.
- **Temporal** — [`github.com/temporalio/temporal`](https://github.com/temporalio/temporal) — durable-execution platform; workflow code is required to be deterministic (no wall-clock, no RNG, no IO outside activities) — the strictest production enforcement of the V12 contract in any widely-used system.
- **Restate** — [`github.com/restatedev/restate`](https://github.com/restatedev/restate) — durable execution with consistent state per entity; explicit support for "Durable AI Agents" built on the same stateless-step-plus-external-state model.

For agents built on a plain LLM SDK (no framework), V12 is a code-review discipline: a typed state object, a load/save harness, no module-level mutables, no `@lru_cache` on session-aware functions, and a CI conformance test for reproducibility. The discipline is portable; the enforcement is the framework's or the team's.

## Known Uses

- **LangGraph-based production agents** (LangChain Inc and downstream) — the default architecture treats nodes as state updaters with explicit reducers and checkpointed external state.
- **Temporal-backed agent services** at companies running long-running agentic workflows — Temporal's determinism constraints enforce V12 at the framework layer; violations fail at replay time, not silently in production.
- **DBOS-backed AI applications** — durable-execution-as-a-library Python services where each workflow step is a V12-compliant function persisted to Postgres.
- **Burr-based agent applications** — explicit `State → State` action functions; the state graph is the production artefact.
- **HumanLayer-pattern agents** — agents built to the 12-Factor reference treat Factor 12 as a first-class architectural commitment; the suspend-to-inbox / resume-from-store flow only works because the agent function is V12-compliant.

## Related Patterns

- **Composes with** V10 Checkpointing — V12 makes the snapshot total (no hidden state to miss); V10 makes the snapshot durable. CONFLICTS CRITICAL 8 resolves their apparent tension: V12 is the agent's *function shape*; V10 is the framework's *state management*. They are complementary, not alternatives.
- **Required by** O4 Parallelization — safe parallel agent calls require V12; without it, concurrent invocations corrupt shared hidden state.
- **Required by** O6 Orchestrator-Workers — workers must be V12-compliant to be freely scheduled, retried, and restarted by the orchestrator. A stateful worker is a worker that cannot be safely replaced mid-task.
- **Required by** O15 Agent Handoff and I6 A2A Delegation — the handoff payload is the V12 state object; without V12, there is no complete state to hand off.
- **Required by** V16 Offline Eval — regression tests replay recorded inputs against the agent function and assert outputs; reproducibility requires V12.
- **Pairs with** V14 Trajectory Logging — V14 records inputs and state transitions; V12 makes those records sufficient to reproduce behaviour. Together they make production agents debuggable.
- **Distinct from** V10 Checkpointing — V10 is a *runtime mechanism* (save state durably); V12 is a *design constraint on the function* (no hidden state to begin with). V10 without V12 is theatre — the snapshot is missing pieces. V12 without V10 is reproducible but forgetful.
- **Distinct from** K11 Observational Memory and K12 Karpathy Memory — those are memory patterns at the knowledge layer (what the agent remembers across sessions). V12 is about execution state at the framework layer (what the agent function carries between calls). They operate at different layers and compose freely.
- **Note on fundamentality** — V12 passes the test: distinct Intent (function purity / state externalisation), distinct Participants (Agent Function vs. State Schema vs. Store vs. Loader vs. Writer), distinct Structure (left-of-line framework / right-of-line pure function). It is not a variant of V10 (which is the durable-state mechanism), and the composability tension flagged in CONFLICTS CRITICAL 8 is resolved by recognising the two patterns live at different layers — confirming V12 stands as its own pattern.

## Sources

- 12-Factor Agents (Dex Horthy, HumanLayer) — Factor 12: "Make your agent a stateless reducer"; also Factor 5 ("Unify execution state and business state") and Factor 8 ("Own your control flow"). [`github.com/humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents).
- 12-Factor App (Adam Wiggins, Heroku) — Factor 6: "Execute the app as one or more stateless processes." The web-app antecedent of agent statelessness. [12factor.net/processes](https://12factor.net/processes).
- Redux — *Reducers* documentation; the JavaScript-frontend analogue of the agent-as-reducer pattern.
- Elm Architecture — `update : Msg -> Model -> Model`; the canonical pure-reducer formulation in a typed language.
- Wadler, P. (1992) — "The essence of functional programming"; `State` monad and the discipline of explicit state threading.
- LangGraph documentation — channels, reducers, and checkpointers reference.
- Burr documentation (DAGWorks) — actions as `State → State` reducers.
- Temporal — "Workflow Determinism" technical documentation; the strictest production enforcement of V12-style purity in a widely-used durable-execution platform.
- DBOS — "Durable Execution as a Library" technical writeup; Postgres-backed workflow state externalisation.
