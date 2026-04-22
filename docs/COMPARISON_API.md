# Comparison API Guide

This guide documents the deterministic comparison workflows exposed by the backend.

## Purpose

The repository now supports two bounded comparison paths:

- `POST /compare/resumes` ranks multiple resumes against one shared JD
- `POST /compare/jobs` ranks multiple JDs against one shared candidate profile

Both flows stay aligned with the deterministic parse and match pipeline. They are reviewable ranking tools, not opaque recommenders.

## `POST /compare/resumes`

Use this when the role is fixed and the candidate slate changes.

Input:

- one shared `job_description_text`
- one or more resume entries with `resume_id` and `resume_text`

Response highlights:

- shared JD metadata
- JD parser confidence
- ranked resume entries
- blocker flags, top gaps, strengths, evidence summary, and adaptation summary per resume

## `POST /compare/jobs`

Use this when the candidate is fixed and you want to compare multiple opportunities.

Input:

- either raw `resume_text` or a reusable `profile_memory`
- one or more job description entries with `jd_id` and `job_description_text`
- optional `semantic_mode` to expose additive semantic hints without changing the core score

Response highlights:

- reusable `candidate_profile`
- ranked job entries
- deterministic fit labels and blocker flags
- top gaps and recommended next steps per role
- bounded retrieval evidence for why the role ranked where it did
- additive semantic hints kept separate from the deterministic score contract

## Ranking Rules

Both comparison services keep ordering deterministic and reviewable:

- fewer critical blockers rank ahead of more blocked results
- higher overall score ranks ahead within the same blocker profile
- parser confidence, unsupported-claim risk, and additive helper signals break ties after the core score

The extra M5 retrieval and semantic fields are additive only. They do not rewrite score meaning or suppress blocker visibility.

## Offline Coverage

`POST /compare/resumes` is locked by the M4 comparison benchmark:

```powershell
.venv\Scripts\Activate.ps1
python -m app.evaluation.comparison_runner
```

`POST /compare/jobs` is currently protected by integration and unit tests rather than a separate offline ranking manifest.
