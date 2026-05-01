# ARCHITECTURE.md

## Overview

CareerFit Agent is a deterministic backend pipeline for resume and JD analysis.

The current architecture supports:

- bounded ingestion for text, TXT, PDF, and DOCX inputs
- deterministic schema extraction for resumes and JDs
- rule-based matching with evidence spans and blocker flags
- single-orchestrator grounded generation for rewrite, interview prep, interview simulation, and learning plans
- multi-resume comparison against one shared JD
- cross-JD comparison against one shared candidate profile
- request-scoped candidate profile memory with bounded evidence retrieval and additive semantic hints
- optional workflow traces on selected public responses for frontend-ready progress and diagnostics
- optional validated LLM advisory generation that remains separate from deterministic results
- additive document contracts for multimodal normalization diagnostics
- offline benchmark and report generation for Milestones 4 and 5

The current backend does not implement vector stores, external profile persistence, JD URL ingestion, hidden external LLM calls, or multi-agent orchestration.

## Milestone State

- M1: completed in the current codebase
- M2: completed in the current codebase
- M3: completed in the current codebase
- M4: completed in the current codebase
- M5: completed in the current codebase
- M6: completed in the current codebase
- M7: completed in the current codebase
- M8: implemented in the current codebase
- M9: implemented as an optional advisory layer, disabled by default

## High-Level Flows

### Parse and match flow

1. Ingest raw text or a bounded uploaded file.
2. Normalize document text.
3. Extract a validated `ResumeSchema` or `JDSchema`.
4. Match parsed schemas with deterministic rules.
5. Return score, strengths, gaps, blockers, explanations, and evidence.

### Grounded generation flow

1. Parse the resume.
2. Parse the JD.
3. Match parsed schemas.
4. Compute generation gating from parser confidence, blockers, and evidence risk.
5. Render rewrite, interview-prep, interview-sim, or learning-plan output from the shared grounded context.

### Multi-resume comparison flow

1. Parse one shared JD.
2. Parse each resume independently.
3. Match each parsed resume against the shared JD.
4. Rank results with blocker-aware, confidence-aware ordering.
5. Return ranked summaries with additive adaptation metadata.

### Cross-JD comparison flow

1. Build request-scoped candidate profile memory from a resume or reuse a provided profile.
2. Parse each JD independently.
3. Match the shared candidate profile against each JD.
4. Add bounded retrieval evidence and optional semantic hints without changing the core score.
5. Rank opportunities and attach role-specific next steps.

### Workflow trace flow

Selected responses expose an optional `workflow_trace` field with a per-request
`trace_id`, ordered step names, step status, service names, warnings, and metadata.
Trace builders live in `app/services/workflow_trace_service.py` and are attached
after deterministic outputs are computed.

Workflow trace metadata is additive. It must not replace evidence spans, parser
confidence, parse warnings, unsupported segments, blocker flags, semantic hints, or
ranking results.

### LLM advisory flow

1. Build the deterministic grounded context from resume parsing, JD parsing, matching, evidence, and generation gating.
2. If `ENABLE_LLM_GENERATION=false`, return deterministic artifacts with `llm_status: "disabled"`.
3. If enabled, send only deterministic artifacts to a provider-neutral `LLMClient`.
4. Validate the raw output against strict advisory schemas.
5. Run deterministic grounding checks before exposing any advice under `llm_advice`.
6. Return fallback or rejected status when configuration, schema validation, or grounding validation fails.

## Core Modules

### API layer

`app/api/routes/`

Public endpoints:

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

Routes should only validate transport concerns and delegate business logic.

### Shared workflow and document contracts

- `app/schemas/workflow.py`
- `app/schemas/document.py`

Responsibilities:

- define additive `WorkflowTrace`, `WorkflowStepTrace`, `WorkflowStatus`, and `WorkflowResult` contracts for trace/result metadata
- define additive `DocumentInput`, `DocumentPage`, `DocumentSegment`, and `NormalizedDocument` contracts for multimodal normalization diagnostics
- expose optional `workflow_trace` on selected frontend-facing responses without removing existing fields
- avoid changing parse, match, generation, comparison, retrieval, semantic helper, or benchmark behavior

### Parsing and ingestion

- `app/services/ingestion/file_ingestion.py`
- `app/services/text_normalizer.py`
- `app/services/extraction_service.py`
- `app/services/parse_service.py`

Responsibilities:

