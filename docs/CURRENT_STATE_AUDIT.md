# Current State Audit

Audit date: 2026-04-28

Update note: 2026-04-29 cleanup reconciled the audit with the existing M6 foundation schemas, Dockerfile, and CI workflow. A later 2026-04-29 M6 foundation pass added the internal `WorkflowResult` schema. A subsequent M7 foundation pass added explicit image/scanned-PDF needs-OCR diagnostics, OCR adapter contracts, multimodal fixtures, and a separate multimodal ingestion evaluation runner. The 2026-05-01 M8 pass exposed optional public `workflow_trace` metadata on selected responses and added frontend view-model documentation. The 2026-05-02 neat pass reconciled README and audit status with the current M8 trace contract. The 2026-05-03 M10 release pass added deployment, demo, API walkthrough, release-note, environment-example, dependency-split, Docker Compose, and CI Docker-build packaging. Baseline artifacts were not regenerated.

Scope: repository inspection, documentation cleanup, internal schema foundation updates, optional advisory LLM boundaries, and release-readiness packaging. Verification updated on 2026-05-03 after M10 with `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`, `.\.venv\Scripts\python.exe -m ruff check app tests`, `.\.venv\Scripts\python.exe -m pytest -q` passing with 106 tests, local `uvicorn` startup, `/health`, `/match` using `docs/examples/match_request.json`, and all five offline evaluation runners passing. Docker was not executable in the local sandbox because the `docker` command is not installed, so Dockerfile, Compose, and CI Docker-build changes were statically verified.

## 1. Repository Overview

### Current folder structure

- `app/`: FastAPI backend package.
  - `app/main.py`: application factory and router registration.
  - `app/api/routes/`: HTTP route layer for health, parsing, matching, generation, comparison, and career workflows.
  - `app/schemas/`: explicit Pydantic contracts for resume, JD, parsing, matching, generation, comparison, career helper outputs, additive workflow trace metadata, and document normalization.
  - `app/services/`: deterministic business logic for ingestion, normalization, extraction, matching, generation rendering, comparison, retrieval, semantic hints, candidate profile memory, and additive workflow trace construction.
  - `app/services/ingestion/`: bounded file ingestion for `.txt`, `.pdf`, and `.docx`.
  - `app/services/generation/`: deterministic grounded generation renderers and guardrails.
  - `app/evaluation/`: offline benchmark runners and artifact writer.
  - `app/core/config.py`: static config for section headers, ingestion limits, match weights, and capability keywords.
- `tests/`: 25 unit test files and 5 integration test files.
- `data/samples/`: small canonical sample resumes and job descriptions.
- `data/eval/`: expected outputs, benchmark manifests, comparison manifests, recommendation manifests, and baseline reports.
- `data/eval/reports/baseline/`: checked-in `benchmark_report.json`, `extraction_report.json`, `comparison_report.json`, `recommendation_report.json`, `artifact_manifest.json`, and `summary.md`.
- `dataset/`: cleaned resume/JD corpus and dataset cleaning script.
  - `dataset/cleaning_report.json` reports 48 JD samples, 24 JD categories, 2,484 resume rows, and 1,767 usable resume rows.
  - `dataset/resume_cleaned/` and `dataset/jd_cleaned/` each contain 24 category folders.
- `docs/`: roadmap, decisions, architecture, API docs, evaluation docs, and review guidance.
- `.env.example`, `docker-compose.yml`, `Dockerfile`, and `.github/workflows/ci.yml`: reviewer-facing runtime configuration, container, and CI packaging.

### Main application entry points

- `app/main.py:create_app()` builds `FastAPI(title="CareerFit Agent", version="0.1.0")` and includes routers from:
  - `app/api/routes/health.py`
  - `app/api/routes/match.py`
  - `app/api/routes/parse.py`
  - `app/api/routes/generation.py`
  - `app/api/routes/comparison.py`
  - `app/api/routes/career.py`
- Runtime command documented in `README.md`: `uvicorn app.main:app --reload`.
- Local test command verified in this audit: `.\.venv\Scripts\python.exe -m pytest -q`.

### Existing backend/API structure

Current public endpoints:

- `GET /health`
- `POST /match`
- `POST /parse/resume`
- `POST /parse/jd`
- `POST /rewrite`
- `POST /interview-prep`
- `POST /interview-sim`
- `POST /learning-plan`
- `POST /compare/resumes`
- `POST /profile-memory`
- `POST /retrieve/evidence`
- `POST /semantic/match`
- `POST /compare/jobs`
- `POST /llm/advice`

