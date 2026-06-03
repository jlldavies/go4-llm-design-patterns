# GO4 — Open Questions and Research Gaps

*Living document. Not included in the PDF build.*

---

## Open Questions and Research Gaps

1. **Long-running agent session coherence**: No consensus on preventing context drift over hours/days
2. **Agent trust hierarchies**: How does Agent B verify that instructions from Agent A are legitimate? (V3 partially addresses; V4 for data; nothing for instruction provenance)
3. **Agent versioning and compatibility**: When a tool or sub-agent is updated, how do orchestrators handle the change?
4. **Cost-aware pattern selection**: Dynamic switching between R5 (ReWOO) and R4 (ReAct) based on runtime cost signals
5. **Cross-model composition**: No established patterns for mixing models from different providers in one pipeline
6. **O10 (Swarm) production viability**: No consensus on when peer-to-peer emerges, vs degrade to O7
7. **Multi-agent consistency**: Per-agent K10 stores create divergent memory; shared substrates are proposed but not standardised
8. **Prompt injection at orchestration layer**: V6 patterns are ad hoc; CaMeL is promising but not widely adopted
9. **Evaluation for long-horizon tasks**: V16/V17 evaluate per-interaction; no consensus on task-completion evals for multi-hour agent runs
10. **Should there be a Category 0**: "When not to use AI" — currently embedded in anti-patterns A2 and A13
11. **Humanizer identity continuity across model upgrades**: When the base model changes, does the agent's accumulated identity survive? No established pattern.
12. **Lesson library poisoning**: H2 (Episodic Self-Improvement) is vulnerable to adversarially-induced wrong lessons persisting across sessions — no defense pattern yet
13. **Constitutional evolution convergence**: Does H5 converge to a stable set of principles or continue drifting? What terminates the evolution?
14. **Authentic vs. simulated identity**: Philosophical question with practical implications — does H1 create genuine continuity or a performance of continuity? Matters for trust calibration.
15. **Cross-agent humanizer state**: If multiple agent instances run simultaneously, how do they share (or isolate) H1–H10 state without racing?

---

## Next Steps

- [ ] Cross-pattern conflict and tension map (patterns/CONFLICTS.md)
- [ ] Build explicit relationship graph: what composes, what conflicts, what requires what
- [ ] Add code examples (Python + TypeScript) for key patterns
- [ ] Define formal "forces" for each pattern
- [ ] Consider POSA format as alternative to GoF for non-OOP patterns
- [ ] Workshop "Category 0: When Not to Use AI"
- [ ] Map each pattern to SDLC phase
- [ ] Add empirical evidence table (quantified results vs. qualitative only)
