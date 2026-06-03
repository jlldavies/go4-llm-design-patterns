# S4 — Instruction Decomposition

> Break a complex instruction into explicit, numbered, sequential steps inside a single prompt, so the model executes them in order rather than collapsing a dense paragraph of requirements into a single best-effort pass.

**Also Known As:** Step Prompting, Numbered Steps, Chain Instructions, Recipe Prompting.

**Classification:** Category I — Signal · the prompt-level instance of *ordered execution* — one LLM call carrying an ordered step list, the cheapest rung of a three-rung ladder that climbs to **O2 Prompt Chaining** (multi-call) and **R3 Plan-and-Solve** (plan + execute as separate calls).

---

## Intent

Replace a dense, unstructured instruction with an explicit numbered procedure inside a single prompt, so the model performs each step in order, no step is silently skipped, and the failure mode of any miss is localisable to a specific step.

## Motivation

Language models read instructions left-to-right but attend non-linearly. A long paragraph that piles up requirements — *"validate the input, then transform the records, then summarise, but only if there are at least three, and format as JSON, and do not include personally identifiable fields"* — gets read into a single soft objective. The model satisfies what it can attend to and quietly drops the rest. The failure is not a refusal but a silently incomplete answer: format right, validation skipped; PII filter missed; transformation half-done. The mechanism is the U-shaped recall distribution over context position (Liu et al. 2024, mechanism 4): K-vectors in the middle of a long prompt are geometrically accessible but statistically under-attended due to learned recency and primacy biases in the Q-K projection matrices. A dense paragraph places all requirements at roughly equal positions; numbering them creates discrete positional anchors the model can attend to individually. This is not merely a cognitive-metaphor claim — it has a direct counterpart in KV-space: numbered items create local Q-K alignment between the step-instruction token and the step-execution position.

The fix is the cheapest piece of structure available: number the steps. A numbered list does three things a paragraph cannot. It forces an ordering the model honours by training (countless cookbook, recipe, and tutorial documents in pre-training establish "1, 2, 3" as a sequence the reader is expected to execute in order). It makes each requirement separately addressable, so the model cannot conflate two steps into one. And it makes auditing tractable — when output is wrong, the auditor (human or LLM-as-Judge) can point to the step that was dropped.

S4 is the *prompt-level* solution to ordered execution. Two stronger rungs exist for harder cases. **O2 Prompt Chaining** breaks the steps into separate LLM calls with state passed between them — strictly more expressive (each step has its own setup, model choice, and quality gate) but strictly more expensive (multiple calls, more wiring, harder caching). **R3 Plan-and-Solve** lifts ordering into a separate planning call that produces the step list, then executes it — appropriate when the steps are not known upfront. S4 is the right choice when the step sequence is fixed, short, and interdependent, and one call is enough.

## Applicability

Use Instruction Decomposition when:

- the task has a clear sequential process (validate $\to$ transform $\to$ format $\to$ output) and you can enumerate the steps at design time;
- previous single-instruction prompts produced output that skipped requirements or fused steps;
- steps are short enough that one model context can hold all of them with room for the data;
- you need auditability — to point at *which* step was dropped when output is wrong;
- the steps are interdependent and pass simple state (each next step trivially uses the previous result) — no quality gate between them is needed.

Do not use when:

- you need to inspect, log, or gate between steps — choose **O2 Prompt Chaining**;
- individual steps need different models, different setups, or different temperatures — choose **O2**;
- the step list itself depends on the input and cannot be written at design time — choose **R3 Plan-and-Solve**;
- a step requires tool use or external action mid-sequence — choose **R4 ReAct**;
- steps are independent and can run in parallel — choose **O4 Parallelization**;
- the prompt is already short and a single zero-shot instruction works — stay with **S1 Zero-Shot**.

## Decision Criteria

S4 is right when the steps are known, fixed, short, and need to run in order inside a single call.

**1. Count the steps.** S4 scales to ~3–7 numbered steps in one prompt. Below 3, S1 / S6 suffices — numbering adds noise without value. Above 7, comprehension degrades and you should split into **O2 Prompt Chaining** or restructure with **R3 Plan-and-Solve**.

**2. Measure the skip rate.** On a labelled test set, count the % of outputs that miss at least one requirement when phrased as paragraph prose. A skip rate above ~10% justifies numbering. If skip rate is already near zero, S4 buys nothing — leave the prompt alone.

