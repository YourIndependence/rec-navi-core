# TRUST Environment Guide

This document summarizes all runtime environments -- development, test, and production -- and explains how key environment variables are switched in each.

---

## 1. Environment Overview

| Environment                   | `ENV` value                     | Purpose                                                                                    |
| ----------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------ |
| **GitHub Codespaces / EC2**   | `LOCAL` (default)               | Personal cloud development environment. Uses real AWS resources.                           |
| **Local VSCode devcontainer** | `LOCAL_CONTAINER`               | Local development environment with Docker Compose under `.devcontainer/local/`.            |
| **GitHub Actions**            | `CI`                            | Unit and integration tests run by `unittests.yaml` & `integration-tests.yaml` on every PR. |
| **run-integration-tests.sh**  | `CI` (overridden by the script) | Running integration tests locally via the helper script.                                   |
| **dev environment**           | `dev`                           | Persistent development environment shared by the team. Uses real AWS resources.            |
| **staging environment**       | `staging`                       | Pre-production validation environment. Uses real AWS resources.                            |
| **prod environment**          | `main`                          | Production environment. Uses real AWS resources.                                           |

---

## 2. Key Branches Driven by `ENV`

`variables.py` and `aws_clients.py` evaluate `ENV` once at startup and switch the following four behaviors.

### 2-1. Secret retrieval (`trust-secret-keys`)

| `ENV` value                          | How secrets are obtained                                                             |
| ------------------------------------ | ------------------------------------------------------------------------------------ |
| `CI`                                 | Read directly from environment variables (SecretsManager is skipped)                 |
| `LOCAL_CONTAINER`                    | Fetched from LocalStack's SecretsManager (`AWS_ENDPOINT_URL=http://localstack:4566`) |
| `LOCAL` / `dev` / `staging` / `main` | Fetched from real AWS SecretsManager                                                 |

