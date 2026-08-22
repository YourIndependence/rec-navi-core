---
id: ARCH-011
title: Test Implementation Rules
domain: testing
status: active
date: 2026-07-11
rules: true
files:
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
external boundaries.

### 1. Shared Mock Implementations

Classes implementing a `Base*` ABC must be defined in `tests/mockups/`, not in
individual test files. See [ARCH-003](./ARCH-003-mockups-as-mock-layer.md) for
the complete mock placement policy.

### 2. Integration Collaborators

Integration tests must not use `@patch` or `monkeypatch.setattr()` to replace
services, agents, stores, or I/O collaborators. FastAPI dependency overrides
and environment configuration through `monkeypatch.setenv()` or
`monkeypatch.setitem()` are allowed.

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

## Automated Enforcement

The following implementation rules are active:

- `no-patch-in-integration-tests`
- `no-monkeypatch-setattr-component-in-integration`
- `async-fixture-must-use-pytest-asyncio-fixture`
- `mock-abc-class-must-be-in-mockups-dir`
- `expensive-fixture-must-not-use-function-scope`
- `unit-test-must-not-make-real-http-calls`
- `monkeypatch-setattr-underscore-attribute`

All listed rules use `error` severity and block the Archgate check when
violated.

## Compliance

**Do:**

- Put reusable `Base*` mock implementations in `tests/mockups/`
- Keep integration tests connected to real collaborators
- Use `@pytest_asyncio.fixture` for asynchronous fixtures
- Use `module` or `session` scope for expensive shared fixtures
- Mock outbound HTTP in unit tests
- Verify private attributes before patching them

**Don't:**

- Patch services, agents, stores, or I/O in integration tests
- Define reusable `Base*` mock classes inside test files
- Recreate database tables, HTTP clients, or indexes per test unnecessarily
- Make unit tests call real external URLs
- Assume a private attribute exists merely because it has an underscore prefix

## References

- [ARCH-003](./ARCH-003-mockups-as-mock-layer.md)
- [ARCH-004](./ARCH-004-testing-strategy.md)
