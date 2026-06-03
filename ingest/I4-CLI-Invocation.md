---
id: I4
title: CLI Invocation
type: pattern
category: Integration
summary: "Let the agent use the existing CLI ecosystem as its tool surface — invoking `git`, `docker`, `gh`, `kubectl`, cloud CLIs, and Unix utilities directly — so the integration carries zero schema-token overhead and inherits decades of battle-tested behaviour."
when_to_use: Wrap an existing CLI as an agent action
also_known_as: [Shell Tool, Command-Line Integration, POSIX Tool Use, Bash Tool, Terminal-First Agent]
siblings: [I2, I3]
related: [I1, V8]
composes_with: [V6, V9, V11, V14, V1, R4, R13]
mechanism_refs: [2, 3, 10]
canonical: patterns/I4-CLI-Invocation.md
derived: true
---

## Description
Let the agent use the existing CLI ecosystem as its tool surface — invoking `git`, `docker`, `gh`, `kubectl`, cloud CLIs, and Unix utilities directly — so the integration carries zero schema-token overhead and inherits decades of battle-tested behaviour. Composes with V6, V9, V11, V14, V1, R4, R13. Sibling of I2, I3. This is a condensed digest; the canonical file (`patterns/I4-CLI-Invocation.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- the underlying operation already has a mature CLI (`git`, `docker`, `gh`, `kubectl`, `aws`, `gcloud`, `terraform`, `psql`, `jq`, `rg`, `sed`, `awk`);
- the CLI's documentation is in the model's training data — established, long-stable tools, not last-week's internal binary;
- token budget matters and an equivalent I3 server would consume tens of thousands of tokens on schemas alone;
- the agent runs in an environment where a sandboxed shell is acceptable (V8) — a developer workstation, a CI runner, a container;

Related: [[V6-Prompt-Injection-Shield]] · [[V9-Bounded-Execution]] · [[V11-Error-Compaction]] · [[V14-Trajectory-Logging]] · [[V1-Human-in-the-Loop]] · [[R4-ReAct]] · [[R13-CodeAct]] · [[I2-Function-Call]] · [[I3-MCP-Server]] · [[I1-Direct-API]] · [[V8-Tool-Sandboxing]]
