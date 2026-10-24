---
name: exploring-codebase
description: Scans the rec-navi-core project to understand the architecture, conventions, and existing patterns relevant to a planned change. Use before designing or implementing any feature or bug fix.
---

# Exploring Codebase

Builds a focused picture of the existing code relevant to a task.

**Input**: A topic, module path, or feature area (e.g., `"document loader"`, `"chat endpoint"`, `"agent tool"`).

## Instructions

### Step 1: Locate Relevant Files

```bash
rg -l "<topic>" src/recnavi -g "*.py"
rg --files src/recnavi -g "*<topic>*.py"
```

Target the most affected layer:

| Change type | Start here |
|---|---|
| New endpoint | `src/recnavi/apis/` |
| Business logic | `src/recnavi/application/` or `src/recnavi/core/` |
| Domain models / project or scene behavior | `src/recnavi/core/` |
| Database / object-storage interfaces | `src/recnavi/core/database/`, `src/recnavi/core/storage/` |
| External client | `src/recnavi/infrastructure/` |

Resolve actual modules and injected interfaces from the current checkout. Do not
assume TRUST agent/tool registries exist in this repository. Trace database and
object-storage abstractions, media serialization and project authorization when relevant.

### Step 2: Read Key Files

For each found file, extract:

- **Public interface**: function signatures, class `__init__`, names exported in `__init__.py`
- **Layer dependencies**: what it imports from other layers
- **Dependency injection**: which core abstraction and startup/request dependency supplies it?

### Step 3: Identify Conventions

From the files above, derive:

- **Naming**: `snake_case` modules, `PascalCase` models, `<verb>_<noun>` domain functions
- **Async**: is the affected layer async?
- **Registry key**: what string is used for this component type?
- **Test location**: `tests/unittests/<same-path-as-src>/`

### Step 4: Output Context Report

```
## Codebase Context Report

### Relevant Files
| File | Purpose | Key Exports |
|---|---|---|
| <path> | <what it does> | <functions/classes> |

### Conventions to Follow
- Naming: <example>
- Async: <yes/no>
- Registry key: <if applicable>

### Constraints
- <anything that would break if changed naively>

### Test Coverage
- Existing test file: <path or "none found">
- Coverage of affected code: <present / absent / partial>
```
