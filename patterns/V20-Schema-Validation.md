# V20 — Output / Schema Validation

> Validate every model output against a declared schema and, on failure, re-prompt the model with the validation error until the output conforms or a retry budget is exhausted.

**Also Known As:** Output Validation, Schema-Validated Generation, Validate-and-Repair, Reask Loop, Structured-Output Retry.

**Classification:** Category V — Reliability · Band V-B Operational Reliability · the *output-conformance* pattern — the runtime check that the model produced what S6 asked for.

---

## Intent

Treat every generated output as untrusted with respect to its declared shape, validate it against that shape, and recover from non-conformance with a bounded retry loop that carries the validation error back to the model — so downstream code never sees a malformed payload.

## Motivation

S6 Output Template tells the model what shape to produce. V20 is what runs when the model produces something else anyway. The two are paired but distinct: S6 is a prompt-side discipline ("here is the skeleton"); V20 is a runtime guarantee ("nothing leaves this step until it matches the skeleton").

Three failure modes make V20 a first-class pattern rather than a footnote on S6:

- **Schema-constrained decoding is not always available.** Provider-native JSON-mode (OpenAI Structured Outputs, Anthropic tool-use schemas) constrains the decoder and so guarantees syntactic conformance — but only for the calls and providers where it is supported, and only at the syntactic level. Outputs that mix narrative and structure, free-text-template variants of S6, local models without grammar-constrained decoding, and any older model all return a string that may or may not match the schema. Validation is the only thing that catches the difference.
- **Syntactic validity is not semantic validity.** A response that parses as JSON of the right shape can still violate cross-field invariants (`end_date < start_date`), domain constraints (`country` not in ISO 3166), or business rules (`total ≠ sum(line_items)`). A Pydantic / Zod / JSON Schema validator catches the first kind for free; custom validators catch the second; both belong inside this pattern.
- **Models fail more on edge cases than on average.** Aggregate parse-failure rates of 1–5% under S6 hide a long tail where the same prompt fails repeatedly on a particular input — a missing enum value, an unusually long string, a tool call whose arguments are subtly wrong. The fix is not "make the prompt stronger" indefinitely; it is to detect the failure and ask again, with the error in hand. The mechanistic root is stochastic sampling: schema-conformant output is an emergent pattern from training, not an architectural guarantee. On inputs that shift the probability distribution away from the training-distribution region where formatting was reinforced, the model samples from a distribution where format-violating tokens receive non-trivial probability mass (mechanism 7). This is why format failure correlates with input rarity — unusual inputs push the distribution toward under-trained regions.

V20 is the named, bounded version of the reask loop that every production extraction pipeline ends up writing. The pattern is one validator, one error-carrying re-prompt, one retry cap, one fallback. It is distinct from V5 Guardrail Layering (which checks for *safety / policy* violations, not *structural correctness*) and from V15 LLM-as-Judge (which evaluates *quality* against a rubric, not *conformance* against a schema). The three pair cleanly: V20 guarantees the output is the right *shape*, V5 guarantees it is *safe*, V15 evaluates whether it is *good*.

## Applicability

Use Schema Validation when:

- the output is consumed by code (parsed, persisted, sent to another API), or by a chained LLM call that depends on a stable shape;
- the schema includes semantic invariants beyond syntactic structure (enums, cross-field rules, domain ranges);
- the runtime cannot rely on schema-constrained decoding for every call (free-text S6, mixed structured + narrative, providers without strict JSON mode, local models without grammar-constrained decoders);
- malformed payloads must never reach the downstream system, even at the cost of an extra round-trip.

Do not use when:

- the output is free prose for a human reader — there is no schema to validate against; use **S1 Zero-Shot**;
- the provider's schema-constrained decoder fully guarantees the schema *and* the schema has no semantic invariants — the validator would be a no-op (still use S6 with the JSON-mode variant);
- the quality of the answer is the concern, not its shape — use **V15 LLM-as-Judge**;
- the safety or policy compliance of the answer is the concern — use **V5 Guardrail Layering**;
- retries are not affordable on the latency budget — fail fast and surface to **V1 Human-in-the-Loop**.

## Decision Criteria

V20 is right when shape failure is a real event and a single targeted retry recovers most of them.

