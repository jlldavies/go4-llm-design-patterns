# Conflicts — Signal

*Per-category conflict detail. Summary + index: [CONFLICTS.md](../CONFLICTS.md).*

## Critical 3 — S9 H/S V7  {#critical-3}

**Type:** Hard vs Soft

S9 embeds principles in the prompt. The model applies them through language reasoning — probabilistic, can be overridden by adversarial prompting, cannot be audited with certainty. V7 externalises rules in a policy engine independent of the LLM — deterministic for defined violations, survives prompt manipulation, produces an audit record.

They are not alternatives. They are layered enforcement:

```
S9 (Constitutional Framing) — soft, broad, in-prompt
    "I should not reveal confidential data"
    $\to$ model usually follows; can be manipulated by injection

V7 (AgentSpec / Declarative Governance) — hard, specific, external
    PROHIBIT: tool_call.name == "send_email" AND context.contains(classified_data)
    $\to$ enforced at runtime regardless of what model "thinks"
```

**Resolution rule:**
- S9 for: values, style, judgment calls, broad ethical principles — anything requiring contextual interpretation
- V7 for: specific, enumerable prohibitions and obligations — anything requiring deterministic enforcement
- Always use both in safety-critical systems; S9 catches the cases V7 didn't anticipate; V7 catches the cases S9 was manipulated into allowing

**Critical error:** Using S9 alone and claiming the system is "aligned." S9 is probabilistic; call it what it is.

---

## Connection B — S2 $\sim$ prefix cache  {#connection-b}

**Type:** Composability Tension ($\sim$)

Dynamic S2 (Retrieval-Augmented Few-Shot variant) changes the token sequence of the few-shot block on every call. This does not only forfeit S2's own cache entry — it invalidates the cache for the entire prefix that precedes it: S3 Persona, S5 Constraint Framing, S6 Output Template, S9 Constitutional Framing. Any stable content placed before the dynamic S2 block cannot be cached if S2 changes.

**The economic cost is larger than it appears:** if the stable prefix (S3+S5+S6+S9) is 2,000 tokens and dynamic S2 is inserted in the middle of it, all 2,000 tokens of stable content re-prefill at full cost on every call.

**Resolution:** If dynamic S2 is required, place it at the END of the prompt — after all stable content. This preserves the stable prefix cache for the S3/S5/S6/S9 block while still allowing the examples to vary.

---

## Signal vs Signal

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| S1 (Zero-Shot) | $\uparrow$ | S2 (Few-Shot) | S1 is the default; add S2 when output format is inconsistent. S2 costs 3-5× more tokens. |
| S3 (Persona) | $\sim$ | S5 (Constraint Framing) | Persona may imply latitude that constraints prohibit. Add explicit "constraints override persona." |
| S3 (Persona) | $\sim$ | S9 (Constitutional Framing) | Persona implies identity; constitution implies values. Conflict when persona's implied expertise contradicts constitutional safety constraints. Constitution wins. |
| S4 (Instruction Decomposition) | $\uparrow$ | O2 (Prompt Chaining) | S4 puts all steps in one prompt; O2 distributes across calls. S4 is cheaper but loses inter-step inspection. |
| S6 (Output Template) | $\uparrow$ | Structured Output API | Structured output API (JSON mode) is strictly better when available. S6 free-text templates only when API not available. |
| R17 (Self-Consistency) | $\oplus$ | H3 (Entropy Curiosity) | See CRITICAL 4. Never apply simultaneously. |
| S8 (Meta-Prompt) | $\to$ | R17 or V15 | S8 requires an evaluation signal to select between generated prompts. Without R17 or V15, S8 cannot function. |
| S9 (Constitutional Framing) | H/S | V7 (AgentSpec) | See CRITICAL 3. Complementary; S9 soft/broad, V7 hard/specific. |

## Signal vs Reasoning

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| S2 (Few-Shot) | $\sim$ | R17 (Self-Consistency) | S2 shapes what the model produces; R17 samples multiple versions and votes. They compose: S2 sets format, R17 improves reliability. Ensure S2 examples don't bias R17 toward a single answer style. |
| S4 (Instruction Decomposition) | $\uparrow$ | R3 (Plan-and-Solve) | S4 is a prompt-level step list; R3 is an agent-level planning cycle with separate plan and execution calls. R3 is more powerful but costs more. |
| S9 (Constitutional Framing) | $\sim$ | R7 (Reflexion) | Reflexion critiques outputs; constitution critiques against principles. If both are active, ensure they don't generate contradictory critique: R7 might say "be more detailed" while S9 says "be more concise." Make priorities explicit. |
