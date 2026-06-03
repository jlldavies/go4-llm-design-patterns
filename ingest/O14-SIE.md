---
id: O14
title: Single Information Environment
type: pattern
category: Orchestration
summary: "Make data ownership the primary unit of agent specialisation, so the routing question becomes \"*which dataset holds the answer?*\" rather than \"*which capability is needed?*\", and each owner agent is tuned to one bounded corpus instead of one shared one.."
when_to_use: Agent edits its own tools
also_known_as: [SIE, Data-Centric Agent Design, Domain-Partitioned Agents, Data-Product Agents]
mechanism_refs: [1, 5]
canonical: patterns/O14-SIE.md
derived: true
---

## Description
Make data ownership the primary unit of agent specialisation, so the routing question becomes "*which dataset holds the answer?*" rather than "*which capability is needed?*", and each owner agent is tuned to one bounded corpus instead of one shared one. This is a condensed digest; the canonical file (`patterns/O14-SIE.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the underlying data is genuinely partitioned — distinct schemas, distinct sources, distinct freshness, or distinct access boundaries;
- a unified K1 RAG over the combined corpus produces confused results because vocabularies clash across domains;
- per-domain tuning matters — each dataset benefits from its own retriever, prompt, and policy;
- access control / data-sovereignty constraints require that an agent only ever sees the data it owns.
