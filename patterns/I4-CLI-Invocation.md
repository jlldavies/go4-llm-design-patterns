# I4 — CLI Invocation

> Have the agent reach for the existing command-line tool — `git`, `docker`, `gh`, `kubectl`, `aws`, `gcloud`, `jq`, `rg` — and run it directly, with no JSON Schema wrapper between the LLM and the binary.

**Also Known As:** Shell Tool, Command-Line Integration, POSIX Tool Use, Bash Tool, Terminal-First Agent.

**Classification:** Category VI — Integration · the *zero-schema* integration path — the LLM emits a shell command string instead of a routed JSON tool call; the help text and man pages already in the model's training data *are* the schema.

---

## Intent

Let the agent use the existing CLI ecosystem as its tool surface — invoking `git`, `docker`, `gh`, `kubectl`, cloud CLIs, and Unix utilities directly — so the integration carries zero schema-token overhead and inherits decades of battle-tested behaviour.

## Motivation

The other Integration patterns make the LLM route through a schema. I2 Function Call describes each tool as a JSON Schema in the system prompt; I3 MCP Server publishes a `tools/list` endpoint whose schemas the agent loads at startup. Both work, both add tokens, both require *someone* to author and maintain the schemas. The schema is a translation layer between the LLM and an underlying capability — and for a large class of engineering work, that translation layer is redundant. The underlying capability already has a description language: its own help text.

`git status`, `docker ps`, `kubectl get pods`, `gh pr create --title "..." --body "..."`, `aws s3 cp`, `rg -n pattern --type py` — these are not abstract operations that need to be wrapped to be usable. They are public interfaces whose documentation has been part of the model's training data for years. A modern frontier model knows `git`'s subcommand structure, `kubectl`'s resource model, `jq`'s filter syntax, and `ripgrep`'s flags without being told. Wrapping any of them in a `git_commit(message: str, files: list[str])` schema discards that knowledge in favour of a paraphrase the developer has to maintain. This is mechanism 10 in its productive form: the model's weights encode training-data knowledge of established CLIs. That knowledge costs nothing to access at inference time and occupies zero context tokens. I4's zero schema overhead is not simply "we skipped writing JSON Schema" — it is that the relevant knowledge already lives in the weights, where it is accessed at inference time without touching seq_len.

I4 takes the inverse position: emit the command, run it, return stdout. The schema cost is zero — there is no schema. The tool inventory is everything on `$PATH`, which on a developer workstation is hundreds of mature binaries. The trade is real: stdout is unstructured text, command construction can go syntactically right and semantically wrong, and a shell is one of the highest-blast-radius surfaces in computing. That trade is why the pattern *requires* V8 Tool Sandboxing and pairs with V6 Prompt Injection Shield — not as nice-to-haves, but as the structural counterweights that make I4 safe to deploy at all.

The pattern's distinct contribution is to name "use the CLI" as a first-class integration choice, on equal footing with I2 and I3, rather than as an informal escape hatch when the schema work feels too heavy. For tools that already have a CLI, I4 is often the *right* answer — Claude Code, Codex, and Gemini CLI all use it heavily for exactly this reason.

## Applicability

Use I4 when:

- the underlying operation already has a mature CLI (`git`, `docker`, `gh`, `kubectl`, `aws`, `gcloud`, `terraform`, `psql`, `jq`, `rg`, `sed`, `awk`);
- the CLI's documentation is in the model's training data — established, long-stable tools, not last-week's internal binary;
- token budget matters and an equivalent I3 server would consume tens of thousands of tokens on schemas alone;
- the agent runs in an environment where a sandboxed shell is acceptable (V8) — a developer workstation, a CI runner, a container;
- the work is software-engineering-shaped (filesystem operations, version control, container management, search, transform) — the historical sweet spot of CLI tools.

Do not use I4 when:

- the operation is privileged, irreversible, or financially material — the action is the wrong fit for shell execution, even sandboxed; gate it with **V1 Human-in-the-Loop** and execute via **I1 Direct API Call** so the call is auditable line-for-line;
- the tool is internal, niche, or recently invented and the model has poor priors on its flags — use **I2 Function Call** so the schema teaches the model the surface;
- the tool must be shared across many agents or clients with credential isolation — use **I3 MCP Server**;
- the runtime is a browser, a phone, or any environment without a shell to sandbox — use **I2** or **I3**;
- the output must be machine-parsable for a downstream code path and the CLI emits free-form text — use the CLI's structured-output flag where it has one (`gh --json`, `kubectl -o json`, `aws --output json`), or switch to **I1** against the underlying API.

