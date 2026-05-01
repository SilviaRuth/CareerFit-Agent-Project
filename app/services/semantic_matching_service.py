"""Explicit semantic-alignment hints that stay additive to deterministic scoring."""

from __future__ import annotations

from app.core.config import CAPABILITY_PATTERNS
from app.schemas.career import SemanticMatchRequest, SemanticMatchResponse, SemanticMatchSignal
from app.services.candidate_profile_service import resolve_candidate_profile
from app.services.tokenization import tokenize_keywords
from app.services.workflow_trace_service import attach_semantic_trace


def semantic_match_labels(request: SemanticMatchRequest) -> SemanticMatchResponse:
    """Return additive semantic hints without rewriting the core score contract."""
    if request.mode == "off":
        return attach_semantic_trace(
            SemanticMatchResponse(
                mode="off",
                signals=[],
                note="Semantic hints are disabled for this request.",
            )
        )

    candidate_profile = resolve_candidate_profile(request)
    candidate_items = {item.label: item for item in candidate_profile.memory_items}
    candidate_canonical = {
        _canonicalize(label): label for label in candidate_items if _canonicalize(label)
    }
    signals: list[SemanticMatchSignal] = []

    for query_label in request.labels:
        canonical_query = _canonicalize(query_label)
        if canonical_query and canonical_query in candidate_canonical:
            matched_label = candidate_canonical[canonical_query]
            memory_item = candidate_items[matched_label]
            signals.append(
                SemanticMatchSignal(
                    query_label=query_label,
                    matched_label=matched_label,
                    confidence="high",
                    reason=(
                        "The query and candidate evidence collapse to the same canonical "
                        "capability alias."
                    ),
                    evidence_used=memory_item.evidence_used,
                )
            )
            continue

        query_tokens = tokenize_keywords(query_label)
        best_label = ""
        best_overlap: set[str] = set()
        for label in candidate_items:
            overlap = query_tokens & tokenize_keywords(label)
            if len(overlap) > len(best_overlap):
                best_overlap = overlap
                best_label = label

        if best_label and best_overlap:
            memory_item = candidate_items[best_label]
            signals.append(
                SemanticMatchSignal(
                    query_label=query_label,
                    matched_label=best_label,
                    confidence="medium" if len(best_overlap) > 1 else "low",
                    reason=(
                        "The query shares meaningful tokens with existing candidate evidence: "
                        + ", ".join(sorted(best_overlap))
                        + "."
                    ),
                    evidence_used=memory_item.evidence_used,
                )
            )

    signals = sorted(
        signals,
        key=lambda item: (_confidence_rank(item.confidence), item.query_label),
    )
    return attach_semantic_trace(
        SemanticMatchResponse(
            mode="heuristic",
            signals=signals[: request.top_k],
            note=(
                "Semantic hints are heuristic and additive only; they do not alter deterministic "
                "match scores or blocker flags."
            ),
        ),
    )


def _canonicalize(label: str) -> str | None:
    lowered = label.lower().strip()
    for canonical, patterns in CAPABILITY_PATTERNS.items():
        if lowered == canonical:
            return canonical
        if any(pattern in lowered or lowered in pattern for pattern in patterns):
            return canonical
    return None

def _confidence_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(value, 3)
