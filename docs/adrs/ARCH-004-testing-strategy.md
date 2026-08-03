---
id: ARCH-004
title: Layered Testing Strategy
domain: testing
status: active
date: 2026-07-11
rules: true
files:
  - 'tests/**/*.py'
  - '.devcontainer/local/localstack/init.sh'
  - '.github/workflows/integration-tests.yaml'
---

## Context

Before establishing a testing strategy, the following problems existed:

- The boundary between `tests/unittests/` and `tests/integration/` was unclear; the same behavior was tested redundantly at multiple layers
- Tests written solely to increase coverage metrics had no clear purpose and were difficult to maintain
- `async def test_*` functions without `@pytest.mark.asyncio` could **silently pass without executing** the test body — a particularly dangerous failure mode
- There was no habit of writing regression tests when fixing bugs, so the same bug recurred
- Integration tests used `@patch` to replace real components, defeating the purpose of integration testing
- LocalStack-backed integration tests could fail when required seed data (agent metadata, permissions, task records, or log records) was present in real dev AWS but missing from local DynamoDB tables
- Real AWS / ECS tests and LocalStack-backed integration tests shared similar file locations, so the execution boundary had to be explicit to avoid accidental CI slowdowns or unsupported LocalStack API calls

Implementation-level rules — mock patterns, fixture scope, transport selection, conftest organization — are specified in [ARCH-011](./ARCH-011-test-implementation.md).

## Decision

**Tests must have a clear purpose and layer responsibility. Achieve maximum protection with the minimum necessary number of tests.**

### 1. The Testing Honeycomb Model

For backend microservices and AI-agent APIs, the **testing honeycomb** is the preferred model over the traditional pyramid. Integration tests form the largest layer because they verify component interactions — which is where most defects actually occur in loosely-coupled architectures.

```
         ┌─────────────────┐
         │   E2E tests      │  ← minimal (slow, brittle)
    ┌────┴──────────────────┴────┐
    │    integration tests        │  ← largest layer (real wiring)
┌───┴────────────────────────────┴───┐
│         unit tests                  │  ← fast, focused on logic
├─────────────────────────────────────┤
│  static analysis (mypy, ruff)       │  ← zero runtime cost
└─────────────────────────────────────┘
```

| Test type       | Location             | What it tests                                        | Mock policy                                          |
| --------------- | -------------------- | ---------------------------------------------------- | ---------------------------------------------------- |
| **Unit**        | `tests/unittests/`   | Single function / class / agent input-output / logic | `unittest.mock`, lightweight fakes, `botocore.stub.Stubber`, `moto`, `tests/mockups/` fixtures |
| **Integration** | `tests/integration/` | Real component interactions across multiple layers   | LocalStack / service containers by default; real cloud services only behind explicit markers |

Mirror `src/trust/` in directory structure:

```
tests/unittests/
  apis/          # FastAPI router unit tests
  application/   # Use-case function unit tests
  core/          # Agent / preprocessor unit tests
  infrastructure/# DB adapter / external client unit tests
tests/integration/
  apis/          # HTTP layer through to application
  agents/        # Agent + tools + LLM integration tests
```

### 1-1. External Service Boundary

Unit tests must not require LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or GitHub repository secrets. They should prove behavior by using in-process test doubles such as `tests/mockups/`, lightweight fake clients, `botocore.stub.Stubber`, or `moto` where moto is stable for that service.

Integration tests keep the historical default behavior: `pytest tests/integration/` collects both local-service tests and real-AWS tests. Tests that require real cloud resources must be marked explicitly so LocalStack-backed profiles can skip them during collection:

```python
pytestmark = [pytest.mark.real_aws]

# ECS task dispatch is a narrower real-AWS dependency:
pytestmark = [pytest.mark.real_aws, pytest.mark.ecs]
```

When `AWS_ENDPOINT_URL` points to LocalStack, `tests/integration/conftest.py` automatically skips `real_aws` tests. The pytest command itself stays unchanged:

```bash
uv run pytest --disable-warnings -q --durations=10 tests/integration/
```

This preserves the existing EC2 / real-AWS integration workflow while keeping GitHub Actions, devcontainer, and local compose runs from calling real AWS resources or LocalStack features that are not available in the free image.

