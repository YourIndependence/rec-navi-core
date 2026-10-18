import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

import ruleSet from "../../docs/adrs/ARCH-011-test-implementation.rules.ts";

const ruleId = "integration-test-must-call-http-client";
const file = "tests/integration/apis/test_recording.py";
const pythonAstScript = `
import ast
import json
import sys

def serialize(value):
    if isinstance(value, ast.AST):
        result = {"_type": type(value).__name__}
        result.update({key: serialize(child) for key, child in ast.iter_fields(value)})
        if hasattr(value, "lineno"):
            result["lineno"] = value.lineno
        return result
    if isinstance(value, list):
        return [serialize(child) for child in value]
    return value

print(json.dumps(serialize(ast.parse(sys.stdin.read()))))
`;

async function check(source) {
  const rule = ruleSet.rules[ruleId];
  assert.ok(rule, `Missing Archgate rule: ${ruleId}`);
  assert.equal(rule.severity, "error");
  const parsed = spawnSync(
    process.env.PYTHON ?? (process.platform === "win32" ? "python" : "python3"),
    ["-c", pythonAstScript],
    { input: source, encoding: "utf8" },
  );
  assert.equal(parsed.status, 0, parsed.stderr);
  const violations = [];
  await rule.check({
    glob: async (pattern) => {
      assert.equal(pattern, "tests/integration/**/*.py");
      return [file];
    },
    ast: async (path, language) => {
      assert.equal(path, file);
      assert.equal(language, "python");
      return JSON.parse(parsed.stdout);
    },
    report: { violation: (detail) => violations.push(detail) },
  });
  return violations;
}

for (const method of ["get", "post", "put", "patch", "delete", "options", "head", "trace"]) {
  test(`allows a response assigned from client.${method}`, async () => {
    assert.deepEqual(await check(`
def test_recording(client):
    response = client.${method}(
        "/recording",
    )
    assert response.status_code == 200
`), []);
  });
}

test("allows awaited HTTP calls and annotated response assignments", async () => {
  assert.deepEqual(await check(`
async def test_recording(client):
    response: Response = await client.post("/recording")
    assert response.status_code == 200
`), []);
});

test("allows HTTP calls inside context managers", async () => {
  assert.deepEqual(await check(`
def test_recording(client):
    with client:
        response = client.post("/recording")
    assert response.status_code == 200
`), []);
});

for (const [name, body] of [
  ["model-only serialization", 'data = ResponseModel(project=project).model_dump()'],
  ["direct OpenAPI generation", 'assert app.openapi()["paths"]["/recording"]'],
  ["a comment containing a request", '# response = client.post("/recording")\n    assert True'],
  ["a string containing a request", 'example = \'response = client.get("/recording")\''],
  ["an unassigned request", 'client.post("/recording")'],
  ["a different assignment target", 'data = client.post("/recording")'],
  ["an application call", 'response = update_scene_usecase()'],
  ["a dictionary get", 'response = data.get("project")'],
  ["an OpenAPI client method", 'response = client.openapi()'],
  ["a request inside an uncalled nested helper", 'def helper():\n        response = client.post("/recording")'],
  ["a request inside a nested class", 'class Helper:\n        response = client.post("/recording")'],
  ["a request inside an uncalled lambda", 'helper = lambda: (response := client.post("/recording"))'],
]) {
  test(`rejects ${name}`, async () => {
    const violations = await check(`def test_recording(client):\n    ${body}\n`);
    assert.equal(violations.length, 1);
    assert.equal(violations[0].file, file);
    assert.equal(violations[0].line, 1);
    assert.match(violations[0].message, /test_recording/);
    assert.match(violations[0].fix, /response = client/);
  });
}

test("checks every test independently, including class methods", async () => {
  const violations = await check(`
def test_success(client):
    response = client.post("/recording")

def test_model_only():
    assert ResponseModel(project=project).model_dump()

class TestRecording:
    async def test_success(self, client):
        response = await client.get("/recording")

    def test_openapi(self):
        assert app.openapi()
`);
  assert.deepEqual(violations.map(({ line }) => line), [5, 12]);
});

test("does not count requests in fixtures or other functions", async () => {
  const violations = await check(`
@pytest.fixture
def response(client):
    response = client.post("/recording")
    return response

def helper(client):
    response = client.post("/recording")
    return response

def test_model_only(response):
    assert response.status_code == 200
`);
  assert.deepEqual(violations.map(({ line }) => line), [11]);
});

test("ignores fixtures, helpers, and classes pytest does not collect", async () => {
  assert.deepEqual(await check(`
@pytest.fixture(scope="module")
def test_data():
    return {}

@pytest_asyncio.fixture
async def test_async_data():
    return {}

def helper():
    pass

class Helper:
    def test_method(self):
        pass
`), []);
});
