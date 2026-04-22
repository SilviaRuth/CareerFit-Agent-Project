"""Unit tests for grounded learning-plan generation."""

from __future__ import annotations

from app.services.generation.learning_plan_service import generate_learning_plan_from_text
from tests.conftest import load_sample


def test_learning_plan_targets_grounded_gaps_and_strengths() -> None:
    response = generate_learning_plan_from_text(
        load_sample("partial_fit_resume.txt"),
        load_sample("partial_fit_jd.txt"),
    )

    assert response.focus_areas
    assert response.plan_steps
    assert response.supporting_strengths
    assert any(item.target_requirement_label == "fastapi" for item in response.focus_areas)
    assert any(step.evidence_used for step in response.plan_steps)
    assert any(strength.label == "python" for strength in response.supporting_strengths)


def test_learning_plan_adds_guardrail_step_for_unsupported_claims() -> None:
    response = generate_learning_plan_from_text(
        load_sample("alex_claimy_resume.txt"),
        load_sample("strong_fit_jd.txt"),
    )

    assert response.blocker_cautions
    assert any("unsupported claims" in caution.lower() for caution in response.blocker_cautions)
    assert any(
        step.step_type == "address_blocker"
        and "summary claims" in step.action.lower()
        for step in response.plan_steps
    )


def test_learning_plan_stays_conservative_in_minimal_mode() -> None:
    response = generate_learning_plan_from_text(
        load_sample("low_confidence_resume.txt"),
        load_sample("responsibility_heavy_jd.txt"),
    )

    assert response.gating.generation_mode == "minimal"
    assert "conservative" in response.summary.lower()
    assert all(step.time_horizon in {"now", "next"} for step in response.plan_steps)
