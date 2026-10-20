# ARCHITECTURE
This document explains about whole architecture of TRUST.


## System Architecture
See here[architecture.drawio](https://github.com/tmc-ccoe/trust-core/blob/dev/docs/architecture.drawio)


## Software Architecture

`trust-core` consists of four layers. Dependencies always point inward (toward the Core Layer).
Based on the Clean Architecture.

```mermaid
graph LR
    P[Presentation Layer]
    A[Application Layer]
    C[Core Layer]
    I[Infrastructure Layer]

    P -->|depends on| A
    A -->|depends on| C
    I -.->|implements<br/>interfaces| C
```

- **Presentation Layer**
  - Presentation I/F for other systems. like API or CLI.
- **Application Layer**
  - Depends on the Core Layer. Do not depend on Infrastructure Layer.
  - The Application Layer is responsible for implementing use cases. It defines specific application behaviors using the business rules from the Core Layer.
- **Core Layer**
  - Do NOT depend on any other layer.
  - The Core Layer is responsible for the heart of the business logic and defines the essential rules and behaviors of `TRUST`.
    This layer is completely independent of technical implementation details.
- **Infrastructure Layer**
  - Depends on the Core Layer (Implements interfaces defined in the Core Layer)
  - The Infrastructure Layer handles interactions with external libraries and external APIs. This layer implements concrete classes that fulfill the interfaces defined in the Core Layer.
  - Note: The Infrastructure Layer does not depend on the Application Layer.


## directory architecture
```
+-- rec-navi-core/  # repo root
+-- .github/
+-- docs/
+-- cli/  # CLI presentation
|
+-- src/  # source root
|   +-- recnavi/
|       +-- core/  # core layer
|       |   +-- agent_runner/
|       |   +-- agents/
|       |   +-- ...
|       |
|       +-- apis/  # API presentation layer
|       |   +-- auth/
|       |   +-- root/
|       |   +-- cms/
|       |   +-- staff/
|       |
|       +-- application/  # application layer
|       |   +-- analysis/
|       |   +-- chat/
|       |   +-- cms/
|       |   +-- dashboard/
|       |   +-- features/
|       |   +-- user/
|       |   +-- validation/
|       |
|       +-- infrastructure/  # infrastructure layer
|       |   +-- database/
|       |   +-- dataloader/
|       |   +-- external_clients/
|       |   +-- session_service/
|       |
|       +-- config/  # application config
|       +-- exceptions/
|       +-- task_runner/  # ECS Task runner
|       +-- main.py  # API server entry point
|
+-- tests
|   +-- data/  # for mock data
|   +-- mockups/
|   +-- unittests/  # Same directory architecture as `src`.
|   +-- integration/
|   +-- testing_util.py
|   +-- conftest.py
|
+-- .gitignore
+-- buildspec.yml
+-- Dockerfile
+-- pyproject.toml
+-- README.md
+-- uv.lock

```

## Test Architecture

Tests follow the same boundary rule as production code: each layer should be verified at the cheapest layer that still proves the behavior.

Unit test files mirror the implementation module tree. For example,
`src/recnavi/apis/staff/staff_router.py` is tested in
`tests/unittests/apis/staff/test_staff_router.py`. Keep additional tests for a
module in that same mirrored directory. `__init__.py` files, tests of shared
mockups, modules that only declare Pydantic schemas or core types, the modules
`config/variables.py` and `exceptions/exceptions.py`, and modules named
`base_*.py` are exempt. See
[ARCH-011](adrs/ARCH-011-test-implementation.md) for the full rule and checks.

| Test layer | Directory | External dependency policy |
| ---------- | --------- | -------------------------- |
| Unit tests | `tests/unittests/` | No LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or repository secrets. Use `tests/mockups/`, lightweight fakes, `botocore.stub.Stubber`, or `moto`. |
| Integration tests | `tests/integration/` | Default command includes all integration tests. LocalStack-backed profiles use LocalStack, MySQL, OpenSearch, and local Cognito. |
| Real AWS tests | `tests/integration/` with markers | Use `pytest.mark.real_aws`; ECS dispatch tests also use `pytest.mark.ecs`. These tests are skipped automatically only when `AWS_ENDPOINT_URL` points to LocalStack. |

This keeps the everyday development workflow fast and deterministic while preserving a place for real-cloud validation when it is intentionally requested.


## Media URLs and persistence

Follow [ARCH-002](adrs/ARCH-002-pydantic-first-type-system.md#media-models-and-temporary-urls).
Use one domain type when the response differs only by temporary media URLs.
Core models own async `attach_presigned_url()` methods updating themselves and returning `self`;
application use cases call them after authorization and filtering.
Normal serialization excludes durable URI/key fields. Database writes use
`to_storage_item()`, including nested media in `Project`, and exclude URLs.
Distinct contracts such as privacy-limited `UserSummary` remain separate.

## Application module naming

Application module filenames use `<verb>_<noun>.py` without `_usecase`.
Use-case function names retain `_usecase`, for example
`application/scene/review_scene.py` exports `review_scene_usecase`.
Unit test filenames mirror the module: `test_review_scene.py`.
See [ARCH-001](adrs/ARCH-001-clean-architecture.md#file-naming) for the decision
and its automated enforcement.


## Project authorization

Follow [ARCH-013](adrs/ARCH-013-project-authorization.md). Existing-project
operations use Project.validate_permission with the declared role and the
canonical ClientAuthorizationError message. Do not add inline role, owner, or
group policy. Authorize before mutation, storage access, or return. Keep the
operation-role map current when adding or moving operations. Enforcement lives
in the ADR's companion `.rules.ts` and runs through `archgate check`.
