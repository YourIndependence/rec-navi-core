# Known Deviations from ADR Rules

This document tracks cases where the current codebase deliberately deviates from the ideal rules established in the Architecture Decision Records. Each deviation records the rule that is being relaxed, the exact locations affected, why enforcement was downgraded (to `warning` instead of `error`, or not captured at all), and the migration path.

The goal is **not** to permanently accept these deviations but to make them visible so they can be addressed incrementally.

---

## DEV-001 — core/ imports concrete infrastructure/ implementations

**Violates:** ARCH-001 (`no-core-imports-infrastructure`)
**Current enforcement:** `warning` (should be `error`)
**Rule file:** `ARCH-001-clean-architecture.rules.ts`

### Affected locations

| File                                                                           | Imported symbol   |
| ------------------------------------------------------------------------------ | ----------------- |
| `src/trust/core/agents/anti_corrosion_adviser/criteria_fetcher.py`             | `OpenAiLlmClient` |
| `src/trust/core/agents/util/title_generator.py`                                | `OpenAiLlmClient` |
| `src/trust/core/agents/util_tools/check_user_language.py`                      | `OpenAiLlmClient` |
| `src/trust/core/agents/util_tools/summarizer.py`                               | `OpenAiLlmClient` |
| `src/trust/core/agents/util_tools/translate.py`                                | `OpenAiLlmClient` |
| `src/trust/core/agents/util_tools/retrieve_docs.py`                            | `OpenAiLlmClient` |
| `src/trust/core/preprocessor/strategies/document_intelligence_preprocessor.py` | `OpenAiLlmClient` |

### Why enforcement is relaxed

`BaseLlmClient` in `core/external_clients_interface/` exists but is not yet wired into the registry. Enforcing this as an error today would block development while the registry migration is in progress.

### Migration path

1. Add `llm_client_registry` (or extend an existing registry) in `core/` to hold `BaseLlmClient` instances
2. Register `OpenAiLlmClient` at startup in `infrastructure/`
3. Replace all direct `OpenAiLlmClient()` instantiations in `core/` with registry lookups
4. Promote rule to `error` once all affected files are migrated

---

## DEV-002 — Pydantic BaseModel defined in application/

**Violates:** ARCH-002 (`no-domain-model-in-application`)
**Current enforcement:** `warning` (should be `error`)
**Rule file:** `ARCH-002-pydantic-first-type-system.rules.ts`

### Affected locations

| File                                         | Class                       |
| -------------------------------------------- | --------------------------- |
| `src/trust/application/validation/prompt.py` | `ResponseSchema(BaseModel)` |

### Why enforcement is relaxed

This class was added before ARCH-002 was established. Migrating it requires coordinating changes in the layers that consume it. Enforcement was downgraded to `warning` to avoid blocking unrelated PRs.

### Migration path

1. Move `ResponseSchema` to `src/trust/core/types/`
2. Update all imports in `application/` and `apis/` layers
3. Promote rule to `error` once migration is complete

---

## DEV-003 — apis/ auth middleware bypasses clean architecture

**Violates:** ARCH-001 (dependency direction: `apis/ → application/ → core/ ← infrastructure/`)
**Current enforcement:** Not yet captured in any `rules.ts` (should be `error`)
**Rule file:** — (pending addition to `ARCH-001-clean-architecture.rules.ts`)

### Affected locations

| File                          | Imported symbol                                                               |
| ----------------------------- | ----------------------------------------------------------------------------- |
| `src/trust/apis/auth/auth.py` | `get_ms_graph_user_client` from `infrastructure/external_clients/ms_clients/` |

### Why enforcement is missing

The auth middleware predates the ADR. Adding a rule that catches it immediately would require either a code fix or a suppress annotation before the rule could be enforced, creating churn in a security-sensitive file.

### Migration path

1. Define an abstract `BaseMsGraphClient` in `core/external_clients_interface/`
2. Register the concrete `ms_graph_client_manager` at startup via a registry
3. Refactor `apis/auth/auth.py` to depend on the abstract interface
4. Add an automated rule to `ARCH-001-clean-architecture.rules.ts`

---

## DEV-004 — Base* ABC mock classes defined inline in test files

