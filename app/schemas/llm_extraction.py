"""Schemas for optional LLM-assisted natural-language extraction."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_EVIDENCE_TEXT_CHARS = 240
MAX_EVIDENCE_REFS_PER_ITEM = 2
MAX_RESUME_SKILLS = 20
MAX_RESUME_EXPERIENCE_ITEMS = 20
MAX_RESUME_PROJECT_ITEMS = 20
MAX_RESUME_EDUCATION_ITEMS = 20
MAX_JD_RESPONSIBILITIES = 20
MAX_JD_REQUIREMENTS = 20
MAX_JD_EDUCATION_REQUIREMENTS = 20


class StrictLLMExtractionModel(BaseModel):
    """Base model for strict LLM extraction payloads."""

    model_config = ConfigDict(extra="forbid", strict=True)


class LLMExtractionEvidenceRef(StrictLLMExtractionModel):
    """Evidence text that must exist in the original source document."""

    source: Literal["resume", "job_description"]
    field: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=MAX_EVIDENCE_TEXT_CHARS)


class LLMExtractedSkill(StrictLLMExtractionModel):
    """Skill extracted from unstructured resume text."""

    name: str = Field(min_length=1, max_length=120)
    evidence_refs: list[LLMExtractionEvidenceRef] = Field(
        min_length=1,
        max_length=MAX_EVIDENCE_REFS_PER_ITEM,
    )


class LLMExtractedExperience(StrictLLMExtractionModel):
    """Experience item extracted from unstructured resume text."""

    heading: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=360)
    organization: str | None = Field(default=None, max_length=160)
    start_year: int | None = None
    end_year: int | None = None
    evidence_refs: list[LLMExtractionEvidenceRef] = Field(
        min_length=1,
        max_length=MAX_EVIDENCE_REFS_PER_ITEM,
    )


class LLMExtractedProject(StrictLLMExtractionModel):
    """Project item extracted from unstructured resume text."""

    summary: str = Field(min_length=1, max_length=360)
    evidence_refs: list[LLMExtractionEvidenceRef] = Field(
        min_length=1,
        max_length=MAX_EVIDENCE_REFS_PER_ITEM,
    )


class LLMExtractedEducation(StrictLLMExtractionModel):
    """Education item extracted from unstructured resume text."""

    summary: str = Field(min_length=1, max_length=360)
    degree: str | None = Field(default=None, max_length=160)
    field: str | None = Field(default=None, max_length=160)
    evidence_refs: list[LLMExtractionEvidenceRef] = Field(
        min_length=1,
        max_length=MAX_EVIDENCE_REFS_PER_ITEM,
    )


class LLMResumeExtractionOutput(StrictLLMExtractionModel):
    """Structured resume extraction proposed by an LLM."""

    candidate_name: str = Field(max_length=160)
    summary: str = Field(max_length=500)
    skills: list[LLMExtractedSkill] = Field(
        default_factory=list,
        max_length=MAX_RESUME_SKILLS,
    )
    experience_items: list[LLMExtractedExperience] = Field(
        default_factory=list,
        max_length=MAX_RESUME_EXPERIENCE_ITEMS,
    )
    project_items: list[LLMExtractedProject] = Field(
        default_factory=list,
        max_length=MAX_RESUME_PROJECT_ITEMS,
    )
    education_items: list[LLMExtractedEducation] = Field(
        default_factory=list,
        max_length=MAX_RESUME_EDUCATION_ITEMS,
    )
    total_years_experience: float | None = None


class LLMExtractedRequirement(StrictLLMExtractionModel):
    """Job requirement extracted from unstructured JD text."""

    label: str = Field(min_length=1, max_length=160)
    raw_text: str = Field(min_length=1, max_length=240)
    priority: Literal["required", "preferred"]
    requirement_type: Literal[
        "skill",
        "experience",
        "education",
        "domain",
        "seniority",
        "other",
    ]
    min_years: float | None = None
    evidence_refs: list[LLMExtractionEvidenceRef] = Field(
        min_length=1,
        max_length=MAX_EVIDENCE_REFS_PER_ITEM,
    )


class LLMJDExtractionOutput(StrictLLMExtractionModel):
    """Structured JD extraction proposed by an LLM."""

    job_title: str = Field(max_length=160)
    company: str = Field(max_length=160)
    responsibilities: list[str] = Field(
        default_factory=list,
        max_length=MAX_JD_RESPONSIBILITIES,
    )
    required_requirements: list[LLMExtractedRequirement] = Field(
        default_factory=list,
        max_length=MAX_JD_REQUIREMENTS,
    )
    preferred_requirements: list[LLMExtractedRequirement] = Field(
        default_factory=list,
        max_length=MAX_JD_REQUIREMENTS,
    )
    education_requirements: list[LLMExtractedRequirement] = Field(
        default_factory=list,
        max_length=MAX_JD_EDUCATION_REQUIREMENTS,
    )
    seniority_hint: str | None = Field(default=None, max_length=120)
    domain_hint: str | None = Field(default=None, max_length=120)


class LLMNaturalLanguageExtractionOutput(StrictLLMExtractionModel):
    """Combined extraction output for one resume and one job description."""

    resume: LLMResumeExtractionOutput
    job_description: LLMJDExtractionOutput


class LLMExtractionEvidenceDiagnostic(StrictLLMExtractionModel):
    """Debug metadata for one LLM extraction evidence reference."""

    source: Literal["resume", "job_description"]
    ref_index: int = Field(ge=1)
    field: str = Field(min_length=1, max_length=64)
    match_mode: Literal["exact", "normalized", "compact", "unsupported", "source_mismatch"]
    matched: bool
    llm_text: str = Field(max_length=MAX_EVIDENCE_TEXT_CHARS)


class LLMExtractionReport(BaseModel):
    """Status block for optional LLM-assisted extraction in match responses."""

    enabled: bool
    status: Literal["disabled", "not_needed", "validated", "rejected", "fallback"]
    provider: str
    model: str
    used_for_resume: bool = False
    used_for_job_description: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_diagnostics: list[LLMExtractionEvidenceDiagnostic] = Field(default_factory=list)
