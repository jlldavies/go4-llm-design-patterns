# R14 — Program of Thoughts

> Generate a self-contained program that computes the answer, run it in a deterministic interpreter, return the interpreter's output — delegating numerical and symbolic work out of the model's tokens and into code.

**Also Known As:** PoT, Program-Aided Language Models (PAL — Gao et al. 2022, structurally the same pattern), Code-Augmented Reasoning, Computational Reasoning, Disentangled Computation.

**Classification:** Category III — Reasoning · Band III-C Executable reasoning · the *single-shot, computation-offloading* counterpart to R13 CodeAct's *looped, action-language* code execution.

---

## Intent

For tasks whose hard part is computation — arithmetic, algebra, financial sums, statistical operations, symbolic manipulation — let the model write a short program and let a Python (or equivalent) interpreter compute the answer, instead of asking the model to compute in natural-language tokens.

## Motivation

Chain-of-thought (R1, R2) made step-by-step reasoning visible and pushed accuracy up across the board, but it left one failure mode untouched: language models do arithmetic badly. Even strong models confidently produce wrong sums on multi-digit multiplication, drop terms in symbolic algebra, and misapply percentage and date arithmetic. The reason is structural — token prediction is not arithmetic — and the failure is silent, because the rest of the chain looks plausible.

Chen et al. (2022) framed the move precisely: *disentangle computation from reasoning*. The mechanistic basis is the stochastic-vs-deterministic distinction (mechanism 7): token generation samples from a learned probability distribution trained on human text, which contains arithmetic errors. There is no probability distribution for the correct answer to 347 × 18 that excludes wrong answers — the model must sample something. A Python interpreter, by contrast, is deterministic (the same expression returns the same value, always) — a hard guarantee absent from stochastic autoregressive generation (mechanism 7). The pattern replaces stochastic sampling over arithmetic with deterministic computation. The model is good at the reasoning part — what to compute, in what order, with what inputs. It is bad at the computation part — the actual multiplication, addition, sorting, statistical operation. So give the reasoning to the model and the computation to a Python interpreter. The model emits a short program that names variables, applies operations, and prints the result; an interpreter runs the program; the printed output is the answer. The model never tries to do the arithmetic itself. On the paper's evaluations across math word problems (GSM8K, AQuA, SVAMP) and financial Q&A (FinQA, ConvFinQA, TATQA), PoT outperforms few-shot CoT by an average of ~12 percentage points; with self-consistency decoding (R17) over PoT programs, it sets or matches state of the art across the math benchmarks.

The defining claim of the pattern is narrow and strong: *for any sub-task where a deterministic algorithm exists, asking the model to simulate that algorithm in natural-language tokens is strictly worse than asking it to emit the algorithm and run it*. The bet only pays when the bottleneck is computation; for purely linguistic or commonsense reasoning, PoT has nothing to offer over CoT.

PoT is fundamentally distinct from R13 CodeAct despite both using code. PoT generates *one program, runs it once, returns the printed answer* — there is no loop, no observation step, no tool catalogue, no self-debugging. R13 uses code as the *action language inside an agent loop* — the model writes code, observes its output (including errors), thinks, writes more code. PoT is to CoT what R13 is to ReAct: a code-grounded replacement of a token-only pattern, but the loop structure (R13) versus single-shot structure (R14) is the architectural difference.

## Applicability

Use Program of Thoughts when:

- the task requires numerical or symbolic computation — arithmetic, percentages, ratios, statistics, financial formulas, date math, unit conversion, simple algebra;
- correctness on the computation step is non-negotiable (financial, scientific, engineering, regulatory contexts);
- the program to compute the answer is short and self-contained — input values are in the prompt or fetched once;
- the answer is a value (number, string, list) the interpreter can print, not a long-form narrative.

Do not use when:

- the task is purely linguistic or commonsense reasoning — there is no computation to offload; use **R1 Zero-Shot CoT** or **R2 Few-Shot CoT**;
- the task needs to call multiple external tools with conditional control flow over their outputs — use **R13 CodeAct**, whose loop and observation step are exactly that;
- the task requires exploratory search over an unknown solution space — use **R9 Tree of Thoughts** or **R10 LATS**;
- a secure code-execution sandbox is unavailable — without **V8 Tool Sandboxing** even a trusted-looking program can do harm; PoT requires V8 as a build dependency.