**3. Test the inter-step state.** Can each next step use the previous step's result with no transformation, gate, or branching? If yes, S4. If a step needs to be parsed, validated, or routed before the next, you need a *boundary* between steps — choose **O2**.

**4. Check the audit need.** Do you need to log, store, or human-review what happened at each step? S4 cannot give you that — the steps are internal to one model turn. Need it $\to$ **O2** (each step a separate call, each loggable). Don't need it $\to$ S4.

**5. Pair with an output contract.** S4 should almost always specify, in its final step, the exact output format. Otherwise the model conflates "do the steps" with "show the working", and emits noisy intermediate state. Compose with **S6 Output Template** to lock the final form.

**Quick test — S4 is the right pattern when:**

- the step list is fixed and enumerable at design time, *and*
- there are roughly 3–7 steps, *and*
- no inter-step inspection, gating, or routing is needed, *and*
- the final output format is specified (typically via S6).

If any condition fails: too many steps or inter-step inspection needed $\to$ **O2 Prompt Chaining**; step list depends on the input $\to$ **R3 Plan-and-Solve**; steps need tools mid-sequence $\to$ **R4 ReAct**; steps are independent $\to$ **O4 Parallelization**.

## Structure

```
   single prompt
   ┌────────────────────────────────────────┐
   │ system / role (optional, e.g. S3)      │
   │                                        │
   │ "Complete the following steps in order:"│
   │   1. <step 1 instruction>              │
   │   2. <step 2 instruction>              │
   │   3. <step 3 instruction>              │
   │   ...                                  │
   │   N. emit final output as <S6 form>    │
   │                                        │
   │ input data                              │
   └───────────────────┬────────────────────┘
                       │
                       ▼
                 single LLM call
                       │
                       ▼
              output (final step only)
```

One prompt, one model call. The steps live *inside* the prompt; the model's job is to execute them in order and return only what the final step asks for.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Step List** | the ordered, numbered procedure inside the prompt | task analysis $\to$ enumerated steps | be unbounded — more than ~7 steps overwhelms a single call; split into **O2** instead. |
| **Output Contract** | what the final step must emit, and only that | step N specification $\to$ format rule | leave intermediate steps' output unconstrained — without this the model dumps working state. Usually delegated to **S6 Output Template**. |
| **Prompt Author** | composing Step List + Output Contract + input into one prompt | requirements $\to$ prompt string | invent steps that depend on external state, tools, or branching — those need **R4**, **O2**, or **R3**. |
| **Model (single call)** | executing the steps in order and emitting the final result | prompt $\to$ answer | be asked to log, return, or expose intermediate-step results unless the contract explicitly says so. Mixing audit output with final output defeats S6. |

Four narrow roles. The pattern's discipline is in the Step List (correctly ordered and bounded) and the Output Contract (final step only). Everything else is a single ordinary call.

## Collaborations

The Prompt Author analyses the task and writes the Step List as a numbered enumeration: each step a single imperative clause, ordered by dependency, with no step requiring information unavailable at the time it runs. The final step names the Output Contract — typically by pointing at a template from **S6**. The whole prompt is composed: optional role (**S3**), optional constraints (**S5**), Step List, input data, Output Contract. The Model executes the steps in a single call and emits the final-step result. If the answer is wrong, the auditor reads the model's output against the Step List and identifies which step was dropped or misordered — that diagnostic is the pattern's compliance benefit.

## Consequences

**Benefits**
- Higher compliance than paragraph prose — fewer silently-skipped requirements.
- One LLM call: latency and cost are the same as a single zero-shot prompt.
- Auditable failure: when output is wrong, the dropped step is usually identifiable.
- Composes trivially with S3 (role), S5 (constraints), S6 (output template), S2 (few-shot demonstrating the procedure).
- Cheap to author and revise — editing a numbered list is faster than restructuring a chain.

**Costs**
- Verbose: the prompt grows linearly with the number of steps.
- No inter-step inspection — you cannot see, log, or gate the intermediate results.
- Cannot mix models or settings across steps; one call, one configuration.
- The model decides internally how to allocate attention across steps — long step lists degrade.

