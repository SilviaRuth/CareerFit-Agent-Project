# AGENT.md

## Project

CareerFit Agent

An explainable AI backend for resume parsing, JD parsing, deterministic fit analysis, grounded career guidance, reusable candidate context, and offline evaluation.

## Purpose Of This File

This file gives repo-specific guidance to coding agents working in this project.

Use it to:

- understand the product and architecture priorities
- preserve bounded, reviewable implementations
- avoid hidden drift toward opaque orchestration
- keep changes aligned with tests, fixtures, and docs

When in doubt:

- preserve clarity over cleverness
- preserve modularity over premature abstraction
- preserve testability over implementation speed

## Product Intent

This is not a generic chatbot project.

The core workflow is:

1. parse a JD into structured requirements
2. parse a resume into a structured candidate profile
3. normalize skills and evidence
4. compute deterministic fit analysis
5. explain strengths, gaps, and blockers
6. generate grounded rewrite, interview-prep, interview-simulation, and learning-plan guidance
7. compare resume variants or opportunities without hiding evidence
8. support offline regression review through checked-in fixtures and reports

Outputs should stay:

- structured
- explainable
- evidence-linked where possible
- safe and advisory rather than overly authoritative
- reviewable without hidden reasoning steps

## Development Priorities

Prioritize work in this order:

1. correctness of structured extraction
2. skill normalization quality
3. explainable matching logic
4. recommendation usefulness
5. retrieval grounding
6. evaluation coverage
7. API stability
8. UI polish

Do not jump to heavy frontend work unless explicitly asked.

## Architecture Principles

### Keep modules narrow

Prefer small, cohesive modules with clear responsibilities.

### Separate concerns

Keep these concerns separate:

- preprocessing
- extraction
- normalization
- scoring
- recommendation
- retrieval
- evaluation
- API transport

### Prefer structured outputs

Whenever possible, validate outputs against explicit schemas instead of free-form text.

### Avoid premature multi-agent complexity

The default architecture is a single orchestrator plus specialized modules or services.

Do not introduce multi-agent orchestration unless the task explicitly calls for it.

### Keep behavior inspectable

Avoid hidden magic. Favor explicit logic, readable flows, and reviewable outputs.

## Milestone Discipline

Use `docs/PLAN.md` and the files under `docs/milestones/` as the source of truth for future milestone boundaries. Do not create a duplicate root `AGENTS.md`; this file remains the AI/Codex contributor guide.

Milestone work must stay inside the named milestone unless the user explicitly expands scope. If a task seems to belong to a later milestone, document it as deferred instead of implementing it early.

### M6: Agent Standardization Foundation

Allowed:
- define shared workflow trace, document, and agent-result contracts
- standardize deterministic service boundaries without changing endpoint behavior
- extract small duplicated helpers when behavior is identical
- improve docs, CI, Docker, and review checklists for future agent work

Not allowed:
- no autonomous multi-agent orchestration
- no LLM provider dependency
- no OCR or multimodal parsing behavior
- no frontend dashboard
- no score-contract or blocker-semantics rewrite

### M7: Multimodal Ingestion Foundation

Allowed:
- add first-class document normalization and diagnostic models for multimodal inputs
- add scanned-PDF/image detection and explicit unsupported or needs-OCR outcomes
- add OCR adapter interfaces and fixtures before choosing heavy OCR dependencies
- expand ingestion tests and evaluation metrics for document quality

Not allowed:
- no LLM generation changes
- no frontend workflow UI
- no persistent storage
- no hidden fallback that turns bad OCR text into normal high-confidence parsing
- no benchmark baseline refresh unless the milestone explicitly calls for it

### M8: Workflow Trace and Frontend Readiness

Allowed:
- expose workflow trace IDs, step status, and frontend-friendly response shapes
- add async/status contracts if workflows become long-running
- add API docs and view-model examples for dashboard use
- add frontend readiness tests or contract fixtures

Not allowed:
- no production frontend build unless explicitly requested
- no LLM behavior
- no OCR engine work beyond consuming M7 document contracts
- no change to deterministic score meaning

### M9: LLM-Assisted Generation With Guardrails

Allowed:
- introduce LLM-assisted generation behind explicit adapters and feature boundaries
- validate LLM outputs against schemas and evidence
- keep deterministic parsing, matching, scoring, blockers, and retrieval as source-of-truth inputs
- add hallucination, grounding, and guardrail evaluation before release claims

Not allowed:
- no prompt-only replacement for deterministic logic
- no unsupported candidate claims
- no hidden model calls in tests or default local workflows
- no autonomous tool loops without traceability and review gates

### M10: Deployment and Portfolio Release

Allowed:
- harden Docker, CI, runtime config, docs, and demo workflows
- prepare release notes, portfolio narrative, and deployment instructions
- add production-readiness checks, dependency split, and operational guidance
- polish API examples and evaluation summaries

Not allowed:
- no large new feature surface
- no new OCR, LLM, or frontend architecture expansion
- no baseline metric changes without explicit release rationale
- no scope creep that delays making the existing system demonstrably shippable

## Tech Stack Expectations

Default assumptions unless a task says otherwise:

- Python 3.11
- FastAPI
- Pydantic v2
- pytest
- lightweight retrieval helpers only when grounding clearly improves
- structured logging
- type hints throughout

Do not introduce major framework changes without justification.

## Repository Shape

Current important paths:

