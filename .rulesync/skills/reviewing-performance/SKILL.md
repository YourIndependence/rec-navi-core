---
name: reviewing-performance
description: Review I/O amplification, concurrency, memory use, query scope and execution cost using concrete related call paths.
---
# Review performance

Apply [the shared review contract](../reviewing-pr/REVIEW-CONTRACT.md), including
related unchanged components, all four provenance classes, per-area verdict and
artifact-only output. Return analysis only; consume quality-gate/ADR evidence.

Trace request counts and data volume across loops, users, agents, retries and tools.
Look for N+1, repeated external calls without appropriate reuse, unbounded results,
large whole-file loads where streaming is feasible, and unnecessary repeated model
or initialization work. Evaluate batching/caching against authorization, freshness,
lifecycle and invalidation requirements; caching is not automatically preferable.

Assess concurrency limits, backpressure and CPU-heavy work on request paths. Explain
scale assumptions and cost with evidence; do not invent benchmark numbers. Unneeded
real-service setup in unit tests is primarily Testing, with performance consequences
linked. Async owns cancellation/race correctness; this skill owns efficiency.
