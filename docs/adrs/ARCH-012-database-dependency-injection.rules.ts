/// <reference path="rules.d.ts" />

function pythonNode(value: unknown): value is PythonAstNode {
  return typeof value === "object" && value !== null && "_type" in value;
}

function pythonNodes(value: unknown): PythonAstNode[] {
  return Array.isArray(value) ? value.filter(pythonNode) : [];
}

function named(value: unknown, name: string): boolean {
  return pythonNode(value) && value._type === "Name" && value.id === name;
}

function containsNode(value: unknown, predicate: (node: PythonAstNode) => boolean): boolean {
  if (Array.isArray(value)) return value.some((child) => containsNode(child, predicate));
  if (!pythonNode(value)) return false;
  if (["FunctionDef", "AsyncFunctionDef", "ClassDef", "Lambda"].includes(value._type)) return false;
  return predicate(value) || Object.values(value).some((child) => containsNode(child, predicate));
}

function receivesMockSession(scope: PythonAstNode | undefined): boolean {
  if (!scope || !pythonNode(scope.args)) return false;
  const args = scope.args;
  return ["args", "posonlyargs", "kwonlyargs"].some((kind) =>
    pythonNodes(args[kind]).some((arg) => arg.arg === "mock_aws_session"),
  );
}

function assignedTargets(statement: PythonAstNode): PythonAstNode[] {
  if (statement._type === "Assign") return pythonNodes(statement.targets);
  if (statement._type === "AnnAssign" && pythonNode(statement.target)) return [statement.target];
  return [];
}

function injectsMockSession(statement: PythonAstNode, instance: string): boolean {
  return named(statement.value, "mock_aws_session") &&
    assignedTargets(statement).some((target) =>
      target._type === "Attribute" && target.attr === "session" && named(target.value, instance),
    );
}

function hasInjectionBeforeUse(statements: PythonAstNode[], index: number, instance: string): boolean {
  for (const statement of statements.slice(index + 1)) {
    if (injectsMockSession(statement, instance)) return true;
    if (assignedTargets(statement).some((target) => named(target, instance))) return false;
    if (containsNode(statement, (node) =>
      ["Call", "Await", "Return", "Yield", "YieldFrom"].includes(node._type) &&
      containsNode(node, (child) => named(child, instance)),
    )) return false;
  }
  return false;
}

async function checkMockSessionInjection(ctx: RuleContext, className: "DynamoDb" | "S3Client"): Promise<void> {
  for (const file of await ctx.glob("tests/unittests/**/*.py")) {
    const tree = await ctx.ast(file, "python");
    const constructors = new Set<string>([className]);
    for (const statement of tree.body) {
      if (statement._type !== "ImportFrom") continue;
      for (const alias of pythonNodes(statement.names)) {
        if (alias.name === className && typeof alias.asname === "string") constructors.add(alias.asname);
      }
    }

    function visit(node: PythonAstNode, scope?: PythonAstNode, statements: PythonAstNode[] = [], index = -1): void {
      if (["FunctionDef", "AsyncFunctionDef"].includes(node._type)) scope = node;
      if (node._type === "ClassDef") scope = undefined;
      const func = node.func;
      if (node._type === "Call" && pythonNode(func) && (
        (func._type === "Name" && typeof func.id === "string" && constructors.has(func.id)) ||
        (func._type === "Attribute" && func.attr === className)
      )) {
        const statement = statements[index];
        const targets = statement ? assignedTargets(statement) : [];
        const instance = targets.length === 1 && targets[0]._type === "Name" ? targets[0].id : undefined;
        if (!receivesMockSession(scope) || statement?.value !== node || typeof instance !== "string" ||
          !hasInjectionBeforeUse(statements, index, instance)) {
          ctx.report.violation({
            message: `${className} in a unit test must receive mock_aws_session before use in the same function or fixture.`,
            file,
            line: node.lineno,
            fix: `Accept the mock_aws_session fixture and assign instance.session = mock_aws_session immediately after constructing ${className}.`,
          });
        }
      }
      for (const [key, value] of Object.entries(node)) {
        if (Array.isArray(value)) {
          const children = pythonNodes(value);
          children.forEach((child, childIndex) => {
            if (["body", "orelse", "finalbody"].includes(key)) visit(child, scope, children, childIndex);
            else visit(child, scope, statements, index);
          });
        } else if (pythonNode(value)) visit(value, scope, statements, index);
      }
    }
    visit(tree);
  }
}

