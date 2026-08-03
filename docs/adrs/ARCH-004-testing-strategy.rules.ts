/// <reference path="rules.d.ts" />

export default {
  rules: {
    /**
     * async def test_* functions (or their enclosing class) must have @pytest.mark.asyncio.
     * Without the decorator, pytest treats the coroutine as a return value and the test body
     * is never executed — it silently passes. Report when a file contains async def test_
     * but no @pytest.mark.asyncio anywhere.
     * NOTE: This rule is a compensating control for the absence of asyncio_mode = "auto".
     * See DEV-006 in known-deviations.md for the migration path.
     */
    "async-test-needs-asyncio-mark": {
      description:
        "Test files containing 'async def test_' must include @pytest.mark.asyncio. Without it, async tests silently pass without executing.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        for (const file of testFiles) {
          if (file.endsWith("conftest.py")) continue;

          const content = await ctx.readFile(file);
          if (!content.includes("async def test_")) continue;
          if (content.includes("pytest.mark.asyncio")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (/async def test_/.test(lines[i])) {
              ctx.report.violation({
                message:
                  "async test function found but @pytest.mark.asyncio is absent from this file — the test body will not execute and will silently PASS",
                file,
                line: i + 1,
                fix: [
                  "Add @pytest.mark.asyncio to the function or its class:",
                  "  @pytest.mark.asyncio",
                  "  async def test_foo(): ...",
                  "",
                  "  # or at class level (applies to all async methods):",
                  "  @pytest.mark.asyncio",
                  "  class TestFoo:",
                  "      async def test_foo(self): ...",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * skip_local() must not include "CI" in its skip condition.
     * CI always has services (OpenSearch, etc.) provided via GitHub Actions service containers.
     * Skipping in CI means those tests never run in automated pipelines.
     *
     * The only acceptable skip condition is ENV == "LOCAL" (Docker not available).
     */
    "skip-local-must-not-exclude-ci": {
      description:
        "skip_local() must only skip when ENV == 'LOCAL'. Including 'CI' prevents tests from running in CI pipelines.",
      severity: "error",
      check: async (ctx) => {
        const content = await ctx.readFile("tests/testing_utils.py");
        if (!content) return;

        const lines = content.split("\n");
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          if (
            line.includes("skipif") &&
            line.includes("CI") &&
            i > 0 &&
            lines
              .slice(Math.max(0, i - 5), i + 1)
              .some((l) => l.includes("skip_local"))
          ) {
            ctx.report.violation({
              message:
                "skip_local() includes 'CI' in its skip condition — CI must run tests with services provided",
              file: "tests/testing_utils.py",
              line: i + 1,
              fix: [
                "Change the condition to skip only in LOCAL environments:",
                '  return pytest.mark.skipif(ENV == "LOCAL", reason=reason)',
                "",
                "CI will provide OPENSEARCH_ENDPOINT and other env vars via GitHub Actions services.",
                "Service fixtures (e.g. opensearch_database) handle unavailability via pytest.skip.",
              ].join("\n"),
            });
            break;
          }
        }

        // Detect ENV in [..., "CI", ...] pattern
        const ciInListPattern =
          /skipif\s*\([\s\S]*?ENV\s+in\s+\[[\s\S]*?"CI"[\s\S]*?\]/;
        const match = content.match(ciInListPattern);
        if (match) {
          const line =
            content.slice(0, content.indexOf(match[0])).split("\n").length;
          ctx.report.violation({
            message:
              "skip_local() skips when ENV is 'CI' — remove 'CI' from the condition so CI pipelines execute the test",
            file: "tests/testing_utils.py",
            line,
            fix: '  return pytest.mark.skipif(ENV == "LOCAL", reason=reason)',
          });
        }
      },
    },

    /**
     * Integration tests conftest.py must have a service availability check.
     * Without it, running integration tests without docker compose will produce
     * confusing errors instead of clear skip messages.
     */
    "integration-conftest-must-check-services": {
      description:
        "tests/integration/conftest.py must contain a session-scoped fixture that checks service availability and calls pytest.skip when services are not running.",
      severity: "error",
      check: async (ctx) => {
        const content = await ctx.readFile("tests/integration/conftest.py");
        if (!content) {
          ctx.report.violation({
            message:
              "tests/integration/conftest.py is missing — integration tests have no service availability guard",
            file: "tests/integration/conftest.py",
            line: 1,
            fix: [
              "Create tests/integration/conftest.py with a require_services fixture:",
              "  @pytest.fixture(scope='session', autouse=True)",
              "  def require_services():",
              "      if not _is_port_open(DATABASE_HOST, DATABASE_PORT):",
              "          pytest.skip('Services not available. Run: bash scripts/run-integration-tests.sh')",
            ].join("\n"),
          });
          return;
        }

        const hasServiceCheck =
          content.includes("pytest.skip") &&
          (content.includes("require_services") ||
            content.includes("_check_required_services") ||
            content.includes("_is_port_open"));

        if (!hasServiceCheck) {
          ctx.report.violation({
            message:
              "tests/integration/conftest.py has no service availability check — add a session-scoped autouse fixture that calls pytest.skip when services are unreachable",
            file: "tests/integration/conftest.py",
            line: 1,
            fix: [
              "Add a require_services fixture that checks service connectivity:",
              "  @pytest.fixture(scope='session', autouse=True)",
              "  def require_services():",
              "      if not _is_port_open(DATABASE_HOST, DATABASE_PORT):",
              "          pytest.skip('Run: bash scripts/run-integration-tests.sh')",
            ].join("\n"),
          });
        }
      },
    },

    /**
     * LocalStack-backed integration tests must define shared seed fixtures for
     * data that dev AWS usually contains but a fresh CI stack does not.
     *
     * Without these fixtures, tests pass on a developer's populated AWS account
     * and fail in clean LocalStack CI with missing agent, permission, task, or
     * log records.
     */
    "integration-conftest-must-seed-local-test-data": {
      description:
        "tests/integration/conftest.py must own shared LocalStack seed fixtures for root agent, permissions, dynamic agents, task records, and conversation logs.",
      severity: "error",
      check: async (ctx) => {
        const file = "tests/integration/conftest.py";
        const content = await ctx.readFile(file);
        const requiredSeeds = [
          {
            token: "seed_trust_root_agent",
            purpose: "minimal TRUST root agent for agent list/conversation flows",
          },
          {
            token: "mock_x_user",
            purpose: "mock authenticated user plus permission relationship",
          },
          {
            token: "create_mock_agent",
            purpose: "dynamic-agent records with permission and cleanup",
          },
          {
            token: "require_task_records",
            purpose: "synthetic task records for status/list APIs without ECS",
          },
          {
            token: "test_conversation",
            purpose: "synthetic conversation log record for history/share APIs",
          },
        ];

        for (const seed of requiredSeeds) {
          if (content.includes(seed.token)) continue;
          ctx.report.violation({
            message:
              `Missing integration seed fixture '${seed.token}' — LocalStack CI needs ${seed.purpose}`,
            file,
            line: 1,
            fix: [
              `Add or restore a '${seed.token}' fixture in tests/integration/conftest.py.`,
              "Shared dev-like test data must be seeded explicitly for clean LocalStack CI.",
            ].join("\n"),
          });
        }
      },
    },

    /**
     * LocalStack schema must be created before integration fixtures depend on it.
     * This check guards the migration path when adding new tests that need data
     * in DynamoDB/S3/SecretsManager.
     */
    "localstack-init-must-define-integration-schemas": {
      description:
        ".devcontainer/local/localstack/init.sh must create DynamoDB/S3/Secrets resources used by LocalStack-backed integration tests.",
      severity: "error",
      check: async (ctx) => {
        const file = ".devcontainer/local/localstack/init.sh";
        const content = await ctx.readFile(file);
        const requiredResources = [
          "DDB_MODEL_AVAILABILITY_TABLE",
          "DDB_TRUST_LOG_TABLE",
          "DDB_TASK_REQUESTS_TABLE",
          "DDB_AGENT_ATELIER_TABLE",
          "PERMISSION_TABLE_NAME",
          "LOG_BUCKET_NAME",
          "trust-secret-keys",
        ];

        for (const token of requiredResources) {
          if (content.includes(token)) continue;
          ctx.report.violation({
            message:
              `LocalStack init is missing '${token}' — integration tests must not depend on pre-existing dev AWS resources`,
            file,
            line: 1,
            fix: [
              `Add '${token}' to .devcontainer/local/localstack/init.sh with the same key schema/indexes expected by production code.`,
              "If an integration fixture starts using a new table, bucket, or secret, migrate that schema here in the same PR.",
            ].join("\n"),
          });
        }
      },
    },

    /**
     * The default integration command must remain unchanged. Instead, pytest
     * skips real-AWS tests only when AWS_ENDPOINT_URL points to LocalStack.
     * This preserves EC2/real-AWS integration behavior while keeping GitHub CI,
     * devcontainer, and local-compose profiles safe.
     */
    "localstack-profile-must-skip-real-aws-tests": {
      description:
        "tests/integration/conftest.py must skip real_aws tests when AWS_ENDPOINT_URL points to LocalStack. Do not change default pytest options to exclude them.",
      severity: "error",
      check: async (ctx) => {
        const workflowFile = ".github/workflows/integration-tests.yaml";
        const workflow = await ctx.readFile(workflowFile);
        if (workflow.includes('not real_aws')) {
          ctx.report.violation({
            message:
              "integration-tests.yaml excludes real_aws via pytest options — keep the default command unchanged and let conftest skip real_aws only for LocalStack profiles",
            file: workflowFile,
            line: 1,
            fix: [
              "Remove the marker expression from the workflow command:",
              "  uv run pytest --disable-warnings -q --durations=10 tests/integration/",
            ].join("\n"),
          });
        }

        const file = "tests/integration/conftest.py";
        const content = await ctx.readFile(file);
        const hasLocalStackDetection =
          content.includes("AWS_ENDPOINT_URL") &&
          content.includes("_is_localstack_endpoint") &&
          content.includes("pytest_collection_modifyitems");
        const skipsRealAws =
          content.includes("real_aws") &&
          content.includes("item.add_marker") &&
          content.includes("pytest.mark.skip");
        if (hasLocalStackDetection && skipsRealAws) return;

        ctx.report.violation({
          message:
            "tests/integration/conftest.py does not skip real_aws tests for LocalStack AWS_ENDPOINT_URL — LocalStack profiles may call real AWS/ECS tests",
          file,
          line: 1,
          fix: [
            "Add a collection hook that skips real_aws tests only when AWS_ENDPOINT_URL points to LocalStack:",
            "  def pytest_collection_modifyitems(_config, items):",
            "      if not _is_localstack_endpoint(os.environ.get('AWS_ENDPOINT_URL')):",
            "          return",
            "      skip_real_aws = pytest.mark.skip(reason='Requires real AWS resources')",
            "      for item in items:",
            "          if item.get_closest_marker('real_aws') is not None:",
            "              item.add_marker(skip_real_aws)",
          ].join("\n"),
        });
      },
    },

    /**
     * Unit tests that call real SharePoint Online URLs must guard access with
     * @pytest.mark.skipif based on MS_TENANT_ID.
     *
     * In CI and LOCAL_CONTAINER the secret "MS_TENANT_ID" is set to
     * "local-tenant-id", so real Graph API calls fail at auth time.
     */
    "spo-real-url-must-have-skipif": {
      description:
        "Unit tests containing real SharePoint Online URLs (toyotajp.sharepoint.com) must have @pytest.mark.skipif guarded by MS_TENANT_ID. Without the guard, auth fails in CI and LOCAL_CONTAINER.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/unittests/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          if (!content.includes("toyotajp.sharepoint.com")) continue;
          if (content.includes("MS_TENANT_ID") && content.includes("skipif")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes("toyotajp.sharepoint.com")) {
              ctx.report.violation({
                message:
                  "Real SharePoint Online URL found in unit test without MS_TENANT_ID skipif guard — the test will fail with auth errors in CI and LOCAL_CONTAINER",
                file,
                line: i + 1,
                fix: [
                  "Add a credential guard at the top of the file or the test class:",
                  '  _SPO_AVAILABLE = os.environ.get("MS_TENANT_ID", "local-tenant-id") != "local-tenant-id"',
                  "",
                  "  @pytest.mark.skipif(not _SPO_AVAILABLE,",
                  '                      reason="Requires real SharePoint credentials (set MS_TENANT_ID)")',
                  "  class TestSpoIntegration:",
                  "      ...",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * Unit tests that call real Box APIs must guard access with
     * @pytest.mark.skipif based on BOX_CLIENT_ID.
     */
    "box-real-url-must-have-skipif": {
      description:
        "Unit tests containing real Box API URLs (app.box.com) must have @pytest.mark.skipif guarded by BOX_CLIENT_ID. Without the guard, SDK raises ValueError on empty JWT key in CI.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/unittests/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          if (!content.includes("app.box.com")) continue;
          if (content.includes("BOX_CLIENT_ID") && content.includes("skipif")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes("app.box.com")) {
              ctx.report.violation({
                message:
                  "Real Box API URL found in unit test without BOX_CLIENT_ID skipif guard — box_sdk_gen raises ValueError in CI and LOCAL_CONTAINER",
                file,
                line: i + 1,
                fix: [
                  "Add a credential guard at the top of the file:",
                  '  _BOX_AVAILABLE = bool(os.environ.get("BOX_CLIENT_ID", ""))',
                  "",
                  "  @pytest.mark.asyncio",
                  "  @pytest.mark.skipif(not _BOX_AVAILABLE,",
                  '                      reason="Requires real Box credentials (set BOX_CLIENT_ID)")',
                  "  async def test_box_walk(box_loader): ...",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * Unit tests that use S3Dataloader or reference the trust-tmp bucket
     * must use an in-process double. Unit tests must not depend on LocalStack
     * or real AWS buckets.
     */
    "s3-unit-test-must-use-in-process-double": {
      description:
        "Unit tests using S3Dataloader or the trust-tmp bucket must use a fake client, Stubber, moto, or tests/mockups. They must not require LocalStack or real AWS.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/unittests/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          const usesRealS3 =
            content.includes("trust-tmp") || content.includes("S3Dataloader");
          if (!usesRealS3) continue;
          const usesInProcessDouble =
            content.includes("mock_aws") ||
            content.includes("@mock_aws") ||
            content.includes("Stubber") ||
            content.includes("FakeS3") ||
            content.includes("FakeS3Client") ||
            content.includes("patch(");
          if (usesInProcessDouble) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (
              lines[i].includes("trust-tmp") ||
              lines[i].includes("S3Dataloader")
            ) {
              ctx.report.violation({
                message:
                  "S3Dataloader or trust-tmp bucket used in unit test without an in-process double — unit tests must not require LocalStack or real AWS",
                file,
                line: i + 1,
                fix: [
                  "Use a fake client, botocore.stub.Stubber, or moto:",
                  "  with patch('trust.infrastructure.dataloader.s3_dataloader.boto3.client', return_value=FakeS3Client()):",
                  "      loader = S3Dataloader()",
                  "",
                  "If the test intentionally needs a real bucket, move it to tests/integration/ and mark it real_aws.",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * Integration tests that call Azure OpenAI endpoints must guard access
     * with @pytest.mark.skipif based on AZURE_OPENAI_ENDPOINT.
     *
     * CI and LOCAL_CONTAINER do not have Azure credentials. Any integration
     * test that exercises a real GPT-4o call must declare:
     *
     *   _AZURE_AVAILABLE = bool(os.environ.get("AZURE_OPENAI_ENDPOINT"))
     *   @pytest.mark.skipif(not _AZURE_AVAILABLE, reason="...")
     */
    "azure-openai-must-have-skipif-in-integration": {
      description:
        "Integration tests that call Azure OpenAI (AZURE_OPENAI_ENDPOINT) must have @pytest.mark.skipif guarded by AZURE_OPENAI_ENDPOINT. Without the guard, the test hangs or fails with auth errors in CI.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/integration/**/*.py");
        for (const file of testFiles) {
          if (file.endsWith("conftest.py")) continue;
          const content = await ctx.readFile(file);

          // Look for references to Azure OpenAI client usage
          const usesAzure =
            content.includes("AzureOpenAI") ||
            content.includes("azure_openai") ||
            content.includes("OpenAiLlmClient") ||
            (content.includes("AZURE_OPENAI") && !content.includes("skipif"));

          if (!usesAzure) continue;
          // If already guarded by skipif on AZURE_OPENAI_ENDPOINT, skip
          if (content.includes("AZURE_OPENAI_ENDPOINT") && content.includes("skipif")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (
              lines[i].includes("AzureOpenAI") ||
              lines[i].includes("azure_openai") ||
              lines[i].includes("OpenAiLlmClient")
            ) {
              ctx.report.violation({
                message:
                  "Integration test uses Azure OpenAI without AZURE_OPENAI_ENDPOINT skipif guard — will fail with auth errors in CI",
                file,
                line: i + 1,
                fix: [
                  "Add a credential guard at the top of the file:",
                  "  import os",
                  '  _AZURE_AVAILABLE = bool(os.environ.get("AZURE_OPENAI_ENDPOINT"))',
                  "",
                  "  @pytest.mark.skipif(not _AZURE_AVAILABLE,",
                  '                      reason="Azure OpenAI not configured (set AZURE_OPENAI_ENDPOINT)")',
                  "  def test_conversation_with_azure_gpt(client, auth_headers): ...",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * Integration tests that intentionally exercise run_task (ECS dispatch)
     * must be marked as real_aws + ecs so LocalStack-backed profiles can
     * skip them during collection while real-AWS runs include them by default.
     *
     * LocalStack Free Tier does not implement ECS. Calling run_task against
     * LocalStack raises InternalFailure instead of dispatching the task.
     */
    "ecs-run-task-must-have-real-aws-markers": {
      description:
        "Integration tests that call run_task (ECS) must be marked with both real_aws and ecs, or use a no-op mock only during fixture setup.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/integration/**/*.py");
        for (const file of testFiles) {
          if (file.endsWith("conftest.py")) continue;
          const content = await ctx.readFile(file);
          if (!content.includes("run_task")) continue;

          // Acceptable: explicit real_aws + ecs markers, or fixture/setup-only mocking.
          const isGuarded =
            (content.includes("real_aws") && content.includes("ecs")) ||
            (content.includes("patch") && content.includes("run_task")) ||
            (content.includes("AsyncMock") && content.includes("run_task"));
          if (isGuarded) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes("run_task")) {
              ctx.report.violation({
                message:
                  "Integration test calls run_task (ECS) without real_aws/ecs markers or a fixture-only no-op mock — LocalStack Free Tier raises InternalFailure",
                file,
                line: i + 1,
                fix: [
                  "Option A — mark as real AWS / ECS:",
                  "  pytestmark = [pytest.mark.real_aws, pytest.mark.ecs]",
                  "",
                  "Option B — mock run_task in fixture setup only, and do not claim ECS dispatch is verified:",
                  '  with patch("trust.application.cms.update_store.run_task", new_callable=AsyncMock):',
                  "      client.post('/cms/update_store', json={...})",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },
  },
} satisfies RuleSet;
