# CLAUDE.md

This repository contains the TRUST backend application.

## Required reading

Before making implementation changes, read the relevant documents under `/docs`.

Primary documents:
- `README.md`
  - Overview
  - Major design decisions

- `docs/ARCHITECTURE.md`
  - System architecture
  - Layer responsibilities
  - Dependency direction

- `docs/CONTRIBUTING.md`
  - Development workflow
  - How to set up developing environment
  - How to run checks before submission

- `docs/CODING_RULES.md`
  - Coding conventions
  - Branch / PR rules
  - Testing expectations
  - Style and maintainability guidelines


## Working rules for Claude

1. Do not implement based only on local assumptions.
2. Check the relevant document in `/docs` before changing code.
3. Follow existing architecture and coding rules.
4. Prefer minimal, consistent changes over broad rewrites.
5. Do not bypass existing abstractions.
6. If documentation and implementation conflict, report the conflict before making a broad change.
7. When changing behavior, update tests accordingly.
8. When adding new behavior, follow the existing test structure.
9. Keep unit tests independent from LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, and repository secrets.
10. Mark real cloud integration tests with `real_aws`; mark ECS dispatch tests with both `real_aws` and `ecs`.


## General principle

- Structure first. Implementation second.
- Do not solve a local problem by introducing a global inconsistency.
