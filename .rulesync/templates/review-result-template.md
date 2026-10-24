# Aggregate review result template

Use this structure for review_result.md. Translate aggregate headings/prose into
Japanese at runtime, but preserve the existing English finding format from
reviewing-pr/REPORT-FORMAT.md. Replace placeholders at finalization. Empty sections
use an explicit None; unexecuted checks use NOT RUN. No preparation logs or
per-substep reports belong here.

Keep `## PR Summary` as the first section. Describe the PR's purpose and resulting
behavior in one or two sentences, based on the actual diff as well as its description.
Use one table row per logically changed function/module, grouping related changes
instead of listing every diff hunk. Use repository-relative paths and symbols.
For non-runtime files, use an appropriate layer such as Tooling, Tests, or Docs.
`Change Type` describes the artifact (Added / Removed / Modified); the responsibilities
column describes which responsibilities or concerns were added, removed, or changed.
Do not confuse a modified module with a newly added responsibility within it.

```markdown
# Review Results

PR: [#<number> - <title>](<url>)
Reviewed: `<head SHA>` / Timestamp: <ISO 8601 timestamp>

## PR Summary

<One or two sentences describing why the PR exists and what behavior it changes.>

| Layer | Function / Module | Change Type | Responsibilities / Concerns Changed | Change Summary |
|---|---|---|---|---|
| <apis / application / core / infrastructure / Tooling / Tests / Docs> | `<path>::<symbol>` or `<module path>` | <Added / Removed / Modified> | <Added: ...; Removed: ...; Modified: ...; include applicable entries only> | <Concrete implementation or behavior change> |

## Verdict

| Review Area | Verdict | Introduced / Worsened | Existing Issues / Improvements | Limitations |
|---|---|---|---|---|
| Architecture | <verdict> | <R-NNN / None> | <R-NNN / None> | <scope/evidence limits or None> |
| Type Safety | <verdict> | <IDs / None> | <IDs / None> | <limits or None> |
| Async | <verdict> | <IDs / None> | <IDs / None> | <limits or None> |
| ADK | <verdict> | <IDs / None> | <IDs / None> | <limits or None> |
| Security | <verdict> | <IDs / None> | <IDs / None> | <limits or None> |
| Performance | <verdict> | <IDs / None> | <IDs / None> | <limits or None> |
| Code Quality | <verdict> | <IDs / None> | <IDs / None> | <limits or None> |
| Testing | <verdict> | <IDs / None> | <IDs / None; coverage matrix reference> | <limits or None> |

<Verdicts: No issues / Needs revision / Improvements suggested / Not applicable /
Unable to verify. Render these in Japanese at runtime; give evidence/reason for
every row, including Not applicable. Keep limitations even with Needs revision.>

Change-induced defects: Critical <N> / Important <N>
Pre-existing issues: <N> / Improvements: <N>
Overall: <Needs revision / No findings / Verification incomplete / Improvements suggested>
Verification: <Complete / Incomplete; separate from the review decision>
<If head changed, identify reviewed SHA and state current head is unreviewed.>

## Unresolved Discussions

| Thread | Issue | Status | Evidence / action |
|---|---|---|---|
| [#<id>](<url>) | <summary> | <VERIFIED / NEEDS FIX / PARTIAL / BLOCKED / OPEN> | <evidence and reply URL or local proposal> |

## Review Findings

<Insert the existing English review report from reviewing-pr/REPORT-FORMAT.md.
Keep its headings and field names; include posted comment URLs beside issues.
Summarize repeated verdict/ADR information here only once in the aggregate.>

<Use canonical R-NNN IDs, one primary area and related-area references. Add
Provenance: Introduced / Worsened / Pre-existing / Improvement as supplemental
metadata without changing the original English finding fields. Include complete
evidence for existing issues too, rather than silently filtering them out.>

## Existing Issues and Improvements

| Finding | Review Area | Provenance | Severity | Impact / Proposal | Evidence / Details |
|---|---|---|---|---|---|
| R-<N> | <primary and related areas> | <Pre-existing / Improvement> | <severity> | <concrete impact or benefit/cost> | <canonical finding/evidence reference> |

<Include observations from every area. Reference existing finding details instead
of duplicating them. Existing high-impact risks remain visible with their severity;
their age does not reduce severity or automatically authorize unrelated repairs.>

## Architecture Assessment

Scope: <related components, unchanged callers/dependencies, analogous implementations,
and boundaries/limits of the investigation>

Assessment: <consistency with existing code, uniform responsibilities/contracts,
and suitability of the component system; concrete strengths and concerns>

| ID | Provenance | Severity | Components / Evidence | Concern and Impact | Recommendation / Tradeoffs | Migration / Verification | Related Finding |
|---|---|---|---|---|---|---|---|
| A-<N> | <Introduced / Worsened / Pre-existing / Improvement> | <Critical / Important / Suggestion> | <pinned links> | <concrete consequence; confidence >=80> | <specific alternative, benefit, cost, or retain current design> | <compatibility and test plan> | <R-NNN / thread / None> |

### All-ADR Applicability and Compliance

| ADR | Lifecycle Status | Applicability / Components | Automated Evidence | Manual Verdict | Evidence / Exception / Reason | Related Finding |
|---|---|---|---|---|---|---|
| [ARCH-<N>](<pinned ADR URL>) | <active / deprecated / superseded> | <components, or reason not applicable> | <PASS / FAIL / BLOCKED / NOT RUN and evidence> | <PASS / FAIL / NOT APPLICABLE / BLOCKED> | <pinned implementation evidence, justified exception, replacement, or missing context> | <R-NNN / A-NNN / None> |

<Include every ADR; retain reasons for non-applicability and missing evidence.
Read deviation registers as supporting evidence. Do not count accepted exceptions
as unexplained violations or enforce superseded decisions as active requirements.>

## Verification

| Check | Status | Details |
|---|---|---|
| Ruff format | <PASS / FAIL / BLOCKED / NOT RUN> | <summary> |
| Ruff lint | <status> | <summary> |
| Unit tests | <status> | <counts and scope> |
| Integration tests | <status> | <scope or reason not run> |
| Archgate | <status> | <summary> |
| Manual ADR review | <status> | <checked ADR IDs and findings> |
| Architecture assessment | <status> | <reviewed scope and A-NNN references; report existing debt separately> |
| Behavior-to-test coverage | Covered <N> / Partial <N> / Missing <N> | <gap findings or no behavior changes> |

## Repair PRs

| PR | Related issues | Verification |
|---|---|---|
| [#<number>](<url>) | <finding/thread IDs> | <status and limitations> |

## Outstanding Work and Assumptions

<Blockers, failed publications, assumptions, unreviewed scope, or None.>

<!-- rec-navi-review:<run-id> -->
```

Count unique root causes, not replies or related-area references. Keep provenance
counts separate. Confirmed change-induced unresolved issues affect the verdict too.
Known change-induced blocking issues mean Needs revision; otherwise missing essential
verification means Verification incomplete. Use No findings only when required
review/checks completed with no outstanding blocking issue. Mention optional
suggestions. Repair PRs do not change the verdict about the original reviewed PR.
Use Improvements suggested when only actionable nonblocking observations remain.
All eight areas report Pre-existing/Improvement observations; these do not alone
block this PR or authorize automatic repairs. Actual failed quality-gate checks
remain failures independently of provenance. Missing required review scope or an
incomplete all-ADR audit means verification
is incomplete. Keep the full ADR table, including NOT APPLICABLE/BLOCKED reasons,
when compacting the report; remove repeated prose rather than silently omitting ADRs.
