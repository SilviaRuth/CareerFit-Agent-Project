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


def test_m1_fixture_regression_stays_stable_for_strong_fit_score_shape() -> None:
    result = match_resume_to_jd(
        load_sample("strong_fit_resume.txt"),
        load_sample("strong_fit_jd.txt"),
    )

    assert result.overall_score == 89
    assert result.dimension_scores.skills == 100
    assert result.dimension_scores.experience == 100
    assert result.dimension_scores.projects == 43
    assert result.dimension_scores.domain_fit == 100
    assert result.dimension_scores.education == 100


def test_m4_role_adaptation_prioritizes_backend_platform_requirements() -> None:
    result = match_resume_to_jd(
        load_sample("strong_fit_resume.txt"),
        load_sample("responsibility_heavy_jd.txt"),
    )

    assert result.adaptation_summary.role_focus == "backend_platform"
    assert "platform_reliability" in result.adaptation_summary.company_signals
    assert result.adaptation_summary.emphasized_requirements == ["aws", "fastapi", "python"]
    assert result.adaptation_summary.prioritized_strengths == ["aws", "fastapi", "python"]
    assert result.strengths[0] == "Matched required aws with resume evidence."


def test_m4_evidence_summary_keeps_reviewable_section_counts() -> None:
    result = match_resume_to_jd(
        load_sample("strong_fit_resume.txt"),
        load_sample("strong_fit_jd.txt"),
    )

    assert result.evidence_summary.resume_section_counts["experience"] >= 1
    assert result.evidence_summary.resume_section_counts["projects"] >= 1
    assert result.evidence_summary.resume_section_counts["education"] >= 1
    assert result.evidence_summary.jd_section_counts["required"] >= 1
    assert result.evidence_summary.jd_section_counts["preferred"] >= 1
