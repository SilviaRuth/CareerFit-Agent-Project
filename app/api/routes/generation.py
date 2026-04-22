"""Grounded generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.generation import (
    GroundedGenerationRequest,
    InterviewPrepResponse,
    InterviewSimulationResponse,
    LearningPlanResponse,
    RewriteResponse,
)
from app.services.orchestration_service import (
    run_grounded_interview_prep_flow,
    run_grounded_interview_simulation_flow,
    run_grounded_learning_plan_flow,
    run_grounded_rewrite_flow,
)

router = APIRouter(tags=["generation"])


@router.post("/rewrite", response_model=RewriteResponse)
def rewrite_resume(request: GroundedGenerationRequest) -> RewriteResponse:
    """Run the single-orchestrator rewrite flow."""
    return run_grounded_rewrite_flow(request)


@router.post("/interview-prep", response_model=InterviewPrepResponse)
def interview_prep(request: GroundedGenerationRequest) -> InterviewPrepResponse:
    """Run the single-orchestrator interview-prep flow."""
    return run_grounded_interview_prep_flow(request)


@router.post("/interview-sim", response_model=InterviewSimulationResponse)
def interview_sim(request: GroundedGenerationRequest) -> InterviewSimulationResponse:
    """Run the single-orchestrator interview-simulation flow."""
    return run_grounded_interview_simulation_flow(request)


@router.post("/learning-plan", response_model=LearningPlanResponse)
def learning_plan(request: GroundedGenerationRequest) -> LearningPlanResponse:
    """Run the single-orchestrator learning-plan flow."""
    return run_grounded_learning_plan_flow(request)
