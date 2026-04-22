"""Unit tests for bounded evidence retrieval."""

from __future__ import annotations

from app.schemas.career import EvidenceRetrievalRequest
from app.services.candidate_profile_service import build_candidate_profile_memory
from app.services.retrieval_service import retrieve_candidate_evidence
from tests.conftest import load_sample


def test_retrieval_service_returns_candidate_evidence_for_grounded_query() -> None:
    profile = build_candidate_profile_memory(load_sample("strong_fit_resume.txt"))

    response = retrieve_candidate_evidence(
        EvidenceRetrievalRequest(
            profile_memory=profile,
            query="python fastapi backend",
            top_k=3,
        )
    )

    assert response.retrieved_items
    assert any(item.evidence_used for item in response.retrieved_items)
    assert response.retrieval_mode == "keyword"
