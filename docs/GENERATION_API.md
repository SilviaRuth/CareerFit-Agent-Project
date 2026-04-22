# Generation API Guide

This guide documents the grounded generation workflows currently exposed by the backend.

## Purpose

The generation endpoints reuse the deterministic parse and match pipeline, then apply structured gating before returning bounded guidance.

Current grounded outputs:

- `POST /rewrite`
- `POST /interview-prep`
- `POST /interview-sim`
- `POST /learning-plan`

These endpoints are not autonomous agents, prompt-only recommenders, or opaque retrieval workflows.

## Shared Request

Each generation endpoint accepts the same JSON payload:

```json
{
  "resume_text": "Alex Chen\n\nSummary\nBackend engineer...",
  "job_description_text": "Senior Backend Engineer\nHealthStack\n\nRequired\n- Python...",
  "resume_source_name": "resume.txt",
  "jd_source_name": "jd.txt"
}
```

## Shared Guardrails

Before rendering output, the orchestrator always:

1. parses the resume
2. parses the JD
3. runs deterministic matching
4. computes a `gating` result from parser confidence, blockers, and missing-evidence risk
5. renders only guidance that stays inside grounded evidence

Generation responses include:

- `generation_warnings`
- `gating`
- evidence-linked fields specific to the endpoint

`generation_mode` stays reviewable:

- `full`: richer grounded output is allowed
- `limited`: bounded output with stronger cautioning
- `minimal`: conservative guidance only

## `POST /interview-sim`

Purpose:

- simulate likely interview probes from JD responsibilities, supported strengths, and explicit gaps
- keep answer coaching truthful when evidence is thin
- practice weak-area framing without inventing new experience

Response highlights:

- `simulation_rounds`
- `coach_notes`
- `evidence_used`
- `generation_warnings`
- `gating`

## `POST /learning-plan`

Purpose:

- turn explicit gaps and blockers into ordered learning actions
- keep supported strengths visible as the safe foundation for growth
- avoid advice that bypasses evidence or hides current blockers

Response highlights:

- `focus_areas`
- `plan_steps`
- `supporting_strengths`
- `blocker_cautions`
- `evidence_used`
- `generation_warnings`
- `gating`

Milestone 5 keeps these outputs deterministic and grounded even when candidate profile memory, retrieval, and semantic helper modules are used elsewhere in the repo.
