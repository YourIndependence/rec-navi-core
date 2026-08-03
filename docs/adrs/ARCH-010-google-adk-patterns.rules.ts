/// <reference path="rules.d.ts" />

export default {
  rules: {
    'agent-required-files': {
      description:
        'Each static Google ADK agent directory must contain agent.py and prompts.py. Dynamic agents use AgentRegistry pattern.',
      severity: 'error',
      check: async (ctx) => {
        const agentFiles = await ctx.glob('src/trust/core/agents/*/agent.py')

        for (const agentFile of agentFiles) {
          const dir = agentFile.replace(/\/agent\.py$/, '')
          const agentName = dir.split('/').pop() ?? dir

          // Skip util, util_tools, and agent_registry (dynamic agent pattern)
          if (agentName === 'util' || agentName === 'util_tools' || agentName === 'agent_registry') {
            continue
          }

          const promptsFiles = await ctx.glob(`${dir}/prompts.py`)
          if (promptsFiles.length === 0) {
            ctx.report.violation({
              message: `Static agent '${agentName}' is missing prompts.py — each static agent must declare its instruction and description`,
              file: agentFile,
              fix: 'Add prompts.py with return_instruction() and return_description() functions, or migrate to dynamic AgentRegistry pattern',
            })
          }
        }
      },
    },

    'agent-factory-function': {
      description:
        'Each static agent.py must expose a get_<name>() or get_<name>_agent() factory function. Dynamic agents use AgentRegistry.get_agent() instead.',
      severity: 'error',
      check: async (ctx) => {
        const agentFiles = await ctx.glob('src/trust/core/agents/*/agent.py')

        for (const agentFile of agentFiles) {
          const dir = agentFile.replace(/\/agent\.py$/, '')
          const agentName = dir.split('/').pop() ?? dir

          // Skip util, util_tools, and agent_registry (dynamic agent pattern)
          if (agentName === 'util' || agentName === 'util_tools' || agentName === 'agent_registry') {
            continue
          }

          // Check for get_<name>() or get_<name>_agent() function
          const content = await ctx.readFile(agentFile)
          const standardPattern = new RegExp(`def get_${agentName}\\(`, 'i')
          const agentSuffixPattern = new RegExp(`def get_${agentName}_agent\\(`, 'i')

          const hasFactory = standardPattern.test(content) || agentSuffixPattern.test(content)

          if (!hasFactory) {
            ctx.report.violation({
              message: `Static agent '${agentName}' is missing get_${agentName}() or get_${agentName}_agent() factory function in agent.py`,
              file: agentFile,
              fix: `Add a 'def get_${agentName}(...) -> Agent:' or 'def get_${agentName}_agent(...) -> Agent:' factory function that returns the agent instance, or migrate to dynamic AgentRegistry pattern`,
            })
          }
        }
      },
    },

    'prompts-required-functions': {
      description:
        'prompts.py must define return_instruction() and return_description() functions.',
      severity: 'error',
      check: async (ctx) => {
        const promptsFiles = await ctx.glob(
          'src/trust/core/agents/*/prompts.py'
        )

        for (const promptsFile of promptsFiles) {
          const dir = promptsFile.replace(/\/prompts\.py$/, '')
          const agentName = dir.split('/').pop() ?? dir

          // Skip util and util_tools directories
          if (agentName === 'util' || agentName === 'util_tools') {
            continue
          }

          const content = await ctx.readFile(promptsFile)

          // Check for return_instruction() or return_instruction_<name>()
          // Accept both patterns: return_instruction() or return_instruction_xxx()
          const hasInstruction =
            /def return_instruction\(\)/.test(content) ||
            /def return_instruction_\w+\(/.test(content)

          if (!hasInstruction) {
            ctx.report.violation({
              message: `prompts.py for '${agentName}' is missing return_instruction() or return_instruction_${agentName}() function`,
              file: promptsFile,
              fix: "Add 'def return_instruction() -> str:' or 'def return_instruction_<name>() -> str:' function that returns the agent's system instruction",
            })
          }

          // Check for return_description() or return_description_<name>()
          const hasDescription =
            /def return_description\(\)/.test(content) ||
            /def return_description_\w+\(/.test(content)

          if (!hasDescription) {
            ctx.report.violation({
              message: `prompts.py for '${agentName}' is missing return_description() or return_description_${agentName}() function`,
              file: promptsFile,
              fix: "Add 'def return_description() -> str:' or 'def return_description_<name>() -> str:' function that returns the agent's description for delegation routing",
            })
          }
        }
      },
    },

    'no-asyncio-run-in-async-context': {
      description:
        'Forbid asyncio.run() inside async def — causes deadlocks in async request context.',
      severity: 'error',
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          // Read file content
          const content = await ctx.readFile(file)
          const lines = content.split('\n')

          // Track if we're inside an async function
          let insideAsyncDef = false
          let asyncDefStartLine = 0

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i]
            const lineNumber = i + 1

            // Detect async def start
            if (/^\s*async\s+def\s+\w+/.test(line)) {
              insideAsyncDef = true
              asyncDefStartLine = lineNumber
            }

            // Detect function end (dedent to same or less indentation as def)
            if (insideAsyncDef && /^\S/.test(line) && !/^\s*async\s+def/.test(line)) {
              insideAsyncDef = false
            }

            // Check for asyncio.run() inside async def
            if (insideAsyncDef && /asyncio\.run\(/.test(line)) {
              ctx.report.violation({
                message: `asyncio.run() called inside async function (starts at line ${asyncDefStartLine}) — this causes deadlocks in async context`,
                file,
                line: lineNumber,
                fix: 'Use await instead of asyncio.run() inside async functions. Only call asyncio.run() from synchronous entry points.',
              })
            }
          }
        }
      },
    },

    'async-io-in-agent-tools': {
      description:
        'Agent tools performing I/O must use async def for non-blocking execution.',
      severity: 'error',
      check: async (ctx) => {
        const toolsFiles = await ctx.glob('src/trust/core/agents/*/tools.py')

        for (const toolsFile of toolsFiles) {
          const content = await ctx.readFile(toolsFile)

          // Look for blocking I/O patterns in non-async functions
          const blockingPatterns = [
            { pattern: /\brequests\.(get|post|put|delete|patch)\(/, name: 'requests' },
            { pattern: /\bopen\([^)]*,\s*['"][rwa]/, name: 'open()' },
            { pattern: /\bpsycopg2\.connect\(/, name: 'psycopg2' },
            { pattern: /\btime\.sleep\(/, name: 'time.sleep()' },
          ]

          const lines = content.split('\n')
          let insideAsyncDef = false
          let currentFunctionLine = 0

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i]
            const lineNumber = i + 1

            // Track async vs sync function context
            if (/^\s*async\s+def\s+\w+/.test(line)) {
              insideAsyncDef = true
              currentFunctionLine = lineNumber
            } else if (/^\s*def\s+\w+/.test(line)) {
              insideAsyncDef = false
              currentFunctionLine = lineNumber
            }

            // Detect function end
            if (/^[^\s#]/.test(line) && !/(async\s+)?def\s+/.test(line)) {
              insideAsyncDef = false
              currentFunctionLine = 0
            }

            // Check for blocking I/O in non-async functions
            if (!insideAsyncDef && currentFunctionLine > 0) {
              for (const { pattern, name } of blockingPatterns) {
                if (pattern.test(line)) {
                  ctx.report.violation({
                    message: `Blocking I/O (${name}) detected in non-async function (line ${currentFunctionLine}) — prefer async equivalents (httpx, aiofiles, asyncpg)`,
                    file: toolsFile,
                    line: lineNumber,
                    fix: `Change the function at line ${currentFunctionLine} to 'async def' and use async I/O libraries (httpx.AsyncClient, aiofiles, asyncpg)`,
                  })
                }
              }
            }
          }
        }
      },
    },

    'no-inline-prompts-in-agent': {
      description:
        'Static agent instruction/description should be defined in prompts.py, not hardcoded in agent.py. Dynamic agents (AgentRegistry) may load prompts from metadata.',
      severity: 'error',
      check: async (ctx) => {
        const agentFiles = await ctx.glob('src/trust/core/agents/*/agent.py')

        for (const agentFile of agentFiles) {
          const dir = agentFile.replace(/\/agent\.py$/, '')
          const agentName = dir.split('/').pop() ?? dir

          // Skip util, util_tools, and agent_registry (dynamic agent pattern)
          if (agentName === 'util' || agentName === 'util_tools' || agentName === 'agent_registry') {
            continue
          }

          const content = await ctx.readFile(agentFile)

          // Check for hardcoded instruction or description strings (only for static agents)
          const hardcodedInstructionPattern = /instruction\s*=\s*["']/
          const hardcodedDescriptionPattern = /description\s*=\s*["']/

          const matches = [
            ...content.matchAll(new RegExp(hardcodedInstructionPattern, 'g')),
            ...content.matchAll(new RegExp(hardcodedDescriptionPattern, 'g')),
          ]

          if (matches.length > 0) {
            ctx.report.violation({
              message: `Static agent '${agentName}' has inline instruction/description strings — move to prompts.py for better testability`,
              file: agentFile,
              fix: 'Define return_instruction() and return_description() in prompts.py and import them in agent.py. For dynamic agents, use AgentRegistry pattern instead.',
            })
          }
        }
      },
    },

    'agent-registry-registration': {
      description:
        '[DEPRECATED] Static agents should be registered in registry.py. With dynamic AgentRegistry pattern, this check is no longer required.',
      severity: 'info',
      check: async (ctx) => {
        // This rule is deprecated with the introduction of dynamic AgentRegistry pattern (PR #686).
        // Dynamic agents are stored in DynamoDB and instantiated at runtime via AgentRegistry.
        // Static agents (legacy pattern) may still use registry.py, but it's optional.

        const registryFile = 'src/trust/core/agents/registry.py'
        const agentRegistryFile = 'src/trust/core/agents/agent_registry.py'

        // Check if dynamic AgentRegistry exists
        let dynamicRegistryExists = false
        try {
          await ctx.readFile(agentRegistryFile)
          dynamicRegistryExists = true
        } catch (e) {
          // File doesn't exist
        }

        if (dynamicRegistryExists) {
          // Dynamic pattern in use — skip static registry check
          return
        }

        // Fallback: Check for static registry (legacy)
        let registryContent = ''
        try {
          registryContent = await ctx.readFile(registryFile)
        } catch (e) {
          ctx.report.violation({
            message: 'Neither dynamic AgentRegistry nor static registry.py found — agents cannot be looked up at runtime',
            file: registryFile,
            severity: 'info',
            fix: 'Implement dynamic AgentRegistry pattern (preferred) or create static registry.py for legacy agents',
          })
          return
        }

        // If static registry exists, optionally check registration (downgraded to info level)
        const agentFiles = await ctx.glob('src/trust/core/agents/*/agent.py')
        for (const agentFile of agentFiles) {
          const dir = agentFile.replace(/\/agent\.py$/, '')
          const agentName = dir.split('/').pop() ?? dir

          // Skip util, util_tools, __pycache__, and root_agent
          if (
            agentName === 'util' ||
            agentName === 'util_tools' ||
            agentName === '__pycache__' ||
            agentName === 'root_agent'
          ) {
            continue
          }

          const standardPattern = new RegExp(`get_${agentName}[^_]`, 'i')
          const agentSuffixPattern = new RegExp(`get_${agentName}_agent`, 'i')

          const isRegistered =
            standardPattern.test(registryContent) ||
            agentSuffixPattern.test(registryContent)

          if (!isRegistered) {
            ctx.report.violation({
              message: `Static agent '${agentName}' may not be registered in registry.py`,
              file: agentFile,
              severity: 'info',
              fix: `Add to static registry.py or migrate to dynamic AgentRegistry pattern`,
            })
          }
        }
      },
    },
  },
} satisfies RuleSet
