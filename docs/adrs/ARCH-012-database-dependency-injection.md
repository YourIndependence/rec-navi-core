---
id: ARCH-012
title: Database Dependency Injection via FastAPI Application State
domain: backend
status: active
date: 2026-09-11
rules: true
files:
  - 'src/recnavi/main.py'
  - 'src/recnavi/core/database/**/*.py'
  - 'src/recnavi/infrastructure/database/**/*.py'
  - 'src/recnavi/infrastructure/s3/**/*.py'
  - 'src/recnavi/apis/**/*.py'
  - 'tests/unittests/**/*.py'
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
        USERS_TABLE_NAME: DynamoDb(table_name=USERS_TABLE_NAME),
        # Future tables can be added here
    }
    yield

# dependencies/auth.py
async def verify_user(request: Request) -> User:
    """Verify JWT token and return authenticated user from database."""
    payload = await decode_token(request)
    sub = str(payload["sub"])
    user_db = request.app.state.database[USERS_TABLE_NAME]
    user = await get_user_by_id(user_id=sub, user_db=user_db)
    return user

# root_router.py
@root_router.get("/getMe")
async def get_me(user: User = Depends(verify_user)) -> GetMeResponse:
    return GetMeResponse(user=user, group_id=user.group_id)
```

**Abstraction Layers:**
- **Core**: `BaseDatabase` (ABC) defines common operations (`get_item`, `put_item`, `query`, `delete_item`)
- **Infrastructure**: Concrete implementation `DynamoDb` with automatic Decimal conversion for all DynamoDB tables
- **API**: Endpoints and dependencies receive `BaseDatabase` instances from `request.app.state.database`

### AWS Adapter Unit Tests

Application and core unit tests use the shared `BaseDatabase` and
`BaseObjectStorage` mock implementations. Infrastructure unit tests exercise
the concrete `DynamoDb` and `S3Client` adapters against Moto instead.

Every concrete AWS adapter constructed in a unit test must receive the
`mock_aws_session` fixture through its public `session` attribute before it is
used, returned, or yielded. The fixture runs an aioboto3 session under
`mock_aws`, with dummy credentials and the shared async transport adapter.

```python
@pytest.fixture
def storage(mock_aws_session):
    storage = S3Client(bucket_name="it-media")
    storage.session = mock_aws_session
    return storage
```

The `no-database-in-test-without-mock` and `no-s3-in-test-without-mock`
rules both have `error` severity. They inspect Python AST nodes and require
the constructing function or fixture to accept `mock_aws_session` and assign
it to that same instance in the same statement block before use. Comments,
string literals, assignments in another function or conditional branch, and
injection into a different instance do not satisfy the rules. Direct
constructor calls without an assigned local variable are rejected.

These checks enforce the explicit fixture injection pattern, not arbitrary
Python data flow or the behavior of custom session factories.

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

**Why DynamoDb with Decimal conversion?**
- **DynamoDB limitation**: DynamoDB doesn't support native int/float, requires Decimal
- **Clean separation**: Conversion logic isolated in Infrastructure layer
- **Application simplicity**: Application and Core layers work with native Python types (int/float)
- **Automatic conversion**: `put_item` converts int/float → Decimal, `get_item`/`query` convert Decimal → int/float
- **Transparency**: Application code doesn't need to know about Decimal handling

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

### Alternative 1: Dependency factories for each table
```python
def get_user_database(request: Request) -> BaseDatabase:
    return request.app.state.database[USERS_TABLE_NAME]

@root_router.get("/getMe")
async def get_me(
    request: Request,
    user_db: BaseDatabase = Depends(get_user_database)
):
    user = await get_user_by_id(user_id=sub, user_db=user_db)
    ...
```

**Positive:**
- Explicit database dependency in endpoint signatures

**Negative:**
- Additional boilerplate (dependency factory per table)
- More indirection when database access is already wrapped in domain-specific dependencies (like `verify_user`)
- **Rejected** because domain-specific dependencies (e.g., `verify_user`) provide better abstraction than table-specific factories

### Alternative 2: Global singletons
```python
user_database = DynamoDb(table_name=USERS_TABLE_NAME)

@root_router.get("/getMe")
async def get_me(request: Request):
    user = await get_user_by_id(user_id=sub, user_db=user_database)
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
    user_db = DynamoDb(table_name=USERS_TABLE_NAME)  # Created every request
    user = await get_user_by_id(user_id=sub, user_db=user_db)
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
- Access databases via `request.app.state.database[TABLE_NAME]` in API dependencies (e.g., `verify_user`)
- Pass `BaseDatabase` instances to Core layer functions
- Use fakes or mocks implementing `BaseDatabase` in unit tests
- In infrastructure unit tests, inject `mock_aws_session` into every
  `DynamoDb` and `S3Client` instance before use

**Don't:**
- Create database instances inside endpoint functions
- Use global database singletons
- Skip `BaseDatabase` abstraction and use concrete classes directly in Core layer
- Hardcode table names (always use environment variables)

## References

- Issue #3: feat: getMe returns the signed-in user
- FastAPI documentation: https://fastapi.tiangolo.com/advanced/events/#lifespan
- Clean Architecture by Robert C. Martin
