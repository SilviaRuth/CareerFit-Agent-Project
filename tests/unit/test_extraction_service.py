"""Unit tests for deterministic extraction behavior."""

from __future__ import annotations

from app.services.extraction_service import extract_jd_schema, extract_resume_schema
from app.services.text_normalizer import normalize_text
from tests.conftest import load_sample


def test_normalize_text_preserves_sections_and_collapses_whitespace() -> None:
    raw_text = "Alex Chen\r\n\r\nSummary\r\nBackend engineer   with  6 years.\r\n• Python\r\n"
    normalized = normalize_text(raw_text)

    assert "Alex Chen" in normalized
    assert "Summary" in normalized
    assert "Backend engineer with 6 years." in normalized
    assert "- Python" in normalized


def test_extract_resume_schema_uses_constrained_fixture_fields() -> None:
    resume_schema = extract_resume_schema(load_sample("strong_fit_resume.txt"))

    assert resume_schema.candidate_name == "Alex Chen"
    assert resume_schema.summary.startswith("Backend engineer with 6 years")
    assert [skill.normalized_name for skill in resume_schema.skills][:3] == [
        "python",
        "fastapi",
        "rest_api",
    ]
    assert len(resume_schema.experience_items) == 2
    assert len(resume_schema.project_items) == 1
    assert len(resume_schema.education_items) == 1
    assert resume_schema.total_years_experience == 6.0


def test_extract_jd_schema_splits_required_preferred_and_education() -> None:
    jd_schema = extract_jd_schema(load_sample("strong_fit_jd.txt"))

    assert jd_schema.job_title == "Senior Backend Engineer"
    assert jd_schema.company == "HealthStack"
    assert len(jd_schema.required_requirements) == 5
    assert len(jd_schema.preferred_requirements) == 4
    assert len(jd_schema.education_requirements) == 1
    assert jd_schema.seniority_hint == "senior"
    assert jd_schema.domain_hint == "healthcare"


def test_extract_jd_schema_prefers_fastapi_for_mixed_python_framework_requirement() -> None:
    jd_schema = extract_jd_schema(load_sample("strong_fit_jd.txt"))

    fastapi_requirement = next(
        requirement
        for requirement in jd_schema.required_requirements
        if "framework experience" in requirement.raw_text.lower()
    )

    assert fastapi_requirement.label == "fastapi"
    assert fastapi_requirement.normalized_label == "fastapi"


def test_extract_resume_schema_supports_realistic_header_aliases() -> None:
    resume_schema = extract_resume_schema(load_sample("messy_resume.txt"))

    assert resume_schema.candidate_name == "Jordan Rivera"
    assert resume_schema.summary.startswith("Backend engineer with 5 years")
    assert any(skill.normalized_name == "fastapi" for skill in resume_schema.skills)
    assert len(resume_schema.experience_items) == 2


def test_extract_jd_schema_supports_alias_headers_for_requirements() -> None:
    jd_schema = extract_jd_schema(load_sample("messy_jd.txt"))

    assert jd_schema.job_title == "Platform Backend Engineer"
    assert len(jd_schema.required_requirements) == 4
    assert len(jd_schema.preferred_requirements) == 3
    assert len(jd_schema.responsibilities) == 1
