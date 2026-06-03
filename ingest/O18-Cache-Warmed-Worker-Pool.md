---
id: O18
title: Cache-Warmed Worker Pool
type: pattern
category: Orchestration
summary: "Design the shared context given to all parallel workers as a single stable, cacheable prefix; fire a warm-up call (or time the first worker call) to establish that prefix in the provider KV cache; then dispatch all remaining workers within the cache TTL — so the shared portion of each worker's prompt is served from cache at ~10% of the normal prefill cost rather than re-computed independently for each worker.."
when_to_use: Establish cacheable shared prefix before fan-out — ~85% cost reduction on shared context
also_known_as: [Primed Agent Pool, Prefix-Warm Fan-Out, Shared Context Warming]
mechanism_refs: [2, 5, 6, 8]
canonical: patterns/O18-Cache-Warmed-Worker-Pool.md
derived: true
---

## Description
Design the shared context given to all parallel workers as a single stable, cacheable prefix; fire a warm-up call (or time the first worker call) to establish that prefix in the provider KV cache; then dispatch all remaining workers within the cache TTL — so the shared portion of each worker's prompt is served from cache at ~10% of the normal prefill cost rather than re-computed independently for each worker. This is a condensed digest; the canonical file (`patterns/O18-Cache-Warmed-Worker-Pool.md`) carries the full decision criteria, failure modes, and implementation.

## Key points
- you are running O4 Parallelization or O6 Orchestrator-Workers with a pool of workers that share a substantial common prompt prefix;
- the shared prefix exceeds the provider minimum for prefix caching (1,024 tokens for Anthropic);
- all workers will be dispatched within the provider TTL window (~5 minutes for Anthropic);
- the shared prefix is stable — it does not change between the warm-up call and the worker calls, and it does not vary across workers.
