---
name: reviewing-code-quality
description: Review readability, naming, local complexity, error handling, unnecessary code and coding-rule consistency across related implementations.
---
# Review code quality

Apply [the shared review contract](../reviewing-pr/REVIEW-CONTRACT.md), including
related unchanged components, all four provenance classes, per-area verdict and
artifact-only output. Return analysis only; consume quality-gate/ADR evidence.

Read and apply the entire `docs/CODING_RULES.md` at the reviewed revision, including
its Coding Guide and every other section, to local implementation and related
patterns. The checks below are illustrative, not an exhaustive checklist or a
replacement for that document. Assess every applicable rule; disclose unavailable
content or unclear applicability instead of claiming a complete review.

Check names
that obscure intent, explanatory/separator comments substituting for structure,
magic values instead of appropriate typed constants, silent return/pass fallbacks,
missing exception causes, overbroad catches, dead code and patch-like TODO workarounds.

Assess long functions and mixed responsibilities by actual cohesion and change cost,
not line count alone. Prefer deletion/reuse or a concrete simpler implementation
when it preserves behavior; avoid speculative abstraction. Architecture owns
cross-component responsibility boundaries; Type Safety owns data model contracts.
Keep framework-/security-specific root causes with their primary specialist.
