# Milestone Task Breakdown for CareerFit Agent

## Summary

Start from the existing project shape in [`docs/ARCHITECTURE.md`](</e:/AI/CareerFit-Agent-Project/docs/ARCHITECTURE.md:1>), but refine it for execution:

- keep Milestone 1 tightly locked to the backend-only MVP defined in [`docs/ROADMAP.md`](</e:/AI/CareerFit-Agent-Project/docs/ROADMAP.md:1>) and [`docs/DECISIONS.md`](</e:/AI/CareerFit-Agent-Project/docs/DECISIONS.md:1>)
- split the old "usable MVP" phase into ingestion/extraction first and generation features second
- make developer workflow infrastructure explicit from the start so implementation stays repeatable and reviewable

The build order should be:
1. developer workflow foundation
2. deterministic backend core
3. ingestion and extraction hardening
4. grounded generation workflows
5. portfolio-grade depth and evaluation
6. advanced agent-assisted features

## Developer Workflow Layer

This layer starts immediately and supports Milestone 1 onward.

Core tasks:
- Create the repo skeleton for `app/`, `tests/`, `data/`, and `docs/`.
- Define baseline config and dependency management for Python 3.11, FastAPI, Pydantic v2, and pytest.
- Lock the sample data layout for `data/samples/` and `data/eval/`.
- Add a test harness structure for unit and integration tests.
- Add linting and formatting configuration early so new code follows one style.
- Record PR conventions aligned to `docs/CODE_REVIEW.md`, including small PR scope, schema updates, fixture updates, and test expectations.
- Make the local developer path obvious: install, run app, run tests, inspect sample fixtures.

Completion signal:
- A new contributor can understand the repo shape, run the baseline checks, and add code without inventing project structure.

## Milestone Tasks

### Milestone 1: Foundation / Backend MVP

Goal: ship a narrow, explainable text-to-JSON matching service against deterministic fixtures only.

Scope guardrails:
- parsing target is limited to sanitized text fixtures, not arbitrary resumes or JDs
- schema coverage is intentionally constrained to the minimum fields needed for baseline matching
- no PDF/DOCX, URLs, frontend, vector store, retrieval, or multi-agent orchestration

Constrained schema coverage target:
- resume: `candidate_name`, `summary`, `skills`, `experience_items`, `project_items`, `education_items`, `evidence_spans`
- JD: `job_title`, `company`, `required_requirements`, `preferred_requirements`, `education_requirements`, `seniority_hint`, `domain_hint`, `evidence_spans`
- output: `MatchResult`, `GapItem`, required/preferred match groups, blocker flags, explanations, evidence spans

Core tasks:
- Create the Python 3.11 + FastAPI + Pydantic v2 project skeleton.
- Define the core contracts: `ResumeSchema`, `JDSchema`, `EvidenceSpan`, `GapItem`, `MatchResult`.
- Implement deterministic text normalization for resume and JD fixture inputs.
- Implement constrained section detection for summary, skills, experience, projects, education, required, preferred, and education requirement sections.
- Implement schema extraction from normalized fixture text into validated Pydantic models.
- Implement requirement classification into required vs preferred.
- Implement the weighted rule-based baseline scorer using the locked weights.
- Implement blocker detection for missing required skills, seniority mismatch, and unsupported claims.
- Implement evidence linking so every match/gap explanation points to source text.
- Add one `POST /match` endpoint returning structured JSON only.
- Add starter sample fixtures and gold expectations for strong, partial, and poor fit cases.
- Add unit tests for required match, preferred match, missing evidence, and blocker behavior.
- Add a basic `GET /health` endpoint only if needed for service sanity checks.

Public interfaces introduced:
- `POST /match`
- text input contract for resume text + JD text
- structured `MatchResult` JSON output

Completion signal:
- The service can accept deterministic text fixtures and return stable, explainable, evidence-backed match results over the constrained schema target.

### Milestone 2: Ingestion and Extraction

Goal: move from fixture-only parsing to more realistic document ingestion and schema extraction.

Core tasks:
- Add dedicated parsing endpoints for resume and JD schema extraction.
- Add PDF/DOCX ingestion and parsing with bounded error handling and parser warnings.
- Preserve raw text, cleaned text, and parser confidence metadata.
- Improve normalization for bullets, headers, noisy formatting, and missing sections.
- Expand schema extraction coverage beyond the Milestone 1 constrained target where needed.
- Improve skill normalization and requirement classification robustness.
- Add integration tests covering file-to-schema and text-to-schema flows.
- Add API examples and docs for the parsing endpoints and ingestion behaviors.

Public interfaces added:
- `POST /parse/resume`
- `POST /parse/jd`

