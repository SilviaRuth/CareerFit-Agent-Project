"""Strict schemas for optional validated LLM advisory output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.generation import GenerationGate
from app.schemas.match import MatchResult
from app.schemas.parse import JDParseResponse, ResumeParseResponse


class StrictLLMModel(BaseModel):
    """Base model for rejecting loose or unexpected LLM fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class LLMEvidenceRef(StrictLLMModel):
    """Evidence reference that must map back to deterministic artifacts."""

    source: Literal["resume", "job_description", "match_result", "generation_gate"]
    field: str
    text: str


class LLMRecommendationItem(StrictLLMModel):
    """One advisory recommendation returned by an LLM client."""

    category: Literal["skills", "experience", "education", "project", "resume_wording"]
    recommendation: str
    priority: Literal["high", "medium", "low"]
    evidence_refs: list[LLMEvidenceRef] = Field(min_length=1)
    unsupported_claim_risk: bool = False


class LLMRecommendationOutput(StrictLLMModel):
    """Validated raw model output before grounding checks."""

    summary: str
    recommendations: list[LLMRecommendationItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class LLMValidationReport(StrictLLMModel):
    """Deterministic validation result for optional LLM output."""

    schema_valid: bool = False
    grounding_valid: bool = False
    unsupported_claims: list[str] = Field(default_factory=list)
    evidence_coverage: float = 0.0
    errors: list[str] = Field(default_factory=list)


class LLMAdvice(StrictLLMModel):
    """Separate advisory payload that never mutates deterministic results."""

    enabled: bool
    status: Literal["disabled", "validated", "rejected", "fallback"]
    provider: str
    model: str
    summary: str | None = None
    recommendations: list[LLMRecommendationItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DeterministicAdvisoryResult(StrictLLMModel):
    """Deterministic source-of-truth artifacts consumed by advisory prompts."""

    resume_parse: ResumeParseResponse
    jd_parse: JDParseResponse
    match_result: MatchResult
    gating: GenerationGate


class LLMAdvisoryResponse(StrictLLMModel):
    """Output contract for optional advisory generation."""

    deterministic_result: DeterministicAdvisoryResult
    llm_status: Literal["disabled", "validated", "rejected", "fallback"]
    llm_advice: LLMAdvice
    validation_report: LLMValidationReport

