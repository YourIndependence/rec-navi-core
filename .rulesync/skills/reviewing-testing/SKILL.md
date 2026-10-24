---
name: reviewing-testing
description: Review behavior-to-test coverage, required scenarios, assertion quality, test boundaries and regression prevention across changed and related behavior.
---
# Review test coverage and validity

Apply [the shared review contract](../reviewing-pr/REVIEW-CONTRACT.md), including
related unchanged components, all four provenance classes, per-area verdict and
artifact-only output. Return analysis only; consume quality-gate/ADR evidence.

## Behavior-to-test analysis

1. Inventory changed or affected behaviors by API/domain behavior, not by file.
   Group related hunks; exclude formatting/docs-only changes and test-only refactors
   without runtime impact. Include affected existing contracts, clearly classified.
2. Before inspecting existing tests, specify required success, failure, boundary,
   authorization, retry/timeout/fallback, cancellation and regression scenarios.
3. Inspect existing and changed tests. Require assertions of the relevant branch
   or contract; imports, smoke paths and mocks bypassing the contract are insufficient.
   Use real HTTP/Runner/cross-layer execution with mocked external boundaries where
   that boundary is essential to the behavior; isolated pure logic needs unit tests.
4. Return matrix rows: behavior ID, source/symbol, required scenarios, matching
   tests, Covered/Partial/Missing, justification and related finding/provenance.
   Covered means targeted assertions exist, not that execution passed. Summarize
   counts separately from quality-gate execution evidence.
5. Missing and unjustified Partial coverage are normally Important; use Critical
   for concrete high-risk regression paths. Justify exceptions such as dead-code
   removal/generated code rather than treating every changed line as testable logic.

## Test boundaries and design

Unit tests must not need LocalStack, real AWS/provider APIs or repository secrets.
Use repository mockups, fakes, Stubber or moto appropriately. Real-provider tests
belong in guarded integration profiles; real AWS tests require real_aws and ECS also
ecs when those profiles exist. Check service-reaching unit tests, dynamic skips
and fixture costs against current ADRs and accepted deviations; a marker alone
does not make remote I/O a unit test. Follow ARCH-003 and ARCH-011: reusable Base*
test doubles belong in tests/mockups/. Integration tests retain real component
wiring, use the shared CI infrastructure fixture, and override only verify_user.
Do not replace app.state database/storage per test or patch integration collaborators.
Every integration test makes its own HTTP client request assigned to response.
Do not add test-only production hooks.

Inspect assertion specificity, false positives, mock fidelity, deterministic setup,
cleanup/isolation, and regression sensitivity. Reuse the supplied suite results;
do not run tests yourself or infer coverage from a green job/line percentage alone.
