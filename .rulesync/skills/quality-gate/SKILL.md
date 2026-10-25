---
name: quality-gate
description: Own validation completeness and gate decisions for Ruff, tests, Archgate and delegated all-ADR compliance, with revision- and scope-bound evidence.
---
# Quality gate

Inputs: revision/checkout, affected scope, mode (`review` or `implementation`),
required unit scope, full diff/base, related-component scope, artifact destination,
and existing evidence. Default mode is
`implementation`. The caller's/project's stricter check requirements take precedence.

- `review`: check only; never autoformat, fix lint, edit sources, install tools,
  create symlinks, or start services. Use the exact pinned checkout. With `onlocal`,
  do not change git state; unavailable matching checkouts mean BLOCKED.
- `implementation`: fixes are allowed in task-owned work only; rerun affected
  checks after changes. Preserve original user changes.
- Reuse results only for the same revision, working-tree content and checked scope,
  with command, status, and output evidence. Changes invalidate affected results.
  A scope-only expansion needs the missing ADR coverage, not repeated unchanged
  automated commands. Return a clear scope boundary if context cannot be obtained.

## Required checks

Run sequentially, capturing logs. Continue independent checks after a failure.

```bash
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
uv run pytest tests/unittests/ -v
```

Targeted tests may run first, but do not replace the full suite required by project
instructions. Unit tests must not require LocalStack, real cloud/provider services,
or secrets; report such dependencies as testing-boundary violations.

Run applicable integration tests only when required services/explicit guards are
available. Consult `docs/ENVIRONMENTS.md` when present, otherwise the repository README,
test configuration and integration runner; do not
infer all providers are available from MySQL alone. Preserve `real_aws`/`ecs` guards.
Use a repository integration runner only if present and applicable; never assume
TRUST's LocalStack runner exists. This checkout's tests/integration/conftest.py
provides in-memory infrastructure when ENV=CI. Use that documented profile for
HTTP integration checks without real AWS. No unrequested service startup during
review. Unavailable optional
integration tests are NOT RUN with a reason, never PASS; they do not block delivery
unless required for this change or by the caller. Real-provider tests require an
explicitly authorized environment/profile.

Run `archgate check`; if unavailable, use an installed executable or the repository's
supported runner (`npx.cmd --yes archgate check` on Windows, `npx --yes archgate check`
elsewhere). If dependencies/network/configuration are unavailable, report BLOCKED.
Do not globally install tools or rewrite configuration as a fallback. Distinguish
actual rule violations (FAIL) from execution/configuration errors (BLOCKED).
In CI, verified dedicated-job results for the exact revision may be reused; merely
being in CI is not a passing result.

## Required ADR compliance

Invoke `review-with-adrs` once with automated Archgate evidence, base/head and
working-tree identity, complete related-component scope, and prior audit if any.
It owns interpretation and every ADR's applicability/manual assessment. This skill
owns ensuring that audit completed and incorporates its outcome into the gate.
Archgate success alone does not satisfy this requirement. Do not report a passing
gate with missing ADR rows, applicable manual failures, or blocked required evidence.
An ADR-specific NOT APPLICABLE verdict needs a reason and is not a passing check.

When a reviewer returns an expanded component scope, supplement only the uncovered
ADR evidence and return the merged complete matrix, noting scope/revision. Reuse
unaffected rows only when the decision and component evidence still match. Required
evidence that remains unavailable means BLOCKED. Changes to code or ADRs invalidate
affected checks/audit; optional ADR creation remains a separate authorized action.
Do not call reviewing-pr or its specialists from the gate: the dependency is one-way.

## Result contract

Return each command/check and ADR-audit outcome with revision, scope, PASS/FAIL/BLOCKED/NOT RUN, counts,
concise evidence/reason, and private log path. Return a Japanese result table when
requested; otherwise retain the caller's language/format. Never edit the aggregate
review file or print detailed logs in artifact-only mode. Include the complete
all-ADR matrix, violations with provenance, gaps, exceptions and scope boundaries.
Preserve actual failures, including baseline failures; never relabel an automated
failure as PASS because its cause predates this PR. Distinguish provenance from
the gate's execution/compliance outcome and disclose both.

Required checks must all PASS before repair PR commit/push/creation. In review mode,
failures block approval, not publication of an honest review report. Optional skipped
integration tests must be disclosed. Do not claim CI passed from local results.
