"""Shared schemas used across extraction and matching."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceSpan(BaseModel):
    """A traceable source span used to ground extraction and matching decisions."""

    source_document: str
    section: str
    text: str
    start_char: int | None = None
    end_char: int | None = None
    normalized_value: str | None = None
    explanation: str


class SkillSignal(BaseModel):
    """A normalized resume skill with evidence and strength metadata."""

    name: str
    normalized_name: str
    evidence_strength: str = "weak"
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    """A deterministic experience block extracted from the fixture resume format."""

    heading: str
    organization: str | None = None
    summary: str
    start_year: int | None = None
    end_year: int | None = None
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)


class ProjectItem(BaseModel):
    """A deterministic project block extracted from the fixture resume format."""

    summary: str
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)


class EducationItem(BaseModel):
    """A deterministic education block extracted from the fixture format."""

    summary: str
    degree: str | None = None
    field: str | None = None
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)


class RequirementItem(BaseModel):
    """A normalized requirement extracted from the JD."""

    requirement_id: str
    label: str
    normalized_label: str
    priority: str
    requirement_type: str
    raw_text: str
    min_years: float | None = None
    evidence_span: EvidenceSpan
