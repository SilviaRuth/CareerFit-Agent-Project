"""Unit tests for grounded interview-prep generation."""

from __future__ import annotations

from app.services.generation.interview_prep_service import generate_interview_prep_from_text
from tests.conftest import load_sample


def test_interview_prep_contains_grounded_questions_and_talking_points() -> None:
    response = generate_interview_prep_from_text(
        load_sample("strong_fit_resume.txt"),
        load_sample("strong_fit_jd.txt"),
    )

    assert response.likely_focus_areas
    assert response.interview_questions
    assert response.recommended_talking_points
    assert any(question.evidence_used for question in response.interview_questions)
    assert all(point.evidence_used for point in response.recommended_talking_points)


def test_interview_prep_uses_honest_framing_for_weak_areas() -> None:
    response = generate_interview_prep_from_text(
        load_sample("partial_fit_resume.txt"),
        load_sample("partial_fit_jd.txt"),
    )

    assert response.weak_area_preparation
    fastapi_prep = next(
        item for item in response.weak_area_preparation if item.requirement_label == "fastapi"
    )
    assert "does not yet show strong direct evidence" in fastapi_prep.honest_framing.lower()


def test_interview_prep_does_not_generate_unsupported_talking_points() -> None:
    response = generate_interview_prep_from_text(
        load_sample("poor_fit_resume.txt"),
        load_sample("poor_fit_jd.txt"),
    )

    topics = {item.topic for item in response.recommended_talking_points}

    assert "fastapi" not in topics
    assert any(item.requirement_label == "fastapi" for item in response.weak_area_preparation)
