"""Unit tests covering Pydantic contract validation for Milestone 1 schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.common import EvidenceSpan, RequirementItem
from app.schemas.generation import (
    GenerationGate,
    InterviewPrepResponse,
    RewriteAction,
    RewriteResponse,
)
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


def test_rewrite_response_requires_nested_generation_shapes() -> None:
    with pytest.raises(ValidationError):
        RewriteResponse.model_validate(
            {
                "summary": "Rewrite guidance",
                "prioritized_actions": [{"priority": "high"}],
                "rewritten_bullets": [],
                "evidence_used": [],
                "unsupported_requests": [],
                "cautions": [],
                "generation_warnings": [],
                "gating": {
                    "generation_mode": "full",
                    "resume_parser_confidence": {},
                    "jd_parser_confidence": {},
                },
            }
        )


def test_interview_prep_response_accepts_valid_grounded_models() -> None:
    span = _sample_span("resume", "experience", "Built FastAPI services.")
    gate = GenerationGate(
        generation_mode="limited",
        resume_parser_confidence={
            "score": 0.82,
            "level": "medium",
            "extraction_complete": True,
            "factors": [],
        },
        jd_parser_confidence={
            "score": 0.93,
            "level": "high",
            "extraction_complete": True,
            "factors": [],
        },
        limited_by_low_parser_confidence=False,
        limited_by_missing_evidence=True,
        limited_by_blockers=False,
        reasons=["missing_evidence"],
    )

    rewrite_action = RewriteAction(
        priority=1,
        category="weak_evidence",
        target_requirement_id="required-1-fastapi",
        target_requirement_label="fastapi",
        explanation="Resume mentions FastAPI weakly.",
        recommendation="Clarify the existing FastAPI material.",
        evidence_used=[span],
        caution="Do not overstate framework ownership.",
    )
    rewrite_response = RewriteResponse(
        summary="Clarify weak FastAPI evidence.",
        prioritized_actions=[rewrite_action],
        rewritten_summary=None,
        rewritten_bullets=[],
        evidence_used=[span],
        unsupported_requests=[],
        cautions=[],
        generation_warnings=[],
        gating=gate,
    )

    interview_response = InterviewPrepResponse.model_validate(
        {
            "summary": "Expect FastAPI depth questions.",
            "likely_focus_areas": [
                {
                    "priority": 1,
                    "focus_area": "fastapi",
                    "reason": "The JD requires it.",
                    "related_requirement_id": "required-1-fastapi",
                    "evidence_used": [span.model_dump()],
                    "caution": None,
                }
            ],
            "interview_questions": [
                {
                    "priority": 1,
                    "question": "Can you walk through your FastAPI work?",
                    "rationale": "Grounded in the JD and resume evidence.",
                    "related_requirement_id": "required-1-fastapi",
                    "support_level": "strong",
                    "evidence_used": [span.model_dump()],
                    "honest_framing": None,
                }
            ],
            "recommended_talking_points": [
                {
                    "topic": "fastapi",
                    "talking_point": "Use the verified FastAPI example.",
                    "support_level": "strong",
                    "evidence_used": [span.model_dump()],
                    "caution": "Do not add unsupported impact metrics.",
                }
            ],
            "weak_area_preparation": [],
            "evidence_used": [span.model_dump()],
            "generation_warnings": [],
            "gating": gate.model_dump(),
        }
    )

    assert rewrite_response.prioritized_actions[0].target_requirement_label == "fastapi"
    assert interview_response.interview_questions[0].support_level == "strong"


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
