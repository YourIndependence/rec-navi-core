---
id: ARCH-011
title: Test Implementation Patterns
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

[ARCH-004](./ARCH-004-testing-strategy.md) defines the testing strategy — what to test, why, and in which layer. This ADR defines **how** to implement those tests efficiently and consistently.

Before these patterns were established:

- Async fixtures used `@pytest.fixture` instead of `@pytest_asyncio.fixture`, causing warnings and event-loop scope mismatches
- Mock classes were defined inline in test files and duplicated across modules
- `@patch` and `monkeypatch.setattr()` were used in integration tests without understanding the distinction between component replacement and environment configuration
- Expensive setup (HTTP clients, DB connections) ran in function-scoped fixtures, slowing test suites significantly
- No consistent approach for FastAPI integration testing transport (TestClient vs. AsyncClient)
- Integration tests sometimes assumed dev AWS already contained root agents, permissions, task records, or log records, which failed in clean LocalStack CI
- Mocking rules did not distinguish deterministic boundary doubles (LLM model resolution, notification sending, ECS handoff setup) from prohibited replacement of application logic under test

## Decision

**Test implementation must use the shared infrastructure in `tests/mockups/` and `tests/testing_utils.py`. Fixture scopes must reflect the cost of setup. Mock and monkeypatch usage must follow explicit Do/Don't rules.**

### 1. Common Test Infrastructure

#### 1-1. `tests/mockups/` — Shared Mock Implementations

All mock classes that implement core ABCs (`Base*`) live in `tests/mockups/` and are auto-loaded as pytest plugins via `pytest_plugins` in `tests/conftest.py`. See [ARCH-003](./ARCH-003-mockups-as-mock-layer.md) for the full policy.

| File                           | Key Classes / Fixtures                                                                       | Fixture Scope     |
| ------------------------------ | -------------------------------------------------------------------------------------------- | ----------------- |
| `mock_database.py`             | `mock_db_url`, `mock_rdb_engine`, `mock_database_session_service_and_db_engine`              | function / async  |
| `mock_dynamo_db.py`            | `mock_models_table` (module), `mock_log_table`, `mock_user_setting_table`, `mock_task_table` | module / function |
| `mock_llm.py`                  | `MockLlmConnection`, `MockModel`, `MockLlmClient`                                            | imported directly |
| `mock_users.py`                | `mock_x_user`, `mock_user` + `get_mock_x_user()`, `get_mock_user()`                          | function          |
| `mock_dataloader.py`           | `mock_dataloader`, `MockDataloader`                                                          | function          |
| `mock_s3.py`                   | `mock_s3`, `S3Mock`                                                                          | function          |
| `mock_sentence_transformer.py` | `mock_sentence_transformer`, `MockSentenceTransformer`                                       | function          |
| `mock_runner.py`               | `MockRunner`, `make_mock_event()`                                                            | imported directly |
| `mock_opensearch.py`           | `OpensearchDatabaseMock`                                                                     | imported directly |

Use the auto-loaded fixture wherever possible. Do not define inline mock classes in test files.

#### 1-2. `tests/testing_utils.py` — Shared Test Utilities

| Function                                       | Purpose                                                                |
| ---------------------------------------------- | ---------------------------------------------------------------------- |
| `skip_local(reason)`                           | Skip when `ENV == "LOCAL"` (bare machine, no compose)                  |
| `is_aws_available()`                           | True when CI, LOCAL_CONTAINER, or credentials exist                    |
| `skip_no_aws(reason)`                          | Skip when no AWS services are available                                |
| `get_test_runner(model, session_service)`      | Create `Runner` with `get_root_agent()` + `InMemorySessionService`     |
| `requests_conversation_without_streaming(...)` | Run conversation through chat application with mocks, return `Session` |
| `simplify_events(events)`                      | Extract `(author, simplified_content)` tuples from `Event` list        |
| `simplify_contents(contents)`                  | Extract `(role, simplified_content)` tuples from `Content` list        |
| `get_session_mock(...)`                        | Create a mock `Session` object                                         |
| `get_test_token()`                             | Get a real Cognito token (requires `TEST_COGNITO_CLIENT_ID`)           |

