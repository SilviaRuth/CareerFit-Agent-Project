"""Unit tests for the single-orchestrator grounded generation service."""

from __future__ import annotations

from app.schemas.generation import GroundedGenerationRequest
from app.services.orchestration_service import (
    build_grounded_context,
    run_grounded_interview_prep_flow,
    run_grounded_learning_plan_flow,
    run_grounded_rewrite_flow,
)
from tests.conftest import load_sample


def test_orchestrator_rewrite_flow_handles_strong_fit() -> None:
    response = run_grounded_rewrite_flow(
        GroundedGenerationRequest(
            resume_text=load_sample("strong_fit_resume.txt"),
            job_description_text=load_sample("strong_fit_jd.txt"),
        )
    )

    assert response.gating.generation_mode == "full"
    assert response.evidence_used
    assert response.prioritized_actions or response.rewritten_bullets


def test_orchestrator_interview_prep_flow_handles_partial_fit() -> None:
    response = run_grounded_interview_prep_flow(
        GroundedGenerationRequest(
            resume_text=load_sample("partial_fit_resume.txt"),
            job_description_text=load_sample("partial_fit_jd.txt"),
        )
    )

    assert response.gating.generation_mode == "minimal"
    assert response.weak_area_preparation
    assert any(item.requirement_label == "fastapi" for item in response.weak_area_preparation)


def test_orchestrator_gating_downgrades_for_low_parser_confidence() -> None:
    context = build_grounded_context(
        GroundedGenerationRequest(
            resume_text=load_sample("low_confidence_resume.txt"),
            job_description_text=load_sample("responsibility_heavy_jd.txt"),
        )
    )

    assert context.gating is not None
    assert context.gating.generation_mode == "minimal"
    assert "low_parser_confidence" in context.gating.reasons
    assert context.generation_warnings
    assert context.evidence_registry


def test_orchestrator_learning_plan_flow_handles_partial_fit() -> None:
    response = run_grounded_learning_plan_flow(
        GroundedGenerationRequest(
            resume_text=load_sample("partial_fit_resume.txt"),
            job_description_text=load_sample("partial_fit_jd.txt"),
        )
    )

    assert response.focus_areas
    assert response.plan_steps
    assert response.supporting_strengths
    assert any(item.target_requirement_label == "fastapi" for item in response.focus_areas)
