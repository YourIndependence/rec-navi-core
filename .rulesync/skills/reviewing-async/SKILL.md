---
name: reviewing-async
description: Review asynchronous I/O, awaiting, task cancellation, concurrency correctness and resource lifecycle across related request paths.
---
# Review async correctness

Apply [the shared review contract](../reviewing-pr/REVIEW-CONTRACT.md), including
related unchanged components, all four provenance classes, per-area verdict and
artifact-only output. Return analysis only; consume quality-gate/ADR evidence.

Trace request, tool, background, streaming, and cleanup paths. Check missing await,
blocking calls in async functions (sync HTTP/file I/O, time.sleep), asyncio.run in
an active async context, async context-manager use, and resource/session closure.
Examine cancellation, timeouts, task ownership, exception propagation, races and
shared mutable state. Distinguish safe sync pure computation or explicit offloading
from blocking I/O. Verify independent work is concurrent only when correctness and
resource limits permit; do not demand gather for dependent operations.

Own execution correctness; Performance owns the efficiency of correct concurrency.
ADK owns callback/framework ordering. Cite the actual I/O implementation and affected
caller, not async naming alone.