- `app/api/routes/`: FastAPI transport layer
- `app/core/`: static config and constants
- `app/schemas/`: Pydantic models and API contracts
- `app/services/`: parsing, matching, orchestration, comparison, and adaptation logic
- `app/services/generation/`: grounded rendering and generation guardrails
- `app/services/ingestion/`: bounded text, PDF, and DOCX ingestion
- `app/services/candidate_profile_service.py`: request-scoped candidate profile memory
- `app/services/retrieval_service.py`: bounded candidate-evidence retrieval
- `app/services/semantic_matching_service.py`: additive semantic hints behind explicit contracts
- `app/evaluation/`: offline benchmark and artifact helpers
- `data/samples/`: reviewable input fixtures
- `data/eval/`: manifests, expected outputs, and checked-in reports
- `tests/unit/` and `tests/integration/`: regression coverage
- `docs/`: project docs and design notes

Do not collapse everything into a single script.

## Coding Preferences

- Use explicit Python with type hints on public and non-trivial internal functions.
- Prefer small functions and narrow modules.
- Avoid abstractions added only for style.
- Fail clearly on invalid inputs.
- Do not swallow parsing failures.
- Preserve deterministic behavior on the parse and match critical path.

### Logging

- Add structured logs for non-trivial workflow steps.
- Do not log secrets or sensitive raw personal data unless a local debug mode explicitly requires it.

### Comments And Docstrings

- Add docstrings for public classes and functions.
- Add concise comments only when the logic is non-obvious.
- Do not over-comment trivial code.

## Schema Rules

Structured schemas are a core part of this project.

When implementing extraction, comparison, retrieval, or generation logic:

- always prefer validated Pydantic models
- avoid loose untyped dicts where a schema should exist
- preserve room for extension
- keep field names explicit and stable

Important:

- extracted fields should distinguish required vs preferred where relevant
- preserve raw extracted evidence when useful
- do not flatten everything into one score too early

## Matching Logic Rules

Matching should remain explainable and evidence-backed.

Typical output includes:

- overall score
- dimension scores
- required and preferred matches
- strengths
- gaps
- blocker flags
- explanations
- evidence spans
- additive adaptation metadata when relevant

Important distinctions must stay visible:

- missing skill vs missing evidence
- required vs preferred requirements
- score vs blocker severity

## Parsing And Generation Expectations

- Supported ingestion inputs are text, `.txt`, `.pdf`, and `.docx`.
- File handling must stay bounded and safe.
- Parse responses must surface warnings, unsupported segments, and parser confidence.
- Rewrite, interview-prep, interview-simulation, and learning-plan outputs must not invent experience, seniority, metrics, or missing tools.
- Any richer generated output must remain grounded in evidence already present in the resume or JD.

## Candidate Context, Retrieval, And Semantic Rules

- Candidate profile memory must remain request-scoped and auditable by default.
- Retrieval should stay lightweight and explicit.
- Separate indexing, retrieval, and answer generation concerns even when the retrieval layer is simple.
- Use retrieval only where it materially improves grounding, consistency, or recommendation quality.
- Semantic hints must remain additive and must not silently rewrite deterministic scores or blocker flags.

## Evaluation Expectations

Evaluation is a first-class concern in this repository.

Any important new logic should be testable and, where practical, evaluable offline.

Prefer adding:

- unit tests for deterministic logic
- small gold examples for extraction and matching
- evaluation scripts for scoring consistency, comparison stability, and recommendation grounding
- regression tests for bug fixes

The current checked-in evaluation layer covers:

- match benchmarks
- extraction benchmarks
- multi-resume comparison scenarios
- recommendation acceptance scenarios
- baseline reports
- snapshot-capable artifact output

Do not rely only on subjective eyeballing.

## Testing Expectations

For non-trivial code changes, add tests.

At minimum:

- normal-case test
- edge-case test
- invalid-input or failure-case test when relevant

Preferred layout:

- `tests/unit/` for narrow logic
- `tests/integration/` for module interactions

Do not merge logic changes without reasonable test coverage unless explicitly instructed.

## Safe Handling Of Resume And JD Content

This repository may handle personal and career-related documents.

Default rules:

- prefer sanitized sample data
- avoid exposing full sensitive personal data in logs
- avoid inventing claims about a candidate
- present outputs as advisory, not authoritative hiring decisions

If implementing UI or output templates:

- avoid phrasing that implies guaranteed hiring outcomes
- avoid biased or overly certain language

## How To Work On Tasks

When implementing a task, follow this sequence:

1. understand the exact scope
2. inspect related schemas and existing module boundaries
3. choose the narrowest clean implementation
4. implement only what is necessary
5. add or update tests
6. make sure the code is easy to review
7. update docs when public behavior changes

If the task is underspecified:

- make the smallest reasonable choice
- avoid expanding scope unnecessarily
- do not redesign unrelated modules

## Change Scope Discipline

Unless explicitly requested, do not:

- rename large parts of the codebase
- introduce major new dependencies
- refactor unrelated modules
- rewrite working code for style alone
- add a frontend
- add multi-agent orchestration
- add persistence complexity beyond project needs

Prefer targeted changes over sweeping rewrites.

## Review Checklist

Before calling work complete, verify:

- correctness
- schema alignment
- evidence traceability
- thin route boundaries
- adequate tests
- docs updated if public behavior changed
- no hidden architectural drift toward retrieval or multi-agent complexity

## Final Rule

This repository values:

- practical usefulness
- engineering clarity
- explainable outputs
- measured iteration

Build it as a strong portfolio-quality AI backend, not just a prompt demo.