Routes are mostly thin. For example, `app/api/routes/match.py:match_resume_to_job()` delegates to `app/services/matching_service.py:match_resume_to_jd()`, and `app/api/routes/generation.py` delegates to `run_grounded_*_flow()` functions in `app/services/orchestration_service.py`.

### Existing data/evaluation/report structure

- `data/eval/benchmark_manifest.json`: 15 match benchmark cases.
- `data/eval/extraction_manifest.json`: 13 extraction benchmark cases.
- `data/eval/comparison_manifest.json`: 3 multi-resume comparison scenarios.
- `data/eval/recommendation_manifest.json`: 3 recommendation acceptance cases.
- `data/eval/multimodal_manifest.json`: 3 multimodal ingestion-quality cases for needs-OCR diagnostics, including one clean embedded-text PDF case.
- `app/evaluation/benchmark_runner.py`: match metrics.
- `app/evaluation/extraction_runner.py`: extraction metrics.
- `app/evaluation/comparison_runner.py`: multi-resume ranking metrics.
- `app/evaluation/recommendation_runner.py`: recommendation usefulness, grounding, blocker guardrails, and hallucination checks.
- `app/evaluation/artifact_writer.py:write_evaluation_artifacts()` writes the baseline/snapshot artifact bundle.

### Key dependencies and runtime assumptions

Dependencies are small and backend-focused:

- Runtime: `fastapi`, `pydantic`, `uvicorn`, `pypdf`, `python-docx`, `python-multipart`.
- Dev/test: `pytest`, `httpx`, `ruff`.
- Python requirement: `>=3.11`.

Runtime assumptions:

- No database.
- No vector store.
- No LLM provider SDK.
- Optional LLM advisory settings are environment-backed and documented in `.env.example`; deterministic local use requires no secrets.
- A backend `Dockerfile` is present for the current FastAPI app and runs runtime dependencies only.
- `docker-compose.yml` runs the API service with a health check.
- `.github/workflows/ci.yml` runs Ruff, pytest, and Docker image build verification on Python 3.11.
- Upload limit is static in `app/core/config.py:MAX_INGESTION_FILE_BYTES` at 5 MB.

## 2. Current Feature Inventory

### Resume/JD input handling

- Text inputs are supported by `app/services/ingestion/file_ingestion.py:ingest_text()`.
- File inputs are supported by `ingest_file()` for `.txt`, `.pdf`, and `.docx`.
- `app/api/routes/parse.py:_read_parse_request()` accepts JSON text, multipart `file`, or multipart `text`.
- `_read_upload_content()` reads upload chunks in 64 KB increments and raises HTTP 413 when the 5 MB limit is exceeded.

Current limitation: image inputs and scanned PDFs now produce explicit needs-OCR diagnostics, low parser confidence, and unsupported segment reasons. They still do not run OCR or produce extracted text. `_read_pdf()` uses `pypdf.PdfReader.extract_text()` without OCR or layout reconstruction.

### Text parsing or normalization

- `app/services/text_normalizer.py:normalize_text()` and `normalize_text_with_diagnostics()` normalize bullets, headers, whitespace, and document-specific section behavior.
- `app/services/extraction_service.py` owns deterministic section splitting and schema extraction.
- `app/services/parse_service.py` wraps ingestion, normalization, extraction, parser confidence, warnings, and unsupported segments into parse response contracts.

### Requirement extraction

- Resume extraction: `extract_resume_schema()`, `analyze_resume_text()`.
- JD extraction: `extract_jd_schema()`, `analyze_jd_text()`.
- Requirement extraction and classification live in private helpers such as `_extract_requirements()`, `_derive_requirement_type()`, `_extract_year_requirement()`, `_infer_seniority_hint()`, and `_infer_domain_hint()` in `app/services/extraction_service.py`.

### Evidence matching

- `app/services/matching_service.py:match_schemas()` is the core deterministic matcher.
- Requirement matching is split into `_evaluate_years_requirement()`, `_evaluate_education_requirement()`, and `_evaluate_capability_requirement()`.
- Evidence spans use `app/schemas/common.py:EvidenceSpan`.
- `MatchResult.evidence_spans` and `MatchResult.evidence_summary` expose evidence traceability counts and source coverage.
- Selected responses now also expose optional `workflow_trace` metadata for execution traceability.

### Scoring

