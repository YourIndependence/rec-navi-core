import assert from "node:assert/strict";
import { test } from "node:test";

import ruleSet from "../../docs/adrs/ARCH-013-application-module-naming.rules.ts";

async function check(files) {
  const rule = ruleSet.rules["application-module-no-usecase-suffix"];
  assert.ok(rule, "Missing application module naming rule");
  assert.equal(rule.severity, "error");
  const violations = [];
  await rule.check({
    scopedFiles: files,
    report: { violation: (detail) => violations.push(detail) },
  });
  return violations;
}

for (const file of [
  "src/recnavi/application/user/get_group_users_usecase.py",
  "src/recnavi/application/scene/nested/review_scene_usecase.py",
  "src\\recnavi\\application\\scene\\review_scene_usecase.py",
]) {
  test(`rejects the application module suffix: ${file}`, async () => {
    const violations = await check([file]);
    assert.equal(violations.length, 1);
    assert.equal(violations[0].file, file.replaceAll("\\", "/"));
    assert.equal(violations[0].line, 1);
    assert.match(violations[0].fix, /imports/);
    assert.match(violations[0].fix, /function/);
  });
}

test("allows operation modules, helpers, and package markers", async () => {
  assert.deepEqual(await check([
    "src/recnavi/application/user/get_group_users.py",
    "src/recnavi/application/scene/__init__.py",
    "src/recnavi/application/scene/usecase_helpers.py",
    "src/recnavi/application/scene/review_usecase_helpers.py",
  ]), []);
});

test("does not apply outside application Python modules", async () => {
  assert.deepEqual(await check([
    "src/recnavi/core/user/get_group_users_usecase.py",
    "src/recnavi/application_extra/get_group_users_usecase.py",
    "tests/unittests/application/user/test_get_group_users_usecase.py",
    "src/recnavi/application/user/get_group_users_usecase.py.bak",
  ]), []);
});

test("reports every violating module", async () => {
  assert.equal((await check([
    "src/recnavi/application/user/get_group_users_usecase.py",
    "src/recnavi/application/scene/review_scene.py",
    "src/recnavi/application/scene/update_scene_record_usecase.py",
  ])).length, 2);
});
