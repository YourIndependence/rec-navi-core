---
name: reviewing-architecture
description: Review consistency with existing implementations, unified responsibilities and contracts, all ADRs, and the design quality of the related component system beyond the PR diff.
---
# Review architecture

Apply [the shared review contract](../reviewing-pr/REVIEW-CONTRACT.md). Inputs include
pinned base/head, full diff, exploration, discussion results, artifact destination,
and quality-gate evidence with its all-ADR matrix. Return analysis only; no source
edits, ADR creation, publication, quality-command execution or aggregate-file writes.

## 1. Establish the component scope

Reuse `exploring-codebase` results; request focused exploration only for missing
context. Trace changed behavior through callers, dependency implementations,
public schemas, domain models, registries, storage, configuration, and tests.
Find analogous implementations of the same responsibility elsewhere in the repo.
Read unchanged components too: the unit of review is the related component system,
not only edited lines. Record included components, relationships, and why the scope
ends there. Record unavailable context instead of implying exhaustive coverage.

## 2. Evaluate design quality

Check the following against concrete existing implementations and requirements:

- Consistency: do callers, schemas, permissions, defaults, errors, persistence,
  lifecycle, and configuration describe and implement the same contract?
- Uniformity: are names, types, update semantics, initialization, and failure
  handling aligned with equivalent components? Find duplicated responsibilities,
  competing abstractions, parallel paths, and independently maintained sources
  of truth. Do not confuse justified domain differences with accidental divergence.
- Ownership: do layer boundaries, dependency direction, DI/registries, and models
  place each responsibility with its owner? Review separation of concerns and
  whether the boundaries between concerns are appropriate: identify unrelated
  concerns coupled in one component, a single concern fragmented across components,
  and implementation details leaking across interfaces. Judge cohesion and coupling
  against actual responsibilities and change patterns, not layer names alone.
  Inspect effects on unchanged callers.
  Check core/infrastructure dependency inversion, API/application boundaries,
  injected abstractions rather than concrete external clients, registry ownership,
  role-specific dependency bundles, dependency-first signatures/calls, and package
  initialization/re-export rules against the supplied current ADR requirements.
  Apply agent/framework patterns only if present in the reviewed checkout; do not
  assume TRUST registries exist. Use `core/database/base_database.py` and
  `core/storage/base_object_storage.py` for injected boundaries. Check media
  `to_storage_item()` persistence against ARCH-002 and existing-project access
  through `Project.validate_permission(...)` against ARCH-013, rather than
  duplicated caller-side owner/group comparisons. Route async I/O, test-boundary and ADK execution
  defects to their primary specialist while retaining architectural consequences.
- Whole-system suitability: does a local addition increase coupling or create
  special cases that reuse, consolidation, or deletion could avoid? Compare the
  current approach with a concrete simpler alternative, including compatibility,
  migration cost, testability, performance, and operational consequences.
- Proportionality: keep an existing design when benefits of replacement do not
  justify the cost. Do not call a design suboptimal based on style, abstraction
  count, speculative future needs, or preference alone.

## 3. Consume the complete ADR audit

Consume quality-gate's delegated `review-with-adrs` result; do not invoke that skill
or Archgate independently. Require every ADR row with applicability, manual verdict,
evidence and exception/supersession rationale. Read decisions needed for design
reasoning without repeating the audit. Missing rows/evidence remain unverified.
If the related-component scope expands, return the delta to `reviewing-pr` (or the
standalone caller) for quality-gate supplementation and reuse the updated result.

With that evidence, use the existing `architect` subagent in review mode
when available. Pass the full component scope, pinned revision, audit results,
and this skill's assessment/output contract. The parent assembles one result.
If the subagent is unavailable, perform the same assessment directly.

## 4. Classify and return

Use the common provenance, severity/confidence, verdict, and automatic-repair rules.
All eight areas include Pre-existing/Improvement observations, not this skill alone.
Optional A-NNN architecture references must map to the parent's canonical R-NNN IDs.

Return, once complete:

1. Scope and overall architectural assessment, including favorable conclusions.
2. An observation table: ID, provenance (Introduced/Worsened/Pre-existing/Improvement),
   severity, components/pinned evidence, concern and impact, recommendation and
   tradeoffs, migration/verification plan, confidence, related R-NNN/thread IDs.
3. References to the supplied all-ADR matrix, status, and any scope delta.
4. Limits, unresolved questions, accepted exceptions, and gaps in existing ADRs.

Use artifacts only in quiet mode. Keep detailed exploration outside the aggregate
report; retain enough evidence to assess every conclusion and every ADR row.