## Decision Criteria

I4 is right when an established CLI already does the job, the model knows that CLI, and a sandboxed shell is acceptable in the runtime.

**1. Does a mature CLI exist?**
- Yes, and it has been stable for years (`git`, `docker`, `gh`, `kubectl`, `aws`, `gcloud`, `terraform`, `jq`, `rg`, standard Unix) → **I4** is a strong default.
- Yes, but it is the project's own internal CLI with non-public documentation → consider **I2** so the schema description teaches the model.
- No CLI; only an API → **I1** (deterministic) or **I2** (LLM-routed).

**2. Schema token cost.** Estimate the I3 cost of an equivalent MCP server: `tools/list` plus all schemas. If that approaches or exceeds 10,000 tokens (GitHub MCP alone runs 40,000–55,000), and the underlying tool has a usable CLI, **I4** wins on token economics alone.

**3. Sandbox feasibility.** Can the runtime confine subprocess execution? Filesystem path allow-list, network policy, no setuid, time-bounded — **V8 Tool Sandboxing** must be in place. If not, **I4** is unsafe; use **I2** + **I1** in code where the blast radius is bounded by what the developer wrote.

**4. Output shape.** Is the agent reading the stdout to *reason*, or does code need to *parse* it?
- Reasoning over text → **I4** fits; the model handles free-form output natively.
- Code parsing → use the CLI's structured-output flag (`--json`, `-o json`) or move to **I1** against the underlying API where the contract is typed.

**5. Reversibility and authority.** Score the worst-case command effect on a per-tool basis.
- Read-only or scoped to an ephemeral workdir → **I4** is fine under V8.
- Mutating with global effect (`rm -rf`, `kubectl delete`, `aws s3 rm`, `terraform apply`) → require **V1 Human-in-the-Loop** approval at the command-construction step, or restrict the allow-list to non-destructive subcommands and force the destructive ones through **I1**.

**Quick test — I4 is the right pattern when:**

- a stable, well-documented CLI already does the job, *and*
- the model has strong priors on that CLI's syntax (training-data coverage), *and*
- the runtime supports a sandboxed subprocess execution path (V8), *and*
- the command's worst-case effect is acceptable under that sandbox, or is gated by V1.

If the underlying tool has no CLI, choose **I1 Direct API Call** (deterministic) or **I2 Function Call** (LLM-routed). If the CLI exists but the agent must be shared across many clients with credential isolation, **I3 MCP Server** is the right level of abstraction. If a sandbox is not available — and "available" includes "enforced," not "intended" — do not use I4; pick the integration pattern whose blast radius the developer controls in code.

## Structure

