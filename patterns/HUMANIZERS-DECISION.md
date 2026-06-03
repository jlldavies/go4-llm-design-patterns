# Humanizer Pattern Selection

## Decision Flow

```
Does the agent run across multiple sessions?
  NO → Humanizer patterns do not apply; use Signal patterns for in-session persona

  YES — start here:
    H1 (Identity Persistence) — PREREQUISITE for all other Humanizer patterns
    Stable identity must exist before it can evolve

    After first failures emerge:
      H2 (Episodic Self-Improvement) — learn from mistakes across sessions
        Requires: K11 or K10 as memory substrate

    After first successes:
      H4 (Procedural Skill Accumulation) — distil successful trajectories into reusable skills
        Complements H2: H2 learns from failure, H4 from success

    As user model grows:
      H7 (Adaptive Persona) — adapt communication style per user
      H10 (Relational Memory) — persist user relationship state
        ⚠ H10 requires explicit user consent and right-to-deletion

    When reasoning loops stall or creativity degrades:
      H3 (Entropy-Driven Curiosity) — autonomous deadlock breaking

    For persistent background reasoning between turns:
      H6 (Continuous Inner Monologue) — separate thinker from responder

    For accurate self-knowledge and capability routing:
      H9 (Observational Identity) — explicit model of own capabilities

    With human governance board and formal oversight:
      H5 (Constitutional Self-Alignment) — evolving principles with mandatory checkpoints
        ⚠ NEVER implement H5 without mandatory human review; alignment risk
```

## Adoption Sequence

| Stage | Patterns | Purpose |
|---|---|---|
| Foundation | H1 | Stable identity across sessions |
| Learning | H2 + H4 | Improve from failure and success |
| Adaptation | H7 + H10 | Serve users better over time |
| Advanced | H3 + H6 + H9 | Autonomous, self-aware operation |
| Governed | H5 | Evolving principles with oversight |

All Humanizer patterns require K11 (Observational Memory) or K10 (Long-Term Memory) as infrastructure. H1 is a prerequisite for all others.

## Anti-Patterns

- **HA1 — Simulated Emotion**: emotional language without genuine affective model (manipulation)
- **HA2 — Unbounded Relationship Depth**: H10 without ethical guardrails $\to$ parasocial harm
- **HA3 — Identity Drift**: H7/H10 without H1 $\to$ agent becomes whoever the user wants
- **HA4 — Autonomous Principle Adoption**: H5 without human review $\to$ alignment risk
- **HA5 — Stale Self-Model**: H9 without decay functions $\to$ overconfident outdated self-assessment
