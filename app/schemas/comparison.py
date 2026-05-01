"""Schemas for multi-resume comparison against one JD."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.match import (
    AdaptationSummary,
    BlockerFlags,
    DimensionScores,
    EvidenceSummary,
    GapItem,
)
from app.schemas.parse import ParserConfidence
from app.schemas.workflow import WorkflowTrace


class ResumeComparisonInput(BaseModel):
    """One resume candidate to compare against a shared JD."""

    resume_id: str
    resume_text: str
    source_name: str | None = None


class MultiResumeComparisonRequest(BaseModel):
    """Input contract for ranking multiple resumes against one JD."""

    resumes: list[ResumeComparisonInput] = Field(min_length=1)
    job_description_text: str
    jd_source_name: str | None = None


class ResumeComparisonResult(BaseModel):
    """One ranked resume entry in the comparison output."""

    rank: int
    resume_id: str
    overall_score: int
    fit_label: str
    blocker_flags: BlockerFlags
    dimension_scores: DimensionScores
    parser_confidence: ParserConfidence
    strengths: list[str] = Field(default_factory=list)
    top_gaps: list[GapItem] = Field(default_factory=list)
    evidence_summary: EvidenceSummary = Field(default_factory=EvidenceSummary)
    adaptation_summary: AdaptationSummary = Field(default_factory=AdaptationSummary)
    score_delta_from_best: int = 0


class MultiResumeComparisonResponse(BaseModel):
    """Structured output for multi-resume comparison."""

    summary: str
    compared_count: int
    job_title: str
    company: str
    jd_parser_confidence: ParserConfidence
    ranking: list[ResumeComparisonResult] = Field(default_factory=list)
    workflow_trace: WorkflowTrace | None = None
