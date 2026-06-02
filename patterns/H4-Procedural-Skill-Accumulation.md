# H4 — Procedural Skill Accumulation

> After a task succeeds, distil the trajectory that produced it — the sequence of steps, decisions, and tool calls — into a reusable parameterised skill, store it in a skill library, and retrieve and instantiate matching skills at the start of similar future tasks instead of re-deriving them.

**Also Known As:** Skill Library, LEGO Memory, Memp, Trajectory Distillation, Workflow Memory, Voyager-Style Skill Acquisition.

**Classification:** Category VII — Humanizer · the *learn-from-success* H-pattern. Sibling of **H2 Episodic Self-Improvement** (H2 learns from failure, H4 learns from success). **Requires K10 Long-Term Memory (procedural variant)** as its persistent substrate; **requires H1 Identity Persistence** as the stable self the accumulating skill set belongs to.

---

## Intent

Convert the agent's successful problem-solving work into reusable, parameterised procedures, so the next time a similar task arrives the agent retrieves and adapts a proven skill rather than re-deriving it from scratch — turning one solved task into a permanent capability.

## Motivation

When an agent successfully completes a complex multi-step task, two things happen at once. It produces a *result* (delivered to the user), and it produces a *trajectory* (the sequence of decisions, tool calls, sub-prompts, and corrections that got it there). The result is consumed; the trajectory is, by default, thrown away. The next time a similar task arrives the agent reconstructs the same reasoning from zero — paying the same tokens, the same latency, and the same stochastic variance — token generation is sampling from a probability distribution, so each re-derivation risks sampling a different (worse) path through the same reasoning space (mechanism 7). A retrieved, parameterised skill replaces that sampling step with a deterministic procedure lookup, eliminating variance and reducing context cost.

K10 Long-Term Memory (procedural variant) provides the substrate — a place to write verified procedures and retrieve them by similarity. But K10 alone does not specify *how* a successful trajectory becomes a procedure, *when* distillation runs, *how* the procedure is parameterised so it generalises, or *how it is invoked* at the start of the next task. K10 is the store; H4 is the learning loop that fills it and uses it. Without that loop the procedural store stays empty (or fills with raw episodes that are not usable as skills).

H4 closes that loop. After each task that succeeds, an Extractor isolates the minimal trajectory, a Parameteriser abstracts the task-specific values into placeholders, a Validator checks the proposed skill generalises, and the result is written to the skill library as a named, callable procedure. On the next task, a Retriever searches the library, an Adaptor instantiates parameters for the current context, and an Executor runs the skill — falling back to freeform reasoning if execution fails. The pattern was articulated by Voyager (Wang et al., 2023) in the embodied-agent setting and generalised by Memp (Fang et al., 2025) and Agent Workflow Memory (Wang et al., 2024) for tool-using LLM agents. Coding agents are the canonical contemporary use case: every successful "set up auth, write the test, run it, commit" sequence has the shape of a future skill.

H4 is the **positive-experience** counterpart to H2 Episodic Self-Improvement. H2 distils failure into don't-do-this lessons; H4 distils success into do-this-again procedures. The agent that runs both gets better in both directions.

## Variants

The variants differ in *what scope of trajectory becomes a skill* and *how skills are represented*:

