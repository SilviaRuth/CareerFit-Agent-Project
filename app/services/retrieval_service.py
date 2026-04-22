"""Bounded retrieval helpers for evidence-grounded M5 recommendation flows."""

from __future__ import annotations

import re

from app.schemas.career import (
    EvidenceRetrievalRequest,
    EvidenceRetrievalResponse,
    RetrievedEvidenceItem,
)
from app.services.candidate_profile_service import resolve_candidate_profile

TOKEN_RE = re.compile(r"[a-z0-9]+")


def retrieve_candidate_evidence(request: EvidenceRetrievalRequest) -> EvidenceRetrievalResponse:
    """Retrieve the most relevant candidate evidence for a bounded query."""
    candidate_profile = resolve_candidate_profile(request)
    query_tokens = _tokenize(request.query)
    ranked_items: list[RetrievedEvidenceItem] = []

    for memory_item in candidate_profile.memory_items:
        item_tokens = _tokenize(" ".join([memory_item.label, memory_item.note]))
        overlap = sorted(query_tokens & item_tokens)
        if not overlap:
            continue

        support_bonus = 0.35 if memory_item.support_level == "strong" else 0.15
        score = round(len(overlap) / max(len(query_tokens), 1) + support_bonus, 3)
        ranked_items.append(
            RetrievedEvidenceItem(
                label=memory_item.label,
                source_section=(
                    memory_item.evidence_used[0].section if memory_item.evidence_used else "unknown"
                ),
                score=score,
                reason=(
                    "Matched candidate memory tokens "
                    + ", ".join(overlap)
                    + " against the retrieval query."
                ),
                evidence_used=memory_item.evidence_used,
            )
        )

    ranked_items.sort(key=lambda item: (-item.score, item.label))
    return EvidenceRetrievalResponse(
        query=request.query,
        retrieval_mode="keyword",
        retrieved_items=ranked_items[: request.top_k],
        audit_note=(
            "Keyword retrieval uses only request-scoped candidate memory and does not rely on "
            "an external index."
        ),
    )


def _tokenize(text: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(text.lower()) if len(token) > 1}
