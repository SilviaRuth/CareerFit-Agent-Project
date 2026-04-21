# Comparison API Guide

This guide documents the Milestone 4 multi-resume comparison workflow.

## Purpose

`POST /compare/resumes` ranks multiple resumes against one shared JD using the same deterministic parse and match pipeline as the rest of the backend.

The comparison flow is intended for:

- comparing resume variants for the same candidate
- comparing a small candidate slate against one role
- reviewing blocker and evidence differences side by side
- making role/company adaptation emphasis reviewable for each ranked resume

It is not a semantic ranking system or a retrieval-backed recommender.

## Endpoint

### `POST /compare/resumes`

Input:

- one shared `job_description_text`
- one or more resume entries with `resume_id` and `resume_text`

Response:

- shared JD metadata
- JD parser confidence
- ranked resume comparison entries
- score deltas from the best result
- blocker flags, top gaps, strengths, evidence summary, and adaptation summary for each ranked resume

## Example

```json
{
  "resumes": [
    {
      "resume_id": "backend_v1",
      "resume_text": "Alex Chen\n\nSummary\nBackend engineer..."
    },
    {
      "resume_id": "backend_v2",
      "resume_text": "Alex Chen\n\nSummary\nSenior backend engineer..."
    }
  ],
  "job_description_text": "Senior Backend Engineer\nHealthStack\n\nRequired\n- Python..."
}
```

## Response Shape

```json
{
  "summary": "Compared 2 resumes against Senior Backend Engineer at HealthStack.",
  "compared_count": 2,
  "job_title": "Senior Backend Engineer",
  "company": "HealthStack",
  "jd_parser_confidence": {},
  "ranking": [
    {
      "rank": 1,
      "resume_id": "backend_v2",
      "overall_score": 89,
      "fit_label": "strong",
      "blocker_flags": {},
      "dimension_scores": {},
      "parser_confidence": {},
      "strengths": [],
      "top_gaps": [],
      "evidence_summary": {},
      "adaptation_summary": {},
      "score_delta_from_best": 0
    }
  ]
}
```

## Ranking Rules

The comparison service keeps the ranking deterministic and reviewable:

- fewer critical blockers rank ahead of more blocked resumes
- higher overall score ranks ahead within the same blocker profile
- unsupported-claim warnings break ties after the score

This ranking is intentionally simple and should stay aligned with the rule-based matcher unless a later decision record changes it.

## Offline Comparison Coverage

The comparison API is also exercised offline through:

```powershell
.venv\Scripts\Activate.ps1
python -m app.evaluation.comparison_runner
```

That runner uses representative scenarios from `data/eval/comparison_manifest.json` to lock ranking order, fit labels, and low-confidence resume ordering.
