/// <reference path="rules.d.ts" />

const POLICIES: Record<string, Record<string, string>> = {
  "core/project/project.py": { get_project: "user.role" },
  "core/project/update_project.py": { update_project: "UserRole.OWNER" },
  "core/project/delete_project.py": { delete_project: "UserRole.OWNER" },
  "core/project/download_project.py": { create_project_archive: "UserRole.OWNER" },
  "core/scene/review_scene.py": { review_scene: "UserRole.OWNER" },
  "core/scene/update_scene.py": { update_scene: "UserRole.STAFF" },
};
const DENIED = "User does not have access permission to this project";

function node(value: unknown): value is PythonAstNode {
  return typeof value === "object" && value !== null && "_type" in value;
}

function nodes(value: unknown): PythonAstNode[] {
  return Array.isArray(value) ? value.filter(node) : [];
}

function walk(value: unknown): PythonAstNode[] {
  if (Array.isArray(value)) return value.flatMap(walk);
  if (!node(value)) return [];
  if (["FunctionDef", "AsyncFunctionDef", "ClassDef", "Lambda"].includes(value._type)) return [];
  return [value, ...Object.values(value).flatMap(walk)];
}

function path(value: unknown): string {
  if (!node(value)) return "";
  if (value._type === "Name") return String(value.id);
  return value._type === "Attribute" ? `${path(value.value)}.${value.attr}` : "";
}

function permissionCall(value: unknown): boolean {
  return node(value) && value._type === "Call" && path(value.func) === "project.validate_permission";
}

function matchesGuard(statement: PythonAstNode, role: string): boolean {
  const test = statement.test;
  if (statement._type !== "If" || !node(test) || test._type !== "UnaryOp" ||
      !node(test.op) || test.op._type !== "Not" || !node(test.operand) || !permissionCall(test.operand)) return false;
  const call = test.operand;
  const keywords = nodes(call.keywords);
  return nodes(call.args).length === 0 && keywords.length === 2 &&
    keywords.some((keyword) => keyword.arg === "user" && path(keyword.value) === "user") &&
    keywords.some((keyword) => keyword.arg === "as_role" && path(keyword.value) === role);
}

function canonicalDenial(guard: PythonAstNode): boolean {
  const body = nodes(guard.body);
  if (body.length !== 1 || body[0]._type !== "Raise" || body[0].cause !== null || nodes(guard.orelse).length) return false;
  const exception = body[0].exc;
  if (!node(exception) || exception._type !== "Call" || path(exception.func) !== "ClientAuthorizationError") return false;
  const args = nodes(exception.args);
  return args.length === 1 && args[0]._type === "Constant" && args[0].value === DENIED && nodes(exception.keywords).length === 0;
}

function inlinePolicy(value: unknown): PythonAstNode | undefined {
  return walk(value).find((item) =>
    (item._type === "Compare" && walk(item).some((part) =>
      ["user.role", "user.group_id", "project.group_id", "project.owner_user_id", "project.assigned_user_ids"].includes(path(part)))) ||
    (item._type === "Call" && path(item.func) === "user.can_act_as"));
}

function beforeEffect(value: unknown): PythonAstNode | undefined {
  return walk(value).find((item) => {
    if (["Return", "Yield", "YieldFrom"].includes(item._type)) return true;
    if (item._type === "Call") {
      const name = path(item.func);
      return name.startsWith("storage.") ||
        (name.startsWith("projects_db.") && !["projects_db.get_item", "projects_db.query"].includes(name)) ||
        (name.startsWith("project.") && name !== "project.model_validate");
    }
    if (["Assign", "AnnAssign", "AugAssign", "Delete"].includes(item._type)) {
      return walk(item.targets ?? [item.target]).some((target) => path(target).startsWith("project."));
    }
    return false;
  });
}

type CheckId = "project-authorization-required" | "project-authorization-no-inline-policy" |
  "project-authorization-guard-format" | "project-authorization-before-effects";

async function check(ctx: RuleContext, id: CheckId): Promise<void> {
  for (const file of ctx.scopedFiles) {
    const relative = file.replace(/\\/g, "/").replace(/^src\/recnavi\//, "");
    if (!relative.startsWith("core/") && !relative.startsWith("application/") && !relative.startsWith("apis/")) continue;
    const tree = await ctx.ast(file, "python");
    for (const func of nodes(tree.body).filter((item) => ["FunctionDef", "AsyncFunctionDef"].includes(item._type))) {
      const body = nodes(func.body);
      const calls = walk(body).filter(permissionCall);
      const role = POLICIES[relative]?.[String(func.name)];
      if (!role && !calls.length) continue;
      const expected = role ?? path(nodes(calls[0].keywords).find((keyword) => keyword.arg === "as_role")?.value);
      const guards = body.filter((statement) => matchesGuard(statement, expected));
      let violation: PythonAstNode | undefined;
      if (id === "project-authorization-required" && guards.length !== 1) violation = func;
      if (id === "project-authorization-no-inline-policy") violation = inlinePolicy(body);
      if (id === "project-authorization-guard-format") violation = guards.find((guard) => !canonicalDenial(guard));
      if (id === "project-authorization-before-effects" && guards.length === 1) {
        violation = beforeEffect(body.slice(0, body.indexOf(guards[0])));
      }
      if (violation) ctx.report.violation({
        file, line: violation.lineno ?? 1,
        message: `${id}: ${String(func.name)} must use the standalone project permission guard before effects`,
        fix: `Use if not project.validate_permission(user=user, as_role=${expected}): raise ClientAuthorizationError("${DENIED}"); keep policy inside Project.validate_permission`,
      });
    }
    for (const name of Object.keys(POLICIES[relative] ?? {})) {
      if (id === "project-authorization-required" && !nodes(tree.body).some((item) => item.name === name)) {
        ctx.report.violation({ file, line: 1, message: `Authorization entry point ${name} is missing; update the explicit policy map when moving it`, fix: "Update the ADR policy map together with the entry point" });
      }
    }
  }
}

export default {
  rules: Object.fromEntries(([
    "project-authorization-required",
    "project-authorization-no-inline-policy",
    "project-authorization-guard-format",
    "project-authorization-before-effects",
  ] as CheckId[]).map((id) => [id, {
    description: "Require canonical project authorization without inline policy or effects before it.",
    severity: "error",
    check: async (ctx: RuleContext) => check(ctx, id),
  }])),
} satisfies RuleSet;
