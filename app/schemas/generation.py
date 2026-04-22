"""Schemas for grounded generation workflows."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import EvidenceSpan
from app.schemas.parse import ParserConfidence


class GroundedGenerationRequest(BaseModel):
    """Text input contract for grounded generation endpoints."""

    resume_text: str
    job_description_text: str
    resume_source_name: str | None = None
    jd_source_name: str | None = None


class GenerationWarning(BaseModel):
    """Warning emitted by generation guardrails or bounded output logic."""

    warning_code: str
    message: str
    severity: Literal["info", "warning", "error"] = "warning"
    limited_output: bool = False


class GenerationGate(BaseModel):
    """Structured gating metadata for grounded generation."""

    generation_mode: Literal["full", "limited", "minimal"]
    resume_parser_confidence: ParserConfidence
    jd_parser_confidence: ParserConfidence
    limited_by_low_parser_confidence: bool = False
    limited_by_missing_evidence: bool = False
    limited_by_blockers: bool = False
    reasons: list[str] = Field(default_factory=list)


class RewriteAction(BaseModel):
    """One prioritized rewrite action grounded in gaps, matches, or warnings."""

    priority: int
    category: Literal[
        "required_gap",
        "preferred_gap",
        "weak_evidence",
        "seniority_gap",
        "education_gap",
        "domain_gap",
        "parser_limit",
    ]
    target_requirement_id: str | None = None
    target_requirement_label: str | None = None
    explanation: str
    recommendation: str
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    caution: str | None = None


class RewrittenBullet(BaseModel):
    """A bounded bullet suggestion linked to existing evidence."""

    target_section: Literal["summary", "experience", "projects"]
    support_level: Literal["strong", "weak"]
    target_requirement_id: str | None = None
    target_requirement_label: str | None = None
    original_text: str | None = None
    suggested_text: str
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    caution: str | None = None


class RewriteResponse(BaseModel):
    """Machine-reviewable output for `POST /rewrite`."""

    summary: str
    prioritized_actions: list[RewriteAction] = Field(default_factory=list)
    rewritten_summary: str | None = None
    rewritten_bullets: list[RewrittenBullet] = Field(default_factory=list)
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    unsupported_requests: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)
    generation_warnings: list[GenerationWarning] = Field(default_factory=list)
    gating: GenerationGate


class InterviewFocusArea(BaseModel):
    """Likely interview focus area grounded in JD responsibilities or requirements."""

    priority: int
    focus_area: str
    reason: str
    related_requirement_id: str | None = None
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    caution: str | None = None


class InterviewQuestion(BaseModel):
    """Structured interview question prompt grounded in the current fit analysis."""

    priority: int
    question: str
    rationale: str
    related_requirement_id: str | None = None
    support_level: Literal["strong", "weak", "missing"]
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    honest_framing: str | None = None


class TalkingPoint(BaseModel):
    """Safe talking point supported by extracted resume evidence."""

    topic: str
    talking_point: str
    support_level: Literal["strong", "weak"]
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    caution: str | None = None


class WeakAreaPreparation(BaseModel):
    """Truthful prep guidance for a weak area or blocker."""

    requirement_label: str
    gap_type: str
    honest_framing: str
    preparation_steps: list[str] = Field(default_factory=list)
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)


class InterviewPrepResponse(BaseModel):
    """Machine-reviewable output for `POST /interview-prep`."""

    summary: str
    likely_focus_areas: list[InterviewFocusArea] = Field(default_factory=list)
    interview_questions: list[InterviewQuestion] = Field(default_factory=list)
    recommended_talking_points: list[TalkingPoint] = Field(default_factory=list)
    weak_area_preparation: list[WeakAreaPreparation] = Field(default_factory=list)
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    generation_warnings: list[GenerationWarning] = Field(default_factory=list)
    gating: GenerationGate


class InterviewSimulationRound(BaseModel):
    """One mock interview exchange aligned to strengths, responsibilities, or weak areas."""

    priority: int
    round_type: Literal["responsibility_probe", "strength_probe", "gap_probe"]
    prompt: str
    intent: str
    answer_strategy: str
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    caution: str | None = None


class InterviewSimulationResponse(BaseModel):
    """Structured output for `POST /interview-sim`."""

    summary: str
    scenario_focus: list[str] = Field(default_factory=list)
    simulation_rounds: list[InterviewSimulationRound] = Field(default_factory=list)
    coach_notes: list[str] = Field(default_factory=list)
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    generation_warnings: list[GenerationWarning] = Field(default_factory=list)
    gating: GenerationGate


class LearningPlanFocusArea(BaseModel):
    """One grounded learning-plan focus area derived from explicit gaps or strengths."""

    priority: int
    focus_type: Literal["gap", "blocker", "strength_maintenance"]
    target_requirement_id: str | None = None
    target_requirement_label: str
    gap_type: str | None = None
    requirement_priority: Literal["required", "preferred"] | None = None
    rationale: str
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    caution: str | None = None


class SupportingStrength(BaseModel):
    """A supported capability the learning plan can build on safely."""

    priority: int
    label: str
    explanation: str
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)


class LearningPlanStep(BaseModel):
    """One deterministic learning action tied to a gap, blocker, or supported strength."""

    priority: int
    time_horizon: Literal["now", "next", "later"]
    step_type: Literal[
        "close_required_gap",
        "strengthen_evidence",
        "address_blocker",
        "build_adjacent_project",
        "maintain_strength",
    ]
    target_requirement_id: str | None = None
    target_requirement_label: str | None = None
    action: str
    reason: str
    success_signal: str
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    caution: str | None = None


class LearningPlanResponse(BaseModel):
    """Machine-reviewable output for `POST /learning-plan`."""

    summary: str
    focus_areas: list[LearningPlanFocusArea] = Field(default_factory=list)
    plan_steps: list[LearningPlanStep] = Field(default_factory=list)
    supporting_strengths: list[SupportingStrength] = Field(default_factory=list)
    blocker_cautions: list[str] = Field(default_factory=list)
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)
    generation_warnings: list[GenerationWarning] = Field(default_factory=list)
    gating: GenerationGate
