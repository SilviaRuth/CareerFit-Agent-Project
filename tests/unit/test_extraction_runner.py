"""Unit tests for the extraction benchmark runner."""

from __future__ import annotations

from app.evaluation.extraction_runner import run_extraction_benchmark


def test_extraction_benchmark_matches_current_parse_expectations() -> None:
    report = run_extraction_benchmark()

    assert report.metrics.case_count == 13
    assert report.metrics.confidence_accuracy == 1.0
    assert report.metrics.field_expectation_accuracy == 1.0
    assert report.metrics.unsupported_segment_coverage == 1.0

    messy_resume = next(case for case in report.cases if case.case_id == "messy_resume")
    low_confidence = next(case for case in report.cases if case.case_id == "low_confidence_resume")
    cleaned_jd = next(case for case in report.cases if case.case_id == "cleaned_dataset_jd")

    assert messy_resume.parser_level == "medium"
    assert messy_resume.field_expectation_accuracy == 1.0
    assert low_confidence.parser_level == "low"
    assert low_confidence.extraction_complete is False
    assert cleaned_jd.parser_level == "high"

    accountant_resume = next(case for case in report.cases if case.case_id == "accountant_resume")
    healthcare_resume = next(case for case in report.cases if case.case_id == "healthcare_resume")

    assert accountant_resume.parser_level == "high"
    assert healthcare_resume.parser_level == "low"
    assert healthcare_resume.extraction_complete is False