## Decision Criteria

R14 is right when the bottleneck is computation, the computation is expressible as a short deterministic program, and a sandbox is available to run it.

**1. Locate the bottleneck.** On a labelled error set, classify CoT failures: are they *reasoning* errors (wrong decomposition, wrong formula, wrong values pulled from context) or *computation* errors (right formula, right values, wrong arithmetic)? If computation errors are ≥ ~20% of failures, PoT removes them at the source. If reasoning errors dominate, PoT will not help — use **R2 Few-Shot CoT** or **R7 Reflexion** instead.

**2. Programmability check.** Can the answer be computed by a 5–30 line program with no external API calls beyond standard math/stats libraries? Yes → PoT fits. If the answer requires multiple tool calls with branching on their results → use **R13 CodeAct**. If the answer is a narrative or open-ended generation → PoT cannot represent it.

**3. Sandbox availability.** PoT requires **V8 Tool Sandboxing** — a Python (or equivalent) execution environment with no network access, no filesystem write outside a scratch dir, and a wall-clock and memory cap. If you cannot deploy V8, do not deploy PoT; the computational gain is not worth an RCE surface. Lower-risk than R13 because PoT runs single-shot programs over data, not loops calling external tools, but the sandbox requirement is identical.

**4. Cost the call.** PoT is one LLM call plus one interpreter execution — strictly cheaper than R7 Reflexion (N retries) or R9 ToT (branching) and on par with R1/R2 CoT. The interpreter call itself is sub-millisecond for typical PoT programs. Combine with **R17 Self-Consistency** (sample N programs, run each, majority-vote the answer) for hardest-cases — that multiplies cost by N but matches state of the art on math benchmarks.

**5. Output verifiability.** PoT's answer is the interpreter's printed value. That is easy to validate, log, and compare to a reference — a Reliability win. If you need to validate intermediate reasoning steps too, pair with **V14 Trajectory Logging** to capture the program alongside the answer.

**Quick test — R14 is the right pattern when:**

- computation errors dominate the failure mode, *and*
- the answer is expressible as a short program with standard libraries only, *and*
- a sandboxed interpreter (V8) is available, *and*
- the task does not need a tool-using loop with observation between calls.

If the task is purely linguistic, use **R1** or **R2** CoT. If the task needs a tool-loop with branching on tool outputs, use **R13 CodeAct**. If the search space itself is unknown, use **R9 ToT** or **R10 LATS**. If the bottleneck is reasoning quality rather than computation, **R7 Reflexion** or **R8 Self-Refine** will help and PoT will not.

## Structure