### 2. Fixture Scope and Caching

Choose fixture scope based on setup cost, not convenience. Expensive operations that are idempotent must use `session` or `module` scope.

| Scope                | When Reset                  | Typical Usage                      | Examples                                |
| -------------------- | --------------------------- | ---------------------------------- | --------------------------------------- |
| `function` (default) | After each test             | Isolated mutable state             | Most mock instances, temp resources     |
| `module`             | After all tests in a module | Expensive setup shared within file | `mock_models_table`, embedding registry |
| `session`            | Once per test session       | Shared infrastructure              | `client`, `auth_headers`, `store_setup` |

**Rule:** If a fixture creates a database table, HTTP client, or OpenSearch index, it must use `module` or `session` scope.

**Anti-pattern — expensive setup in function scope:**

```python
# ❌ Creates a DynamoDB table for every single test
@pytest.fixture
async def table():
    with mock_aws():
        table = dynamodb.create_table(...)
        yield table

# ✅ Create once per module; all tests in the file share it
@pytest_asyncio.fixture(scope="module")
async def table():
    with mock_aws():
        table = dynamodb.create_table(...)
        yield table
```

### 3. Async Fixture Declaration

Async fixtures must use `@pytest_asyncio.fixture`, not `@pytest.fixture`. As of pytest-asyncio v1.x, using `@pytest.fixture` for an `async def` fixture raises a deprecation warning and may cause event-loop scope mismatches.

```python
import pytest_asyncio

# ✅ Correct: pytest_asyncio.fixture for async fixtures
@pytest_asyncio.fixture(scope="module")
async def opensearch_database():
    db = await OpensearchDatabase.get_database_instance()
    if db is None:
        pytest.skip("OpenSearch not available. Set OPENSEARCH_ENDPOINT.")
    yield db

# ❌ Wrong: pytest.fixture on async def
@pytest.fixture(scope="module")
async def opensearch_database():
    ...
```

For `session`-scoped async fixtures with pytest-asyncio v1.x, add `loop_scope`:

```python
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def session_level_resource():
    ...
```

### 4. @patch and monkeypatch — Do/Don't Rules

#### 4-1. In Unit Tests

`unittest.mock.patch` and `monkeypatch.setattr()` are permitted in unit tests to isolate the unit under test from its collaborators.

```python
# ✅ Unit test: patch at the module binding (not in the defining module)
with patch("trust.core.agents.util_tools.check_user_language", return_value="en"):
    result = await agent.run(...)

# ✅ Patch the registry call, not the model class
with patch("trust.application.analysis.prompt_expansion.get_sentence_transformer_model",
           return_value=_mock_model):
    ...
```

Always patch at the **import binding** (the name as it appears in the module under test), not in the module where the symbol is defined.

**Verify attribute existence before `monkeypatch.setattr()`:** Passing a nonexistent attribute name raises `AttributeError` at test time and masks the real failure. Private names starting with `_` are especially error-prone because they may represent internal implementation details absent from the public interface.

When a collaborator is instantiated **inside** a method via `async with ClassName(...)` rather than stored as an instance attribute, `monkeypatch.setattr(instance, "_client", ...)` cannot intercept the call — no `_client` is ever set on the instance. Patch the **class** at its import binding instead.

```python
# ❌ Wrong: DocumentIntelligenceTextExtractor has no _client attribute.
#    The client is created per-call via `async with AsyncDocumentIntelligenceClient(...)`.
monkeypatch.setattr(document_intelligence_text_extractor, "_client", mock_client)

# ✅ Correct: patch the class at its import binding in the module under test.
mock_client = AsyncMock()
mock_client.__aenter__ = AsyncMock(return_value=mock_client)
mock_client.__aexit__ = AsyncMock(return_value=False)
monkeypatch.setattr(_di_module, "AsyncDocumentIntelligenceClient", MagicMock(return_value=mock_client))
```

