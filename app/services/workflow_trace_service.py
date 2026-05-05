"""Additive workflow trace builders for frontend-ready responses."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from app.schemas.career import (
    EvidenceRetrievalResponse,
    JobComparisonResponse,
    SemanticMatchResponse,
)
from app.schemas.comparison import MultiResumeComparisonResponse
from app.schemas.match import BlockerFlags, MatchResult
from app.schemas.parse import ParserConfidence, ParserDiagnostic, UnsupportedSegment
from app.schemas.workflow import WorkflowStatus, WorkflowStepTrace, WorkflowTrace


def new_trace_id() -> str:
    """Return a stable per-request trace identifier."""
    return str(uuid4())


def attach_match_trace(result: MatchResult, trace_id: str | None = None) -> MatchResult:
    """Attach a deterministic match trace without changing score output."""
    llm_extraction_step = []
    if result.llm_extraction is not None:
        status = (
            WorkflowStatus.COMPLETED
            if result.llm_extraction.status == "validated"
            else WorkflowStatus.SKIPPED
            if result.llm_extraction.status in {"disabled", "not_needed"}
            else WorkflowStatus.PARTIAL
        )
        llm_extraction_step.append(
            _step(
                "llm_extract_natural_language",
                status=status,
                service_name="llm_extraction_service",
                warnings=result.llm_extraction.warnings,
                metadata=result.llm_extraction.model_dump(mode="json"),
            )
        )

    trace = WorkflowTrace(
        trace_id=trace_id or new_trace_id(),
        workflow_name="match",
        status=WorkflowStatus.COMPLETED,
        steps=[
            _step(
                "parse_resume",
                service_name="extraction_service",
                metadata={"input": "resume_text"},
            ),
            _step(
                "parse_job_description",
                service_name="extraction_service",
                metadata={"input": "job_description_text"},
            ),
            *llm_extraction_step,
            _step(
                "extract_requirements",
                service_name="extraction_service",
                metadata={
                    "required_count": len(result.required_matches),
                    "preferred_count": len(result.preferred_matches),
                },
            ),
            _step(
                "score_match",
                service_name="matching_service",
                metadata={
                    "overall_score": result.overall_score,
                    "dimension_scores": result.dimension_scores.model_dump(mode="json"),
                },
            ),
            _step(
                "collect_evidence",
                status=_status_for_count(result.evidence_summary.total_evidence_spans),
                service_name="matching_service",
                metadata=result.evidence_summary.model_dump(mode="json"),
            ),
            _step(
                "compute_blockers",
                service_name="matching_service",
                warnings=_blocker_warnings(result.blocker_flags),
                metadata={"blocker_flags": result.blocker_flags.model_dump(mode="json")},
            ),
        ],
        warnings=_blocker_warnings(result.blocker_flags),
    )
    return result.model_copy(update={"workflow_trace": trace})


def attach_multi_resume_comparison_trace(
    response: MultiResumeComparisonResponse,
    *,
    jd_warnings: Iterable[ParserDiagnostic] = (),
    jd_confidence: ParserConfidence | None = None,
    resume_diagnostics: Iterable[tuple[str, list[ParserDiagnostic], ParserConfidence]] = (),
    trace_id: str | None = None,
) -> MultiResumeComparisonResponse:
    """Attach trace metadata to the multi-resume ranking response."""
    resume_warning_messages = [
        _diagnostic_message(resume_id, warning)
        for resume_id, warnings, _ in resume_diagnostics
        for warning in warnings
    ]
    low_confidence_resumes = [
        resume_id
        for resume_id, _, confidence in resume_diagnostics
        if confidence.level == "low"
    ]
    trace_warnings = [
        *_diagnostic_messages("job_description", jd_warnings),
        *resume_warning_messages,
    ]
    if jd_confidence is not None and jd_confidence.level == "low":
        trace_warnings.append("job_description parser confidence is low")
    trace_warnings.extend(
        f"{resume_id} parser confidence is low" for resume_id in low_confidence_resumes
    )

    trace = WorkflowTrace(
        trace_id=trace_id or new_trace_id(),
        workflow_name="compare_resumes",
        status=WorkflowStatus.COMPLETED,
        steps=[
            _step(
                "parse_job_description",
                service_name="parse_service",
                warnings=_diagnostic_messages("job_description", jd_warnings),
                metadata={
                    "parser_confidence": (
                        jd_confidence.model_dump(mode="json") if jd_confidence else None
                    ),
                },
            ),
            _step(
                "parse_resume",
                service_name="parse_service",
                status=_status_for_count(response.compared_count),
                warnings=resume_warning_messages,
                metadata={
                    "resume_count": response.compared_count,
                    "low_confidence_resume_ids": low_confidence_resumes,
                },
            ),
            _step(
                "score_match",
                service_name="matching_service",
                metadata={"scored_count": response.compared_count},
            ),
            _step(
                "compute_blockers",
                service_name="matching_service",
                warnings=[
                    f"{entry.resume_id}: {warning}"
                    for entry in response.ranking
                    for warning in _blocker_warnings(entry.blocker_flags)
                ],
                metadata={
                    "blocked_resume_ids": [
                        entry.resume_id
                        for entry in response.ranking
                        if any(entry.blocker_flags.model_dump(mode="json").values())
                    ],
                },
            ),
            _step(
                "rank_resumes",
                service_name="comparison_service",
                metadata={"ranking_ids": [entry.resume_id for entry in response.ranking]},
            ),
        ],
        warnings=trace_warnings,
    )
    return response.model_copy(update={"workflow_trace": trace})


def attach_retrieval_trace(
    response: EvidenceRetrievalResponse,
    trace_id: str | None = None,
) -> EvidenceRetrievalResponse:
    """Attach a trace to the bounded evidence retrieval response."""
    trace = WorkflowTrace(
        trace_id=trace_id or new_trace_id(),
        workflow_name="retrieve_evidence",
        status=WorkflowStatus.COMPLETED,
        steps=[
            _step(
                "resolve_candidate_profile",
                service_name="candidate_profile_service",
            ),
            _step(
                "collect_evidence",
                service_name="retrieval_service",
                status=_status_for_count(len(response.retrieved_items)),
                metadata={
                    "query": response.query,
                    "retrieval_mode": response.retrieval_mode,
                    "retrieved_count": len(response.retrieved_items),
                },
            ),
        ],
    )
    return response.model_copy(update={"workflow_trace": trace})


def attach_semantic_trace(
    response: SemanticMatchResponse,
    trace_id: str | None = None,
) -> SemanticMatchResponse:
    """Attach a trace to additive semantic matching hints."""
    trace = WorkflowTrace(
        trace_id=trace_id or new_trace_id(),
        workflow_name="semantic_match",
        status=WorkflowStatus.COMPLETED,
        steps=[
            _step(
                "resolve_candidate_profile",
                service_name="candidate_profile_service",
                status=(
                    WorkflowStatus.SKIPPED
                    if response.mode == "off"
                    else WorkflowStatus.COMPLETED
                ),
            ),
            _step(
                "semantic_match",
                service_name="semantic_matching_service",
                status=(
                    WorkflowStatus.SKIPPED
                    if response.mode == "off"
                    else _status_for_count(len(response.signals))
                ),
                metadata={
                    "mode": response.mode,
                    "signal_count": len(response.signals),
                },
            ),
        ],
    )
    return response.model_copy(update={"workflow_trace": trace})


def attach_job_comparison_trace(
    response: JobComparisonResponse,
    *,
    jd_diagnostics: Iterable[tuple[str, list[ParserDiagnostic], ParserConfidence]] = (),
    trace_id: str | None = None,
) -> JobComparisonResponse:
    """Attach trace metadata to the cross-JD opportunity ranking response."""
    jd_warning_messages = [
        _diagnostic_message(jd_id, warning)
        for jd_id, warnings, _ in jd_diagnostics
        for warning in warnings
    ]
    low_confidence_jds = [
        jd_id for jd_id, _, confidence in jd_diagnostics if confidence.level == "low"
    ]
    trace_warnings = [
        *jd_warning_messages,
        *(f"{jd_id} parser confidence is low" for jd_id in low_confidence_jds),
    ]
    blocker_step_warnings = [
        f"{entry.jd_id}: {warning}"
        for entry in response.ranking
        for warning in _blocker_warnings(entry.blocker_flags)
    ]

    trace = WorkflowTrace(
        trace_id=trace_id or new_trace_id(),
        workflow_name="compare_jobs",
        status=WorkflowStatus.COMPLETED,
        steps=[
            _step(
                "parse_resume",
                service_name="candidate_profile_service",
                metadata={
                    "candidate_profile_id": response.candidate_profile.profile_id,
                    "parser_confidence": response.candidate_profile.parser_confidence.model_dump(
                        mode="json"
                    ),
                },
            ),
            _step(
                "parse_job_description",
                service_name="parse_service",
                status=_status_for_count(response.compared_count),
                warnings=jd_warning_messages,
                metadata={
                    "jd_count": response.compared_count,
                    "low_confidence_jd_ids": low_confidence_jds,
                },
            ),
            _step(
                "score_match",
                service_name="matching_service",
                metadata={"scored_count": response.compared_count},
            ),
            _step(
                "collect_evidence",
                service_name="retrieval_service",
                status=_status_for_count(
                    sum(len(entry.retrieved_evidence) for entry in response.ranking)
                ),
                metadata={
                    "retrieved_count": sum(
                        len(entry.retrieved_evidence) for entry in response.ranking
                    ),
                    "semantic_signal_count": sum(
                        len(entry.semantic_support) for entry in response.ranking
                    ),
                },
            ),
            _step(
                "compute_blockers",
                service_name="matching_service",
                warnings=blocker_step_warnings,
                metadata={
                    "blocked_jd_ids": [
                        entry.jd_id
                        for entry in response.ranking
                        if any(entry.blocker_flags.model_dump(mode="json").values())
                    ],
                },
            ),
            _step(
                "build_recommendations",
                service_name="learning_plan_service",
                status=_status_for_count(
                    sum(len(entry.recommended_next_steps) for entry in response.ranking)
                ),
                metadata={
                    "recommendation_count": sum(
                        len(entry.recommended_next_steps) for entry in response.ranking
                    ),
                },
            ),
            _step(
                "rank_jobs",
                service_name="opportunity_comparison_service",
                metadata={"ranking_ids": [entry.jd_id for entry in response.ranking]},
            ),
        ],
        warnings=trace_warnings + blocker_step_warnings,
    )
    return response.model_copy(update={"workflow_trace": trace})


def _step(
    step_name: str,
    *,
    service_name: str,
    status: WorkflowStatus = WorkflowStatus.COMPLETED,
    warnings: list[str] | None = None,
    metadata: dict | None = None,
) -> WorkflowStepTrace:
    return WorkflowStepTrace(
        step_name=step_name,
        status=status,
        service_name=service_name,
        warnings=warnings or [],
        metadata={key: value for key, value in (metadata or {}).items() if value is not None},
    )


def _status_for_count(count: int) -> WorkflowStatus:
    return WorkflowStatus.COMPLETED if count > 0 else WorkflowStatus.PARTIAL


def _blocker_warnings(blocker_flags: BlockerFlags) -> list[str]:
    flags = blocker_flags.model_dump(mode="json")
    return [f"{name}=true" for name, enabled in flags.items() if enabled]


def _diagnostic_messages(
    prefix: str,
    warnings: Iterable[ParserDiagnostic],
) -> list[str]:
    return [_diagnostic_message(prefix, warning) for warning in warnings]


def _diagnostic_message(prefix: str, warning: ParserDiagnostic | UnsupportedSegment) -> str:
    if isinstance(warning, ParserDiagnostic):
        section = f":{warning.section}" if warning.section else ""
        return f"{prefix}{section}:{warning.warning_code}:{warning.severity}"
    section = f":{warning.section}" if warning.section else ""
    return f"{prefix}{section}:{warning.reason}"
