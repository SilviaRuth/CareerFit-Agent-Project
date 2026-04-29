# M6: Agent Standardization Foundation

## Goal

Prepare the deterministic backend for future agent-style workflows without introducing autonomous agents, LLM dependencies, OCR behavior, or public API behavior changes.

## Allowed Scope

- Define shared workflow trace, step trace, document, and agent-result contracts.
- Standardize service boundaries around existing deterministic capabilities.
- Extract duplicated deterministic helpers when behavior is identical.
- Add tests for schemas, helper contracts, and no-regression behavior.
- Keep CI, Docker, and docs aligned with the current backend.

## Out Of Scope

- Autonomous multi-agent orchestration.
- LLM provider SDKs or model calls.
- OCR or image/scanned-PDF parsing behavior.
- Frontend dashboard implementation.
- Persistent profile memory.
- Score weighting, blocker semantics, or match contract rewrites.

## Required Invariants

- Existing endpoints keep their current behavior.
- Deterministic parse, match, generation, comparison, retrieval, and semantic helper behavior remains unchanged unless explicitly scoped.
- Existing benchmark metrics stay preserved.
- Baseline artifacts are not refreshed unless the task explicitly requires it.

## Completion Signal

- Shared foundation schemas are in place, and helper extraction decisions are documented when no identical behavior can be moved safely.
- Tests and lint pass.
- Existing benchmark behavior is preserved.
- Future agent work has clear contracts to build on.

## Current Foundation Status

Implemented:

- `app/schemas/workflow.py`: `WorkflowStatus`, `WorkflowStepTrace`, `WorkflowTrace`, and `WorkflowResult`.
- `app/schemas/document.py`: `DocumentInput`, `DocumentSegment`, and `NormalizedDocument`.
- `tests/unit/test_workflow_document_schemas.py`: validation coverage for workflow trace, workflow result, and document contracts.

Helper extraction decision:

- No additional helper extraction was performed in this foundation slice.
- Existing shared deterministic helpers remain in place.
- Tokenization/adaptation differences remain deferred unless a future behavior-parity test proves they are identical.

## Definition Of Done

- Exact contract names are listed in this file.
- Exact target files are `app/schemas/workflow.py`, `app/schemas/document.py`, and focused tests under `tests/unit/`.
- Public API behavior does not change.
- No LLM, OCR, autonomous agent, frontend, score-weight, or blocker-semantic work is included.
- Tests cover schema serialization, invalid values, and helper parity for any extracted deterministic helper.
- Benchmark preservation is verified by existing tests or offline runners without regenerating baseline artifacts.
- Documentation updates include `README.md`, `docs/ARCHITECTURE.md`, `docs/CURRENT_STATE_AUDIT.md`, and this milestone file when scope or status changes.

## Verification

Verified on 2026-04-29:

- `.\.venv\Scripts\python.exe -m pytest -q`: 83 passed.
- `.\.venv\Scripts\python.exe -m ruff check app tests`: all checks passed.
- `.\.venv\Scripts\python.exe -m app.evaluation.benchmark_runner`: 15 cases, all tracked metrics 1.0.
- `.\.venv\Scripts\python.exe -m app.evaluation.extraction_runner`: 13 cases, all tracked metrics 1.0.
- `.\.venv\Scripts\python.exe -m app.evaluation.comparison_runner`: 3 scenarios, all tracked metrics 1.0.
- `.\.venv\Scripts\python.exe -m app.evaluation.recommendation_runner`: 3 cases, usefulness/grounding/blocker metrics 1.0 and hallucination rate 0.0.

Baseline artifacts were not regenerated.
