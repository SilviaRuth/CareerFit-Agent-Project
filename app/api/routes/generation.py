"""Grounded generation endpoints for Milestone 2B."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.generation import (
    GroundedGenerationRequest,
    InterviewPrepResponse,
    RewriteResponse,
)
from app.services.generation.interview_prep_service import generate_interview_prep_from_text
from app.services.generation.rewrite_service import generate_rewrite_response_from_text

router = APIRouter(tags=["generation"])


@router.post("/rewrite", response_model=RewriteResponse)
def rewrite_resume(request: GroundedGenerationRequest) -> RewriteResponse:
    """Generate bounded resume rewrite guidance grounded in parse and match outputs."""
    return generate_rewrite_response_from_text(
        resume_text=request.resume_text,
        job_description_text=request.job_description_text,
        resume_source_name=request.resume_source_name,
        jd_source_name=request.jd_source_name,
    )


@router.post("/interview-prep", response_model=InterviewPrepResponse)
def interview_prep(request: GroundedGenerationRequest) -> InterviewPrepResponse:
    """Generate grounded interview preparation guidance from parse and match outputs."""
    return generate_interview_prep_from_text(
        resume_text=request.resume_text,
        job_description_text=request.job_description_text,
        resume_source_name=request.resume_source_name,
        jd_source_name=request.jd_source_name,
    )