```
  Question ──▶ Reasoner (LLM)
                   │
                   ▼
           emits: short program
           ┌────────────────────────┐
           │ def solve():           │
           │     x = ...            │
           │     y = ...            │
           │     return f(x, y)     │
           │ print(solve())         │
           └────────────────────────┘
                   │
                   ▼
           Interpreter (sandboxed, V8)
                   │
                   ▼
           printed value ──▶ Answer
                              (optionally: Formatter wraps it
                               in a natural-language reply)
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Reasoner (LLM)** | the program — variable naming, formula choice, control flow, the printed answer | question + relevant data → executable program ending in a `print` of the answer | compute the answer in natural-language commentary; if the model "shows its work" inline and ignores the print value, the whole point of the pattern is lost. |
| **Program (artefact)** | the deterministic algorithm | — → runnable code | depend on network, filesystem, time, or environment beyond a fixed sandbox; reach into a tool catalogue (that's R13); or contain a loop over external observations (also R13). |
| **Interpreter** | deterministic execution | program → printed value or error | be granted any capability beyond compute on the inputs — network, write-filesystem, subprocess, and unbounded time/memory are out (V8). |
| **Sandbox (V8)** | the security boundary around the Interpreter | program → bounded execution context | leak a successful PoT into a long-lived process; each run is ephemeral. |
| **Formatter** *(optional)* | wrapping the printed value into a user-facing answer | question + printed value → natural-language reply | recompute or second-guess the value; its job is presentation only. |

The Reasoner-and-Formatter separation matters most: the Reasoner emits the program, the Formatter (often the same model in a different session) shapes the answer. Mixing them tempts the model to "explain its reasoning" by recomputing in prose — and the recomputation drifts from the program's actual output.

## Collaborations

A question arrives. The Reasoner reads it and any inline data, then emits a short Python program that defines variables, applies the operations the question requires, and prints the answer. The Interpreter — running inside a V8 sandbox — executes the program. The printed value is the answer. Optionally, a Formatter takes the question and the printed value and produces a natural-language reply with the answer embedded. There is no loop: the program is single-shot, there is no observation step, there is no tool catalogue. If the program raises an exception or fails validation, the outer policy may retry once with the error in context (a thin Reflexion-style retry, bounded by **V9**), but that is a wrapper around PoT, not part of it. When the harder of the math benchmarks demand more, PoT composes with **R17 Self-Consistency**: sample N independent programs, run each, majority-vote the printed answers.

## Consequences

**Benefits**

- Eliminates arithmetic hallucination at the source — computation is deterministic.
- Cheap: one LLM call + one interpreter call, comparable cost to CoT and far below ToT/LATS/Reflexion. Single-shot, no loop — PoT's LLM call is the only call (plus one interpreter execution). The interpreter result is constant regardless of context length, and the program can be computed without any KV-cache growth from observation accumulation (mechanism 2 / 3). This is the mechanistic reason PoT is cost-equivalent to CoT rather than multiplicatively more expensive.
- The program is an inspectable artefact — easier to audit and test than a CoT trace.
- Composes naturally with **R17 Self-Consistency** for hardest cases (sample-and-vote over programs).
- Removes the "plausible-but-wrong number" failure mode in financial, scientific, and engineering Q&A.

**Costs**

- Requires a sandboxed execution environment (V8) as a build dependency.
- Does not help on purely linguistic / commonsense tasks — same cost as CoT, no benefit.
- Programs can be syntactically valid but semantically wrong — a misread of the question goes uncaught unless validated against a reference.
- Adds an interpreter step to the critical path (small but non-zero latency).

**Risks and failure modes**

- *Mis-formalised question* — the Reasoner reads the question wrong and writes a correct program for the wrong problem; the deterministic interpreter then computes a confidently wrong answer.
- *Library hallucination* — the Reasoner imports a non-existent package or calls a function that does not exist; the run fails. Bound the available imports in the sandbox.
- *Sandbox escape* — if V8 is mis-configured, PoT becomes an RCE surface; the program is generated text, not vetted code.
- *Recompute drift* — the Reasoner's commentary disagrees with the program's printed value, and a downstream formatter trusts the commentary instead of the value.
- *Misapplied pattern* — PoT used on a task whose hard part is *reasoning* rather than computation; accuracy does not improve and the program-emission overhead is wasted.

## Implementation Notes

- Force the program to end in `print(<answer>)`; downstream code reads the last printed line as the answer. A program that "shows work" without printing the final value is unusable.
- Pin the sandbox's import set. The Reasoner should know what it is allowed to import (e.g. `math`, `statistics`, `datetime`, `decimal`, `fractions`, `sympy` if available). Anything outside the allow-list is a hard error.
- For currency and financial work, force `decimal.Decimal` or `fractions.Fraction` over `float` to avoid binary-float artefacts in the answer.
- Cap the program's wall-clock (e.g. 5 seconds) and memory; PoT programs are typically <1ms and <50MB. Anything exceeding the cap is a runaway and should fail closed.
- Validate the program before executing: it parses, it only imports allow-listed modules, it has no obvious dangerous calls (`os.system`, `subprocess`, `eval`, network I/O). Validation is cheaper than running a malicious program and recovering.
- Pair with **R17 Self-Consistency** when the task is hard enough that one sample is unreliable: sample 5–20 programs at temperature > 0, run each, majority-vote the printed values. This is the configuration that sets SOTA on math benchmarks.
- Log the program and the printed value as separate artefacts (**V14 Trajectory Logging**) — easier to diff regressions.
- Do not patch PoT into a tool-use loop. If the task needs that, switch to **R13 CodeAct**; PoT's value is in being single-shot.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** R14 chains a *Reasoner* LLM session with a sandboxed *Interpreter*. The Reasoner's setup is Signal-layer work — a role (**S3**), constraints (**S5**) on imports and side effects, and a strict output template (**S6**) for the program format. Sandboxing is **V8 Tool Sandboxing** (required). Optional composers: **R17 Self-Consistency** for sample-and-vote, **V9 Bounded Execution** for retry budget, **V14 Trajectory Logging** for program + answer artefacts. For a user-facing wrapper, add a Formatter LLM session.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Reasoner emits a program ending in `print(<answer>)` | `LLM` | Reasoner session, S6 template |
| 2 | Validate program — parses, imports allow-listed, no banned calls | `code` | V8 policy |
| 3 | On invalid: one bounded retry with the error; else fail closed | `code` (or LLM) | V9 |
| 4 | Run program in sandboxed interpreter; capture printed output and any error | `code` | V8 |
| 5 | *(optional)* Sample N programs and majority-vote answers | `code` | R17 |
| 6 | *(optional)* Formatter wraps the printed value into a user reply | `LLM` | Formatter session |
| 7 | Log program + printed value + final answer as separate artefacts | `code` | V14 |

**Skeleton** — wiring only; `# LLM` markers identify configured sessions:

```
program_of_thoughts(question):
    program = Reasoner(question)                  # LLM — one call, emit program
    if not validate(program):                     # code — V8 import + AST allow-list
        program = Reasoner.retry(question, error) # LLM — one bounded retry, V9
        if not validate(program): fail_closed()
    output  = sandboxed_exec(program)             # code — V8 interpreter, capped time/memory
    answer  = parse_printed_value(output)         # code
    log(program, output, answer)                  # code — V14
    return answer

# Optional: self-consistency wrapper (R17)
def pot_with_voting(question, n=10):
    answers = [program_of_thoughts(question) for _ in range(n)]  # parallel via O4
    return majority_vote(answers)
```

**The LLM sessions.** One session is required; a Formatter is optional.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Reasoner** | strong generalist with code-fluency (program quality caps the pattern); GPT-4, Claude, Gemini-class, or any code-tuned variant | role (*"you solve numerical / computational problems by writing a short Python program; do not compute in prose"*); the **import allow-list**; the **output template** — code only, ending in `print(<answer>)`, no commentary outside the program; 1–3 few-shot exemplars showing the expected form (S2); constraint (S5): *no network, no filesystem, no subprocess, no `eval`* | the question (and inline data) |
| **Formatter** *(optional)* | small fast generalist | role (*"you wrap a computed value in a natural-language answer to a user; do not recompute"*); answer-format rule (S6); rule that the value is authoritative | the question + the printed value |

Concretely, the **Reasoner** setup includes: *"Reply with a single Python code block. Define a `solve()` function, return the answer from it, and call `print(solve())` at the end. You may import only from: `math`, `statistics`, `datetime`, `decimal`, `fractions`. Do not include explanation outside the code block."* The per-call prompt then carries only the question and any inline numbers or tables. The Formatter (if used) carries the corresponding rule that it must report the printed value verbatim.

**Specialist-model note.** No fine-tuned specialist is required. Two structural choices change everything. First, **the Reasoner must be a separate session from any Formatter** even when the same model serves both — a Reasoner that knows a Formatter will rephrase its answer is tempted to add prose; a Formatter that can recompute drifts from the program's printed value. Second, **the sandbox (V8) is a hard build dependency**, not an optional add-on — PoT runs untrusted generated code by construction. The Reasoner benefits from a code-fluent model (any modern Opus/Sonnet/GPT-4/Gemini-class generalist; smaller models drop import-correctness and edge-case handling); the Formatter can be cheaper.

## Open-Source Implementations

