"""Shared deterministic fit-label derivation."""

from __future__ import annotations

from app.schemas.match import MatchResult


def derive_fit_label(match_result: MatchResult) -> str:
    """Map the deterministic score and blocker shape into a coarse fit label."""
    blockers = match_result.blocker_flags
    if blockers.missing_required_skills or blockers.seniority_mismatch:
        return "poor"
    if match_result.overall_score >= 80 and not blockers.unsupported_claims:
        return "strong"
    if match_result.overall_score >= 40:
        return "partial"
    return "poor"