**1. Measure the parse-and-validate failure rate.** Run N production-representative calls through S6 *without* V20. Count outputs that fail (a) JSON parsing, (b) schema validation, or (c) custom invariants.
- **< 1%** — V20 still pays back (cheap insurance), but a hard-fail-and-log path may suffice. Skip the retry loop and surface to **V1**.
- **1–10%** — V20 is the right default; the retry loop pays for itself.
- **> 10%** — V20 alone is treating a symptom. Fix S6 (the skeleton is under-specified) or the model choice first; V20 catches what remains.

**2. Pick the validator stack.** Pydantic (Python), Zod (TypeScript), JSON Schema (language-neutral). The validator is the source of truth — the schema in the prompt is rendered *from* it, never the other way round.

**3. Set the retry budget.** Hard cap: typically **1–3** retries. The first retry recovers most failures; the second catches a few more; the third rarely helps. Pair with **V9 Bounded Execution** — never an unbounded reask loop.

**4. Decide the fallback.** When all retries fail, what happens? Options: (a) raise a typed exception the caller handles; (b) escalate to **V1 Human-in-the-Loop** with the bad output and the error; (c) emit a sentinel record and log to **V14 Trajectory Logging** for offline triage. Choose by the consequence of a missing record, not by what is easiest.

**5. Decide where decoder-constraint sits.** If the provider supports schema-constrained decoding for the call, use it (S6 JSON-mode variant). V20 still validates afterwards — for semantic invariants and for the calls where the decoder constraint cannot be applied. The decoder is the strong defence; V20 is the catch-net.

**Quick test — V20 is the right pattern when:**

- output is consumed by code or a chained LLM step, *and*
- the schema carries semantic constraints beyond JSON syntax (enums, cross-field rules, domain ranges) *or* the runtime cannot guarantee decoder-constrained generation, *and*
- a single error-carrying retry recovers a meaningful share of failures (measured, not assumed), *and*
- the retry budget is bounded and the fallback is defined.

If schema-constrained decoding *fully* covers the call and the schema has no semantic invariants, S6's JSON-mode variant alone suffices. If the failure rate is dominated by quality not shape, V15 is the right pattern. If the failure rate is dominated by safety not shape, V5 is.

## Structure