**Risks and failure modes**
- *Step fusion* — the model collapses two adjacent steps into one when they look similar, producing a single composite step's output and silently dropping the other.
- *Step skipping* — long step lists (>~7) get partially attended; later steps suffer more than earlier ones. The mechanism is lost-in-middle (mechanism 4): steps 4–7 in a long list occupy mid-context positions that are geometrically under-attended, producing the characteristic pattern where early and late steps complete while middle steps drop. The ~7-step cap is a practical bound on this effect.
- *Order violation* — the model executes steps in semantic, not numbered, order, especially when the numbered order is non-obvious from the data.
- *Working-state leak* — without an explicit Output Contract, the model emits intermediate-step output ("Step 1: ..., Step 2: ...") instead of only the final result.
- *Constraint drift in later steps* — a constraint named in step 1 is forgotten by step 5; pair with **S5 Constraint Framing** restated at the top, not buried in step 1.

## Implementation Notes

- Keep each step to a single imperative clause. *"Validate"*, *"transform"*, *"summarise"* — one verb per step.
- Put hard constraints in a separate constraints block above the step list (S5), not inside step 1. Constraints buried in step 1 attenuate by step 5.
- Always specify the final-step output format. Either reference an **S6 Output Template** or describe the format explicitly ("Output: a single JSON object with fields x, y, z").
- The phrase "Output only the result of step N" at the end of the prompt is load-bearing — without it, models leak working state.
- If you find yourself writing more than ~7 steps, restructure: either merge adjacent steps, split the task, or upgrade to **O2 Prompt Chaining** so each step gets its own call.
- Few-shot the procedure (**S2**) once if step adherence is critical — one example showing the full sequence dramatically improves compliance.
- Combine with **S9 Constitutional Framing** when steps include compliance or safety checks; principles override the step list when they conflict.
- If a step needs to *decide* between branches, the prompt is no longer S4 — it is a single-call routing pattern, and you likely want **O3 Routing** or **O2**.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** S4 lives entirely inside a single LLM session. It composes naturally with **S3 Persona** (role at the top), **S5 Constraint Framing** (a constraints block above the step list), **S6 Output Template** (the final-step contract), and optionally **S2 Few-Shot** (one worked example of the procedure). The upgrade path when boundaries are needed is **O2 Prompt Chaining**; the planning-cousin at agent scope is **R3 Plan-and-Solve**.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Assemble prompt: role + constraints + numbered step list + input + output contract | `code` | S3, S5, S6 |
| 2 | Single LLM call — model executes all numbered steps in order | `LLM` | Procedural session |
| 3 | Optional: validate the final-step output against the S6 contract | `code` (or rule) | S6 |

**Skeleton** — the wiring is trivial; the engineering is in the prompt itself:

```
instruction_decomposition(task, input):
    prompt = compose(
        role         = persona(),                      # code — S3
        constraints  = constraints_block(),            # code — S5
        steps        = numbered_step_list(task),       # code — S4 step list
        input        = input,                          # code
        output_form  = output_template(),              # code — S6
    )
    answer = Procedural(prompt) ────────────────────── # LLM
    validate(answer, schema=output_template())         # code (optional)
    return answer
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Procedural** | the task's normal generalist — no special model needed | role (S3, if any); constraints (S5); the numbered step list; the output contract (S6); the instruction *"Complete the following steps in order. Output only the result of the final step."* | the input data the steps operate on |

Concretely, the per-call prompt looks like:

```
You are <role>.

CONSTRAINTS:
- <constraint 1>
- <constraint 2>

Complete the following steps in order:
1. <step 1>
2. <step 2>
3. <step 3>
4. <step 4>
5. Emit the result as: <S6 template>

Output only the result of step 5.

