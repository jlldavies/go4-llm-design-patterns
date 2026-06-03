---
id: I5
title: Agent Card
type: pattern
category: Integration
summary: "Make an agent self-describing on the open web: serve a stable JSON document at a well-known path that names its identity, skills, endpoint, authentication, and protocol version, so other agents can locate it, verify compatibility, and call it without hard-coded configuration.."
when_to_use: Publish self-describing JSON for agent discovery
also_known_as: [Agent Manifest, Capability Declaration, Well-Known Agent Descriptor, AgentCard]
mechanism_refs: [2, 4, 5]
canonical: patterns/I5-Agent-Card.md
derived: true
---

## Description
Make an agent self-describing on the open web: serve a stable JSON document at a well-known path that names its identity, skills, endpoint, authentication, and protocol version, so other agents can locate it, verify compatibility, and call it without hard-coded configuration. This is a condensed digest; the canonical file (`patterns/I5-Agent-Card.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- multiple agents — particularly from different teams, vendors, or organisations — must find each other dynamically;
- the agent is designed to receive tasks from *other agents*, not only from human users (an A2A server, in protocol terms);
- the system implements or plans to implement **I6 A2A Delegation**, the Agent2Agent protocol, or any of its peers (ACP, ANP);
- capability versioning matters and you want compatibility checks before invocation rather than at failure time;
