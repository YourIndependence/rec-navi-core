---
id: ARCH-003
title: tests/mockups/ as the Sole Source of Mock Implementations
domain: testing
status: active
date: 2026-07-11
rules: true
files:
  - 'tests/**/*.py'
---

## Context

`tests/mockups/` contains mock implementations registered as pytest plugins — concrete classes that implement core ABCs (`BaseDatabase`, `BaseStore`, `BaseLlmClient`, etc.) and are made available to all tests via `pytest_plugins` in `tests/conftest.py`.

In practice, test files sometimes define mock classes for core ABCs inline. These inline definitions bloat the test file, cannot be reused by other tests, and lead to the same mock being duplicated across multiple files.

The LocalStack-backed integration suite also needs deterministic mock data, but mock
data is not the same thing as a mock implementation. Keeping those responsibilities
separate prevents root test plugins from importing runtime configuration too early or
from depending on Docker/LocalStack during unit test collection.

## Decision

**Mock classes that implement core ABCs (`Base*`) must be placed in `tests/mockups/`. Test files contain only test functions; they do not own mock class implementations.**

### Before (wrong)

```python
# tests/unittests/apis/root/test_foo.py — inline mock class

from trust.core.store.presearch_processor.base_presearch_processor import BasePresearchProcessor

class MockFooProcessor(BasePresearchProcessor):    # must not be here
    def process(self, query: str) -> str:
        return query

def test_foo():
    proc = MockFooProcessor()
    ...
```

### After (correct)

```python
# tests/mockups/mock_foo_processor.py — centralized in mockups/

import pytest
from trust.core.store.presearch_processor.base_presearch_processor import BasePresearchProcessor

class MockFooProcessor(BasePresearchProcessor):
    def process(self, query: str) -> str:
        return query

@pytest.fixture
def mock_foo_processor() -> MockFooProcessor:
    return MockFooProcessor()
```

```python
# tests/conftest.py — register in pytest_plugins so all tests can use it

pytest_plugins = [
    ...
    "tests.mockups.mock_foo_processor",
]
```

```python
# tests/unittests/apis/root/test_foo.py — consume via fixture argument

def test_foo(mock_foo_processor):    # injected by pytest
    ...
```

### Exception: locally-scoped stubs are allowed

Inline definitions are allowed only when all of the following conditions hold:

- Does not inherit any `Base*` ABC (duck-typing only)
- Prefixed with `_` to indicate private scope
- Used by only 1–2 tests within the same file

```python
# OK: no Base* inheritance, private prefix, file-local use only
class _StubProvider:
    def get(self, key: str) -> dict:
        return {"value": 42}
```

### Integration seed data is not a mockup module

`tests/mockups/` owns reusable mock implementations and unit-safe fixtures. It must
not own LocalStack/service-backed data migration. Shared integration data belongs in
`tests/integration/conftest.py`, while DynamoDB/S3/Secrets schema belongs in
`.devcontainer/local/localstack/init.sh`.

Examples:

- `MockModel`, `MockLlmClient`, `MockSentenceTransformer` -> `tests/mockups/`
- Minimal root `TRUST` agent seed -> `tests/integration/conftest.py`
- LocalStack `AgentAtelier-dev` / `PermissionTable-dev` schema -> `.devcontainer/local/localstack/init.sh`
- Per-test dynamic agent records -> `create_mock_agent` fixture, not a new mockup module

## Rationale

**Alternative: Define all mocks inline in each test file**
Works for small files, but mock classes multiply across the codebase as the test suite grows. The `pytest_plugins` auto-provision mechanism in `tests/mockups/` is lost, meaning a change to a mock must be applied in every file that defines a copy.

**Alternative: Generate mock objects with `unittest.mock.MagicMock` / `AsyncMock` on the spot**
Effective for simple cases where no ABC implementation is needed. However, it cannot verify that the mock honors the ABC contract (method signatures, return types). When a core API changes, such tests will not catch the drift. For mocking core logic, use the `tests/mockups/` implementations.

## Consequences

- **Positive**: Core ABC mock implementations are centralized and reusable across all tests
- **Positive**: Changes to a mock are made in a single place, with no risk of missing a copy
- **Positive**: Test files contain only test logic, improving readability
- **Negative**: Adding a new mock requires both creating the file in `tests/mockups/` and registering it in `tests/conftest.py`

## Compliance

**Do:**

- Define mock classes implementing core ABCs (`Base*`) in `tests/mockups/mock_xxx.py` and expose them via `@pytest.fixture`
- Register new mockup modules in the `pytest_plugins` list in `tests/conftest.py`
- Consume mock objects through pytest fixture arguments rather than instantiating them directly in test files
- Name mock files after the target class: `mock_llm.py`, `mock_database.py`, etc.
- Put reusable LocalStack-backed seed data in `tests/integration/conftest.py`, not in `tests/mockups/`

**Don't:**

- Define `Base*` ABC mock implementations in any test file outside `tests/mockups/`
- Duplicate the same mock class across multiple test files
- Forget to add new mockup modules to `tests/conftest.py`
- Add integration seed data or LocalStack setup to `tests/mockups/`

## References

- [ARCH-001](./ARCH-001-clean-architecture.md) — where core ABCs are defined
- `tests/conftest.py` — `pytest_plugins` registration list
- `tests/mockups/` — complete list of mock implementations
- [ARCH-004](./ARCH-004-testing-strategy.md) — integration data contract and service boundaries
- [ARCH-011](./ARCH-011-test-implementation.md) — integration seed fixture patterns
