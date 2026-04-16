"""Resume schema contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import EducationItem, EvidenceSpan, ExperienceItem, ProjectItem, SkillSignal


class ResumeSchema(BaseModel):
    """Canonical structured representation of a resume."""

    candidate_name: str
    summary: str
    skills: list[SkillSignal] = Field(default_factory=list)
    experience_items: list[ExperienceItem] = Field(default_factory=list)
    project_items: list[ProjectItem] = Field(default_factory=list)
    education_items: list[EducationItem] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    normalized_text: str
    total_years_experience: float | None = None