```
   Agent (LLM) ── decides:   "I need to find every occurrence of foo in ./src"
                  selects:    ripgrep                              (training-data prior)
                  emits:      rg -n "foo" --type py ./src/         (command string)
                       │
                       ▼
              Command Validator  ── allow-list of binaries, deny-list of flags,
                       │            argument-shape checks, V6 injection check
                 (fail)│ (pass)
                 ▼     ▼
               refuse  V8 Sandbox  ── subprocess(shell=False, args=[...]),
                       │             scoped filesystem, network policy, timeout
                       ▼
                  exec the CLI ──▶  stdout, stderr, exit_code
                       │
                       ▼
                Output Shaper   ── truncate, V11-compact stderr, strip ANSI
                       │
                       ▼
              back to Agent context (text — no schema)

   The schema is the CLI's own help/man text, already in the model's weights;
   it is never serialised into the prompt.
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Agent (LLM)** | choosing the CLI and constructing the command string | task + prior CLI knowledge → shell command | invent flags it has not seen — hallucinated flags fail loudly under exec, but only after burning a turn. Constrain by allow-list so unknown binaries are refused before exec. |
| **Command Constructor** *(part of the Agent's per-call prompt)* | the format contract — *what* a valid command emission looks like | task → `argv`-shaped output (binary + args), never a shell-string with operators baked in | emit a single shell string for `subprocess(shell=True)`; the contract is an argument list. The moment the contract becomes "raw shell," injection is wide open. |
| **Command Validator** | gatekeeping the binary, flags, and argument shapes before exec | argv → pass / fail | trust an internal-caller bypass; the validator runs on every command, including ones the model emitted via a "safe-looking" allow-listed binary. `rg` is safe; `rg --exec=...` may not be. |
| **V8 Sandbox** | confining the actual exec (paths, network, time, capabilities) | argv → bounded subprocess | be optional. I4 without V8 is the pattern's primary failure mode — the page does not claim to be I4 in a production sense unless V8 is present. |
| **Output Shaper** | turning raw stdout/stderr/exit into something useful in context | (stdout, stderr, exit_code) → trimmed text + status | flood the agent's context with raw stderr on failure; that is what **V11 Error Compaction** is for. Likewise, ANSI escapes and long-tail noise get stripped here. |
| **Result Returner** | handing text back to the agent | shaped output → text in the next message | restructure the CLI's natural output format unnecessarily — the LLM is good at reading CLI output as-is, and rewrites can erase signal. |

Six narrow responsibilities, three of them in code, one of them an LLM emission. The pattern works because Command Validator and V8 Sandbox sit between the LLM's string and the kernel — the LLM proposes; code disposes.

## Collaborations

The Agent decides a command should run — typically inside an **R4 ReAct** Act step, or as an inline action in **R13 CodeAct** — and emits an argv list under the Command Constructor's format contract. The Command Validator checks the binary against an allow-list, flags against a deny-list, and argument shapes against any per-tool rules (`git` is permitted; `git push --force` to `main` is not). On a pass, **V8 Tool Sandboxing** runs the subprocess with filesystem and network policy scoped to the workdir and with a hard timeout from **V9 Bounded Execution**. On exit, the Output Shaper truncates and **V11 Error Compaction** rewrites any error blob into a short, model-readable summary. The result returns to the Agent's context as plain text; the Agent reasons over it natively, with no schema-to-natural-language step in between. Every invocation writes to the **V14 Trajectory Logging** trace including argv, exit code, and a head/tail of output, so the agent's actions are auditable after the fact. When the command is privileged or irreversible, **V1 Human-in-the-Loop** sits between Command Validator and V8 Sandbox, deferring exec until an out-of-band human ack lands.

## Consequences

**Benefits**
- Zero schema-token overhead — the CLI's help text already lives in the model's weights.
- Vast immediate tool inventory — anything on `$PATH` is reachable; no per-tool integration work.
- Idiomatic for software-engineering agents — the same commands a human engineer would type.
- Tools are battle-tested — `git`, `docker`, `kubectl` have flag-level semantics shaped by years of production use.
- Composes with the Unix pipeline — `cmd1 | cmd2 | jq ...` is one shell call, not three tool routes (though pipes deserve extra validation).

**Costs**
- Stdout is unstructured — the agent must parse free-form text; programmatic downstream code paths are fragile.
- The blast radius is large — a shell can touch the filesystem, the network, processes, the clock; the sandbox is doing real work.
- Command construction can be syntactically valid but semantically wrong — there is no schema validator catching a misused flag before exec.
- Tools that update their flag set faster than the model's training cycle drift into bad-prior territory.

**Risks and failure modes**
- *Shell injection* — passing an LLM-generated string to `subprocess(shell=True)`, or constructing a command via string concatenation with unsanitised inputs, is direct OWASP A03 territory. The Command Constructor must emit `argv` lists; the Validator must reject shell-meta in arguments that should be literal.
- *Off-allow-list binary* — without a strict binary allow-list, a creative agent invokes `curl | sh` or a packaged interpreter (`python -c`, `node -e`) and the sandbox has to catch what the allow-list should have refused.
- *Destructive-flag drift* — `rm`, `git push --force`, `kubectl delete`, `terraform apply`, `aws s3 rm` are all syntactically ordinary; the per-tool deny-list is where the actual safety lives, and it has to be maintained.
- *Stderr flood* — a failing CLI can dump megabytes of stack traces and stderr; without V11 compaction, the agent's context overflows.
- *Stale priors* — an old training cut taught the model `kubectl --foo` and the flag has since been removed; the failure surfaces as repeated bad exec attempts. Bound via V9.
- *Quiet success on the wrong action* — `cp -r src dest` succeeds when the agent meant `mv`; exit code is 0; the audit log shows success; the user's data is in the wrong place. Reversibility is a per-command question, not a per-pattern guarantee.

## Implementation Notes

- **`argv`, not strings.** The Command Constructor's output contract is an argument list — `["rg", "-n", "foo", "./src"]` — fed to `subprocess(shell=False, args=...)`. Never `subprocess(shell=True, args=llm_output)`. This is the single highest-leverage I4 rule.
- **Binary allow-list, not deny-list.** Permit `git`, `docker`, `gh`, `kubectl`, `rg`, `jq`, `sed`, `awk`, the ones you actually want; refuse everything else. A deny-list cannot keep up with `curl | sh`, `python -c`, `node -e`, container-escape gadgets.
- **Per-tool flag policy.** `git` is permitted; `git push --force` to a protected branch is gated. `kubectl get` is permitted; `kubectl delete` requires V1 approval. The per-tool layer is where most of the safety reasoning sits, and it has to be written down per tool.
- **Prefer structured-output flags where they exist.** `gh --json`, `kubectl -o json`, `aws --output json`, `docker --format '{{json .}}'` — when the agent will reason over a list or set, asking for JSON keeps stdout clean and gives the model an unambiguous shape. The agent still reads it as text; the structure just stabilises the read.
- **V8 sandbox first; V6 sanitise; V9 bound; V11 compact stderr; V14 log.** Composition with the Reliability category is not optional — those five together are what makes I4 production-grade.
- **Capture exit code, not just text.** Many CLIs distinguish "no matches" (exit 1) from "error" (exit 2); throwing both away by reading only stdout discards a useful signal.
- **Truncate output before it re-enters context.** Default to head + tail (e.g., first 100 lines + last 50) with an explicit "…N lines elided…" marker, rather than truncating to a fixed byte cap that drops the punchline. The mechanistic reason (mechanisms 2 and 3): CLI output that enters the context extends the KV cache, which grows monotonically for the session. Those tokens are present for every subsequent generation step, paying O(n²) attention cost. Aggressive truncation minimises this cost. The intermediate computation inside the CLI binary happens entirely outside the model's seq_len; only the compact result needs to cross back in.
- **Time-bound every exec.** A hung CLI is a hung agent; V9-style timeouts must apply.
- **Document the allow-list per agent.** The allow-list is part of the agent's V7 AgentSpec — what binaries this agent may invoke is a governance artifact, not a code constant.
- **Wrap state-modifying commands with confirmation.** For agents running outside V1, pre-flight a `git status` / `kubectl diff` / `terraform plan` before the corresponding `git push` / `apply` / `kubectl apply` — same pattern human engineers use.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** I4 chains the Agent's command emission with code that validates, sandboxes, executes, and shapes the result. The Agent itself is most often inside **R4 ReAct** (the command is an Act) or **R13 CodeAct** (where commands and small code blocks interleave). The exec layer pairs **V8 Tool Sandboxing** (mandatory), **V6 Prompt Injection Shield** (the Validator), **V9 Bounded Execution** (timeout, retry cap), **V11 Error Compaction** (stderr shaping), and **V14 Trajectory Logging** (audit). Privileged commands gate through **V1 Human-in-the-Loop**.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Agent picks tool and constructs argv | `LLM` | Agent session (with CLI-emission contract) |
| 2 | Validate binary against allow-list, flags against deny-list, args against per-tool rules | `code` | V6 Prompt Injection Shield, V7 AgentSpec |
| 3 | *(optional)* Human approval for privileged commands | `code` | V1 Human-in-the-Loop |
| 4 | Execute under sandbox: `subprocess(shell=False, args=argv)`, scoped FS/net, timeout | `code` | V8 Tool Sandboxing, V9 Bounded Execution |
| 5 | Capture stdout, stderr, exit_code | `code` | — |
| 6 | Shape output: truncate, strip ANSI, V11-compact stderr | `code` | V11 Error Compaction |
| 7 | Log argv, exit, head/tail of output, latency | `code` | V14 Trajectory Logging |
| 8 | Return shaped text to the Agent's next turn | `code` | — |

**Skeleton** — the wiring; the single `# LLM` line is the entire LLM contribution to the pattern:

