"""Unit tests for parse-service envelopes and degraded-input behavior."""

from __future__ import annotations

from app.services.parse_service import parse_jd_text, parse_resume_file, parse_resume_text
from tests.conftest import SAMPLES_DIR, load_sample


def test_parse_resume_text_handles_aliases_warnings_and_partial_segments() -> None:
    result = parse_resume_text(load_sample("messy_resume.txt"), source_name="messy_resume.txt")

    warning_codes = {warning.warning_code for warning in result.warnings}
    normalized_skills = {skill.normalized_name for skill in result.parsed_schema.skills}

    assert result.source_type == "text"
    assert result.source_name == "messy_resume.txt"
    assert result.parsed_schema.candidate_name == "Jordan Rivera"
    assert result.parsed_schema.summary.startswith("Backend engineer with 5 years")
    assert {"python", "fastapi", "rest_api", "postgresql", "aws"}.issubset(normalized_skills)
    assert warning_codes >= {
        "bullet_format_normalized",
        "colon_headers_normalized",
        "section_header_alias_used",
        "unsupported_section_header",
    }
    assert result.unsupported_segments[0].section == "Open Source"
    assert "Maintainer" in result.unsupported_segments[0].text
    assert result.parser_confidence.level == "medium"
    assert result.parser_confidence.extraction_complete is True


def test_parse_jd_text_handles_realistic_headers_and_confidence_metadata() -> None:
    result = parse_jd_text(load_sample("messy_jd.txt"), source_name="messy_jd.txt")

    warning_codes = {warning.warning_code for warning in result.warnings}

    assert result.parsed_schema.job_title == "Platform Backend Engineer"
    assert result.parsed_schema.company == "CareBridge"
    assert len(result.parsed_schema.responsibilities) == 1
    assert len(result.parsed_schema.required_requirements) == 4
    assert len(result.parsed_schema.preferred_requirements) == 3
    assert len(result.parsed_schema.education_requirements) == 1
    assert warning_codes >= {
        "section_header_alias_used",
        "unsupported_section_header",
    }
    assert result.parser_confidence.level == "medium"
    assert result.parser_confidence.extraction_complete is True


def test_parse_scanned_pdf_keeps_needs_ocr_separate_from_extraction_quality() -> None:
    content = (SAMPLES_DIR / "scanned_resume_placeholder.pdf").read_bytes()

    result = parse_resume_file(content, filename="scanned_resume_placeholder.pdf")

    warning_codes = {warning.warning_code for warning in result.warnings}
    unsupported_reasons = {segment.reason for segment in result.unsupported_segments}

    assert result.raw_text == ""
    assert result.cleaned_text == ""
    assert "pdf_scanned_needs_ocr" in warning_codes
    assert "scanned_pdf_requires_ocr" in unsupported_reasons
    assert result.parser_confidence.level == "low"
    assert result.parser_confidence.extraction_complete is False


def test_parse_image_keeps_needs_ocr_separate_from_clean_text() -> None:
    result = parse_resume_file(b"placeholder", filename="resume.png", media_type="image/png")

    warning_codes = {warning.warning_code for warning in result.warnings}
    unsupported_reasons = {segment.reason for segment in result.unsupported_segments}

    assert result.raw_text == ""
    assert result.cleaned_text == ""
    assert "image_requires_ocr" in warning_codes
    assert "image_requires_ocr" in unsupported_reasons
    assert result.parser_confidence.level == "low"
    assert result.parser_confidence.extraction_complete is False
