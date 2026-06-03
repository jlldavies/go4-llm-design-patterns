---
id: DECISION-orchestration
title: Orchestration — Decision Guide
type: decision-guide
summary: How to choose among Orchestration patterns.
canonical: patterns/ORCHESTRATION-DECISION.md
derived: true
---

## Primary Decision Flow

```
Is the task solvable with a single LLM call + tools?
  YES → O1 (Single Agent) + appropriate Signal and Reasoning patterns

  NO:
    Does the task decompose into FIXED sequential steps?
      YES → O2 (Prompt Chaining)

    Are there distinct input TYPES needing specialisation?
      YES → O3 (Routing)

    Are sub-tasks INDEPENDENT and can run in parallel?
      YES → O4 (Parallelization)
        + O18 (Cache-Warmed Worker Pool) if workers share a prefix >1024 tokens

      NO → O6 (Orchestrator-Workers) + R4 (ReAct) inside workers
           + O17 (Agent Isolation) — REQUIRED companion to O6

Does output quality matter AND can it be verified objectively?
  YES → O5 (Evaluator-Optimizer) or R7 (Reflexion)

Are there distinct specialised roles exceeding a single context?
  YES → O7 (Supervisor Hierarchy)

Do agents need to share state asynchronously across turns?
  YES → O11 (Blackboard) or K10 (Long-Term Memory shared substrate)
```

## Composition Law

Most production systems are: `O6 + O4 + R4 (per worker) + O17 + O18`

- O6 without O17 loses the n² cost bounding that produces the quality win
- O4 without O18 misses ~85% cost reduction on shared worker context
- O16 (Hybrid Control Flow) describes most real agents — stacked primitives, not a single pattern

## Cost Escalation by Pattern

| Pattern | Relative cost | When justified |
|---|---|---|
| O1 Single Agent | Baseline | Default; increase complexity only when this fails |
| O2 Prompt Chaining | Low | Fixed decomposition; fully testable |
| O3 Routing | Low + classifier | Distinct specialised inputs |
| O4 Parallelization | N$\times$ but parallel | Independent sub-tasks; latency matters |
| O5 Evaluator-Optimizer | 2$\times$ + loop | Objective quality criterion exists |
| O6 Orchestrator-Workers | High | Dynamic decomposition required |
| O7 Supervisor Hierarchy | Very high | O6 applied recursively; most complex tasks |