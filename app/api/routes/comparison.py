"""Multi-resume comparison endpoints for M4 ranking workflows."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.comparison import MultiResumeComparisonRequest, MultiResumeComparisonResponse
from app.services.comparison_service import compare_resumes_to_jd

router = APIRouter(tags=["comparison"])


@router.post("/compare/resumes", response_model=MultiResumeComparisonResponse)
def compare_resumes(request: MultiResumeComparisonRequest) -> MultiResumeComparisonResponse:
    """Rank multiple resumes against one JD using the deterministic matcher."""
    return compare_resumes_to_jd(request)