```
cli_invocation(agent_state):
    argv = Agent.emit_command(agent_state)          # LLM — argv contract, not a shell string
    validate(argv)                                   # code — allow-list, deny-list, V6
    if requires_approval(argv):                      # code
        await human_ack(argv)                        # code — V1 gate
    with sandbox(workdir, net_policy, timeout):      # code — V8 + V9
        proc = subprocess.run(argv, shell=False,
                              capture_output=True,
                              timeout=timeout_s)
    shaped = shape(proc.stdout, proc.stderr,
                   proc.returncode)                  # code — truncate, V11 compact
    log(argv, proc.returncode, shaped, latency)     # code — V14
    return shaped                                    # text into the next Agent turn
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | a capable generalist with strong CLI priors — recent frontier models from Anthropic / OpenAI / Google fit | role (S3: e.g. *"you are a software engineer working in a sandboxed shell"*); the **command-emission contract** (S6: emit `argv` as a JSON array, no shell-meta); the **binary allow-list** for this agent (S5: explicit refusal language for anything off-list); the per-tool conventions the agent should prefer (`--json` where available, read-only subcommands before mutating ones) | the task / current ReAct step + the prior turn's tool output |

**Specialist-model note.** No fine-tuned specialist is required, but the pattern *is* training-data-sensitive in a way I1/I2/I3 are not: the model's prior on each CLI's flag set is doing the work that schemas do elsewhere. A capable generalist suffices; a weaker model with thin CLI exposure will fabricate flags. The prompt artifact carrying the weight is the **command-emission contract** plus the **allow-list** — those two together are what make a generalist behave like a disciplined shell user. Where the model's priors are weak (an internal CLI, a recently-released tool), prefer I2 instead so the schema teaches the surface.

## Open-Source Implementations

I4 is an architecture — *any* agent that invokes CLIs through a sandbox is an instance. The relevant references are the production agents that adopted CLI-first as their primary integration choice, and the sandbox libraries that make the path safe:

- **Claude Code** — [`github.com/anthropics/claude-code`](https://github.com/anthropics/claude-code) — Anthropic's terminal-resident coding agent. CLI-first by design: filesystem operations, `git`, `gh`, build/test runners, package managers all invoked as shell commands under an approval-and-sandbox layer; MCP is layered on top for tools that have no good CLI.
- **OpenAI Codex CLI** — [`github.com/openai/codex`](https://github.com/openai/codex) — OpenAI's local-running coding agent (Rust). Reads, edits, and executes code in the working directory through a sandboxed shell interface; Windows runs under a sandbox or WSL2.
- **Gemini CLI** — [`github.com/google-gemini/gemini-cli`](https://github.com/google-gemini/gemini-cli) — Google's open-source terminal agent. Built-in tools include file operations, shell commands, web fetch, and grounded search; uses a ReAct loop over CLI tools and optional MCP servers. (Being merged into Antigravity CLI through 2026.)
- **Aider** — [`github.com/Aider-AI/aider`](https://github.com/Aider-AI/aider) — terminal pair-programmer; `/run` invokes arbitrary shell commands (tests, linters, builds) and feeds output back to the model; tightly bound to the local git repo.
- **Open Interpreter** — [`github.com/openinterpreter/open-interpreter`](https://github.com/openinterpreter/open-interpreter) — runs Python, JavaScript, and shell locally inside the chat loop; the canonical "let the LLM use the shell" project for ad-hoc tasks.
- **Warp** — [`github.com/warpdotdev/warp`](https://github.com/warpdotdev/warp) — Rust-based agentic terminal (dual-licensed MIT / AGPL v3); Agent Mode chains shell commands, reads output, and self-corrects inside the terminal.

There is no single "I4 framework" — like I1, the pattern is the *absence* of a schema layer, plus the sandbox + validator pair that makes the absence safe. The agents above show the pattern in production form.

## Known Uses

- **Claude Code, Codex CLI, Gemini CLI, Aider** in active production use by software engineers worldwide — the dominant pattern for coding agents is *CLI-first, MCP-when-no-CLI*.
- **GitHub Copilot Workspace and similar PR-bot agents** — operate primarily through `git`, `gh`, and language-specific build tooling rather than schema-wrapped APIs.
- **DevOps and SRE agents** that wrap `kubectl`, `terraform`, `aws` / `gcloud` / `az` CLIs rather than reimplementing the underlying APIs as I3 servers — the schema cost of doing it via MCP would be prohibitive.
- **Anthropic's published "CLI-first" guidance** for agent design — the explicit recommendation to prefer CLI invocation over schema-wrapping where a CLI already exists; named in the Anthropic and Claude Code docs as the default pattern.
- **GitHub Actions and CI agents** (Gemini CLI GitHub Actions, Claude Code in CI) — the runner itself is a sandboxed shell environment, and the agent works through it natively.

## Related Patterns

- **Sibling of** I2 Function Call — I2 routes through schemas; I4 routes through CLI text. Both have the LLM choose the call; they differ in what the choice is expressed *in*.
- **Sibling of** I3 MCP Server — I3 is a shared, multi-client schema surface; I4 has no schema. For tools with mature CLIs and no multi-client sharing requirement, I4 typically wins on token cost.
- **Distinct from** I1 Direct API Call — I1 is code-chosen and code-executed; I4 is LLM-chosen and code-executed. Both share "no schema in the prompt"; they differ in *who chooses the call*.
- **Required by** V8 Tool Sandboxing — I4 without V8 is the pattern's primary failure mode; production I4 deployments treat V8 as part of the pattern, not a separate concern.
- **Pairs with** V6 Prompt Injection Shield — the Command Validator is V6's checkpoint at the shell boundary; LLM-emitted strings flowing into a subprocess are an OWASP A03 vector by default.
- **Pairs with** V9 Bounded Execution — every exec has a timeout; runaway CLIs are bounded the same way runaway loops are.
- **Pairs with** V11 Error Compaction — stderr from a failing CLI is the canonical case V11 was written for.
- **Pairs with** V14 Trajectory Logging — argv + exit + head/tail of output is the audit unit for a CLI agent.
- **Pairs with** V1 Human-in-the-Loop — privileged or irreversible commands (`git push --force`, `kubectl delete`, `terraform apply`, `aws s3 rm`, `rm -rf`) gate through V1.
- **Composes with** R4 ReAct — the Act step in a ReAct loop, when the action is a shell command, is an I4 invocation.
- **Composes with** R13 CodeAct — CodeAct generates and executes code blocks; those blocks frequently include CLI invocations, making CodeAct a heavy I4 user.

## Sources

- Unix philosophy — McIlroy, M. D. (1978), Bell System Technical Journal — "small, composable programs that do one thing well"; the design ethos under every CLI tool I4 reaches for.
- Anthropic Claude Code documentation — [`code.claude.com/docs`](https://code.claude.com/docs/en/overview) — terminal-first agent architecture; explicit CLI-first guidance with MCP as the second layer.
- OpenAI Codex CLI documentation — [`developers.openai.com/codex/cli`](https://developers.openai.com/codex/cli) — sandboxed local shell agent.
- Google Gemini CLI announcement and docs — [`blog.google` introducing Gemini CLI](https://blog.google/innovation-and-ai/technology/developers-tools/introducing-gemini-cli-open-source-ai-agent/) and [`google-gemini.github.io/gemini-cli`](https://google-gemini.github.io/gemini-cli/) — ReAct loop over CLI tools and MCP.
- 12-Factor Agents — Factor 8, *Own Your Control Flow* — argues for explicit, code-owned execution paths; aligns with I4's "the shell is your control surface" framing.
- Karpathy, A. (2025) — public commentary on agent architecture; "use the LLM only where language understanding adds value" generalises to "don't wrap a tool that already has a usable interface."
- OWASP Top 10 — A03:2021 Injection — the security baseline for any pattern that feeds LLM-generated text into a subprocess; the argv-not-shell-string rule comes from here.
- Anthropic and OpenAI agent guidance materials on tool use — implicitly position CLI invocation as a first-class integration alongside function calling and MCP for coding-shaped tasks.
