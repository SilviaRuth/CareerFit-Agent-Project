# Career Workflow API Guide

This guide documents the Milestone 5 endpoints that extend the deterministic core into bounded career-workflow assistance.

## Purpose

These endpoints add reusable candidate context and helper modules without turning the backend into opaque agent sprawl.

Current endpoints:

- `POST /profile-memory`
- `POST /retrieve/evidence`
- `POST /semantic/match`
- `POST /compare/jobs`

## `POST /profile-memory`

Build request-scoped candidate context from one resume input.

Response highlights:

- `profile_id`
- `candidate_name`
- `parser_confidence`
- `strongest_capabilities`
- `development_areas`
- `memory_items`
- `audit`

Important boundaries:

- derived only from the provided resume
- no external persistence
- evidence-linked memory items only

## `POST /retrieve/evidence`

Run bounded keyword retrieval over `profile_memory`.

Use this when you want the most relevant candidate evidence for a recommendation or comparison query without relying on an external vector index.

Response highlights:

- `retrieved_items`
- `retrieval_mode`
- `audit_note`

## `POST /semantic/match`

Return additive semantic hints over `profile_memory`.

This module is explicit and optional:

- `mode: "off"` disables semantic hints
- `mode: "heuristic"` returns canonical-alias and token-overlap hints

The response is additive only. It does not alter deterministic scores or blocker flags.

## `POST /compare/jobs`

Rank multiple opportunities against one candidate profile.

Input:

- either raw `resume_text` or reusable `profile_memory`
- one or more JD entries with `jd_id` and `job_description_text`
- optional `semantic_mode`

Response highlights:

- reusable `candidate_profile`
- ranked JD entries with fit labels and blocker flags
- retrieval-backed evidence snippets
- additive semantic hints
- recommended next steps per role

## Evaluation

Milestone 5 recommendation quality is checked offline through:

```bash
./.venv/Scripts/python.exe -m app.evaluation.recommendation_runner
```

That benchmark tracks:

- usefulness accuracy
- grounding accuracy
- blocker-guardrail accuracy
- hallucination rate
