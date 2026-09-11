/// <reference path="rules.d.ts" />

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
        "Unit tests must use MockDatabase/fakes, not real DynamoDb instances (except in integration tests)",
      severity: "warning",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /DynamoDb\s*\(/,
          "tests/unittests/**/*.py",
        );
        for (const match of matches) {
          ctx.report.warning({
            message:
              "DynamoDb instance in unit test — unit tests should use MockDatabase or fakes, not real database instances",
            file: match.file,
            line: match.line,
            fix: "Use MockDatabase from tests/mockups/ or create a fake implementing BaseDatabase",
          });
        }
      },
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
