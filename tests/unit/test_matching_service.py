"""Unit tests for rule-based matching behavior."""

from __future__ import annotations

from app.services.matching_service import match_resume_to_jd
from tests.conftest import load_eval, load_sample


def test_strong_fit_matches_required_and_preferred_expectations() -> None:
    result = match_resume_to_jd(
        load_sample("strong_fit_resume.txt"),
        load_sample("strong_fit_jd.txt"),
    )
    expected = load_eval("strong_fit_expected.json")

    required_labels = {
        match.requirement_label for match in result.required_matches if match.status == "matched"
    }
    preferred_labels = {
        match.requirement_label for match in result.preferred_matches if match.status == "matched"
    }

    assert set(expected["required_skill_matches"]).issubset(required_labels)
    assert set(expected["preferred_skill_matches"]).issubset(preferred_labels)
    assert result.blocker_flags.missing_required_skills is False
    assert result.blocker_flags.seniority_mismatch is False
    assert result.blocker_flags.unsupported_claims is False


def test_partial_fit_marks_missing_evidence_and_unsupported_claims() -> None:
    result = match_resume_to_jd(
        load_sample("partial_fit_resume.txt"),
        load_sample("partial_fit_jd.txt"),
    )
    expected = load_eval("partial_fit_expected.json")

    matched_required = {
        match.requirement_label for match in result.required_matches if match.status == "matched"
    }
    gap_map = {gap.requirement_label: gap.gap_type for gap in result.gaps}

    assert set(expected["required_skill_matches"]).issubset(matched_required)
    assert gap_map["fastapi"] == "missing_evidence"
    assert gap_map["rest api development"] == "missing_evidence"
    assert gap_map["aws deployment"] == "missing_evidence"
    assert result.blocker_flags.missing_required_skills is False
    assert result.blocker_flags.seniority_mismatch is False
    assert (
        result.blocker_flags.unsupported_claims is expected["blocker_flags"]["unsupported_claims"]
    )


def test_poor_fit_surfaces_blockers_and_missing_skill_distinction() -> None:
    result = match_resume_to_jd(
        load_sample("poor_fit_resume.txt"),
        load_sample("poor_fit_jd.txt"),
    )
    expected = load_eval("poor_fit_expected.json")

    gap_map = {gap.requirement_label: gap.gap_type for gap in result.gaps}

    assert gap_map["python"] == "missing_evidence"
    assert gap_map["fastapi"] == "missing_skill"
    assert gap_map["postgresql"] == "missing_skill"
    assert gap_map["aws"] == "missing_skill"
    assert (
        result.blocker_flags.missing_required_skills
        is expected["blocker_flags"]["missing_required_skills"]
    )
    assert (
        result.blocker_flags.seniority_mismatch is expected["blocker_flags"]["seniority_mismatch"]
    )
    assert (
        result.blocker_flags.unsupported_claims is expected["blocker_flags"]["unsupported_claims"]
    )
