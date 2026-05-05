"""Tests for M8 workflow trace and frontend-readiness invariants."""

from __future__ import annotations

from pathlib import Path

from app.services.matching_service import match_resume_to_jd
from tests.conftest import load_sample


def test_match_trace_is_additive_and_score_shape_stays_stable() -> None:
    result = match_resume_to_jd(
        load_sample("strong_fit_resume.txt"),
        load_sample("strong_fit_jd.txt"),
    )

    assert result.overall_score == 89
    assert result.dimension_scores.skills == 100
    assert result.dimension_scores.experience == 100
    assert result.dimension_scores.projects == 43
    assert result.dimension_scores.domain_fit == 100
    assert result.dimension_scores.education == 100
    assert result.workflow_trace is not None
    assert result.workflow_trace.trace_id
    step_names = [step.step_name for step in result.workflow_trace.steps]
    if "llm_extract_natural_language" in step_names:
        step_names.remove("llm_extract_natural_language")
    assert step_names == [
        "parse_resume",
        "parse_job_description",
        "extract_requirements",
        "score_match",
        "collect_evidence",
        "compute_blockers",
    ]


def test_match_trace_can_be_omitted_for_deterministic_offline_reports() -> None:
    result = match_resume_to_jd(
        load_sample("strong_fit_resume.txt"),
        load_sample("strong_fit_jd.txt"),
        include_trace=False,
    )

    assert result.overall_score == 89
    assert result.workflow_trace is None


def test_blockers_and_unsupported_evidence_remain_visible_with_trace() -> None:
    result = match_resume_to_jd(
        load_sample("poor_fit_resume.txt"),
        load_sample("poor_fit_jd.txt"),
    )

    assert result.blocker_flags.missing_required_skills is True
    assert result.gaps
    assert result.evidence_spans
    assert result.workflow_trace is not None
    blocker_step = result.workflow_trace.steps[-1]
    assert blocker_step.step_name == "compute_blockers"
    assert "missing_required_skills=true" in blocker_step.warnings
    assert result.blocker_flags.model_dump()["missing_required_skills"] is True


def test_route_handlers_do_not_construct_workflow_traces_directly() -> None:
    route_dir = Path("app/api/routes")
    route_sources = "\n".join(path.read_text() for path in route_dir.glob("*.py"))

    assert "WorkflowTrace" not in route_sources
    assert "WorkflowStepTrace" not in route_sources
    assert "attach_match_trace" not in route_sources
    assert "attach_job_comparison_trace" not in route_sources