> Implementation: [`src/trust/config/variables.py:41-69`](../src/trust/config/variables.py#L41-L69)

### 2-2. MySQL connection

| `ENV` value              | How credentials are obtained                                                     |
| ------------------------ | -------------------------------------------------------------------------------- |
| `LOCAL_CONTAINER` / `CI` | Read directly from `DATABASE_HOST/PORT/NAME/USER/PASSWORD` environment variables |
| All others               | Fetched from the SecretsManager secret identified by `DATABASE_SECRET_ID`        |

> Implementation: [`src/trust/infrastructure/external_clients/aws_clients.py:62-79`](../src/trust/infrastructure/external_clients/aws_clients.py#L62-L79)

### 2-3. Google Gemini / Vertex AI authentication

| `ENV` value              | Authentication method                                                                                                             |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `LOCAL_CONTAINER` / `CI` | Application Default Credentials (ADC). `GOOGLE_GENAI_USE_VERTEXAI=TRUE` and `GOOGLE_CLOUD_LOCATION=global` are set automatically. |
| All others               | `trust-gemini-key` is fetched from SecretsManager, written to a temp file, and set as `GOOGLE_APPLICATION_CREDENTIALS`.           |

> Implementation: [`src/trust/config/variables.py:114-127`](../src/trust/config/variables.py#L114-L127)

### 2-4. OpenSearch password

| `ENV` value | How the password is obtained                                                  |
| ----------- | ----------------------------------------------------------------------------- |
| `CI`        | Read from the `OPENSEARCH_PASS` environment variable (default: `local-admin`) |
| All others  | Fetched from the `TrustOpenSearchAdmin` SecretsManager secret                 |

> Implementation: [`src/trust/config/variables.py:101-107`](../src/trust/config/variables.py#L101-L107)

---

## 3. Per-Environment Configuration

### 3-1. GitHub Codespaces / EC2 (`ENV=LOCAL`)

Uses default values.

> Implementation: [`src/trust/config/variables.py:26`](../src/trust/config/variables.py#L26)

**Characteristics:**

*Application runtime* (`uvicorn`, `uv run python -m trust.main`, etc.):
- Connects to real AWS via AWS SSO (`aws sso login`) or an IAM role.
- `get_secret()` / `get_opensearch_secret()` call real AWS SecretsManager.

*`uv run pytest` (unit tests)*:
- `tests/conftest.py::pytest_configure` applies a targeted botocore monkey-patch before `trust.config.variables` is imported. SecretsManager calls are intercepted and return dummy payloads so that test startup succeeds without SSO credentials.
- `OPENSEARCH_ENDPOINT` is not set, so OpenSearch-dependent tests are skipped.
- Tests that require real AWS behaviour must use `skip_no_aws()` from `tests/testing_utils.py`.

For test commands, see [tests/readme.md -- Running tests](../tests/readme.md#running-tests).

---

### 3-2. Local VSCode devcontainer (`ENV=LOCAL_CONTAINER`)

**Config file:** [`.devcontainer/local/compose.yaml`](../.devcontainer/local/compose.yaml)

**Services started:**

| Service        | Image                                | Port | Role                                      |
| -------------- | ------------------------------------ | ---- | ----------------------------------------- |
| `localstack`   | `localstack/localstack:3.7`          | 4566 | Mock for S3, DynamoDB, and SecretsManager |
| `mysql`        | `mysql:8.0`                          | 3306 | ADK session database                      |
| `opensearch`   | `opensearchproject/opensearch:2.13.0` | 9200 | Vector search                             |
| `cognito`      | `jagregory/cognito-local:latest`     | 9229 | Auth mock                                 |
| `cognito-init` | `amazon/aws-cli:latest`              | --   | Initializes the user pool and test user   |

**Dynamic Cognito variables:**
`cognito-init` generates `.devcontainer/local/cognito-env/cognito.env` at startup, which the `core` service mounts as an `env_file`.

```bash
COGNITO_USER_POOL_ID=<generated>
COGNITO_CLIENT_ID=<generated>
```

For test commands, see [tests/readme.md -- Running tests](../tests/readme.md#running-tests).

---

### 3-3. GitHub Actions -- Unit tests (`ENV=CI`)

**Config file:** [`.github/workflows/unittests.yaml`](../.github/workflows/unittests.yaml)

For the full job layout, parallelism strategy, and CI optimizations, see [tests/readme.md -- CI architecture](../tests/readme.md#ci-architecture).

**Key environment variables:**

```bash
ENV=CI
OPENSEARCH_ENDPOINT=localhost
OPENSEARCH_PASS=${{ secrets.OPENSEARCH_TEST_PASSWORD }}
```

**AWS auth:**
Assumes `arn:aws:iam::905418085415:role/trust-dev-bastion-role` via OIDC.

**External service availability in unit tests:**

| Service                          | CI                                                      | LOCAL_CONTAINER                                         |
| -------------------------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| AWS (S3, DynamoDB)               | Mocked/faked in unit tests; no real AWS required        | Mocked/faked in unit tests; no LocalStack required      |
| OpenSearch                       | Service container `localhost:9200`                      | `opensearch:9200`                                       |
| SharePoint Online                | (skip) `MS_TENANT_ID=local-tenant-id` -> skipped        | (skip) `MS_TENANT_ID=local-tenant-id` -> skipped        |
| Box                              | (skip) `BOX_CLIENT_ID=""` -> skipped                    | (skip) `BOX_CLIENT_ID=""` -> skipped                    |
| Sentence Transformers            | (skip/mock) No internet / no cached models -> must mock | (skip/mock) No internet / no cached models -> must mock |
| LLM APIs (Azure OpenAI, Bedrock) | (mock) No real credentials in unit tests -> must mock   | (mock) No real credentials in unit tests -> must mock   |

> **AWS in unit tests**: Unit tests must not rely on real AWS, LocalStack, or repository secrets. Use lightweight fake clients, `botocore.stub.Stubber`, `moto`, or fixtures in `tests/mockups/`. Real AWS behavior belongs in `tests/integration/` with `pytest.mark.real_aws`.
>
> SharePoint and Box integration tests that require real credentials are collected but skipped via `@pytest.mark.skipif` in both CI and LOCAL_CONTAINER. They run only when the respective tenant / client credentials are provided as environment variables.

---

### 3-4. GitHub Actions -- Integration tests (`ENV=CI`)

**Config file:** [`.github/workflows/integration-tests.yaml`](../.github/workflows/integration-tests.yaml)

**Trigger:** PR + push to `dev` / `staging` branches

**Service containers (GitHub Actions native):**

| Service      | Image                                | Port |
| ------------ | ------------------------------------ | ---- |
| `localstack` | `localstack/localstack:3.7`          | 4566 |
| `mysql`      | `mysql:8.0`                          | 3306 |
| `opensearch` | `opensearchproject/opensearch:2.13.0` | 9200 |
| `cognito`    | `jagregory/cognito-local:latest`     | 9229 |

**Environment variables (all steps):**

```bash
ENV=CI
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=ap-northeast-1
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=trust_session
DATABASE_USER=trust
DATABASE_PASSWORD=trust
OPENSEARCH_ENDPOINT=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_PASS=${{ secrets.OPENSEARCH_TEST_PASSWORD || 'TestPassword1!' }}
COGNITO_IDP_ENDPOINT_URL=http://localhost:9229
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=Test1234!
AZURE_OPENAI_ENDPOINT=${{ secrets.AZURE_OPENAI_ENDPOINT }}
AZURE_OPENAI_API_KEY=${{ secrets.AZURE_OPENAI_API_KEY }}
EASTUS_ENDPOINT=${{ secrets.EASTUS_ENDPOINT }}
EASTUS_API_KEY=${{ secrets.EASTUS_API_KEY }}
```

**Initialization steps:**
1. `bash .devcontainer/local/localstack/init.sh` -- creates DynamoDB tables, S3 bucket, and SecretsManager secrets
2. `bash .devcontainer/local/cognito/init.sh` -- creates the user pool and test user; passes the generated `COGNITO_USER_POOL_ID` / `COGNITO_CLIENT_ID` to subsequent steps via `$GITHUB_ENV`

**Services and features NOT available in CI integration tests:**

The integration job is LocalStack-backed because `AWS_ENDPOINT_URL` points to LocalStack. Optional provider tests may run when their secrets are configured; otherwise they must skip cleanly. Tests marked `real_aws` are skipped automatically by `tests/integration/conftest.py` when the AWS endpoint is LocalStack; the pytest command itself stays the same as normal integration runs.

| Service / Feature                    | Reason unavailable in CI                                       | Skip condition                                                  |
| ------------------------------------ | -------------------------------------------------------------- | --------------------------------------------------------------- |
| Azure OpenAI (LLM, GPT-4o)           | Optional repository secret may be absent                       | Only real-provider tests use `not os.environ.get("AZURE_OPENAI_ENDPOINT")` |
| Azure Document Intelligence          | Endpoint and API key are both required                         | `not (EASTUS_ENDPOINT and EASTUS_API_KEY)`                      |
| Google Custom Search API             | `GOOGLE_CUSTOM_SEARCH_CX` / `CX` is not set                    | `not CX` (where `CX` is imported from `trust.config.variables`) |
| ECS `run_task` (async task dispatch) | LocalStack Free Tier does not support the ECS API              | Mark with `real_aws` and `ecs`; skipped automatically when `AWS_ENDPOINT_URL` points to LocalStack |

> **`run_task` and store creation:** The `update_store` use-case calls `run_task` to dispatch an ECS task after creating an OpenSearch index. LocalStack-backed CI must not claim to verify ECS dispatch. Tests that intentionally verify ECS must be marked `real_aws` / `ecs` and run from a credentialed environment such as an EC2 bastion. LocalStack-backed tests should prepare state through supported APIs; a no-op mock is acceptable only for fixture setup that is not itself under test.

> **`_send_notice_sync` ordering:** `error_handler._send_notice_sync` must check `ENV in ["LOCAL_CONTAINER", "CI"]` **before** calling `TRUST_ALERT_MAIL_TABLE.get_item()`. If the ENV guard comes after the DynamoDB call, CI raises `ValidationException` ("One of the required keys was not given a value") because the alert-mail table is not seeded in LocalStack. This ordering bug propagates upward to any endpoint that calls `send_error_alert`.

---

### 3-5. Endpoint selection logic in `scripts/run-integration-tests.sh`

The script probes service reachability and branches into four paths:

| Branch | Trigger                     | ENV                      | Services used                                                  |
| ------ | --------------------------- | ------------------------ | -------------------------------------------------------------- |
| **1**  | `mysql:3306` reachable      | `CI`                     | devcontainer services (LocalStack, MySQL, OpenSearch, Cognito) |
| **2**  | `localhost:3306` reachable  | `CI`                     | Pre-started local services (LocalStack at `localhost:4566`)    |
| **3**  | `DATABASE_HOST` env var set | `LOCAL` (not overridden) | Real AWS + whichever local services the caller pre-started     |
| **4**  | None of the above           | `CI`                     | Starts all services via docker compose, then uses localhost    |

**Branch 3 - real-AWS integration test mode (EC2 / GitHub Codespaces):**

Use this when real AWS services (SecretsManager, DynamoDB, S3, OpenSearch) are reachable from the current machine (e.g., EC2 with an IAM role, or Codespaces with SSO credentials). `ENV` is **not** overridden, so `variables.py` calls `get_secret()` against real AWS SecretsManager and all AWS clients point to real resources.

Required env vars before running the script:

```bash
export DATABASE_HOST=<rds-endpoint-or-localhost>
# If connecting to a local MySQL (not real RDS), also set credentials:
export DATABASE_USER=trust
export DATABASE_PASSWORD=trust
# Required for OpenSearch availability check and connection:
export OPENSEARCH_ENDPOINT=<dev-opensearch-domain-hostname>
# Recommended: avoid colliding with shared dev OpenSearch indexes:
export TEST_STORE_NAME=<your-name>-test-store
```

Test credentials are fetched automatically from the `trust-test-user` SecretsManager secret. If that secret does not exist, set `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`, and `TEST_COGNITO_CLIENT_ID` manually.

**Data isolation:** Integration tests in Branch 3 write to real dev AWS resources (DynamoDB tables, OpenSearch indexes). DynamoDB records use random UUIDs so they do not conflict across runs. Set `TEST_STORE_NAME` to a unique value to isolate OpenSearch index creation.

> Implementation: [`scripts/run-integration-tests.sh`](../scripts/run-integration-tests.sh)

---

### 3-6. dev / staging / prod environments

| Item                   | dev (`ENV=dev`)                             | staging (`ENV=staging`)                 | prod (`ENV=main`)                                         |
| ---------------------- | ------------------------------------------- | --------------------------------------- | --------------------------------------------------------- |
| Secrets                | Real SecretsManager                         | Real SecretsManager                     | Real SecretsManager                                       |
| MySQL                  | Real RDS (credentials from SecretsManager)  | Real RDS                                | Real RDS                                                  |
| OpenSearch             | Real domain (e.g. `trust-dev-vector-store`) | Real domain                             | Real domain                                               |
| Cognito                | Real User Pool                              | Real User Pool                          | Real User Pool                                            |
| Gemini                 | SecretsManager -> `trust-gemini-key`        | Same                                    | Same                                                      |
| Additional CORS origin | `https://dev.trust.toyota`                  | `https://staging.trust.toyota`          | `https://main.trust.toyota` + `https://chat.trust.toyota` |
| Notification URL       | `https://apis.dev.trust.toyota/...`         | `https://apis.staging.trust.toyota/...` | `https://apis.main.trust.toyota/...`                      |

---

## 4. Key Environment Variable Reference

### General

| Variable             | Default              | Description                                                                                                                                                                       |
| -------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ENV`                | `LOCAL`              | Runtime mode; the branch key in `variables.py`.                                                                                                                                   |
| `AWS_DEFAULT_REGION` | `ap-northeast-1`     | Default boto3 region.                                                                                                                                                             |
| `AWS_ENDPOINT_URL`   | (unset)              | Set to `http://localstack:4566` etc. when using LocalStack.                                                                                                                       |
| `LOG_BUCKET_NAME`    | `trust-dev-log-data` | S3 bucket for conversation logs.                                                                                                                                                  |
| `IMPERSONATE`        | (unset)              | Set to `true` / `1` to enable auth bypass only in `LOCAL`, `LOCAL_CONTAINER`, or `CI`. See [Auth bypass for local development](../docs/CONTRIBUTING.md#auth-bypass-for-local-development-impersonate). |

### MySQL (ADK session database)

| Variable             | Default in CI / devcontainer    | Description                                         |
| -------------------- | ------------------------------- | --------------------------------------------------- |
| `DATABASE_HOST`      | `localhost` / `mysql`           | DB hostname.                                        |
| `DATABASE_PORT`      | `3306`                          | DB port.                                            |
| `DATABASE_NAME`      | `trust_session`                 | Database name.                                      |
| `DATABASE_USER`      | `trust`                         | DB user.                                            |
| `DATABASE_PASSWORD`  | `trust`                         | DB password.                                        |
| `DATABASE_SECRET_ID` | `trust-dev-session-db-password` | SecretsManager secret ID used in real environments. |

### OpenSearch

| Variable                 | Default in CI              | Description                                              |
| ------------------------ | -------------------------- | -------------------------------------------------------- |
| `OPENSEARCH_ENDPOINT`    | `localhost` / `opensearch` | Hostname. When unset, OpenSearch unit tests are skipped. |
| `OPENSEARCH_PORT`        | `9200`                     | Port number.                                             |
| `OPENSEARCH_PASS`        | `local-admin` (CI)         | Admin password.                                          |
| `OPENSEARCH_SECRET_ID`   | `TrustOpenSearchAdmin`     | SecretsManager secret ID (non-CI environments).          |
| `OPENSEARCH_DOMAIN_NAME` | `trust-dev-vector-store`   | AWS OpenSearch domain name.                              |

### Cognito

| Variable                   | Default                      | Description                                                   |
| -------------------------- | ---------------------------- | ------------------------------------------------------------- |
| `COGNITO_CLIENT_ID`        | `1ha4nav80ahgsehv8tumfga5o0` | Cognito app client ID. Dynamically generated in devcontainer. |
| `COGNITO_USER_POOL_ID`     | `ap-northeast-1_4vHDvo7ik`   | User pool ID. Dynamically generated in devcontainer.          |
| `COGNITO_IDP_ENDPOINT_URL` | (unset)                      | Local Cognito endpoint (e.g. `http://cognito:9229`).          |

### DynamoDB table names

| Variable                       | Default (with `-dev` suffix) |
| ------------------------------ | ---------------------------- |
| `DDB_MODEL_AVAILABILITY_TABLE` | `ModelAvailability-dev`      |
| `DDB_TRUST_LOG_TABLE`          | `TrustLogTable-dev`          |
| `DDB_USER_SETTING_TABLE`       | `UserSettingTable-dev`       |
| `DDB_TASK_REQUESTS_TABLE`      | `TaskRequestsTable-dev`      |
| `DDB_TRUST_ALERT_MAIL_TABLE`   | `TrustAlertMailTable-dev`    |

### SharePoint Online (Microsoft Graph)

All four variables are stored inside the `trust-secret-keys` SecretsManager secret (see [section 2-1](#2-1-secret-retrieval-trust-secret-keys)). In `ENV=CI`, they fall back to the environment-variable defaults shown below if the env var is absent.

| Variable         | Default (CI / LOCAL_CONTAINER)     | Description                                                                                              |
| ---------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `MS_TENANT_ID`   | `local-tenant-id`                  | Azure AD tenant ID. Tests use `skipif(MS_TENANT_ID == "local-tenant-id")` to guard real Graph API calls. |
| `MS_CLIENT_ID`   | `local-client-id`                  | Azure AD application (client) ID.                                                                        |
| `MS_SECRET_ID`   | `local-secret`                     | Azure AD client secret value.                                                                            |
| `GRAPH_ENDPOINT` | `https://graph.microsoft.com/v1.0` | Microsoft Graph API base URL. Override only when using a national cloud or a proxy.                      |

> **How credentials are provided per environment:**
> - `CI`: read directly from environment variables (not set in `unittests.yaml` / `integration-tests.yaml`, so all fall back to the placeholder defaults above).
> - `LOCAL_CONTAINER`: fetched from the LocalStack `trust-secret-keys` secret, which is seeded with placeholder values by `.devcontainer/local/localstack/init.sh`.
> - `LOCAL` / `dev` / `staging` / `main`: fetched from real AWS SecretsManager `trust-secret-keys`.
>
> To run SPO tests locally against a real tenant, see [tests/readme.md -- SharePoint Online](../tests/readme.md#sharepoint-online-spo).

### Box

All six variables are stored inside the `trust-secret-keys` SecretsManager secret. In `ENV=CI`, they fall back to the environment-variable defaults (empty strings) if unset.

| Variable            | Default (CI / LOCAL_CONTAINER) | Description                                                                           |
| ------------------- | ------------------------------ | ------------------------------------------------------------------------------------- |
| `BOX_CLIENT_ID`     | `""` (empty)                   | Box app client ID. Tests use `skipif(not BOX_CLIENT_ID)` to guard real Box API calls. |
| `BOX_CLIENT_SECRET` | `""` (empty)                   | Box app client secret.                                                                |
| `BOX_ENTERPRISE_ID` | `""` (empty)                   | Box enterprise (account) ID.                                                          |
| `BOX_PUB_KEY`       | `""` (empty)                   | Box JWT public key ID (kid).                                                          |
| `BOX_PRI_KEY`       | `""` (empty)                   | Box JWT RSA private key (PEM format).                                                 |
| `BOX_PASSPHRASE`    | `""` (empty)                   | Passphrase for the JWT private key.                                                   |

> **How credentials are provided per environment:**
> - `CI` / `LOCAL_CONTAINER`: all values are empty; `box_sdk_gen` raises `ValueError` on init, so tests must be guarded with `skipif(not BOX_CLIENT_ID)`.
> - `LOCAL` / `dev` / `staging` / `main`: fetched from real AWS SecretsManager `trust-secret-keys`.
>
> To run Box tests locally, see [tests/readme.md -- Box](../tests/readme.md#box).

### Azure OpenAI / Document Intelligence

| Variable                | Default in CI | Description                                                                                                                                                                                                        |
| ----------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AZURE_OPENAI_ENDPOINT` | `""` (empty)  | Azure OpenAI base URL. Integration tests that call GPT-4o must use `skipif(not os.environ.get("AZURE_OPENAI_ENDPOINT"))`.                                                                                          |
| `AZURE_OPENAI_API_KEY`  | `""` (empty)  | Azure OpenAI API key. Required only for tests that call the real Azure OpenAI endpoint.                                                                                                                            |
| `EASTUS_ENDPOINT`       | `""` (empty)  | Azure Document Intelligence endpoint (East US region). When empty, `DocumentIntelligenceTextExtractor` raises `ValueError` immediately and the `ProcessTaskWithFallback` chain falls through to the next strategy. |
| `EASTUS_API_KEY`        | `""` (empty)  | Azure Document Intelligence API key. Tests that call Document Intelligence directly must require both `EASTUS_ENDPOINT` and `EASTUS_API_KEY`.                                                                      |

### Google Custom Search API

| Variable                   | Default in CI | Description                                                                                  |
| -------------------------- | ------------- | -------------------------------------------------------------------------------------------- |
| `GOOGLE_CUSTOM_SEARCH_CX`  | `""` (empty)  | Google Custom Search engine ID (`CX`). Tests calling `search_web` must use `skipif(not CX)`. |
| `GOOGLE_CUSTOM_SEARCH_KEY` | `""` (empty)  | Google Custom Search API key. Required together with `CX` for real search calls.             |

### Google / Vertex AI

| Variable                         | Description                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| `GOOGLE_GENAI_USE_VERTEXAI`      | When set to `TRUE`, uses Vertex AI instead of a service account key file.                   |
| `GOOGLE_CLOUD_PROJECT`           | GCP project ID. Injected from `compose.yaml` or environment variables in CI / devcontainer. |
| `GOOGLE_CLOUD_LOCATION`          | Vertex AI region (default: `global`).                                                       |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to the service account key file (real environments only).                              |

---

## 5. Service Endpoint Comparison

### Application runtime

| Service        | Codespaces / EC2 (`LOCAL`)           | devcontainer (`LOCAL_CONTAINER`)    | GitHub Actions (`CI`)              |
| -------------- | ------------------------------------ | ----------------------------------- | ---------------------------------- |
| **AWS**        | Real AWS (`ap-northeast-1`)          | LocalStack `http://localstack:4566` | LocalStack `http://localhost:4566` |
| **MySQL**      | Real RDS (via SecretsManager)        | `mysql:3306`                        | `localhost:3306`                   |
| **OpenSearch** | Real domain (via SecretsManager)     | `opensearch:9200`                   | `localhost:9200`                   |
| **Cognito**    | Real User Pool                       | `cognito:9229`                      | `localhost:9229`                   |
| **Gemini**     | SecretsManager -> `trust-gemini-key` | ADC (Vertex AI)                     | ADC (Vertex AI)                    |

### Integration tests (`run-integration-tests.sh`)

| Service        | Branch 1 (devcontainer)             | Branch 2 (pre-started localhost)   | Branch 3 (real-AWS mode)        | Branch 4 / CI (compose)            |
| -------------- | ----------------------------------- | ---------------------------------- | ------------------------------- | ---------------------------------- |
| **AWS**        | LocalStack `http://localstack:4566` | LocalStack `http://localhost:4566` | Real AWS (`ap-northeast-1`)     | LocalStack `http://localhost:4566` |
| **MySQL**      | `mysql:3306`                        | `localhost:3306`                   | `DATABASE_HOST` (env var)       | `localhost:3306`                   |
| **OpenSearch** | `opensearch:9200`                   | `localhost:9200`                   | `OPENSEARCH_ENDPOINT` (env var) | `localhost:9200`                   |
| **Cognito**    | `cognito:9229`                      | `localhost:9229`                   | Real User Pool or local         | `localhost:9229`                   |
| **ENV value**  | `CI`                                | `CI`                               | `LOCAL` (not overridden)        | `CI`                               |

---

## 6. Related Documents

- [tests/readme.md](../tests/readme.md) -- How to run tests and the environment matrix
- [tests/integration/readme.md](../tests/integration/readme.md) -- Integration test prerequisites and Cognito configuration
- [docs/adrs/ARCH-004-testing-strategy.md](./adrs/ARCH-004-testing-strategy.md) -- Testing strategy ADR
- [`scripts/run-integration-tests.sh`](../scripts/run-integration-tests.sh) -- Local integration test runner script
- [`.devcontainer/local/compose.yaml`](../.devcontainer/local/compose.yaml) -- Local development Compose definition
- [`.github/workflows/integration-tests.yaml`](../.github/workflows/integration-tests.yaml) -- Integration test CI workflow
- [`src/trust/config/variables.py`](../src/trust/config/variables.py) -- Central environment variable management module