**Violates:** ARCH-003 (`no-base-mock-class-in-test-file`)
**Current enforcement:** `warning` (should be `error`)
**Rule file:** `ARCH-003-mockups-as-mock-layer.rules.ts`

### Affected locations

| File                                                    | Class                                          |
| ------------------------------------------------------- | ---------------------------------------------- |
| `tests/unittests/apis/root/test_toyota_words_search.py` | `MockToyotaProcessor(BasePresearchProcessor)`  |
| `tests/unittests/apis/root/test_toyota_words_search.py` | `MockSynonymProcessor(BasePresearchProcessor)` |

### Why enforcement is relaxed

These classes were added before ARCH-003 was codified. Moving them requires creating new files in `tests/mockups/` and registering them in `conftest.py`, which is low-risk but deferred.

### Migration path

1. Create `tests/mockups/mock_presearch_processors.py` with `MockToyotaProcessor` and `MockSynonymProcessor` plus `@pytest.fixture` wrappers
2. Add the module to `pytest_plugins` in `tests/conftest.py`
3. Update `test_toyota_words_search.py` to consume the fixtures
4. Promote rule to `error`

---

## DEV-005 — @patch used in integration tests

**Violates:** ARCH-011 (`no-patch-in-integration-tests`)
**Current enforcement:** `warning` (should be `error`)
**Rule file:** `ARCH-011-test-implementation.rules.ts`

### Affected locations

Verify current state with:

```bash
grep -rn "@patch\|with patch(" tests/integration/
```

### Why enforcement is relaxed

Some integration tests patch LLM model resolution because a real or emulated LLM backend is not available in the CI environment. These tests must still exercise the HTTP/application wiring around the patched model and must not be skipped just because Azure OpenAI credentials are absent. The patch is a temporary deterministic model boundary, not proof that real Azure OpenAI is available.

This deviation does not allow arbitrary component replacement in integration tests. It is limited to deterministic LLM seams until a first-class injectable stub model is available.

### Migration path

1. Introduce a deterministic stub LLM client or model resolver fixture in `tests/mockups/`
2. Wire it as an injectable fixture for integration tests without requiring real provider credentials
3. Replace all LLM-related `@patch` usages in `tests/integration/` with the stub
4. Promote rule to `error`

---

## DEV-015 — monkeypatch.setattr() replaces real components in integration tests

**Violates:** ARCH-011 (`no-monkeypatch-setattr-component-in-integration`)
**Current enforcement:** `warning` (should be `error`)
**Rule file:** `ARCH-011-test-implementation.rules.ts`

### Affected locations

| File                                                 | Lines  | Replaced attributes                                                                                |
| ---------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| `tests/integration/apis/test_load_history.py`        | 40–44  | `log_handler.LOG_TABLE`, `log_handler.s3`, `log_handler.LOG_BUCKET_NAME`, `log_handler.get_runner` |
| `tests/integration/apis/test_load_shared_history.py` | 42–47  | `log_handler.LOG_TABLE`, `log_handler.s3`, `log_handler.LOG_BUCKET_NAME`, `log_handler.get_runner` |
| `tests/integration/apis/test_pub_router.py`          | 36, 63 | (module-level attributes via monkeypatch.setattr)                                                  |

### Why enforcement is relaxed

These tests replace `s3`, `get_runner`, and DynamoDB table references because the log handler module hard-codes its dependencies as module-level attributes rather than accepting them via dependency injection. Removing `monkeypatch.setattr` requires refactoring `log_handler` to accept its dependencies explicitly.

### Migration path

1. Refactor `log_handler` to receive `s3`, `LOG_TABLE`, and `get_runner` via constructor or FastAPI DI rather than as module-level globals
2. Replace `monkeypatch.setattr()` with `app.dependency_overrides` or fixture-injected instances
3. Verify integration tests still pass against real LocalStack services
4. Promote rule to `error`

---

## DEV-006 — asyncio_mode = "auto" not configured

**Violates:** ARCH-004 (ideal configuration, section 6)
**Current enforcement:** Not a rule violation; gap versus 2026 best practice
**Rule file:** `ARCH-004-testing-strategy.rules.ts` (rule `async-test-needs-asyncio-mark` is a compensating control)

### Description

