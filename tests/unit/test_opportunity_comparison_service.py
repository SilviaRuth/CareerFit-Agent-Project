"""Unit tests for cross-JD opportunity comparison."""

from __future__ import annotations

from app.schemas.career import JobComparisonRequest
from app.services.opportunity_comparison_service import compare_candidate_to_jobs
from tests.conftest import load_sample


def test_compare_candidate_to_jobs_ranks_best_opportunity_first() -> None:
    response = compare_candidate_to_jobs(
        JobComparisonRequest(
            resume_text=load_sample("strong_fit_resume.txt"),
            job_descriptions=[
                {
                    "jd_id": "strong",
                    "job_description_text": load_sample("strong_fit_jd.txt"),
                },
                {
                    "jd_id": "poor",
                    "job_description_text": load_sample("poor_fit_jd.txt"),
                },
            ],
        )
    )

    assert response.compared_count == 2
    assert response.ranking[0].jd_id == "strong"
    assert response.ranking[0].recommended_next_steps
    assert response.ranking[0].retrieved_evidence
    assert response.workflow_trace is not None
    assert response.workflow_trace.workflow_name == "compare_jobs"
    assert [step.step_name for step in response.workflow_trace.steps] == [
        "parse_resume",
        "parse_job_description",
        "score_match",
        "collect_evidence",
        "compute_blockers",
        "build_recommendations",
        "rank_jobs",
    ]
