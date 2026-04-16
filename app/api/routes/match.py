"""Matching endpoint for the deterministic backend MVP."""

from fastapi import APIRouter

from app.schemas.match import MatchRequest, MatchResult
from app.services.matching_service import match_resume_to_jd

router = APIRouter(tags=["matching"])


@router.post("/match", response_model=MatchResult)
def match_resume_to_job(request: MatchRequest) -> MatchResult:
    """Match a resume and job description using the deterministic Milestone 1 pipeline."""
    return match_resume_to_jd(
        resume_text=request.resume_text,
        job_description_text=request.job_description_text,
    )