- Weights live in `app/core/config.py:MATCH_WEIGHTS`:
  - skills: 30
  - experience: 30
  - projects: 20
  - domain fit: 10
  - education: 10
- `app/services/matching_service.py:_build_dimension_scores()` computes dimension scores.
- `_weighted_overall_score()` computes the final score.
- `_status_value()` maps `matched`, `partial`, `unsupported`, and missing statuses into score contribution.

### Recommendation generation

Current "generation" is deterministic rendering, not LLM generation.

- Shared orchestration: `app/services/orchestration_service.py:build_grounded_context()`.
- Resume rewrite: `app/services/generation/rewrite_service.py:render_rewrite_response()`.
- Interview prep: `app/services/generation/interview_prep_service.py:render_interview_prep_response()`.
- Interview simulation: `app/services/generation/interview_simulation_service.py:render_interview_simulation_response()`.
- Learning plan: `app/services/generation/learning_plan_service.py:render_learning_plan_response()`.
- Cross-JD career recommendations: `app/services/opportunity_comparison_service.py:compare_candidate_to_jobs()`.

### Blocker/guardrail handling

- `app/schemas/match.py:BlockerFlags` exposes:
  - `missing_required_skills`
  - `seniority_mismatch`
  - `unsupported_claims`
- `app/services/generation/generation_guardrails.py:build_generation_gate()` converts parser confidence, blockers, and evidence risk into `GenerationGate`.
- Generation responses include `generation_warnings` and `gating`.
- Learning-plan outputs include `blocker_cautions`.

### Evaluation metrics and benchmark reports

Checked-in baseline metrics:

- Match benchmark: 15 cases, fit label accuracy 1.0, blocker flag accuracy 1.0, required match recall 1.0, preferred match recall 1.0, top-gap coverage 1.0.
- Extraction benchmark: 13 cases, confidence accuracy 1.0, field expectation accuracy 1.0, unsupported segment coverage 1.0.
- Comparison benchmark: 3 scenarios, ranking accuracy 1.0, fit label accuracy 1.0, low-confidence ordering accuracy 1.0.
- Recommendation benchmark: 3 cases, usefulness accuracy 1.0, grounding accuracy 1.0, blocker guardrail accuracy 1.0, hallucination rate 0.0.

## 3. Architecture Assessment

### Where core business logic currently lives

- Ingestion: `app/services/ingestion/file_ingestion.py`.
- Normalization: `app/services/text_normalizer.py`.
- Extraction: `app/services/extraction_service.py`.
- Parse response assembly: `app/services/parse_service.py`.
- Matching/scoring/blockers: `app/services/matching_service.py`.
- Adaptation metadata: `app/services/adaptation_service.py`.
- Multi-resume comparison: `app/services/comparison_service.py`.
- Cross-JD comparison: `app/services/opportunity_comparison_service.py`.
- Candidate profile memory: `app/services/candidate_profile_service.py`.
- Retrieval helper: `app/services/retrieval_service.py`.
- Semantic hints: `app/services/semantic_matching_service.py`.
- Grounded generation: `app/services/orchestration_service.py` plus `app/services/generation/`.

The route layer is not carrying much business logic, which is a good foundation.

### Whether the current structure already resembles agents

It resembles a capability/service architecture, not an agent architecture.

The strongest agent-like modules are:

- parser/extractor capability: `parse_service.py` plus `extraction_service.py`
- matcher capability: `matching_service.py`
- recommendation capability: generation service modules
- evidence capability: `retrieval_service.py`
- semantic hint capability: `semantic_matching_service.py`
- career comparison capability: `opportunity_comparison_service.py`

However, none of these own independent planning, tool selection, memory lifecycle, retry policy, or conversational state. They are deterministic functions behind schemas.

### Whether there is an orchestrator/workflow layer

Yes. `app/services/orchestration_service.py` is the current workflow layer for grounded generation. It coordinates:

1. parse resume
2. parse JD
3. match schemas
4. build guardrail gate
5. collect evidence
6. render a bounded output

`app/services/opportunity_comparison_service.py` is a second workflow layer for cross-JD comparison. It resolves candidate profile memory, parses each JD, matches, retrieves evidence, adds semantic hints, generates next steps, ranks opportunities, and attaches additive workflow trace metadata.

### Whether input/output schemas are explicit

Yes. The project is schema-first:

- parse schemas: `app/schemas/parse.py`
- resume/JD schemas: `app/schemas/resume.py`, `app/schemas/jd.py`
- match schemas: `app/schemas/match.py`
- generation schemas: `app/schemas/generation.py`
- comparison schemas: `app/schemas/comparison.py`
- career helper schemas: `app/schemas/career.py`