**Unit tests must not make real outbound HTTP calls.** Tests in `tests/unittests/` run in CI without network access to external services. Any test that calls a real URL (e.g. a public API or website) will either fail or produce non-deterministic results. Instead, mock the HTTP client or extractor class at its import binding. If real network access is needed, move the test to `tests/integration/` with a `@pytest.mark.skipif` guard.

#### 4-2. In Integration Tests — Prohibition

`@patch` and `monkeypatch.setattr()` on service, agent, store, or I/O attributes are **prohibited** in integration tests. They remove a real component from the integration path, turning the test into a unit test.

```python
# ❌ Prohibited: replaces a real service
@patch("trust.application.chat.conversation.get_runner")
async def test_conversation_integration(mock_runner):
    ...

# ❌ Prohibited: monkeypatch.setattr on a component attribute
def test_load_history(monkeypatch, client):
    monkeypatch.setattr(log_handler, "s3", S3Mock())
    monkeypatch.setattr(log_handler, "get_runner", AsyncMock())
```

`monkeypatch` is permitted in integration tests **only** for environment configuration:

| Usage                                               | Verdict      | Reason                                  |
| --------------------------------------------------- | ------------ | --------------------------------------- |
| `monkeypatch.setenv("TIMEOUT", "5")`                | ✅ Allowed    | Configures environment, not a component |
| `monkeypatch.setitem(config, "key", val)`           | ✅ Allowed    | Configures values, not a component      |
| `monkeypatch.setattr(module, "db_client", fake)`    | ❌ Prohibited | Replaces a real collaborator            |
| `monkeypatch.setattr(module, "http_post", mock_fn)` | ❌ Prohibited | Replaces real I/O                       |

#### 4-3. FastAPI Dependency Override as Alternative

Instead of `@patch` on a dependency function, use `app.dependency_overrides` in the test fixture. This is idiomatic FastAPI and does not bypass the real ASGI stack.

```python
# ✅ Integration-safe: override the DI binding, not a module attribute
@pytest.fixture(scope="session")
def client():
    app.dependency_overrides[verify_user] = get_mock_x_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

#### 4-4. AWS Services in Unit Tests — Prefer In-Process Doubles

For AWS services in unit tests, prefer the lightest in-process double that proves the behavior:

| Pattern | Use when |
| ------- | -------- |
| Plain fake client | The unit under test calls only a few methods (`head_object`, `get_object`, paginator, etc.) |
| `botocore.stub.Stubber` | You need to validate exact boto3 request / response shapes |
| `moto` | You need service-level behavior such as DynamoDB table operations |

Do not call real AWS or LocalStack from `tests/unittests/`. Unit tests must not depend on repository secrets, AWS OIDC, SSO, or a running Docker service.

```python
class FakeS3Client:
    def head_object(self, *, Bucket: str, Key: str):
        return {"ContentType": "text/plain"}

    def get_object(self, *, Bucket: str, Key: str):
        return {"Body": io.BytesIO(b"Hello")}

with patch("trust.infrastructure.dataloader.s3_dataloader.boto3.client", return_value=FakeS3Client()):
    loader = S3Dataloader()
    assert await loader.get_content("s3://trust-tmp/hello.txt")
```

For DynamoDB-style tests where moto is the right fit:

```python
from moto import mock_aws

@pytest_asyncio.fixture(scope="module")
async def dynamo_table():
    with mock_aws():
        # moto intercepts boto3/botocore calls within this context
        table = dynamodb.create_table(...)
        yield
