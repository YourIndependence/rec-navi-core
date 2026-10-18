---
id: ARCH-011
title: Test Implementation Rules
domain: testing
status: active
date: 2026-10-16
rules: true
files:
  - 'src/recnavi/**/*.py'
  - 'tests/**/*.py'
---

## Context

Test implementation details can undermine the layer boundaries defined by
ARCH-004. In particular, replacing integration collaborators, creating
expensive fixtures repeatedly, or allowing real outbound HTTP calls makes the
test suite misleading or nondeterministic.

## Decision

Tests must preserve the distinction between integration and unit behavior.
Reusable abstract-class mocks belong in `tests/mockups/`; integration tests
must keep real component wiring; and unit tests must use in-process doubles for
external boundaries. Every API endpoint must have at least one HTTP-boundary
test in both `tests/unittests/apis/<router>/` and `tests/integration/`. Unit
tests must be in the matching router directory so identical method/path pairs
in different routers are checked independently. In CI, where `ENV=CI` is
injected, integration tests use
the `mock_infrastracture_injection_when_ci` fixture to replace external
infrastructure with in-memory doubles while preserving the application wiring.

Unit test paths mirror implementation module paths under `src/recnavi/`.
For `src/recnavi/<path>/<module>.py`, the corresponding test is
`tests/unittests/<path>/test_<module>.py`. The mapping is required in both
directions: implementation modules require a mirrored test, and unit test
modules must identify the implementation module they test. Package marker
`__init__.py` files and tests of shared test doubles under `tests/unittests/mockups/`
are excluded. Modules that only declare Pydantic models or types, including
`apis/schemas/` and `core/types/`, are exempt until they contain behavior that
needs testing; tests under `core/types/` are exempt as well. The modules
`config/variables.py`, `exceptions/exceptions.py`, and any module named
`base_*.py` are also exempt because they do not need unit tests.

```text
src/recnavi/apis/staff/staff_router.py
tests/unittests/apis/staff/test_staff_router.py
```

The mirror check reports missing implementation or test mirrors as errors.

Every API endpoint must be exercised at least once through an HTTP client in
the unit test directory matching its router under
`tests/unittests/apis/<router>/`, and at least once in `tests/integration/`.
The `every-api-endpoint-has-unittest` and
`every-api-endpoint-has-integration-test` rules enforce these requirements.
Unit coverage is scoped to the router directory because separate routers may
expose the same HTTP method and path.

### 1. Shared Mock Implementations

Classes implementing a `Base*` ABC must be defined in `tests/mockups/`, not in
individual test files. See [ARCH-003](./ARCH-003-mockups-as-mock-layer.md) for
the complete mock placement policy.

### 2. Integration Collaborators

Integration files, including `conftest.py`, must not contain the text `patch`
(case-insensitive). This deliberately conservative check includes imports,
aliases, fixture parameters, comments, strings, and all `monkeypatch` methods.
There are no exceptions for environment configuration, notification clients,
model resolution, or HTTP PATCH calls. Prefer false positives over missed
component replacements; any future exception requires an explicit ADR change.

Authentication is the only dependency that tests may override. Use
`app.dependency_overrides[verify_user]` directly and restore it in `finally`.
Do not override other dependencies or clear the entire override mapping.
The rule checks each occurrence, not whether a file mentions `verify_user`.

The shared CI infrastructure setup remains in `tests/integration/conftest.py`.
Individual tests must use that existing infrastructure, insert records through
its public interface, and remove their records in `finally`. Do not replace
`app.state.database` or storage objects per test. Configure environments outside
the test body rather than modifying them with test substitution helpers.

Every `test_*` function or test method under `tests/integration/` must make
an HTTP request in its own body and assign the result to `response`:

```python
def test_update_scene(client, auth_headers):
    response = client.post(
        "/updateScene",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 200
```

Use `response = client.get(...)`, `response = client.post(...)`, or the
corresponding `put`, `patch`, `delete`, `options`, `head`, or `trace` method.
Awaited calls and annotated response assignments are also supported.
Model construction, `model_dump()`, direct application/core calls, and
`app.openapi()` alone belong in unit tests and do not satisfy this requirement.

The `integration-test-must-call-http-client` rule checks each test's Python
AST independently, including methods in `Test*` classes. Fixtures, helpers,
comments, string literals, and nested function/class/lambda bodies do not
count as HTTP calls in the test. This is a structural check; reviewers must
still verify that requests execute and assertions cover the intended behavior.

### 3. Fixture Scope

Fixtures that create expensive resources such as HTTP clients, database
tables, or indexes must use `module` or `session` scope when sharing the
resource is safe. Avoid recreating those resources for every test.

Asynchronous fixtures must use `@pytest_asyncio.fixture`, not
`@pytest.fixture`.

### 4. Unit Test Network Isolation

