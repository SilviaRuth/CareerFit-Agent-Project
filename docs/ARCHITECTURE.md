# ARCHITECTURE.md

## Overview

CareerFit Agent is a deterministic backend pipeline for resume and JD analysis.

The current architecture supports:

- bounded ingestion for text, TXT, PDF, and DOCX inputs
- deterministic schema extraction for resumes and JDs
- rule-based matching with evidence spans and blocker flags
- single-orchestrator grounded generation for rewrite and interview prep
- multi-resume comparison against one shared JD
- offline benchmark and report generation for Milestone 4 regression review

The current backend does not implement retrieval, semantic matching, JD URL ingestion, or
multi-agent orchestration.

## Milestone State

- M1: completed in the current codebase
- M2: completed in the current codebase
- M3: completed in the current codebase
- M4: completed in the current codebase
- M5: not started

The current focus before M5 is preserving correctness, keeping docs in sync, and protecting the
evaluation baseline.

## High-Level Flow

### Parse and match flow

1. Ingest raw text or a bounded uploaded file.
2. Normalize document text.
3. Extract a validated `ResumeSchema` or `JDSchema`.
4. Match parsed schemas with deterministic rules.
5. Return score, strengths, gaps, blockers, explanations, and evidence.

### Grounded generation flow

1. Parse resume text.
2. Parse JD text.
3. Match parsed schemas.
4. Compute generation gating from parser confidence, blockers, and evidence quality.
5. Render rewrite or interview-prep output from the shared grounded context.

### Multi-resume comparison flow

1. Parse one shared JD.
2. Parse each resume independently.
3. Match each parsed resume against the shared JD.
4. Rank results with blocker-aware, confidence-aware ordering.
5. Return ranked summaries with additive adaptation metadata.

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
- `POST /compare/resumes`

Routes should only validate transport concerns and delegate business logic.

### Parsing and ingestion

- `app/services/ingestion/file_ingestion.py`
- `app/services/text_normalizer.py`
- `app/services/extraction_service.py`
- `app/services/parse_service.py`

Responsibilities:

- bounded file ingestion
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

Responsibilities:

- deterministic role and company emphasis summaries
- multi-resume ranking against a shared JD
- ranking tie-breaks informed by parser confidence

Adaptation metadata is additive. It should shape presentation and ordering, not silently redefine
the underlying score contract.

### Grounded generation

- `app/services/orchestration_service.py`
- `app/services/generation/generation_guardrails.py`
- `app/services/generation/rewrite_service.py`
- `app/services/generation/interview_prep_service.py`
- `app/services/generation/grounding.py`

Responsibilities:

- build one shared grounded context
- compute gating from parser quality and evidence risk
- keep outputs narrowly grounded
- prevent unsupported or overconfident generation

### Evaluation

- `app/evaluation/benchmark_runner.py`
- `app/evaluation/extraction_runner.py`
- `app/evaluation/comparison_runner.py`
- `app/evaluation/artifact_writer.py`

Responsibilities:

- run fixture-backed regression checks
- produce reviewable JSON artifacts
- refresh baseline reports intentionally
- create labeled snapshots for comparison review

## Data Contracts

Important public contract families:

- parse responses in `app/schemas/parse.py`
- match responses in `app/schemas/match.py`
- generation responses in `app/schemas/generation.py`
- comparison responses in `app/schemas/comparison.py`

The repo favors explicit, stable schemas over loose dictionaries.

## Current Safety Boundaries

- file uploads are bounded
- unsupported or malformed files fail clearly
- parse responses expose warnings and confidence
- generation must remain evidence-linked
- resumes and JDs should be treated as sensitive career documents
- outputs must not imply guaranteed hiring outcomes

## Evaluation Story

Milestone 4 is artifact-driven.

The checked-in evaluation layer includes:

- match benchmark manifests and expected outputs
- extraction benchmark manifests and expected outputs
- comparison benchmark manifests and expected outputs
- baseline reports under `data/eval/reports/baseline/`
- snapshot-capable report writing under `data/eval/reports/snapshots/`

This evaluation bundle is part of the architecture, not an optional afterthought.

## Non-Goals At The Current Stage

- retrieval or vector stores
- semantic matching
- JD URL scraping or ingestion
- frontend delivery
- background job systems
- autonomous agent loops
- opaque scoring or prompt-only behavior
