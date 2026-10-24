---
name: reviewing-type-safety
description: Review concrete types, Pydantic models, validation and cross-module data contracts across PR changes and related implementations.
---
# Review type safety

Apply [the shared review contract](../reviewing-pr/REVIEW-CONTRACT.md), including
related unchanged components, all four provenance classes, per-area verdict and
artifact-only output. Return analysis only; consume quality-gate/ADR evidence.

Check public signatures and returns, optionality, collection/item types, unions,
serialization aliases/exclusions, and schema/runtime compatibility. Identify bare
Any without explicit external-boundary justification, unsubstantiated type ignores,
unsafe casts, and fields accepting unrestricted data where the contract is known.
Check external-to-domain validation and cross-module models rather than loose dicts;
compare related callers, stored records, API schemas, fixtures, and error contracts.

Keep model ownership with Architecture and injection/exposure impact with Security;
link a shared cause instead of producing duplicate findings. Explain a concrete
invalid state, missed validation, runtime mismatch or maintenance consequence.