### 1-2. Local Integration Data Contract

LocalStack-backed integration tests must be able to run from an empty local service stack. Any data that a test needs because production/dev environments usually contain it must be migrated into the test layer explicitly.

**Required local data belongs in one of these places:**

| Data type | Preferred home | Reason |
| --------- | -------------- | ------ |
| DynamoDB table schema | `.devcontainer/local/localstack/init.sh` | Service startup owns schema creation |
| Shared session seed data | `tests/integration/conftest.py` session fixture | One setup point for local/CI integration tests |
| Per-test agent metadata | `create_mock_agent` fixture | Generates unique names and cleans up AgentAtelier + PermissionTable |
| Per-test permission graph | Test-local fixture with `try/finally` cleanup | Permission tests intentionally validate table behavior |
| Per-test task/log records | Named fixture (`require_task_records`, `test_conversation`, etc.) | Makes synthetic ECS/log state explicit |
| Real cloud fixtures | `real_aws` / `ecs` marked integration tests | Avoids implying LocalStack coverage where none exists |

The integration stack must not rely on real dev data being pre-populated. For example, if `/cms/getAgents` requires a root `TRUST` agent, the root agent record must be seeded in `tests/integration/conftest.py`; if `/task/status` expects at least one task row, a synthetic task record fixture must create it.

When adding a new integration test that depends on mock data, update all three places together:

1. **Schema**: add missing LocalStack DynamoDB tables, GSIs, S3 buckets, or Secrets Manager values to `.devcontainer/local/localstack/init.sh`.
2. **Seed fixture**: add reusable seed data to `tests/integration/conftest.py` only when multiple tests or endpoints rely on it.
3. **Documentation/rules**: update this ADR, [ARCH-011](./ARCH-011-test-implementation.md), and the corresponding `.rules.ts` checks when the new data contract is reusable.

Per-test records must use unique names or UUIDs (`it_...`, random suffix, or `uuid4`) and must clean up when the test writes to shared real AWS resources. LocalStack CI containers are ephemeral, but real-AWS mode is not.

### 2. Use-Case-Driven Design Principle

Write tests to prove "this use case works correctly" or "this bug will not recur". Do not write tests to improve coverage metrics.

```
✅ Purposeful tests:
  - "ClientValueError is raised when store_name is unregistered"
  - "RuntimeError is raised when the DynamoDB table does not exist"
  - "bug: empty groupId returns None (missing None guard)"
  - "CMS flow with 2+ preprocessing steps completes end to end"

❌ Purposeless tests:
  - "the function exists" — guaranteed by mypy / Pyright
  - "the class can be instantiated" — proves nothing
  - "the mock was called" — tests implementation details, not behavior
```

Integration tests in particular should be designed around **customer journeys** — the sequences of actions a real user would perform across multiple API calls. A test that exercises only a single endpoint in isolation adds less value than a test that walks through a complete user-facing flow (create → configure → query → verify result).

### 3. Mandatory TDD for New Features

All new feature implementations must use TDD (RED → GREEN → REFACTOR).

| Phase      | Rule                                                                                                                        |
| ---------- | --------------------------------------------------------------------------------------------------------------------------- |
| 🔴 RED      | Write one failing test → confirm **FAIL** with `uv run pytest tests/path/test_file.py -v` before writing any implementation |
| 🟢 GREEN    | Write the minimum implementation to make the test pass → confirm **PASS**                                                   |
| 🔵 REFACTOR | Clean up the code → confirm the test still passes                                                                           |

> **Constraint**: If the test passes before any implementation exists, it is not proving anything — rewrite it.

### 4. Prove-It Pattern for Bug Fixes

Before fixing a bug, write a test that reproduces it. The test going RED confirms the bug is reproduced; GREEN confirms the fix is correct and prevents recurrence.

```python
# ✅ Name the test after the symptom — not the fix
async def test_bug_empty_store_name_raises_client_error():
    """bug: empty store_name should raise ClientValueError, not KeyError"""
    # Arrange: minimal conditions that reproduce the bug
    # Act: execute the broken operation
    # Assert: expect correct (post-fix) behavior
    with pytest.raises(ClientValueError):
        await retrieve(store_name="", ...)

# ❌ Do not name it after the fix
async def test_fix_add_store_name_validation():
    ...
```

