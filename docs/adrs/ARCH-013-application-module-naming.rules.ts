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
  },
} satisfies RuleSet;
