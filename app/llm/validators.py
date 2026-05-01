"""Deterministic grounding checks for optional LLM output."""

from __future__ import annotations

import re

from app.schemas.llm_generation import LLMRecommendationOutput, LLMValidationReport
from app.services.generation.context import GroundedFlowContext

_PROTECTED_TERMS = {
    "aws certified",
    "certified",
    "certification",
    "docker",
    "director",
    "fortune 500",
    "java",
    "kubernetes",
    "lead",
    "manager",
    "master",
    "mba",
    "phd",
    "react",
    "senior",
    "terraform",
}

_METRIC_PATTERN = re.compile(
    r"(\$+\s*\d|\b\d+\s*%|\b\d+\s*x\b|\b\d+\+?\s+years?\b)",
    re.IGNORECASE,
)


def validate_grounding(
    output: LLMRecommendationOutput,
    context: GroundedFlowContext,
) -> LLMValidationReport:
    """Validate evidence coverage and unsupported-claim risk deterministically."""
    allowed_texts = _allowed_evidence_texts(context)
    allowed_corpus = " ".join(allowed_texts).casefold()
    errors: list[str] = []
    unsupported_claims: list[str] = []
    covered_recommendations = 0

    for index, item in enumerate(output.recommendations, start=1):
        valid_refs = [
            ref for ref in item.evidence_refs if _text_is_allowed(ref.text, allowed_texts)
        ]
        if not valid_refs:
            errors.append(f"recommendation_{index}_missing_supported_evidence")
        else:
            covered_recommendations += 1

        item_claims = _unsupported_claims_for_text(item.recommendation, allowed_corpus)
        if item_claims and not (item.unsupported_claim_risk and output.limitations):
            unsupported_claims.extend(
                f"recommendation_{index}:{claim}" for claim in item_claims
            )

    summary_claims = _unsupported_claims_for_text(output.summary, allowed_corpus)
    unsupported_claims.extend(f"summary:{claim}" for claim in summary_claims)

    recommendation_count = len(output.recommendations)
    evidence_coverage = (
        1.0 if recommendation_count == 0 else covered_recommendations / recommendation_count
    )
    grounding_valid = not errors and not unsupported_claims and evidence_coverage >= 1.0
    return LLMValidationReport(
        schema_valid=True,
        grounding_valid=grounding_valid,
        unsupported_claims=unsupported_claims,
        evidence_coverage=evidence_coverage,
        errors=errors,
    )


def _allowed_evidence_texts(context: GroundedFlowContext) -> list[str]:
    texts = [span.text.strip() for span in context.evidence_registry if span.text.strip()]
    texts.extend(context.match_result.strengths)
    texts.extend(context.match_result.explanations)
    texts.extend(gap.explanation for gap in context.match_result.gaps)
    if context.gating is not None:
        texts.extend(context.gating.reasons)
    return texts


def _text_is_allowed(text: str, allowed_texts: list[str]) -> bool:
    normalized = text.strip().casefold()
    return bool(normalized) and any(
        normalized == allowed.casefold() or normalized in allowed.casefold()
        for allowed in allowed_texts
    )


def _unsupported_claims_for_text(text: str, allowed_corpus: str) -> list[str]:
    lowered = text.casefold()
    claims = sorted(
        term for term in _PROTECTED_TERMS if term in lowered and term not in allowed_corpus
    )
    claims.extend(
        match.group(0)
        for match in _METRIC_PATTERN.finditer(text)
        if match.group(0).casefold() not in allowed_corpus
    )
    return claims