- **Program of Thoughts (original)** — [`github.com/TIGER-AI-Lab/Program-of-Thoughts`](https://github.com/TIGER-AI-Lab/Program-of-Thoughts) — Chen et al.'s reference implementation; few-shot and zero-shot PoT prompts, evaluation on GSM8K / AQuA / SVAMP / FinQA / ConvFinQA / TATQA, plus the self-consistency composition.
- **PAL: Program-Aided Language Models** — [`github.com/reasoning-machines/pal`](https://github.com/reasoning-machines/pal) — Gao et al.'s contemporaneous implementation of the same pattern (ICML 2023); BIG-Bench Hard reasoning tasks, math word problems, symbolic reasoning; the structural twin of PoT.
- **LangChain `PALChain`** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) (`langchain_experimental.pal_chain.base.PALChain`) — runnable PAL/PoT chain in LangChain Experimental; useful as a working reference even though it sits in the experimental package.
- **E2B Code Interpreter** — [`github.com/e2b-dev/code-interpreter`](https://github.com/e2b-dev/code-interpreter) — sandboxed code-execution SDK (Python and JS/TS) commonly used as the V8 layer beneath PoT-style patterns; not PoT itself but the standard sandbox under it.
- **LLM Sandbox** — [`github.com/vndee/llm-sandbox`](https://github.com/vndee/llm-sandbox) — lightweight container-backed sandbox for running LLM-generated code; alternative V8 substrate.

## Known Uses

- **OpenAI Code Interpreter / "Advanced Data Analysis"** — productionised single-program code execution against user prompts; the consumer-facing embodiment of PoT for math, data-analysis, and computation questions.
- **Claude analysis tool** and equivalent code-execution features in Gemini and other assistant products — same single-shot-program pattern when the user's question is computational.
- **Financial Q&A assistants** over filings and reports — FinQA / ConvFinQA-style workloads where PoT eliminates the percentage / ratio / period-arithmetic errors CoT generates.
- **Math-tutor and STEM-homework assistants** — the canonical end-user task where PoT's accuracy advantage over CoT is largest.
- **Spreadsheet copilots** that emit a formula or a short script to compute a cell value, rather than guessing the value — structurally PoT with a non-Python target language.

## Related Patterns

- **Sibling of** R13 CodeAct — both delegate to a code interpreter. **Distinct** in structure: PoT is *single-shot, computation-offloading*, one program one run; R13 is *looped, action-language*, code as the action inside a ReAct-style think-act-observe loop with tools and self-debugging. They are two patterns because the loop changes the Participants (R13 adds an Observer, a Tool Catalogue, and a self-debug branch) and the failure modes (PoT fails on mis-formalised questions; R13 fails on cascading tool errors).
- **Refines** R1 / R2 Chain-of-Thought — same intent (decompose the problem step-by-step), strictly better implementation when the steps are computational. PoT replaces token-arithmetic with interpreter-arithmetic. For any numerical task, PoT strictly dominates CoT.
- **Composes with** R17 Self-Consistency — sample N programs, run each, majority-vote the printed answers. This is the configuration that set SOTA on the math benchmarks in the original paper.
- **Required by** V8 Tool Sandboxing — PoT cannot be deployed without a sandboxed interpreter. V8 is a hard build dependency, not an optional add-on.
- **Pairs with** V9 Bounded Execution — caps any retry-on-error wrapper; without a cap, a broken question can re-emit broken programs.
- **Pairs with** V14 Trajectory Logging — log the program and the printed value separately; this is the artefact a Reliability review will want.
- **Pairs with** O4 Parallelization — when run inside R17 Self-Consistency, the N independent program samples and executions parallelise trivially.
- **Distinct from** R7 Reflexion — Reflexion adapts across attempts by remembering past failures; PoT does not adapt at all. If the issue is "the model keeps writing programs for the wrong problem", Reflexion may help; if the issue is "the model can't multiply correctly", PoT solves it directly.
- **Distinct from** R5 ReWOO — ReWOO plans tool calls; PoT computes. ReWOO's Worker is deterministic dispatch over a tool catalogue; PoT's Interpreter is a deterministic computer over inline data.
- **Note on fundamentality** — PoT and PAL (Gao et al. 2022) are the same pattern under two names from contemporaneous papers; treat as one. PoT and CodeAct are two patterns: the single-shot computational structure is genuinely different from the looped action-language structure.

## Sources

- Chen, W., Ma, X., Wang, X., Cohen, W. W. (2022) — "Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks" (arXiv:2211.12588; TMLR 2023). Primary source.
- Gao, L., Madaan, A., Zhou, S., Alon, U., Liu, P., Yang, Y., Callan, J., Neubig, G. (2022) — "PAL: Program-aided Language Models" (arXiv:2211.10435; ICML 2023). The structurally-identical contemporaneous formulation.
- LangChain documentation — `langchain_experimental.pal_chain.base.PALChain` reference.
- Promptingguide.ai — PAL technique page (practitioner walkthrough of the prompt format).
- E2B and LLM Sandbox documentation — the de-facto V8 substrates used to deploy PoT in production.
