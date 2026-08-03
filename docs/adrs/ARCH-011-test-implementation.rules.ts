/// <reference path="rules.d.ts" />

export default {
  rules: {
    /**
     * Integration tests must not use @patch or unittest.mock.patch.
     * Patching out real components turns the test into a unit test and removes
     * the ability to verify that actual component interactions work correctly.
     * (Moved from ARCH-004 — this is an implementation-level enforcement.)
     */
    "no-patch-in-integration-tests": {
      description:
        "Integration tests must not patch application collaborators. Deterministic boundary doubles are allowed for LLM model resolution, notification sending, ECS handoff setup, and startup registry isolation.",
      severity: "warning",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /@patch\s*\(|with\s+patch\s*\(/,
          "tests/integration/**/*.py",
        );
        for (const match of matches) {
          if (match.file.endsWith("conftest.py")) continue;
          const allowedBoundaryPatch =
            match.content.includes("_resolve_model") ||
            match.content.includes("get_sentence_transformer_model") ||
            match.content.includes("send_notice") ||
            match.content.includes("run_task") ||
            match.content.includes("initialize_store_registry") ||
            match.content.includes("initialize_agent_registry");
          if (allowedBoundaryPatch) continue;

          ctx.report.warning({
            message:
              "unittest.mock.patch used in integration test — patching application collaborators turns this into a unit test",
            file: match.file,
            line: match.line,
            fix: [
              "Use real local services or framework-provided test doubles instead:",
              "  - AWS services: use the LocalStack-backed integration profile",
              "  - ADK sessions: use InMemorySessionService",
              "  - FastAPI dependencies: use app.dependency_overrides",
              "  - LLM determinism: patch only _resolve_model / MockModel boundary",
              "  - If unit-level isolation is truly needed, move to tests/unittests/",
            ].join("\n"),
          });
        }
      },
    },

    /**
     * monkeypatch.setattr() in integration tests must not replace components.
     * Using monkeypatch.setattr() on a service, agent, store, or I/O attribute
     * has the same effect as @patch — it removes a real collaborator from the
     * integration path.
     *
     * monkeypatch is permitted ONLY for environment configuration (setenv, setitem).
     */
    "no-monkeypatch-setattr-component-in-integration": {
      description:
        "monkeypatch.setattr() must not replace services, agents, stores, or I/O in integration tests. It is allowed only for environment configuration (setenv, setitem).",
      severity: "warning",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/integration/**/*.py");
        for (const file of testFiles) {
          if (file.endsWith("conftest.py")) continue;
          const content = await ctx.readFile(file);
          if (!content.includes("monkeypatch.setattr")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes("monkeypatch.setattr")) {
              ctx.report.warning({
                message:
                  "monkeypatch.setattr() in integration test replaces a real component — this defeats the purpose of integration testing",
                file,
                line: i + 1,
                fix: [
                  "Replace with an environment-safe alternative:",
                  "  - For FastAPI dependencies: app.dependency_overrides[dep] = stub",
                  "  - For AWS services: use moto @mock_aws",
                  "  - For environment config: monkeypatch.setenv() or monkeypatch.setitem() are allowed",
                  "  - If component isolation is needed, move to tests/unittests/",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * Root conftest is imported by unit tests and before trust.* modules are
     * safely configured. It must not own LocalStack/service-backed integration
     * seed data. Put that data in tests/integration/conftest.py instead.
     */
    "root-conftest-must-not-own-integration-seed-data": {
      description:
        "Root tests/conftest.py must not create LocalStack-backed integration seed data. Shared integration data belongs in tests/integration/conftest.py.",
      severity: "error",
      check: async (ctx) => {
        const file = "tests/conftest.py";
        const content = await ctx.readFile(file);
        const forbiddenPatterns = [
          "seed_trust_root_agent",
          "create_mock_agent",
          "require_task_records",
          "test_conversation",
          "VectorStore.create_store",
          ".put_item(",
          ".create_table(",
        ];

        for (const token of forbiddenPatterns) {
          if (!content.includes(token)) continue;
          ctx.report.violation({
            message:
              `Root tests/conftest.py contains integration seed/setup pattern '${token}' — this can affect unit collection and should live in tests/integration/conftest.py`,
            file,
            line: 1,
            fix: [
              "Move LocalStack/service-backed seed data to tests/integration/conftest.py.",
              "Keep root conftest limited to pytest plugin registration and unit-safe global setup.",
            ].join("\n"),
          });
        }
      },
    },

    /**
     * Tool-transfer and dynamic-agent integration tests should use the shared
     * create_mock_agent fixture. It creates AgentAtelier data, permission data,
     * unique names, and cleanup consistently across LocalStack and real-AWS modes.
     */
    "dynamic-agent-integration-tests-use-create-mock-agent": {
      description:
        "Dynamic-agent/tool-transfer integration tests must use create_mock_agent so AgentAtelier and PermissionTable seed data are created consistently with cleanup.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/integration/chat_usecase/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          const needsDynamicAgent =
            content.includes("transfer_to_agent") ||
            content.includes('"agents"') ||
            content.includes("'agents'");
          if (!needsDynamicAgent) continue;
          if (content.includes("create_mock_agent")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (
              lines[i].includes("transfer_to_agent") ||
              lines[i].includes('"agents"') ||
              lines[i].includes("'agents'")
            ) {
              ctx.report.violation({
                message:
                  "Dynamic-agent integration test does not use create_mock_agent — AgentAtelier/PermissionTable seed data may be missing or leak across runs",
                file,
                line: i + 1,
                fix: [
                  "Add the create_mock_agent fixture and use it to create per-test agent metadata:",
                  "  async def test_tool_calling_agent(client, auth_headers, create_mock_agent):",
                  "      agent_name = create_mock_agent('it_tool_use_agent', tools=['calculator'])",
                  "",
                  "The fixture creates AgentAtelier, PermissionTable, unique names, and cleanup.",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * Agent CRUD integration tests may write AgentAtelier directly, but direct
     * writes must have cleanup because real-AWS mode uses shared dev tables.
     */
    "direct-agent-table-writes-must-clean-up": {
      description:
        "Integration tests that write AgentAtelier directly must delete their records or use create_mock_agent. Real-AWS mode uses shared dev tables.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/integration/**/*.py");
        for (const file of testFiles) {
          if (file.endsWith("conftest.py")) continue;
          const content = await ctx.readFile(file);
          const touchesAgentTable =
            content.includes("DDB_AGENT_ATELIER_TABLE") ||
            content.includes("AgentAtelier-dev");
          if (!touchesAgentTable) continue;

          const writesAgentData =
            content.includes(".put_item(") ||
            content.includes('"/cms/createAgent"') ||
            content.includes("'/cms/createAgent'");
          if (!writesAgentData) continue;
          if (content.includes("create_mock_agent")) continue;
          if (content.includes(".delete_item(") && content.includes("finally")) continue;

          ctx.report.violation({
            message:
              "Integration test writes AgentAtelier data without obvious finally/delete_item cleanup — this can leak records in real-AWS mode",
            file,
            line: 1,
            fix: [
              "Wrap the write/API call in try/finally and delete the agent record:",
              "  try:",
              "      response = client.post('/cms/createAgent', json=payload, headers=auth_headers)",
              "      assert response.status_code == 200",
              "  finally:",
              "      agent_atelier_table.delete_item(Key={'name': test_agent_name})",
              "",
              "For dynamic-agent chat tests, prefer create_mock_agent instead.",
            ].join("\n"),
          });
        }
      },
    },

    /**
     * Service fixtures in unit tests that retrieve optional external connections
     * (e.g. OpensearchDatabase.get_database_instance()) must use pytest.skip when
     * the result is None, not assert. Using assert causes ERROR instead of SKIP,
     * which breaks the test run when the service is unavailable.
     */
    "service-fixture-must-use-pytest-skip": {
      description:
        "Fixtures that obtain optional external service connections must use pytest.skip (not assert) when the connection is None.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/unittests/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          if (!content.includes("get_database_instance")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (
              /assert\s+\w+\s+is\s+not\s+None/.test(lines[i]) &&
              i > 0
            ) {
              const context = lines.slice(Math.max(0, i - 5), i + 1).join("\n");
              if (context.includes("get_database_instance")) {
                ctx.report.violation({
                  message:
                    "assert on a service fixture return value — use pytest.skip instead to avoid ERROR when the service is unavailable",
                  file,
                  line: i + 1,
                  fix: [
                    "Replace the assert with a conditional pytest.skip:",
                    "  db = await SomeDatabase.get_database_instance()",
                    "  if db is None:",
                    '      pytest.skip("Service not available. Set OPENSEARCH_ENDPOINT to run.")',
                    "  return db",
                  ].join("\n"),
                });
              }
            }
          }
        }
      },
    },

    /**
     * Unit tests that call get_sentence_transformer_model must mock it.
     *
     * The function downloads models from HuggingFace on first use. CI runners
     * have no internet access (or no pre-cached models), so any test that
     * triggers this call hangs indefinitely.
     */
    "sentence-transformer-must-be-mocked": {
      description:
        "Unit tests that call get_sentence_transformer_model must patch it with MockSentenceTransformer. The function downloads from HuggingFace and hangs indefinitely in CI without internet access.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/unittests/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          if (!content.includes("get_sentence_transformer_model")) continue;
          const isMocked =
            (content.includes("patch") &&
              content.includes("get_sentence_transformer_model")) ||
            content.includes("MockSentenceTransformer") ||
            content.includes("mock_sentence_transformer");
          if (isMocked) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes("get_sentence_transformer_model")) {
              ctx.report.violation({
                message:
                  "get_sentence_transformer_model called in unit test without mocking — downloads from HuggingFace and hangs in CI (no internet)",
                file,
                line: i + 1,
                fix: [
                  "Mock the function at the import binding in the module under test:",
                  "  from tests.mockups.mock_sentence_transformer import MockSentenceTransformer",
                  '  _mock = MockSentenceTransformer("paraphrase-multilingual-mpnet-base-v2")',
                  '  with patch("<module>.get_sentence_transformer_model", return_value=_mock):',
                  "      # run the test",
                  "",
                  "Or register the mock model before the test:",
                  "  from trust.core.model_registry.sentence_transformer_registry import register_model",
                  '  register_model(model_name="...", model=MockSentenceTransformer("..."))',
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * Async fixtures must use @pytest_asyncio.fixture, not @pytest.fixture.
     *
     * Using @pytest.fixture on an async def function is deprecated in
     * pytest-asyncio v0.21+ and causes a DeprecationWarning or error in v1.x.
     * It can also cause event-loop scope mismatches for session/module fixtures.
     */
    "async-fixture-must-use-pytest-asyncio-fixture": {
      description:
        "Async fixtures (async def) must use @pytest_asyncio.fixture, not @pytest.fixture. Using @pytest.fixture on async def is deprecated in pytest-asyncio v1.x and may cause event-loop scope mismatches.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          // Only check files that have async fixtures
          if (!content.includes("async def") || !content.includes("@pytest.fixture")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            // Look for @pytest.fixture followed (within 3 lines) by async def
            if (/^\s*@pytest\.fixture/.test(lines[i])) {
              // Check next few lines for async def
              for (let j = i + 1; j <= i + 3 && j < lines.length; j++) {
                if (/^\s*async def /.test(lines[j])) {
                  // Check it's not a test function (those are decorated differently)
                  if (!/async def test_/.test(lines[j])) {
                    ctx.report.violation({
                      message:
                        "@pytest.fixture used on an async def function — use @pytest_asyncio.fixture to avoid event-loop scope mismatches in pytest-asyncio v1.x",
                      file,
                      line: i + 1,
                      fix: [
                        "Replace @pytest.fixture with @pytest_asyncio.fixture:",
                        "  import pytest_asyncio",
                        "",
                        "  @pytest_asyncio.fixture(scope='module')  # or 'function', 'session'",
                        "  async def my_fixture():",
                        "      ...",
                        "",
                        "For session-scoped async fixtures, add loop_scope:",
                        "  @pytest_asyncio.fixture(scope='session', loop_scope='session')",
                        "  async def my_session_fixture():",
                        "      ...",
                      ].join("\n"),
                    });
                    break;
                  }
                }
              }
            }
          }
        }
      },
    },

    /**
     * Mock classes implementing core ABCs (Base*) must be placed in tests/mockups/,
     * not defined inline inside test files.
     *
     * Inline mock class definitions cannot be reused, bloat test files, and lead
     * to the same mock being duplicated across modules. See ARCH-003 for the full policy.
     */
    "mock-abc-class-must-be-in-mockups-dir": {
      description:
        "Classes implementing Base* ABCs defined inline in test files must be moved to tests/mockups/. Inline mock classes cannot be shared and duplicate across modules.",
      severity: "warning",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        for (const file of testFiles) {
          // Skip mockups/ themselves and conftest files
          if (file.includes("tests/mockups/")) continue;
          if (file.endsWith("conftest.py")) continue;

          const content = await ctx.readFile(file);
          // Look for class definitions that inherit from Base*
          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            const classMatch = lines[i].match(/^class\s+(\w+)\s*\(.*Base\w+.*\)\s*:/);
            if (classMatch) {
              const className = classMatch[1];
              // Exclude if it's a test class (TestFoo pattern)
              if (/^Test/.test(className)) continue;
              ctx.report.warning({
                message:
                  `Inline mock class '${className}' implements a Base* ABC — move it to tests/mockups/ so it can be shared and registered as a pytest plugin`,
                file,
                line: i + 1,
                fix: [
                  `Move the class to tests/mockups/mock_${className.toLowerCase().replace("mock", "")}.py`,
                  "Then register it in pytest_plugins in tests/conftest.py:",
                  '  pytest_plugins = [',
                  `      "tests.mockups.mock_${className.toLowerCase().replace("mock", "")}",`,
                  "  ]",
                  "See ARCH-003 for the full mock class policy.",
                ].join("\n"),
              });
            }
          }
        }
      },
    },

    /**
     * Expensive fixture setup (DB table creation, HTTP client creation, search index
     * initialization) must use module or session scope, not function scope.
     *
     * Creating a DynamoDB table or FastAPI TestClient for every test function
     * multiplies setup cost by the number of tests and slows the suite significantly.
     */
    "expensive-fixture-must-not-use-function-scope": {
      description:
        "Fixtures that create database tables, HTTP clients, or search indexes must use module or session scope. Function-scoped setup for expensive resources slows the test suite significantly.",
      severity: "warning",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        for (const file of testFiles) {
          const content = await ctx.readFile(file);

          // Only check files with fixtures
          if (!content.includes("@pytest.fixture") && !content.includes("@pytest_asyncio.fixture")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            // Look for function-scoped (default) fixtures — no scope= argument
            const isDefaultScopedFixture =
              (/^\s*@pytest\.fixture\s*$/.test(lines[i]) ||
                /^\s*@pytest_asyncio\.fixture\s*$/.test(lines[i]));

            if (!isDefaultScopedFixture) continue;

            // Check the body of the fixture (next ~10 lines) for expensive patterns
            const body = lines.slice(i + 1, Math.min(i + 15, lines.length)).join("\n");
            const isExpensive =
              body.includes("create_table") ||
              body.includes("TestClient") ||
              body.includes("create_async_engine") ||
              body.includes("create_index") ||
              body.includes("get_database_instance");

            if (isExpensive) {
              // Find the fixture function name for a better message
              const nextDef = lines.slice(i + 1, i + 4).find((l) => /def /.test(l));
              const nameMatch = nextDef?.match(/def (\w+)/);
              const fixtureName = nameMatch ? nameMatch[1] : "this fixture";

              ctx.report.warning({
                message:
                  `'${fixtureName}' creates an expensive resource (DB table, HTTP client, or index) in function scope — use scope='module' or scope='session' to avoid per-test recreation`,
                file,
                line: i + 1,
                fix: [
                  "Add scope='module' (shared within a test file) or scope='session' (shared across all tests):",
                  "  @pytest_asyncio.fixture(scope='module')",
                  "  async def my_table():",
                  "      with mock_aws():",
                  "          table = dynamodb.create_table(...)",
                  "          yield table",
                ].join("\n"),
              });
            }
          }
        }
      },
    },

    /**
     * Integration tests that call Azure Document Intelligence must guard access
     * with @pytest.mark.skipif based on both EASTUS_ENDPOINT and EASTUS_API_KEY.
     *
     * Both EASTUS_ENDPOINT and EASTUS_API_KEY are required. Any integration test
     * that exercises real Document Intelligence calls must declare:
     *
     *   _DI_AVAILABLE = bool(EASTUS_ENDPOINT and EASTUS_API_KEY)
     *   @pytest.mark.skipif(not _DI_AVAILABLE, reason="...")
     *
     * Note: exec_impl should also fail-fast with ValueError when the endpoint is
     * not configured so that ProcessTaskWithFallback can skip to the next strategy.
     */
    "azure-document-intelligence-must-have-skipif-in-integration": {
      description:
        "Integration tests that call Azure Document Intelligence must have @pytest.mark.skipif guarded by both EASTUS_ENDPOINT and EASTUS_API_KEY. Without the guard, the test fails or times out in CI.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/integration/**/*.py");
        for (const file of testFiles) {
          if (file.endsWith("conftest.py")) continue;
          const content = await ctx.readFile(file);

          const usesDI =
            content.includes("DocumentIntelligence") ||
            content.includes("document_intelligence") ||
            content.includes("DOCUMENT_INTELLIGENCE") ||
            content.includes("EASTUS_ENDPOINT");

          if (!usesDI) continue;
          if (
            content.includes("EASTUS_ENDPOINT") &&
            content.includes("EASTUS_API_KEY") &&
            content.includes("skipif")
          ) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (
              lines[i].includes("DocumentIntelligence") ||
              lines[i].includes("document_intelligence") ||
              lines[i].includes("DOCUMENT_INTELLIGENCE")
            ) {
              ctx.report.violation({
                message:
                  "Integration test uses Azure Document Intelligence without EASTUS_ENDPOINT and EASTUS_API_KEY skipif guard — will fail or time out in CI",
                file,
                line: i + 1,
                fix: [
                  "Add a credential guard at the top of the file:",
                  "  from trust.config.variables import EASTUS_API_KEY, EASTUS_ENDPOINT",
                  "  _DI_AVAILABLE = bool(EASTUS_ENDPOINT and EASTUS_API_KEY)",
                  "",
                  "  @pytest.mark.skipif(not _DI_AVAILABLE,",
                  '                      reason="Azure Document Intelligence not configured (set EASTUS_ENDPOINT and EASTUS_API_KEY)")',
                  "  def test_analysis_document_with_document_intelligence(client): ...",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * Integration tests that call Google Custom Search must guard access
     * with @pytest.mark.skipif based on the CX (Custom Search Engine ID) variable.
     *
     * CX is empty in CI and LOCAL_CONTAINER. Any integration test that exercises
     * real Google Custom Search calls must declare:
     *
     *   from trust.config.variables import CX as GOOGLE_CX
     *   @pytest.mark.skipif(not GOOGLE_CX, reason="...")
     */
    "google-custom-search-must-have-skipif-in-integration": {
      description:
        "Integration tests that call Google Custom Search must have @pytest.mark.skipif guarded by the CX variable. Without the guard, the test fails in CI where CX is empty.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/integration/**/*.py");
        for (const file of testFiles) {
          if (file.endsWith("conftest.py")) continue;
          const content = await ctx.readFile(file);

          const usesGCS =
            content.includes("google_custom_search") ||
            content.includes("GoogleCustomSearch") ||
            content.includes("GOOGLE_CUSTOM_SEARCH");

          if (!usesGCS) continue;
          // Acceptable if skipif guards CX or GOOGLE_CUSTOM_SEARCH
          if (
            (content.includes("CX") || content.includes("GOOGLE_CUSTOM_SEARCH")) &&
            content.includes("skipif")
          ) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            if (
              lines[i].includes("google_custom_search") ||
              lines[i].includes("GoogleCustomSearch") ||
              lines[i].includes("GOOGLE_CUSTOM_SEARCH")
            ) {
              ctx.report.violation({
                message:
                  "Integration test uses Google Custom Search without CX skipif guard — will fail in CI where CX is empty",
                file,
                line: i + 1,
                fix: [
                  "Add a credential guard at the top of the file:",
                  "  from trust.config.variables import CX as GOOGLE_CX",
                  "",
                  "  @pytest.mark.skipif(not GOOGLE_CX,",
                  '                      reason="Google Custom Search not configured (set GOOGLE_CUSTOM_SEARCH_CX)")',
                  "  async def test_web_search(client): ...",
                ].join("\n"),
              });
              break;
            }
          }
        }
      },
    },

    /**
     * Unit tests must not contain real outbound HTTP URLs without mocking.
     *
     * Tests in tests/unittests/ run in CI without external network access.
     * A real URL string (https://...) combined with no evidence of patching
     * the HTTP client or extractor class indicates the test will make a live
     * request that will either fail or produce non-deterministic results.
     *
     * Allowed safe patterns:
     *  - https://mock.  (explicit mock endpoint)
     *  - https://example.com  (RFC 2606 test domain, no real server)
     *  - https://localhost  / https://127.0.0.1  (local loopback)
     *  - any https:// URL inside a string that also appears in the same file
     *    alongside patch / AsyncMock / MagicMock (the URL is being mocked)
     */
    "unit-test-must-not-make-real-http-calls": {
      description:
        "Unit tests in tests/unittests/ must not contain real outbound HTTPS URLs without mocking the HTTP client or extractor class. CI has no external network access; real URLs cause non-deterministic failures.",
      severity: "error",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/unittests/**/*.py");
        // Matches https:// URLs that are NOT safe placeholder/loopback domains
        const realUrlPattern =
          /https:\/\/(?!mock\.|example\.com|localhost|127\.0\.0\.1)[a-zA-Z0-9][\w.-]+\.[a-zA-Z]{2,}/g;

        // Lines where a URL is clearly a data literal rather than a live call:
        //   - dict value:            "key": "https://..."  or  'key': 'https://...'
        //   - assert equality RHS:   assert expr == "https://..."
        //   - equality LHS check:    "https://..." ==
        const safeLinePattern =
          /(?:["']\w+["']\s*:\s*["']https?:|assert\b.*==\s*["']https?:|==\s*["']https?:)/;

        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          realUrlPattern.lastIndex = 0;
          const matches = [...content.matchAll(realUrlPattern)];
          if (matches.length === 0) continue;

          // File-level guards — the author is already aware of the network
          // dependency and has handled it via mocking or a skipif guard.
          const hasMocking =
            content.includes("patch(") ||
            content.includes("AsyncMock") ||
            content.includes("MagicMock") ||
            content.includes("monkeypatch") ||
            content.includes("responses.") ||
            content.includes("httpretty") ||
            content.includes("respx");
          if (hasMocking) continue;

          // skipif guard: the real call is conditional on an env var, which is
          // the accepted integration-style pattern inside unittests/
          if (content.includes("skipif")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            realUrlPattern.lastIndex = 0;
            if (!realUrlPattern.test(line)) continue;

            // Skip lines where the URL is a passive data value, not a call arg
            if (safeLinePattern.test(line)) continue;

            ctx.report.violation({
              message:
                "Real outbound HTTPS URL found in unit test without any mocking — CI has no external network access and the request will fail or return unexpected results",
              file,
              line: i + 1,
              fix: [
                "Option A — mock the HTTP client or extractor class (pure unit test):",
                "  from unittest.mock import AsyncMock, patch",
                "",
                "  with patch(",
                '      "trust.core.agents.website_reader_agent.tools.Html2MarkdownTextExtractor",',
                "      return_value=AsyncMock(return_value='mock content'),",
                "  ):",
                "      async for event in load_website('https://example.com/article'):",
                "          ...",
                "",
                "Option B — guard with skipif (integration-style, inside unittests/):",
                '  _NET_AVAILABLE = bool(os.environ.get("INTEGRATION_NET"))',
                "  @pytest.mark.skipif(not _NET_AVAILABLE,",
                '                      reason="Requires external network access")',
                "  async def test_load_real_website(): ...",
              ].join("\n"),
            });
            break;
          }
        }
      },
    },

    /**
     * monkeypatch.setattr() calls that pass a private attribute name (starting
     * with "_") are almost always wrong in unit tests targeting TRUST classes.
     *
     * The most common mistake is patching an instance attribute that doesn't
     * exist because the external client is created per-call via
     * `async with ClassName(...)`, not stored as `self._client`.
     *
     * The rule flags any monkeypatch.setattr() whose second argument is a
     * string starting with "_", prompting the author to verify the attribute
     * actually exists on the target object before merging.
     */
    "monkeypatch-setattr-underscore-attribute": {
      description:
        "monkeypatch.setattr(obj, '_attr', ...) with a private attribute name starting with '_' is likely wrong — the attribute may not exist on the target, masking the real failure with AttributeError. Verify existence first; for async-context-manager clients, patch the class at its import binding instead.",
      severity: "warning",
      check: async (ctx) => {
        const testFiles = await ctx.glob("tests/**/*.py");
        // Match: monkeypatch.setattr(<anything>, "_<name>", ...)
        // The second argument is a quoted string starting with underscore.
        const setAttrPrivatePattern =
          /monkeypatch\.setattr\s*\([^,]+,\s*["'](_[^"']+)["']/g;

        for (const file of testFiles) {
          const content = await ctx.readFile(file);
          if (!content.includes("monkeypatch.setattr")) continue;

          const lines = content.split("\n");
          for (let i = 0; i < lines.length; i++) {
            const match = setAttrPrivatePattern.exec(lines[i]);
            if (match) {
              const attrName = match[1];
              ctx.report.violation({
                message: `monkeypatch.setattr with private attribute '${attrName}' — verify that this attribute exists on the target object. If the collaborator is created via 'async with ClassName(...)', patch the class at its import binding instead`,
                file,
                line: i + 1,
                fix: [
                  `Verify '${attrName}' is a real attribute of the target class.`,
                  "",
                  "If the collaborator is created per-call via `async with ClassName(...)`",
                  "there is no instance attribute to patch. Patch the class instead:",
                  "",
                  "  import module_under_test as _mod",
                  "  mock_client = AsyncMock()",
                  "  mock_client.__aenter__ = AsyncMock(return_value=mock_client)",
                  "  mock_client.__aexit__ = AsyncMock(return_value=False)",
                  "  monkeypatch.setattr(_mod, 'ClassName', MagicMock(return_value=mock_client))",
                ].join("\n"),
              });
            }
            setAttrPrivatePattern.lastIndex = 0;
          }
        }
      },
    },
  },
} satisfies RuleSet;
