---
id: V14
title: Trajectory Logging
type: pattern
category: Reliability
summary: "Make every step the agent takes visible as a structured event, in a vendor-neutral format, so that debugging, auditing, evaluation, and monitoring can all read from the same record — instead of each rebuilding the run from fragmentary logs.."
when_to_use: "OTel-compatible trace of every call, action, and observation"
also_known_as: [Agent Trace, OTel for Agents, Audit Log, GenAI Telemetry, Span-Based Observability]
mechanism_refs: [3, 7]
canonical: patterns/V14-Trajectory-Logging.md
derived: true
---

## Description
Make every step the agent takes visible as a structured event, in a vendor-neutral format, so that debugging, auditing, evaluation, and monitoring can all read from the same record — instead of each rebuilding the run from fragmentary logs. This is a condensed digest; the canonical file (`patterns/V14-Trajectory-Logging.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the agent is heading for production — V14 is universal there, not optional;
- multiple subsystems (debugging, audit, eval, monitoring) need to read the same run record;
- the agent has more than one step, more than one tool, or more than one collaborating component;
- regulated industries (healthcare, finance, legal) require an audit trail by law;