### Whether deterministic logic is separated from generative/LLM logic

Yes, mostly. Deterministic critical-path logic lives in extraction, matching, scoring, adaptation, retrieval, and semantic helper services. Generation modules are also deterministic template renderers today, not LLM calls.

No actual LLM boundary exists yet. Before adding LLM agents, the project needs a clear separation between:

- deterministic facts and scores
- prompt/LLM inputs
- LLM outputs
- post-generation validation
- audit trail and trace IDs

### Whether the current design can scale into a multi-agent architecture

It can scale, but not by directly renaming every service into an agent. The code already has good service boundaries and explicit schemas. The next step should be standardizing workflow contracts and traces before adding autonomous behavior.

Risks if multi-agent work is added too early:

- score contract drift if agents rewrite deterministic match meaning
- latency increases with no async task model
- duplicated validation logic between services and agents
- harder benchmark attribution if each agent changes outputs without structured traces

## 4. Evaluation & Benchmark Assessment

### Existing benchmark cases

- Match: 15 cases in `data/eval/benchmark_manifest.json`, including strong, partial, poor, messy parsing, cleaned engineering/IT/accounting/healthcare samples, cross-domain comparisons, and responsibility-heavy JDs.
- Extraction: 13 cases in `data/eval/extraction_manifest.json`, including strong, messy, low-confidence, cleaned dataset resume/JD, accounting, healthcare, and responsibility-heavy JD samples.
- Comparison: 3 scenarios in `data/eval/comparison_manifest.json`, covering backend variants, responsibility variants, and low-confidence ranking.
- Recommendation: 3 cases in `data/eval/recommendation_manifest.json`, covering learning plan and interview simulation workflows.

### Existing metrics

- `app/evaluation/benchmark_runner.py` tracks fit label accuracy, blocker flag accuracy, required match recall, preferred match recall, and top-gap coverage.
- `app/evaluation/extraction_runner.py` tracks confidence accuracy, field expectation accuracy, and unsupported segment coverage.
- `app/evaluation/comparison_runner.py` tracks ranking accuracy, fit label accuracy, and low-confidence ordering accuracy.
- `app/evaluation/recommendation_runner.py` tracks usefulness accuracy, grounding accuracy, blocker guardrail accuracy, and hallucination rate.

### How evaluation artifacts are generated

- Individual runners print JSON reports.
- `app/evaluation/artifact_writer.py:write_evaluation_artifacts()` runs all four benchmark families and writes JSON plus `summary.md`.
- Baseline artifacts live under `data/eval/reports/baseline/`.
- Snapshot artifacts are supported under `data/eval/reports/snapshots/<label>/` when using `--snapshot-label`.

### Whether the benchmark is strong enough for regression testing

For the current deterministic backend, yes. The benchmark has enough coverage to catch obvious regressions in:

- parser confidence
- fit labels
- blocker flags
- required/preferred match recall
- ranking order
- recommendation grounding

For the next platform stage, it is not yet strong enough. It does not cover:

- scanned PDFs or images
- OCR confidence and layout loss
- multimodal normalization into a shared document schema
- LLM output validation
- multi-agent trace correctness
- latency/timeouts
- partial workflow failures
- frontend task-status behavior

### Evaluation gaps after M7 multimodal foundation

Before adding OCR runtime support:

- Add golden PDF/DOCX fixtures that include tables, two-column layouts, and extraction failures.
- M7 added scanned-PDF/image fixtures with expected "unsupported/needs OCR" diagnostics and a clean embedded-text PDF fixture that should not need OCR.
- M7 added multimodal ingestion metrics for needs-OCR detection correctness, diagnostic coverage, unsupported-reason coverage, and low-confidence guardrails.
- Still add text extraction coverage, OCR confidence threshold behavior, page-level warning coverage, and normalized schema completeness once OCR exists.
- Add failure-case tests for corrupt image files, password/encrypted PDFs, very large files, and files with no text.
- Add report fields that separate parser quality from matcher quality. A bad OCR parse should not look like a matcher regression.

## 5. Code Quality Assessment

### Duplicated logic

Baseline cleanup after this audit resolved the duplicated fit-label derivation through `app/services/fit_label.py` and the duplicated benchmark ratio helper through `app/evaluation/utils.py`.

Tokenization/canonicalization still appears in multiple places:

- `app/services/adaptation_service.py:_tokenize()`
- `app/services/matching_service.py:_detect_capabilities()` uses related keyword matching.
- retrieval and semantic matching now share `app/services/tokenization.py:tokenize_keywords()`.

The adaptation tokenization path is intentionally deferred because it preserves ordered list semantics and one-character tokens, unlike the set-based retrieval/semantic helper.
- Generation service modules repeat patterns for choosing top gaps, evidence, cautions, and summary text.

### Over-coupled modules

- `app/services/extraction_service.py` is large and owns section splitting, resume extraction, JD extraction, requirement typing, seniority/domain inference, diagnostics, span building, and helper normalization.
- `app/services/matching_service.py` is large and owns requirement evaluation, evidence map construction, scoring, blockers, strengths, explanations, evidence summaries, and adaptation injection.
- `app/services/opportunity_comparison_service.py` coordinates candidate memory, JD parsing, matching, learning plan generation, retrieval, semantic hints, and ranking in one function.
- `app/evaluation/artifact_writer.py` owns running benchmarks, writing artifacts, generating summaries, and snapshot comparison.

### Weak abstraction boundaries

- Fit labels are derived outside the core match schema instead of being a single shared utility or schema field.
- Capability definitions live in `app/core/config.py:CAPABILITY_PATTERNS`, while related semantic aliasing lives elsewhere.
- Selected downstream match, comparison, retrieval, semantic, and cross-JD ranking responses expose optional workflow trace metadata.
- Retrieval and semantic helper behavior is additive by intent, but the boundary is conventional rather than enforced by a formal contract.

### Missing tests

Current test suite is healthy for existing features: 106 passed on 2026-05-03 after the M10 release-packaging pass. The M10 release pass keeps test coverage focused on existing behavior and verifies release packaging with Ruff, pytest, local startup, API walkthrough, and static Docker/CI checks.

Gaps before the next milestone:

- Image and scanned-PDF needs-OCR tests now exist for the M7 foundation.
- No real OCR-runtime tests.
- No async task/progress tests.
- Workflow trace and document schema validation tests exist in `tests/unit/test_workflow_document_schemas.py`.
- No tests for agent registry or agent lifecycle because those abstractions do not exist.
- Docker and CI config exist, and M10 adds Docker image build coverage to the CI workflow.
- Limited benchmark size for recommendation cases: only 3 cases.

### Hidden assumptions

- Capability detection is constrained to a small fixed vocabulary in `app/core/config.py:CAPABILITY_PATTERNS`.
- File type support is extension-driven in `ingest_file()`.
- PDF parsing assumes extractable embedded text; scanned PDFs degrade into empty text warnings.
- DOCX table text is intentionally ignored and only reported as an info warning.
- Candidate profile memory is request-scoped and non-persistent.
- Semantic matching is heuristic-only and additive.
- The current docs mark M5 as completed. Baseline cleanup resolves the next-plan naming by making agent standardization M6.

### Error-handling gaps

- Parse upload size handling is good, but there is no malware scanning, MIME validation beyond filename/media metadata, or page-count limit for PDFs.
- OCR/image input has an explicit needs-OCR failure path, but no real OCR runtime or image text extraction.
- No global exception handler or standardized API error envelope exists.
- No timeout/cancellation/progress model exists for future long-running multimodal or agent workflows.

### Naming or structure issues

- The repository name and docs still use "CareerFit Agent", but the implemented architecture is explicitly not agentic yet.
- API and evaluation docs now use the same Bash-style repo venv interpreter examples as `README.md`.
- `docs/ROADMAP.md` is historical and can be misread as current scope unless readers notice the note.
- `app/services/generation/` contains deterministic renderers; "generation" may later become ambiguous once LLM-backed generation is introduced.

### Files doing too much

Largest/highest-risk files by current size:

- `app/services/extraction_service.py`
- `app/services/matching_service.py`
- `app/services/generation/learning_plan_service.py`
- `app/services/generation/rewrite_service.py`
- `app/services/generation/interview_prep_service.py`
- `app/evaluation/artifact_writer.py`
- `app/evaluation/benchmark_runner.py`
- `app/schemas/generation.py`

These do not need immediate refactors before small feature work, but they should be split before adding OCR, LLM agents, or a larger frontend workflow/status surface.

## 6. Readiness for Agent Standardization

### Existing modules/functions that could become agents

Candidate agent boundaries if the next milestone intentionally introduces agents:

- `IngestionAgent`: wraps `ingest_text()`, `ingest_file()`, and future OCR ingestion.
- `ParsingAgent`: wraps `parse_resume_text()`, `parse_jd_text()`, `parse_resume_file()`, and `parse_jd_file()`.
- `MatchingAgent`: wraps `match_schemas()` and emits deterministic score, blockers, gaps, and evidence summary.
- `EvidenceAgent`: wraps `retrieve_candidate_evidence()` and future vector/OCR page evidence retrieval.
- `RecommendationAgent`: wraps deterministic learning plan, interview simulation, interview prep, and rewrite renderers, later allowing LLM generation behind strict validation.
- `OpportunityComparisonAgent`: wraps `compare_candidate_to_jobs()`.
- `ReviewAgent` or `GuardrailAgent`: wraps `build_generation_gate()` plus output validation.

### Suggested agent boundaries

Agents should align to explicit input/output contracts rather than files:

- Ingestion: raw bytes/text -> normalized `DocumentInput`/`IngestedDocument`.
- Parsing: normalized document -> `ResumeParseResponse` or `JDParseResponse`.
- Matching: parsed resume + parsed JD -> `MatchResult`.
- Evidence retrieval: candidate profile + query -> `EvidenceRetrievalResponse`.
- Recommendation: grounded context -> validated recommendation response.
- Review/guardrail: proposed output + evidence registry + gate -> validation result.

### Suggested input and output schemas

Schemas to preserve or add before real agents:

- Implemented: `WorkflowTrace` with ordered steps, service name, schema versions, duration, warnings, and error status.
- Implemented: `WorkflowResult` with status, output metadata, optional trace, confidence, evidence references, warnings, and recoverable errors.
- Implemented: `DocumentInput`, `DocumentSegment`, and `NormalizedDocument` for source metadata, normalized text, segments, diagnostics, confidence, and warnings.
- Pending: `WorkflowRequest` with workflow id, input documents, options, and trace settings.
- Pending: `AgentRunStatus` with queued/running/succeeded/failed/cancelled states for future frontend polling.

### Modules that should remain deterministic utilities

Do not turn these into LLM agents:

- `app/core/config.py`
- `app/services/text_normalizer.py`
- scoring helpers in `app/services/matching_service.py`
- `app/services/adaptation_service.py`
- schema models under `app/schemas/`
- benchmark runners under `app/evaluation/`
- file readers inside `app/services/ingestion/file_ingestion.py`

These should remain deterministic and testable.

### Whether BaseAgent and AgentRegistry are needed now

Not yet for the current codebase. There are no LLM calls, no autonomous agent loop, no background execution, and no dynamic agent discovery requirement.

Recommended sequence:

1. Preserve the implemented workflow trace schemas and add a shared result envelope only when it can stay additive.
2. Extract shared utilities for fit-label derivation, tokenization, and benchmark ratio handling.
3. Add a small `BaseAgent` only when at least two real agent implementations need common lifecycle behavior.
4. Add `AgentRegistry` only when workflows need runtime selection between multiple interchangeable agents.

Adding `BaseAgent` and `AgentRegistry` immediately would mostly rename services without solving current risks.

## 7. Readiness for Multimodal Input

### Current ingestion capability

Implemented:

- direct text input
- `.txt`
- `.pdf` with embedded text extraction via `pypdf`
- `.docx` paragraph extraction via `python-docx`
- parser warnings and confidence metadata
- bounded upload size
- image extension detection with explicit `image_requires_ocr`
- scanned-PDF detection with explicit `pdf_scanned_needs_ocr`

Not implemented:

- OCR
- scanned PDF OCR
- page-level layout extraction
- table extraction from DOCX
- MIME sniffing
- background processing for long-running files

### What is missing for PDF, DOCX, image, and OCR support

PDF:

- page-count limits
- scanned-PDF detection as a first-class diagnostic
- OCR fallback strategy
- page-level spans
- layout/table handling

DOCX:

- table extraction
- header/footer extraction
- embedded image handling
- richer paragraph/list style handling

Image/OCR:

- image file validation
- OCR provider/library decision
- OCR confidence schema
- page/region-level evidence spans
- failure-mode tests
- latency and cancellation model

### Recommended ingestion package structure

Keep existing `app/services/ingestion/`, but split by responsibility before adding OCR:

- `app/services/ingestion/models.py`: `IngestedDocument`, future `NormalizedDocument`, page/segment models.
- `app/services/ingestion/text_reader.py`: direct text and TXT handling.
- `app/services/ingestion/pdf_reader.py`: embedded-text PDF parsing and scanned-PDF detection.
- `app/services/ingestion/docx_reader.py`: DOCX paragraph/table extraction.
- `app/services/ingestion/image_reader.py`: image metadata validation and OCR handoff.
- `app/services/ingestion/ocr.py`: OCR adapter interface, not a heavy dependency by default.
- `app/services/ingestion/errors.py`: typed ingestion errors mapped by routes.

### Risks of adding OCR dependencies too early

- Heavy native dependencies may complicate Windows setup.
- OCR can be slow enough to require background jobs and progress tracking.
- OCR output can degrade match quality while appearing as normal text unless confidence is carried through the pipeline.
- Benchmarks may falsely blame matching when the real failure is OCR.
- Docker and CI readiness should come before adopting OCR packages that need system libraries.

### Shared schema recommendation

Normalize every modality into a shared document shape before extraction:

- source metadata: type, filename, media type, page count
- normalized text
- segments with source spans
- extraction/OCR diagnostics
- confidence score and confidence level
- unsupported segments
- original text/bytes reference policy

The existing parse response model is close, but it needs page/region granularity before OCR.

## 8. Readiness for Frontend

### Existing API endpoints

The backend has enough endpoints for a first dashboard:

- health check
- parse resume/JD
- match resume to JD
- rewrite
- interview prep
- interview simulation
- learning plan
- compare multiple resumes
- profile memory
- retrieve evidence
- semantic hints
- compare multiple jobs

### Whether responses are frontend-friendly

Mostly yes. Responses are explicit Pydantic JSON with structured fields, evidence spans, warnings, parser confidence, blockers, and ranking data.

Frontend pain points:

- No common response envelope across endpoints beyond additive `workflow_trace`.
- No async status endpoint.
- No progress model for future long-running parsing/OCR/agent work.
- Some response structures are deeply nested and will require view-model shaping.

### Dashboard data structures needed

Suggested frontend view models:

- `FitSummaryCard`: score, fit label, blockers, confidence, top strengths, top gaps.
- `EvidenceTable`: source, section, text, requirement id, support level.
- `ParseDiagnosticsPanel`: warnings, confidence, unsupported segments.
- `RecommendationPanel`: plan steps, simulation rounds, cautions, evidence used.
- `ComparisonRankingTable`: rank, resume/job id, score, blockers, score delta, parser confidence.
- `WorkflowTraceTimeline`: step, status, duration, warnings, linked output.

### Whether async task status, progress tracking, or workflow trace is needed

For the current deterministic backend, a persistent async task-status model is not required. M8 adds per-response `workflow_trace` metadata for frontend timelines without adding storage.

For multimodal and multi-agent support, yes. OCR, LLM calls, and multi-agent review loops should not be handled as simple synchronous calls only. Add:

- `POST /workflows`
- `GET /workflows/{run_id}`
- `GET /workflows/{run_id}/trace`
- status values: queued, running, succeeded, failed, cancelled
- progress events for ingestion, OCR, parse, match, generate, review

### UX risks caused by multi-agent latency

- Users may not know whether the system is parsing, scoring, waiting on OCR, or waiting on an LLM.
- Long synchronous requests will feel broken without progress states.
- Multiple agents can produce contradictory outputs unless a final review/guardrail step is visible.
- Evidence inspection must stay central; otherwise frontend polish can hide unsupported recommendations.

## 9. Readiness for Deployment

### Dependency management

Good for local development:

- `pyproject.toml` defines package metadata and dependency bounds.
- `requirements.txt` contains runtime dependencies.
- `requirements-dev.txt` includes runtime dependencies plus pytest, httpx, and Ruff for local checks.
- Python 3.11 is explicit.

Remaining dependency-management improvement before a hosted production deployment:

- Add reproducible lock strategy if this will be deployed or demoed by others.

### Environment variables

No environment variables are required for deterministic local use.

Optional LLM advisory settings are documented in `.env.example`:

- `ENABLE_LLM_GENERATION=false`
- `LLM_PROVIDER=openai`
- `LLM_MODEL=gpt-5.4-mini`
- `LLM_TEMPERATURE=0`
- `LLM_MAX_OUTPUT_TOKENS=800`

Secrets such as `OPENAI_API_KEY` or `LLM_API_KEY` should only be set in a
private local environment and should not be committed.

### Docker readiness

Ready for reviewer use. The backend `Dockerfile` installs runtime dependencies only, runs `uvicorn app.main:app` on port 8000, and drops to a non-root user.