**Sequence:**

1. Write the test → `uv run pytest tests/path/test_file.py::test_name -v` → **FAIL (🔴)** — bug reproduced
2. Fix the production code → same command → **PASS (🟢)** — bug fixed
3. `uv run pytest tests/unittests/ -n auto --dist loadscope -m "not libreoffice" -v` -> all non-LibreOffice unit tests GREEN -> no regression

If the test passes from the start, the bug has not been reproduced. Revisit the test.

### 5. Mirror Test Prohibition

A **mirror test** generates expected values using the same logic as the code under test. It can never detect implementation bugs.

```python
# ❌ Mirror test: expected value generated by the same filter logic
def test_get_permitted_stores():
    stores = get_all_stores()
    result = filter_stores_by_user(stores, user)
    expected = [s for s in stores if s.owner == user.id]  # same condition — tautology
    assert result == expected

# ✅ Behavioral invariant: every returned item belongs to that user
def test_get_permitted_stores():
    result = filter_stores_by_user(get_all_stores(), user)
    assert len(result) > 0
    assert all(s.owner == user.id for s in result)
```

### 6. asyncio Configuration — Ideal vs. Current

**Ideal (2026 standard):** Configure `asyncio_mode = "auto"` with `asyncio_default_fixture_loop_scope` in `pyproject.toml`. Since pytest-asyncio v0.19.0, auto mode eliminates both the decorator requirement and the silent-PASS risk. As of pytest-asyncio v1.x, the loop scope must be specified explicitly to avoid deprecation warnings.

```toml
# pyproject.toml — ideal configuration
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

**Current state (accepted deviation):** `asyncio_mode` is not configured. Every `async def test_*` function must carry `@pytest.mark.asyncio` explicitly. See [known-deviations.md](./known-deviations.md) for migration status.

Until migration is complete: **every `async def test_*` function (or its enclosing class) must have `@pytest.mark.asyncio`.**

```python
# ✅ Correct: decorator present
@pytest.mark.asyncio
async def test_conversation_returns_event():
    ...

# ✅ Correct: class-level (applies to all async methods)
@pytest.mark.asyncio
class TestConversation:
    async def test_streaming(self):
        ...

# ❌ Wrong: no decorator — test body will not execute, silently PASS
async def test_conversation_returns_event():
    ...
```

### 7. @patch Prohibited in Integration Tests

Integration tests exist to verify that real components work together. Replacing any component with `@patch` (including `monkeypatch.setattr()` on service, agent, store, or I/O attributes) makes the test functionally equivalent to a unit test.

**Why this matters:** if the integration test mocks a component, it cannot detect bugs in how that component interacts with its collaborators — exactly the category of bug that integration tests are designed to catch.

`monkeypatch` is permitted in integration tests **only** for configuring the test environment (environment variables, config values). It is never permitted for replacing a real component.

For implementation patterns (FastAPI DI overrides, moto, conftest alternatives), see [ARCH-011](./ARCH-011-test-implementation.md).

Provider availability checks must reflect whether the test actually calls the provider. If a test uses a deterministic `MockModel`, it must not be skipped just because `AZURE_OPENAI_ENDPOINT` is absent. Conversely, a test that exercises Azure Document Intelligence must require both endpoint and API key.

### 8. Property-Based Testing

For functions with complex input spaces (validators, parsers, formatters), complement example-based tests with property-based tests using [Hypothesis](https://hypothesis.readthedocs.io/).

```python
from hypothesis import given, settings, strategies as st

@given(st.text(min_size=1, max_size=500))
def test_sanitize_prompt_never_raises(raw_input: str):
    result = sanitize_prompt(raw_input)
    assert isinstance(result, str)
    assert len(result) <= 500
```

Apply to: input validators, text processors, data transformation pipelines, boundary-condition-heavy logic. Do not apply mechanically to all tests — use where the input space is large or poorly understood.

**CI profile configuration** — Hypothesis examples should scale with the environment:

```python
# tests/conftest.py
from hypothesis import settings, HealthCheck
import os

