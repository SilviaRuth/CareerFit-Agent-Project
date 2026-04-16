"""Guardrails and gating logic for grounded generation."""

from __future__ import annotations

from app.schemas.generation import GenerationGate, GenerationWarning
from app.services.generation.workflow import GenerationContext


def build_generation_gate(context: GenerationContext) -> tuple[GenerationGate, list[GenerationWarning]]:
    """Compute structured generation gating from parse confidence and blockers."""
    warnings: list[GenerationWarning] = []
    reasons: list[str] = []

    resume_low = context.resume_parse.parser_confidence.level == "low"
    jd_low = context.jd_parse.parser_confidence.level == "low"
    blockers = context.match_result.blocker_flags
    limited_by_blockers = any(
        (
            blockers.missing_required_skills,
            blockers.seniority_mismatch,
            blockers.unsupported_claims,
        )
    )
    limited_by_missing_evidence = any(gap.gap_type == "missing_evidence" for gap in context.match_result.gaps)

    if resume_low or jd_low:
        reasons.append("low_parser_confidence")
        warnings.append(
            GenerationWarning(
                warning_code="low_parser_confidence",
                message=(
                    "Parser confidence is low for at least one input, so generation is narrowed "
                    "to conservative, evidence-first guidance."
                ),
                severity="warning",
                limited_output=True,
            )
        )

    if blockers.unsupported_claims:
        reasons.append("unsupported_claims_present")
        warnings.append(
            GenerationWarning(
                warning_code="unsupported_claims_guardrail",
                message=(
                    "Unsupported claims were detected in the resume, so generation will not "
                    "upgrade those claims into confident rewrites or talking points."
                ),
                severity="warning",
                limited_output=True,
            )
        )

    if blockers.missing_required_skills:
        reasons.append("required_skills_missing")
        warnings.append(
            GenerationWarning(
                warning_code="required_skills_missing",
                message=(
                    "Required skills are missing from the current evidence set. Guidance will "
                    "focus on truthful gap framing instead of persuasive rewrites."
                ),
                severity="info",
                limited_output=False,
            )
        )

    if blockers.seniority_mismatch:
        reasons.append("seniority_mismatch")
        warnings.append(
            GenerationWarning(
                warning_code="seniority_gap_present",
                message=(
                    "A seniority gap was detected, so the system will avoid rewriting the "
                    "resume to imply a higher level than the evidence supports."
                ),
                severity="warning",
                limited_output=True,
            )
        )

    if resume_low or jd_low:
        generation_mode = "minimal"
    elif limited_by_blockers or limited_by_missing_evidence:
        generation_mode = "limited"
    else:
        generation_mode = "full"

    gate = GenerationGate(
        generation_mode=generation_mode,
        resume_parser_confidence=context.resume_parse.parser_confidence,
        jd_parser_confidence=context.jd_parse.parser_confidence,
        limited_by_low_parser_confidence=resume_low or jd_low,
        limited_by_missing_evidence=limited_by_missing_evidence,
        limited_by_blockers=limited_by_blockers,
        reasons=reasons,
    )
    return gate, warnings