Since pytest-asyncio v1.0.0 (May 2025), `asyncio_mode = "auto"` in `pyproject.toml` is the recommended default. It automatically treats all `async def test_*` functions as asyncio tests, removing the need for `@pytest.mark.asyncio` and eliminating the risk of the silent-PASS failure mode entirely.

The current codebase does not configure this. The `async-test-needs-asyncio-mark` rule in `ARCH-004-testing-strategy.rules.ts` is a compensating control, but it is a symptom treatment rather than a root cause fix.

### Migration path

1. Set `asyncio_mode = "auto"` in `pyproject.toml` under `[tool.pytest.ini_options]`
2. Run the full test suite and confirm all async tests still pass
3. Optionally remove redundant `@pytest.mark.asyncio` decorators (they are harmless to keep)
4. Remove or simplify the `async-test-needs-asyncio-mark` rule once migration is confirmed

---

## DEV-007 — Bare `Any` type hints without justification

**Violates:** ARCH-006 (`no-bare-any-in-signatures`, `no-any-return-type`)
**Current enforcement:** `warning` (should be `error` after migration)
**Rule file:** `ARCH-006-strict-type-hints.rules.ts`

### Affected locations

**Function signatures with `Any` (13 occurrences):**
- `src/trust/core/agents/anti_corrosion_adviser/providers/excel_provider.py:20`
- `src/trust/core/agents/anti_corrosion_adviser/providers/fallback_provider.py:22`
- `src/trust/core/agents/facilitator_agent/problems.py:96`
- `src/trust/core/database/base_database.py:71`
- `src/trust/core/external_clients_interface/base_llm_clients.py:25,30`
- `src/trust/core/utils/convert_model_to_dict.py:21`
- `src/trust/core/utils/ddb_record.py:19,30,35`
- `src/trust/infrastructure/external_clients/llm_clients.py:22,30`
- `src/trust/task_runner/local_task_runner.py:84`

**Return types with `Any` (5 occurrences):**
- `src/trust/core/preprocessor/base_preprocess_task.py:31`
- `src/trust/core/preprocessor/preprocess_task_with_fallback.py:27,54`
- `src/trust/core/utils/convert_model_to_dict.py:21`
- `src/trust/core/utils/ddb_record.py:35`

### Why enforcement is relaxed

These functions use `Any` at external boundaries (boto3, DynamoDB, untyped third-party APIs) without explicit justification comments. Adding comments to all locations would create churn before a systematic review.

### Migration path

1. Audit each usage and classify as:
   - **External boundary** (boto3, DynamoDB) → add justification comment
   - **Can use `Mapping[str, object]`** → refactor type hint
   - **Can use Pydantic model** → define in `core/types/`
2. Add justification comments for legitimate `Any` usage
3. Promote rules to `error` once all usages are reviewed

---

## DEV-008 — Broad `Exception` catching without logging + alerting

**Violates:** ARCH-007 (`no-broad-exception-in-library`)
**Current enforcement:** `warning` (should be `error` at top-level boundaries only)
**Rule file:** `ARCH-007-error-handling-patterns.rules.ts`

### Affected locations

47 occurrences across the codebase, including:
- Registry modules: `database_registry.py`, `loader_registry.py`, `store_registry.py`, etc.
- Agent tools: `document_reader_agent/tools.py`, `web_searcher_agent/tools.py`, etc.
- Infrastructure: `opensearch_database.py`, `ms_graph_client.py`, etc.
- Main entry points: `main.py`, `task_runner/__main__.py`

### Why enforcement is relaxed

Many of these are legitimate error boundaries (registries, async tasks) but lack the required `logging.error() + send_error_alert()` pattern. Enforcing as `error` immediately would block PRs while the logging infrastructure is being added.

### Migration path

1. Categorize each `except Exception` as:
   - **Top-level boundary** (registries, main.py, task runner) → add logging + alerting
   - **Library function** → refactor to catch specific exceptions
2. Add `logging.error()` + `send_error_alert()` to all top-level boundaries
3. Refactor library functions to catch specific exceptions (`ValueError`, `KeyError`, etc.)
4. Promote rule to `error` for library functions once migration is complete

---

## DEV-010 — Functions missing keyword-only parameter separator (`*`)

