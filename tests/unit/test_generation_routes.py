"""Unit tests ensuring generation routes stay thin."""

from __future__ import annotations

from app.api.routes.generation import interview_prep, rewrite_resume
from app.schemas.generation import (
    GenerationGate,
    GroundedGenerationRequest,
    InterviewPrepResponse,
    RewriteResponse,
)


def test_rewrite_route_delegates_to_orchestrator(monkeypatch) -> None:
    request = GroundedGenerationRequest(
        resume_text="resume",
        job_description_text="jd",
    )
    captured: dict[str, GroundedGenerationRequest] = {}
    expected = RewriteResponse(
        summary="rewrite",
        prioritized_actions=[],
        rewritten_summary=None,
        rewritten_bullets=[],
        evidence_used=[],
        unsupported_requests=[],
        cautions=[],
        generation_warnings=[],
        gating=_sample_gate(),
    )

    def fake_flow(incoming: GroundedGenerationRequest) -> RewriteResponse:
        captured["request"] = incoming
        return expected

    monkeypatch.setattr("app.api.routes.generation.run_grounded_rewrite_flow", fake_flow)

    response = rewrite_resume(request)

    assert response == expected
    assert captured["request"] == request


def test_interview_prep_route_delegates_to_orchestrator(monkeypatch) -> None:
    request = GroundedGenerationRequest(
        resume_text="resume",
        job_description_text="jd",
    )
    captured: dict[str, GroundedGenerationRequest] = {}
    expected = InterviewPrepResponse(
        summary="prep",
        likely_focus_areas=[],
        interview_questions=[],
        recommended_talking_points=[],
        weak_area_preparation=[],
        evidence_used=[],
        generation_warnings=[],
        gating=_sample_gate(),
    )

    def fake_flow(incoming: GroundedGenerationRequest) -> InterviewPrepResponse:
        captured["request"] = incoming
        return expected

    monkeypatch.setattr("app.api.routes.generation.run_grounded_interview_prep_flow", fake_flow)

    response = interview_prep(request)

    assert response == expected
    assert captured["request"] == request


def _sample_gate() -> GenerationGate:
    return GenerationGate(
        generation_mode="limited",
        resume_parser_confidence={
            "score": 0.82,
            "level": "medium",
            "extraction_complete": True,
            "factors": [],
        },
        jd_parser_confidence={
            "score": 0.93,
            "level": "high",
            "extraction_complete": True,
            "factors": [],
        },
        limited_by_low_parser_confidence=False,
        limited_by_missing_evidence=True,
        limited_by_blockers=False,
        reasons=["significant_missing_evidence"],
    )