- bounded file ingestion
- image/scanned-PDF needs-OCR diagnostics without hidden OCR fallback
- clean embedded-text PDF ingestion checks that should not trigger needs-OCR
- normalization diagnostics
- section detection
- schema extraction
- parser confidence and unsupported segment reporting

### Matching

`app/services/matching_service.py`

Responsibilities:

- deterministic requirement evaluation
- missing skill vs missing evidence distinction
- blocker flag calculation
- dimension scores and overall score
- evidence summary creation
- additive adaptation summary injection

### Adaptation and comparison

- `app/services/adaptation_service.py`
- `app/services/comparison_service.py`
- `app/services/opportunity_comparison_service.py`
- `app/services/workflow_trace_service.py`

Responsibilities:

- deterministic role and company emphasis summaries
- multi-resume ranking against a shared JD
- cross-JD opportunity ranking against a shared candidate profile
- ranking tie-breaks informed by parser confidence and additive helper signals
- additive workflow trace construction for comparison and ranking responses

### Grounded generation

- `app/services/orchestration_service.py`
- `app/services/generation/generation_guardrails.py`
- `app/services/generation/rewrite_service.py`
- `app/services/generation/interview_prep_service.py`
- `app/services/generation/interview_simulation_service.py`
- `app/services/generation/learning_plan_service.py`
- `app/services/generation/grounding.py`

Responsibilities:

- build one shared grounded context
- compute gating from parser quality and evidence risk
- keep outputs narrowly grounded
- translate explicit gaps and blockers into deterministic guidance
- prevent unsupported or overconfident generation

### Optional LLM advisory generation

- `app/llm/base.py`
- `app/llm/config.py`
- `app/llm/providers.py`
- `app/llm/prompts.py`
- `app/llm/validators.py`
- `app/llm/advisory.py`
- `app/schemas/llm_generation.py`

Responsibilities:

- keep provider configuration and client contracts isolated from deterministic services
- build prompts only from deterministic parse, match, evidence, and gate outputs
- validate free-form provider output before returning it
- reject missing evidence and unsupported claims conservatively
- keep `llm_advice`, `llm_status`, and `validation_report` separate from deterministic outputs

### Candidate context, retrieval, and semantic helpers

- `app/services/candidate_profile_service.py`
- `app/services/retrieval_service.py`
- `app/services/semantic_matching_service.py`

Responsibilities:

- build request-scoped candidate profile memory with audit metadata
- retrieve bounded candidate evidence for recommendation queries
- expose optional semantic hints through explicit contracts

These helpers are additive only and must not silently rewrite the score contract.

### Evaluation

- `app/evaluation/benchmark_runner.py`
- `app/evaluation/extraction_runner.py`
- `app/evaluation/comparison_runner.py`
- `app/evaluation/recommendation_runner.py`
- `app/evaluation/artifact_writer.py`

Responsibilities:

- run fixture-backed regression checks
- produce reviewable JSON artifacts
- refresh baseline reports intentionally
- create labeled snapshots for comparison review

## Current Safety Boundaries

- file uploads are bounded
- unsupported or malformed files fail clearly
- parse responses expose warnings and confidence
- generation must remain evidence-linked
- LLM advice is disabled by default and must pass schema plus grounding validation
- candidate profile memory is request-scoped and non-persistent
- retrieval and semantic hints are explicit helper layers, not hidden score rewrites
- resumes and JDs should be treated as sensitive career documents
- outputs must not imply guaranteed hiring outcomes

## Evaluation Story

The checked-in evaluation layer includes:

- match benchmark manifests and expected outputs
- extraction benchmark manifests and expected outputs
- comparison benchmark manifests and expected outputs
- recommendation benchmark manifests and expected outputs
- baseline reports under `data/eval/reports/baseline/`
- snapshot-capable report writing under `data/eval/reports/snapshots/`

This evaluation bundle is part of the architecture, not an optional afterthought.

## Non-Goals At The Current Stage

- vector stores or external retrieval infrastructure
- persistent user-profile storage
- JD URL scraping or ingestion
- frontend delivery
- background job systems
- autonomous agent loops
- opaque scoring or prompt-only behavior

## Forward Architecture Direction

Completed foundation layers now cover service/trace contracts in M6, multimodal ingestion diagnostics in M7, selected public workflow traces for frontend readiness in M8, and optional validated LLM advisory generation in M9. Future milestones should extend this architecture with deployment/portfolio release hardening in M10.

The deterministic parser, matcher, blocker flags, evidence model, and benchmark reports remain the source of truth unless a later milestone explicitly changes that contract.
