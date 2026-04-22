# DECISIONS.md

## Status

These decisions are the default baseline for v1 planning as of 2026-04-16.

Implementation note: the current repository has already moved well beyond the original plain-text MVP. The active codebase now includes bounded PDF/DOCX ingestion, grounded generation, request-scoped candidate profile memory, cross-JD comparison, bounded retrieval helpers, additive semantic hints, and expanded evaluation, while the locked defaults below still apply unless explicitly replaced.

---

## Locked Defaults

- Python 3.11
- FastAPI
- Pydantic v2
- pytest
- local JSON/sample fixtures for v1
- single orchestrator only
- no vector store
- no frontend
- no large framework additions

These defaults remain in force unless a later decision record explicitly replaces them.

---

## Orchestration Pattern

For Milestone 3, grounded generation uses a single orchestrator service.

Current decision:

- keep orchestration in backend service code, not a multi-agent framework
- coordinate `parse -> match -> gate -> generate` through one explicit module
- treat rewrite and interview-prep modules as callable capabilities, not autonomous agents
- keep generation subordinate to parse outputs, match diagnostics, evidence spans, warnings, and gating metadata

Rejected for the current stage:

- multi-agent planner/executor/reviewer setups
- framework-heavy orchestration graphs
- autonomous tool loops

This keeps the critical path deterministic, reviewable, and aligned with the repo's schema-first architecture.

---

## MVP Boundary

The first MVP is backend-only and explainability-first.

It will support:

- text resume input
- text JD input
- deterministic parsing and normalization
- rule-based matching
- evidence-linked structured outputs

It will not support in v1:

- retrieval
- semantic matching
- multi-agent orchestration
- frontend delivery
- file parsing beyond plain text

Current repo status beyond the original MVP boundary:

- bounded file parsing for `.txt`, `.pdf`, and `.docx`
- dedicated parse endpoints
- single-orchestrator grounded generation via `/rewrite`, `/interview-prep`, `/interview-sim`, and `/learning-plan`
- request-scoped `profile_memory` plus bounded retrieval and additive semantic helper endpoints
- offline benchmark, extraction, comparison, and recommendation evaluation runners
- deterministic `adaptation_summary` output shaping for `/match` and `/compare/resumes`
- deterministic cross-JD comparison via `/compare/jobs`
- checked-in baseline plus snapshot-capable report artifacts

Still intentionally out of scope by default:

- vector-store-backed retrieval
- opaque semantic score rewrites
- multi-agent orchestration
- frontend delivery

---

## Core Contracts

Define contracts before code so the first implementation can stay stable and testable.

### `EvidenceSpan`

Purpose: point to the exact source text behind a match, gap, or warning.

Required fields:

- `source_document`: `resume` or `job_description`
- `section`: normalized section label such as `skills`, `experience`, `projects`, `requirements`
- `text`: the supporting text span
- `start_char`: start character offset in normalized text when available
- `end_char`: end character offset in normalized text when available
- `normalized_value`: normalized skill/requirement label when applicable
- `explanation`: short plain-English note for why this span matters

### `ResumeSchema`

Purpose: canonical structured representation extracted from resume text.

Required fields:

- `candidate_name`
- `summary`
- `skills`
- `experience_items`
- `project_items`
- `education_items`
- `evidence_spans`

Important modeling rules:

- skills should be normalized but preserve the original text evidence
- experience and project items should keep enough text to support later matching
- claims listed only in summary or skills may still require stronger evidence from experience/projects

### `JDSchema`

Purpose: canonical structured representation extracted from JD text.

Required fields:

- `job_title`
- `company`
- `required_requirements`
- `preferred_requirements`
- `responsibilities`
- `education_requirements`
- `seniority_hint`
- `domain_hint`
- `evidence_spans`

Important modeling rules:

- requirements must distinguish `required` from `preferred`
- skills, experience, education, and domain signals should be classifiable separately
- every extracted requirement should retain the original JD text span

### `GapItem`

Purpose: explain a missing or weak qualification in a reviewable way.

Required fields:

- `requirement_id`
- `requirement_label`
- `requirement_priority`: `required` or `preferred`
- `gap_type`: `missing_skill`, `missing_evidence`, `seniority_mismatch`, `education_gap`, or `domain_gap`
- `explanation`
- `resume_evidence`
- `jd_evidence`

Important modeling rules:

- `missing_skill` means the normalized capability is absent from the resume schema
- `missing_evidence` means the capability is claimed or loosely implied but not supported strongly enough
- gaps must keep required vs preferred visible in the contract

### `MatchResult`

Purpose: final structured output for the `/match` endpoint.

Required fields:

- `overall_score`
- `dimension_scores`
- `required_matches`
- `preferred_matches`
- `gaps`
- `blocker_flags`
- `strengths`
- `explanations`
- `evidence_spans`

Important modeling rules:

- `required_matches` and `preferred_matches` must be separate collections
- each match item should include a status such as `matched`, `partial`, `missing`, or `unsupported`
- explanations must be human-readable and grounded in evidence
- blocker flags must stay explicit even when the overall score is high

---

## Scoring Baseline

Start with weighted rule-based scoring only.

Default weights:

- skills: 30
- experience: 30
- projects: 20
- domain fit: 10
- education: 10

### Plain-English Scoring Rules

1. Score each dimension separately before combining them.
2. Give credit only for qualifications that can be linked to resume evidence.
3. Treat required and preferred requirements differently.
4. Required matches drive the baseline score.
5. Preferred matches can add soft upside but cannot erase important required misses.
6. If a skill appears in a weak way, classify it as missing evidence instead of a full match.
7. If the resume clearly lacks a required capability, classify it as missing skill.
8. If the resume seniority is materially below the JD, set a blocker flag even if some skills match.
9. If the resume claims expertise without support in experience or projects, set an unsupported-claims blocker flag.
10. Return the score together with explanations, gaps, and evidence rather than as a standalone number.

### Blocker Flags

The baseline matcher should emit explicit blocker flags for:

- missing required skills
- seniority mismatch
- unsupported claims

Blockers are not the same thing as gaps:

- a gap explains what is weak or missing
- a blocker marks a high-risk issue that should stand out immediately

---

## Evaluation Baseline

Use small local fixtures first.

Initial gold set:

- 3 sanitized resume/JD pairs
- 1 strong fit
- 1 partial fit
- 1 poor fit

Each expected outcome should record:

- required skill matches
- preferred skill matches when useful
- top gaps
- blocker flags

This gold set is intended for unit and early regression coverage, not broad model benchmarking.
