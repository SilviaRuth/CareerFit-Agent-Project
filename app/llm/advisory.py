"""Optional advisory generation orchestration."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.llm.base import LLMClient
from app.llm.config import LLMSettings, load_llm_settings
from app.llm.errors import LLMError
from app.llm.prompts import build_advisory_prompt
from app.llm.providers import build_llm_client
from app.llm.validators import validate_grounding
from app.schemas.generation import GroundedGenerationRequest
from app.schemas.llm_generation import (
    DeterministicAdvisoryResult,
    LLMAdvice,
    LLMAdvisoryResponse,
    LLMRecommendationOutput,
    LLMValidationReport,
)
from app.services.orchestration_service import build_grounded_context


def run_llm_advisory_generation(
    request: GroundedGenerationRequest,
    *,
    client: LLMClient | None = None,
    settings: LLMSettings | None = None,
) -> LLMAdvisoryResponse:
    """Return deterministic results plus optional validated LLM advice."""
    resolved_settings = settings or load_llm_settings()
    context = build_grounded_context(request)
    if context.gating is None:
        raise ValueError("LLM advisory generation requires populated gating metadata.")

    deterministic_result = DeterministicAdvisoryResult(
        resume_parse=context.resume_parse,
        jd_parse=context.jd_parse,
        match_result=context.match_result,
        gating=context.gating,
    )

    if not resolved_settings.enable_llm_generation:
        return _response(
            deterministic_result,
            resolved_settings,
            status="disabled",
            report=LLMValidationReport(errors=["LLM generation is disabled."]),
            warning="Set ENABLE_LLM_GENERATION=true to opt in to advisory LLM output.",
        )

    try:
        resolved_client = client or build_llm_client(resolved_settings)
        raw_output = resolved_client.generate_json(
            build_advisory_prompt(context),
            "LLMRecommendationOutput",
        )
    except LLMError as exc:
        return _response(
            deterministic_result,
            resolved_settings,
            status="fallback",
            report=LLMValidationReport(errors=[str(exc)]),
            warning="LLM advisory generation fell back to deterministic-only output.",
        )

    parsed_output, schema_report = _parse_schema(raw_output)
    if parsed_output is None:
        return _response(
            deterministic_result,
            resolved_settings,
            status="fallback",
            report=schema_report,
            warning="LLM output failed schema validation.",
        )

    validation_report = validate_grounding(parsed_output, context)
    if not validation_report.grounding_valid:
        return _response(
            deterministic_result,
            resolved_settings,
            status="rejected",
            report=validation_report,
            warning="LLM output failed grounding validation.",
        )

    return LLMAdvisoryResponse(
        deterministic_result=deterministic_result,
        llm_status="validated",
        llm_advice=LLMAdvice(
            enabled=True,
            status="validated",
            provider=resolved_settings.provider,
            model=resolved_settings.model,
            summary=parsed_output.summary,
            recommendations=parsed_output.recommendations,
            limitations=parsed_output.limitations,
            warnings=[],
        ),
        validation_report=validation_report,
    )


def _parse_schema(raw_output: dict[str, Any] | str) -> tuple[
    LLMRecommendationOutput | None,
    LLMValidationReport,
]:
    try:
        candidate = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
        return (
            LLMRecommendationOutput.model_validate(candidate),
            LLMValidationReport(schema_valid=True),
        )
    except (json.JSONDecodeError, TypeError, ValidationError) as exc:
        return (
            None,
            LLMValidationReport(
                schema_valid=False,
                grounding_valid=False,
                evidence_coverage=0.0,
                errors=[f"schema_validation_failed: {exc}"],
            ),
        )


def _response(
    deterministic_result: DeterministicAdvisoryResult,
    settings: LLMSettings,
    *,
    status: str,
    report: LLMValidationReport,
    warning: str,
) -> LLMAdvisoryResponse:
    return LLMAdvisoryResponse(
        deterministic_result=deterministic_result,
        llm_status=status,
        llm_advice=LLMAdvice(
            enabled=settings.enable_llm_generation,
            status=status,
            provider=settings.provider,
            model=settings.model,
            summary=None,
            recommendations=[],
            limitations=[],
            warnings=[warning],
        ),
        validation_report=report,
    )