Completion signal:
- A user can submit text or supported files and reliably receive structured resume and JD schemas with bounded parsing behavior and reviewable warnings.

### Milestone 3: Grounded Generation Workflows

Goal: add practical generation features only after extraction and matching are trustworthy.

Core tasks:
- Expand matching explanations into strengths, weak matches, and prioritized gaps.
- Add resume rewrite support grounded in extracted evidence.
- Add interview-prep output grounded in JD responsibilities and candidate gaps.
- Introduce a lightweight orchestrator that sequences extract -> score -> diagnose -> improve.
- Add schema validation and evidence checks for generated outputs.
- Add integration tests covering parse-to-match-to-generation workflows.
- Add API examples and docs for generation endpoints.
- Add a minimal UI only after backend contracts are stable.

Public interfaces added:
- `POST /rewrite`
- `POST /interview-prep`

Completion signal:
- A user can submit a resume/JD, inspect structured fit output, and receive grounded rewrite and interview-prep guidance without losing evidence traceability.

### Milestone 4: Strong Portfolio Version

Goal: make the system demonstrably robust, reviewable, and portfolio-grade.

Core tasks:
- Expand the gold dataset beyond the first 3 pairs into a larger annotated benchmark set.
- Add offline evaluation scripts for extraction accuracy, match precision/recall, score consistency, and explanation usefulness.
- Add richer evidence tracing across skills, experience, projects, and education.
- Support multiple resume versions for the same candidate and compare fit across them.
- Add company/role adaptation logic without breaking the core schemas.
- Add result versioning or comparable output snapshots for regression review.
- Add analytics/reporting views for benchmark and model/rule comparisons.
- Add regression tests for scoring changes and fixture-based acceptance checks.
- Tighten docs for architecture, decisions, and scoring rationale as the system grows.

Public interfaces added or expanded:
- evaluation/report artifacts
- multi-resume comparison inputs/outputs
- stronger evidence and explanation fields in result contracts

Completion signal:
- The project has clear benchmark coverage, regression protection, and a polished story for explainable matching quality.

### Milestone 5: Advanced Agent Features

Goal: add higher-level career workflow assistance on top of a trustworthy core.

Core tasks:
- Add learning plan generation tied to explicit skill gaps and blockers.
- Add interview simulation alignment using matched responsibilities and weak areas.
- Add cross-JD comparison to rank opportunities against one candidate profile.
- Add profile memory or reusable candidate context with clear boundaries and auditability.
- Add retrieval only if it materially improves grounding for recommendations.
- Add optional semantic matching only after the deterministic baseline is benchmarked.
- Add orchestration upgrades only where simple module sequencing is no longer enough.
- Add safeguards so advanced outputs never bypass evidence or schema validation.
- Add evaluation for recommendation usefulness and hallucination rate.

Public interfaces added or expanded:
- learning-plan outputs
- cross-JD comparison outputs
- optional retrieval/semantic modules behind explicit contracts

Completion signal:
- The system supports multi-step career assistance without turning into opaque or hard-to-review agent sprawl.

## Test Plan

Each milestone should be considered complete only if its task set is backed by the right tests.

Developer workflow layer:
- repo bootstrap verification
- config loading checks
- sample data path and fixture loading tests
- test harness sanity checks
- lint/format commands documented and runnable

Milestone 1:
- schema validation tests
- deterministic parsing/normalization tests against the constrained fixture format
- required vs preferred matching tests
- missing skill vs missing evidence tests
- blocker flag tests
- `/match` endpoint tests

Milestone 2:
- PDF/DOCX parser tests on clean and messy inputs
- parse endpoint tests
- normalization regression tests for noisy documents
- schema extraction coverage tests for added fields

Milestone 3:
- rewrite and interview-prep schema/output validation tests
- evidence presence tests for generated outputs
- end-to-end integration tests from parse to grounded generation

Milestone 4:
- fixture-based regression suite
- benchmark runner checks
- score consistency tests across sample sets
- multi-resume comparison tests

Milestone 5:
- recommendation grounding tests
- retrieval/semantic fallback tests if added
- hallucination/unsupported-claim guardrail tests
- cross-JD comparison and learning-plan acceptance tests

## Assumptions

- Milestone 1 remains strictly backend-only with no frontend, no vector store, and no multi-agent orchestration.
- Milestone 1 parsing is intentionally narrow and only expected to work on deterministic, sanitized fixture layouts.
- The first coding PR stays inside the narrow boundary already locked in `ROADMAP.md`.
- Later milestones may introduce UI, retrieval, and richer orchestration, but only after the deterministic backend core is stable and benchmarked.
- All milestones keep the same project values: schema-first, explainable, evidence-linked, modular, and evaluation-driven.
