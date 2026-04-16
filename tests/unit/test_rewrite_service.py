"""Unit tests for grounded rewrite generation."""

from __future__ import annotations

from app.services.generation.rewrite_service import generate_rewrite_response_from_text
from tests.conftest import load_sample


def test_rewrite_response_contains_evidence_references_for_grounded_output() -> None:
    response = generate_rewrite_response_from_text(
        load_sample("strong_fit_resume.txt"),
        load_sample("strong_fit_jd.txt"),
    )

    assert response.gating.generation_mode in {"full", "limited"}
    assert response.evidence_used
    assert response.prioritized_actions or response.rewritten_bullets
    assert any(item.evidence_used for item in response.prioritized_actions) or any(
        item.evidence_used for item in response.rewritten_bullets
    )


def test_rewrite_low_parser_confidence_degrades_to_minimal_output() -> None:
    response = generate_rewrite_response_from_text(
        load_sample("low_confidence_resume.txt"),
        load_sample("responsibility_heavy_jd.txt"),
    )

    warning_codes = {warning.warning_code for warning in response.generation_warnings}

    assert response.gating.generation_mode == "minimal"
    assert response.rewritten_summary is None
    assert response.rewritten_bullets == []
    assert "low_parser_confidence" in warning_codes


def test_rewrite_missing_skill_does_not_generate_fabricated_bullet() -> None:
    response = generate_rewrite_response_from_text(
        load_sample("poor_fit_resume.txt"),
        load_sample("poor_fit_jd.txt"),
    )

    bullet_targets = {bullet.target_requirement_label for bullet in response.rewritten_bullets}

    assert "fastapi" not in bullet_targets
    assert any("fastapi" in message.lower() for message in response.unsupported_requests)
    assert any(
        action.target_requirement_label == "fastapi" and "Do not add" in action.recommendation
        for action in response.prioritized_actions
    )
