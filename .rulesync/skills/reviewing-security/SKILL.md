---
name: reviewing-security
description: Review authentication, authorization, tenant isolation, trust boundaries, information exposure and injection risks across related components.
---
# Review security

Apply [the shared review contract](../reviewing-pr/REVIEW-CONTRACT.md), including
related unchanged components, all four provenance classes, per-area verdict and
artifact-only output. Return analysis only; consume quality-gate/ADR evidence.

Trace user identity and permissions from HTTP/tool entry through use cases, domain
checks, storage/search and returned data. Check cross-user/tenant object access,
side effects before authorization, bypassable defaults, shared histories, caching
keys, logs/errors, secrets and sensitive model/tool context.

Inspect untrusted input entering subprocess/eval/exec, SQL, URLs, filesystem paths,
and templates; require appropriate validation/parameterization and destination
controls. Assess external-call timeout/resource-exhaustion exposure and excessive
IAM permissions from concrete reachable paths. Avoid reporting an exploit without
its prerequisites, evidence and impact. Keep necessary test or type evidence linked
rather than duplicating the underlying finding across areas.
