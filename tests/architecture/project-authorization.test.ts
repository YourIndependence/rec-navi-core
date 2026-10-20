import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import ruleset from "../../docs/adrs/ARCH-013-project-authorization.rules.ts";

const FILE = "src/recnavi/core/project/download_project.py";
const MESSAGE = "User does not have access permission to this project";
const GUARD = `    if not project.validate_permission(user=user, as_role=UserRole.OWNER):
        raise ClientAuthorizationError("${MESSAGE}")`;

function source(guard = GUARD, before = "", after = "") {
  return `async def create_project_archive(*, project: Project, user: User, storage: BaseObjectStorage):
${before}${guard}
${after}    return await project.create_download_url(storage=storage)
`;
}

async function violations(code: string, file = FILE) {
  const parsed = spawnSync(process.env.PYTHON ?? "python", ["-c", `
import ast, json, sys
def encode(value):
    if isinstance(value, ast.AST):
        return {"_type": type(value).__name__, **{k: encode(v) for k, v in ast.iter_fields(value)}, "lineno": getattr(value, "lineno", 1)}
    if isinstance(value, list):
        return [encode(v) for v in value]
    return value
print(json.dumps(encode(ast.parse(sys.stdin.read()))))
`], { input: code, encoding: "utf8" });
  assert.equal(parsed.status, 0, parsed.stderr);
  const found: { rule: string; line?: number; message: string }[] = [];
  for (const [id, rule] of Object.entries(ruleset.rules)) {
    await rule.check({
      scopedFiles: [file],
      ast: async () => JSON.parse(parsed.stdout),
      report: { violation: (detail: { line?: number; message: string }) => found.push({ rule: id, ...detail }) },
    } as unknown as RuleContext);
  }
  return found.map((item) => item.rule);
}

test("canonical guard and independent scene assignment are accepted", async () => {
  assert.deepEqual(await violations(source()), []);
  assert.deepEqual(await violations(source(GUARD, "", `    if user.user_id not in scene.assigned_user_ids:
        raise ClientAuthorizationError("Not assigned to this scene")
`)), []);
});

test("missing, wrong-role, and nested-only guards cannot authorize an operation", async () => {
  for (const guard of ["    pass", GUARD.replace("UserRole.OWNER", "UserRole.STAFF"), `    if optional:
${GUARD.split("\n").map((line) => "    " + line).join("\n")}`]) {
    assert.ok((await violations(source(guard))).includes("project-authorization-required"));
  }
});

test("comments, strings, and nested functions cannot supply a guard", async () => {
  for (const guard of [`    # ${GUARD.trim().split("\n")[0]}`, `    text = ${JSON.stringify(GUARD)}`, `    def helper():
${GUARD.split("\n").map((line) => "    " + line).join("\n")}`]) {
    assert.ok((await violations(source(guard))).includes("project-authorization-required"));
  }
});

test("inline role, owner, group comparisons and role helpers are rejected", async () => {
  for (const condition of ["user.role != UserRole.OWNER", "user.user_id != project.owner_user_id", "user.group_id != project.group_id", "not user.can_act_as(UserRole.OWNER)"]) {
    assert.ok((await violations(source(GUARD, `    if ${condition}:
        raise ClientAuthorizationError("denied")
`))).includes("project-authorization-no-inline-policy"));
  }
});

test("combined guards, wrong user, positional calls, and additional keywords fail", async () => {
  for (const guard of [GUARD.replace("if not ", "if blocked or not "), GUARD.replace("user=user", "user=other"), GUARD.replace("user=user, ", "user, "), GUARD.replace("as_role=UserRole.OWNER", "as_role=UserRole.OWNER, extra=True")]) {
    assert.ok((await violations(source(guard))).includes("project-authorization-required"));
  }
});

test("denial must raise the exact exception and message without success branches", async () => {
  for (const guard of [GUARD.replace(MESSAGE, "Only owners can download"), GUARD.replace("ClientAuthorizationError", "ValueError"), GUARD.replace(`raise ClientAuthorizationError("${MESSAGE}")`, "return None"), GUARD + "\n    else:\n        return project"]) {
    assert.ok((await violations(source(guard))).includes("project-authorization-guard-format"));
  }
});

test("effects and early returns before authorization fail, including nested effects", async () => {
  for (const before of ["    await storage.upload_base64(object_key=key)\n", "    await projects_db.put_item(item)\n", "    project.status = state\n", "    project.increment_version()\n", "    return project\n", "    if enabled:\n        await storage.delete_object_by_key(object_key=key)\n"]) {
    assert.ok((await violations(source(GUARD, before))).includes("project-authorization-before-effects"));
  }
});

test("DB reads before the guard and effects after it are accepted", async () => {
  assert.deepEqual(await violations(source(GUARD, '    item = await projects_db.get_item(key={"projectId": project_id})\n')), []);
  assert.deepEqual(await violations(source(GUARD, "", "    project.increment_version()\n    await projects_db.put_item(item)\n")), []);
});

test("STAFF update and role-dependent retrieval use their declared policies", async () => {
  for (const [file, name, role] of [
    ["src/recnavi/core/scene/update_scene.py", "update_scene", "UserRole.STAFF"],
    ["src/recnavi/core/project/project.py", "get_project", "user.role"],
  ]) {
    const code = source().replace("create_project_archive", name).replace("UserRole.OWNER", role);
    assert.deepEqual(await violations(code, file), []);
    assert.ok((await violations(code.replace(role, "UserRole.ADMIN"), file)).includes("project-authorization-required"));
  }
});

test("all OWNER entry points enforce their declared role", async () => {
  for (const [file, name] of [
    ["src/recnavi/core/project/update_project.py", "update_project"],
    ["src/recnavi/core/project/delete_project.py", "delete_project"],
    ["src/recnavi/core/scene/review_scene.py", "review_scene"],
  ]) {
    const code = source().replace("create_project_archive", name);
    assert.deepEqual(await violations(code, file), []);
    assert.ok((await violations(code.replace("UserRole.OWNER", "UserRole.ADMIN"), file)).includes("project-authorization-required"));
  }
});

test("new guarded operations are checked, policy implementation and list filtering are excluded", async () => {
  assert.ok((await violations(source(GUARD.replace(MESSAGE, "denied")), "src/recnavi/core/project/other.py")).includes("project-authorization-guard-format"));
  assert.deepEqual(await violations("class Project:\n    def validate_permission(self, user):\n        return user.role == UserRole.OWNER\n", "src/recnavi/core/types/project.py"), []);
  assert.deepEqual(await violations("def list_projects(projects, user):\n    return [project for project in projects if project.owner_user_id == user.user_id]\n", "src/recnavi/core/project/projects.py"), []);
});

test("entry point rename cannot silently remove required coverage", async () => {
  assert.ok((await violations(source().replace("create_project_archive", "renamed"))).includes("project-authorization-required"));
});
