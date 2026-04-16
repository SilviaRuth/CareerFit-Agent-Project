"""Unit tests covering Pydantic contract validation for Milestone 1 schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.common import EvidenceSpan, RequirementItem
from app.schemas.jd import JDSchema
from app.schemas.match import (
    BlockerFlags,
    DimensionScores,
    MatchRequest,
    MatchResult,
    RequirementMatch,
)
from app.schemas.resume import ResumeSchema


def test_match_request_requires_both_text_inputs() -> None:
    with pytest.raises(ValidationError):
        MatchRequest.model_validate({"resume_text": "Resume only"})


def test_resume_schema_requires_candidate_name() -> None:
    with pytest.raises(ValidationError):
        ResumeSchema.model_validate(
            {
                "summary": "Backend engineer",
                "skills": [],
                "experience_items": [],
                "project_items": [],
                "education_items": [],
                "evidence_spans": [],
                "normalized_text": "Summary\nBackend engineer",
            }
        )


def test_jd_schema_requires_normalized_text() -> None:
    requirement = RequirementItem(
        requirement_id="required-1-python",
        label="python",
        normalized_label="python",
        priority="required",
        requirement_type="skill",
        raw_text="Strong Python experience",
        evidence_span=_sample_span("job_description", "required", "Strong Python experience"),
    )

    with pytest.raises(ValidationError):
        JDSchema.model_validate(
            {
                "job_title": "Backend Engineer",
                "company": "HealthStack",
                "required_requirements": [requirement.model_dump()],
                "preferred_requirements": [],
                "responsibilities": [],
                "education_requirements": [],
                "seniority_hint": "mid",
                "domain_hint": "healthcare",
                "evidence_spans": [],
            }
        )


def test_match_result_requires_nested_contract_shapes() -> None:
    with pytest.raises(ValidationError):
        MatchResult.model_validate(
            {
                "overall_score": 88,
                "dimension_scores": {"skills": "high"},
                "required_matches": [],
                "preferred_matches": [],
                "gaps": [],
                "blocker_flags": {},
                "strengths": [],
                "explanations": [],
                "evidence_spans": [],
            }
        )


def test_match_result_accepts_valid_nested_models() -> None:
    span = _sample_span("resume", "experience", "Built FastAPI services.")
    match = RequirementMatch(
        requirement_id="required-1-fastapi",
        requirement_label="fastapi",
        normalized_label="fastapi",
        requirement_priority="required",
        requirement_type="skill",
        status="matched",
        explanation="Resume provides direct evidence for fastapi.",
        resume_evidence=[span],
        jd_evidence=[_sample_span("job_description", "required", "FastAPI experience")],
    )

    result = MatchResult(
        overall_score=92,
        dimension_scores=DimensionScores(
            skills=100,
            experience=90,
            projects=80,
            domain_fit=100,
            education=90,
        ),
        required_matches=[match],
        preferred_matches=[],
        gaps=[],
        blocker_flags=BlockerFlags(),
        strengths=["Matched required fastapi with resume evidence."],
        explanations=["Overall score is 92 based on weighted rule-based matching."],
        evidence_spans=[span],
    )

    assert result.required_matches[0].normalized_label == "fastapi"
    assert result.blocker_flags.missing_required_skills is False


def _sample_span(source_document: str, section: str, text: str) -> EvidenceSpan:
    return EvidenceSpan(
        source_document=source_document,
        section=section,
        text=text,
        start_char=0,
        end_char=len(text),
        normalized_value=None,
        explanation="Test evidence span.",
    )
