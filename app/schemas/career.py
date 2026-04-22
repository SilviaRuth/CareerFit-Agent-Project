"""Schemas for advanced career workflow assistance in Milestone 5."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import EvidenceSpan
from app.schemas.match import AdaptationSummary, BlockerFlags, EvidenceSummary, GapItem
from app.schemas.parse import ParserConfidence
from app.schemas.resume import ResumeSchema


class CandidateMemoryItem(BaseModel):
    """One bounded, auditable memory item derived from the candidate resume only."""

    label: str
    memory_type: Literal["skill", "experience", "project", "education", "summary"]
    support_level: Literal["strong", "weak"]
    note: str
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)


class CandidateProfileAudit(BaseModel):
    """Audit metadata describing the scope and limits of reusable candidate context."""

    source_name: str | None = None
    profile_scope: Literal["request_bound"] = "request_bound"
    persistence: Literal["none"] = "none"
    derived_from_resume_only: bool = True
    audit_notes: list[str] = Field(default_factory=list)


class CandidateProfileMemory(BaseModel):
    """Reusable candidate context with explicit boundaries and traceable evidence."""

    profile_id: str
    candidate_name: str
    parser_confidence: ParserConfidence
    strongest_capabilities: list[str] = Field(default_factory=list)
    development_areas: list[str] = Field(default_factory=list)
    domain_signals: list[str] = Field(default_factory=list)
    memory_items: list[CandidateMemoryItem] = Field(default_factory=list)
    parsed_resume: ResumeSchema
    audit: CandidateProfileAudit


class ProfileMemoryRequest(BaseModel):
    """Request contract for building request-scoped candidate profile memory."""

    resume_text: str
    source_name: str | None = None


class CandidateProfileReference(BaseModel):
    """Shared input shape for raw resume input or reusable candidate profile memory."""

    resume_text: str | None = None
    resume_source_name: str | None = None
    profile_memory: CandidateProfileMemory | None = None

    @model_validator(mode="after")
    def validate_candidate_source(self) -> "CandidateProfileReference":
        has_resume = bool(self.resume_text)
        has_memory = self.profile_memory is not None
        if has_resume == has_memory:
            raise ValueError(
                "Provide exactly one candidate source: raw `resume_text` or `profile_memory`."
            )
        return self


class RetrievedEvidenceItem(BaseModel):
    """One evidence item returned by the bounded retrieval helper."""

    label: str
    source_section: str
    score: float
    reason: str
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)


class EvidenceRetrievalRequest(CandidateProfileReference):
    """Request contract for bounded candidate-evidence retrieval."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


class EvidenceRetrievalResponse(BaseModel):
    """Structured evidence retrieval output for recommendation grounding."""

    query: str
    retrieval_mode: Literal["keyword"]
    retrieved_items: list[RetrievedEvidenceItem] = Field(default_factory=list)
    audit_note: str


class SemanticMatchSignal(BaseModel):
    """Additive semantic-alignment hint that does not rewrite the core match score."""

    query_label: str
    matched_label: str
    confidence: Literal["high", "medium", "low"]
    reason: str
    evidence_used: list[EvidenceSpan] = Field(default_factory=list)


class SemanticMatchRequest(CandidateProfileReference):
    """Request contract for explicit semantic-alignment hints."""

    labels: list[str] = Field(min_length=1)
    mode: Literal["off", "heuristic"] = "heuristic"
    top_k: int = Field(default=5, ge=1, le=10)


class SemanticMatchResponse(BaseModel):
    """Additive semantic output that stays separate from deterministic scoring."""

    mode: Literal["off", "heuristic"]
    signals: list[SemanticMatchSignal] = Field(default_factory=list)
    note: str


class JobDescriptionInput(BaseModel):
    """One job description to compare against a shared candidate profile."""

    jd_id: str
    job_description_text: str
    source_name: str | None = None


class JobComparisonRequest(CandidateProfileReference):
    """Request contract for cross-JD opportunity ranking."""

    job_descriptions: list[JobDescriptionInput] = Field(min_length=1)
    retrieval_mode: Literal["keyword"] = "keyword"
    semantic_mode: Literal["off", "heuristic"] = "heuristic"


class JobComparisonResult(BaseModel):
    """One ranked JD opportunity for a shared candidate profile."""

    rank: int
    jd_id: str
    job_title: str
    company: str
    overall_score: int
    fit_label: str
    blocker_flags: BlockerFlags
    parser_confidence: ParserConfidence
    strengths: list[str] = Field(default_factory=list)
    top_gaps: list[GapItem] = Field(default_factory=list)
    adaptation_summary: AdaptationSummary = Field(default_factory=AdaptationSummary)
    evidence_summary: EvidenceSummary = Field(default_factory=EvidenceSummary)
    retrieved_evidence: list[RetrievedEvidenceItem] = Field(default_factory=list)
    semantic_support: list[SemanticMatchSignal] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    score_delta_from_best: int = 0


class JobComparisonResponse(BaseModel):
    """Structured output for ranking multiple JDs against one candidate profile."""

    summary: str
    compared_count: int
    candidate_profile: CandidateProfileMemory
    ranking: list[JobComparisonResult] = Field(default_factory=list)
