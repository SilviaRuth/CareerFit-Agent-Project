"""Shared grounding helpers for rewrite and interview-prep services."""

from __future__ import annotations

from app.schemas.common import EvidenceSpan
from app.schemas.match import GapItem, RequirementMatch
from app.services.generation.workflow import GenerationContext


def dedupe_evidence(spans: list[EvidenceSpan]) -> list[EvidenceSpan]:
    """Deduplicate evidence spans while preserving order."""
    seen: set[tuple[str, str, str, int | None, int | None, str | None]] = set()
    unique: list[EvidenceSpan] = []
    for span in spans:
        key = (
            span.source_document,
            span.section,
            span.text,
            span.start_char,
            span.end_char,
            span.normalized_value,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(span)
    return unique


def collect_context_evidence(context: GenerationContext) -> list[EvidenceSpan]:
    """Collect all evidence used across the current match result."""
    spans = list(context.match_result.evidence_spans)
    spans.extend(context.resume_parse.parsed_schema.evidence_spans)
    spans.extend(context.jd_parse.parsed_schema.evidence_spans)
    return dedupe_evidence(spans)


def extract_bullet_text(span: EvidenceSpan) -> str:
    """Extract the most useful line from a resume evidence span."""
    lines = [line.strip().lstrip("- ").strip() for line in span.text.split("\n") if line.strip()]
    if not lines:
        return span.text.strip()
    if span.section in {"experience", "projects"} and len(lines) > 1:
        return lines[1]
    return lines[0]


def sort_gaps(gaps: list[GapItem]) -> list[GapItem]:
    """Sort gaps by priority and severity for generation outputs."""
    priority_rank = {"required": 0, "preferred": 1}
    gap_rank = {
        "missing_skill": 0,
        "seniority_mismatch": 1,
        "domain_gap": 2,
        "education_gap": 3,
        "missing_evidence": 4,
    }
    return sorted(
        gaps,
        key=lambda gap: (
            priority_rank.get(gap.requirement_priority, 2),
            gap_rank.get(gap.gap_type, 5),
            gap.requirement_label,
        ),
    )


def top_supported_matches(context: GenerationContext, *, required_only: bool = True) -> list[RequirementMatch]:
    """Return matched requirements with resume evidence, prioritizing required matches."""
    matches = list(context.match_result.required_matches)
    if not required_only:
        matches.extend(context.match_result.preferred_matches)
    return [
        match
        for match in matches
        if match.status == "matched" and match.resume_evidence
    ]
