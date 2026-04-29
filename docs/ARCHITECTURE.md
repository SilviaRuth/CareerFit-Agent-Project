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
- additive workflow trace and document contracts for future agent-style workflows without endpoint behavior changes
- offline benchmark and report generation for Milestones 4 and 5

The current backend does not implement vector stores, external profile persistence, JD URL ingestion, or multi-agent orchestration.

## Milestone State

- M1: completed in the current codebase
- M2: completed in the current codebase
- M3: completed in the current codebase
- M4: completed in the current codebase
- M5: completed in the current codebase
- M6: foundation in progress, Agent Standardization Foundation

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

Routes should only validate transport concerns and delegate business logic.

### Shared workflow and document contracts

- `app/schemas/workflow.py`
- `app/schemas/document.py`

Responsibilities:

- define additive `WorkflowTrace`, `WorkflowStepTrace`, `WorkflowStatus`, and `WorkflowResult` contracts for future trace/result metadata
- define additive `DocumentInput`, `DocumentPage`, `DocumentSegment`, and `NormalizedDocument` contracts for multimodal normalization diagnostics
- keep these contracts internal until a later milestone explicitly documents public API exposure
- avoid changing parse, match, generation, comparison, retrieval, semantic helper, or benchmark behavior

### Parsing and ingestion

- `app/services/ingestion/file_ingestion.py`
- `app/services/text_normalizer.py`
- `app/services/extraction_service.py`
- `app/services/parse_service.py`

Responsibilities:

- bounded file ingestion
- image/scanned-PDF needs-OCR detection without hidden OCR fallback
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

Responsibilities:

- deterministic role and company emphasis summaries
- multi-resume ranking against a shared JD
- cross-JD opportunity ranking against a shared candidate profile
- ranking tie-breaks informed by parser confidence and additive helper signals

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

Future milestones should extend this architecture in layers: M6 standardizes service and trace contracts, M7 strengthens document ingestion for multimodal inputs, M8 exposes workflow status for frontend readiness, M9 adds optional LLM-assisted generation behind guardrails, and M10 hardens deployment and portfolio release materials.

The deterministic parser, matcher, blocker flags, evidence model, and benchmark reports remain the source of truth unless a later milestone explicitly changes that contract.
