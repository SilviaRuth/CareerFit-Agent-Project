"""Deterministic role/company adaptation helpers for reviewable M4 output shaping."""

from __future__ import annotations

import re

from app.schemas.jd import JDSchema
from app.schemas.match import AdaptationSummary, GapItem, RequirementMatch

ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "backend_platform": (
        "backend",
        "platform",
        "python",
        "fastapi",
        "api",
        "microservice",
        "cloud",
        "aws",
    ),
    "clinical_care": (
        "nurse",
        "patient",
        "clinical",
        "care",
        "healthcare",
        "medical",
    ),
    "finance_accounting": (
        "accounting",
        "accountant",
        "finance",
        "financial",
        "gaap",
        "ledger",
    ),
    "it_support": (
        "support",
        "help desk",
        "ticket",
        "troubleshoot",
        "administrator",
        "desktop",
    ),
}

COMPANY_SIGNAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "healthcare_safety": ("health", "care", "clinic", "patient", "medical"),
    "platform_reliability": ("cloud", "ops", "platform", "service", "internal"),
    "financial_control": ("finance", "accounting", "audit", "ledger", "bank"),
    "service_delivery": ("support", "customer", "client", "help"),
}


def build_adaptation_summary(
    *,
    jd_schema: JDSchema,
    required_matches: list[RequirementMatch],
    preferred_matches: list[RequirementMatch],
    gaps: list[GapItem],
) -> AdaptationSummary:
    """Build a deterministic summary of what the JD emphasizes."""
    context = _build_context(jd_schema)
    role_focus = _derive_role_focus(context, jd_schema)
    company_signals = _derive_company_signals(context)

    requirement_scores: dict[str, int] = {}
    for match in required_matches + preferred_matches:
        requirement_scores[match.requirement_label] = _score_requirement_emphasis(
            label=match.requirement_label,
            priority=match.requirement_priority,
            context=context,
            role_focus=role_focus,
        )
    for gap in gaps:
        requirement_scores[gap.requirement_label] = _score_requirement_emphasis(
            label=gap.requirement_label,
            priority=gap.requirement_priority,
            context=context,
            role_focus=role_focus,
        )

    emphasized_requirements = _take_top_labels(requirement_scores, limit=3)
    prioritized_strengths = _take_top_labels(
        {
            match.requirement_label: requirement_scores.get(match.requirement_label, 0)
            for match in required_matches + preferred_matches
            if match.status == "matched"
        },
        limit=3,
    )
    prioritized_gaps = _take_top_labels(
        {gap.requirement_label: requirement_scores.get(gap.requirement_label, 0) for gap in gaps},
        limit=3,
    )

    explanation_parts = []
    if role_focus:
        explanation_parts.append(f"Role focus: {role_focus.replace('_', ' ')}")
    if company_signals:
        explanation_parts.append(
            "company signals: " + ", ".join(signal.replace("_", " ") for signal in company_signals)
        )
    if emphasized_requirements:
        explanation_parts.append("emphasized requirements: " + ", ".join(emphasized_requirements))

    return AdaptationSummary(
        role_focus=role_focus,
        company_signals=company_signals,
        emphasized_requirements=emphasized_requirements,
        prioritized_strengths=prioritized_strengths,
        prioritized_gaps=prioritized_gaps,
        explanation="; ".join(explanation_parts) + "." if explanation_parts else "",
    )


def sort_gaps_for_adaptation(
    gaps: list[GapItem],
    adaptation_summary: AdaptationSummary,
) -> list[GapItem]:
    """Bring the most role-relevant gaps to the front without changing their content."""
    priority_order = {
        label: index for index, label in enumerate(adaptation_summary.prioritized_gaps)
    }
    return sorted(
        gaps,
        key=lambda gap: (
            0 if gap.requirement_label in priority_order else 1,
            priority_order.get(gap.requirement_label, 99),
            0 if gap.requirement_priority == "required" else 1,
            gap.requirement_label,
        ),
    )


def order_strength_matches(
    matches: list[RequirementMatch],
    adaptation_summary: AdaptationSummary,
) -> list[RequirementMatch]:
    """Order matched requirements so strengths reflect JD emphasis first."""
    priority_order = {
        label: index for index, label in enumerate(adaptation_summary.prioritized_strengths)
    }
    return sorted(
        [match for match in matches if match.status == "matched"],
        key=lambda match: (
            0 if match.requirement_label in priority_order else 1,
            priority_order.get(match.requirement_label, 99),
            0 if match.requirement_priority == "required" else 1,
            match.requirement_label,
        ),
    )


def _build_context(jd_schema: JDSchema) -> str:
    parts = [
        jd_schema.job_title,
        jd_schema.company,
        jd_schema.domain_hint or "",
        jd_schema.seniority_hint or "",
        *jd_schema.responsibilities,
        *(requirement.label for requirement in jd_schema.required_requirements),
        *(requirement.label for requirement in jd_schema.preferred_requirements),
    ]
    return " ".join(part for part in parts if part).lower()


def _derive_role_focus(context: str, jd_schema: JDSchema) -> str:
    for role_focus, keywords in ROLE_KEYWORDS.items():
        if any(keyword in context for keyword in keywords):
            return role_focus
    if jd_schema.domain_hint:
        return f"{jd_schema.domain_hint}_focused"

    title_tokens = _tokenize(jd_schema.job_title)
    if title_tokens:
        return "_".join(title_tokens[:2])
    return ""


def _derive_company_signals(context: str) -> list[str]:
    signals = [
        signal
        for signal, keywords in COMPANY_SIGNAL_KEYWORDS.items()
        if any(keyword in context for keyword in keywords)
    ]
    return signals[:3]


def _score_requirement_emphasis(
    *,
    label: str,
    priority: str,
    context: str,
    role_focus: str,
) -> int:
    label_tokens = _tokenize(label)
    score = 3 if priority == "required" else 1
    for token in label_tokens:
        if token in context:
            score += 2
        if role_focus and token in role_focus:
            score += 1
    return score


def _take_top_labels(scores: dict[str, int], limit: int) -> list[str]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [label for label, _score in ranked[:limit]]


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())
