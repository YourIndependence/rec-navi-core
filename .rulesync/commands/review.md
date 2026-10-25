---
description: Review a PR, verify discussions, post findings, create validated repair PRs, and publish a final report. Supports --auto and onlocal.
targets: ["*"]
claudecode:
  skills:
    - exploring-codebase
    - reviewing-pr
    - verifying-pr-discussions
    - addressing-review-findings
    - quality-gate
    - draft-pr
    - record-architectural-decision
  allowed-tools: Read, Write, Edit, Agent, Bash(gh *), Bash(git *), Bash(uv run ruff *), Bash(uv run pytest *), Bash(archgate *), Bash(npx *), Bash(npx.cmd *), Bash(rg *), Bash(mkdir *), Bash(python *)
  disable-model-invocation: true
---
# Review

## Usage and modes

```text
/review <PR-NUMBER|PR-URL>
/review --auto <PR-NUMBER|PR-URL>
/review --auto
/review --auto <PR-NUMBER|PR-URL> onlocal
```

Parse `--auto` and `onlocal` independently of order. Reject unknown flags and
multiple targets. Without a target, resolve the PR for the current branch; stop
if ambiguous. Resolve owner/repository from the URL or checkout and pass
`--repo <OWNER/REPO>` to PR commands. Never mix repositories.

- All phases run without approval gates, preserving existing review behavior.
- `--auto`: run non-interactively. Record defensible assumptions; stop dependent
  work when essential context is unavailable. Display only brief phase progress,
  blockers, and the final URL/path. Route detailed skill results, diffs, API bodies,
  and test logs to temporary artifacts rather than screen output.
- Without `--auto`, phase summaries may be displayed.
- Both modes retain verification replies, individual Critical/Important comments,
  repair PR creation, and repair-PR replies. Only the aggregate comment is deferred.
- `onlocal` overrides both modes: no GitHub writes, source edits, checkout, branch,
  commit, push, PR creation, fetch, or other git-state changes. Read-only remote
  queries and temporary files are allowed. Record proposed actions locally.

## Ownership and artifacts

The command owns orchestration, individual finding publication, and final report
assembly. Skills own analysis/checks and return completed sections; only the parent
command writes `review_result.md`. Pass repository, pinned SHA, mode, artifact
output destination, and existing evidence to skills. Merge subagent results serially.

Read `.rulesync/templates/review-result-template.md` from the repository root
as the result template (also when running a generated copy of this command). Final prose is
Japanese; code, identifiers, and commits remain English. Update sections once per
phase, not per substep. Do not create duplicate summary/report/discussion files.
Keep detailed coverage matrices and raw logs as working artifacts outside the report.

## Phase 0: Preparation

1. Parse modes and resolve PR/repository.
2. Create a unique repository/PR/run directory beneath the OS temporary directory
   with `tempfile.mkdtemp` or an equivalent native facility; never hardcode `/tmp`.
   Reserve `review_result.md`, `pr.diff`, and `logs/`.
3. Keep a small execution record with run ID, completed phases, posted IDs/URLs,
   and repair PRs for resumption. Do not write preparation logs into the report.
   Preserve user changes and settings.

## Phase 1: PR retrieval

1. Fetch PR metadata, base/head refs and SHAs, and all changed files, paginating
   as needed. Save the full diff to `pr.diff`.
2. Pin analysis, source/test reads, and code links to the captured head SHA.
   Review every addition, modification, and deletion, including large PRs.
3. Run checks in an isolated checkout of that revision when writes are allowed.
   In `onlocal`, use an existing matching checkout; otherwise mark runtime checks
   BLOCKED and analyze read-only remote content. Never verify another revision.

No report output is needed during this phase.

## Phase 2: Context and impact

1. Apply `exploring-codebase` to affected modules, adjacent callers/dependencies,
   analogous implementations, and contracts. Record a bounded related-component
   scope for both quality-gate's ADR audit and all eight specialist reviews.
2. Classify layers and added/modified/deleted files. Prepare changed behaviors for
   `reviewing-pr`, which owns the detailed behavior-to-test analysis rules.
3. At phase end, initialize the template with concise metadata (PR link/title,
   reviewed SHA, timestamp) and the compact PR Summary description/table defined
   by the template. Leave later sections pending. Do not include exhaustive file
   inventories or exploration logs in the final report.

## Phase 3: Unresolved discussion verification

Apply `verifying-pr-discussions` at the pinned SHA, with posting disabled only in
`onlocal`. Process every unresolved thread, even with author replies. At phase end,
fill only the unresolved-thread table (status, evidence, reply URLs). Retain repair
candidates for Phase 6. Do not append per-substep results.

## Phase 4: Review and checks