- **Voyager-style executable code skills.** Each skill is a self-contained snippet of code (in Voyager: JavaScript controlling a Minecraft agent) that the agent generates, debugs, verifies, and stores under a descriptive name. The skill *is* code; retrieval surfaces the code; execution runs it. Fits agents whose action space is a programmable interface. The code-skill variant exemplifies mechanism 7 directly: the distilled skill is executable code, and code execution is deterministic — same input, same output, zero sampling variance. This is the strongest form of H4's variance-reduction property. (Wang et al., 2023.)
- **Memp-style procedural memory.** Each successful trajectory is distilled into *both* a fine-grained step-by-step instruction set *and* a higher-level script-like abstraction; the build/retrieval/update strategies are themselves treated as design choices. Includes deprecation: the repository updates and prunes as new experience arrives. Fits tool-using LLM agents on diverse task suites (TravelPlanner, ALFWorld). (Fang et al., 2025.)
- **Agent Workflow Memory (AWM).** Workflows are induced from past action sequences as common sub-routines, with task-specific context abstracted out; works offline (from training trajectories) or online (from the agent's own runs on the fly). Workflows are injected as guiding plans into the next task's context. Fits browser and web agents. (Wang et al., 2024.)
- **LEGOMem (multi-agent).** Past trajectories decompose into reusable modular memory units — full-task memories and subtask memories — allocated across orchestrator and task agents in a multi-agent system. Recombines past sub-procedures LEGO-style for new compositions. Fits orchestrator-worker systems. (Microsoft, 2025.)

All four are the same pattern — *capture the trajectory of a success, abstract it, store it for retrieval, instantiate at the next match* — differing in skill granularity (code blob / dual fine-and-coarse / sub-routine / modular unit) and in the multi-agent allocation question. None adds a structural element the others lack.

## Applicability

Use Procedural Skill Accumulation when:

- the agent performs **recurring task types** where the same shape of work shows up again — code reviews, data transformations, report generation, navigation flows, tool orchestration recipes;
- task-completion **trajectories are long and expensive** (many tool calls, much reasoning), so re-deriving each time is a real cost;
- the environment and the success criterion are **stable enough** that a skill captured today is still valid in N days;
- the task language has **parameterisable shape** — there is a clear "what is the topic / source / target / parameters" axis along which similar tasks vary.

Do not use when:

- tasks are one-shot and never recur — the distillation cost is wasted; use plain **R3 Plan-and-Solve** each time;
- the environment changes faster than skills can be validated — stale procedures actively mislead; rely on **R4 ReAct** with no skill cache;
- success cannot be reliably detected — without a trustworthy success signal, H4 stores noise; build the success signal first (**V15 LLM-as-Judge**, V14 Trajectory Logging, or a deterministic task oracle);
- the procedural store substrate is missing — **K10 Long-Term Memory (procedural variant)** is the prerequisite. Without it, fall back to in-session **K11 Observational Memory** (skills die with the session) or use **R11 Buffer of Thoughts** for in-context skill reuse only.

## Decision Criteria

H4 is right when the same shape of task recurs, success is detectable, and the distillation cost amortises across reuses.

**1. Estimate the recurrence rate.** Across the agent's task stream, count the share of tasks that are structurally similar to a prior task. Practical threshold: if **≥ 20%** of tasks have a structural twin in history, H4 starts paying. Below 10%, the skill library will rarely match — stay with **R3 Plan-and-Solve** per task.

**2. Compute the amortisation.** Distillation costs ~1–3 LLM calls per successful task (Extractor + Parameteriser + Validator). Reuse saves the original task's reasoning tokens. If average reuse per stored skill is ≥ 3, distillation has paid; below 2, the library is bloating with rarely-touched skills and the Retriever's noise floor grows.

**3. Verify the success signal.** Can you tell, automatically or with high reliability, that a task succeeded? Options: deterministic oracle (tests pass, file written, API 200), **V15 LLM-as-Judge**, explicit user confirmation. If the success signal is weak or absent, H4 stores trajectories that *looked* successful and degrades over time; build the signal first or do not deploy H4.

**4. Validate the parameterisation surface.** Pick three recent successes. Can you, by inspection, name the 2–5 parameters that would let the same procedure handle the *next* instance? If yes, the parameterisation surface exists. If not, the task is procedurally singular — either accept skills that overfit to one instance, or rebuild the task with more structure (**S4 Instruction Decomposition** at the input layer).

**5. Bound the library, plan the deprecation.** A skill library grows monotonically unless governed. Set: a size cap, a freshness window (skills not retrieved or re-validated within N days are demoted), a stale-skill detector (skills whose recent invocations failed → quarantine). Pair with **V9 Bounded Execution** on the retrieve-instantiate-execute path so a bad skill cannot loop. Without governance the library becomes a graveyard of obsolete procedures.

**Quick test — H4 is the right pattern when:**

- task recurrence ≥ ~20% with parameterisable structure, *and*
- a reliable success signal exists to gate which trajectories become skills, *and*
- K10's procedural variant (or an equivalent store) is wired in as the substrate, *and*
- library deprecation/governance is in place from day one.

If recurrence is low, choose **R3** per task. If success cannot be detected, build the detector first. If the substrate is missing, deploy **K10 (procedural)** first. If the failure side dominates and you want to avoid repeating mistakes more than to repeat successes, deploy **H2 Episodic Self-Improvement** first — most production systems run H2 and H4 together.

## Structure

```
   AFTER a task succeeds                          AT the start of a similar task
   ─────────────────────                          ──────────────────────────────
   trajectory (steps, tool calls,                  query / task description
    decisions, outcomes)                                  │
            │                                             ▼
            ▼                                      Retriever ── similarity ──▶
   Extractor — minimal successful path                    │       skill library
            │                                             ▼
            ▼                                      [ match? ] ──no──▶ R3 fresh plan
   Parameteriser — abstract task-specific                 │
    values into named parameters                         yes
            │                                             ▼
            ▼                                      Adaptor — instantiate
   Validator — would this generalise?                     │   parameters
            │                                             ▼
            ▼                                      Executor — run skill, V9-bounded
   Skill library (K10 procedural store)                   │
     • named, callable                          ┌─────────┴─────────┐
     • parameter schema                       success            failure
     • exemplar invocations                     │                   │
     • provenance + invocation log              ▼                   ▼
                                          log success         fallback to R3,
                                          + reinforce          flag skill for
                                                              quarantine / revision
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Success Detector** | the verdict on whether a finished task succeeded | task + final state → SUCCESS / FAIL / UNKNOWN | distil on UNKNOWN. A skill built from a maybe-success poisons the library; absence of a verdict must abort distillation. |
| **Trajectory Extractor** | isolating the minimal successful path | full session log → ordered list of load-bearing steps | keep the failed attempts and dead ends — they belong in H2's lesson library, not in a skill. The skill is what *worked*, not what was tried. |
| **Parameteriser** | abstracting task-specific values into named parameters | minimal trajectory → parameterised procedure with parameter schema | over-parameterise. Too many parameters means the skill matches everything and applies to nothing. The Parameteriser's job is to find the *right* abstraction axis, not the maximal one. |
| **Validator** | the verdict on whether the candidate skill generalises | parameterised procedure → ACCEPT / REJECT / REVISE | pass a skill that has not been *re-stated* in general form. A trajectory that still references the original task's specifics is not yet a skill. |
| **Skill Library** | persistent storage of accepted skills with name, parameter schema, exemplars, invocation log | skill writes / queries → matched skills | be unbounded or unaudited. Skills must carry provenance, an invocation log, and a freshness signal — without them, deprecation is impossible. |
| **Skill Retriever** | finding candidate skills for a new task | task description + library index → ranked candidates | return a single answer with no confidence. The Adaptor needs to know whether to trust the match or fall back. |
| **Adaptor** | instantiating the matched skill's parameters for the current task | candidate skill + current task → instantiated procedure | rewrite the skill's structure. Adaptation is parameter substitution; structural edits belong to a new distillation cycle, not to inline mutation. |
| **Executor** | running the instantiated procedure, with bounded recovery and fallback | instantiated procedure → outcome | continue past **V9** bounds; on bound exhaustion or repeated step failure, the Executor must surrender to a fresh **R3** plan and flag the skill for quarantine. |
| **Skill Governor** | deprecation, quarantine, freshness, library hygiene | invocation log + age → keep / demote / retire | rely solely on age. A skill is stale because it *fails*, not because it's old; failure rate is the primary signal, age is the secondary. |

The Extractor / Parameteriser / Validator triad is the **write path** (distillation, post-success). The Retriever / Adaptor / Executor triad is the **read path** (instantiation, at next-task start). The Skill Library and Skill Governor are the shared store and its caretaker. This write/read separation is the same discipline K12 Karpathy Memory enforces between Curator and Agent — and for the same reason: an agent that edits skills mid-task destabilises the library and the in-flight reasoning at once.

## Collaborations

A task completes; the Success Detector emits SUCCESS. The Trajectory Extractor pulls the session log (typically from K11 Observational Memory or V14 Trajectory Logging), prunes failed branches, and produces the minimal successful path. The Parameteriser abstracts task-specific values into named parameters and writes a parameter schema. The Validator inspects the candidate — does it stand on its own? does it generalise? — and ACCEPT/REJECT/REVISE. On ACCEPT, the skill is written to the Skill Library with provenance and an empty invocation log.

A later task arrives. The Skill Retriever queries the library by similarity (typically using K10's similarity-search machinery). On a confident match, the Adaptor instantiates parameters from the current task and the Executor runs the procedure, V9-bounded, with each step's outcome logged. On success, the invocation log records the reuse — reinforcing the skill. On failure, the Executor falls back to R3 Plan-and-Solve for a fresh plan, and the Skill Governor flags the skill for quarantine or revision. On no match, R3 runs from scratch and — if the result succeeds — the write path produces a new skill.

The Skill Governor runs periodically (or on every failure signal): it demotes skills whose recent invocations have failed, retires skills not touched within a freshness window, and surfaces high-conflict skills for human or H5 review.

## Consequences

**Benefits**
- Recurring tasks become progressively cheaper — retrieval replaces re-derivation. This cost reduction is structural: re-deriving a trajectory requires holding the full reasoning chain in context (O(n²) attention cost, mechanism 2); executing a retrieved skill operates on a shorter context (mechanism 6). The savings grow with trajectory length. In Voyager-style code-skill variants, execution is fully deterministic (mechanism 7) — no sampling variance at all, not merely reduced variance.
- Institutional procedural knowledge — *how to do X here* — outlives any single session.
- Compounds with H2 Episodic Self-Improvement: H4 captures successes, H2 captures failures; together they are inference-time learning without weight updates (mechanism 10).
- Multi-agent systems get distributable skills — one agent's success becomes the system's capability.

**Costs**
- Each successful task pays a distillation tax — 1–3 LLM calls for Extractor + Parameteriser + Validator.
- The library is now a first-class asset: storage, retrieval, governance, deprecation.
- Retrieval and adaptation sit on the critical path of every new task; cheap, but not free.
- Schema and parameterisation discipline matter — sloppy distillation produces an unusable library.

**Risks and failure modes**
- *Skill poisoning* — a trajectory that finished but did not actually succeed is distilled, embedding wrong behaviour. The Success Detector is the defence; weak detection turns H4 into a corruption engine.
- *Over-generalisation* — the Parameteriser strips so much that the skill applies to tasks it should not match. Defence: stricter parameter-schema typing, Validator examples.
- *Stale skills* — environment changes (an API, a library version, a website layout) silently invalidate skills. Defence: freshness windows, invocation-failure detection, and explicit re-validation triggers.
- *Library bloat* — every success writes; without deprecation the library becomes noise. Defence: the Skill Governor.
- *Adapter drift* — the Adaptor rewrites a skill mid-execution to fit the task, accumulating mutations into the library. Defence: adaptation is parameter substitution only; structural changes go through a new distillation cycle.
- *Cascading retrieval* — the Retriever surfaces a wrong skill, the Executor fails, the system retrieves another wrong skill, and so on. Defence: pair with **V9 Bounded Execution**, cap retrieval-then-fallback to a single retry before R3.

## Implementation Notes

- **Bootstrap from H1 + K10.** The skill library sits in K10's procedural store; the agent's identity and outstanding-capabilities pointer lives in H1. Deploy both before H4.
- **Trust the success signal or do not deploy.** The pattern's reliability is bounded by the quality of the Success Detector. For coding agents: tests pass / build green / commit accepted. For research agents: V15 LLM-as-Judge against a rubric. For tool agents: deterministic post-conditions. If the signal is fuzzy, H4 will degrade the system over time, not improve it.
- **Parameterise with intent.** A small, named parameter schema is better than a long one. The right test: a human reading the skill's name and parameter list should know whether it applies to a new task, without reading the procedure body.
- **Treat the Parameteriser as the quality lever.** A capable generalist model produces far better skills than a small fast one — the cost is paid once per success, not per turn. Spend on the Parameteriser.
- **Separate skill execution from skill mutation.** The Executor runs; the Distillation chain writes; never let the Executor edit the skill. If a skill needs to change, the next success against that skill's task triggers a re-distillation that *replaces* it under governance.
- **Invocation log earns its keep.** Every retrieve-and-execute event is logged with task, parameter values, success/failure, and tokens consumed. The log feeds the Skill Governor's deprecation decisions and is the only honest signal for which skills earn their place.
- **Pair with H2 from day one in production.** H4 alone learns only from success; in any non-trivial domain, the failure side matters as much. The same trajectory infrastructure feeds both.
- **Coding-agent specifics.** For code agents the natural skill granularity is *a function plus a usage exemplar plus a test*. Voyager's executable-code-skills approach maps directly; Memp's dual fine/coarse layering helps when the same task can be done at multiple levels of abstraction.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** H4 chains a **distillation pipeline** (post-success) with an **instantiation pipeline** (next-task start), backed by **K10 Long-Term Memory (procedural variant)** as the store and gated by a Success Detector that is typically **V15 LLM-as-Judge** or a deterministic oracle. The Executor is V9-bounded. Activity input typically comes from **K11 Observational Memory** or **V14 Trajectory Logging**. H4 is naturally paired with **H2 Episodic Self-Improvement** (same trajectory feed, opposite polarity).

**The chain — distil (after success):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| D1 | Success Detector verdict | `LLM (or rule)` | V15 LLM-as-Judge / oracle |
| D2 | Gather trajectory: ordered steps, decisions, tool calls, outcomes | `code` | K11 / V14 |
| D3 | Extractor — prune to the minimal successful path | `LLM` | Extractor session |
| D4 | Parameteriser — abstract task-specific values into a parameter schema | `LLM` | Parameteriser session |
| D5 | Validator — does this stand on its own and generalise? | `LLM` | Validator session |
| D6 | Branch — REJECT discards; REVISE returns to D4; ACCEPT proceeds | `code` | |
| D7 | Write to skill library with name, schema, exemplars, provenance, empty invocation log | `code` | K10 (procedural variant) |

**The chain — instantiate (at next task):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| I1 | Skill Retriever — similarity search over the library | `code` | K10 retrieval |
| I2 | Branch — confident match? on miss → fresh **R3 Plan-and-Solve** | `code` | R3 |
| I3 | Adaptor — instantiate parameters from current task | `LLM` | Adaptor session |
| I4 | Executor — run the instantiated procedure, V9-bounded | `code` and `LLM` per step | V9 |
| I5 | On success: log invocation, reinforce. On failure: fallback to R3, flag skill | `code` | R3 / Skill Governor |
| I6 | If the run succeeded as a *novel* procedure, re-enter the distillation chain | `code` | back to D1 |

**Skeleton:**

```
on_task_complete(session):
    verdict = SuccessDetector(session)                    # LLM (or rule)
    if verdict != SUCCESS: return
    traj  = gather_trajectory(session)                    # code — K11 / V14
    path  = Extractor(traj)                                # LLM
    skill = Parameteriser(path)                            # LLM
    v     = Validator(skill)                                # LLM
    if v == ACCEPT:
        library.write(skill, provenance=session.id)        # code — K10
    elif v == REVISE:
        skill = Parameteriser(path, hint=v.notes)          # LLM (retry)
        if Validator(skill) == ACCEPT: library.write(...)
    # REJECT: drop

on_task_start(task):
    candidates = library.retrieve(task)                    # code — K10 retrieval
    if not candidates.confident:
        return run_R3(task)                                # fresh plan
    skill   = candidates.top
    bound   = SkillInvocationBound()                       # V9
    plan    = Adaptor(skill, task)                         # LLM
    result  = Executor(plan, bound)                        # code + per-step LLM
    library.log_invocation(skill, task, result)            # code
    if result.failed:
        Governor.flag(skill, reason="execution_failure")   # code
        return run_R3(task)                                # fallback
    return result
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Success Detector** | small-to-mid generalist, *or* a deterministic rule, *or* V15 LLM-as-Judge | role: *"you verdict whether a finished task met its success criterion"*; the success rubric for this task type; output contract (SUCCESS / FAIL / UNKNOWN) | the task, the final state, the success criterion |
| **Extractor** | capable generalist | role: *"isolate the minimal sequence of steps that produced this success; remove failed branches and dead ends"*; the trajectory schema (step, decision, tool call, outcome) | the full session log of the succeeded task |
| **Parameteriser** | the strongest available generalist — *parameterisation quality caps the library's value* | role: *"convert this trajectory into a named, parameterised procedure"*; **schema** (skill name, parameter list with types, body, exemplar invocations); abstraction rules (what is task-specific vs. procedural; how to name parameters; how many is too many) | the minimal trajectory + the original task description |
| **Validator** | capable generalist | role: *"verdict whether this candidate skill is general, self-contained, and correctly parameterised"*; rejection criteria (over-parameterised, task-specific values remain, unverifiable, redundant with existing library); output contract (ACCEPT / REVISE with notes / REJECT) | the candidate skill + a sample of existing library entries for duplication check |
| **Adaptor** | mid-tier generalist | role: *"instantiate this skill's parameters for the current task; do not edit the procedure body"*; the skill's parameter schema; rules for refusing to instantiate when a parameter cannot be confidently inferred | the matched skill + the current task description |

**Specialist-model note.** No fine-tuned specialist is required. The structural choices that make H4 work are not model choices but discipline choices: (1) **the write path runs only on a verified success signal** — without it, the pattern stores noise; (2) **the Parameteriser and the Executor are separate sessions** — same model is fine, never share setup; the Executor must never edit the library; (3) **the Skill Governor is real, not aspirational** — a freshness window, an invocation-log-based deprecation trigger, and a failure-rate quarantine. Skipping any of the three turns H4 into "a vector store of random trajectories", which is the wrong pattern under a misleading name.

In multi-agent (LEGOMem-style) deployments the additional structural choice is **memory unit allocation** — full-task units go to orchestrators, subtask units go to workers; the same Parameteriser/Validator chain runs, but at two granularities.

## Open-Source Implementations

- **Voyager** — [`github.com/MineDojo/Voyager`](https://github.com/MineDojo/Voyager) — the canonical embodied implementation. GPT-4 + an automatic curriculum + an *ever-growing skill library of executable code* + iterative self-verification. The reference for skills-as-code with success-driven storage and retrieval.
- **Memp** — [`github.com/zjunlp/MemP`](https://github.com/zjunlp/MemP) — the canonical tool-using-agent implementation. Distills trajectories into both step-by-step instructions and higher-level scripts; explores Build / Retrieval / Update strategies; benchmarked on TravelPlanner and ALFWorld.
- **Agent Workflow Memory** — [`github.com/zorazrw/agent-workflow-memory`](https://github.com/zorazrw/agent-workflow-memory) — induced workflows for web/browser agents; both offline (from training trajectories) and online (from agent's own runs); reference results on Mind2Web and WebArena.
- **Agent Memory Techniques** — [`github.com/NirDiamant/Agent_Memory_Techniques`](https://github.com/NirDiamant/Agent_Memory_Techniques) — runnable notebooks covering procedural memory among other memory types; useful for wiring the K10 substrate H4 builds on.
- **LEGOMem** — Microsoft Research, [paper at arXiv 2510.04851](https://arxiv.org/abs/2510.04851) — architectural reference for multi-agent procedural memory allocation; no canonical OSS repository yet.

## Known Uses

- **Voyager** in the Minecraft research setting — lifelong skill library; novel-world transfer demonstrated.
- **Memp** on TravelPlanner and ALFWorld — procedural memory transferred even *across model strengths* (procedures built by a stronger model help a weaker model).
- **AWM** on Mind2Web and WebArena — workflow memory in browser-agent production-style settings.
- **Coding-agent ecosystems** (Claude Code, Cursor, the open coding-agent stack) — community-curated and agent-curated skill / recipe files (a `skills/` folder, project recipes, reusable prompts) function as Procedural Skill Accumulation in practice; the trajectory-to-skill pipeline is often human-supervised today, increasingly automated.
- **Enterprise process agents** in Microsoft and similar research/production work — procedural-memory libraries shared across orchestrator and worker agents per LEGOMem.

## Related Patterns

- **Required by** Category VII — H4 is one of the H-patterns Voyager-style lifelong-learning agents and Memp-style tool agents are built on; it is the **success** half of the change-the-agent-over-time loop.
- **Required-substrate** **K10 Long-Term Memory (procedural variant)** — the skill library *is* a K10 procedural store. H4 is the learning loop K10's Distiller is the building block of.
- **Required-substrate** **H1 Identity Persistence** — the skill set the agent accumulates is part of *who the agent is*; without H1 the skill library exists but does not belong to a continuous self.
- **Sibling of** **H2 Episodic Self-Improvement** — H2 learns from failure, H4 learns from success. They share the trajectory ingest and run on opposite verdicts. In production they are almost always deployed together.
- **Composes with** **V15 LLM-as-Judge** — the Success Detector and the Validator are V15 instantiations.
- **Composes with** **V9 Bounded Execution** — the retrieve-instantiate-execute path must be bounded; on bound exhaustion the system falls back to R3 and quarantines the skill.
- **Composes with** **V14 Trajectory Logging** — the trajectory the Extractor reads is V14's natural output.
- **Composes with** **K11 Observational Memory** — within a session, K11 is the activity record the Extractor draws from at task completion.
- **Pairs with** **R3 Plan-and-Solve** as fallback — on retrieval miss or skill-execution failure, R3 takes over fresh.
- **Pairs with** **S4 Instruction Decomposition** — explicit task decomposition at the input layer makes the Parameteriser's job easier and the resulting skills cleaner.
- **Pairs with** **O6 Orchestrator-Workers** — in multi-agent systems (LEGOMem variant) skills are allocated by role; orchestrators carry task-shaped skills, workers carry sub-task-shaped skills.
- **Distinct from** **R11 Buffer of Thoughts** — R11 reuses solution templates *within* a context window; H4 persists procedures across sessions and instances. Different time-scales, same instinct.
- **Distinct from** **S8 Meta-Prompt** — S8 produces better prompts under human supervision; H4 produces reusable procedures from the agent's own successful work.
- **Distinct from** **K10 procedural variant** — K10 (procedural) is the *store and the bare distiller*; H4 is the surrounding *learning loop* (Success Detector → Extractor → Parameteriser → Validator → Library → Retriever → Adaptor → Executor → Governor) that fills, governs, and uses that store. K10 (procedural) without H4 is an empty file system; H4 without K10 has nowhere to write.
- **Cognitive grounding** — Anderson's ACT-R distinction between declarative and procedural memory; Fitts & Posner (1967) on skill-acquisition stages (cognitive → associative → autonomous). H4 implements the cognitive→autonomous transition for agents.

## Sources

- Wang, G., Xie, Y., Jiang, Y., Mandlekar, A., Xiao, C., Zhu, Y., Fan, L., Anandkumar, A. (2023) — "Voyager: An Open-Ended Embodied Agent with Large Language Models." arXiv 2305.16291. The canonical skill-library agent.
- Fang, R., et al. (2025) — "Memp: Exploring Agent Procedural Memory." arXiv 2508.06433. Procedural memory at task-suite scale; build/retrieval/update strategies; deprecation regimen.
- Wang, Z., Mao, J., Fried, D., Neubig, G. (2024) — "Agent Workflow Memory." arXiv 2409.07429. Workflow induction for browser/web agents.
- Microsoft Research et al. (2025) — "LEGOMem: Modular Procedural Memory for Multi-agent LLM Systems for Workflow Automation." arXiv 2510.04851. The multi-agent allocation variant.
- Anderson, J. R. (1983) — "The Architecture of Cognition." Declarative vs procedural memory; the cognitive grounding for the skill-acquisition split.
- Fitts, P. M., & Posner, M. I. (1967) — "Human Performance." Skill-acquisition stages (cognitive → associative → autonomous).
- Shinn et al. (2023) — "Reflexion." arXiv 2303.11366. Within-session self-improvement; the failure-side counterpart H2 builds on.
