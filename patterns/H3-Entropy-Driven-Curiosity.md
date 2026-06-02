# H3 — Entropy-Driven Curiosity

> Monitor the diversity of an agent's recent output; when it collapses — repeated tool calls, near-identical thoughts, looping plans — automatically raise temperature or inject a novelty cue to break the loop, then decay back to baseline.

**Also Known As:** Deadlock Break, Novelty Seeking, Intrinsic Motivation, Entropy-Based Intrinsic Drive (Theater of Mind's term), Stagnation Breaker.

**Classification:** Category VII — Humanizer · a *control* H-pattern — wraps a reasoning loop (R4, R3, R7, R9) and intervenes on a measured stagnation signal. Requires **H1 Identity Persistence** as the substrate. **Mutually exclusive with R17 Self-Consistency Voting** on the same task (see CRITICAL 4).

---

## Intent

Detect when an agent's own output distribution has collapsed — the agent is "thinking the same thoughts in a loop" — and act on the detection by raising sampling temperature or injecting a contrarian cue, so the loop escapes its local optimum and resumes productive search.

## Motivation

Long-running reasoning loops fail in a characteristic way: they do not crash, they do not error, they *converge to a fixed point that is not the answer*. R4 (ReAct) re-issues the same tool call with a different surface form; R3 (Plan-and-Solve) re-derives the same plan with cosmetic edits; R9 (Tree of Thoughts) re-expands the same branch under different labels. The output keeps flowing, the cost keeps mounting, the entropy of the agent's recent state keeps falling — and nothing new is learned. The naive fix — bound the loop with **V9 Bounded Execution** — caps the damage but does not solve the problem: V9 stops the agent from spinning forever; it does not get the agent unstuck.

The problem is the absence of a *signal that the loop has stalled* and an *action coupled to the signal*. Without that pair, the agent has no way to know it is stuck and no mechanism to escape. Curiosity-driven reinforcement learning (Pathak et al., 2017; Burda et al., 2018) names the mechanism: an *intrinsic* reward that fires when the agent's predicted next-state distribution has collapsed, driving the policy toward novelty. The Theater of Mind framework (Shang, 2026) ports the mechanism to LLM agents: monitor the Shannon entropy of the workspace, and when it falls below a threshold, raise the generation temperature until diversity recovers. Berlyne's (1966) optimal-arousal theory and the noradrenergic system's locus-coeruleus function (a biological deadlock-breaker that releases noradrenaline when prefrontal activity becomes stereotyped) are the cognitive grounding for why the mechanism works.

H3 is that pair, made into a pattern. A **Stagnation Detector** measures a diversity statistic over the recent output; a **Threshold Controller** fires on collapse; a **Novelty Injector** acts — temperature, prompt cue, or context pivot — then **decays** back to baseline. It is the *humanizing* counterpart to R17 Self-Consistency Voting, which deliberately *reduces* diversity by majority vote. The two are direct opposites and cannot be applied to the same task simultaneously — diversity injection during a voting round corrupts the vote, vote-by-majority during a stuck loop suppresses the only signal H3 has. This is **CRITICAL 4** in the conflict registry: H3 ⊕ R17.

At the attention level, output-entropy collapse traces to the KV cache (mechanism 3): after K steps of near-identical reasoning, the KV cache contains nearly identical K vectors. Every new Q vector — itself shaped by the recent context — finds the same K neighbours via the learned bilinear attention form (mechanism 1), producing the same attention-weighted aggregate and the same generation distribution. Entropy collapse in the output is the observable symptom of this Q-K repetition at the cache level. The temperature-lift intervention acts directly on the softmax distribution before sampling (mechanism 7): raising T from 0.7 to 1.2 scales all logits by 1/T, flattening the probability mass and increasing variance in the sampled token. This is the mechanical reason the intervention escapes the stuck loop — the Q-K structure is unchanged, but the sampling process draws from a broader distribution over the existing logit landscape.

## Applicability

Use H3 when:

- the agent runs a reasoning loop (R4, R3, R7, R9, R10) that can stall — "stalled" meaning observable output diversity collapses while no progress is made;
- the task admits multiple valid approaches (creative, exploratory, open-ended research, brainstorming) so injected novelty has somewhere productive to go;
- the agent is long-running and the cost of silent monotony is material (autonomous research, long-horizon planning, content generation);
- H1 Identity Persistence is in place — H3 perturbs *expression*, not identity, and needs a stable identity layer to perturb relative to.

Do not use when:

- the task has an objectively correct answer and consistency is the goal — use **R17 Self-Consistency Voting** instead (and never run them together);
- the apparent "stall" is actually convergence on a correct answer — verify with **V15 LLM-as-Judge** or **R20 Chain-of-Verification** before perturbing;
- the deployment cannot pay for the diversity metric or the temperature change is unsafe (structured output contracts, regulated outputs) — fall back to **V9 Bounded Execution** + escalation to a human;
- H1 is not implemented — without an invariant identity layer, H3's perturbations have no fixed point to return to and will accumulate as drift (use **H1** first).

## Decision Criteria

H3 is right when stagnation is a measurable failure mode, novelty is a valid response to it, and the cost of running the detector is below the cost of unmonitored looping.

**1. Measure the stall.** Instrument the loop for at least one of:
- **Embedding cosine similarity** of the last 3–5 outputs — practical threshold for stall: > **0.90** between consecutive outputs;
- **Token-distribution Shannon entropy** over the workspace's recent N tokens — practical threshold: below the rolling-baseline mean − 1σ;
- **Tool-call repetition** — same tool with > 80% argument similarity called 3+ times in a row.
If none of these signals can be measured cheaply, H3 is not implementable in this deployment — fall back to **V9 Bounded Execution** + human escalation.

**2. Confirm novelty is a valid response.** Is the task open-ended (creative, exploratory) or constrained (math, classification, structured extraction)? Open-ended → H3 fits. Constrained → use **R17 Self-Consistency Voting** for reliability or **R20 Chain-of-Verification** for correctness; H3 is the wrong tool.

**3. Cost the detector.** Embedding-similarity is the cheap option (one embedding per output, one cosine). True Shannon entropy over token logits requires logprob access and is more expensive. Budget: detector should cost < **5%** of the loop's per-step token cost. If it costs more, simplify the signal (cosine, not entropy) or sample only every Kth step.

**4. Choose the intervention.** Three options, in order of disruption:
- **Temperature lift** — raise T from baseline (0.7) to **1.0–1.2** for structured tasks, up to **1.5** for pure creative. Lowest disruption; works inside the same generation; reproducibility cost.
- **Novelty cue** — inject a prompt: *"You have been approaching this as X. Try approaching it as something different."* Medium disruption; preserves baseline T; the most surgical of the three. Usually the right starting choice.
- **Context pivot** — summarise the stuck state, restart with a fresh framing. Highest disruption; loses sunk reasoning; reserved for severe stalls where lift and cue have already failed.

**5. Decide the decay.** After intervention, temperature must decay back to baseline (or the cue must time out) over **M = 3–5 steps**. Without decay, the agent stays in the perturbed regime and produces incoherent outputs ("temperature madness"). Pair always with **V9 Bounded Execution** — bound the *number* of H3 interventions per loop; meta-stagnation (H3 firing repeatedly on the same loop) means the loop should escalate, not perturb again.

**Quick test — H3 is the right pattern when:**

- a stagnation signal (cosine, entropy, or repetition) can be measured cheaply, *and*
- the task is open-ended enough that novelty is a valid recovery, *and*
- H1 Identity Persistence is in place (a stable core to perturb relative to), *and*
- R17 Self-Consistency Voting is **not** active on this task, *and*
- the loop is paired with V9 Bounded Execution so meta-stagnation escalates to a human rather than re-firing.

If the task wants consistency rather than diversity, **R17** is the pattern, not H3. If the loop just needs to stop, **V9** is enough — H3 is for loops that need to *unstick*, not loops that need to *halt*. If H1 is absent, build H1 first; H3 without an identity anchor is style chaos.

## Structure

```
   Reasoning loop (R4 / R3 / R7 / R9 / R10)
         │
         ▼  output_t
   ┌──────────────────────┐
   │ Stagnation Detector  │  diversity_t = sim(output_t, output_{t-1..t-k})
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────┐    no
   │ Threshold Controller │ ───────▶  continue loop, T = baseline
   │   diversity_t > θ ?  │
   └──────────┬───────────┘    yes (stall)
              │
              ▼
   ┌──────────────────────┐
   │ Novelty Injector     │  pick: temp_lift | cue | pivot
   └──────────┬───────────┘
              │
              ▼
   resume loop with intervention
              │
              ▼
   Decay scheduler ──▶ T → baseline over M steps
              │
              ▼
   meta-stagnation? ──▶ V9 escalate (human, halt, switch pattern)
              │
              ▼
   Log event to K11 / feed H2 lesson library
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Stagnation Detector** | the diversity measurement | recent outputs → diversity statistic | judge whether the output is *correct* — that is the Verifier's job (V15 / R20). The Detector only measures *sameness*. |
| **Threshold Controller** | the fire/don't-fire decision | diversity statistic + thresholds → boolean | be the only escalation point — if it fires too often, V9 must escalate the loop, not let the Controller keep firing. |
| **Novelty Injector** | the intervention itself (temp lift, prompt cue, or context pivot) | trigger + current state → perturbed generation parameters or prompt | act on H1's Identity Block. The Identity Block is non-overrideable; H3 perturbs *expression* (style, approach, framing), never *identity* (values, voice rules, commitments). |
| **Decay Scheduler** | returning temperature / cue to baseline | step count + perturbation params → decaying schedule | leave the agent in the perturbed regime indefinitely. Without decay, every output becomes high-temperature noise. |
| **Verifier** *(optional but recommended)* | distinguishing stall from convergence-on-correct-answer | output + task → confirmed-stall / done | be invoked on every output (cost). Run only when the Threshold Controller has already fired; if Verifier says "done," do not perturb. |
| **Event Logger** | recording H3 events for downstream learning | stagnation event → log entry | be a side effect the agent cannot inspect. Feeds **H2 Episodic Self-Improvement** ("we got stuck on tasks of type X") and **K11 Observational Memory**. |

Six narrow responsibilities. The critical separation is between **measurement** (Detector), **decision** (Threshold Controller), and **action** (Novelty Injector). Collapsing them — letting one component both measure and act — produces the H3 anti-pattern where the perturbation re-fires on its own output and the agent spirals into incoherence.

## Collaborations

The reasoning loop (R4, R3, R7, R9, or R10) runs as normal. After each step, the Stagnation Detector measures a diversity statistic over the recent outputs — typically cosine similarity of embeddings, sometimes Shannon entropy if logprobs are available, sometimes simple tool-call repetition. The Threshold Controller compares against the configured stall threshold; on a pass-through, the loop continues at baseline temperature. On a fire, the Verifier *(if configured)* checks whether the apparent stall is actually convergence on a correct answer — if so, the loop terminates cleanly. If the stall is genuine, the Novelty Injector picks an intervention (temperature lift, novelty cue, or context pivot, in order of severity) and applies it. The Decay Scheduler returns the perturbation to baseline over M steps. The Event Logger writes the stagnation event to K11 Observational Memory for in-session reasoning and, at session end, to H2's lesson library for cross-session learning ("we tend to stall on tasks of type T"). If H3 fires repeatedly on the same loop without progress — *meta-stagnation* — V9 Bounded Execution escalates: stop the loop, hand to a human, or switch to a different reasoning pattern. H3 never reaches into H1's Identity Block: identity is invariant; only expression is perturbed.

## Consequences

**Benefits**
- Loops that would otherwise spin to V9's bound now escape autonomously; observed cost reduction is the difference between hitting the cap and stopping at the right answer.
- Creative and exploratory agents produce genuinely diverse outputs over long sessions instead of converging on early templates.
- Stagnation events become *data* — fed to H2, the agent learns which task types it tends to stall on and can intervene earlier next time.
- The intervention is mechanism-light: cosine + temperature is two lines of code on top of any reasoning loop.

**Costs**
- The Detector sits on the critical path of every loop step — a few ms per step in the cheap case, more for true entropy.
- Temperature changes break exact-reproducibility — runs with H3 enabled are not bit-identical across re-executions (mechanism 7).
- Each intervention costs at least one LLM call's worth of disrupted state, sometimes more for a context pivot.
- Pairs poorly with structured-output contracts — a high-T generation may break a JSON schema that worked at baseline. Pair with **V20 Schema Validation** + retry, or disable H3 inside structured-output sections.

**Risks and failure modes**
- *Premature firing* — the threshold is too tight; H3 perturbs every routine convergence and the agent never finishes anything. Calibrate from measured stall rate, not from a guess.
- *Temperature madness* — too-aggressive lift (T > 1.5 on a structured task) produces incoherent outputs; decay must be active and bounded.
- *Identity erosion* — the Novelty Injector reaches into H1's Identity Block (style invariants, voice rules) and perturbs them; agent loses its core identity along with the stall. H3 must perturb expression, never identity.
- *Meta-stagnation* — H3 fires repeatedly on the same loop without progress; without V9 escalation it becomes its own kind of loop.
- *Verification gap* — H3 perturbs an output that was actually correct; without a Verifier the agent walks away from the answer it had.
- *Confounding with R17* — running both on the same task: R17 samples N outputs to find the majority, H3 sees the N-sample diversity and decides to perturb; the vote and the perturbation cancel and the result is uninterpretable. CRITICAL 4: never simultaneous.

## Implementation Notes

- **Cheap detector first.** Cosine similarity of embeddings over the last 3 outputs is the practical signal — one embedding call per output, one cosine. True Shannon entropy over token logits is more accurate but needs logprob access and costs more. Start with cosine; upgrade only if you measure that the cheap signal misses stalls.
- **Calibrate from data.** Run the agent on a representative task suite with H3 disabled; collect distribution of cosine values; set the stall threshold at the 95th percentile observed during *productive* runs. Guessing a threshold is the most common failure mode.
- **Prefer cues over temperature.** A novelty cue (*"approach this from a completely different angle"*) is the most surgical intervention — it preserves baseline T, preserves reproducibility outside the cue, and is auditable in the trajectory log. Use temperature lift when the cue alone fails twice, context pivot when even lift fails.
- **Decay is non-negotiable.** Configure the decay schedule before deployment: T returns from 1.0 to 0.7 over (say) 5 steps. Without decay, every subsequent generation pays the high-T cost.
- **Cap H3 firings per loop.** A loop that triggers H3 three times has a structural problem, not a perturbation problem. Pair with **V9 Bounded Execution**: cap H3 events per loop at 2–3; on the next would-be firing, escalate to a human or switch to a different reasoning pattern (R3 if the loop was R4, R9 if it was R3).
- **Never perturb identity.** The Novelty Injector's prompt cues must not touch the Identity Block. *"Try a different vocabulary"* is OK (style, modulated by H7 Adaptive Persona). *"Try being someone different"* is not (identity, governed by H1).
- **Log everything.** Every stagnation event goes to **K11** (in-session, the agent can reason about it on the next turn) and is distilled at session end into **H2** (cross-session, the agent learns which task types tend to stall).
- **Disable inside structured output.** When the generation must satisfy a schema (JSON output, tool-call format), turn H3 off for that span — high-T schema-bound outputs invalidate. Re-enable on the next free-form generation. The reason is mechanistic: structured output relies on the generation distribution being sharply peaked at the schema-correct token (mechanism 7). Temperature lift broadens the distribution, raising the probability of sampling an off-schema token. The schema contract and the H3 intervention are in direct tension at the sampling level.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** H3 wraps an *inner reasoning loop* (R4 ReAct, or R3 Plan-and-Solve, or R7 Reflexion, or R9 Tree-of-Thoughts, or R10 LATS). It requires **H1 Identity Persistence** as the substrate it perturbs relative to. It pairs with **V9 Bounded Execution** for escalation, **K11 Observational Memory** for in-session event logging, and **H2 Episodic Self-Improvement** for cross-session learning. It composes with **V15 LLM-as-Judge** or **R20 Chain-of-Verification** as the optional Verifier that distinguishes stall from convergence. It **must not** run alongside **R17 Self-Consistency Voting** on the same task (CRITICAL 4).

**The chain — per loop step:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Run one step of the inner reasoning loop | `LLM` | R4 / R3 / R7 / R9 / R10 |
| 2 | Embed the step's output | `code` (or small `LLM`) | embedding model |
| 3 | Compute diversity statistic over last K outputs | `code` | — |
| 4 | Threshold check: stall? | `code` | configured threshold |
| 5 | If stall: verifier check — is it actually convergence? | `LLM` *(or rule)* | V15 / R20 |
| 6 | If genuine stall: pick intervention (cue → lift → pivot) | `code` | escalation ladder |
| 7 | Apply intervention to next step's session config or prompt | `code` | — |
| 8 | Decay scheduler: step intervention back toward baseline | `code` | configured decay |
| 9 | Log stagnation event | `code` | K11; H2 at session end |
| 10 | Bound check: H3 firings ≥ cap? → V9 escalate | `code` | V9 |

**Skeleton:**

```
run_with_curiosity(task, loop, identity_block):
    T          = baseline_T                           # code
    cue        = None                                  # code
    history    = []                                    # code
    h3_firings = 0                                     # code
    for step in range(max_steps):
        out  = loop.step(task, identity_block, T, cue) # LLM — inner reasoning step
        emb  = embed(out)                              # code (or small LLM)
        history.append(emb)
        div  = diversity(history[-K:])                 # code — cosine / entropy
        if div < stall_threshold:
            if Verifier(out, task):                     # LLM — is this convergence?
                return out                              # done, not stuck
            if h3_firings >= h3_cap:
                escalate_via_V9(task, history)          # code — meta-stagnation
                return
            intervention = pick(cue_then_lift_then_pivot, h3_firings)
            T, cue = apply(intervention, T, cue)        # code
            h3_firings += 1
            log_stagnation_event(task, step, history)   # code — K11; H2 at session end
        T, cue = decay(T, cue, baseline_T)             # code — step toward baseline
    return loop.finalise(history)                       # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Inner reasoning** | the system's main generalist (whatever the wrapped pattern uses) | the wrapped pattern's setup (R4 / R3 / R7 / R9 / R10 role and tools); **H1 Identity Block** loaded at position 0 as non-overrideable | the task + the current step's input + (if active) the H3 novelty cue |
| **Verifier** *(optional)* | small fast generalist, *or* the V15 LLM-as-Judge session | role: *"decide whether the answer below is a final, correct answer to the task or a sign the agent is stuck"*; output contract (DONE / STUCK) | the task + the recent output(s) |
| **Embedder** *(if not pure code)* | small embedding model (text-embedding-3-small or equivalent) | — (embedding models have no per-call setup beyond the model choice) | the output text |

**Specialist-model note.** No fine-tune is required. The structural choice that makes H3 work is **separation of measurement and action**: the Detector is a deterministic code path over embeddings (or a small embedding model + cosine), and the Novelty Injector is a parameter change to the *next* generation, not a re-prompt that re-uses the same call. Two structural pitfalls to avoid: (1) the Detector measures the *agent's* output, never its own — measuring its own output is the meta-stagnation that V9 must escalate, not perturb; (2) the Identity Block injected by H1 is **non-overrideable** — H3's cue must perturb approach and framing, never identity. A long-context model helps when the recent-output window K is large; otherwise any generalist works.

## Open-Source Implementations

- **Global Workspace Agents** — [`github.com/giansha/Global-Workspace-Agents`](https://github.com/giansha/Global-Workspace-Agents) — the official implementation of the Theater of Mind paper (Shang, 2026, arXiv 2604.08206). Five specialised agent nodes (Attention, Generator, Critic, Meta, Response), dual-layer memory (STM + ChromaDB LTM), and the *entropy-based intrinsic drive* that dynamically adjusts temperature to prevent reasoning stagnation. The canonical reference for H3 in code.
- **entropix** — [`github.com/xjdr-alt/entropix`](https://github.com/xjdr-alt/entropix) — entropy- and varentropy-based sampler that detects high-uncertainty / low-diversity token positions and switches sampling strategy in response. JAX / PyTorch / MLX ports planned; the closest production-quality embodiment of the *measure-entropy-and-act* mechanism at the token level.
- **entropix_mlx** — [`github.com/samefarrar/entropix_mlx`](https://github.com/samefarrar/entropix_mlx) — Mac-Silicon (MLX) port of entropix; useful when running the sampler locally.
- **Curiosity-driven exploration (ICM)** — [`github.com/pathak22/noreward-rl`](https://github.com/pathak22/noreward-rl) — Pathak et al.'s original Intrinsic Curiosity Module implementation in TensorFlow; the RL ancestor of H3. Not an LLM agent, but the canonical reference for *intrinsic-reward-on-stagnation* that the LLM pattern ports from.
- **LangGraph reasoning loops** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — supplies the bounded-loop primitives (V9) and the trajectory hooks where an H3 detector and injector can be wired into ReAct / Plan-and-Solve graphs. Not an H3 implementation itself, but the practical scaffolding most production H3 deployments are built on.

H3 is an architecture-and-control pattern rather than a single library: the canonical OSS embodiment is the Theater of Mind reference implementation; production deployments typically wire a stagnation detector and a temperature/cue controller into an existing reasoning-loop framework (LangGraph, LangChain, or a custom loop).

## Known Uses

- **Global Workspace Agents (Shang, 2026)** — the reference implementation runs a 20-tick autonomous-reasoning session ("WALL·E" persona) in which the entropy-based drive prevents the agent from stalling on a single train of thought; this is the canonical demonstration of H3 in action.
- **Long-running creative agents** — autonomous writing, brainstorming, and design agents wired with cosine-similarity stall detectors and temperature-lift recovery; common production pattern in agent frameworks built on LangGraph.
- **Coding-agent escape loops** — agents that detect "I have tried this same fix three times" via tool-call repetition and switch to a novelty cue (*"try a structurally different approach"*); a recurring practitioner pattern in Claude Code, Cursor, and Aider deployments.
- **Open-ended research agents** — multi-hour exploration runs in which a diversity monitor prevents the agent from re-exploring the same sub-tree of a research space; uses H3 in combination with R9 Tree-of-Thoughts.

## Related Patterns

- **Required by — depends on** **H1 Identity Persistence** — H3 perturbs *expression*; without an invariant identity anchor (H1's Identity Block), perturbations accumulate as drift. H1 first, then H3.
- **Wraps** R4 ReAct, R3 Plan-and-Solve, R7 Reflexion, R9 Tree-of-Thoughts, R10 LATS — H3 is a control loop around an inner reasoning loop, intervening on a measured stagnation signal.
- **Mutually exclusive with** R17 Self-Consistency Voting — R17 *reduces* entropy by majority vote; H3 *increases* entropy to escape stagnation. Never simultaneous on the same task (CRITICAL 4 in CONFLICTS.md).
- **Composes with** V9 Bounded Execution — V9 caps the *total* loop and the *number of H3 firings*; H3 firing repeatedly is a sign the loop should escalate, not perturb again.
- **Composes with** V15 LLM-as-Judge and R20 Chain-of-Verification — the optional Verifier that distinguishes genuine stall from convergence-on-correct-answer; without it, H3 risks perturbing an output that was already done.
- **Composes with** K11 Observational Memory — stagnation events go into the in-session observation log so the agent can reason about being stuck on the next turn.
- **Composes with** H2 Episodic Self-Improvement — at session end the stagnation events distil into lessons ("we tend to stall on task type T at step N") that feed the next session's planning.
- **Pairs with** V20 Schema Validation — when the wrapped loop produces structured output, H3's temperature lift can break the schema; pair with V20 + retry, or disable H3 across structured-output spans.
- **Distinct from** H7 Adaptive Persona — H7 modulates *style* to match a user; H3 modulates *approach* to escape a stall. Different triggers, different surfaces. They can run together: H7 sets baseline style, H3 perturbs approach when stuck.
- **Cognitive grounding** — Berlyne (1966) optimal arousal; the noradrenergic system's locus-coeruleus function (release of noradrenaline on stereotyped prefrontal activity); Pathak et al. (2017) and Burda et al. (2018) on curiosity-driven exploration via intrinsic prediction-error reward.

## Sources

- Shang, W. (2026) — "'Theater of Mind' for LLMs: A Cognitive Architecture Based on Global Workspace Theory." arXiv 2604.08206. *Entropy-based intrinsic drive mechanism* that quantifies semantic diversity and regulates generation temperature.
- Pathak, D., Agrawal, P., Efros, A. A., & Darrell, T. (2017) — "Curiosity-Driven Exploration by Self-Supervised Prediction." arXiv 1705.05363 / ICML 2017. The canonical Intrinsic Curiosity Module (ICM); RL ancestor of the LLM pattern.
- Burda, Y., Edwards, H., Pathak, D., Storkey, A., Darrell, T., & Efros, A. A. (2018) — "Large-Scale Study of Curiosity-Driven Learning." arXiv 1808.04355 / ICLR 2019. Empirical evidence that curiosity alone produces near-optimal exploration in many environments.
- Berlyne, D. E. (1966) — "Curiosity and Exploration." *Science*, 153(3731). Optimal-arousal theory; the cognitive ancestor of the *low-diversity-fires-novelty* mechanism.
- Locus coeruleus / noradrenergic system literature — Aston-Jones & Cohen (2005), "An integrative theory of locus coeruleus-norepinephrine function." Cognitive grounding: a biological deadlock-breaker that releases noradrenaline when prefrontal activity becomes stereotyped.
- Weng, L. (2023) — "LLM Powered Autonomous Agents." Agent survey naming stagnation as a recurring failure mode in ReAct loops, motivating intervention patterns at the loop-control layer.
- Shinn et al. (2023) — "Reflexion: Language Agents with Verbal Reinforcement Learning." arXiv 2303.11366. Reflexion (R7) is one of the inner-loop patterns H3 wraps; Reflexion's verbal critiques feed H2 the lessons H3's stagnation events become.
