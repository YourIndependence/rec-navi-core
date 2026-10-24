---
name: reviewing-adk
description: Review ADK-specific agent, tool, callback, instruction, session and Runner contracts using the installed framework and repository patterns.
---
# Review ADK contracts

Apply [the shared review contract](../reviewing-pr/REVIEW-CONTRACT.md), including
related unchanged components, all four provenance classes, per-area verdict and
artifact-only output. Return analysis only; consume quality-gate/ADR evidence.

Inspect dynamic and legacy static agent construction, tool binding/injection,
callback signatures/order, instruction and description providers, transfer trees,
model inheritance, session/state/event lifecycle, streaming and runner plugins.
Check real framework behavior from local dependency source or authoritative evidence;
do not assume every Agent must live in a legacy static factory directory.

Use supplied ADR results for dynamic/static exceptions, registration ownership and
the sole Runner-instantiation boundary. Architecture owns those structural findings;
this skill owns runtime ADK misuse. Link async I/O defects to Async and lack of
contract assertions to Testing. Check unchanged factory/runner callers after contract
changes and account for accepted temporary implementations.

First establish whether ADK code or dependencies exist in the pinned checkout.
If absent or unrelated, return Not applicable with evidence; do not require TRUST
AgentRegistry, tool_registry, or Runner boundaries that this repository does not have.
Apply framework ownership requirements only when supported by current repository ADRs.
