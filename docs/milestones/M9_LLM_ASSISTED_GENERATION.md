# M9: LLM-Assisted Generation With Guardrails

## Goal

Introduce optional LLM-assisted generation behind strict schemas, evidence grounding, and validation gates while preserving deterministic parsing, matching, scoring, and blocker logic.

## Allowed Scope

- Add provider-neutral LLM adapter interfaces.
- Add prompt/input builders that consume deterministic parse, match, evidence, and gate outputs.
- Validate model outputs against Pydantic schemas.
- Add unsupported-claim, hallucination, and evidence-coverage checks.
- Add opt-in configuration so local deterministic workflows can still run without model access.
- Expand recommendation evaluation for LLM-assisted outputs.

## Out Of Scope

- Replacing deterministic extraction or matching with prompt-only behavior.
- Hidden model calls in default tests.
- Unsupported resume claims, invented metrics, or invented seniority.
- Autonomous tool loops without trace and review gates.
- Vector-store or persistent memory expansion unless explicitly scoped.

## Required Invariants

- Deterministic parser, matcher, blocker flags, evidence spans, and benchmark reports remain the source of truth.
- LLM output must be advisory and grounded in available evidence.
- A missing model key or disabled model path must not break deterministic local tests.

## Completion Signal

- LLM-assisted generation is optional, schema-validated, and auditable.
- Grounding and hallucination checks are part of automated verification.
- Existing deterministic outputs remain available.
