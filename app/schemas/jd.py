"""Job description schema contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import EvidenceSpan, RequirementItem


class JDSchema(BaseModel):
    """Canonical structured representation of a job description."""

    job_title: str
    company: str
    required_requirements: list[RequirementItem] = Field(default_factory=list)
    preferred_requirements: list[RequirementItem] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    education_requirements: list[RequirementItem] = Field(default_factory=list)
    seniority_hint: str | None = None
    domain_hint: str | None = None
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    normalized_text: str
