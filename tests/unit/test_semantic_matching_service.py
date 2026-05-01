"""Unit tests for additive semantic matching hints."""

from __future__ import annotations

from app.schemas.career import SemanticMatchRequest
from app.services.candidate_profile_service import build_candidate_profile_memory
from app.services.semantic_matching_service import semantic_match_labels
from tests.conftest import load_sample


def test_semantic_matching_service_returns_additive_alias_hints() -> None:
    profile = build_candidate_profile_memory(load_sample("strong_fit_resume.txt"))

    response = semantic_match_labels(
        SemanticMatchRequest(
            profile_memory=profile,
            labels=["postgres", "api design"],
            mode="heuristic",
        )
    )

    assert response.signals
    assert any(signal.matched_label in {"postgresql", "rest_api"} for signal in response.signals)
    assert "additive" in response.note.lower()
    assert response.workflow_trace is not None
    assert response.workflow_trace.workflow_name == "semantic_match"
    assert [step.step_name for step in response.workflow_trace.steps] == [
        "resolve_candidate_profile",
        "semantic_match",
    ]
