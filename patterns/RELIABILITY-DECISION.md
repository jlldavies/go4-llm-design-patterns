# Reliability Pattern Selection

## Ask This First — What Is the Verifier?

**Every loop has a verifier. If you did not choose one, you have one anyway, and it is
whatever the loop happens to stop on.** That is the single most consequential
unexamined decision in agent design, so it is the first question here rather than a
branch buried in the flow below.

The verifier does two jobs, and the second is the one people miss:

1. it is the **stop condition** — when the loop is done;
2. it **defines what the loop treats as progress** — what "better" means.

So an incomplete verifier does not merely stop too early or too late. **The loop
optimises toward it.** Yoko Li's account of this ([a16z, "Knowing When to Stop"]
(https://a16z.com/knowing-when-to-stop-the-art-of-making-a-loop-converge/)) supplies
the sharpest evidence: on SpecBench, frontier agents routinely passed the visible tests
while failing held-out ones, and one produced a 2,900-line "compiler" that had simply
memorised the test inputs. The loop converged — on the verifier, not on the user's
intent. Tests looked like a perfectly objective stop condition and were a proxy.

```
Does anything here run more than once — a loop, a retry, a fan-out, a scheduled routine?
  YES → NAME THE VERIFIER EXPLICITLY. Then classify it:

    Is the check DETERMINISTIC (schema, exit code, diff, invariant)?
      → V20 (Schema Validation) / V9 (Bounded Execution) as the stop condition
        Cheapest and most trustworthy. Prefer it wherever the property is decidable.

    Does it need JUDGEMENT (quality, tone, "is this finding real")?
      → V15 (LLM-as-Judge) — and pick the judge model deliberately (see below)
        Adversarial variant: prompt the judge to REFUTE, not to approve

    Is the property only observable in AGGREGATE (regression, drift, win-rate)?
      → V16 (Offline Eval) pre-deployment · V17 (Online Eval) in production

    Can the check be gamed by the thing it checks?
      → Hold out part of the signal. A verifier the generator can see is a target.

  NO natural verifier exists → say so, and put a human at the boundary:
      → V1 (Human-in-the-Loop) blocking, or V2 (Human-on-the-Loop) monitoring
        "No verifier" is a valid finding. An unexamined proxy is not.
```

### The verifier is a model choice, not just a pattern choice

**Match the verifier model to the verification task — not reflexively the strongest
model, and never reflexively the cheapest.** This is mechanism **M8 (Model Size
Matching to Task Complexity)** applied to the verifier itself, and it cuts both ways:

- **Too weak a verifier** rubber-stamps. It cannot detect the failure it was hired to
  detect, so the loop converges on a check that never fires — the SpecBench failure in
  miniature.
- **Too strong a verifier** is a different bug, not merely an expensive one. If judging
  costs as much as generating, the verifier stops being affordable at the frequency
  that makes it useful, and it gets sampled, batched or quietly dropped — leaving the
  loop unverified precisely where it is hottest. A verifier that runs on 5% of
  iterations is 5% of a verifier.
- **The same model that generated the output is the worst judge of it.** Shared blind
  spots, shared priors. Prefer a *different* model over a *bigger* one when the risk is
  correlated error rather than insufficient capability.
- **Diversity beats scale when failure is multi-modal.** Three cheap judges with
  distinct lenses (correctness, security, does-it-reproduce) catch more than one
  expensive judge asked to consider everything at once.

Rule of thumb: **the verifier should be as weak as it can be while still able to fail
the check.** Size it to the discrimination required, then confirm it can actually
produce a negative — a judge that has never rejected anything is not evidence of
quality, it is an untested branch.

## Decision Flow

```
Does the agent take irreversible or high-blast-radius actions?
  YES → V1 (Human-in-the-Loop) at those decision boundaries
  MONITOR only → V2 (Human-on-the-Loop)
  Two independent confirmations required → V3 (Rule of Two)

Does the agent process untrusted external content?
  YES:
    Private data + untrusted content + external comms? → V3 (lethal trifecta check)
    Route untrusted content to quarantined model → V4 (Dual LLM)
    Inject structural defences at prompt boundaries → V6 (Prompt Injection Shield)

Does the agent run in a loop or have no natural exit condition?
  YES → V9 (Bounded Execution) — REQUIRED; hard caps on steps, cost, wall-time
    ⚠ V20 retry loops expand context ~2× per retry; include in V9 token cap calculation

Does the agent generate or execute code?
  YES → V8 (Tool Sandboxing): restrict filesystem, network, clock

Does the agent have more than 10 active tools?
  YES → V13 (Tool Budget): hard limit on active schema tokens
    Tool selection accuracy: 43% at low counts → 14% at high counts (3× degradation)

Does the agent need to recover from partial failure without restart?
  YES → V10 (Checkpointing): replayable state snapshots

Are there multiple safety boundaries (input, tool calls, output)?
  YES → V5 (Guardrail Layering): safety checks at all four points

Is output conformance to a schema required?
  YES → V20 (Schema Validation): validate-and-reask loop
    Bundle with V9: each retry expands context

Is output quality measurable?
  Pre-deployment → V16 (Offline Eval)
  In production → V17 (Online Eval)
  Second model as judge → V15 (LLM-as-Judge)

Is full observability required (compliance, debugging)?
  YES → V14 (Trajectory Logging): OTel-compatible trace from day 1

Does the agent need declarative policy enforcement outside the prompt?
  YES → V7 (AgentSpec): deterministic policy; not probabilistic like S9
```

## Must-Have Baseline

Every production agent needs at minimum: **V9 + V14, plus a named verifier**. Add V1 at
any irreversible action boundary. Add V5 at any external input boundary.

The verifier belongs in the baseline rather than the optional tier because V9 and V14
tell you the loop *stopped* and *what it did* — neither tells you whether stopping was
**right**. A bounded, fully-traced loop converging on the wrong signal is still
converging on the wrong signal, and it will do so tidily, on budget, with excellent
logs.
