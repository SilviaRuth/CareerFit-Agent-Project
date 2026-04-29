"""Cross-JD opportunity comparison for one shared candidate profile."""

from __future__ import annotations

from app.schemas.career import (
    EvidenceRetrievalRequest,
    JobComparisonRequest,
    JobComparisonResponse,
    JobComparisonResult,
    SemanticMatchRequest,
)
from app.schemas.match import MatchResult
from app.services.candidate_profile_service import resolve_candidate_profile
from app.services.fit_label import derive_fit_label
from app.services.generation.context import GroundedFlowContext
from app.services.generation.generation_guardrails import build_generation_gate
from app.services.generation.grounding import collect_context_evidence
from app.services.generation.learning_plan_service import render_learning_plan_response
from app.services.matching_service import match_schemas
from app.services.parse_service import parse_jd_text
from app.services.retrieval_service import retrieve_candidate_evidence
from app.services.semantic_matching_service import semantic_match_labels


def compare_candidate_to_jobs(request: JobComparisonRequest) -> JobComparisonResponse:
    """Rank multiple JDs against one candidate profile without changing core score meaning."""
    candidate_profile = resolve_candidate_profile(request)
    provisional_results: list[tuple[JobComparisonResult, int, float]] = []

    for job_input in request.job_descriptions:
        jd_parse = parse_jd_text(
            job_input.job_description_text,
            source_name=job_input.source_name,
        )
        match_result = match_schemas(candidate_profile.parsed_resume, jd_parse.parsed_schema)
        learning_plan = _build_learning_plan(candidate_profile, jd_parse, match_result)
        retrieval_query = _build_retrieval_query(match_result)
        retrieval_response = retrieve_candidate_evidence(
            EvidenceRetrievalRequest(
                profile_memory=candidate_profile,
                query=retrieval_query,
                top_k=3,
            )
        )
        semantic_response = semantic_match_labels(
            SemanticMatchRequest(
                profile_memory=candidate_profile,
                labels=_top_requirement_labels(match_result),
                mode=request.semantic_mode,
                top_k=3,
            )
        )
        result = JobComparisonResult(
            rank=0,
            jd_id=job_input.jd_id,
            job_title=jd_parse.parsed_schema.job_title or "Unknown role",
            company=jd_parse.parsed_schema.company or "Unknown company",
            overall_score=match_result.overall_score,
            fit_label=derive_fit_label(match_result),
            blocker_flags=match_result.blocker_flags,
            parser_confidence=jd_parse.parser_confidence,
            strengths=match_result.strengths[:3],
            top_gaps=match_result.gaps[:3],
            adaptation_summary=match_result.adaptation_summary,
            evidence_summary=match_result.evidence_summary,
            retrieved_evidence=retrieval_response.retrieved_items,
            semantic_support=semantic_response.signals,
            recommended_next_steps=[step.action for step in learning_plan.plan_steps[:2]],
        )
        retrieval_score = sum(item.score for item in retrieval_response.retrieved_items)
        provisional_results.append((result, len(semantic_response.signals), retrieval_score))

    ranking = sorted(
        provisional_results,
        key=lambda item: (
            item[0].blocker_flags.missing_required_skills,
            item[0].blocker_flags.seniority_mismatch,
            item[0].parser_confidence.level == "low",
            -item[0].overall_score,
            item[0].blocker_flags.unsupported_claims,
            -item[1],
            -item[2],
        ),
    )

    best_score = ranking[0][0].overall_score if ranking else 0
    finalized: list[JobComparisonResult] = []
    for index, (result, _, _) in enumerate(ranking, start=1):
        finalized.append(
            result.model_copy(
                update={
                    "rank": index,
                    "score_delta_from_best": best_score - result.overall_score,
                }
            )
        )

    top_role = finalized[0].job_title if finalized else "no compared role"
    summary = (
        f"Compared {len(finalized)} job descriptions for {candidate_profile.candidate_name}. "
        f"The top-ranked opportunity is {top_role}."
    )
    return JobComparisonResponse(
        summary=summary,
        compared_count=len(finalized),
        candidate_profile=candidate_profile,
        ranking=finalized,
    )


def _build_learning_plan(candidate_profile, jd_parse, match_result: MatchResult):
    context = GroundedFlowContext(
        resume_parse=_resume_parse_from_profile(candidate_profile),
        jd_parse=jd_parse,
        match_result=match_result,
    )
    gating, generation_warnings = build_generation_gate(context)
    context.gating = gating
    context.generation_warnings = generation_warnings
    context.evidence_registry = collect_context_evidence(context)
    return render_learning_plan_response(context)


def _resume_parse_from_profile(candidate_profile):
    from app.schemas.parse import ResumeParseResponse

    return ResumeParseResponse(
        source_type="text",
        source_name=None,
        media_type="text/plain",
        raw_text=candidate_profile.parsed_resume.normalized_text,
        cleaned_text=candidate_profile.parsed_resume.normalized_text,
        warnings=[],
        parser_confidence=candidate_profile.parser_confidence,
        unsupported_segments=[],
        schema=candidate_profile.parsed_resume,
    )


def _build_retrieval_query(match_result: MatchResult) -> str:
    labels = _top_requirement_labels(match_result)
    return " ".join(labels) if labels else "resume evidence"


def _top_requirement_labels(match_result: MatchResult) -> list[str]:
    labels = [
        match.requirement_label
        for match in match_result.required_matches
        if match.status == "matched"
    ][:2]
    labels.extend(gap.requirement_label for gap in match_result.gaps[:2])
    return labels[:4]
