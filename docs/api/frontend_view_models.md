# Frontend View Models

M8 adds optional `workflow_trace` fields to selected responses so a frontend can show
execution state without inferring backend internals. Trace data is additive only. It
does not replace parser confidence, parser warnings, unsupported segments, evidence
spans, blockers, semantic hints, recommendations, or ranking data.

## Shared Workflow Trace

```json
{
  "workflow_trace": {
    "trace_id": "0a2f7c40-d9a9-4bdf-b8e2-8b716a7f6f12",
    "workflow_name": "match",
    "status": "completed",
    "steps": [
      {
        "step_name": "parse_resume",
        "status": "completed",
        "service_name": "extraction_service",
        "warnings": [],
        "metadata": {
          "input": "resume_text"
        }
      },
      {
        "step_name": "score_match",
        "status": "completed",
        "service_name": "matching_service",
        "warnings": [],
        "metadata": {
          "overall_score": 89
        }
      }
    ],
    "warnings": []
  }
}
```

Trace status values intended for frontend display are `completed`, `partial`,
`failed`, and `skipped`.

## Fit Summary

Use `/match` for a single candidate-to-role fit view.

```json
{
  "overall_score": 89,
  "dimension_scores": {
    "skills": 100,
    "experience": 100,
    "projects": 43,
    "domain_fit": 100,
    "education": 100
  },
  "blocker_flags": {
    "missing_required_skills": false,
    "seniority_mismatch": false,
    "unsupported_claims": false
  },
  "strengths": [
    "Matched required python with resume evidence."
  ],
  "explanations": [
    "Overall score is 89 based on weighted rule-based matching across skills, experience, projects, domain fit, and education."
  ],
  "workflow_trace": {
    "trace_id": "uuid",
    "workflow_name": "match",
    "status": "completed"
  }
}
```

## Evidence Panel

Keep evidence spans visible in the primary panel. The trace can explain that evidence
collection happened, but it should not be used as the evidence source.

```json
{
  "evidence_spans": [
    {
      "source_document": "resume",
      "section": "experience",
      "text": "Built backend APIs using FastAPI and PostgreSQL.",
      "start_char": 120,
      "end_char": 167,
      "normalized_value": null,
      "explanation": "Experience block extracted deterministically."
    }
  ],
  "evidence_summary": {
    "total_evidence_spans": 8,
    "resume_evidence_spans": 5,
    "jd_evidence_spans": 3,
    "required_match_count": 4,
    "preferred_match_count": 2,
    "gap_count": 1
  },
  "workflow_trace": {
    "steps": [
      {
        "step_name": "collect_evidence",
        "status": "completed",
        "metadata": {
          "total_evidence_spans": 8
        }
      }
    ]
  }
}
```

## Diagnostics Panel

Use parse responses for parser diagnostics and confidence. Use trace warnings only as
execution metadata.

```json
{
  "parser_confidence": {
    "score": 0.76,
    "level": "medium",
    "extraction_complete": true,
    "factors": [
      "warning:section_header_alias_used"
    ]
  },
  "warnings": [
    {
      "warning_code": "section_header_alias_used",
      "message": "Recognized section header variant as a canonical section.",
      "section": "experience",
      "severity": "info",
      "source": "extraction"
    }
  ],
  "unsupported_segments": [],
  "workflow_trace": {
    "warnings": [
      "resume-1:experience:section_header_alias_used:info"
    ]
  }
}
```

## Recommendation Panel

Use `/compare/jobs` for ranked opportunities with request-scoped recommendations.

```json
{
  "ranking": [
    {
      "rank": 1,
      "jd_id": "backend-platform",
      "job_title": "Senior Backend Engineer",
      "company": "Example Co",
      "overall_score": 89,
      "fit_label": "strong",
      "retrieved_evidence": [
        {
          "label": "FastAPI",
          "source_section": "experience",
          "score": 1.35,
          "reason": "Matched candidate memory tokens against the retrieval query.",
          "evidence_used": []
        }
      ],
      "semantic_support": [],
      "recommended_next_steps": [
        "Strengthen project evidence for deployment ownership."
      ]
    }
  ],
  "workflow_trace": {
    "workflow_name": "compare_jobs",
    "steps": [
      {
        "step_name": "build_recommendations",
        "status": "completed"
      }
    ]
  }
}
```

## Ranking Table

Use `/compare/resumes` for multiple candidates against one role, or `/compare/jobs`
for one candidate against multiple roles.

```json
{
  "summary": "Compared 3 resumes against Senior Backend Engineer at Example Co.",
  "compared_count": 3,
  "ranking": [
    {
      "rank": 1,
      "resume_id": "candidate-a",
      "overall_score": 89,
      "fit_label": "strong",
      "score_delta_from_best": 0,
      "parser_confidence": {
        "score": 0.98,
        "level": "high",
        "extraction_complete": true,
        "factors": []
      },
      "blocker_flags": {
        "missing_required_skills": false,
        "seniority_mismatch": false,
        "unsupported_claims": false
      }
    }
  ],
  "workflow_trace": {
    "steps": [
      {
        "step_name": "rank_resumes",
        "status": "completed",
        "metadata": {
          "ranking_ids": [
            "candidate-a",
            "candidate-b",
            "candidate-c"
          ]
        }
      }
    ]
  }
}
```