settings.register_profile("ci", max_examples=100, suppress_health_check=[HealthCheck.too_slow])
settings.register_profile("dev", max_examples=10)
settings.load_profile("ci" if os.getenv("CI") else "dev")
```

### 9. Mutation Testing

For high-criticality code paths (auth, billing, safety filters), run [mutmut](https://mutmut.readthedocs.io/) (3.x) to verify that the test suite actually catches bugs. If mutants survive, the test suite has gaps.

```bash
uv run mutmut run --paths-to-mutate src/trust/core/agents/
uv run mutmut results
```

mutmut 3.5.0 introduced `type_check_command`, which filters out mutations that are already invalid according to mypy — reducing noise in CI:

```toml
# pyproject.toml
[tool.mutmut]
paths_to_mutate = "src/trust/core/"
tests_dir = "tests/"
type_check_command = "uv run mypy {filename}"
```

Apply mutation testing when:

- A module handles security or data integrity
- A bug in the module has already caused a production incident
- Coverage metrics look high but confidence is low

### 10. AI Agent Testing

For Google ADK agents, use the built-in `AgentEvaluator` to verify tool call trajectories and response quality. This evaluates the agent's reasoning path — not just its final output.

```python
# tests/integration/agents/test_root_agent_eval.py
from google.adk.evaluation.agent_evaluator import AgentEvaluator
import pytest

@pytest.mark.asyncio
async def test_root_agent_eval():
    await AgentEvaluator.evaluate(
        agent_module="trust.core.agents.root_agent",
        eval_dataset_file_path_or_dir="tests/data/evals/root_agent/",
    )
