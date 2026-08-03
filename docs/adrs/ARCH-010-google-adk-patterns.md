---
id: ARCH-010
title: Google ADK Agent Patterns and Best Practices
domain: architecture
status: active
date: 2026-05-09
rules: true
files:
  - 'src/trust/core/agents/**/*.py'
---

## Context

TRUST is built on the [Google Agent Development Kit (ADK)](https://adk.dev), an open-source framework for building multi-agent AI applications. Without explicit guidelines, ADK-based code can diverge from established patterns, leading to inconsistent agent structures, inefficient token usage, poor error handling, and difficult-to-test systems.

This ADR codifies the Google ADK agent sub-pattern adopted by TRUST and consolidates best practices from official ADK documentation, community patterns, and lessons learned from production deployments.

## Decision

### Agent Creation Patterns

TRUST supports two agent creation patterns:

#### Pattern 1: Dynamic Agent Registry (Standard, Preferred)

Agents are stored as metadata in DynamoDB and instantiated dynamically at runtime via `AgentRegistry`:

```python
# core/agents/agent_registry.py
agent = agent_registry.get_agent("my_agent")  # Loads from DynamoDB
```

**Advantages:**
- Agents can be created/updated/deleted at runtime via CMS API
- No code deployment required for agent configuration changes
- Centralized agent metadata management
- Supports runtime permission control

**When to use:** Default for all new agents unless they require complex initialization logic or static compilation.

#### Pattern 2: Static Agent Directory (Legacy)

Each `core/agents/<name>/` directory contains:

```
agent.py    # get_<name>_agent() → google.adk.agents.Agent
prompts.py  # return_instruction(), return_description()
tools.py    # Tool callables — async def for any I/O (omit if only using shared tools/)
```

**Exempt from this pattern:**
- `core/agents/util/` — shared utilities
- `core/agents/agent_registry.py` — dynamic agent registry

**When to use:** Only for agents requiring complex initialization, compile-time validation, or integration with legacy systems.

### Agent Factory Function

Every agent must expose a **factory function** in `agent.py`. Two naming patterns are accepted:

**Pattern 1 (Compact):**
```python
def get_<name>(
    model: str | BaseLlm | None = None,
    **kwargs,
) -> Agent:
    """Create and return the <name> agent instance."""
    return Agent(
        model=resolve_model(model),
        name="<AgentName>",
        instruction=return_instruction(),
        description=return_description(),
        tools=get_tools(),  # if tools.py exists
    )
```

**Pattern 2 (Explicit, preferred):**
```python
def get_<name>_agent(
    model: str | BaseLlm | None = None,
    **kwargs,
) -> Agent:
    """Create and return the <name> agent instance."""
    return Agent(
        model=resolve_model(model),
        name="<AgentName>",
        instruction=return_instruction(),
        description=return_description(),
        tools=get_tools(),  # if tools.py exists
    )
```

Static agent factories are looked up through the dynamic `AgentRegistry`; the legacy static `registry.py` has been removed.

### Prompt Functions

`prompts.py` must define instruction and description functions. Two naming patterns are accepted:

**Pattern 1 (Standard):**
```python
def return_instruction() -> str:
    """Return the agent's system instruction (behavior guide)."""
    ...

def return_description() -> str:
    """Return a concise agent description for delegation routing."""
    ...
```

**Pattern 2 (Suffixed):**
```python
def return_instruction_<agent_name>() -> str:
    """Return the agent's system instruction (behavior guide)."""
    ...

def return_description_<agent_name>() -> str:
    """Return a concise agent description for delegation routing."""
    ...
```

**Rationale:**
- `instruction` defines the agent's behavior and capabilities
- `description` helps parent agents decide when to delegate to this agent
- Separating prompts from `agent.py` improves testability and version control diffs
- Both naming patterns are supported for backward compatibility

### Tool Development

**Rule: All I/O operations in `tools.py` must use `async def`**

ADK agents execute within an async request context (FastAPI). Blocking I/O in tools will degrade performance and may cause timeouts.

**Good:**
```python
async def fetch_document(doc_id: str) -> str:
    """Fetch document from external API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/docs/{doc_id}")
        return response.text
```

**Bad:**
```python
def fetch_document(doc_id: str) -> str:
    """❌ Blocking I/O in sync function."""
    response = requests.get(f"/api/docs/{doc_id}")
    return response.text
```

**Exception:** Pure computation tools (e.g., `calculate_total(a: int, b: int) -> int`) can remain synchronous.

## Best Practices

### 1. Agent Type Selection

Google ADK provides three foundational agent types ([source](https://adk.dev/agents/)):

| Agent Type       | Use Case                                    | Key Characteristics                     |
| ---------------- | ------------------------------------------- | --------------------------------------- |
| `LlmAgent`       | Reasoning, dynamic decision-making          | Flexible, adaptive, non-deterministic   |
| Workflow Agents  | Orchestration (sequence, parallel, loop)    | Deterministic, predictable control flow |
| Custom Agents    | Specialized logic beyond standard abstractions | Full `BaseAgent` interface control      |

**Guideline:** Choose `LlmAgent` for adaptive tasks requiring natural language understanding. Use workflow agents (e.g., `SequentialAgent`) for predictable pipelines. Reserve custom agents for domain-specific logic.

### 2. Multi-Agent Composition

Complex workflows benefit from combining agent types ([source](https://cloud.google.com/blog/topics/developers-practitioners/building-collaborative-ai-a-developers-guide-to-multi-agent-systems-with-adk)):

- Deploy `LlmAgent` for intelligent task execution
- Use workflow agents for orchestrating overall process flows
- Implement custom agents for specialized integrations

**Example:** A document analysis pipeline might use:
- `SequentialAgent` to orchestrate the workflow
- `LlmAgent` for content extraction
- Custom agent for proprietary data validation

### 3. Tool Design Principles

- **Precision over generality:** Create task-specific tools when pre-built integrations don't match requirements ([source](https://developers.googleblog.com/developers-guide-to-building-adk-agents-with-skills/))
- **Observable execution:** Log tool invocations for debugging and monitoring
- **Error handling:** Wrap I/O in try-except blocks and return meaningful error messages to the agent

### 4. Skill Implementation Patterns

ADK supports tiered skill complexity ([source](https://developers.googleblog.com/developers-guide-to-building-adk-agents-with-skills/)):

| Pattern          | Use Case                                | Example                          |
| ---------------- | --------------------------------------- | -------------------------------- |
| Inline skills    | Small, stable rules (< 10 lines)        | Hardcoded checklist instructions |
| File-based skills | Reusable knowledge across agents       | SEO optimization guidelines      |
| External skills  | Community repositories                  | agentskills.io catalog           |
| Skill factory    | Meta-skills generating new capabilities | Agent-generated SKILL.md         |

**Guideline:** "Start with inline, graduate to files. Don't over-engineer."

### 5. Session & Memory Management

- **Session state** holds short-term conversation context (`Session`, `Events`)
- **Memory** provides cross-session recall (long-term knowledge)
- **Artifacts** manage binary data (images, PDFs) within sessions

**Guideline:** Use session state for conversation history. Use memory for user preferences or domain knowledge that persists across sessions. Use artifacts for file attachments.

## Common Pitfalls

### 1. Tool Failure Crashes Entire Workflow

**Problem:** Tool failures in multi-agent systems can crash the entire workflow ([source](https://github.com/google/adk-python/discussions/795))

**Mitigation:**
- Wrap tool logic in try-except blocks
- Return error messages as tool results rather than raising exceptions
- Test tool failure scenarios in unit tests

### 2. Schema Validation Failures

**Problem:** ADK does not auto-retry when `output_schema` validation fails ([source](https://github.com/google/adk-python/discussions/3759))

**Mitigation:**
- Wrap agent invocation in `try...except pydantic.ValidationError`
- Use a "Generator-Critic" pattern: one agent generates, a second validates
- Provide explicit schema examples in the instruction

### 3. Token Inefficiency

**Problem:** Concatenating all instructions into monolithic system prompts wastes 90% of tokens ([source](https://developers.googleblog.com/developers-guide-to-building-adk-agents-with-skills/))

**Mitigation:**
- Use tiered knowledge loading (metadata → instructions → resources)
- Keep `return_instruction()` concise; load reference docs on-demand
- Leverage ADK's progressive disclosure mechanisms

### 4. Blocking I/O in Async Context

**Problem:** Calling `asyncio.run()` or using blocking I/O inside an async request path causes deadlocks or performance degradation

**Mitigation:**
- Use `async def` for all I/O operations
- Never call `asyncio.run()` inside a FastAPI endpoint or ADK tool
- Prefer `httpx.AsyncClient` over `requests`, `asyncpg` over `psycopg2`

## Consequences

**Positive:**
- Consistent agent structure makes onboarding and code review faster
- Separating prompts from logic improves testability and version control
- Async I/O ensures FastAPI performance at scale
- Documented pitfalls reduce debugging time for common ADK issues

**Negative:**
- Requires boilerplate for every agent (`agent.py`, `prompts.py`, `tools.py`)
- Developers must understand async/await for tool development
- Multi-agent patterns increase architectural complexity

## Compliance

**Do:**

- **Prefer dynamic agent registry** for new agents (Pattern 1) — store metadata in DynamoDB
- For static agents (Pattern 2): Include `agent.py` and `prompts.py` in every new `core/agents/<name>/` directory
- For static agents (Pattern 2): Expose a `get_<name>_agent()` factory function in `agent.py`
- For static agents (Pattern 2): Define `return_instruction()` and `return_description()` in `prompts.py`
- Use `async def` for all tools that perform I/O (HTTP, DB, file system)
- Write unit tests for agent tools with mocked I/O

**Don't:**

- Create agents outside of `core/agents/` (except when using AgentRegistry for dynamic agents)
- Use blocking I/O (`requests`, `psycopg2`, `open()` for large files) in tools
- Call `asyncio.run()` inside an async context (FastAPI endpoint, ADK tool)
- Omit error handling in tools that interact with external systems
- Hardcode model names — use `resolve_model()` or accept `BaseLlm`
- **For static agents only:** Skip `prompts.py` or inline prompts directly in `agent.py`
- **For dynamic agents:** Inline prompts from DynamoDB metadata are allowed and expected

## References

- [Google ADK Official Documentation](https://adk.dev)
- [ADK Agents Guide](https://adk.dev/agents/)
- [Building Multi-Agent Systems with ADK (Google Cloud Blog)](https://cloud.google.com/blog/topics/developers-practitioners/building-collaborative-ai-a-developers-guide-to-multi-agent-systems-with-adk)
- [Developer's Guide to Building ADK Agents with Skills](https://developers.googleblog.com/developers-guide-to-building-adk-agents-with-skills/)
- [ADK Python GitHub Discussions](https://github.com/google/adk-python/discussions)
- [ARCH-001: Clean Architecture](./ARCH-001-clean-architecture.md)
- [.rulesync/rules/architecture.md](../../.rulesync/rules/architecture.md)
