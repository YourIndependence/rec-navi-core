# Review ownership and integration rules

Specialist rules live in the eight skills listed by [SKILL.md](SKILL.md).
[REVIEW-CONTRACT.md](REVIEW-CONTRACT.md) is the shared scope, output, provenance,
confidence, severity and verdict contract. Do not maintain a second checklist here.

| Boundary | Primary owner | Related evidence |
|---|---|---|
| Layer direction, model ownership, DI/registry registration, package initialization | Architecture | Supplied all-ADR matrix; Type Safety/ADK where relevant |
| Concrete types, Pydantic contracts, justified Any/type suppression | Type Safety | Architecture for model ownership; Security for unsafe trust boundaries |
| Synchronous HTTP in an async ADK tool | Async | ADK runtime consequences |
| Callback ordering, instruction injection, session/Runner behavior | ADK | Async cancellation; Testing assertions |
| Missing permission checks, tenant isolation or unsafe input use | Security | Type Safety/Architecture contracts |
| N+1, duplicate requests, memory pressure or inefficient concurrency | Performance | Async execution correctness |
| Readability, local complexity, silent error handling or dead code | Code Quality | Owner of the underlying correctness issue |
| Missing behavior assertions or improperly external-service-dependent unit tests | Testing | Relevant specialist's runtime contract |

Do not report duplicate issues per category. Pick the primary cause and preserve
related-area references. An ADR violation is interpreted by quality-gate's delegated
`review-with-adrs` audit and consumed by specialists, not independently re-audited.
Security or correctness effects of the same cause remain visible in impact/severity.
Legacy static/dynamic ADK patterns are assessed against current ADRs and explicit
exceptions, not obsolete blanket rules about directories or registries.