```

Evaluation datasets live in `tests/data/evals/<agent_name>/` as `.test.json` or `.evalset.json` files. Each case specifies:

- `conversation` — the input turns
- `expected_tool_use` — expected tool call names and arguments
- `reference_final_response` — a reference answer for similarity scoring

**Four-layer evaluation model for AI agents:**

| Layer             | Mechanism                             | Determinism        |
| ----------------- | ------------------------------------- | ------------------ |
| Schema validation | Pydantic `model_validate` on response | Deterministic      |
| Trajectory check  | `AgentEvaluator` tool-call sequence   | Semi-deterministic |
| Semantic quality  | LLM-as-judge or ROUGE scoring         | Non-deterministic  |
| Human review      | PR description + QA sign-off          | Manual             |

### 11. Environment Consistency Principle

Tests must behave **consistently across environments** (LOCAL, LOCAL_CONTAINER, CI). Avoid skipping tests in CI — CI always has services provided via GitHub Actions service containers. When a service is unavailable in a specific environment, the correct response is:

1. **Fixture-level `pytest.skip`** — when a service is optional and its absence is expected (e.g., OpenSearch in LOCAL without compose)
2. **`@pytest.mark.skipif`** — when a specific credential or endpoint is genuinely never available in CI (e.g., real Azure OpenAI, Box, SharePoint)
3. **In-process doubles** — for AWS-like behavior in unit tests, use lightweight fakes, `botocore.stub.Stubber`, or moto

Do **not** use `skip_local()` with `CI` in the condition — this defeats the purpose of CI validation.

### 12. Service Classification — What to Use Where

| Service                       | Unit tests                                    | Integration tests (LocalStack mode)                   | Integration tests (real-AWS mode, Branch 3)                         |
| ----------------------------- | --------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------- |
| AWS DynamoDB / SecretsManager | `moto @mock_aws` or `tests/mockups/` fixtures | Real service via LocalStack                           | Real AWS (dev environment)                                          |
| AWS S3 (`trust-tmp` bucket)   | Fake client, `botocore.stub.Stubber`, or moto | Real service via LocalStack                           | Real AWS                                                            |
| AWS ECS (`run_task`)          | Mock ECS client and task table                | Auto-skipped when `AWS_ENDPOINT_URL` points to LocalStack | Real ECS in the default command                                     |
| OpenSearch                    | Skip via `pytest.skip` in fixture if None     | Real OpenSearch service container                     | Real dev OpenSearch domain (`OPENSEARCH_ENDPOINT` env var required) |
| MySQL / Session DB            | Not required                                  | Real service via docker-compose                       | `DATABASE_HOST` env var; real RDS or local MySQL                    |
| Cognito / Auth                | `get_mock_x_user` fixture                     | Real cognito-local or skip with `@pytest.mark.skipif` | Real Cognito User Pool (or local if `COGNITO_IDP_ENDPOINT_URL` set) |
| SharePoint Online (SPO)       | Skip when `MS_TENANT_ID == "local-tenant-id"` | Skip (same)                                           | Skip (same)                                                         |
| Box                           | Skip when `BOX_CLIENT_ID` empty               | Skip (same)                                           | Skip (same)                                                         |
| Azure OpenAI (GPT-4o)         | Mock                                          | Skip only for tests calling the real provider         | Skip only for tests calling the real provider                       |
| Azure Document Intelligence   | Mock                                          | Skip when `EASTUS_ENDPOINT` or `EASTUS_API_KEY` is not set | Skip when `EASTUS_ENDPOINT` or `EASTUS_API_KEY` is not set      |
| Google Custom Search          | Mock                                          | Skip when `CX` empty                                  | Skip when `CX` empty                                                |
| Sentence Transformer          | `MockSentenceTransformer`                     | Real model or mock per test                           | Real model or mock per test                                         |
| LLM APIs (Bedrock)            | Mock                                          | Mock                                                  | Mock                                                                |

**Real-AWS integration test mode (Branch 3)** is triggered by setting `DATABASE_HOST` before running `scripts/run-integration-tests.sh`. It is intended for EC2 / GitHub Codespaces where real AWS services are reachable. `ENV` is not overridden (`LOCAL`), so `variables.py` uses `get_secret()` against real SecretsManager. Data written to real dev tables uses random UUIDs; OpenSearch index names are controlled by `TEST_STORE_NAME` to avoid collisions with shared dev state.

**Decision checklist for new tests that touch an external service:**

1. Is the service available in CI without credentials? → Use real; add service container if needed.
2. Is the service replaced by an in-process double (`tests/mockups/`, fake client, Stubber, moto, `MockSentenceTransformer`)? → Use the double; no `skipif` needed.
3. Does the service need real credentials never present in CI? → Add `@pytest.mark.skipif(not credential_var, ...)`.
4. Does the service need real AWS resources rather than LocalStack? → Move it to `tests/integration/` and add `pytest.mark.real_aws`.
5. Does the code path call `run_task` (ECS)? → Add both `pytest.mark.real_aws` and `pytest.mark.ecs`; LocalStack-backed profiles skip it automatically, while real-AWS runs still include it by default.
6. Does an extractor wrap an optional external endpoint? → Add fail-fast guard at the top of `exec_impl` (`if not ENDPOINT: raise ValueError(...)`).
7. Does the test require data that normally exists in dev AWS? → Migrate the schema/seed data into LocalStack init or `tests/integration/conftest.py` before adding assertions.

### 13. `skip_local()` — Must Not Exclude CI

`tests/testing_utils.skip_local()` skips **only when `ENV == "LOCAL"`** (bare machine without docker-compose). Including `"CI"` in the condition prevents tests from running in CI pipelines, where services are provided.

```python
# ✅ Correct
def skip_local(reason="skipped in local"):
    return pytest.mark.skipif(ENV == "LOCAL", reason=reason)

# ❌ Wrong — CI tests never run
def skip_local(reason="skipped in local"):
    return pytest.mark.skipif(ENV in ["CI", "LOCAL"], reason=reason)
