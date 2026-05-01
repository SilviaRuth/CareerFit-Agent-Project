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
    assert response.workflow_trace is not None
    assert response.workflow_trace.workflow_name == "compare_resumes"


def test_compare_resumes_to_jd_ranks_same_candidate_variants_deterministically() -> None:
    response = compare_resumes_to_jd(
        MultiResumeComparisonRequest(
            resumes=[
                ResumeComparisonInput(
                    resume_id="targeted",
                    resume_text=load_sample("alex_targeted_resume.txt"),
                ),
                ResumeComparisonInput(
                    resume_id="general",
                    resume_text=load_sample("alex_general_resume.txt"),
                ),
                ResumeComparisonInput(
                    resume_id="claimy",
                    resume_text=load_sample("alex_claimy_resume.txt"),
                ),
            ],
            job_description_text=load_sample("strong_fit_jd.txt"),
        )
    )

    assert [entry.resume_id for entry in response.ranking] == ["targeted", "claimy", "general"]
    assert response.ranking[0].adaptation_summary.role_focus == "backend_platform"
    assert response.ranking[1].fit_label == "partial"
    assert response.ranking[2].fit_label == "poor"


def test_compare_resumes_to_jd_pushes_low_confidence_resume_to_the_bottom() -> None:
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
                    resume_id="low_confidence",
                    resume_text=load_sample("low_confidence_resume.txt"),
                ),
            ],
            job_description_text=load_sample("strong_fit_jd.txt"),
        )
    )

    assert [entry.resume_id for entry in response.ranking] == [
        "strong",
        "partial",
        "low_confidence",
    ]
    assert response.ranking[-1].parser_confidence.level == "low"


def test_compare_resumes_to_jd_uses_parser_confidence_as_a_tie_breaker() -> None:
    response = compare_resumes_to_jd(
        MultiResumeComparisonRequest(
            resumes=[
                ResumeComparisonInput(
                    resume_id="low_confidence",
                    resume_text=(
                        "Highlights\n"
                        "Python, FastAPI, AWS, Docker\n"
                        "Experience\n"
                        "Backend Engineer at Example\n"
                        "Built backend APIs and platform services on AWS using FastAPI.\n"
                        "Projects\n"
                        "Platform migration to Docker and Python microservices.\n"
                        "Random Notes\n"
                        "Mentored interns and handled on-call.\n"
                        "Education\n"
                        "B.S. in Computer Science\n"
                    ),
                ),
                ResumeComparisonInput(
                    resume_id="higher_confidence",
                    resume_text=(
                        "Alex Chen\n"
                        "Summary\n"
                        "Backend engineer building Python services on AWS.\n"
                        "Skills\n"
                        "Python, FastAPI, AWS, Docker\n"
                        "Experience\n"
                        "Senior Backend Engineer at Example\n"
                        "Built backend APIs and services on AWS using FastAPI.\n"
                        "Projects\n"
                        "Platform migration to Docker and Python microservices.\n"
                        "Education\n"
                        "B.S. in Computer Science\n"
                    ),
                ),
            ],
            job_description_text=(
                "Senior Backend Engineer\n"
                "Example Co\n"
                "Responsibilities\n"
                "Build backend APIs and platform services.\n"
                "Required\n"
                "- Python\n"
                "- FastAPI\n"
                "- AWS\n"
                "Preferred\n"
                "- Docker\n"
                "Education\n"
                "- Bachelor's degree in Computer Science or related field preferred\n"
            ),
        )
    )

    assert [entry.resume_id for entry in response.ranking] == [
        "higher_confidence",
        "low_confidence",
    ]
    assert response.ranking[0].overall_score == response.ranking[1].overall_score
    assert response.ranking[0].parser_confidence.score > response.ranking[1].parser_confidence.score


def test_compare_resumes_to_jd_trace_ends_with_rank_resumes() -> None:
    response = compare_resumes_to_jd(
        MultiResumeComparisonRequest(
            resumes=[
                ResumeComparisonInput(
                    resume_id="strong",
                    resume_text=load_sample("strong_fit_resume.txt"),
                ),
                ResumeComparisonInput(
                    resume_id="poor",
                    resume_text=load_sample("poor_fit_resume.txt"),
                ),
            ],
            job_description_text=load_sample("strong_fit_jd.txt"),
        )
    )

    assert response.workflow_trace is not None
    assert response.workflow_trace.steps[-1].step_name == "rank_resumes"
    assert [step.step_name for step in response.workflow_trace.steps] == [
        "parse_job_description",
        "parse_resume",
        "score_match",
        "compute_blockers",
        "rank_resumes",
    ]