Unit tests must not make real outbound HTTPS calls. Use a fake client or mock
the HTTP client at the import binding. If a test genuinely requires a network
service, it belongs in the integration layer with an explicit environment
policy.

### 5. Private Attribute Patching

Before using `monkeypatch.setattr(obj, "_attribute", value)`, verify that the
attribute exists on the target object. When a collaborator is instantiated
inside a method, patch the class at its import binding instead of an instance
attribute that may not exist.

### 6. Application Use-Case Tests

Application use cases are responsible for orchestration and delegation. When a
use case delegates to a core function, its unit test should isolate the core
collaborator and verify only the application-layer contract:

1. The core collaborator is called once with the intended arguments.
2. The value returned by the core collaborator is returned unchanged by the
   use case.

Application tests should not duplicate core-layer domain behavior, such as
project construction, authorization rules, scene generation, or persistence
serialization. Those behaviors belong in core-layer tests. Persistence and
component wiring belong in integration tests when they need to be verified
together.

Patch the collaborator at the import binding used by the application module,
not necessarily at the collaborator's definition module. For example:

```python
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from application.foo import hoge_usecase


@pytest.mark.asyncio
async def test_hoge_usecase_delegates_to_core():
    expected_output = object()
    with patch(
        "application.foo.hoge_function",
        new=AsyncMock(return_value=expected_output),
    ) as mock_hoge_function:
        result = await hoge_usecase(
            key_1="val_1",
            key_2="val_2",
        )

    mock_hoge_function.assert_awaited_once_with(
        key_1="val_1",
        key_2="val_2",
    )
    assert result is expected_output
```

### 7. AWS Resource Cleanup

Integration tests outside CI may access real AWS resources. Tests that create
temporary AWS resources or data must clean them up reliably. Temporary AWS
resource names must use the `it_` prefix so that test-owned resources are
identifiable and safe to remove.

Each test module must inject the data required for its own responsibility and
remove it after the test completes. Use the `fixture + yield + cleanup`
pattern so cleanup runs even when assertions fail:

```python
@pytest_asyncio.fixture
async def integration_data(database):
    item = {
        "id": "it_example",
        "data": "mock_data"
    }
    await database.put_item(item)
    
    yield
    with suppress(Exception):
        await database.delete_item({"id": item["id"]})
```

Cleanup coverage for every temporary AWS resource and injected test datum is a
manual review requirement. It is intentionally not enforced by Archgate,
because the complete lifecycle cannot be reliably determined from static
source inspection.

## Automated Enforcement

The following implementation rules are active:

- `src-module-must-have-mirrored-unittest`
- `unittest-must-mirror-src-module`
- `every-application-usecase-has-unit-test`
- `application-usecase-must-patch-core-collaborator`
- `application-usecase-must-propagate-mock-output`
- `every-api-endpoint-has-unittest`
- `every-api-endpoint-has-integration-test`
- `integration-test-must-call-http-client`
- `no-patch-in-integration-tests`
- `async-fixture-must-use-pytest-asyncio-fixture`
- `mock-abc-class-must-be-in-mockups-dir`
- `expensive-fixture-must-not-use-function-scope`
- `unit-test-must-not-make-real-http-calls`
- `monkeypatch-setattr-underscore-attribute`

All listed rules use `error` severity and block the Archgate check when
violated.

## Compliance

**Do:**

- Put unit tests at `tests/unittests/<src-relative-path>/test_<module>.py`
- Keep additional tests for one implementation module in its mirrored directory
- Put reusable `Base*` mock implementations in `tests/mockups/`
- Keep integration tests connected to real collaborators
- Assign `response` from an HTTP `client` call in every integration test
- Use `@pytest_asyncio.fixture` for asynchronous fixtures
- Use `module` or `session` scope for expensive shared fixtures
- Mock outbound HTTP in unit tests
- In application use-case unit tests, isolate core collaborators and verify
  intended calls and unchanged return-value propagation
- Verify private attributes before patching them
- Prefix temporary AWS resource names with `it_`
- Inject module-owned test data and clean it up with `fixture + yield + cleanup`
- Manually verify that every temporary AWS resource and test datum is cleaned up

**Don't:**

- Put a unit test in a path or filename that cannot be mapped to its implementation module
- Patch services, agents, stores, or I/O in integration tests
- Put model-only or direct-function tests in `tests/integration/`
- Define reusable `Base*` mock classes inside test files
- Recreate database tables, HTTP clients, or indexes per test unnecessarily
- Make unit tests call real external URLs
- Duplicate core-layer domain behavior in application use-case tests
- Assume a private attribute exists merely because it has an underscore prefix
- Leave temporary AWS resources or injected test data behind after integration tests

## References

- [ARCH-003](./ARCH-003-mockups-as-mock-layer.md)
- [ARCH-004](./ARCH-004-testing-strategy.md)
