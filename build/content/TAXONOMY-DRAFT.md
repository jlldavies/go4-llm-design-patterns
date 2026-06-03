# GO4 Taxonomy

*A pattern language for AI engineering, structured analogously to the Gang of Four.*

---

## The Seven Categories

The original GoF had three categories: Creational, Structural, Behavioural. AI engineering patterns span more distinct concerns:

| Category | Governs | Analogy to GoF |
|---|---|---|
| **I. Signal** | How you shape instructions, personas, and examples | Creational — what gets built from what |
| **II. Knowledge** | What information and memory the model has access to | Structural — how things are assembled and connected |
| **III. Reasoning** | How a model structures its thinking process | Behavioural (individual) |
| **IV. Orchestration** | How agents coordinate, delegate, and interoperate | Behavioural (collective) |
| **V. Reliability** | Safety, cost, governance, observability | Cross-cutting / NFR |
| **VI. Integration** | How agents connect to tools, services, and each other | Infrastructure / Connective tissue |
| **VII. Humanizers** | How agents develop continuity, identity, and adaptive evolution | Emergent / Longitudinal |

---

**Signal patterns** govern how instructions, personas, and examples are shaped before the model sees them — the prompt design surface.

**Knowledge patterns** govern context engineering: what information and memory the model has access to during a task, and how that context is assembled, retrieved, compressed, and persisted.

**Reasoning patterns** govern how a model structures its thinking: chain-of-thought, planning, tool use, reflection, search, and verification.

**Orchestration patterns** govern how multiple inferences and agents are coordinated — chains, routers, parallel workers, hierarchies, and multi-agent collectives.

**Reliability patterns** govern the cross-cutting concerns that production systems cannot omit: safety bounds, cost control, observability, evaluation, and recovery.

**Integration patterns** govern how agents reach the world outside their prompt: deterministic API calls, typed tool calling, standardised protocol servers, and inter-agent delegation.

**Humanizer patterns** govern the longitudinal layer: how agents develop continuity, self-knowledge, and adaptive behaviour across sessions.
