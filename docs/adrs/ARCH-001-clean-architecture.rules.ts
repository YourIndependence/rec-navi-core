/// <reference path="rules.d.ts" />

export default {
  rules: {
    "application-module-no-usecase-suffix": {
      description: "Application module filenames must omit the _usecase suffix; function names retain it.",
      severity: "error",
      check: async (ctx) => {
        for (const path of ctx.scopedFiles) {
          const file = path.replace(/\\/g, "/");
          if (!/^src\/recnavi\/application\/(?:[^/]+\/)*[^/]+_usecase\.py$/.test(file)) {
            continue;
          }
          const target = file.replace(/_usecase\.py$/, ".py");
          ctx.report.violation({
            message: `Application module ${file} repeats the use-case layer in its filename`,
            file,
            line: 1,
            fix: `Rename to ${target}; update imports, mock patch targets, and mirrored tests, keeping function names unchanged`,
          });
        }
      },
    },

    "no-infrastructure-imports-application": {
      description:
        "infrastructure/ must not import from application/ or apis/ — prevents upward coupling.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /from trust\.(application|apis)\b/,
          "src/trust/infrastructure/**/*.py",
        );
        for (const match of matches) {
          const target = match.content.includes("trust.application")
            ? "application"
            : "apis";
          ctx.report.violation({
            message: `infrastructure/ imports from ${target}/ — this creates upward coupling that breaks the dependency rule`,
            file: match.file,
            line: match.line,
            fix: "Move shared logic to core/, or invert the dependency via an abstract interface in core/",
          });
        }
      },
    },

    "no-application-imports-apis": {
      description:
        "application/ must not import from apis/ — use cases must stay decoupled from HTTP schemas.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /from trust\.apis\b/,
          "src/trust/application/**/*.py",
        );
        for (const match of matches) {
          ctx.report.violation({
            message:
              "application/ imports from apis/ — use cases must not depend on FastAPI/Pydantic request models",
            file: match.file,
            line: match.line,
            fix: "Accept plain Python types or core/types/ models as parameters instead of apis/ schemas",
          });
        }
      },
    },

    "no-core-imports-infrastructure": {
      description:
        "core/ should not import concrete implementations from infrastructure/. Use ABCs and rely on Registry injection.",
      severity: "error",
      check: async (ctx) => {
        const matches = await ctx.grepFiles(
          /from trust\.infrastructure\b/,
          "src/trust/core/**/*.py",
        );
        for (const match of matches) {
          ctx.report.violation({
            message:
              "core/ imports from infrastructure/ — use the abstract base class and let the Registry inject the concrete implementation",
            file: match.file,
            line: match.line,
            fix: "Replace with the BaseLlmClient / BaseDatabase / BaseStore import from core/, and inject via registry at startup",
          });
        }
      },
    },
  },
} satisfies RuleSet;
