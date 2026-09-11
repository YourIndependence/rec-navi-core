---
id: ARCH-012
title: Database Dependency Injection via FastAPI Application State
domain: backend
status: active
date: 2026-09-11
rules: false
files:
  - 'src/recnavi/main.py'
  - 'src/recnavi/core/database/**/*.py'
  - 'src/recnavi/infrastructure/database/**/*.py'
  - 'src/recnavi/apis/**/*.py'
---

## Context

The application needs a consistent pattern for managing database connections and providing them to API endpoints and use cases. Database instances must be:

1. **Initialized once** during application startup
2. **Shared across requests** without creating new connections per request
3. **Accessible** to all layers (API, Application, Core)
4. **Testable** with lightweight fakes or mocks

Previously, there was no standardized database abstraction or dependency injection mechanism.

## Decision

Use **FastAPI application state** (`app.state.database`) as a dictionary holding database instances, initialized in the `lifespan` context manager.

**Structure:**
```python
# main.py
@asynccontextmanager
async def lifespan(_app: FastAPI):
    _app.state.database = {
        USERS_TABLE_NAME: UserDatabase(table_name=USERS_TABLE_NAME),
        # Future tables can be added here
    }
    yield

# root_router.py
@root_router.get("/getMe")
async def get_me(request: Request) -> GetMeResponse:
    user_db = request.app.state.database[USERS_TABLE_NAME]
    user = await get_me_use_case(sub=sub, user_db=user_db)
    return GetMeResponse(user=user, group_id=user.group_id)
```

**Abstraction Layers:**
- **Core**: `BaseDatabase` (ABC) defines common operations (`get_item`, `put_item`, `query`, `delete_item`)
- **Infrastructure**: Concrete implementations like `UserDatabase` (DynamoDB)
- **Application**: Use cases receive `BaseDatabase` instances

## Rationale

**Why FastAPI app.state?**
- **Single initialization**: Database instances are created once in `lifespan`, not per-request
- **Global accessibility**: All routes can access via `request.app.state`
- **No hidden globals**: Explicit access through request object
- **Framework-native**: Uses FastAPI's built-in pattern

**Why dictionary structure?**
- **Multiple tables**: Easily support multiple table names (e.g., `USERS_TABLE_NAME`, `PROJECTS_TABLE_NAME`)
- **Environment flexibility**: Table names can vary by environment (dev, staging, prod)
- **Clear semantics**: `app.state.database[TABLE_NAME]` is self-documenting

**Why BaseDatabase abstraction?**
- **Testability**: Unit tests use lightweight fakes without real DynamoDB
- **Reusability**: All DynamoDB tables can share common interface
- **Decoupling**: Application and Core layers don't depend on specific database technology

## Consequences

**Positive:**
- ✅ **Testability**: Easy to inject fake databases in tests
- ✅ **Performance**: No connection overhead per request
- ✅ **Flexibility**: Adding new tables is straightforward
- ✅ **Type safety**: BaseDatabase provides contract for all implementations
- ✅ **Clean Architecture**: Core layer independent of infrastructure

**Negative:**
- ❌ **Manual registration**: Each new table must be added to `lifespan` dictionary
- ❌ **Runtime lookup**: `app.state.database[TABLE_NAME]` can fail at runtime if key missing (but caught immediately on startup)

## Alternatives Considered

### Alternative 1: FastAPI Depends with factory functions
```python
def get_user_database(request: Request) -> BaseDatabase:
    return request.app.state.database[USERS_TABLE_NAME]

@root_router.get("/getMe")
async def get_me(
    request: Request,
    user_db: BaseDatabase = Depends(get_user_database)
):
    ...
```

**Positive:**
- Cleaner endpoint signatures
- Type hints in function parameters

**Negative:**
- Additional boilerplate (dependency factory functions)
- More indirection for simple state access
- **Rejected** because direct `request.app.state` access is simpler for this use case

### Alternative 2: Global singletons
```python
user_database = UserDatabase(table_name=USERS_TABLE_NAME)

@root_router.get("/getMe")
async def get_me(request: Request):
    user = await get_me_use_case(sub=sub, user_db=user_database)
```

**Positive:**
- Minimal code

**Negative:**
- Hidden dependencies (not visible in function signature)
- Harder to test (must mock global state)
- Initialization order issues
- **Rejected** because it violates dependency injection principles

### Alternative 3: Per-request database creation
```python
@root_router.get("/getMe")
async def get_me(request: Request):
    user_db = UserDatabase(table_name=USERS_TABLE_NAME)  # Created every request
    user = await get_me_use_case(sub=sub, user_db=user_db)
```

**Positive:**
- Simple to understand

**Negative:**
- Performance overhead (connection pool creation per request)
- Wasteful resource usage
- **Rejected** due to performance concerns

## Compliance

**Do:**
- Initialize all database instances in `main.py` `lifespan` function
- Add new tables to `app.state.database` dictionary with environment-based table names
- Access databases via `request.app.state.database[TABLE_NAME]` in API endpoints
- Pass `BaseDatabase` instances to Application layer use cases
- Use fakes or mocks implementing `BaseDatabase` in unit tests

**Don't:**
- Create database instances inside endpoint functions
- Use global database singletons
- Skip `BaseDatabase` abstraction and use concrete classes directly in Application layer
- Hardcode table names (always use environment variables)

## References

- Issue #3: feat: getMe returns the signed-in user
- FastAPI documentation: https://fastapi.tiangolo.com/advanced/events/#lifespan
- Clean Architecture by Robert C. Martin
