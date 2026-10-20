---
id: ARCH-001
title: 4-Layer Clean Architecture (apis / application / core / infrastructure)
domain: architecture
status: active
date: 2026-10-19
rules: true
files:
  - 'src/**/*.py'
  - 'tests/**/*.py'
---

## Context

The TRUST backend is an AI-agent platform built on FastAPI + Google ADK. It integrates with diverse external systems — LLM backends, vector stores, document pipelines, and external SaaS APIs. Without explicit separation of concerns, the codebase becomes difficult to test and change over time.

## Decision

The `src/trust/` directory is organized into **4 layers**:

| Layer             | Path                        | Responsibility                                                                           |
| ----------------- | --------------------------- | ---------------------------------------------------------------------------------------- |
| `apis/`           | `src/trust/apis/`           | HTTP boundary: FastAPI routers, Pydantic request/response schemas                        |
| `application/`    | `src/trust/application/`    | Use-case orchestration: coordinates core + infrastructure, no framework dependencies     |
| `core/`           | `src/trust/core/`           | Domain logic: abstract base classes, registries, agents, preprocessors, type definitions |
| `infrastructure/` | `src/trust/infrastructure/` | External I/O: DB adapters, external API clients, session services                        |

Dependency direction: `apis/ → application/ → core/ ← infrastructure/`

`infrastructure/` registers concrete implementations into `core/` registries at startup time. `application/` and `core/` depend only on abstract interfaces resolved through the registry.

### Auxiliary Modules

| Module         | Responsibility                                                  |
| -------------- | --------------------------------------------------------------- |
| `config/`      | Environment variables and settings (accessible from all layers) |
| `exceptions/`  | Custom exceptions (accessible from all layers)                  |
| `task_runner/` | Background task management                                      |

### File Naming

Application module filenames use `<verb>_<noun>.py` without the `_usecase`
suffix. The `application/` directory already identifies the layer. Use-case
function names retain `_usecase` to distinguish them from core operations.

```python
from recnavi.application.user.get_group_users import get_group_users_usecase
```

The implementation module `application/user/get_group_users.py` is tested by
`tests/unittests/application/user/test_get_group_users.py` under ARCH-011.
Rename imports, mock patch targets, and mirrored tests together. Do not retain
compatibility modules ending in `_usecase.py`.

## Rationale

**Alternative: `_usecase` on both modules and functions.** The module suffix
repeats the layer and conflicts with the existing project application modules.
Removing the function suffix as well would obscure application entry points at
call sites, so this decision changes only module names and import paths.


**Alternative: Feature-Sliced Design**
Organizes directories by feature domain. As feature count grows, cross-cutting concerns like LLM clients and DB connections scatter across multiple features, making dependency graphs complex and hard to reason about.

**Alternative: Flat structure**
Works at small scale but loses control of inter-component dependencies quickly. Test isolation also becomes difficult.

**Adopted because:**
- Port (core/ ABC) + Adapter (infrastructure/ concrete class) pattern makes external system replacement straightforward
- Registry-based DI is a lightweight DI mechanism for Python — no heavy DI framework required
- Centralizing use cases in `application/` allows unit testing completely decoupled from FastAPI

## Known Deviations

See [known-deviations.md](./known-deviations.md) for the full list of accepted compromises. Key items:

## Consequences

- **Positive**: Each layer can be tested independently (`infrastructure/` can be replaced with `core/` ABC stubs)
- **Positive**: Adding new DB, store, or agent, or tool requires only a registry registration
- **Negative**: New features require creating files across multiple layers (responsibility is unambiguous, but there is more boilerplate)
- **Negative**: Registry singletons are global state; parallel tests require explicit cleanup (`registry.clear()` in teardown)

## Compliance

**Do:**

- Name application modules `<verb>_<noun>.py`, retaining `_usecase` on use-case functions
- Update imports, mock patch targets, and mirrored unit tests when modules move

**Don't:**

- Add or retain application Python modules ending in `_usecase.py`

- Import from `application/` or `apis/` inside `infrastructure/`
- Import `apis/` Pydantic schemas inside `application/` (use `core/types/` instead)
- Import concrete `infrastructure/` implementations directly inside `core/` (inject via Registry)

## References

- [ARCH-010: Google ADK Patterns and Best Practices](./ARCH-010-google-adk-patterns.md)
- [ARCH-013: Tool Registry and Initialization Pattern](./ARCH-013-tool-registry-pattern.md)
- [Archgate ADR guide](https://cli.archgate.dev/)
- [.rulesync/rules/architecture.md](../../.rulesync/rules/architecture.md)
