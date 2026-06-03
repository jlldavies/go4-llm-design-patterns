---
id: I3
title: MCP Server
type: pattern
category: Integration
summary: "Expose a set of tools through a separate protocol-conformant server so multiple agents and clients can discover, authenticate, and invoke those tools without per-agent integration code — accepting the resulting schema-token cost as a first-class budget item.."
when_to_use: Standardised tool discovery; 5+ tools shared across agents
also_known_as: [Model Context Protocol, MCP, Tool Server, Standardised Tool Discovery, "\"the npm of AI tools\""]
conflicts_with: [V13]
mechanism_refs: [2, 5, 6, 8]
canonical: patterns/I3-MCP-Server.md
derived: true
---

## Description
Expose a set of tools through a separate protocol-conformant server so multiple agents and clients can discover, authenticate, and invoke those tools without per-agent integration code — accepting the resulting schema-token cost as a first-class budget item. In tension with V13. This is a condensed digest; the canonical file (`patterns/I3-MCP-Server.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- 5+ tools must be shared across multiple agents, clients, or developers — the integration cost of doing this per-framework exceeds the schema-token cost of MCP;
- credential isolation matters — the server holds API keys, OAuth tokens, database credentials; the agent's process never sees them;
- tools must run in a different process, language, or trust boundary than the agent — separation is enforced by the protocol;
- a high-quality pre-built server already exists for the integration you need (GitHub, Slack, Postgres, Filesystem, Fetch, Git, Notion, Linear) — taking the ecosystem benefit;

Related: [[V13-Tool-Budget]]
