# M8: Workflow Trace and Frontend Readiness

## Goal

Expose workflow state and traceability so a future frontend can show progress, diagnostics, and evidence without guessing backend internals.

## Allowed Scope

- Add trace IDs, step status, and workflow timelines to selected responses or status endpoints.
- Define frontend-friendly view-model examples for fit summary, evidence, diagnostics, recommendations, and rankings.
- Add async/status contracts only where workflows are long-running enough to need them.
- Add API documentation and tests for trace/status behavior.
- Keep route handlers thin and delegate workflow logic to services.

## Out Of Scope

- Large production frontend build.
- LLM-assisted generation.
- OCR engine implementation.
- Persistent workflow storage unless explicitly scoped.
- Score-contract, blocker, or ranking rewrites.

## Required Invariants

- Existing endpoint payloads remain backward compatible unless the milestone explicitly version-controls a change.
- Trace metadata explains workflow execution but does not replace evidence spans or parser confidence.
- Frontend readiness must not hide warnings, blockers, or unsupported evidence.

## Completion Signal

- The backend can explain workflow progress and step outcomes through stable contracts.
- Frontend implementation can start from documented response shapes.
- Deterministic benchmark behavior remains preserved.

## Implemented Surface

- `workflow_trace` is optional on selected public response schemas.
- Trace construction lives in `app/services/workflow_trace_service.py`.
- Trace IDs are generated per request with UUIDs.
- Step metadata covers parse, requirement extraction, scoring, evidence collection, blocker computation, recommendations, and ranking where those steps apply.
- Frontend view-model examples are documented in `docs/api/frontend_view_models.md`.
