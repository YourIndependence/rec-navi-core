---
name: verifying-pr-discussions
description: Verify every unresolved GitHub PR review thread against a pinned revision and optionally reply with fresh evidence. Returns a thread table and repair candidates.
---
# Verify PR discussions

Inputs: repository, PR number, pinned head SHA, artifact directory, posting policy
(`post` or `local-only`), and prior execution record. Posting requires authorization
from the caller; `/review` authorizes it except in `onlocal`.

1. Fetch all review threads using paginated GraphQL `reviewThreads`, including
   `isResolved`, `isOutdated`, path/line, original commit, and comments. Paginate
   comments within each thread too. REST review comments do not expose reliable
   thread resolution state; do not infer it from a missing `resolved` property.
2. Exclude resolved threads only. Include unresolved outdated threads and those
   with author replies. Classify by meaning as repair request or design discussion,
   not by keyword alone. Capture stable thread/root-comment IDs and URLs.
3. For each repair request, inspect current code, relevant callers, and tests at
   the pinned SHA. Compare with original code when helpful. An unchanged file does
   not prove the issue persists: a caller, dependency, or contract may have changed.
   Assign VERIFIED, NEEDS FIX, PARTIAL, or BLOCKED with concrete evidence. Distinguish
   reading a test from actually executing it. Design discussions remain OPEN.
4. With `post`, reply to every repair-request thread on every new review run,
   including previously verified threads that remain unresolved. Include the
   pinned SHA, status, issue summary, evidence, remaining fix, and run marker.
   Use the root review-comment reply API and structured input/body files. Save
   returned IDs/URLs. Reconcile uncertain writes before retries within the same run.
   Do not automatically resolve threads or answer design decisions speculatively.
5. With `local-only`, do not post, fetch git objects, or modify git/source state;
   return proposed replies. Missing historical objects may be read remotely.

Return one completed table in Japanese:

| Thread | Issue | Status | Evidence / action |
|---|---|---|---|
| [#ID](URL) | Summary | VERIFIED / NEEDS FIX / PARTIAL / BLOCKED / OPEN | Pinned evidence; reply URL or proposed reply |

Also return deduplicated repair candidates (thread ID, category, evidence, concrete
fix, original/pinned SHA) and any retrieval/posting failures. Unknown status must
remain unknown. Return artifacts to the caller; do not edit `review_result.md`,
post an aggregate summary, or print detailed reports in quiet mode.
