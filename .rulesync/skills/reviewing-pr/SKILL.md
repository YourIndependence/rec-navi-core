---
name: reviewing-pr
description: Orchestrate eight specialist PR reviews across related components, consolidate revision-bound quality and ADR evidence, and return per-area verdicts and deduplicated findings.
---
# Orchestrate PR review

Read [REVIEW-CONTRACT.md](REVIEW-CONTRACT.md) for shared scope, provenance, verdict,
severity/confidence, and output rules. This skill owns review coordination, not
quality-command execution, ADR auditing, source edits, or GitHub publication.

## 1. Prepare shared inputs

Receive pinned base/head, complete diff/file list, exploration, existing threads,
quality-gate evidence with its all-ADR matrix, and artifact destination. Read project
coding rules and identify the related component scope. Reuse exploration; request
`exploring-codebase` only for missing context. Never drop changed files for PR size.
Missing validation does not prevent independent analysis, but remains explicit.

## 2. Delegate eight areas

Invoke all eight skills; Not applicable still needs a reason. The skill directories
are siblings, not nested copies. Pass the shared input and requested scope to each.

| Area | Skill | Primary ownership |
|---|---|---|
| Architecture | `reviewing-architecture` | Component consistency/uniformity, responsibilities, concern boundaries, DI and design fitness |
| Type Safety | `reviewing-type-safety` | Types, models, validation and data contracts |
| Async | `reviewing-async` | Async I/O, cancellation and resource/task lifecycle |
| ADK | `reviewing-adk` | ADK-specific agent/tool/callback/session/Runner runtime contracts |
| Security | `reviewing-security` | Authorization, isolation, trust boundaries and information protection |
| Performance | `reviewing-performance` | I/O volume, concurrency, memory and execution cost |
| Code Quality | `reviewing-code-quality` | Readability, naming, local complexity, error handling and maintainability |
| Testing | `reviewing-testing` | Behavior-to-test coverage, assertions, test boundaries and regression evidence |

Use the existing reviewer/architect subagents as execution roles when available;
they follow the assigned specialist contract rather than their own duplicated rules.
Delegation need not mean one concurrent agent per skill. Merge artifact results in
the parent; specialists never write the aggregate report. Architecture consumes the
quality-gate ADR matrix, rather than invoking `review-with-adrs` itself.

## 3. Reconcile evidence and observations

Validate scope, evidence, provenance, confidence and verdict for every area. Request
missing analysis instead of inventing success. If specialist scope exceeds the ADR
matrix, return the explicit delta to the caller for one quality-gate supplement,
then propagate updated evidence to affected specialists. Missing supplementation
means verification incomplete. Standalone callers likewise provide quality-gate
results or receive unverified status; do not silently launch duplicate checks.

Merge observations sharing a root cause into one R-NNN finding with one primary
area and related-area references. Preserve all eight verdicts/evidence references,
without counting or posting that finding twice. Use [CHECK-RULES.md](CHECK-RULES.md)
for ownership boundaries. Existing debt is included for every area, not Architecture
alone. Preserve accepted exceptions and actual check failures honestly.

## 4. Return once complete

Return eight verdict rows (area, verdict, Introduced/Worsened finding IDs,
Pre-existing/Improvement IDs, limitations), canonical findings, architecture
assessment, the supplied complete ADR matrix, Testing's detailed coverage matrix
and counts, checked scope, blockers, and scope deltas.

Preserve [REPORT-FORMAT.md](REPORT-FORMAT.md) in its original English form. Its legacy
confidence ranges are presentation examples; this contract's independent severity
and confidence govern classification. Add provenance/related-area metadata without
redefining the original fields. The caller owns report assembly, aggregate decision,
comment URLs, publication, and repair delivery.