**Violates:** ARCH-008 (`recommend-keyword-only-params`)
**Current enforcement:** `warning` (should be `error` for public APIs)
**Rule file:** `ARCH-008-keyword-only-arguments.rules.ts`

### Affected locations

83 occurrences across the codebase, including:
- Registry methods: `database_registry.py`, `loader_registry.py`, etc.
- Agent tools: `anti_corrosion_adviser/tools.py`, `facilitator_agent/tools.py`, etc.
- Infrastructure: `opensearch_database.py`, `spo_dataloader.py`, etc.

### Why enforcement is relaxed

Many existing functions with 2+ parameters allow both positional and keyword arguments. Enforcing `*` separator would break backward compatibility for internal callers.

### Migration path

1. Audit public APIs (used by `apis/` or `application/` layers) vs. internal helpers
2. Add `*,` separator to public APIs first (prioritize those with 3+ parameters)
3. Add `*,` to internal helpers during refactoring (not urgent)
4. Promote rule to `error` for public APIs once migration is complete

---

## DEV-011 — `list[T]` used for function arguments instead of `Sequence[T]`

**Violates:** ARCH-006 (`prefer-sequence-over-list-args`)
**Current enforcement:** `warning` (should be `error` for public APIs)
**Rule file:** `ARCH-006-strict-type-hints.rules.ts`

### Affected locations

9 occurrences:
- `src/trust/application/analysis/translate.py:16`
- `src/trust/application/validation/validation.py:166`
- `src/trust/core/agents/util_tools/retrieve_docs.py:31`
- `src/trust/core/agents/util_tools/translate.py:17`
- `src/trust/core/preprocessor/preprocess_task_with_fallback.py:24`
- `src/trust/core/preprocessor/series_preprocessor.py:26`
- `src/trust/core/store/presearch_processor/query_expansion/toyota_words_query_expansion.py:109`
- `src/trust/infrastructure/dataloader/spo_dataloader.py:246,279`

### Why enforcement is relaxed

Using `list[T]` for arguments is more restrictive than necessary. Callers must pass a `list`, preventing use of `tuple`, `range`, or other sequences. This is a minor issue and low-priority refactor.

### Migration path

1. Change `list[T]` → `Sequence[T]` for function arguments
2. Keep `list[T]` for return types (concrete type preferred)
3. Promote rule to `error` after migration

---

## DEV-012 — `Any` type hint used without `object` alternative

**Violates:** ARCH-006 (`use-object-not-any`)
**Current enforcement:** `warning` (should be `error`)
**Rule file:** `ARCH-006-strict-type-hints.rules.ts`

### Affected locations

6 occurrences:
- `src/trust/core/agents/anti_corrosion_adviser/providers/fallback_provider.py:22`
- `src/trust/core/agents/facilitator_agent/problems.py:96`
- `src/trust/core/agents/util_tools/code_interpreter.py:64`
- `src/trust/core/database/base_database.py:71`
- `src/trust/core/types/conversation.py:32`
- `src/trust/core/types/dashboard/component/control_component.py:44`

### Why enforcement is relaxed

These locations use `Any` for variable annotations or simple parameters where the value can truly be anything, but they are not part of a generic type like `Mapping[str, Any]`. Converting to `object` requires careful review to ensure type compatibility with downstream consumers.

### Migration path

1. Review each usage and determine if `object` is appropriate
2. Replace `Any` with `object` for simple value containers
3. Add justification comments for remaining legitimate `Any` usage
4. Promote rule to `error` once all usages are reviewed

---

## DEV-013 — Single-letter parameter names in utility functions

**Violates:** ARCH-008 (`no-single-letter-params`)
**Current enforcement:** `warning` (should be `error`)
**Rule file:** `ARCH-008-keyword-only-arguments.rules.ts`

### Affected locations

14 occurrences:
- `src/trust/core/preprocessor/chunker/base_chunker.py:37,47,76`
- `src/trust/core/preprocessor/chunker/simple_chunker.py:47`
- `src/trust/core/store/presearch_processor/query_expansion/synonym_query_expansion.py:72`
- `src/trust/core/store/presearch_processor/query_expansion/toyota_words_query_expansion.py:92,109`
- `src/trust/core/utils/retry_util.py:20`
- `src/trust/core/utils/text_preprocess_utils.py:188,224`
- `src/trust/core/utils/wild_card.py:15`
- `src/trust/infrastructure/dataloader/spo_dataloader.py:377`
- `src/trust/infrastructure/external_clients/ms_clients/ms_graph_client.py:193`
- `src/trust/task_runner/__main__.py:142`