`docker-compose.yml` defines the API service, maps port 8000, uses `.env.example`, and includes a `/health` check. Before adding heavy multimodal dependencies, keep the Docker packaging focused on the current backend. OCR should wait until Docker/system-library handling is intentionally designed and tested.

### Local run instructions

README local setup is usable and currently Bash-style:

- create venv
- activate with `source .venv/Scripts/activate`
- install `requirements-dev.txt`
- run tests with `./.venv/Scripts/python.exe -m pytest -q`
- run app with `uvicorn app.main:app --host 127.0.0.1 --port 8000`

M10 adds reviewer-facing `docs/DEPLOYMENT.md`, `docs/DEMO_GUIDE.md`, `docs/API_WALKTHROUGH.md`, `RELEASE_NOTES.md`, and `docs/examples/match_request.json`.

### CI/test readiness

The local test suite is healthy after the M10 release pass: 106 tests passed on 2026-05-03.

CI is ready for reviewer-gate use:

- `.github/workflows/ci.yml` installs `.[dev]`
- CI runs `python -m ruff check app tests`
- CI runs `python -m pytest -q`
- CI runs `docker build -t careerfit-agent:ci .`
- no artifact comparison check

### Remaining deployment limitations

- No hosted production target is configured.
- No API versioning strategy.
- No async/background task model for future OCR/agent workflows.
- No observability/logging/tracing beyond response fields and offline artifacts.

## 10. Release Readiness And Next Steps

Important milestone-label note: current `README.md`, `docs/ARCHITECTURE.md`, `docs/CAREER_API.md`, and implemented endpoints now present M1-M10 as completed or packaged in sequence. `docs/PLAN.md` remains the active milestone source of truth, while `docs/ROADMAP.md` is historical.

### Must-preserve after M10 release packaging

1. Keep planning docs aligned so "M5 completed" does not conflict with M6 agent-standardization work.
2. Keep `docs/CURRENT_STATE_AUDIT.md` in the repo as the starting point for milestone cleanup.
3. Keep fit-label logic centralized in `app/services/fit_label.py`.
4. Keep workflow trace metadata additive and do not let it replace evidence spans, parser confidence, warnings, blockers, or unsupported-evidence diagnostics.
5. Keep the shared multimodal document schemas internal until image/OCR support is explicitly scoped.
6. Keep CI running pytest, Ruff, and Docker build checks.
7. Keep the Dockerfile free of OCR dependencies until OCR support is intentionally added.
8. Keep `.env.example` conservative and secret-free.
9. Keep public demo examples synthetic and non-sensitive.

### Future cleanup candidates

1. Split `app/services/extraction_service.py` into section splitting, resume extraction, JD extraction, and diagnostics modules.
2. Split `app/services/matching_service.py` into requirement evaluation, scoring, blockers, and evidence summary modules.
3. Move duplicated tokenization/canonicalization helpers into shared deterministic utilities where semantics are identical.
4. Add a common API error envelope.
5. Add a persistent async workflow status model only when a future long-running workflow requires it.
6. Expand recommendation benchmark coverage beyond 3 cases.
7. Add snapshot artifact generation to the standard review checklist.
8. Expand dashboard-oriented response examples as frontend requirements become concrete.
9. Add a reproducible lock strategy before a hosted production deployment.
10. Add artifact comparison checks to CI if baseline drift becomes a release risk.

### Can defer beyond this release

1. Real LLM-backed agents.
2. `BaseAgent` and `AgentRegistry`.
3. Vector store integration.
4. Persistent profile memory.
5. OCR provider integration.
6. Frontend dashboard implementation.
7. Background job queue.
8. External JD URL ingestion.

### Suggested branch name

`release/m10-deployment-portfolio`

### Suggested PR title

`Package CareerFit Agent for deployment and portfolio review`

### Suggested acceptance criteria

- README includes project overview, architecture, install, run, Docker, tests, API walkthrough, benchmarks, and portfolio narrative.
- `docs/DEPLOYMENT.md`, `docs/DEMO_GUIDE.md`, `docs/API_WALKTHROUGH.md`, `RELEASE_NOTES.md`, `.env.example`, and `docker-compose.yml` exist.
- Public walkthrough examples use synthetic data.
- CI runs Ruff, pytest, and Docker build verification.
- Existing tests still pass: `.\.venv\Scripts\python.exe -m pytest -q`.
- Existing benchmark behavior is preserved; no baseline artifacts are refreshed as part of the release-packaging pass.
