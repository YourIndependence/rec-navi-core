---
id: ARCH-013
title: Project Authorization Pattern
domain: backend
status: active
date: 2026-10-20
rules: true
files:
  - 'src/recnavi/core/**/*.py'
  - 'src/recnavi/application/**/*.py'
  - 'src/recnavi/apis/**/*.py'
---

## Context

Inline role, ownership, or group comparisons drift from Project's permission
policy. Download previously rejected ADMIN owners and added a group condition
absent from other project operations. Identical guards also used different
denial messages.

## Decision

Project.validate_permission is the single authority for project access.
Callers use this standalone, top-level guard with explicit keyword arguments:

```python
if not project.validate_permission(user=user, as_role=UserRole.OWNER):
    raise ClientAuthorizationError(
        "User does not have access permission to this project",
    )
```

The denial branch contains only this raise and has no else branch. Authorize
before effects or early returns. Loading a project and checking its existence
may precede authorization. Do not add group checks or reproduce role, owner,
or project assignment decisions at call sites. For project authorization,
User.can_act_as is used only inside Project.validate_permission.

| Entry point | Required as_role |
| --- | --- |
| core/project/project.py:get_project | user.role |
| core/project/update_project.py:update_project | UserRole.OWNER |
| core/project/delete_project.py:delete_project | UserRole.OWNER |
| core/project/download_project.py:create_project_archive | UserRole.OWNER |
| core/scene/review_scene.py:review_scene | UserRole.OWNER |
| core/scene/update_scene.py:update_scene | UserRole.STAFF |
| core/project/submit_project.py:submit_project | UserRole.STAFF |

Preserve the shared role hierarchy: OWNER operations require ownership even
when ADMIN acts as OWNER. No additional group validation is required. Scene
assignment checks enforce a separate rule after the project guard. List
filtering and project creation do not authorize an existing single project and
are outside this guard contract. Non-project role authorization is unchanged.

## Rationale

**Alternative: Inline comparisons.** They duplicate policy and narrow or widen
access independently as roles evolve.

**Alternative: Router dependency.** This ties resource authorization to HTTP
and does not protect other callers of the operation.

**Alternative: Text matching.** Comments, strings, nested functions, combined
conditions, and reordered effects can look authorized without enforcing it.
Python AST inspection checks executable structure instead.

## Consequences

- Positive: Project operations share permission semantics and denial format.
- Positive: Four error-severity Archgate rules enforce presence/role, inline
  policy prohibition, denial format, and effect ordering.
- Negative: Moving or adding entry points requires updating the explicit
  operation-to-role map. Additional functions calling
  project.validate_permission are checked structurally; an entirely new
  operation lacking a guard must be added to the map during review.
- Limitation: This is a syntactic contract, not interprocedural verification.
  Aliases and arbitrary helper side effects need manual review. Known effects
  are storage calls, non-read projects_db calls, project method calls, project
  attribute mutations, and early returns. Nested definitions cannot authorize
  their enclosing operation.

## Compliance

**Do:**

- Use the exact standalone guard and denial message shown above.
- Keep the operation-to-role map in the companion rule file current.
- Authorize before mutation, storage access, return, or URL generation.
- Keep project access policy in Project.validate_permission.
- Implement enforcement only in this ADR's companion `.rules.ts` file and run
  it through `archgate check`; do not add a separate authorization test runner.
- Verify violations of every enforced property through Archgate against
  temporary source mutations, restoring the source after each check.

**Don't:**

- Compare role, owner, project assignments, or groups at project authorization
  call sites, or call user.can_act_as there.
- Add OR/AND conditions, positional arguments, or a conditional wrapper around
  the project permission guard.
- Treat comments, strings, or nested helpers as authorization of their caller.
- Remove independent scene assignment checks or list filtering for this ADR.

## References

- [ARCH-001](ARCH-001-clean-architecture.md)
- [ARCH-011](ARCH-011-test-implementation.md)
- [PR #61](https://github.com/YourIndependence/rec-navi-core/pull/61)
