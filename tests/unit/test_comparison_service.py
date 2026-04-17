"""Unit tests for multi-resume comparison service behavior."""

from __future__ import annotations

from app.schemas.comparison import MultiResumeComparisonRequest, ResumeComparisonInput
from app.services.comparison_service import compare_resumes_to_jd
from tests.conftest import load_sample


def test_compare_resumes_to_jd_ranks_stronger_resume_first() -> None:
    response = compare_resumes_to_jd(
        MultiResumeComparisonRequest(
            resumes=[
                ResumeComparisonInput(
                    resume_id="strong",
                    resume_text=load_sample("strong_fit_resume.txt"),
                ),
                ResumeComparisonInput(
                    resume_id="partial",
                    resume_text=load_sample("partial_fit_resume.txt"),
                ),
                ResumeComparisonInput(
                    resume_id="poor",
                    resume_text=load_sample("poor_fit_resume.txt"),
                ),
            ],
            job_description_text=load_sample("strong_fit_jd.txt"),
        )
    )

    assert response.compared_count == 3
    assert response.ranking[0].resume_id == "strong"
    assert response.ranking[0].fit_label == "strong"
    assert response.ranking[1].resume_id == "partial"
    assert response.ranking[2].resume_id == "poor"
    assert response.ranking[0].score_delta_from_best == 0
    assert response.ranking[2].blocker_flags.missing_required_skills is True
