---
id: ARCH-013
title: Application Modules Omit the Usecase Suffix
domain: architecture
status: active
date: 2026-10-19
rules: true
files:
  - 'src/recnavi/application/**/*.py'
---

## Context

Application modules currently mix names such as `get_project.py` and
`get_group_users_usecase.py`. The application directory already identifies the
layer, so repeating `_usecase` in module names adds inconsistent redundancy.
Function names still need to distinguish application entry points from core
operations when both appear in imports or tests.

## Decision

Python module filenames anywhere under `src/recnavi/application/` must not end
with `_usecase.py`. Name operation modules `<verb>_<noun>.py`. Keep the
`_usecase` suffix on use-case function names. Rename mirrored unit test modules
according to ARCH-011 and update imports and patch targets together.

Before:

```python
from recnavi.application.user.get_group_users_usecase import get_group_users_usecase
```

After:

```python
from recnavi.application.user.get_group_users import get_group_users_usecase
```

The implementation module `application/user/get_group_users.py` is tested by
`tests/unittests/application/user/test_get_group_users.py`.

## Rationale

The directory identifies the layer; the function suffix identifies an entry
point at call sites. This matches the existing project application modules.

**Alternative: retain `_usecase` on both modules and functions.** This repeats
the layer in module paths and would require renaming already consistent modules.

**Alternative: remove `_usecase` from functions as well.** This obscures the
distinction between application orchestration and core operations. This decision
changes filenames and import paths only, not function names or behavior.

## Consequences

- Application module paths follow one convention.
- Imports, patch targets, and mirrored test paths must change with module moves.
- Downstream branches introducing `_usecase.py` modules must rename them before
  merging. Compatibility modules with the old suffix are not retained.

## Compliance

**Do:**

- Use names such as `application/scene/review_scene.py`.
- Keep use-case function names such as `review_scene_usecase`.
- Mirror the implementation filename in unit test filenames under ARCH-011.
- Run the naming rule tests and `archgate check` after module renames.

**Don't:**

- Add or keep an application Python module ending in `_usecase.py`.
- Rename use-case functions merely because their module moves.
- Leave imports or mock patch targets pointing at the old module path.

## References

- [Architecture overview](../ARCHITECTURE.md)
- [ARCH-001: Clean Architecture](ARCH-001-clean-architecture.md)
- [ARCH-011: Test Implementation](ARCH-011-test-implementation.md)
