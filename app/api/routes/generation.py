"""Grounded generation endpoints for Milestone 2B."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.generation import (
    GroundedGenerationRequest,
    InterviewPrepResponse,
    RewriteResponse,
)
from app.services.orchestration_service import (
    run_grounded_interview_prep_flow,
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
