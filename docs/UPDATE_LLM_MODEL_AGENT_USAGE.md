# Update LLM Model Agent Usage

This document explains how to use the `update-llm-model` custom agent in this repository.

## Purpose
Use this agent when you want to update one or more LLM model mappings safely with a structured, test-first workflow.

The architecture is intentionally split:
- Agent (`.github/agents/update-llm-model.agent.md`): intake, validation, and handoff orchestration.
- Skill (`.github/skills/update-llm-model-execution/SKILL.md`): implementation details, terminal commands, tests, and local verification.

## Prerequisites
- You are in this repository root.
- `uv` is available.
- AWS authentication is available (or you can run AWS SSO login when prompted).

## How to Run
1. Start a chat with the custom agent `update-llm-model`.
2. Provide updates one model at a time:
   - model name (frontend display name)
   - model ID (runtime model ID)
3. Repeat until all updates are entered.
4. Reply `done` to finish intake.
5. Answer whether OpenAI API key or endpoint changed (`yes` / `no`).
6. The agent locks the collected list and executes updates through the dedicated skill.

## Example Interaction
- `What is the model name (frontend display name)?`
- `GPT-5.3`
- `What is the model ID?`
- `azure/gpt-5.3`
- `Are there any additional model updates? (continue / done)`
- `done`
- `Were there any changes to the OpenAI API Key or Endpoint? (yes / no)`
- `no`

## What the Workflow Performs
- Adds or updates tests first.
- Verifies tests fail before implementation changes.
- Updates `model_dict` in `src/trust/config/variables.py`.
- Re-runs tests and confirms pass.
- Optionally updates OpenAI key/endpoint references in `variables.py` only.
- Runs non-interactive local runtime checks for each added model.

## Expected Output
At the end, the agent reports:
1. Collected model updates (provider / model name / model ID)
2. Changed files
3. Command execution outcomes for test and local run
4. Whether OpenAI key/endpoint updates were applied in `variables.py`

## Notes
- If AWS credentials are missing or expired, the workflow pauses and asks for authentication.
- The agent intentionally does not store explicit terminal command details; those are maintained in the skill for easier maintenance.

For a usage walkthrough video, see: [How to use the update-llm-model agent.mov](https://toyotajp.sharepoint.com/:v:/r/sites/msspo_trust/Shared%20Documents/TRUST/AI%E9%A7%86%E5%8B%95%E9%96%8B%E7%99%BA/update-llm-model%E3%82%A8%E3%83%BC%E3%82%B7%E3%82%99%E3%82%A7%E3%83%B3%E3%83%88%E3%81%AE%E4%BD%BF%E3%81%84%E6%96%B9.mov?csf=1&web=1&e=MGhtS3)