Input:
<data>
```

**Specialist-model note.** None — a capable generalist suffices. The pattern's lift comes from prompt structure, not model capability. The artifact that does the heavy lifting is the numbered step list itself, paired with the final-step output contract (**S6**). If the model used cannot reliably follow a 5-step numbered procedure in one call, the right move is not a specialist but to split into **O2 Prompt Chaining** so each step gets its own call.

## Open-Source Implementations

Instruction Decomposition is a prompt-engineering convention, not a library — there is no canonical project. The relevant references are practitioner cookbooks and prompt-engineering catalogs:

- **OpenAI Cookbook** — [`github.com/openai/openai-cookbook`](https://github.com/openai/openai-cookbook) — many examples use numbered-step prompts as the default structure for non-trivial tasks; the "techniques to improve reliability" guide explicitly recommends breaking complex tasks into ordered steps within a single prompt.
- **Anthropic Cookbook** — [`github.com/anthropics/anthropic-cookbook`](https://github.com/anthropics/anthropic-cookbook) — prompt-engineering examples include numbered-step patterns for multi-stage tasks, and the Claude documentation's "Chain prompts" guidance distinguishes single-prompt step decomposition (S4) from multi-call chaining (O2).
- **Prompt Engineering Guide** — [`github.com/dair-ai/Prompt-Engineering-Guide`](https://github.com/dair-ai/Prompt-Engineering-Guide) — community catalog including step-by-step / decomposition patterns; useful as a teaching reference.
- **LangChain prompt templates** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — the `PromptTemplate` mechanism is the most common production substrate for parameterised numbered-step prompts; the library does not enforce the pattern but most production agents use it for S4-shaped prompts.

For the *boundary cases* — when you need step-by-step with inspection — the canonical implementations are the **O2 Prompt Chaining** references (LangChain LCEL, LangGraph linear graphs).

## Known Uses

- **Coding assistants** (Cursor, Claude Code, Copilot prompts) — system prompts routinely use numbered procedural steps for code-edit tasks: *"1. Read the file. 2. Identify the change. 3. Emit the edit in this format."*
- **Document-processing pipelines** — extraction-then-validation-then-format tasks are commonly implemented as single S4 prompts when the document fits in context.
- **Customer-service agent prompts** — published assistant system prompts (Anthropic, OpenAI cookbook examples) routinely use 4–6 numbered procedural steps for triage workflows.
- **Constitutional / safety check prompts** — *"1. Identify the user's request. 2. Check against principles. 3. Respond or refuse."* — the canonical inference-time pattern for self-checking outputs.
- **Evaluation rubrics** (LLM-as-Judge prompts) — graders are typically given numbered criteria and instructed to score each in order; S4 in evaluation form.

## Related Patterns

- **Upgrades to** **O2 Prompt Chaining** — when steps need inter-step inspection, gating, different models, or logging, lift each step into its own LLM call. O2 is strictly more expressive and strictly more expensive; S4 is the cheaper default when boundaries are not needed.
- **Sibling at agent scope of** **R3 Plan-and-Solve** — R3 is the planning-cycle cousin: a separate Planner call produces the step list, an Executor call (or chain) runs it. S4 is the prompt-level instance where the step list is *authored* at design time; R3 is the agent-level instance where the step list is *generated* at runtime.
- **Distinct from** **R4 ReAct** — ReAct interleaves thought + action + observation calls; S4 has no actions, no observations, and no iteration. If a step needs to call a tool, S4 is the wrong pattern.
- **Distinct from** **O4 Parallelization** — O4 runs independent steps concurrently; S4 runs ordered steps sequentially in one call. They solve different problems and compose: an S4 prompt may sit inside one branch of an O4 fan-out.
- **Pairs with** **S3 Persona** — role at the top of the prompt frames the procedure.
- **Pairs with** **S5 Constraint Framing** — constraints block above the step list survives long step lists better than constraints buried in step 1.
- **Pairs with** **S6 Output Template** — the final-step output contract; without it the model leaks working state.
- **Pairs with** **S2 Few-Shot** — one fully-worked example of the procedure substantially lifts step-adherence on borderline-capable models.
- **Composes with** **V15 LLM-as-Judge** — when audit is needed without paying for O2, an S4 prompt with a final "self-check" step approximates inline review (lower fidelity than V15 proper, but free).

## Sources

- White, J., Fu, Q., Hays, S., et al. (2023) — "A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT" (PLoP). The "Recipe Pattern" and "Output Customization" patterns are the formal antecedents of S4.
- Wei, J., Wang, X., Schuurmans, D., et al. (2022) — "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." CoT is the *intra-step* relative of S4 (think step-by-step inside one call); S4 generalises the move to explicit numbered procedural steps.
- Khot, T., Trivedi, H., Finlayson, M., et al. (2022) — "Decomposed Prompting: A Modular Approach for Solving Complex Tasks" (arXiv 2210.02406). Establishes decomposition as a primitive in prompt engineering.
- Weng, L. (2023) — "Prompt Engineering" survey, lilianweng.github.io — discusses instruction decomposition and its position relative to CoT and chain-of-prompts approaches.
- Anthropic — "Chain complex prompts" prompt-engineering documentation; distinguishes single-prompt step decomposition (S4) from multi-prompt chaining (O2).
- OpenAI — "Techniques to improve reliability" cookbook; recommends numbered step breakdowns for non-trivial tasks.
- *12-Factor Agents* — Factor 8 ("Own Your Control Flow") frames the same move at system level: making the execution order explicit rather than implicit.