export default {
  rules: {
    "no-database-instance-in-endpoints": {
      description:
        "API endpoints must not create database instances directly — use app.state.database initialized in lifespan",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /DynamoDb\s*\(/,
          "src/recnavi/apis/**/*.py",
        );
        for (const match of matches) {
          // Skip if this is in main.py lifespan (allowed)
          if (match.file.includes("main.py")) {
            continue;
          }

          ctx.report.violation({
            message:
              "Database instance created in API layer — database instances must be initialized in main.py lifespan and accessed via request.app.state.database",
            file: match.file,
            line: match.line,
            fix: "Access database via request.app.state.database[TABLE_NAME] instead of creating new instances",
          });
        }
      },
    },

    "no-global-database-singletons": {
      description:
        "Database instances must not be global module-level variables — use app.state.database instead",
      severity: "error",
      check: async (ctx) => {
        // Look for module-level database assignments (not inside functions/classes)
        const matches = await ctx.grepFiles(
          /^[a-z_]+_database\s*=\s*DynamoDb\(/,
          "src/recnavi/**/*.py",
        );
        for (const match of matches) {
          // Skip main.py where initialization happens in lifespan
          if (match.file.includes("main.py")) {
            continue;
          }

          ctx.report.violation({
            message:
              "Global database singleton detected — use app.state.database dictionary initialized in lifespan instead",
            file: match.file,
            line: match.line,
            fix: "Remove global variable and initialize in main.py lifespan: app.state.database[TABLE_NAME] = DynamoDb(...)",
          });
        }
      },
    },

    "no-hardcoded-table-names": {
      description:
        "Table names must not be hardcoded strings — use environment variables from config/variables.py",
      severity: "error",
      check: async (ctx) => {
        // Look for direct string literals in database access
        const patterns = [
          /app\.state\.database\[['"](users|projects|groups)['"]\]/,
          /DynamoDb\(table_name\s*=\s*['"]/,
        ];

        for (const pattern of patterns) {
          const matches = await ctx.grepFiles(
            pattern,
            "src/recnavi/**/*.py",
          );
          for (const match of matches) {
            ctx.report.violation({
              message:
                "Hardcoded table name detected — use environment variable constants (e.g., USERS_TABLE_NAME) from config/variables.py",
              file: match.file,
              line: match.line,
              fix: "Replace hardcoded string with environment variable: app.state.database[USERS_TABLE_NAME]",
            });
          }
        }
      },
    },

    "core-must-use-base-database": {
      description:
        "Core layer must use BaseDatabase abstraction, not concrete DynamoDb implementation",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /from recnavi\.infrastructure\.database\.dynamodb import DynamoDb/,
          "src/recnavi/core/**/*.py",
        );
        for (const match of matches) {
          ctx.report.violation({
            message:
              "Core layer imports concrete DynamoDb class — use BaseDatabase abstraction instead",
            file: match.file,
            line: match.line,
            fix: "Import BaseDatabase from recnavi.core.database.base_database instead of DynamoDb from infrastructure",
          });
        }
      },
    },

    "core-function-params-must-use-base-database": {
      description:
        "Core layer function parameters must be typed as BaseDatabase, not DynamoDb",
      severity: "error",
      check: async (ctx) => {
        const coreFiles = await ctx.glob("src/recnavi/core/**/*.py");
        for (const file of coreFiles) {
          const tree = await ctx.ast(file, "python");

          // Find all function definitions
          const functionDefs = ctx.findAstNodes(tree, "FunctionDef", "AsyncFunctionDef");

          for (const funcDef of functionDefs) {
            // Check function arguments for type annotations
            const args = (funcDef as any).args;
            if (!args) continue;

            // Check all argument types
            const allArgs = [
              ...(args.args || []),
              ...(args.posonlyargs || []),
              ...(args.kwonlyargs || []),
            ];

            for (const arg of allArgs) {
              const annotation = (arg as any).annotation;
              if (!annotation) continue;

              // Check if annotation references DynamoDb
              const annotationStr = JSON.stringify(annotation);
              if (annotationStr.includes('"DynamoDb"')) {
                ctx.report.violation({
                  message:
                    `Core function parameter typed as DynamoDb — use BaseDatabase abstraction instead`,
                  file,
                  line: (arg as any).lineno,
                  fix: "Change parameter type annotation from DynamoDb to BaseDatabase",
                });
              }
            }
          }
        }
      },
    },

    "no-database-in-test-without-mock": {
      description:
        "DynamoDb instances in unit tests must receive the mock_aws_session fixture before use",
      severity: "error",
      check: async (ctx) => checkMockSessionInjection(ctx, "DynamoDb"),
    },

    "no-s3-in-test-without-mock": {
      description:
        "S3Client instances in unit tests must receive the mock_aws_session fixture before use",
      severity: "error",
      check: async (ctx) => checkMockSessionInjection(ctx, "S3Client"),
    },

    "no-infrastructure-imports-in-apis": {
      description:
        "APIs layer must not import from infrastructure/ — prevents tight coupling to concrete implementations",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /from recnavi\.infrastructure\b/,
          "src/recnavi/apis/**/*.py",
        );
        for (const match of matches) {
          // Skip main.py where infrastructure is initialized in lifespan
          if (match.file.includes("main.py")) {
            continue;
          }

          ctx.report.violation({
            message:
              "APIs layer imports from infrastructure/ — API endpoints should access databases via app.state.database, not import infrastructure directly",
            file: match.file,
            line: match.line,
            fix: "Access database via request.app.state.database[TABLE_NAME] instead of importing from infrastructure/",
          });
        }
      },
    },
  },
} satisfies RuleSet;
