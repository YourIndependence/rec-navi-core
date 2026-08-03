/// <reference path="../rules.d.ts" />

const CORE_TOOL_FILE_GLOBS = [
  "src/trust/core/tools/**/*_tool.py",
  "src/trust/core/tools/**/*_tools.py",
];

const AGENT_TOOL_FILE_GLOBS = [
  // Agent-specific tool modules are usually colocated with the agent and named tools.py.
  // tool_registry._init_module(...) initializes these modules with initialize(prefix).
  "src/trust/**/tools.py",
];

const ALL_TOOL_FILE_GLOBS = [
  ...CORE_TOOL_FILE_GLOBS,
  ...AGENT_TOOL_FILE_GLOBS,
];

const CORE_INITIALIZE_SIGNATURE = /^def\s+initialize\s*\(\s*\)\s*(?:->\s*None\s*)?:/m;
const AGENT_INITIALIZE_SIGNATURE =
  /^def\s+initialize\s*\(\s*prefix\s*:\s*str\s*\)\s*->\s*None\s*:/m;
const SYNC_INITIALIZE_SIGNATURE = /^def\s+initialize\s*\(/m;
const ASYNC_INITIALIZE_SIGNATURE = /^async\s+def\s+initialize\s*\(/m;
const REGISTER_TOOL_CALL = "tool_registry.register_tool(";
const TOOLSET_CONSTRUCTOR = /\b[A-Za-z_]\w*ToolSet\s*\(/;
const TOOLSET_VARIABLE_ASSIGNMENT =
  /^\s*([A-Za-z_]\w*)\s*(?::\s*[^=]*\bToolSet\b[^=]*)?\s*=\s*.*\b[A-Za-z_]\w*ToolSet\s*\(/;
const DIRECT_TOOL_IMPORT_PATTERN =
  /from\s+trust\.core\.tools\..*_tools?\s+import\s+/;
const DIRECT_TOOL_IMPORT_RULE_NAME = "no-direct-tool-import-in-agent-construction";
const AGENT_CONSTRUCTION_MARKERS = [
  /\bAgent\s*\(/,
  /\bLlmAgent\s*\(/,
  /\bBaseAgent\s*\(/,
  /\bSequentialAgent\s*\(/,
  /\bParallelAgent\s*\(/,
  /\bLoopAgent\s*\(/,
  /from\s+google\.adk\.agents\s+import\s+/,
  /from\s+trust\.core\.agents\.registry\s+import\s+agent_registry/,
];

type GrepMatch = {
  file: string;
  line: number;
  content: string;
};

type RuleContext = {
  glob: (pattern: string) => Promise<string[]>;
  readFile: (file: string) => Promise<string>;
  grepFiles: (pattern: RegExp, patternGlob: string) => Promise<GrepMatch[]>;
  report: {
    violation: (args: {
      message: string;
      file: string;
      line: number;
      fix?: string;
    }) => void;
    warning: (args: {
      message: string;
      file: string;
      line: number;
      fix?: string;
    }) => void;
  };
};

type InitializeRange = {
  start: number;
  end: number;
};

function shouldIgnoreToolFile(file: string): boolean {
  return (
    file.endsWith("__init__.py") ||
    file.endsWith("registry.py") ||
    file.endsWith("tool_registry.py") ||
    file.includes("/util/") ||
    file.includes("/__pycache__/")
  );
}

function isCoreToolFile(file: string): boolean {
  return file.includes("src/trust/core/tools/");
}

function isAgentSpecificToolFile(file: string): boolean {
  return file.endsWith("/tools.py") && !isCoreToolFile(file);
}

async function getToolFiles(ctx: RuleContext): Promise<string[]> {
  const files = new Set<string>();

  for (const patternGlob of ALL_TOOL_FILE_GLOBS) {
    for (const file of await ctx.glob(patternGlob)) {
      if (!shouldIgnoreToolFile(file)) {
        files.add(file);
      }
    }
  }

  return [...files].sort();
}

function getInitializeRanges(content: string): InitializeRange[] {
  const lines = content.split("\n");
  const ranges: InitializeRange[] = [];

  for (let i = 0; i < lines.length; i++) {
    const initializeMatch = lines[i].match(/^(\s*)def\s+initialize\s*\(/);
    if (!initializeMatch) continue;

    const initializeIndent = initializeMatch[1].length;
    let end = lines.length;

    for (let j = i + 1; j < lines.length; j++) {
      const trimmed = lines[j].trim();
      if (trimmed.length === 0 || trimmed.startsWith("#")) continue;

      const currentIndent = lines[j].match(/^\s*/)?.[0].length ?? 0;
      if (currentIndent <= initializeIndent) {
        end = j;
        break;
      }
    }

    ranges.push({ start: i, end });
  }

  return ranges;
}

function isLineInsideInitialize(lineIndex: number, ranges: InitializeRange[]): boolean {
  return ranges.some((range) => lineIndex >= range.start && lineIndex < range.end);
}

function getInitializeBlock(content: string): string {
  const lines = content.split("\n");
  const [range] = getInitializeRanges(content);

  if (!range) return "";

  return lines.slice(range.start, range.end).join("\n");
}

function initializeLine(content: string): number {
  const lines = content.split("\n");
  const index = lines.findIndex((line) => /^def\s+initialize\s*\(/.test(line));

  return index >= 0 ? index + 1 : 1;
}

function hasRegisterToolInsideInitialize(content: string): boolean {
  return getInitializeBlock(content).includes(REGISTER_TOOL_CALL);
}

function registerToolCallsPassPrefix(initializeBlock: string): boolean {
  const registerToolCalls = initializeBlock.match(/tool_registry\.register_tool\([\s\S]*?\)/g);

  if (!registerToolCalls || registerToolCalls.length === 0) return true;

  return registerToolCalls.every((call) => /\bprefix\s*=\s*prefix\b/.test(call));
}

function getToolSetVariableNames(content: string): Set<string> {
  const toolsetNames = new Set<string>();

  for (const line of content.split("\n")) {
    const assignmentMatch = line.match(TOOLSET_VARIABLE_ASSIGNMENT);
    if (assignmentMatch) {
      toolsetNames.add(assignmentMatch[1]);
    }
  }

  return toolsetNames;
}

function getRegisteredToolName(line: string): string | null {
  const match = line.match(/tool_registry\.register_tool\s*\(\s*([A-Za-z_]\w*)\s*(?:,|\))/);

  return match?.[1] ?? null;
}

function isInlineToolSetRegistration(line: string): boolean {
  const registerToolIndex = line.indexOf(REGISTER_TOOL_CALL);
  if (registerToolIndex < 0) return false;

  const callArgument = line.slice(registerToolIndex + REGISTER_TOOL_CALL.length);

  return TOOLSET_CONSTRUCTOR.test(callArgument);
}

function toToolSetVariableName(name: string): string {
  return `${name.replace(/_?tool_?set$/i, "")}_toolset`;
}

function hasArchgateDisableComment(
  lines: string[],
  lineIndex: number,
  ruleName: string,
): boolean {
  const currentLine = lines[lineIndex] ?? "";
  const previousLine = lines[lineIndex - 1] ?? "";

  return (
    currentLine.includes("archgate-disable") &&
      currentLine.includes(ruleName)
  ) || (
    previousLine.includes("archgate-disable-next-line") &&
      previousLine.includes(ruleName)
  );
}

function isLikelyAgentConstructionFile(file: string, content: string): boolean {
  if (!file.includes("src/trust/core/agents/")) return false;

  // Domain helper modules under core/agents may legitimately import reusable
  // tool factories. Rule 6 is only for files that actually construct agents.
  if (file.endsWith("/tools.py")) return false;

  return AGENT_CONSTRUCTION_MARKERS.some((marker) => marker.test(content));
}

export default {
  rules: {
    /**
     * Tool modules must expose the correct initialize() entrypoint.
     *
     * Core shared tool modules use initialize() with no arguments.
     * Agent-specific tool modules use initialize(prefix: str), because
     * tool_registry._init_module(...) passes the agent prefix when registering
     * tools that must be namespaced per agent.
     */
    "tool-modules-require-initialize": {
      description:
        "Tool modules must define the correct initialize entrypoint: core tools use def initialize() and agent-specific tools use def initialize(prefix: str).",
      severity: "error",
      check: async (ctx: RuleContext) => {
        const toolFiles = await getToolFiles(ctx);

        for (const file of toolFiles) {
          const content = await ctx.readFile(file);

          if (isAgentSpecificToolFile(file)) {
            if (!AGENT_INITIALIZE_SIGNATURE.test(content)) {
              ctx.report.violation({
                message:
                  "agent-specific tool module must define def initialize(prefix: str) -> None so the Tool Registry can pass the agent prefix",
                file,
                line: initializeLine(content),
                fix: [
                  "Add an agent-specific initialize function:",
                  "",
                  "def initialize(prefix: str) -> None:",
                  "    \"\"\"Register agent-specific tools with ToolRegistry.\"\"\"",
                  "    tool_registry.register_tool(example_tool, prefix=prefix)",
                ].join("\n"),
              });
            }

            continue;
          }

          if (!CORE_INITIALIZE_SIGNATURE.test(content)) {
            ctx.report.violation({
              message:
                "core tool module must define def initialize() -> None so tool_registry.initialize() can register it at startup",
              file,
              line: initializeLine(content),
              fix: [
                "Add a synchronous initialize() function:",
                "",
                "def initialize() -> None:",
                "    \"\"\"Register shared tools with ToolRegistry.\"\"\"",
                "    tool_registry.register_tool(example_tool)",
              ].join("\n"),
            });
          }
        }
      },
    },

    /**
     * Agent-specific tools must pass the prefix through registration.
     *
     * Without prefix=prefix, tools from different agents can collide in the
     * registry or be looked up under the wrong name.
     */
    "agent-tool-registration-must-pass-prefix": {
      description:
        "Agent-specific tool modules must register tools with tool_registry.register_tool(..., prefix=prefix).",
      severity: "error",
      check: async (ctx: RuleContext) => {
        const toolFiles = await getToolFiles(ctx);

        for (const file of toolFiles) {
          if (!isAgentSpecificToolFile(file)) continue;

          const content = await ctx.readFile(file);
          const initializeBlock = getInitializeBlock(content);

          if (
            initializeBlock.includes(REGISTER_TOOL_CALL) &&
            !registerToolCallsPassPrefix(initializeBlock)
          ) {
            ctx.report.violation({
              message:
                "agent-specific tool registration must pass prefix=prefix to tool_registry.register_tool(...)",
              file,
              line: initializeLine(content),
              fix: [
                "Pass the agent prefix when registering tools:",
                "",
                "def initialize(prefix: str) -> None:",
                "    tool_registry.register_tool(example_tool, prefix=prefix)",
              ].join("\n"),
            });
          }
        }
      },
    },

    /**
     * initialize() must not be async.
     *
     * Tool registration should be a lightweight synchronous startup operation.
     * Tools may do async work when executed, not when registered.
     */
    "tool-initialize-must-be-sync": {
      description:
        "Tool module initialize() functions must be synchronous. Do not use async def initialize().",
      severity: "error",
      check: async (ctx: RuleContext) => {
        for (const patternGlob of ALL_TOOL_FILE_GLOBS) {
          const matches = await ctx.grepFiles(
            ASYNC_INITIALIZE_SIGNATURE,
            patternGlob,
          );

          for (const match of matches) {
            if (shouldIgnoreToolFile(match.file)) continue;

            ctx.report.violation({
              message:
                "tool module defines async def initialize() - tool registration must be synchronous",
              file: match.file,
              line: match.line,
              fix: "Change async def initialize() to def initialize() and keep registration free of I/O.",
            });
          }
        }
      },
    },

    /**
     * Tool registration must happen inside initialize().
     *
     * Registering tools at module import time creates hidden side effects and
     * bypasses the registry startup lifecycle.
     */
    "no-tool-registration-outside-initialize": {
      description:
        "tool_registry.register_tool(...) must only be called inside def initialize().",
      severity: "error",
      check: async (ctx: RuleContext) => {
        const toolFiles = await getToolFiles(ctx);

        for (const file of toolFiles) {
          const content = await ctx.readFile(file);
          const lines = content.split("\n");
          const initializeRanges = getInitializeRanges(content);

          for (let i = 0; i < lines.length; i++) {
            if (
              lines[i].includes(REGISTER_TOOL_CALL) &&
              !isLineInsideInitialize(i, initializeRanges)
            ) {
              ctx.report.violation({
                message:
                  "tool_registry.register_tool(...) is called outside initialize() - registration must not happen at import time",
                file,
                line: i + 1,
                fix: [
                  "Move registration into initialize():",
                  "",
                  isAgentSpecificToolFile(file)
                    ? "def initialize(prefix: str) -> None:"
                    : "def initialize() -> None:",
                  isAgentSpecificToolFile(file)
                    ? "    tool_registry.register_tool(example_tool, prefix=prefix)"
                    : "    tool_registry.register_tool(example_tool)",
                ].join("\n"),
              });
            }
          }
        }
      },
    },

    /**
     * initialize() should register at least one tool.
     *
     * An initialize() function that does not call tool_registry.register_tool(...)
     * is usually incomplete or dead boilerplate.
     */
    "tool-initialize-must-register-tool": {
      description:
        "Tool module initialize() functions must call tool_registry.register_tool(...).",
      severity: "error",
      check: async (ctx: RuleContext) => {
        const toolFiles = await getToolFiles(ctx);

        for (const file of toolFiles) {
          const content = await ctx.readFile(file);

          if (
            SYNC_INITIALIZE_SIGNATURE.test(content) &&
            !hasRegisterToolInsideInitialize(content)
          ) {
            ctx.report.violation({
              message:
                "initialize() does not register any tool - call tool_registry.register_tool(...) inside initialize()",
              file,
              line: initializeLine(content),
              fix: [
                "Register at least one tool:",
                "",
                isAgentSpecificToolFile(file)
                  ? "def initialize(prefix: str) -> None:"
                  : "def initialize() -> None:",
                isAgentSpecificToolFile(file)
                  ? "    tool_registry.register_tool(example_tool, prefix=prefix)"
                  : "    tool_registry.register_tool(example_tool)",
              ].join("\n"),
            });
          }
        }
      },
    },

    /**
     * ToolSet registration is supported by tool_registry.register_tool(...).
     *
     * register_tool(...) accepts either a plain Callable tool or a ToolSet.
     * ToolSet instances should be assigned to a clearly named *_toolset variable
     * before registration so ADR #688 / PR #687 behavior is documented and
     * easy to audit.
     */
    "toolset-registration-naming-convention": {
      description:
        "ToolSet instances registered through tool_registry.register_tool(...) must be named *_toolset.",
      severity: "error",
      check: async (ctx: RuleContext) => {
        const toolFiles = await getToolFiles(ctx);

        for (const file of toolFiles) {
          const content = await ctx.readFile(file);
          const lines = content.split("\n");
          const toolsetVariableNames = getToolSetVariableNames(content);

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const assignmentMatch = line.match(TOOLSET_VARIABLE_ASSIGNMENT);

            if (assignmentMatch) {
              const toolsetName = assignmentMatch[1];

              if (!toolsetName.endsWith("_toolset")) {
                const suggestedToolsetName = toToolSetVariableName(toolsetName);

                ctx.report.violation({
                  message:
                    "ToolSet instance name must end with _toolset before registration",
                  file,
                  line: i + 1,
                  fix: [
                    "Rename the ToolSet instance to use the *_toolset suffix:",
                    "",
                    `${suggestedToolsetName} = ExampleToolSet(...)`,
                    `tool_registry.register_tool(${suggestedToolsetName})`,
                  ].join("\n"),
                });
              }
            }

            if (!line.includes(REGISTER_TOOL_CALL)) continue;

            const registeredToolName = getRegisteredToolName(line);
            if (
              registeredToolName &&
              toolsetVariableNames.has(registeredToolName) &&
              !registeredToolName.endsWith("_toolset")
            ) {
              ctx.report.violation({
                message:
                  "registered ToolSet variable must end with _toolset",
                file,
                line: i + 1,
                fix: [
                  "Use a *_toolset variable when registering a ToolSet:",
                  "",
                  "document_handler_toolset = DocumentHandlerToolSet(...)",
                  "tool_registry.register_tool(document_handler_toolset)",
                ].join("\n"),
              });
            }

            if (isInlineToolSetRegistration(line)) {
              ctx.report.violation({
                message:
                  "ToolSet registration should use a named *_toolset variable instead of inline construction",
                file,
                line: i + 1,
                fix: [
                  "Assign the ToolSet to a *_toolset variable before registration:",
                  "",
                  "document_handler_toolset = DocumentHandlerToolSet(...)",
                  "tool_registry.register_tool(document_handler_toolset)",
                ].join("\n"),
              });
            }
          }
        }
      },
    },

    /**
     * Tool factory functions must use the *_tool_factory naming convention.
     */
    "tool-factory-naming-convention": {
      description:
        "Factory functions that create tools must be named *_tool_factory.",
      severity: "warning",
      check: async (ctx: RuleContext) => {
        const matches = await ctx.grepFiles(
          /^def\s+\w*factory\s*\(/m,
          "src/trust/core/tools/**/*.py",
        );

        for (const match of matches) {
          if (shouldIgnoreToolFile(match.file)) continue;

          const line = match.content;
          const functionName = line.match(/^def\s+(\w+)\s*\(/)?.[1];

          if (!functionName) continue;
          if (functionName.endsWith("_tool_factory")) continue;

          ctx.report.warning({
            message:
              "tool factory function does not follow *_tool_factory naming convention",
            file: match.file,
            line: match.line,
            fix: `Rename ${functionName} to ${functionName.replace(/_?factory$/, "")}_tool_factory if it creates a tool callable.`,
          });
        }
      },
    },

    /**
     * Dynamic agent construction should use the registry instead of importing
     * concrete tool functions directly.
     *
     * This rule intentionally targets only files that appear to construct ADK
     * agents. Domain helper modules under core/agents, such as criteria
     * fetchers, may legitimately import concrete tool factories. Those helpers
     * are not dynamic agent construction code, so they should not be warned.
     */
    "no-direct-tool-import-in-agent-construction": {
      description:
        "Agent construction code should use tool_registry lookup instead of directly importing concrete tool functions.",
      severity: "warning",
      check: async (ctx: RuleContext) => {
        const matches = await ctx.grepFiles(
          DIRECT_TOOL_IMPORT_PATTERN,
          "src/trust/core/agents/**/*.py",
        );

        for (const match of matches) {
          const content = await ctx.readFile(match.file);
          const lines = content.split("\n");

          if (
            !isLikelyAgentConstructionFile(match.file, content) ||
            hasArchgateDisableComment(
              lines,
              match.line - 1,
              DIRECT_TOOL_IMPORT_RULE_NAME,
            )
          ) {
            continue;
          }

          ctx.report.warning({
            message:
              "agent construction code imports a concrete tool module directly - use tool_registry lookup instead",
            file: match.file,
            line: match.line,
            fix: [
              "Use tool_registry.get_tool(tool_name) in agent construction code.",
              "If this file is a domain helper rather than agent construction code, no warning should be emitted.",
              "For a one-off exception, add:",
              `# archgate-disable-next-line ${DIRECT_TOOL_IMPORT_RULE_NAME}`,
            ].join("\n"),
          });
        }
      },
    },
  },
} satisfies RuleSet;
