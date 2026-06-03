# Appendix C — Anti-Patterns and Composition Examples

## Anti-Pattern Registry

| # | Anti-Pattern | Description | Costs | Better Alternative |
|---|---|---|---|---|
| A1 | **God Prompt** | All instructions in one massive prompt | Attention dilution; maintenance nightmare | Decompose with O2/O6 |
| A2 | **Over-Agentification** | Agentic loops when deterministic code suffices | Cost; latency; brittleness | O2 (Prompt Chaining) or just write code |
| A3 | **Uncontrolled Recursion** | Reflection/planning loops with no exit condition | Runaway cost; stuck agents | V9 (Bounded Execution) |
| A4 | **Agent Sprawl** | Proliferating agents without ownership or governance | Inconsistency; undebuggable | V14 (Trajectory Logging) + V1 (H-in-the-L) |
| A5 | **Output-Only Guardrails** | Safety checks only on final output | Intermediate failures propagate | V5 (Guardrail Layering) at all 4 points |
| A6 | **Vibe-Checking as Testing** | Subjective assessment replacing eval frameworks | No regression detection | V15 (LLM-as-Judge) + V16 (Offline Eval) |
| A7 | **Context Hoarding** | Never pruning context; dumping everything in | Token waste; attention degradation; cost | K6/K7 (Compress/Prune) or O17 (Agent Isolation) |
| A8 | **Synchronous Everything** | Running independent sub-tasks sequentially | Unnecessary latency | O4 (Parallelization) |
| A9 | **Stateful Reducer** | Hidden agent state not reflected in business state | Bugs; replay failure; debugging hell | V12 (Stateless Reducer) + V10 (Checkpoint) |
| A10 | **Silent Failure** | Agent fails quietly; no error surfaced | Data loss; cascading failures | V1 + V14 + V10 |
| A11 | **Framework Lock-in** | Choosing LangChain/heavy framework first | Abstraction ceiling; debugging difficulty; cost opacity | Own your control flow |
| A12 | **Tool Proliferation** | Adding tools without tool budget management | Context overflow; selection accuracy collapse | V13 (Tool Budget) + I4 (CLI first) |
| A13 | **Pilot Simplification** | Clean data/sandbox in pilot; assume production is similar | 88% production failure rate | Data realism in pilots; governance from day 1 |
| A14 | **Trust Handoff** | Agent trusts instructions from other agents without verification | Prompt injection cascading | V3 (Rule of Two) + V4 (Dual LLM) |
| A15 | **Untraced Agent** | No observability; no audit trail | Debugging takes hours not minutes; no compliance | V14 (Trajectory Logging) from day 1 |

---

## Pattern Composition Examples

### Example 1: Standard Production Coding Agent (Claude Code, Devin)
`S3 + S4 + K1 + K8 + R4 + O6 + O4 + V1 + V9 + V14 + I2/I3`

### Example 2: Research Agent
`S4 + K10 + R4 + O4 + O8 + V9 + V14`

### Example 3: Safety-Critical Enterprise Agent
`S3 + S9 + K1 + R3 + O6 + V1 + V3 + V4 + V5 + V7 + V8 + V14 + I1`

### Example 4: Customer Support Router
`O3 + O1 + K1 + K11 + V1 + V5 + V17`

### Example 5: Document Analysis Pipeline
`S2 + K6 + O2 + O5 + V5 + V16`

### Example 6: Multi-Agent Research Network
`S3 + K10 + R4 + O7 + O11 + I5 + I6 + V14`

### Example 7: Long-Term Personal Research Assistant
`H1 + H2 + H4 + H7 + H9 + H10 + K11 + R7 + V1`

### Example 8: Autonomous Creative Agent
`H1 + H3 + H6 + H7 + K10 + R4`

### Example 9: Enterprise Process Automation Agent
`H2 + H4 + H5 + H9 + V1 + V7 + V14`
