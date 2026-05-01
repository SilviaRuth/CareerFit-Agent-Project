"""Unit tests for optional validated LLM advisory generation."""

from __future__ import annotations

from app.llm.advisory import run_llm_advisory_generation
from app.llm.config import LLMSettings
from app.llm.providers import FakeLLMClient
from app.schemas.generation import GroundedGenerationRequest
from app.services.orchestration_service import build_grounded_context
from tests.conftest import load_sample


def test_llm_advisory_generation_is_disabled_by_default() -> None:
    response = run_llm_advisory_generation(
        _request(),
        settings=LLMSettings(),
    )

    assert response.llm_status == "disabled"
    assert response.llm_advice.enabled is False
    assert response.llm_advice.recommendations == []
    assert response.deterministic_result.match_result.overall_score > 0


def test_llm_advisory_generation_falls_back_without_api_key() -> None:
    response = run_llm_advisory_generation(
        _request(),
        settings=LLMSettings(enable_llm_generation=True, provider="openai", api_key=None),
    )

    assert response.llm_status == "fallback"
    assert response.llm_advice.recommendations == []
    assert response.deterministic_result.match_result.required_matches
    assert "no API key" in response.validation_report.errors[0]


def test_llm_advisory_generation_accepts_valid_grounded_output() -> None:
    evidence_text = _first_evidence_text()
    fake_client = FakeLLMClient(
        {
            "summary": "The deterministic match supports focused resume wording advice.",
            "recommendations": [
                {
                    "category": "resume_wording",
                    "recommendation": (
                        "Emphasize the verified FastAPI service work already present."
                    ),
                    "priority": "high",
                    "evidence_refs": [
                        {
                            "source": "resume",
                            "field": "experience",
                            "text": evidence_text,
                        }
                    ],
                    "unsupported_claim_risk": False,
                }
            ],
            "limitations": [],
        }
    )

    response = run_llm_advisory_generation(
        _request(),
        client=fake_client,
        settings=LLMSettings(enable_llm_generation=True, provider="fake"),
    )

    assert response.llm_status == "validated"
    assert response.validation_report.schema_valid is True
    assert response.validation_report.grounding_valid is True
    assert response.validation_report.evidence_coverage == 1.0
    assert response.llm_advice.recommendations[0].evidence_refs[0].text == evidence_text
    assert fake_client.calls[0][1] == "LLMRecommendationOutput"


def test_llm_advisory_generation_falls_back_on_invalid_json() -> None:
    response = run_llm_advisory_generation(
        _request(),
        client=FakeLLMClient("not valid json"),
        settings=LLMSettings(enable_llm_generation=True, provider="fake"),
    )

    assert response.llm_status == "fallback"
    assert response.validation_report.schema_valid is False
    assert response.llm_advice.recommendations == []


def test_llm_advisory_generation_rejects_evidence_not_in_deterministic_outputs() -> None:
    response = run_llm_advisory_generation(
        _request(),
        client=FakeLLMClient(
            {
                "summary": "Advice with no evidence should not be trusted.",
                "recommendations": [
                    {
                        "category": "skills",
                        "recommendation": "Improve Python positioning.",
                        "priority": "medium",
                        "evidence_refs": [
                            {
                                "source": "resume",
                                "field": "skills",
                                "text": "This text is not present in deterministic evidence.",
                            }
                        ],
                        "unsupported_claim_risk": False,
                    }
                ],
                "limitations": [],
            }
        ),
        settings=LLMSettings(enable_llm_generation=True, provider="fake"),
    )

    assert response.llm_status == "rejected"
    assert response.validation_report.schema_valid is True
    assert response.validation_report.grounding_valid is False
    assert response.validation_report.errors == ["recommendation_1_missing_supported_evidence"]


def test_llm_advisory_generation_rejects_unsupported_claims() -> None:
    evidence_text = _first_evidence_text()
    response = run_llm_advisory_generation(
        _request(),
        client=FakeLLMClient(
            {
                "summary": "The candidate can be positioned for verified backend strengths.",
                "recommendations": [
                    {
                        "category": "experience",
                        "recommendation": (
                            "Claim Fortune 500 Kubernetes leadership with 10x project impact."
                        ),
                        "priority": "high",
                        "evidence_refs": [
                            {
                                "source": "resume",
                                "field": "experience",
                                "text": evidence_text,
                            }
                        ],
                        "unsupported_claim_risk": False,
                    }
                ],
                "limitations": [],
            }
        ),
        settings=LLMSettings(enable_llm_generation=True, provider="fake"),
    )

    assert response.llm_status == "rejected"
    assert response.validation_report.schema_valid is True
    assert response.validation_report.grounding_valid is False
    assert response.validation_report.unsupported_claims
    assert response.llm_advice.recommendations == []


def _request() -> GroundedGenerationRequest:
    return GroundedGenerationRequest(
        resume_text=load_sample("strong_fit_resume.txt"),
        job_description_text=load_sample("strong_fit_jd.txt"),
    )


def _first_evidence_text() -> str:
    context = build_grounded_context(_request())
    return context.evidence_registry[0].text
