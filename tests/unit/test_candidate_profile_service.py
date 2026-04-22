"""Unit tests for reusable candidate profile memory."""

from __future__ import annotations

from app.services.candidate_profile_service import build_candidate_profile_memory
from tests.conftest import load_sample


def test_candidate_profile_memory_stays_auditable_and_evidence_linked() -> None:
    profile = build_candidate_profile_memory(
        load_sample("strong_fit_resume.txt"),
        source_name="strong_fit_resume.txt",
    )

    assert profile.candidate_name
    assert profile.audit.persistence == "none"
    assert profile.audit.derived_from_resume_only is True
    assert profile.memory_items
    assert any(item.evidence_used for item in profile.memory_items)
