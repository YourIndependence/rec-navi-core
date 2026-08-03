---
id: ARCH-013
title: Tool Registry and Initialization Pattern
domain: architecture
status: accepted
date: 2026-06-16
rules: true
files:
  - 'src/trust/core/tools/**/*_tool.py'
  - 'src/trust/core/tools/**/*_tools.py'
  - 'src/trust/core/agents/*/tools.py'
---

## Context

The dynamic agent implementation introduced a consistent tool initialization pattern.

Current pattern:

- Shared tool modules live under `src/trust/core/tools/`.
- Shared tool modules are named `*_tool.py` or `*_tools.py`.
- Agent-specific tool modules may live under `src/trust/core/agents/*/tools.py`.
- Shared tool modules expose an `initialize()` function.
- Agent-specific tool modules expose an `initialize(prefix: str)` function.
- The `initialize()` function registers one or more tools with `tool_registry`.
- `tool_registry.initialize()` imports tool modules and calls their `initialize()` functions at startup.
- Agent-specific tool modules are initialized with an agent-specific prefix so registered tool names do not collide across agents.
- This follows the same registry initialization approach used by the dataloader registry.

Without a documented rule, new tool modules may skip registration, register tools at import time, omit agent prefixes, or use inconsistent factory and ToolSet naming.

## Decision

**All tools must be registered through the Tool Registry initialization lifecycle.**

Tool modules must not rely on import side effects. Registration must happen inside an explicit `initialize()` function.

Shared tool modules use:

```python
def initialize() -> None:
    ...
```

Agent-specific tool modules use:

```python
def initialize(prefix: str) -> None:
    ...
```

`tool_registry.register_tool(...)` accepts either a plain callable tool or a `ToolSet`. Both must be registered through the same initialization lifecycle.

## Scope

This ADR applies to shared tool implementation modules:

```txt
src/trust/core/tools/**/*_tool.py
src/trust/core/tools/**/*_tools.py
```

This ADR also applies to agent-specific tool modules:

```txt
src/trust/core/agents/*/tools.py
```

Agent-specific tool modules are included because `tool_registry._scan_agent_tools()` discovers them and initializes them with an agent-specific prefix.

It does not apply to:

```txt
src/trust/core/tools/registry.py
src/trust/core/tools/tool_registry.py
src/trust/core/tools/**/util/**/*.py
src/trust/core/tools/**/__init__.py
```

## Rules

### 1. Shared tool modules must define initialize()

Every shared tool module under `src/trust/core/tools/` must expose:

```python
def initialize() -> None:
    ...
```

The `initialize()` function is the only supported entry point for startup registration.

Bad:

```python
async def toyota_jp_websearch_tool(...):
    ...

tool_registry.register_tool(toyota_jp_websearch_tool)
```

Good:

```python
async def toyota_jp_websearch_tool(...):
    ...


def initialize() -> None:
    tool_registry.register_tool(toyota_jp_websearch_tool)
```

### 2. Agent-specific tool modules must define initialize(prefix: str)

Every agent-specific tool module under `src/trust/core/agents/*/tools.py` must expose:

```python
def initialize(prefix: str) -> None:
    ...
```

Registered tools must pass the prefix through to `tool_registry.register_tool(...)`.

Good:

```python
def initialize(prefix: str) -> None:
    """Register agent-specific tools with ToolRegistry."""
    tool_registry.register_tool(fetch_parameter_criteria, prefix=prefix)
    tool_registry.register_tool(evaluate_bath_parameters, prefix=prefix)
```

Bad:

```python
def initialize() -> None:
    tool_registry.register_tool(fetch_parameter_criteria)
```

Bad:

```python
def initialize(prefix: str) -> None:
    tool_registry.register_tool(fetch_parameter_criteria)
```

Without `prefix=prefix`, tools from different agents may collide or be looked up under the wrong registry name.

### 3. Tool registration must happen inside initialize()

Tool registration must not happen at module import time.

Bad:

```python
tool_registry.register_tool(translate_tool)
```

Good:

```python
def initialize() -> None:
    tool_registry.register_tool(translate_tool)
```

For agent-specific tools:

```python
def initialize(prefix: str) -> None:
    tool_registry.register_tool(translate_tool, prefix=prefix)
```

This prevents hidden import side effects and keeps startup behavior centralized.

### 4. initialize() must be synchronous

`initialize()` must be a normal synchronous function.

Bad:

```python
async def initialize() -> None:
    tool_registry.register_tool(search_web_tool)
```

Good:

```python
def initialize() -> None:
    tool_registry.register_tool(search_web_tool)
```

Good for agent-specific tools:

```python
def initialize(prefix: str) -> None:
    tool_registry.register_tool(search_web_tool, prefix=prefix)
```

Tool registration should not perform I/O. Any I/O required by a tool must happen when the tool executes, not when it is registered.

### 5. Tool factories must use the *_tool_factory naming convention

Factory functions that create tools must be named:

