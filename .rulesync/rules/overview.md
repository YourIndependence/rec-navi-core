---
root: true
targets: ["*"]
description: "Project overview and development guidelines for TRUST backend"
globs: ["**/*"]
---

# Project Overview


## Repository Layout

```
src/recnavi/
  apis/             # FastAPI routers & Pydantic I/O schemas
  application/      # Use-case orchestration (chat, analysis, cms, dashboard, features, user, validation)
  core/             # Domain logic: agents, preprocessors, stores, types
  infrastructure/   # External clients, DB connections, session service
cli/                # Typer CLI (local dev server, OpenAPI gen, test runner)
tests/
  unittests/        # Fast unit tests, mirroring src/ layer structure
  integration/      # End-to-end tests against real or mocked services
```

## Related Documents

- [`docs/ENVIRONMENTS.md`](../../docs/ENVIRONMENTS.md) -- Runtime environments (LOCAL, LOCAL_CONTAINER, CI, dev, staging, prod), environment variables, and service endpoint matrix.

## Critical Rules

- **Respond in Japanese** -- ALL responses to the user MUST be in Japanese. Code, identifiers, commit messages, and `.rulesync/` files stay in English.
- **No bare `Any`** -- use proper type hints; `Any` is allowed only at external system boundaries with explicit justification.
- **Async-first** -- all I/O must be `async def`; never call `asyncio.run()` inside an async request path.

## Workflow

- **Plan first**: Present an implementation plan and wait for user approval before making significant changes.
- **Verify**: After implementation, run `uv run ruff format --check src/ tests/ && uv run ruff check src/ tests/ && uv run pytest tests/unittests/ -v`.
- **Testing boundary**: Unit tests must not require LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or repository secrets. Use fakes, `botocore.stub.Stubber`, `moto`, or `tests/mockups/`.
- **Real cloud tests**: Put real AWS/provider checks under `tests/integration/` with explicit guards. Mark real AWS tests `real_aws`; mark ECS dispatch tests both `real_aws` and `ecs`.
- **Multi-phase**: Significant tasks use `/build` (features) or `/fix` (bugs), which define phase gates and require explicit approval at each step.

## Language & Communication

- **Responses**: All responses and descriptions to the user MUST be in **Japanese**. This is VERY IMPORTANT!
- **Code comments**: Write in English, except variable/function names and commit messages (those stay in English).
- **Human-in-the-loop**: When asking for permission or clarification, use clear and polite Japanese.