### Why enforcement is relaxed

These functions use single-letter parameters (often `s` for string, `n` for number) in utility functions where the parameter meaning is obvious from context. Renaming requires updating all call sites and may affect readability in simple helper functions.

### Migration path

1. Review each function and rename single-letter params to descriptive names
2. Prioritize public APIs and complex functions first
3. Allow single-letter params only in trivial helpers (with justification comment)
4. Promote rule to `error` once migration is complete

---

## DEV-014 — Optional parameters without keyword-only separator

**Violates:** ARCH-008 (`enforce-keyword-only-for-optional`)
**Current enforcement:** `warning` (should be `error`)
**Rule file:** `ARCH-008-keyword-only-arguments.rules.ts`

### Affected locations

24 occurrences across the codebase, including:
- `src/trust/application/chat/log_handler.py:89,104,108`
- `src/trust/application/validation/validation.py:48,138`
- `src/trust/core/agents/anti_corrosion_adviser/calc_logic.py:177`
- `src/trust/core/agents/anti_corrosion_adviser/tools.py:383,413`
- `src/trust/core/agents/facilitator_agent/problems.py:96`
- `src/trust/core/agents/root_agent/agent.py:30,65`
- `src/trust/core/preprocessor/text_extractor/document_intelligence_text_extractor.py:201,228,256`
- `src/trust/infrastructure/database/on_memory_database.py:55`
- `src/trust/infrastructure/database/opensearch_database.py:356`
- `src/trust/infrastructure/dataloader/local_dataloader.py:110,129`
- And others...

### Why enforcement is relaxed

Many existing functions with default parameters allow both positional and keyword arguments. Adding `*,` separator would break backward compatibility for internal callers that pass arguments positionally.

### Migration path

1. Audit affected functions to identify internal vs. public APIs
2. Add `*,` separator to public APIs first (breaking change requires coordination)
3. Add `*,` to internal helpers during refactoring (lower priority)
4. Promote rule to `error` for public APIs once migration is complete

---

## Deviation Tracking Summary

| ID      | ADR      | Rule                                              | Severity gap         | Status      |
| ------- | -------- | ------------------------------------------------- | -------------------- | ----------- |
| DEV-001 | ARCH-001 | `no-core-imports-infrastructure`                  | warning → error      | In progress |
| DEV-002 | ARCH-002 | `no-domain-model-in-application`                  | warning → error      | Deferred    |
| DEV-003 | ARCH-001 | (no rule yet)                                     | missing → error      | Pending     |
| DEV-004 | ARCH-003 | `no-base-mock-class-in-test-file`                 | warning → error      | Deferred    |
| DEV-005 | ARCH-011 | `no-patch-in-integration-tests`                   | warning → error      | In progress |
| DEV-006 | ARCH-004 | (config gap, not a rule)                          | compensating control | Deferred    |
| DEV-007 | ARCH-006 | `no-bare-any-in-signatures`                       | warning → error      | Deferred    |
| DEV-008 | ARCH-007 | `no-broad-exception-in-library`                   | warning → error      | In progress |
| DEV-009 | ARCH-007 | `require-raise-from`                              | warning → error      | Deferred    |
| DEV-010 | ARCH-008 | `recommend-keyword-only-params`                   | warning → error      | Deferred    |
| DEV-011 | ARCH-006 | `prefer-sequence-over-list-args`                  | warning → error      | Deferred    |
| DEV-012 | ARCH-006 | `use-object-not-any`                              | warning → error      | Deferred    |
| DEV-013 | ARCH-008 | `no-single-letter-params`                         | warning → error      | Deferred    |
| DEV-014 | ARCH-008 | `enforce-keyword-only-for-optional`               | warning → error      | Deferred    |
| DEV-015 | ARCH-011 | `no-monkeypatch-setattr-component-in-integration` | warning → error      | In progress |
