"""Single-orchestrator service for grounded generation flows.

This module lives in ``services/`` rather than ``agents/`` because the repo's current
architecture treats orchestration as deterministic backend business logic, not as an
autonomous agent system. The orchestrator coordinates parse -> match -> gate -> render
while keeping routes thin and generation modules narrowly focused.
"""

from __future__ import annotations

from app.schemas.generation import (
    GroundedGenerationRequest,
    InterviewPrepResponse,
    InterviewSimulationResponse,
    LearningPlanResponse,
    RewriteResponse,
)
from app.services.generation.context import GroundedFlowContext
from app.services.generation.generation_guardrails import build_generation_gate
from app.services.generation.grounding import collect_context_evidence
from app.services.generation.interview_prep_service import render_interview_prep_response
from app.services.generation.interview_simulation_service import (
    render_interview_simulation_response,
)
from app.services.generation.learning_plan_service import render_learning_plan_response
from app.services.generation.rewrite_service import render_rewrite_response
from app.services.matching_service import match_schemas
from app.services.parse_service import parse_jd_text, parse_resume_text


def build_grounded_context(request: GroundedGenerationRequest) -> GroundedFlowContext:
    """Build the shared context used by grounded generation flows."""
    resume_parse = parse_resume_text(
        request.resume_text,
        source_name=request.resume_source_name,
    )
    jd_parse = parse_jd_text(
        request.job_description_text,
        source_name=request.jd_source_name,
    )
    match_result = match_schemas(
        resume_parse.parsed_schema,
        jd_parse.parsed_schema,
    )
    preliminary_context = GroundedFlowContext(
        resume_parse=resume_parse,
        jd_parse=jd_parse,
        match_result=match_result,
    )
    gating, generation_warnings = build_generation_gate(preliminary_context)
    evidence_registry = collect_context_evidence(preliminary_context)
    return GroundedFlowContext(
        resume_parse=resume_parse,
        jd_parse=jd_parse,
        match_result=match_result,
        gating=gating,
        generation_warnings=generation_warnings,
        evidence_registry=evidence_registry,
    )


def run_grounded_rewrite_flow(request: GroundedGenerationRequest) -> RewriteResponse:
    """Run the orchestrated grounded rewrite flow."""
    context = build_grounded_context(request)
    return render_rewrite_response(context)


def run_grounded_interview_prep_flow(
    request: GroundedGenerationRequest,
) -> InterviewPrepResponse:
    """Run the orchestrated grounded interview-prep flow."""
    context = build_grounded_context(request)
    return render_interview_prep_response(context)


def run_grounded_interview_simulation_flow(
    request: GroundedGenerationRequest,
) -> InterviewSimulationResponse:
    """Run the orchestrated grounded interview-simulation flow."""
    context = build_grounded_context(request)
    return render_interview_simulation_response(context)


def run_grounded_learning_plan_flow(
    request: GroundedGenerationRequest,
) -> LearningPlanResponse:
    """Run the orchestrated grounded learning-plan flow."""
    context = build_grounded_context(request)
    return render_learning_plan_response(context)
