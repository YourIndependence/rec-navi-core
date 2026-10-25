---
name: addressing-review-findings
description: Implement confirmed PR review fixes in independent per-category branches, validate them with existing skills, and create repair PRs when authorized by the caller.
---
# Address review findings

Inputs: repository, original PR/base/head and pinned head SHA, confirmed finding
and thread IDs, categories, proposed fixes, artifact directory, posting policy,
and prior execution record. Execution/delivery must be authorized by the caller;
`/review` authorizes this workflow except in `onlocal`.

## Plan and isolate

1. Deduplicate candidates by root cause, group by category, and preserve links to
   original comments. Check existing repair PRs/branches before creating duplicates.
   Conflicting cross-category repairs must be reported rather than stacked silently.
   Admit only confirmed Introduced/Worsened defects as automatic repair candidates.
   Existing-thread candidates need the same provenance check against the PR base.
   Pre-existing debt and optional Improvements remain reported proposals unless the
   user explicitly authorized their repair; severity alone does not expand scope.
2. In `local-only`, return a repair proposal table and stop. Never edit sources,
   create worktrees/branches, commit, push, or post.
3. Capture the original worktree/branch and dirty state. Create a separate worktree
   per category from the pinned original PR head, not `dev` or another repair branch.
   Process categories sequentially. Use collision-safe branch names. Never reset,
   stash, clean, or overwrite user work. If the PR head moved, report the mismatch
   and defer delivery until the repair can be based on reviewed current content.

## Implement and validate

4. Apply concrete minimal fixes and meaningful regression tests, respecting project
   layer, typing, async, and testing rules. Do not treat an uncertain finding as
   permission for speculative redesign.
5. Apply `record-architectural-decision` only when implementation introduces or
   changes an architectural decision. Merely detecting an ADR coverage gap is not
   a reason to create one.
6. Apply `quality-gate` in `implementation` mode with the repaired related-component
   scope; it delegates the required all-ADR assessment to `review-with-adrs`.
   Never reuse original-PR check success for modified repair content.
   Do not create or push a repair PR
   when required checks fail, are blocked, or were not run. Preserve failed local
   work and report it; continue independent categories where possible.

## Deliver

7. Apply `draft-pr` with explicit change scope, base=original PR head branch,
   finding/thread IDs, validation evidence, and `output=artifact`. It only generates
   title/body; this skill owns commit/push/creation. Commit only intended files.
8. Push and create a PR with `gh pr create --body-file <path>` targeting the original
   PR branch. Recheck its head before delivery. Record actual branch, SHA, PR URL,
   and validation state; never claim CI passed without observing it.
9. Reply to related review threads with the created PR URL, reconciling prior writes
   before retrying. Do not mark the original issue fixed merely because a PR exists.
10. Leave the user's original worktree untouched. Remove only clean, task-owned
    temporary worktrees after verifying their exact paths; preserve failed/dirty
    work and report its location privately to the caller.

Return one Japanese table: PR/proposal or failure, related finding/thread IDs,
validation status, remaining limitations. Include reply URLs and delivery failures
in the execution record. Do not edit `review_result.md`, publish an aggregate
summary, or print detailed output when the caller requests artifacts only.
