---
root: false
targets: ["*"]
description: "Tech stack and architecture patterns for TRUST backend"
globs: ["src/**", "tests/**", "cli/**"]
---

# Architecture

## Tech Stack

| Concern          | Technology                                                 |
| ---------------- | ---------------------------------------------------------- |
| HTTP server      | FastAPI + Uvicorn                                          |
| Agent framework  | Google ADK (`google-adk`, custom fork)                     |
| LLM backends     | LiteLLM, Azure OpenAI (`openai`), Google GenAI             |
| Data validation  | Pydantic v2                                                |
| ORM              | SQLAlchemy 2 (async)                                       |
| Databases        | PostgreSQL (asyncpg), MySQL (asyncmy), DynamoDB            |
| Vector search    | FAISS, OpenSearch                                          |
| Document parsing | Unstructured, PyMuPDF, python-docx, python-pptx            |
| Japanese NLP     | MeCab, neologdn                                            |
| Package manager  | uv                                                         |
| Lint / format    | Ruff                                                       |
| Testing          | pytest + pytest-asyncio; moto for AWS mocking              |
| Git hooks        | lefthook (gitleaks secret scan on commit/push)             |

## Clean Architecture Layers

```
apis/            <- HTTP boundary: FastAPI routers, Pydantic request/response schemas
application/     <- Use cases: orchestrate core + infra, no framework imports
core/            <- Domain logic: agents, preprocessors, stores, model_registry, types
infrastructure/  <- External I/O: DB sessions, boto3 clients, third-party APIs
```

### Deviations from Canonical Clean Architecture

- `core/` owns **abstract base classes** for databases and stores. Application code imports only from `core`, not `infrastructure`. Concrete implementations are injected at startup via registries.
- **Registry pattern** is the DI mechanism: `database_registry`, `store_registry`, `dataloader_registry`, `preprocessor_strategy_registry`, `chunker_registry`, `tool_registry`, `agent_registry`. Concrete implementations register themselves during startup; consumers retrieve them by key at runtime. Tool registration follows ARCH-013.
- Agent sub-module (`core/agents/`) holds all Google ADK `Agent` definitions. `core/agents/agent_registry.py` provides dynamic agent registration with DynamoDB persistence, allowing runtime agent CRUD via CMS API without code deployment.
- Tool sub-module (`core/tools/`) contains all tool implementations. Tool modules must follow [ARCH-013 Tool Registry and Initialization Pattern](../../docs/adrs/ARCH-013-tool-registry-pattern.md): each `*_tool.py` or `*_tools.py` module exposes a synchronous `initialize()` function and registers tools with `tool_registry` during startup. `core/tools/tool_registry.py` provides runtime tool lookup for dynamic agent construction.
- `core/agent_runner/` wraps `google.adk.runners.Runner` and is the only place an ADK `Runner` is instantiated.

## Media model serialization

Follow [ARCH-002](docs/adrs/ARCH-002-pydantic-first-type-system.md#media-models-and-temporary-urls).
Use one domain type when the only response difference is temporary media URLs.
Core models expose async `attach_presigned_url(*, storage)` returning a deep copy;
application use cases attach URLs after authorization and filtering. Exclude
storage references with `Field(exclude=True)`. Persist media models and aggregates
only through `to_storage_item()`, never ordinary `model_dump()`.
Distinct contracts such as privacy-limited `UserSummary` remain separate.

## Google ADK Agent Pattern

TRUST supports two agent creation patterns:

**Dynamic Agent Registry (Standard)**: Agents are stored as metadata in DynamoDB and instantiated at runtime via `AgentRegistry`. Agents can be created/updated/deleted at runtime via CMS API without code deployment. Use this pattern for all new agents unless they require complex initialization logic.

**Static Agent Directory (Legacy)**: Each agent lives in `core/agents/<name>/` with `agent.py` (factory function), `prompts.py` (instruction/description), and optionally `tools.py`. Use only for agents requiring complex initialization or compile-time validation.

Tools are plain callables passed to `Agent(tools=[...])`. Use `async def` for any tool that performs I/O. All tools are registered in `tool_registry` for runtime lookup.

## Async Convention

All I/O -- database, HTTP, external APIs -- must be async. FastAPI endpoints are `async def`. Never call `asyncio.run()` inside an async context.

## Testing Conventions

- Unit tests mirror implementation module paths: `src/recnavi/apis/staff/staff_router.py` maps to `tests/unittests/apis/staff/test_staff_router.py`. Keep related test files in the same mirrored directory. See [ARCH-011](../../docs/adrs/ARCH-011-test-implementation.md).
- Unit test paths exclude the `src/recnavi/` prefix and add `test_` to the implementation module filename.
- `__init__.py` files, declarative-only modules under `apis/schemas/` or `core/types/`, `config/variables.py`, `exceptions/exceptions.py`, modules named `base_*.py`, and tests of shared doubles under `tests/unittests/mockups/` are exempt from mirrored test requirements.
- Run a single file: `uv run pytest tests/unittests/path/to/test_file.py -v`
- Run all non-LibreOffice unit tests: `uv run pytest tests/unittests/ -n auto --dist loadscope -m "not libreoffice" -v`
- Unit tests must not require LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or repository secrets
- AWS services in unit tests: prefer lightweight fakes or `botocore.stub.Stubber`; use `moto` for service behavior such as DynamoDB
- Integration tests: default command includes all tests; LocalStack-backed profiles skip `real_aws` automatically from `tests/integration/conftest.py`
- ECS integration tests: mark with both `real_aws` and `ecs`; they are skipped only when `AWS_ENDPOINT_URL` points to LocalStack
- Async tests: decorate with `@pytest.mark.asyncio`
- Format + lint before committing: `uv run ruff format src/ tests/ && uv run ruff check src/ tests/`
