# ROADMAP.md

Historical note: this document records the original Milestone 1 boundary. The active milestone breakdown now lives in `docs/PLAN.md`, and detailed future milestone scopes live under `docs/milestones/`. The current repo has already moved beyond this initial scope into later completed milestones.

## Goal

Lock the first milestone to a backend-only MVP that can take resume text plus JD text, normalize them deterministically, extract structured schemas, run rule-based matching, and return evidence-linked JSON.

This milestone explicitly excludes:
- frontend/UI work
- vector retrieval or any vector store
- multi-agent orchestration
- PDF/DOCX parsing
- resume rewrite generation
- interview preparation generation
- semantic matching

---

## Milestone 1: Backend MVP

### Outcome

Deliver a narrow, explainable pipeline:

1. accept raw text inputs only
2. normalize and parse text deterministically
3. extract `ResumeSchema` and `JDSchema`
4. run a weighted rule-based matcher
5. return `MatchResult` as structured JSON with evidence spans

### Success Criteria

- FastAPI service starts locally
- one `POST /match` endpoint accepts text payloads
- schemas are validated with Pydantic v2
- outputs distinguish required vs preferred requirements
- outputs distinguish missing skill vs missing evidence
- blocker flags are returned explicitly
- every match/gap explanation is tied to resume or JD evidence where possible
- unit tests cover baseline matching behavior

### Out of Scope

- file uploads
- PDF/DOCX parsing
- embeddings or semantic similarity
- retrieval/RAG
- databases or vector stores
- orchestration frameworks
- frontend or dashboard work

---

## Implementation Slices

### Slice 1: Text-to-JSON Match Flow

Scope for the first coding slice:

- parse normalized text
- extract schema
- match requirements
- return evidence-backed result

Interfaces in this slice should stay backend-only and machine-readable:

- input: plain text resume + plain text JD
- output: structured JSON only

Leave these for later slices:

- document parsing from PDF/DOCX
- resume rewriting
- interview prep
- semantic matching
- retrieval-backed explanations

### Slice 2: Better Parsing Inputs

Add PDF/DOCX ingestion only after Slice 1 is stable and tested.

### Slice 3: Evaluation Expansion

Add more gold fixtures and regression reporting once the baseline matcher is stable.

### Slice 4: Optional Enhancement Work

Consider semantic matching, rewrite support, or retrieval only after the deterministic baseline is trustworthy.

---

## First Coding PR Boundary

The first coding PR should include only:

- project skeleton
- Pydantic schemas
- one matching service with rule-based baseline logic
- one `/match` endpoint
- sample fixtures
- unit tests for:
  - required match
  - preferred match
  - missing evidence
  - blocker flags

The first coding PR should not include:

- extra endpoints
- background jobs
- agent graphs
- database work
- UI assets
- semantic ranking

---

## Review Notes

This roadmap keeps the first build aligned with the repo rules:

- schema-first
- deterministic critical path
- thin API routes
- evidence before polish
- small, reviewable PRs