```txt
*_tool_factory
```

Good:

```python
def retrieve_docs_tool_factory(store_names: list[str]):
    ...
```

Bad:

```python
def retrieve_docs_factory(store_names: list[str]):
    ...
```

The suffix makes it clear that the function returns a tool callable, not a plain helper.

### 6. Tool modules may register multiple tools

A `*_tools.py` module may register multiple related tools.

Good:

```python
def initialize() -> None:
    tool_registry.register_tool(load_document_tool)
    tool_registry.register_tool(summarize_document_tool)
```

Good for agent-specific tools:

```python
def initialize(prefix: str) -> None:
    tool_registry.register_tool(fetch_parameter_criteria, prefix=prefix)
    tool_registry.register_tool(evaluate_bath_parameters, prefix=prefix)
    tool_registry.register_tool(calculate_fa_timer, prefix=prefix)
    tool_registry.register_tool(calculate_a_component_dosage, prefix=prefix)
```

Use `*_tools.py` when the module owns a closely related group of tools.

Use `*_tool.py` when the module owns one primary tool.

### 7. ToolSet registration is supported

`tool_registry.register_tool(...)` accepts either a plain callable tool or a `ToolSet`.

ToolSet instances must also be registered through `initialize()`.

Good:

```python
def initialize() -> None:
    """Register tools with ToolRegistry."""
    document_handler_toolset = DocumentHandlerToolSet(...)
    tool_registry.register_tool(document_handler_toolset)
```

Good for agent-specific ToolSets:

```python
def initialize(prefix: str) -> None:
    """Register agent-specific tools with ToolRegistry."""
    problems_handler_toolset = ProblemsHandlerToolSet(...)
    tool_registry.register_tool(problems_handler_toolset, prefix=prefix)
```

ToolSet instances must be assigned to variables whose names end with `_toolset`.

Good:

```python
document_handler_toolset = DocumentHandlerToolSet(...)
problems_handler_toolset = ProblemsHandlerToolSet(...)
```

Bad:

```python
document_handler_tools = DocumentHandlerToolSet(...)
problems_handler = ProblemsHandlerToolSet(...)
```

Inline ToolSet registration should be avoided because it is harder to audit.

Bad:

```python
def initialize() -> None:
    tool_registry.register_tool(DocumentHandlerToolSet(...))
```

Good:

```python
def initialize() -> None:
    document_handler_toolset = DocumentHandlerToolSet(...)
    tool_registry.register_tool(document_handler_toolset)
```

### 8. Use registry lookup for dynamic agent construction

Dynamic agent construction must use the Tool Registry as the source of truth.

Good:

```python
tool = tool_registry.get_tool(tool_name)
```

Avoid direct imports of specific tool functions in dynamic agent construction code unless the code is inside the tool registry initialization layer.

Bad in dynamic agent construction code:

```python
from trust.core.tools.retrieve_docs_tool import retrieve_docs_tool_factory
```

Good in dynamic agent construction code:

```python
tool = tool_registry.get_tool(tool_name)
```

This rule applies to code that dynamically resolves tools for an agent at runtime.

It does not prohibit legitimate domain helper modules from importing tool factories when the helper is not dynamically constructing an agent.

Allowed in a domain helper such as `criteria_fetcher.py`:

```python
from trust.core.tools.retrieve_docs_tool import retrieve_docs_tool_factory
```

If a direct import is intentionally needed in a file that otherwise matches the dynamic-agent-construction rule, add a local suppression comment and document why it is safe:

```python
# archgate-disable-next-line no-direct-tool-import-in-agent-construction
from trust.core.tools.retrieve_docs_tool import retrieve_docs_tool_factory
```

## Shared tool module template

Use this template for new shared tools:

```python
from google.adk.tools.tool_context import ToolContext

from trust.core.tools.registry import tool_registry


async def example_tool(
    search_query: str,
    tool_context: ToolContext,
) -> dict:
    """Short description of what the tool does.

    Args:
        search_query: Search query.
        tool_context: Runtime tool context.

    Returns:
        Tool response dictionary.
    """
    ...


def initialize() -> None:
    """Register tools with ToolRegistry."""
    tool_registry.register_tool(example_tool)
```

## Agent-specific tool module template

Use this template for new agent-specific tools:

```python
from google.adk.tools.tool_context import ToolContext

from trust.core.tools.registry import tool_registry


async def example_agent_tool(
    search_query: str,
    tool_context: ToolContext,
) -> dict:
    """Short description of what the agent-specific tool does.

    Args:
        search_query: Search query.
        tool_context: Runtime tool context.

    Returns:
        Tool response dictionary.
    """
    ...


def initialize(prefix: str) -> None:
    """Register agent-specific tools with ToolRegistry."""
    tool_registry.register_tool(example_agent_tool, prefix=prefix)
```

## Factory tool template

Use this template when a tool requires construction-time configuration:

```python
from google.adk.tools.tool_context import ToolContext


def retrieve_docs_tool_factory(store_names: list[str]):
    """Create a retrieve-docs tool bound to specific stores."""

    async def retrieve_docs_tool(
        search_query: str,
        tool_context: ToolContext,
        conversation_summary: list[dict] | None = None,
    ):
        ...

    return retrieve_docs_tool
```

If the factory result itself is registered as a normal tool, registration still happens inside `initialize()`.

## ToolSet template

Use this template when registering a `ToolSet`:

```python
from trust.core.tools.registry import tool_registry


def initialize() -> None:
    """Register ToolSet with ToolRegistry."""
    document_handler_toolset = DocumentHandlerToolSet(...)
    tool_registry.register_tool(document_handler_toolset)
```

For agent-specific ToolSets:

```python
from trust.core.tools.registry import tool_registry


def initialize(prefix: str) -> None:
    """Register agent-specific ToolSet with ToolRegistry."""
    problems_handler_toolset = ProblemsHandlerToolSet(...)
    tool_registry.register_tool(problems_handler_toolset, prefix=prefix)
```

## Relationship to dataloader registry

This pattern intentionally mirrors the dataloader registry pattern:

```txt
module initialize()
-> registry.register(...)
-> registry.initialize() calls module initialize() at startup
```

The same lifecycle should be used for registries that support pluggable implementations.

## Compliance

Do:

- Put shared tool modules under `src/trust/core/tools/`.
- Name shared tool modules `*_tool.py` or `*_tools.py`.
- Put agent-specific tool modules under `src/trust/core/agents/*/tools.py`.
- Define `def initialize() -> None` for shared tool modules.
- Define `def initialize(prefix: str) -> None` for agent-specific tool modules.
- Register tools only inside `initialize()`.
- Use `tool_registry.register_tool(...)`.
- Pass `prefix=prefix` when registering tools from agent-specific tool modules.
- Use `*_tool_factory` for factory functions that create tools.
- Use `_toolset` suffix for ToolSet variables.
- Keep registration free of I/O and side effects.
- Use `tool_registry.get_tool(tool_name)` in dynamic agent construction code.

Do not:

- Register tools at module import time.
- Define `async def initialize()`.
- Omit `prefix=prefix` in agent-specific tool registration.
- Use inconsistent factory names such as `*_factory` for tool factories.
- Use ToolSet variable names that do not end with `_toolset`.
- Register ToolSets inline without assigning them to a named `_toolset` variable.
- Hide registration in helper functions that are not called by `initialize()`.
- Directly import concrete tool functions from dynamic agent construction code.

## Examples

Current accepted shared tool pattern:

```python
async def toyota_jp_websearch_tool(
    search_query: str,
    tool_context: ToolContext,
    conversation_summary: list[dict] | None = None,
) -> dict:
    """Search information about the Toyota official website."""
    retrieve_tool = retrieve_docs_tool_factory(["toyota_official_web_site"])

    async for ans in retrieve_tool(
        search_query=search_query,
        conversation_summary=conversation_summary,
        tool_context=tool_context,
    ):
        yield ans


def initialize() -> None:
    """Register tools with ToolRegistry."""
    tool_registry.register_tool(toyota_jp_websearch_tool)
```

Current accepted agent-specific tool pattern:

```python
def initialize(prefix: str) -> None:
    """Register anti-corrosion adviser tools with ToolRegistry."""
    tool_registry.register_tool(fetch_parameter_criteria, prefix=prefix)
    tool_registry.register_tool(evaluate_bath_parameters, prefix=prefix)
    tool_registry.register_tool(calculate_fa_timer, prefix=prefix)
    tool_registry.register_tool(calculate_a_component_dosage, prefix=prefix)
```

Current accepted ToolSet pattern:

```python
def initialize() -> None:
    """Register document handler tools with ToolRegistry."""
    document_handler_toolset = DocumentHandlerToolSet(...)
    tool_registry.register_tool(document_handler_toolset)
```

## Consequences

Positive:

- Tool startup behavior is explicit and predictable.
- Dynamic agents can rely on the registry as the source of truth.
- Tool registration follows the same lifecycle as other registries.
- Import side effects are avoided.
- Agent-specific tools can be namespaced with prefixes to avoid collisions.
- ToolSet registration is documented and auditable.

Negative:

- Every new tool module needs a small amount of registration boilerplate.
- Existing tool modules may need migration if they register tools outside `initialize()`.
- Existing `initialize()` functions may need explicit `-> None` return annotations if they do not already match this ADR.

## References

- [ARCH-001](./ARCH-001-clean-architecture.md) - Clean Architecture and Registry Pattern
- [ARCH-010](./ARCH-010-google-adk-patterns.md) - Google ADK Patterns
- `src/trust/core/tools/registry.py`
- `src/trust/core/tools/tool_registry.py`
- `src/trust/core/agents/*/tools.py`
- `src/trust/infrastructure/dataloader/`
