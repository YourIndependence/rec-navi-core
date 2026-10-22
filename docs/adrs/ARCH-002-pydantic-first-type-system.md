---
id: ARCH-002
title: Pydantic-First Type System (core/types/ as SSOT)
domain: architecture
status: active
date: 2026-10-20
rules: true
files:
  - 'src/**/*.py'
---

## Context

`core/types/` is the designated location for domain type definitions shared across all layers. When independent Pydantic `BaseModel` classes are defined inside `application/` or `infrastructure/`, the same structure ends up in multiple places. Changes to one copy are not propagated to the other, creating type drift that becomes a source of runtime errors.

A concrete example: a `ResponseSchema(BaseModel)` was defined inside `application/validation/` for HTTP responses, making the boundary between it and `core/types/` ambiguous.

## Decision

**Domain types shared across multiple layers must use `core/types/` as the Single Source of Truth.**

| Case                                       | Where to define the type                                                      |
| ------------------------------------------ | ----------------------------------------------------------------------------- |
| Domain types shared across multiple layers | `src/trust/core/types/` (Pydantic model)                                      |
| Fields specific to HTTP input validation   | `apis/schemas/request_schemas.py` (composes `core/types/`)                    |
| Fields specific to HTTP response shaping   | `apis/schemas/response_schemas.py` (composes `core/types/`)                   |
| Structures used only inside `application/` | Python `dataclass` or `TypedDict` (when no external I/O validation is needed) |

**No new Pydantic `BaseModel` subclasses should be defined in `application/` or `infrastructure/`.**

### Media models and temporary URLs

Use one canonical domain model when a response differs only by presigned URLs.
`SceneMaster`, `Scene`, and `Project` own an async
`attach_presigned_url(*, storage: BaseObjectStorage) -> Self` method. It updates
its own URL fields, returns `self`, retains durable references, and regenerates
URLs on every call. It does not check object existence. Concrete storage
clients remain in infrastructure. Application use cases orchestrate reads and
URL attachment after authorization and filtering. `Project.attach_presigned_url()`
recursively delegates to every child scene and preserves scene order. Callers
use this aggregate method rather than iterating over its scenes themselves.

```python
master = SceneMaster.model_validate(item)
public_master = await master.attach_presigned_url(storage=storage)
response = public_master.model_dump(by_alias=True)
item = public_master.to_storage_item()
public_project = await project.attach_presigned_url(storage=storage)
```

Storage-only URI/key fields use `Field(exclude=True)`. Normal serialization and
serialization schemas expose URLs and omit durable references.
`to_storage_item() -> dict[str, object]` explicitly includes durable references
and excludes temporary URLs. Aggregates such as `Project` call each child's
storage method. All database writers use this explicit persistence boundary.
Preserve existing aliases, metadata, URI validation, missing-media behavior,
authorization, and the 3600-second signing lifetime.

Project archive downloads follow the same model ownership and persistence
boundary: `Project.create_download_url(*, storage: BaseObjectStorage) -> Self`
creates a fresh archive through its private `_create_download_object()` method,
updates `download_url`, and returns `self`. Authorization precedes this call;
recording eligibility and source-key validation precede any storage access.
Unlike playback URL attachment, archive creation is explicit and must not run
as a side effect of project listing or scene URL attachment. Download URLs are
excluded from `to_storage_item()`. Archive entries shared with storage adapters
use a frozen Pydantic model in `core/types/`.

Do not introduce a second `HogeView` solely to add temporary media URLs.
Distinct contracts still warrant separate types: `UserSummary` deliberately
omits personal information and remains separate. Template images follow this contract. See ARCH-014 for the overall media delivery design.

## Rationale

**Alternative: Independent persistence and media View types**
Duplicates domain fields or requires unions for nested aggregates. A difference
limited to temporary URLs does not justify a second domain type.

**Alternative: Return deep copies or select persistence by JSON mode**
Copying every aggregate and child adds allocation and changes object identity.
URL attachment consistently updates the current model and returns `self`, so
callers retaining the same instance also observe refreshed URLs. Callers needing
independent state must copy explicitly before attachment. Mode-dependent
persistence relies on an implicit caller option; an explicit storage method
keeps the persistence boundary visible. Every writer, including aggregate
writers, must use it. Round-trip tests enforce that contract.

**Alternative: Each layer defines its own Pydantic models**
Allows slim, layer-specific models but introduces DRY violations. The same fields appear in multiple places and changes in one location are not reflected in another, creating a breeding ground for runtime errors.

**Alternative: Pass data as `Any` / `dict`**
Abandons type strictness. Loses the benefits of Pydantic validation and IDE auto-completion.

## Consequences

- **Positive**: Field changes are centralized in `core/types/`, eliminating the risk of missed updates
- **Positive**: Reading `core/types/` alone gives a complete picture of the domain data structures
- **Positive**: Type errors are caught at analysis time (mypy / Pyright)
- **Negative**: HTTP-specific validation (alias config, pagination-only fields, etc.) must remain in `apis/schemas/`

## Compliance

**Do:**

- Add new domain types to `src/trust/core/types/` as Pydantic models
- In `apis/schemas/`, wrap or compose types imported from `core/types/`
- When a data structure is needed inside `application/` with no external I/O validation, use Python `dataclass` or `TypedDict`

**Don't:**

- Define `class Xxx(BaseModel):` in `application/` (put it in `core/types/`)
- Define `class Xxx(BaseModel):` in `infrastructure/` (same rule)
- Re-define a model that already exists in `core/types/` in another layer

### Media model compliance

**Do:**

- Inject `BaseObjectStorage` into the async model method and return `self` after updating its URL fields.
- Use `to_storage_item()` for media and aggregate database writes.
- Test that storage round trips retain references and omit URLs after signing.
- Verify responses and serialization schemas omit storage-only fields.

**Don't:**

- Persist temporary URLs or use ordinary `model_dump()` for media DB writes.
- Define a separate View solely to attach URLs.
- Remove durable references from the in-memory model during attachment.

## References

- [PR #59 review](https://github.com/YourIndependence/rec-navi-core/pull/59#discussion_r4318691073)

- [ARCH-001](./ARCH-001-clean-architecture.md) — 4-layer Clean Architecture
- `src/trust/core/types/` — canonical list of domain types
