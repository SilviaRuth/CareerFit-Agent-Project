"""Comparison service for ranking multiple resumes against a shared JD."""

from __future__ import annotations

from app.schemas.comparison import (
    MultiResumeComparisonRequest,
    MultiResumeComparisonResponse,
    ResumeComparisonResult,
)
from app.services.fit_label import derive_fit_label
from app.services.matching_service import match_schemas
from app.services.parse_service import parse_jd_text, parse_resume_text


def compare_resumes_to_jd(
    request: MultiResumeComparisonRequest,
) -> MultiResumeComparisonResponse:
    """Parse one JD, score multiple resumes against it, and return a ranking."""
    jd_parse = parse_jd_text(
        request.job_description_text,
        source_name=request.jd_source_name,
    )

    provisional_results: list[ResumeComparisonResult] = []
    for resume_input in request.resumes:
        resume_parse = parse_resume_text(
            resume_input.resume_text,
            source_name=resume_input.source_name,
        )
        match_result = match_schemas(
            resume_parse.parsed_schema,
            jd_parse.parsed_schema,
        )
        provisional_results.append(
            ResumeComparisonResult(
                rank=0,
                resume_id=resume_input.resume_id,
                overall_score=match_result.overall_score,
                fit_label=derive_fit_label(match_result),
                blocker_flags=match_result.blocker_flags,
                dimension_scores=match_result.dimension_scores,
                parser_confidence=resume_parse.parser_confidence,
                strengths=match_result.strengths[:3],
                top_gaps=match_result.gaps[:3],
                evidence_summary=match_result.evidence_summary,
                adaptation_summary=match_result.adaptation_summary,
            )
        )

    ranking = sorted(
        provisional_results,
        key=lambda item: (
            item.blocker_flags.missing_required_skills,
            item.blocker_flags.seniority_mismatch,
            item.parser_confidence.level == "low",
            -item.overall_score,
            item.blocker_flags.unsupported_claims,
            -item.parser_confidence.score,
        ),
    )

    best_score = ranking[0].overall_score if ranking else 0
    finalized_ranking: list[ResumeComparisonResult] = []
    for index, item in enumerate(ranking, start=1):
        finalized_ranking.append(
            item.model_copy(
                update={
                    "rank": index,
                    "score_delta_from_best": best_score - item.overall_score,
                }
            )
        )

    job_title = jd_parse.parsed_schema.job_title or "Unknown role"
    company = jd_parse.parsed_schema.company or "Unknown company"
    summary = (
        f"Compared {len(finalized_ranking)} resumes against {job_title} at {company}. "
        f"Top-ranked resume scored {best_score}."
    )
    return MultiResumeComparisonResponse(
        summary=summary,
        compared_count=len(finalized_ranking),
        job_title=job_title,
        company=company,
        jd_parser_confidence=jd_parse.parser_confidence,
        ranking=finalized_ranking,
    )
