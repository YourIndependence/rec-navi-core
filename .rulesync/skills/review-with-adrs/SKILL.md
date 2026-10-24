---
name: review-with-adrs
description: Inventory every ADR and assess applicability and compliance across the supplied component scope, reusing Archgate evidence without duplicate automated runs.
---
# Review with ADRs

Inputs: pinned revision/diff, related-component scope when supplied, quality-gate
Archgate evidence (command, revision, status, output), artifact destination. This
skill owns the single ADR audit, not code repair or aggregate report publication.

## Automated evidence

Reuse Archgate results only when the revision AND working-tree state match.
`quality-gate` owns execution and audit orchestration. Consume its evidence; do not
execute Archgate yourself or recursively invoke quality-gate. If called standalone
without automated evidence, assess manual applicability and return NOT RUN/BLOCKED
automation to the caller, who obtains it through quality-gate. Do not infer a
complete passing gate or install tools/rewrite symlinks implicitly.
CI execution is not proof of success: inspect the dedicated job for the exact SHA
or mark NOT RUN/BLOCKED. Distinguish rule violations from tool/configuration errors;
exit code 1 alone is insufficient evidence of a code violation.

## Manual compliance

Inventory and read every ADR in `docs/adrs/`, including context, decisions, rationale,
and Compliance requirements; do not select documents only by filenames or diff globs.
Include deprecated/superseded decisions to establish status and replacement, but
enforce the active decision. Read the deviation register as supporting evidence,
not as an active ADR. Record unreadable or unparseable decisions as BLOCKED, not
non-applicable. No ADR may be omitted from the matrix.

For each ADR, assess applicability to all changed files and the supplied related
components, including unchanged callers/implementations. If no expanded scope is
supplied, use the caller's review scope and disclose that limit. Check both automated
and human requirements: a passing rule does not prove the whole decision is satisfied.
Return one row per ADR: ID/link, lifecycle status, applicable components or reason
not applicable, automated evidence/status, manual verdict, evidence/exception,
and related finding IDs. Manual verdicts are PASS, FAIL, NOT APPLICABLE, or BLOCKED.
An applicable ADR needs concrete evidence for PASS; a non-applicable one needs a
reason; unavailable context means BLOCKED. A mixed result reports FAIL with blocked
portions explicitly listed. Do not present NOT APPLICABLE as a passing check.
- Explicit mandatory prohibition violated: Critical.
- Required practice omitted: Important unless high-impact/mandatory constraints
  justify Critical.
- Ambiguous preference: evidence-backed Suggestion, not a fabricated violation.

Separate pre-existing violations from those introduced or worsened by the PR.
Classify violations as Introduced, Worsened or Pre-existing with base evidence;
optional gaps/proposals are Improvements. Return existing violations with impact
and severity, not as new PR defects; retain actual check failures. Deduplicate ADR and
code-review findings by root cause. Identify architectural coverage gaps, but do
not create an ADR during read-only review; return the gap to the caller.

Return the complete all-ADR matrix, automated status/evidence, manual status, violations with
file/line/ADR/fix/confidence, gaps, and blockers. No findings below confidence 80.
Use artifact-only output when requested. Do not edit `review_result.md` or publish.
For supplementation, receive the prior matrix and explicit scope delta; inspect
uncovered components/decisions and merge a full matrix with the previous evidence.
Never treat a new component as covered just because an ADR row already existed.