```
  Task input ──▶ Generator (LLM) ──▶ raw output
                                         │
                                         ▼
                              Parser (JSON / text)
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                           parse fail           parse ok
                              │                     │
                              │                     ▼
                              │           Schema Validator
                              │            (Pydantic / Zod / JSON Schema)
                              │            + custom invariants
                              │                     │
                              │         ┌───────────┴───────────┐
                              │         ▼                       ▼
                              │   validation fail         validation ok
                              │         │                       │
                              └────┬────┘                       ▼
                                   ▼                       Typed object
                       Retry budget left?                  → downstream
                            │      │
                          yes      no
                            │      │
                            ▼      ▼
            Reask: original prompt    Fallback:
            + bad output              raise typed error,
            + validator's error       or escalate to V1,
            ─▶ Generator (LLM)         or log + sentinel
            (loop, capped by V9)
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Schema** | the canonical declaration of shape and invariants | — → schema object | live in two places — the prompt skeleton (S6) and the validator must be rendered from the same source. Drift between them is the pattern's most common failure. |
| **Generator (LLM)** | producing the candidate output | prompt → string | be trusted to self-check; that is the validator's job. A generator that "knows" its output is valid still produces invalid output on a non-trivial slice of inputs. |
| **Parser** | string → structured object (JSON / YAML / tagged blocks) | raw output → parsed value or parse error | swallow parse errors silently; a parse error is a validation event and must enter the retry loop with its message intact. |
| **Schema Validator** | enforcing structural and semantic conformance | parsed value + schema → typed object or validation error | be lenient about "minor" deviations; lenient validators hide drift and let malformed payloads reach downstream code. |
| **Reask Step (LLM)** | one targeted retry per failure, carrying the error | original prompt + bad output + error → corrected string | be a different conversation — the reask must reference the original prompt and the validator's exact error, not a paraphrase. |
| **Retry Budget** | the hard cap on reask rounds | round count → continue or fall back | be unbounded; an unbounded reask loop is a production incident waiting to happen (compose with **V9**). |
| **Fallback** | the defined exit when retries are exhausted | last bad output + error → exception / human escalation / sentinel | be implicit — every V20 deployment must declare what happens on terminal failure. |

The Schema and the Parser-plus-Validator are the read and write sides of the same artefact. The Reask Step and the Generator share a model but are *different sessions* — the reask carries different setup (its role is *correct this output*, not *answer the task*).

## Collaborations

The Generator produces a candidate string. The Parser converts it into a structured value, or raises a parse error. On success, the Schema Validator runs both schema-level checks (types, required fields, enums) and any custom invariant checks (cross-field rules, domain constraints). On any failure — parse or validation — the loop checks the retry budget; if rounds remain, it composes a Reask prompt that carries the original task, the bad output, and the validator's exact error message, and sends it back to the Generator. The cycle repeats up to the cap. When the budget is exhausted, the Fallback fires: a typed exception, a V1 escalation, or a logged sentinel. Every loop event — generation, parse, validation, retry, fallback — is emitted to V14 Trajectory Logging.

## Consequences

**Benefits**

- Guarantees downstream code never sees a malformed payload — the typed object that escapes V20 is structurally and semantically valid by construction.
- Recovers from most format failures with a single targeted retry — measurably cheaper than upgrading the model or enriching the prompt.
- Catches schema drift early: a sudden rise in validation failures is a leading signal that the prompt, the model, or the schema has changed.
- Captures the failure mode in a structured form (the validator's error), making it easy to triage and to feed back into S6 improvements or V16 Offline Eval regression cases.

**Costs**

- Adds 0–N extra LLM calls per request — typically 0, occasionally 1–3 on failures.
- Latency increases on the failure tail; the p99 of any V20-wrapped step is N times the p50 where N is the retry cap.
- Maintenance: the schema and the prompt skeleton must stay in lockstep, or the validator rejects outputs the prompt encouraged.
- A poorly-written reask prompt can drag the model further from the right answer rather than closer — empty retries are dead weight.

**Risks and failure modes**

- *Schema-prompt drift* — the validator and the skeleton fall out of sync; the model produces what the prompt asked for, the validator rejects it; retries cannot recover.
- *Reask cargo-culting* — the same bad output is re-submitted unchanged because the reask prompt does not actually carry the error message to a position the model attends to.
- *Forced-field syndrome at scale* — validators that require fields the model has no evidence for force the model to invent values; allow nullable / unknown explicitly in the schema (see S6 Implementation Notes).
- *Silent retry burn* — the loop succeeds eventually but only after expensive retries on a non-trivial share of traffic; without V14 logging of retry counts, the cost is invisible until the bill arrives.
- *Validation as safety theatre* — the validator passes syntactically conformant outputs that violate business rules because the rules were not encoded as invariants. V20 only catches what the schema declares.

## Implementation Notes

- **One schema, two renderings.** Define the schema once (Pydantic / Zod / JSON Schema). Render the prompt skeleton from it (S6) and pass the same schema to the validator. A code generator or a single source-of-truth file prevents drift.
- **Use schema-constrained decoding where you can.** The S6 JSON-mode variant (OpenAI Structured Outputs, Anthropic tool-use schemas, Outlines, Guidance, Instructor) eliminates a whole class of failures at the decoder. V20 then handles only semantic invariants and the calls the decoder cannot constrain. The two are complementary, not alternatives.
- **The reask prompt must carry the error verbatim.** "Your previous output failed validation: `<exact validator error>`. Fix the output to match the schema; change as little as possible." Paraphrasing the error degrades the recovery rate. The validator error should appear at the *end* of the reask prompt, immediately before the generation boundary, to benefit from recency bias — RoPE positional encoding assigns stronger attention weights to tokens at smaller relative distances to the current query position (mechanism 12). Placing the error deep in a long context before the bad output buries it in the geometrically weak mid-context zone (mechanism 4).
- **Cap the retry budget.** 1–3 retries is typical. Pair with **V9 Bounded Execution** to enforce the cap and surface terminations.
- **Encode invariants explicitly.** Cross-field rules, enum membership, range constraints, format rules (ISO-8601 dates, ISO 3166 country codes). The validator only catches what is declared; undeclared invariants leak through.
- **Allow `null` / `unknown` / `n/a` where the model may legitimately lack evidence.** Forced-field syndrome (S6) is V20's main quality cost — required fields with no nullable option force fabrication.
- **Log every validation event to V14.** Generation, parse, validation, retry, fallback. The failure-and-retry rate is one of the highest-signal production-quality metrics available.
- **Define the fallback explicitly.** Typed exception, V1 escalation, or sentinel record. "Hope it doesn't happen" is not a fallback.
- **Treat the failure modes as data.** Validator errors that recur across inputs are a signal to fix the prompt skeleton, the schema, or the model choice — not to bump the retry cap.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V20 wraps S6 Output Template's Generator with a parse-validate-reask loop. The reask loop is bounded by **V9 Bounded Execution**, the events are emitted to **V14 Trajectory Logging**, and the terminal-failure fallback typically escalates to **V1 Human-in-the-Loop**. The schema artefact is shared with S6; the validator stack (Pydantic / Zod / JSON Schema) is the source of truth that S6's skeleton is rendered from.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Define the schema (Pydantic / Zod / JSON Schema) — single source of truth | `code` | S6 schema artefact |
| 2 | Render the prompt — bind task input + render skeleton (or attach schema to API) | `code` | S6 |
| 3 | Generate candidate output | `LLM` | Generator session |
| 4 | Parse the string into a structured value | `code` | |
| 5 | Validate (schema + custom invariants) | `code` (or `LLM` for semantic invariants) | |
| 6 | Branch — valid → return; invalid + budget left → step 7; invalid + budget exhausted → step 9 | `code` | V9 cap |
| 7 | Compose reask prompt (original prompt + bad output + validator error) | `code` | |
| 8 | Re-generate; loop to step 4 | `LLM` | Reask session |
| 9 | Fallback — raise typed error / escalate to V1 / emit sentinel | `code` | V1, V14 |

**Skeleton** — the wiring only; each `# LLM` line is a configured session:

```
generate_validated(task_input, schema, max_retries=2):
    prompt = render_prompt(task_input, schema)          # code — S6
    output = Generator(prompt)                          # LLM
    for attempt in range(max_retries + 1):              # code — V9 bound
        try:
            return validate(parse(output), schema)      # code — typed object out
        except (ParseError, ValidationError) as e:
            log_event(attempt, output, e)               # code — V14
            if attempt == max_retries:
                return fallback(output, e)              # code — V1 / sentinel
            output = Reask(prompt, output, e)           # LLM — error-carrying retry
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Generator** | the system's chosen generator (any capable generalist; schema-constrained decoder if available) | role (S3 where relevant); the schema / skeleton (S6); the rule that placeholders are to be replaced and no extra fields invented; any S5 constraint framing | the task input |
| **Reask** | the same model, or a smaller fast generalist tuned for correction | role: *"correct this output to satisfy the schema; change as little as possible; do not invent new fields; preserve all valid content"*; the schema | the original task input + the bad output + the validator's exact error message |

**Specialist-model note.** No fine-tuned specialist is required. The artefact that does the work is the **schema** and the **validator** — both code, not a model. One runtime dependency does change the architecture: whether the provider supports schema-constrained decoding for the call. If it does, the Generator is configured to use it (S6 JSON-mode variant) and V20 catches only semantic-invariant failures; if it does not, the Generator is unconstrained and V20 catches the full failure surface. Either way the validator and the reask loop are the same.

## Open-Source Implementations

- **Instructor** — [`github.com/567-labs/instructor`](https://github.com/567-labs/instructor) — Pydantic-first structured output with automatic validation and **retry-on-failure across OpenAI, Anthropic, Google, Groq, and Ollama**. The canonical V20 implementation: schema in Pydantic, validate after generation, reask with the error on failure. (Previously hosted at `jxnl/instructor`; current canonical home is `567-labs/instructor`.)
- **Outlines** — [`github.com/dottxt-ai/outlines`](https://github.com/dottxt-ai/outlines) — schema-constrained *decoding* for JSON Schema, Pydantic, regex, and grammars; works with OpenAI, vLLM, Ollama, and local transformers. Sits one layer earlier than V20 (it prevents most failures at decode time), but pairs with V20 for the semantic-invariant layer.
- **Guidance** — [`github.com/guidance-ai/guidance`](https://github.com/guidance-ai/guidance) — guidance language for constrained generation with JSON Schema, regex, and grammars; like Outlines, sits at the decoder layer.
- **OpenAI Structured Outputs** — `platform.openai.com/docs/guides/structured-outputs` — provider-native JSON Schema enforcement via `response_format` with `strict: true`; guarantees syntactic conformance. V20 still validates semantic invariants on top.
- **Anthropic tool-use schemas** — `tools[].input_schema` with JSON Schema in the Messages API — the equivalent provider-native pathway for Claude models.
- **Pydantic** — [`github.com/pydantic/pydantic`](https://github.com/pydantic/pydantic) — the validator stack underlying Instructor and most Python V20 implementations; field validators, model validators, and custom invariants are the V20 schema in code.

## Known Uses

- **Production extraction pipelines** — invoice, contract, form, and resume parsers built on Instructor or OpenAI Structured Outputs, where the validator is the gate between the LLM and the database.
- **Tool-calling agents** — every function-call API is V20 in disguise: the schema is enforced by the provider, the model's arguments are validated before the function runs, and an argument-validation failure triggers a retry with the error.
- **LLM-as-Judge evaluators (V15)** — judge verdicts are returned through V20-wrapped Instructor calls so the verdict, score, and rationale fields are guaranteed to load.
- **RAG retrieval-grading pipelines (K5 Adaptive RAG)** — the Quality and Support evaluator outputs (PASS / FAIL with reasoning) are V20-validated so the control branch sees a clean enum, never a freeform sentence.
- **Workflow agents that hand off between steps** — every O2 Prompt Chaining step validates the previous step's output; this *is* V20 between every pair of steps.

## Related Patterns

- **Pairs with** S6 Output Template — S6 is the prompt-side skeleton; V20 is the runtime guarantee. They share the schema; deploy them together. S6 alone is probabilistic; V20 makes the contract enforceable.
- **Pairs with** V9 Bounded Execution — the reask loop must be capped, or a hard input cascades retries without end.
- **Pairs with** V14 Trajectory Logging — every parse, validate, retry, and fallback event is a signal worth logging; retry-rate is a leading quality metric.
- **Pairs with** V1 Human-in-the-Loop — the natural fallback when retries are exhausted on a high-value record.
- **Pairs with** V11 Error Compaction — the validator error carried into the reask prompt should be compact and specific, not a raw stack trace.
- **Distinct from** V5 Guardrail Layering — V5 checks for *safety / policy* violations at four points in the pipeline; V20 checks for *structural and semantic conformance* of generated output. Different verdicts, different fallbacks; they compose.
- **Distinct from** V15 LLM-as-Judge — V15 evaluates *quality* against a rubric (was the answer good?); V20 evaluates *conformance* against a schema (is the answer the right shape?). A V15 verdict is itself usually returned through V20 so its rubric fields are guaranteed to load.
- **Distinct from** S6 — S6 is the prompt-side artefact (the skeleton in the prompt or the schema attached to the API); V20 is the runtime check after generation. They are two halves of the same contract; neither replaces the other.
- **Required by** O2 Prompt Chaining — every hand-off in a chained pipeline must validate the previous step's output, or the chain breaks the first time the model rephrases. The chain *is* a sequence of V20-wrapped S6 steps.
- **Required by** I2 Function / Tool Call — every function invocation validates its arguments against the function's input schema before executing; argument-validation failure should re-prompt the model with the error.

## Sources

- Willard & Louf (2023) — "Efficient Guided Generation for Large Language Models" (arXiv 2307.09702) — the Outlines paper; basis for schema-constrained decoding as the strong-defence layer V20 wraps.
- OpenAI (2024) — "Introducing Structured Outputs in the API" and the Structured Outputs guide — provider-native JSON Schema enforcement.
- Anthropic — Tool use documentation, `input_schema` for Claude tool definitions.
- Instructor documentation — Pydantic-first structured output across providers; the canonical reask-on-validation-failure implementation.
- Pydantic documentation — field validators, model validators, custom invariants.
- White et al. (2023) — "A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT" — the *Output Customization* / *Output Template* category that V20 operationalises at runtime.
