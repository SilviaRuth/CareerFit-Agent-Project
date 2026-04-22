"""Unit tests for grounded interview simulation."""

from __future__ import annotations

from app.services.generation.interview_simulation_service import (
    generate_interview_simulation_from_text,
)
from tests.conftest import load_sample


def test_interview_simulation_stays_grounded_and_conservative_for_low_confidence() -> None:
    response = generate_interview_simulation_from_text(
        load_sample("low_confidence_resume.txt"),
        load_sample("responsibility_heavy_jd.txt"),
    )

    assert response.gating.generation_mode == "minimal"
    assert response.simulation_rounds
    assert any(round_item.caution for round_item in response.simulation_rounds)
