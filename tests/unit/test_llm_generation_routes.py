"""Unit tests ensuring the optional LLM advisory route stays thin."""

from __future__ import annotations

from app.api.routes.llm_generation import llm_advice
from app.schemas.generation import GroundedGenerationRequest
from app.schemas.llm_generation import (
    DeterministicAdvisoryResult,
    LLMAdvice,
    LLMAdvisoryResponse,
    LLMValidationReport,
)
from app.services.orchestration_service import build_grounded_context
from tests.conftest import load_sample


def test_llm_advice_route_delegates_to_orchestrator(monkeypatch) -> None:
    request = GroundedGenerationRequest(
        resume_text=load_sample("strong_fit_resume.txt"),
        job_description_text=load_sample("strong_fit_jd.txt"),
    )
    context = build_grounded_context(request)
    assert context.gating is not None
    expected = LLMAdvisoryResponse(
        deterministic_result=DeterministicAdvisoryResult(
            resume_parse=context.resume_parse,
            jd_parse=context.jd_parse,
            match_result=context.match_result,
            gating=context.gating,
        ),
        llm_status="disabled",
        llm_advice=LLMAdvice(
            enabled=False,
            status="disabled",
            provider="openai",
            model="gpt-5.4-mini",
            warnings=["disabled"],
        ),
        validation_report=LLMValidationReport(errors=["disabled"]),
    )
    captured: dict[str, GroundedGenerationRequest] = {}

    def fake_flow(incoming: GroundedGenerationRequest) -> LLMAdvisoryResponse:
        captured["request"] = incoming
        return expected

    monkeypatch.setattr("app.api.routes.llm_generation.run_llm_advisory_generation", fake_flow)

    response = llm_advice(request)

    assert response == expected
    assert captured["request"] == request
