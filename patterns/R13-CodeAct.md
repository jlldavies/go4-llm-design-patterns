# R13 — CodeAct

> Have the agent emit *executable Python code* as its action — calling tools, composing them with control flow, and parking intermediate values in variables — instead of emitting a single structured JSON tool call per step, with the code running in a sandbox and its stdout / errors returning as the Observation.

**Also Known As:** Executable Code Actions, Code-as-Action, Programmatic Tool Calling, Code Agent (HuggingFace's term).

**Classification:** Category III — Reasoning · Band III-B Tool-using loops · the *code-as-action* loop — sibling of **R4 ReAct** (same Thought / Action / Observation loop, JSON action language) and **R5 ReWOO** (plan-then-execute, no observation feedback). Distinct from **R14 Program of Thoughts** — same syntactic surface (Python emission), different purpose (R14 delegates *computation*, R13 delegates *tool orchestration*).

---

## Intent

Make the agent's Action a *program*, not a tool call — so one step can call several tools, branch on what they return, loop, and keep intermediate results in variables — and execute that program in a sandbox whose stdout, return value, and stack traces become the next Observation.

## Motivation

R4 ReAct's action is one structured tool call per turn: pick a tool, fill its JSON schema, get one Observation back, decide again. That works, but it strains in three ways on real multi-tool tasks. **Composition is expensive in turns.** Calling three tools where output of A feeds B feeds C takes three full LLM round-trips, each re-reading the entire trajectory. **Intermediate data bloats context.** Every Observation — a search result, a file dump, a JSON blob — lands in the prompt and rides with every subsequent turn, even when the agent only needed one field. **Control flow is faked in prose.** Conditionals ("if the search returned nothing, try the alternate index") become Thoughts the model has to re-derive each turn instead of `if` statements.

Wang et al. (2024) ran the obvious experiment: replace JSON-action with *Python-code-action*. The agent emits a block of code; the runtime executes it; the block can call any number of tools (each is a Python function), can compose them, can branch and loop, can hold intermediate values in local variables that *never enter the LLM context*. The Observation is what the code printed plus any exception trace. Across multi-tool benchmarks (M3 ToolEval, API-Bank, MINT) they reported **~20 percentage points higher success rate** than JSON / text actions and **~30% fewer agent steps** to completion. The mechanistic basis of R13's accuracy advantage is context discipline (mechanisms 2 and 3): when one code block calls three tools, the intermediate values are Python variables in the kernel — they never enter the LLM's KV cache. Under R4, the same three tools would require three Observations, each adding to the growing trajectory that every subsequent LLM call attends over at O(seq_len²) cost (mechanism 2). R13 keeps the O(n²) attention budget bounded to the goal + code + stdout, not to intermediate data that the LLM has already processed. The mechanism is mundane and large: code is a denser, more expressive action language than JSON, and Python's call stack is a cheaper place to hold intermediate state than the LLM's prompt.

R13 is not a variant of R4. The loop shape is the same (Thought $\to$ Action $\to$ Observation), but the Participants differ — there is now a **Code Executor** with its own behavioural contract (must run sandboxed, must return stdout *and* errors as Observations, must persist variables across iterations), and the action language change cascades through almost every Implementation Note. Most importantly, the security envelope changes completely: a JSON tool call is constrained by the schema you wrote; an arbitrary Python block is constrained by *nothing the model is incentivised to respect*. This makes **V8 Tool Sandboxing a hard prerequisite, not a recommendation** — see CONFLICTS.md CRITICAL 5. R13 without V8 is not a deployable pattern in any environment that matters.

R13 is also not R14 Program of Thoughts. R14 generates code to do *arithmetic / numerical work* the LLM is bad at — no tools, no agent loop, one shot. R13 generates code to *orchestrate tools* across an agent loop. Same syntax, different job; an R13 step may also do R14-style computation inside its block, but R14 alone is not an agent pattern.

## Applicability

Use CodeAct when:

- the task naturally needs multi-tool coordination per step — A's output is B's input, possibly conditioned on a check;
- intermediate results are large or numerous (search hits, file contents, dataframes, lists) and should *not* bloat the LLM context;
- control flow (loops over collections, conditional branches, retries) is part of the action, not the reasoning;
- the model is strong enough to write correct Python against the available tool surface (modern frontier or tool-tuned mid-size models);
- you have, or can stand up, a sandboxed Python executor — **V8 Tool Sandboxing is mandatory**.

Do not use it when:

- there is no sandbox available and one cannot be deployed — **V8** prerequisite fails; fall back to **R4 ReAct** with JSON tool calls;
- the task is a single tool call per step with no composition — the code wrapper is pure overhead; use **R4** or a plain **I2 Function Call**;
- the tool sequence is independent and plannable up front — **R5 ReWOO** is 5$\times$ more token-efficient;
- the model cannot reliably write Python against your tool surface — error rates and re-tries will erase the 20pp gain; use **R4** instead;
- the loop cannot be bounded — never run R13 unbounded; pair with **V9 Bounded Execution** or it becomes anti-pattern **A3 Uncontrolled Recursion**;
- the task is pure numerical reasoning with no tools — use **R14 Program of Thoughts**, which is the same syntactic device for a different job.

## Decision Criteria

R13 is right when actions naturally chain tools per step, a sandbox is available, and the model writes good Python.

**1. Test for per-step composition.** Sketch the trajectory. If a *single logical step* naturally calls 2+ tools, or needs `if` / `for` over a returned collection, that step is one R13 action — but would be 2–4 R4 actions. Wang et al.'s ~30% step reduction comes entirely from this collapse. If every logical step is a single atomic tool call, R13's expressivity buys nothing and **R4** is simpler.

**2. Sandbox available?** This is a gate, not a slider. R13 executes LLM-generated Python; without **V8 Tool Sandboxing** (Docker, gVisor, E2B, Modal, Blaxel — see Implementation Notes) the pattern is a remote-code-execution channel to your filesystem and network. No V8 $\to$ no R13. If V8 cannot be provisioned in the deployment environment, fall back to **R4 ReAct**.

**3. Score the model's Python-against-tools quality.** Run a representative sample. Measure: parse-failure rate (model emits non-runnable code), tool-misuse rate (wrong argument shape), error-recovery rate (does the model correctly read a traceback Observation and fix the next block?). Wang et al.'s gains come from frontier or tool-tuned models. Below a quality threshold, R13 spends its accuracy advantage on retry overhead and **R4** wins.

**4. Cost the per-step LLM call.** R13 calls are typically *larger* per turn than R4 calls — the model emits more code than a JSON object — but there are *fewer* turns (30% fewer). Net token cost is usually comparable to slightly lower than R4. The dominant cost is the LLM call count; the sandbox roundtrip is fast and cheap compared to the model.

**5. Bound the loop and the sandbox.** Pair with **V9 Bounded Execution** for the agent loop (max steps, max wall-time, max cost — same as R4). Independently bound the *sandbox*: per-block CPU / memory / wall-time / network policy. The agent-loop bound stops infinite reasoning; the sandbox bound stops a single block from melting the executor. Both are required.

**Quick test — R13 is the right pattern when:**

- a single logical step naturally calls multiple tools or needs control flow, *and*
- **V8 Tool Sandboxing** is provisioned (this is a gate, not a preference), *and*
- the model reliably writes Python against the available tool surface (low parse / misuse rate on a sample), *and*
- the agent loop and the sandbox both have hard bounds (**V9** for the loop, sandbox limits for each block).

If actions are single atomic tool calls, use **R4 ReAct** — the code wrapper is overhead. If the tool sequence is independent and plannable, use **R5 ReWOO** for 5$\times$ token efficiency. If the work is pure numerical computation with no tools, use **R14 Program of Thoughts**. If no sandbox is available, the pattern is unsafe — fall back to **R4**.

## Structure

```
                              ┌──────────────────────────────────────────────┐
                              │                                              │
                              ▼                                              │
  Goal ─▶ [LLM] ─▶ Thought ─▶ Code Block ─▶ [Sandbox] ─▶ Observation ────────┘
            │                  (Python:                  (stdout +
            │                   imports tools,            return value +
            │                   calls them,               stack trace on
            │                   uses if / for,            error)
            │                   binds variables)
            │
            └─▶ Thought ─▶ Code Block: return answer ─▶ Answer

  Sandbox (V8) wraps every code block: filesystem isolation,
    network policy, CPU / mem / wall-time caps per block,
    a *persistent kernel* that carries variables across iterations.
  Agent loop bound (V9) wraps the outer loop.
  Trajectory logger (V14) records (Thought, Code, Observation) triples.
```

The single change from R4 is that **Action** has become a **Code Block** executed by a **Sandbox** that holds a *persistent kernel* — local variables defined in step *n* are still bound in step *n+1*, so the agent can fetch a large result in one step (`docs = search(...)`), let it sit out of the LLM context, and reference it (`docs[3]`) in a later step.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Agent (LLM)** | producing the next *Thought* and *Code Block* given the trajectory so far | trajectory $\to$ (Thought, Code) | execute its own code, or fabricate stdout / errors. If it produces both the code *and* its purported output in the same turn, the loop has collapsed and the agent is now hallucinating execution results. |
| **Tool surface** | the Python functions the code block may call (`search(...)`, `read_file(...)`, `fetch(...)`, etc.) | function calls $\to$ return values | reason or decide what to call next. Tools are passive callables in the sandbox namespace; the agent decides composition. |
| **Code Executor (Sandbox, V8)** | safely running each emitted code block in an isolated environment with a persistent kernel | Code Block + kernel state $\to$ (stdout, return value, stack trace, updated kernel) | run code outside the isolation envelope. *This is the load-bearing prohibition* — a Code Executor without V8 isolation is a remote-code-execution endpoint. The executor must enforce filesystem / network / CPU / memory / wall-time policy on every block. |
| **Kernel state** | the Python session's local variables, persisted across loop iterations | block N's bindings $\to$ block N+1's namespace | leak across agent sessions or users. Each agent run gets a fresh kernel; a kernel reused across users is a data-leak channel. |
| **Trajectory** | the append-only record `[(Thought, Code, Observation), …]` fed back into each LLM call | each completed triple $\to$ updated history | be edited or reordered mid-run. The *kernel* holds the heavy state (large results in variables); the *trajectory* holds the audit-grade history. Conflating them undoes R13's context-discipline win. |
| **Termination check** | deciding when the loop ends | trajectory + step count + cost $\to$ continue / halt | be implicit. R13 inherits R4's bound-or-die rule. Implicit termination ("the model will know") is anti-pattern **A3**. |
| **Trajectory logger** *(V14)* | persistent record of every triple for audit and debugging | each triple $\to$ log | be optional. R13 trajectories include *executable code the model wrote* — the audit log is also evidence. |

The defining separation is **Agent $\leftrightarrow$ Code Executor**: the Agent writes the program, the Executor runs it. The defining hard dependency is **Code Executor $\leftrightarrow$ V8 Sandbox**: the Executor *is* a V8 implementation, not a `subprocess.run` shortcut. Both separations failing — agent fabricates outputs, or executor runs without isolation — produce the pattern's two canonical disasters (hallucinated tool use; arbitrary code execution).

## Collaborations

A goal arrives. The Agent emits the first Thought (short natural-language reasoning about what to do) and the first Code Block — a snippet that imports / calls one or more tool functions from the sandbox namespace, may use `if` / `for` / variables, and ends with whatever output it wants the agent to see (a `print(...)`, a return value, or a final expression). The Code Executor receives the block, runs it in the persistent kernel, captures stdout, the final value, and any exception traceback, and returns all of it as the Observation. The trajectory now holds one complete triple. The next LLM call passes the full trajectory back to the Agent, which writes the next Thought conditioned on the Observation, then the next Code Block — which can reference variables bound in earlier blocks because the kernel persisted. The Termination check increments the step counter and checks the cost; if either bound trips, the loop halts. Otherwise the loop runs until the Agent's Code Block returns the final answer or calls an explicit `finish(answer)` tool. The Trajectory logger records every triple — Thought, Code, Observation — for audit.

Two collaboration patterns sit one level up. **O6 Orchestrator-Workers** can run an R13 worker for any sub-task that needs multi-tool coordination — the orchestrator's bound (V9) wraps the worker's bound (V9) wraps each block's sandbox bound (V8). **V14 Trajectory Logging** carries extra weight here: because the model is writing executable code, the log is also a security / incident artefact. A block that did something unexpected is reviewable as code, not as opaque LLM output.

## Consequences

**Benefits**

- ~20pp accuracy gain over JSON/text actions on multi-tool benchmarks (Wang et al., 2024); ~30% fewer agent steps to completion.
- Per-step composition: one block can call several tools with `if` / `for` / variables, instead of one tool per LLM call.
- Intermediate results live in the kernel, not the prompt — large search hits, file dumps, dataframes stay out of context.
- Self-debugging: tracebacks come back as Observations the model can read and respond to ("oh, that key doesn't exist — I'll check first").
- Uses the Python ecosystem natively — no custom JSON schemas to author for each library; an `import` is a tool.
- Composes with **R7 Reflexion** for across-run learning, **O6** for delegation, **K6 / K7** for trajectory compression, **V14** for trace audit.

**Costs**

- **Hard dependency on V8 Tool Sandboxing.** This is infrastructure (Docker / gVisor / E2B / Modal / Blaxel) — not a flag. Without it, R13 is unsafe at any scale.
- Larger per-turn LLM output (code is wordier than a JSON object) — though typically offset by ~30% fewer turns.
- Latency: each block adds a sandbox roundtrip on top of the LLM call (usually small — milliseconds — relative to the LLM).
- Sandbox-management complexity: kernel lifetime, per-block resource caps, network policy, persistent-state cleanup between users.
- Weaker models write worse code — the 20pp gain inverts on models that can't reliably emit runnable Python against your tools.

**Risks and failure modes**

- *Unsandboxed execution* — R13 deployed without V8. The pattern's catastrophic failure: prompt injection can make the LLM emit arbitrary code that runs with the agent's full permissions. See CONFLICTS.md CRITICAL 5.
- *Hallucinated Observation* — the model emits the code *and* what it "would have printed" in the same generation. Strict wiring must cut the model off after the code block; everything after must come from the actual sandbox.
- *Kernel leakage across users* — a sandbox that re-uses a kernel across agent runs leaks one user's variables into another's session. Each run gets a fresh kernel.
- *Same-block-repeat loop* — the model emits the same broken block repeatedly because the traceback is the same each time. Catch with a same-action-N-times detector and a forced "try a different approach" prompt.
- *Resource exhaustion* — a single emitted block can `while True` or allocate without bound inside the sandbox. The agent-loop bound (V9) is not enough; the sandbox needs *per-block* CPU / memory / wall-time caps.
- *Drift on long trajectories* — Long trajectories push the original goal into the middle of the accumulated context, where U-shaped recall (mechanism 4 — Liu et al. 2024) causes it to be geometrically under-attended relative to recent Observations. Restate the goal in a fixed position (system prompt or first user message prefix) and compress old code/observation triples with K6.
- *Untraced* — anti-pattern **A15 Untraced Agent**; R13 without **V14** is undebuggable and, given that the agent writes code, also unauditable.

## Implementation Notes

- **The sandbox is the pattern.** Pick a V8 implementation and treat it as a build dependency before writing the agent. In 2025–2026 the production options are: Docker containers with a network policy (general-purpose, well-understood), gVisor (stronger kernel isolation), and hosted services E2B / Modal / Blaxel / Daytona (turnkey, language-aware, ship with Jupyter kernels). HuggingFace's smolagents documentation is blunt: "The built-in LocalPythonExecutor is not a security sandbox." Believe it.
- **Persistent kernel, fresh per run.** Variables bound in step *n* should still exist in step *n+1* — that's where the context-discipline win comes from. Across distinct agent runs (different users, different tasks) the kernel must be fresh. Jupyter-style kernels per session is the canonical model.
- **Return stdout *and* stack traces as Observations.** Both are signal: stdout tells the agent what its code printed; the traceback tells it what went wrong. Hiding the traceback is the most common implementation bug — it removes the self-debugging channel that produces a chunk of R13's accuracy gain.
- **Bind tools as Python functions in the sandbox namespace** — the agent calls `search(query)` not `tool({"name": "search", "args": {...}})`. The tool surface becomes a Python module the model imports; this is what makes one block call many tools cheaply.
- **Cap each block's resources independently of the loop bound.** Per-block CPU seconds, memory, wall-time, and (especially) network policy. The agent-loop V9 says "stop the loop after N steps"; the sandbox cap says "stop *this* block after T seconds / M megabytes." Both are required.
- **Strict generation cut after the code block.** Stop tokens or explicit message-boundary handling must prevent the model from continuing past its code into fabricated stdout. The harness, not the model, owns the Observation channel.
- **Model choice matters more than for R4.** R13's gains are conditional on the model writing correct Python against your tools. Frontier models (Claude Sonnet 4 / Opus 4, GPT-4-class, Llama 3.1+ instruction-tunes) are reliable; smaller models drop the accuracy advantage in re-try overhead. Wang et al. specifically fine-tuned CodeActAgent on Mistral-7B and Llama-2-7B to make 7B-class models competitive — at the frontier the fine-tune is unnecessary.
- **Compose with R7 Reflexion** for across-run learning: R13 is the within-run loop; R7 retries failed R13 runs with a verbal critique of what went wrong, often pointing at specific code mistakes.
- **Log the code.** V14 Trajectory Logging is non-negotiable; the emitted code is part of the audit trail. For security review, the log of executed blocks is also the incident-response artefact.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** R13 is the *code-as-action* agent loop. The Agent session draws on **S3 Persona** for role, **S5 Constraint Framing** for code-emission rules, **S6 Output Template** for the Thought / Code contract. The loop is bounded by **V9** and logged by **V14**; long sessions compose with **K6 / K7** for trajectory compression. The Code Executor *is* a **V8 Tool Sandboxing** implementation — that is a hard prerequisite, not a composition. The tool surface is **I2 Function Call** style (Python functions in the sandbox namespace); **I3 MCP** tools can be wrapped as Python shims.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Initialise trajectory with goal; spin up fresh sandbox kernel | `code` | V8 |
| 2 | Check bounds (steps, cost, wall-time) — halt if tripped | `code` | V9 |
| 3 | LLM emits next Thought + Code Block | `LLM` | Agent session |
| 4 | If Code calls `finish(answer)` (or returns the final value), return | `code` | |
| 5 | Execute Code in sandbox kernel; capture stdout, return value, stack trace; apply per-block caps | `code` | V8 |
| 6 | Append (Thought, Code, Observation) to trajectory; log triple | `code` | V14 |
| 7 | Loop to step 2 | `code` | |

**Skeleton** — the wiring; each `# LLM` line is a configured session:

```
run(goal, tools, max_steps, max_cost):
    sandbox = V8.fresh_kernel(tools)                          # code — V8 mandatory
    trajectory = [goal]
    while not V9.bound_tripped(trajectory, max_steps, max_cost):  # code — V9
        thought, code_block = Agent(trajectory)                   # LLM
        if code_block.calls("finish"):
            return code_block.extract_answer()
        try:
            obs = sandbox.run(code_block,                         # code — V8 per-block caps
                              cpu_s=5, mem_mb=512,
                              wall_s=10, network="deny")
        except SandboxLimitExceeded as e:
            obs = f"Sandbox limit hit: {e}"                       # cap trips become Observations
        # obs = {stdout, return_value, traceback?} — all returned
        trajectory.append((thought, code_block, obs))             # code
        V14.log(thought, code_block, obs)                         # code — V14
    return bounded_out(trajectory)                                # code — V9 halt path
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | the system's main generalist (frontier or tool-use-tuned: Claude Sonnet 4/Opus 4, GPT-4-class, Llama 3.1+ — see Specialist-model note) | role (**S3**); the *tool surface as Python signatures* (function names, parameter types, docstrings — what is importable in the kernel); the Thought / Code output contract (**S6**); behavioural rules (**S5**: *"emit exactly one code block per turn; stop after the block; never invent stdout or tracebacks; call `finish(answer)` when done"*); examples of good multi-tool composition; the kernel-persistence rule (*"variables you bind persist into later blocks"*) | the full trajectory so far (goal + all prior (Thought, Code, Observation) triples) |

**Specialist-model note.** No fine-tuned specialist is *required*, but R13's accuracy advantage over R4 is *conditional on the model writing reliably-runnable Python against the provided tool surface*. Frontier instruction-tuned models (Claude Sonnet 4 / Opus 4, GPT-4-class, Llama 3.1+ instruction tunes) clear this bar; mid-size and small open models often do not without specific training. Wang et al.'s contribution included **CodeActAgent**, fine-tunes of Mistral-7B and Llama-2-7B on a 7K-example CodeActInstruct dataset that brought 7B-class models into competitive range. If your deployment requires a small open model, the fine-tune is a build dependency; if you can run a frontier generalist, none is needed. *V8 Tool Sandboxing is the only non-negotiable build dependency for this pattern* — not the model, the sandbox.

## Open-Source Implementations

- **CodeAct (official)** — [`github.com/xingyaoww/code-act`](https://github.com/xingyaoww/code-act) — Wang et al.'s reference implementation: the CodeActInstruct 7K-example dataset, CodeActAgent fine-tunes (Mistral-7B, Llama-2-7B), a containerised Jupyter-based execution engine, and reproduction scripts for the M3 ToolEval and MINT benchmarks. MIT-licensed.
- **OpenHands** (formerly OpenDevin) — [`github.com/All-Hands-AI/OpenHands`](https://github.com/All-Hands-AI/OpenHands) — production autonomous-software-engineering platform whose primary agent is `CodeActAgent`: a CodeAct loop with bash, Python, and a browser DSL as the unified action space, run inside a Docker sandbox. The largest-scale CodeAct deployment in the open-source ecosystem.
- **smolagents** — [`github.com/huggingface/smolagents`](https://github.com/huggingface/smolagents) — HuggingFace's minimal agent framework whose default agent (`CodeAgent`) writes Python code as actions. Ships with sandbox backends for E2B, Modal, Blaxel, Docker, and WebAssembly. Documentation is explicit that the built-in `LocalPythonExecutor` is *not* a security sandbox; production deployments must select a real V8 backend.
- **E2B Code Interpreter SDK** — [`github.com/e2b-dev/code-interpreter`](https://github.com/e2b-dev/code-interpreter) — sandboxed Python execution as a hosted service; the dominant turnkey **V8** backend for R13 implementations that don't want to manage Docker themselves.

## Known Uses

- **OpenHands (All-Hands AI)** — the CodeActAgent is the platform's flagship agent for software-engineering tasks; production use at scale across the OpenHands cloud, CLI, and self-hosted deployments.
- **HuggingFace smolagents** in deployed agent products — CodeAgent is the framework's default; widely used in HuggingFace Hub Space demos and downstream products.
- **Anthropic / OpenAI Code Interpreter–style features** — vendor-hosted code-execution channels (ChatGPT Code Interpreter, Claude's code execution tool) are CodeAct in everything but name: model emits Python, sandbox runs it, stdout returns as the next observation.
- **Coding agents** (Devin, Aider with code-execution mode, Cursor's background agents) — increasingly use code-as-action for multi-tool steps where R4-style JSON tool calls were the prior default.
- **Research agents** running on E2B / Modal sandboxes — data-analysis agents, scientific workflow agents, and dataframe-manipulation agents commonly run R13 against a Jupyter-kernel sandbox.

## Related Patterns

- **Sibling of** **R4 ReAct** — same Thought / Action / Observation loop, different action language. R4: structured JSON tool calls, one tool per step. R13: Python code, many tools + control flow per step. R13 reports ~20pp accuracy gain and ~30% fewer steps on multi-tool benchmarks but adds a hard sandbox dependency.
- **Sibling of** **R5 ReWOO** — same loop family, different stance on observation. R5 plans tool calls up front, no observation feedback; R13 conditions on observations every step. Mutually exclusive on the same task (the R4 $\oplus$ R5 logic applies to R13 $\oplus$ R5 identically).
- **Required by** **V8 Tool Sandboxing** — *hard prerequisite*, not a recommendation. See CONFLICTS.md CRITICAL 5. R13 without V8 is a remote-code-execution channel and is not a valid configuration in any production or shared environment.
- **Required by** **V9 Bounded Execution** — the agent loop must be capped; unbounded R13 is anti-pattern **A3**.
- **Pairs with** **V14 Trajectory Logging** — R13 logs are also security / audit artefacts because the model is emitting executable code.
- **Distinct from** **R14 Program of Thoughts** — same syntactic surface (model emits Python), different scope. R14 offloads *computation* the model is bad at (arithmetic, symbolic math), one-shot, no tools, no agent loop. R13 orchestrates *tools* in an agent loop. An R13 step may also do R14-style computation inside its block; R14 alone is not an agent pattern.
- **Inner pattern of** **O6 Orchestrator-Workers** — when a worker's sub-task needs multi-tool composition, R13 is the natural inner loop; nest **V9** bounds and **V8** sandbox limits.
- **Composes with** **R7 Reflexion** — across-run learning loop wrapping R13's within-run loop; especially useful when failures are diagnosable code mistakes.
- **Composes with** **K6 / K7** — long trajectories accumulate Observations; compress old triples while keeping the kernel (which holds the actual heavy state) intact.
- **Tool surface** — uses **I2 Function Call** style natively (Python functions in the sandbox namespace); **I3 MCP** tools can be wrapped as Python shims into the sandbox.

## Sources

- Wang, X., Li, B., Song, Y., Xu, F. F., Tang, X., Zhuge, M., Pan, J., et al. (2024). "Executable Code Actions Elicit Better LLM Agents." arXiv 2402.01030. ICML 2024. — the canonical reference; introduces the pattern, the CodeActInstruct dataset, the CodeActAgent fine-tunes, and the M3 ToolEval benchmark comparison against JSON / text actions.
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models." arXiv 2210.03629. ICLR 2023. — the R4 baseline that R13 measures against; same loop shape, different action language.
- Chen, W., Ma, X., Wang, X., & Cohen, W. W. (2022). "Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks." arXiv 2211.12588. — the R14 reference, included to disambiguate R13 from R14: same syntax, different purpose.
- OpenHands documentation — the `CodeActAgent` implementation reference; the largest open-source production deployment of R13.
- HuggingFace smolagents documentation — `CodeAgent` and its sandbox backends; the canonical "code-as-action is the default" framework, with explicit guidance that the built-in local executor is not a sandbox.