```

### 13-1. OpenSearch Version Must Match Production (2.13) — `knn_vector` `_source` Round-Trips

Production runs AWS OpenSearch **2.13**. The local (`.devcontainer/local/compose.yaml`) and CI
(`unittests.yaml`, `integration-tests.yaml`) service images **must pin the same 2.13 line**
(`opensearchproject/opensearch:2.13.0`), so tests exercise the same engine behavior as production.

On 2.13, `knn_vector` fields are stored verbatim in `_source`, so a `put_item` → `refresh()` →
`get_item` round-trip returns the exact vector written. Tests therefore assert full equality
(`assert item == test_item`), including `embeddingVector`.

**History — do not bump the image to 3.x without also migrating production.** A previous change
raised the local/CI image to 3.6.0 while production stayed on 2.13. OpenSearch 3.x enables
`knn.derived_source.enabled` by default for `knn_vector` fields: the raw vector is replaced with a
storage placeholder on write and reconstructed on read, and reconstruction timing relative to
`refresh()` is not guaranteed. This made the round-trip intermittently return the placeholder (an
`int`) instead of the vector — `TypeError: object of type 'int' has no len()` — and forced the
tests to weaken their assertions. Keeping the test engine aligned with production (2.13) removes
the non-determinism at the source. If production is ever upgraded to 3.x, revisit derived source
(e.g. `"knn.derived_source.enabled": False` in the index mapping) as part of that migration.

### 14. Integration Test Execution — Docker Compose Required

Integration tests **must be executed via docker compose** (locally) or via the CI integration workflow. Running `pytest tests/integration/` directly without services will produce a session-level `pytest.skip`.

```bash
bash scripts/run-integration-tests.sh            # all integration tests
bash scripts/run-integration-tests.sh -k test_greeting -v  # with filter
```

## Rationale

**Alternative A: Manage by coverage targets**
Setting a coverage percentage goal (e.g., 80%) drives tests that execute code without proving anything. Purposeless tests accumulate, increasing maintenance cost with no quality gain. Rejected.

**Alternative B: Integration tests only**
Skipping unit tests and covering everything with integration tests. Integration tests are slow and difficult to debug — locating the failing component requires significant investigation. Rejected.

**Alternative C: `asyncio_mode = "auto"` immediately**
As of pytest-asyncio v1.x, this is the recommended default. It eliminates decorator boilerplate and the silent-PASS risk. **This is the ideal long-term state.** Currently not adopted due to migration cost; tracked as a known deviation.

## Consequences

- **Positive**: Test purpose is always explicit — every test answers "why does this test exist?"
- **Positive**: TDD catches bugs immediately after implementation
- **Positive**: Prove-It pattern prevents the same bug from recurring
- **Positive**: Separating unit / integration responsibilities makes the failing component easier to identify
- **Negative**: Test design requires up-front work (use case derivation, criteria confirmation)

## Compliance

**Do:**

- Clarify "what use case does this test prove?" before writing any test
- Design integration tests around customer journeys, not isolated endpoint calls
- Add `@pytest.mark.asyncio` to every `async def test_*` function or its enclosing class (until `asyncio_mode = "auto"` is enabled)
- Write a reproducing test before fixing any bug, and confirm RED → GREEN (Prove-It)
- Use real components in integration tests; do not use `@patch` or `monkeypatch.setattr()` to replace services or I/O
- Mock AWS services with lightweight fake clients, `botocore.stub.Stubber`, or `moto` in unit tests
- Assert behavioral invariants (every item satisfies property X) when verifying algorithm correctness
- Apply Hypothesis for validators and functions with large or complex input spaces
- Configure Hypothesis profiles in `conftest.py` (`max_examples=100` in CI)
- Use `pytest.skip` (not `assert`) in fixtures that obtain optional external service connections
- Run integration tests via `bash scripts/run-integration-tests.sh` locally
- Limit `skip_local()` to `ENV == "LOCAL"` only
- Keep unit tests independent from LocalStack, real AWS, and repository secrets
- Mark real cloud integration tests with `real_aws`, and ECS dispatch tests with both `real_aws` and `ecs`
- Keep the default integration pytest command unchanged; skip `real_aws` tests automatically only when `AWS_ENDPOINT_URL` points to LocalStack
- Keep LocalStack DynamoDB schemas in `.devcontainer/local/localstack/init.sh` in sync with integration fixtures
- Seed shared integration data in `tests/integration/conftest.py` rather than depending on real dev AWS state
- Use unique `it_...` names, UUIDs, or `TEST_STORE_NAME` for records that may touch shared real-AWS resources
- Add `@pytest.mark.skipif(not MS_TENANT_ID_var, ...)` to any test that calls real SharePoint Online
- Add `@pytest.mark.skipif(not BOX_CLIENT_ID_var, ...)` to any test that calls real Box APIs
- Move real S3 bucket tests to `tests/integration/` and mark them `real_aws`; keep unit S3 tests on fake clients, Stubber, or moto
- Add `@pytest.mark.skipif(not os.environ.get("AZURE_OPENAI_ENDPOINT"), ...)` only to tests that call real Azure OpenAI (GPT-4o)
- Add `@pytest.mark.skipif(not (EASTUS_ENDPOINT and EASTUS_API_KEY), ...)` to integration tests that call Azure Document Intelligence directly
- Add a fail-fast guard (`if not ENDPOINT: raise ValueError(...)`) at the top of `exec_impl` for any extractor wrapping an optional external endpoint
- Use `real_aws` / `ecs` markers so LocalStack-backed profiles skip ECS integration tests without changing test startup options

**Don't:**

- Write tests solely to improve coverage (purposeless tests)
- Generate expected values with the same logic as the code under test (mirror tests)
- Write `async def test_*` without `@pytest.mark.asyncio` (silent PASS)
- Use `@patch`, `unittest.mock.patch`, or `monkeypatch.setattr()` to replace services, agents, stores, or I/O in `tests/integration/`
- Skip regression tests when fixing a bug
- Re-assert at runtime what the type system already guarantees (`assert isinstance(result, object)`)
- Use `assert` on a service fixture return value — use `pytest.skip` instead
- Include `"CI"` in `skip_local()` conditions — CI must execute tests with services provided
- Run `pytest tests/integration/` directly without docker compose services
- Call real SharePoint / Box APIs in unit tests without a credential-based `skipif` guard
- Add unit tests that need a real S3 bucket, ECS task, Microsoft tenant, Box account, Azure endpoint, or repository secret
- Skip a mocked unit or integration test only because a real provider credential is absent
- Call `get_sentence_transformer_model` in unit tests without mocking it — the model download hangs in CI
- Allow an extractor's `exec_impl` to proceed when its required endpoint variable is empty — always fail-fast with `ValueError` so the fallback chain can recover
- Call `run_task` (ECS) from an unmarked LocalStack-backed test — ECS dispatch tests need `real_aws` / `ecs` markers so LocalStack profiles skip them
- Assume local/CI integration tests can read pre-existing dev AWS data such as root agents, permissions, task records, log records, or OpenSearch indexes
- Add shared seed data inline in a single test when multiple integration tests depend on the same record

## Human-Only ADR Compliance Checks

The following rules are enforced by code review, not by automated tools:

- **Use-case naming**: Test names must describe a behavior or bug symptom, not an implementation detail
- **Customer journey coverage**: Integration tests should cover complete user flows, not just isolated endpoints
- **Mirror test detection**: Review expected-value generation for tautologies
- **TDD sequence**: Confirm that RED was observed before implementation in PR description
- **Mutation test coverage**: For security-critical modules, require mutmut results in the PR
- **Service fixture review**: Verify that fixtures obtaining external connections use `pytest.skip`, not `assert`, when the connection is unavailable
- **Integration test scope**: Confirm that integration tests do not duplicate unit-test-level logic, that real components are used throughout, and that any `monkeypatch.setattr()` usage replaces only environment configuration — not services or I/O
- **Mock data migration**: Confirm that integration tests depending on dev-like data added LocalStack schema and deterministic seed fixtures, and that real-AWS runs use unique names plus cleanup

## References

- [ARCH-003](./ARCH-003-mockups-as-mock-layer.md) — centralized mock implementations
- [ARCH-011](./ARCH-011-test-implementation.md) — test implementation patterns, mock/fixture details
- `.devcontainer/local/localstack/init.sh` — LocalStack DynamoDB/S3/Secrets schema for integration tests
- `tests/integration/conftest.py` — shared integration seed fixtures
- [known-deviations.md](./known-deviations.md) — accepted deviations from ideal rules
- `tests/conftest.py` — `pytest_plugins` registration list
- `tests/mockups/` — mock implementation list
- [pytest-asyncio docs](https://pytest-asyncio.readthedocs.io/en/stable/reference/configuration.html)
- [Hypothesis docs](https://hypothesis.readthedocs.io/)
- [mutmut docs](https://mutmut.readthedocs.io/)
- [FastAPI async testing](https://fastapi.tiangolo.com/advanced/async-tests/)
- [Spotify Testing Honeycomb](https://engineering.atspotify.com/2018/01/testing-of-microservices/)
- [Google ADK AgentEvaluator](https://google.github.io/adk-docs/evaluate/)
