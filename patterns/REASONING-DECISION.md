# Reasoning Pattern Selection

## Decision Flow

```
Need token efficiency above all?
  → R5 (ReWOO): 5× reduction vs ReAct; plan all tool calls upfront

Need mid-run adaptation to observations?
  → R4 (ReAct): adaptive tool use; each action informs the next

Multi-tool task needing self-debugging?
  → R13 (CodeAct): ~20pp accuracy gain over JSON tool calls

Hard open-ended problem, quality trumps cost?
  → R9 (Tree of Thoughts) or R10 (LATS)

Clear pass/fail criteria and retries are acceptable?
  → R7 (Reflexion): verbal self-critique across retries

Math or numerical computation?
  → R14 (Program of Thoughts): delegate to a deterministic executor

Parallel generation needed to reduce latency?
  → R12 (Skeleton-of-Thought): outline first, fill sections in parallel

Reusable reasoning templates exist for this task type?
  → R11 (Buffer of Thoughts): 12% cost of ToT/GoT

Multi-hop factual question?
  → R6 (Self-Ask): sub-question chains

Quick reasoning improvement with no examples?
  → R1 (Zero-Shot CoT): "think step by step"
```

## Cost Guide

| Pattern | LLM Calls | Relative Cost | Notes |
|---|---|---|---|
| R1 Zero-Shot CoT | 1 | Baseline | Add "think step by step" only |
| R2 Few-Shot CoT | 1 | Low + example tokens | Static examples cache cleanly |
| R3 Plan-and-Solve | 2 | Low | Plan + execute; two clean calls |
| R4 ReAct | N per step | Medium–High | Scales with task complexity |
| R5 ReWOO | 2 total | **5$\times$ cheaper than R4** | All tool calls must be independent |
| R6 Self-Ask | 1 + N follow-ups | Medium | Sub-question depth drives cost |
| R7 Reflexion | N $\times$ retries | High | Needs measurable success criterion |
| R8 Self-Refine | N iterations | Medium | In-session; no separate judge |
| R9 ToT | N (branching) | Very High | Use when path genuinely unknown |
| R10 LATS | N (tree search) | Highest | Highest quality; highest cost |
| R11 BoT | 1 + template | Low | Templates amortise across calls |
| R12 SoT | 1 + N parallel | Medium | Latency win via parallelism |
| R13 CodeAct | N (with execution) | Medium | Self-debugging loop |
| R14 PoT | 1 + execution | Low | Deterministic computation free |