```

**Note:** When `AWS_ENDPOINT_URL` is set (LocalStack environment), clear it before activating moto. Moto and LocalStack cannot be active simultaneously; shared helpers such as `_isolated_mock_aws()` should restore the variable after the fixture exits.

#### 4-5. Real AWS and ECS Integration Tests — Use Markers

`run_task` dispatches an ECS task. LocalStack Free Tier does not implement ECS. Tests that intentionally exercise real AWS resources must be explicit:

```python
pytestmark = [pytest.mark.real_aws, pytest.mark.ecs]
```

The default integration command must not exclude these tests with pytest options. Instead, `tests/integration/conftest.py` skips `real_aws` tests only when `AWS_ENDPOINT_URL` points to LocalStack. This keeps real-ECS tests included in EC2 / real-AWS runs while making GitHub Actions, devcontainer, and local compose profiles safe.

If a LocalStack-backed integration fixture needs to prepare state for a path that normally dispatches ECS, prefer creating the state directly through LocalStack-supported APIs. A no-op mock is acceptable only during fixture setup, and the test itself must not claim to verify ECS dispatch.

#### 4-6. Integration Mock Data and Migration Fixtures

Integration tests must declare their data dependencies explicitly. Clean LocalStack CI starts with schemas and secrets from `.devcontainer/local/localstack/init.sh`; it does not contain dev AWS business data.

Use these shared fixtures before adding test-local setup:

| Fixture | Owns | When to use |
| ------- | ---- | ----------- |
| `seed_trust_root_agent` | Minimal `TRUST` root agent in AgentAtelier | API/agent tests that expect the root agent to exist |
| `mock_x_user` | Mock authenticated user + `__related__` permission | Tests that need permission lookup for the standard test user |
| `create_mock_agent` | AgentAtelier record + read permission + cleanup | Dynamic-agent or tool-transfer integration tests |
| `store_setup` | Local OpenSearch test store | Tests requiring an existing store |
| `require_task_records` | Synthetic task row | Status/list APIs that normally depend on ECS worker output |
| `test_conversation` | Synthetic conversation log row | Share/load history APIs that need an existing log |
| `require_synonym_words_index` / `require_toyota_words_index` | Optional OpenSearch corpus availability | Tests that depend on separately loaded production-like search data |

**Migration rule:** when a new integration test needs data that exists in dev/staging but not in a fresh LocalStack stack, add the missing schema or seed fixture in the same PR as the test.

```python
# Correct: shared dynamic-agent setup through the fixture.
async def test_tool_calling_agent(client, auth_headers, create_mock_agent):
    agent_name = create_mock_agent("it_calculator_use_agent", tools=["calculator"])
    ...
```

```python
# Correct: endpoint CRUD test owns its direct table state and cleanup.
try:
    response = client.post("/cms/createAgent", json=payload, headers=auth_headers)
    assert response.status_code == 200
finally:
    agent_atelier_table.delete_item(Key={"name": test_agent_name})
```

Do not add broad data setup to the root `tests/conftest.py`. Root conftest is for unit-safe plugins and global pytest setup. LocalStack/service-backed data belongs in `tests/integration/conftest.py`.

When writing direct DynamoDB records in integration tests:

- Use unique names (`it_...` prefix plus random suffix or `uuid4`) for agent, store, permission, task, and conversation IDs.
- Use the real Pydantic/domain models (`PermissionEntry`, etc.) where possible so attribute names match production serialization.
- Add cleanup with `try/finally` when the data can be written to real AWS in `real_aws` mode.
- Do not rely on test execution order; each test or fixture must create its own required records.
- Do not seed records through production endpoints unless the endpoint itself is part of the behavior under test.

### 5. Sentence Transformer — Always Mock in Unit Tests

`get_sentence_transformer_model` downloads from HuggingFace on first call. CI runners have no internet access; any test that triggers this call hangs indefinitely.

In unit tests, always mock via the registry call (not the model class):

```python
from tests.mockups.mock_sentence_transformer import MockSentenceTransformer

_mock_model = MockSentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

with patch("trust.application.analysis.prompt_expansion.get_sentence_transformer_model",
           return_value=_mock_model):
    ...