1. Apply `quality-gate` in `review` mode at the exact reviewed revision with base,
   diff, related-component scope, and the full required unit suite. It owns Ruff,
   tests, Archgate and the delegated `review-with-adrs` all-ADR audit. Retain revision,
   working-tree identity, scope, statuses, evidence, complete matrix and log paths.
2. Apply `reviewing-pr` once with that evidence, exploration and discussion results.
   It delegates Architecture, Type Safety, Async, ADK, Security, Performance,
   Code Quality and Testing to eight specialist skills. Require all eight verdicts,
   reviewed/unchecked scope, provenance and evidence. Every area reviews relevant
   unchanged components and returns existing debt as well as change-induced defects.
   Architecture consumes the ADR audit rather than executing or owning it.
3. If specialists expand scope, pass their scope delta to quality-gate for missing
   ADR coverage and return the merged evidence to reviewing-pr. Do not rerun
   unaffected commands or audit rows. Unresolved coverage means verification
   incomplete; do not falsely imply all eight reviews or all ADRs completed.
4. reviewing-pr merges root causes into stable R-NNN IDs with one primary area and
   related-area references. Preserve Introduced/Worsened/Pre-existing/Improvement
   classification for every observation. Include Missing/unjustified Partial test
   gaps, linked to provenance. Retain all completed results for Phase 5.

## Phase 5: Individual finding publication

1. Post each confirmed Introduced/Worsened Critical/Important finding with path,
   provenance, pinned commit ID, valid diff
   side/line or range, impact, evidence, fix, and confidence. Use inline suggestions
   for concrete consecutive-line fixes. Suggestions are proposals, not applied fixes.
2. For findings without a valid diff anchor, post a regular PR comment with a pinned
   source link. Never invent lines or repost issues already in existing threads.
3. Use body files/structured API input files with actual newlines, not shell
   interpolation of Markdown. Record returned IDs/URLs directly. In `onlocal`,
   retain proposed comments without posting.
4. After publication, fill findings and verification sections together, including
   the architectural assessment, complete ADR matrix, and behavior coverage counts.
   Include all eight area verdicts and retain existing debt/improvements from every
   area in the aggregate report. Count/post a root cause once; A-NNN architecture
   references map to canonical R-NNN IDs. Pre-existing debt and optional alternatives
   do not alone block this PR or trigger repairs; keep their actual severity visible
   and preserve independently failed quality checks.
   Do not post an aggregate comment yet.

## Phase 6: Repair PRs

Apply `addressing-review-findings` to structural Introduced/Worsened defects from
Phase 5 and confirmed change-induced unresolved candidates from Phase 3. Existing
debt/optional improvements require separate repair authorization. Deduplicate
overlapping candidates. The skill owns
sequential per-category repair branches from the original PR head and delegates
checks to `quality-gate`, PR text to `draft-pr`, and necessary ADR work to
`record-architectural-decision`. In `onlocal`, return proposals only.

Fill the repair table once at phase end, including failures/skips, or `None`.

## Phase 7: Finalize and publish

1. Re-read PR head. If changed, identify the reviewed SHA and explicitly state that
   the current head remains unreviewed.
2. Finalize all eight per-area verdicts, provenance counts and outstanding work
   using the template. Distinguish
   PASS/FAIL/BLOCKED/NOT RUN. Repair PRs do not resolve the original PR automatically.
3. Remove pending placeholders, raw logs, secrets, and local-only paths from the
   public body. Keep evidence links. Add `<!-- rec-navi-review:<run-id> -->`.
4. Unless `onlocal`, post exactly one aggregate comment for this run:

   ```bash
   gh pr comment <NUMBER> --repo <OWNER/REPO> --body-file <RESULT_PATH>
   ```

   Save the actual returned URL in the execution record, not the published body.
   Never infer it from the latest comment, which may belong to another author.
5. Before retrying an ambiguous write, paginate comments and reconcile this run's
   marker. Reuse a posted comment instead of duplicating it. Reconcile recorded
   replies, findings, and repair PRs similarly before retrying.
6. If too large, compact repetition without removing findings/blockers. Do not
   silently truncate or split the aggregate report. If still too large, preserve
   the full file and report publication BLOCKED.
7. Display a brief outcome, final comment URL if available, and local result path.

## Failures and resumption

Keep artifacts on failure. If preparation fails, create a minimal report with
available metadata and the blocker, not fabricated results. When the PR is known,
attempt a final blocked report if publication remains available. Continue independent
checks/categories. Rate limits, authentication errors, and missing services are
blockers, never passes. Resume from the execution record, reconciling uncertain
writes. Never automatically delete artifacts or disturb the original worktree.
