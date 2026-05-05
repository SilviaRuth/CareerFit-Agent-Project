"""Match request and result contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import EvidenceSpan
from app.schemas.llm_extraction import LLMExtractionReport
from app.schemas.workflow import WorkflowTrace


class MatchRequest(BaseModel):
    """Input contract for the deterministic `/match` endpoint."""

    resume_text: str
    job_description_text: str


class RequirementMatch(BaseModel):
    """Status for one required or preferred requirement."""

    requirement_id: str
    requirement_label: str
    normalized_label: str
    requirement_priority: str
    requirement_type: str
    status: str
    explanation: str
    resume_evidence: list[EvidenceSpan] = Field(default_factory=list)
    jd_evidence: list[EvidenceSpan] = Field(default_factory=list)


class GapItem(BaseModel):
    """A missing or weak qualification surfaced by the matcher."""

    requirement_id: str
    requirement_label: str
    requirement_priority: str
    gap_type: str
    explanation: str
    resume_evidence: list[EvidenceSpan] = Field(default_factory=list)
    jd_evidence: list[EvidenceSpan] = Field(default_factory=list)


class DimensionScores(BaseModel):
    """Per-dimension scores that sum into the overall score."""

    skills: int
    experience: int
    projects: int
    domain_fit: int
    education: int


class BlockerFlags(BaseModel):
    """High-risk issues that must stay explicit even with a solid score."""

    missing_required_skills: bool = False
    seniority_mismatch: bool = False
    unsupported_claims: bool = False


class EvidenceSummary(BaseModel):
    """High-level evidence tracing summary for review and regression analysis."""

    total_evidence_spans: int = 0
    resume_evidence_spans: int = 0
    jd_evidence_spans: int = 0
    resume_section_counts: dict[str, int] = Field(default_factory=dict)
    jd_section_counts: dict[str, int] = Field(default_factory=dict)
    required_match_count: int = 0
    preferred_match_count: int = 0
    gap_count: int = 0


class AdaptationSummary(BaseModel):
    """Deterministic role/company emphasis summary for reviewable output shaping."""

    role_focus: str = ""
    company_signals: list[str] = Field(default_factory=list)
    emphasized_requirements: list[str] = Field(default_factory=list)
    prioritized_strengths: list[str] = Field(default_factory=list)
    prioritized_gaps: list[str] = Field(default_factory=list)
    explanation: str = ""


class MatchResult(BaseModel):
    """Structured output for the deterministic matching pipeline."""

    overall_score: int
    dimension_scores: DimensionScores
    required_matches: list[RequirementMatch] = Field(default_factory=list)
    preferred_matches: list[RequirementMatch] = Field(default_factory=list)
    gaps: list[GapItem] = Field(default_factory=list)
    blocker_flags: BlockerFlags
    strengths: list[str] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    evidence_summary: EvidenceSummary = Field(default_factory=EvidenceSummary)
    adaptation_summary: AdaptationSummary = Field(default_factory=AdaptationSummary)
    llm_extraction: LLMExtractionReport | None = None
    workflow_trace: WorkflowTrace | None = None
