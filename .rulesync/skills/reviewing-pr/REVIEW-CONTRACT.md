# Shared specialist review contract

All eight specialist skills use this contract, including standalone invocation.

## Inputs and scope

Receive repository, pinned base/head revisions and working-tree state, complete
PR diff/file list, related-component exploration, existing threads, quality-gate
results (including the all-ADR matrix), and artifact destination when available.
Read project coding rules. Use the diff as the entry point; inspect affected
callers, dependencies, analogous implementations, public contracts, configuration,
persistence, and tests relevant to your perspective, including unchanged code.
Record the scope and why its boundary is sufficient; disclose missing context.
Do not expand into an unrelated repository-wide audit.

Analyze only: do not modify code, run quality commands, create ADRs, post to GitHub,
or edit review_result.md. Consume quality-gate evidence. If scope expands beyond
its ADR audit, return the scope delta to the parent for quality-gate supplementation;
do not independently repeat checks or the audit. In artifact-only mode return
results without detailed screen output. In standalone mode, missing other reviews
or required validation must remain unverified, never implicitly passed.

## Findings

Report evidence-backed findings with confidence >=80; confidence is independent of
severity. Critical means high-impact correctness/security or mandatory architecture
violations; Important means material defects/test gaps; Suggestion means an optional
improvement with concrete benefit. Do not turn style preferences into defects.

Assign one provenance to each observation:
- Introduced: the PR created the problem; identify the causal diff and base evidence.
- Worsened: the PR expanded an existing problem; show what worsened against base.
- Pre-existing: relevant debt present before this PR; retain evidence and consequences
  without blaming this change or suppressing it as out of diff.
- Improvement: a concrete beneficial alternative; include benefits, costs,
  compatibility/migration implications, and a verification plan.

If base evidence is unavailable, disclose uncertain provenance; do not fabricate
an Introduced/Worsened classification to enable automatic repair. Severity of an
existing issue is not reduced by its age. Urgent existing risks must remain visible.
Only confirmed Introduced/Worsened defects enter ordinary individual-comment and
automatic repair flows. Pre-existing debt and optional improvements remain in the
report; they do not alone block this PR or expand authorized repair scope. Record
actual failed quality checks separately; never convert them to PASS on this basis.

## Output

Return area name, verdict, reviewed scope, limitations, observations, quality/ADR
references, and scope deltas. Each observation includes local ID, provenance,
severity, confidence, exact pinned path/line/evidence, problem and impact, concrete
fix/alternative, verification evidence or missing scenarios, related areas/threads,
and whether an inline suggestion or structural repair is appropriate.

Area verdicts: No issues / Needs revision / Improvements suggested / Not applicable /
Unable to verify. A confirmed change-induced blocking defect means Needs revision;
otherwise incomplete required evidence means Unable to verify. Use Improvements
suggested for actionable nonblocking observations (including existing debt), with
severity visible. Not applicable requires a reason. No issues requires sufficient
scope/evidence. Preserve limitations even when the main verdict is Needs revision.

The parent deduplicates by root cause, assigns stable R-NNN IDs to all observations,
selects one primary area with related-area references, and renders the original
English reviewing-pr/REPORT-FORMAT.md fields with provenance as supplemental metadata.
Specialists do not duplicate that report template. Architecture may keep A-NNN
cross-references; the same root cause still has one canonical R-NNN ID.
