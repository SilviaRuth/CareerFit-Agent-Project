"""Unit tests for the multimodal ingestion evaluation runner."""

from __future__ import annotations

from app.evaluation.multimodal_runner import run_multimodal_benchmark


def test_multimodal_benchmark_reports_needs_ocr_and_guardrails() -> None:
    report = run_multimodal_benchmark()

    assert report.metrics.case_count == 3
    assert report.metrics.needs_ocr_detection_accuracy == 1.0
    assert report.metrics.diagnostic_coverage == 1.0
    assert report.metrics.unsupported_reason_coverage == 1.0
    assert report.metrics.low_confidence_guardrail_accuracy == 1.0

    scanned_pdf = next(
        case for case in report.cases if case.case_id == "scanned_pdf_resume_needs_ocr"
    )
    image_case = next(case for case in report.cases if case.case_id == "image_resume_needs_ocr")
    clean_pdf = next(
        case for case in report.cases if case.case_id == "clean_text_pdf_resume_no_ocr"
    )

    assert scanned_pdf.parser_level == "low"
    assert scanned_pdf.extraction_complete is False
    assert scanned_pdf.needs_ocr_detected is True
    assert scanned_pdf.needs_ocr_correct is True
    assert scanned_pdf.missing_warning_codes == []
    assert image_case.parser_level == "low"
    assert image_case.needs_ocr_detected is True
    assert image_case.needs_ocr_correct is True
    assert image_case.missing_unsupported_reasons == []
    assert clean_pdf.parser_level == "high"
    assert clean_pdf.extraction_complete is True
    assert clean_pdf.needs_ocr_detected is False
    assert clean_pdf.needs_ocr_correct is True
    assert clean_pdf.missing_warning_codes == []
    assert clean_pdf.missing_unsupported_reasons == []
