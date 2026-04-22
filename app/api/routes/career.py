"""Milestone 5 career workflow endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.career import (
    CandidateProfileMemory,
    EvidenceRetrievalRequest,
    EvidenceRetrievalResponse,
    JobComparisonRequest,
    JobComparisonResponse,
    ProfileMemoryRequest,
    SemanticMatchRequest,
    SemanticMatchResponse,
)
from app.services.candidate_profile_service import build_candidate_profile_memory
from app.services.opportunity_comparison_service import compare_candidate_to_jobs
from app.services.retrieval_service import retrieve_candidate_evidence
from app.services.semantic_matching_service import semantic_match_labels

router = APIRouter(tags=["career"])


@router.post("/profile-memory", response_model=CandidateProfileMemory)
def profile_memory(request: ProfileMemoryRequest) -> CandidateProfileMemory:
    """Build request-scoped candidate profile memory from raw resume text."""
    return build_candidate_profile_memory(request.resume_text, source_name=request.source_name)


@router.post("/compare/jobs", response_model=JobComparisonResponse)
def compare_jobs(request: JobComparisonRequest) -> JobComparisonResponse:
    """Rank multiple JDs against one candidate profile."""
    return compare_candidate_to_jobs(request)


@router.post("/retrieve/evidence", response_model=EvidenceRetrievalResponse)
def retrieve_evidence(request: EvidenceRetrievalRequest) -> EvidenceRetrievalResponse:
    """Retrieve bounded candidate evidence for a grounded recommendation query."""
    return retrieve_candidate_evidence(request)


@router.post("/semantic/match", response_model=SemanticMatchResponse)
def semantic_match(request: SemanticMatchRequest) -> SemanticMatchResponse:
    """Return additive semantic hints without changing deterministic scoring."""
    return semantic_match_labels(request)