# Or register the mock model before the test:
from trust.core.model_registry.sentence_transformer_registry import register_model
register_model(model_name="...", model=MockSentenceTransformer("..."))
```

### 6. FastAPI Integration Testing — Transport Selection

Use `httpx.AsyncClient` with `ASGITransport` for async tests. Use `TestClient` (synchronous) for simple sync tests.

```python
import httpx

# ✅ Async test — full ASGI stack without an external server
@pytest.mark.asyncio
async def test_api_endpoint(app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/conversation", json={...})
    assert response.status_code == 200
```

**`TestClient` limitation:** Cannot be used inside `async def` test functions. For async tests, always use `AsyncClient`.

#### 6-1. Streaming and SSE Response Testing

TRUST's `/conversation` endpoint emits a **JSON Lines** stream. Select the transport that matches the test's execution context:

| Scenario                           | Transport                                         |
| ---------------------------------- | ------------------------------------------------- |
| Sync test, finite stream           | `TestClient` + `response.text.splitlines()`       |
| Async test, JSON Lines             | `AsyncClient` + `ASGITransport` + `aiter_lines()` |
| Async test, SSE with event fields  | `AsyncClient` + `ASGITransport` + `httpx-sse`     |
| App requires lifespan (DB startup) | Wrap `app` with `asgi-lifespan.LifespanManager`   |

**Sync test:**

```python
import json
from fastapi.testclient import TestClient

def test_conversation_stream(client: TestClient, auth_headers):
    response = client.post("/conversation", headers=auth_headers, json={...})
    assert response.status_code == 200
    chunks = [
        json.loads(line)
        for line in response.text.strip().splitlines()
        if line.strip()
    ]
    assert len(chunks) > 0
    for chunk in chunks:
        ConversationEventResponse.model_validate(chunk)
```

**Async test with JSON Lines:**

```python
@pytest.mark.asyncio
async def test_conversation_stream_async(app, auth_headers):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with client.stream("POST", "/conversation",
                                 headers=auth_headers, json={...}) as response:
            assert response.status_code == 200
            chunks = [
                json.loads(line)
                async for line in response.aiter_lines()
                if line.strip()
            ]
    assert len(chunks) > 0
```

**Async test with SSE field access:**

```python
from httpx_sse import aconnect_sse

@pytest.mark.asyncio
async def test_sse_fields(app, auth_headers):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        async with aconnect_sse(
            client, "POST", "/conversation",
            headers=auth_headers, json={...}
        ) as event_source:
            events = [e async for e in event_source.aiter_sse()]

    done = [e for e in events if e.event == "done"]
    assert len(done) == 1
```

### 7. External Service Guard Patterns

#### 7-1. Azure OpenAI (GPT-4o)

Only tests that call the real Azure OpenAI endpoint need an Azure OpenAI skip guard. Tests using `MockModel`, `MockLlmClient`, or a patched model resolver must run without Azure credentials.

```python
import os
_AZURE_AVAILABLE = bool(os.environ.get("AZURE_OPENAI_ENDPOINT"))

@pytest.mark.skipif(not _AZURE_AVAILABLE, reason="Azure OpenAI not configured (set AZURE_OPENAI_ENDPOINT)")
def test_conversation_with_azure_gpt(client, auth_headers): ...
```

#### 7-2. Azure Document Intelligence

Fail-fast in `exec_impl` so `ProcessTaskWithFallback` skips to the next strategy:

```python
async def exec_impl(self, source: SourceData) -> str:
    if not EASTUS_ENDPOINT:
        raise ValueError("EASTUS_ENDPOINT not configured; skipping Azure Document Intelligence")
    ...
```

Integration tests that specifically exercise this strategy:

```python
_DI_AVAILABLE = bool(EASTUS_ENDPOINT and EASTUS_API_KEY)

@pytest.mark.skipif(
    not _DI_AVAILABLE,
    reason="Azure Document Intelligence not configured (set EASTUS_ENDPOINT and EASTUS_API_KEY)",
)
def test_analysis_document_with_document_intelligence(client): ...
```

#### 7-3. SharePoint Online (SPO)

```python
_SPO_AVAILABLE = os.environ.get("MS_TENANT_ID", "local-tenant-id") != "local-tenant-id"

@pytest.mark.skipif(not _SPO_AVAILABLE, reason="Requires real SharePoint credentials (set MS_TENANT_ID)")
class TestSpoDataloaderIntegration:
    async def test_walk_folder(self, spo_loader): ...
```

#### 7-4. Box

```python
_BOX_AVAILABLE = bool(os.environ.get("BOX_CLIENT_ID", ""))

@pytest.mark.asyncio
@pytest.mark.skipif(not _BOX_AVAILABLE, reason="Requires real Box credentials (set BOX_CLIENT_ID)")
async def test_box_walk(box_loader): ...
```

#### 7-5. S3

Unit tests for S3 loaders should use a fake client or `botocore.stub.Stubber`. Do not skip unit tests because a LocalStack bucket is absent; that means the test has crossed into integration territory.

Tests that require a real bucket belong in `tests/integration/` and must be marked `real_aws`.

#### 7-6. Google Custom Search

```python
from trust.config.variables import CX as GOOGLE_CX

@pytest.mark.skipif(not GOOGLE_CX, reason="Google Custom Search not configured (set GOOGLE_CUSTOM_SEARCH_CX)")
async def test_web_search(client): ...
```

### 8. Service Fixture — pytest.skip, Not assert

Fixtures that retrieve optional external service connections must use `pytest.skip` when the connection is unavailable. Using `assert` produces `ERROR` status instead of `SKIP`, which breaks the test run.

```python
# ✅ Correct: graceful skip when OpenSearch is not available
@pytest_asyncio.fixture(scope="module")
async def opensearch_database():
    db = await OpensearchDatabase.get_database_instance()
    if db is None:
        pytest.skip("OpenSearch not available. Set OPENSEARCH_ENDPOINT.")
    return db

# ❌ Wrong: assert causes ERROR — breaks the test run
@pytest_asyncio.fixture(scope="module")
async def opensearch_database():
    db = await OpensearchDatabase.get_database_instance()
    assert db is not None  # ← ERROR when LocalStack absent
    return db
```

### 9. conftest.py Organization

- **Root** `tests/conftest.py`: Secrets Manager mocking + `pytest_plugins` list. Must be executed before any trust module imports (botocore patching must happen first).
- **`tests/integration/conftest.py`**: Session-scoped fixtures: `require_services`, `client`, `auth_headers`, `store_setup`. Must contain a service availability guard that calls `pytest.skip` when MySQL/OpenSearch are unreachable.
- **Domain `conftest.py`** (e.g., `tests/unittests/apis/conftest.py`): Domain-specific setup (FastAPI client, embedding registry, code interpreter replacement). Keep small — 20–60 lines maximum.

**`require_services` pattern — mandatory in integration conftest:**

```python
@pytest.fixture(scope="session", autouse=True)
def require_services():
    """Skip entire integration session if services are not running."""
    error = _check_required_services()
    if error:
        pytest.skip(error)

def _check_required_services() -> str | None:
    if not _is_port_open(DATABASE_HOST, DATABASE_PORT):
        return "MySQL not reachable. Run: bash scripts/run-integration-tests.sh"
    return None
```

## Compliance

**Do:**

- Use `@pytest_asyncio.fixture` for all `async def` fixtures
- Add `loop_scope="session"` to session-scoped async fixtures (pytest-asyncio v1.x)
- Import mock classes from `tests/mockups/`; do not define `Base*` implementations inline
- Use `module` or `session` scope for fixtures that create database tables, HTTP clients, or search indexes
- Use `app.dependency_overrides` to replace FastAPI dependencies in integration tests
- Use lightweight fake clients, `botocore.stub.Stubber`, or `moto @mock_aws` for AWS service isolation in unit tests
- Use `pytest.skip` (not `assert`) in fixtures that obtain optional service connections
- Clear `AWS_ENDPOINT_URL` before activating moto in environments where LocalStack may be set
- Mark real cloud integration tests with `pytest.mark.real_aws`; add `pytest.mark.ecs` for ECS dispatch tests
- Keep the default integration pytest command unchanged; let `tests/integration/conftest.py` skip `real_aws` tests only for LocalStack-backed profiles
- Mock `get_sentence_transformer_model` with `MockSentenceTransformer` in all unit tests
- Use `httpx.AsyncClient` + `ASGITransport` for async FastAPI test calls
- Add `require_services` autouse session fixture to `tests/integration/conftest.py`
- Keep reusable integration seed data in `tests/integration/conftest.py`, not root `tests/conftest.py`
- Add LocalStack table/index/bucket/secret schema to `.devcontainer/local/localstack/init.sh` before depending on it in integration fixtures
- Prefer `create_mock_agent` for dynamic-agent/tool-transfer tests; write AgentAtelier directly only when the endpoint under test is agent CRUD itself
- Use unique record names and cleanup for direct DynamoDB/OpenSearch writes that may run against real AWS
- Patch at the import binding (the name as used in the module under test)
- Verify that the attribute to be patched exists on the target before calling `monkeypatch.setattr()` — pass a nonexistent name and `AttributeError` masks the real failure
- For collaborators instantiated via `async with ClassName(...)` inside a method, patch the class at its import binding rather than a nonexistent instance attribute

**Don't:**

- Use `@pytest.fixture` for `async def` fixtures — use `@pytest_asyncio.fixture`
- Define inline mock classes for `Base*` interfaces inside test files
- Use `function` scope for expensive setup (DB tables, HTTP clients, search indexes)
- Use `@patch` or `monkeypatch.setattr()` on service, agent, store, or I/O attributes in integration tests
- Use `assert` on a service fixture return value — use `pytest.skip` instead
- Call LocalStack or real AWS from `tests/unittests/`
- Skip a test using `MockModel` only because Azure OpenAI credentials are absent
- Remove `real_aws` / `ecs` markers from ECS tests; LocalStack-backed profiles need those markers to skip unsupported real-AWS dispatch
- Put integration seed data into root `tests/conftest.py`
- Depend on dev/staging data that is not seeded in LocalStack CI
- Share hard-coded agent, store, task, or conversation IDs across tests without a unique suffix
- Write to AgentAtelier/PermissionTable directly for dynamic-agent chat tests; use `create_mock_agent` unless testing the CRUD endpoint itself
- Call `get_sentence_transformer_model` in unit tests without mocking — the model download hangs in CI
- Use `TestClient` inside `async def` test functions — use `AsyncClient` instead
- Allow `exec_impl` to proceed when its required endpoint env var is empty — fail-fast with `ValueError`
- Place tests that make real outbound HTTP calls in `tests/unittests/` — CI has no external network access; move them to `tests/integration/` with a `skipif` guard
- Call `monkeypatch.setattr(obj, "_attr", ...)` with an attribute name that does not exist on `obj` — the `AttributeError` will be raised immediately, hiding the underlying test logic

## References

- [ARCH-003](./ARCH-003-mockups-as-mock-layer.md) — centralized mock implementations
- [ARCH-004](./ARCH-004-testing-strategy.md) — testing strategy and design principles
- [known-deviations.md](./known-deviations.md) — accepted deviations
- `tests/mockups/` — mock implementation catalog
- `tests/testing_utils.py` — shared test utilities
- `tests/conftest.py` — pytest plugins registration
- [pytest-asyncio docs](https://pytest-asyncio.readthedocs.io/en/stable/reference/configuration.html)
- [FastAPI async testing](https://fastapi.tiangolo.com/advanced/async-tests/)
- [FastAPI streaming response](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [httpx-sse](https://pypi.org/project/httpx-sse/)
- [moto docs](https://docs.getmoto.org/)
- [pytest monkeypatch](https://docs.pytest.org/en/latest/how-to/monkeypatch.html)
