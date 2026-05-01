"""Multimodal ingestion benchmark design for scanned/image document quality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.evaluation.utils import safe_ratio
from app.services.parse_service import parse_jd_file, parse_resume_file

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLES_DIR = REPO_ROOT / "data" / "samples"
DEFAULT_EVAL_DIR = REPO_ROOT / "data" / "eval"
DEFAULT_MANIFEST_PATH = DEFAULT_EVAL_DIR / "multimodal_manifest.json"


class MultimodalCase(BaseModel):
    """Manifest entry for one multimodal ingestion-quality case."""

    case_id: str
    document_type: Literal["resume", "job_description"]
    sample_name: str
    media_type: str
    expected_eval: str


class MultimodalExpected(BaseModel):
    """Expected needs-OCR and diagnostic behavior for one fixture."""

    expected_warning_codes: list[str] = Field(default_factory=list)
    expected_unsupported_reasons: list[str] = Field(default_factory=list)
    parser_level: Literal["high", "medium", "low"]
    extraction_complete: bool
    needs_ocr: bool
    max_parser_score: float | None = Field(default=None, ge=0.0, le=1.0)


class MultimodalMetrics(BaseModel):
    """Aggregate document-quality metrics for multimodal ingestion."""

    case_count: int
    needs_ocr_detection_accuracy: float
    diagnostic_coverage: float
    unsupported_reason_coverage: float
    low_confidence_guardrail_accuracy: float


class MultimodalCaseReport(BaseModel):
    """Detailed result for one multimodal ingestion fixture."""

    case_id: str
    document_type: Literal["resume", "job_description"]
    parser_score: float
    parser_level: str
    extraction_complete: bool
    needs_ocr_detected: bool
    needs_ocr_correct: bool
    missing_warning_codes: list[str] = Field(default_factory=list)
    missing_unsupported_reasons: list[str] = Field(default_factory=list)
    confidence_guardrail_correct: bool


class MultimodalReport(BaseModel):
    """Structured multimodal ingestion benchmark output."""

    manifest_path: str
    report_label: str | None = None
    generated_at: str | None = None
    metrics: MultimodalMetrics
    cases: list[MultimodalCaseReport]


def run_multimodal_benchmark(
    manifest_path: Path | None = None,
    *,
    samples_dir: Path | None = None,
    eval_dir: Path | None = None,
    report_label: str | None = None,
    generated_at: str | None = None,
) -> MultimodalReport:
    """Run fixture-backed checks that separate ingestion/OCR quality from matching."""
    manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
    samples_dir = samples_dir or DEFAULT_SAMPLES_DIR
    eval_dir = eval_dir or DEFAULT_EVAL_DIR

    manifest = _load_json(manifest_path)
    cases = [MultimodalCase.model_validate(item) for item in manifest["cases"]]
    reports: list[MultimodalCaseReport] = []
    warning_total = 0
    warning_correct = 0
    unsupported_total = 0
    unsupported_correct = 0

    for case in cases:
        expected = MultimodalExpected.model_validate(_load_json(eval_dir / case.expected_eval))
        response = _parse_case(case, samples_dir)
        report = _build_case_report(case, expected, response)
        reports.append(report)

        warning_total += len(expected.expected_warning_codes)
        warning_correct += len(expected.expected_warning_codes) - len(report.missing_warning_codes)
        unsupported_total += len(expected.expected_unsupported_reasons)
        unsupported_correct += len(expected.expected_unsupported_reasons) - len(
            report.missing_unsupported_reasons
        )

    metrics = MultimodalMetrics(
        case_count=len(reports),
        needs_ocr_detection_accuracy=safe_ratio(
            sum(report.needs_ocr_correct for report in reports),
            len(reports),
        ),
        diagnostic_coverage=safe_ratio(warning_correct, warning_total),
        unsupported_reason_coverage=safe_ratio(unsupported_correct, unsupported_total),
        low_confidence_guardrail_accuracy=safe_ratio(
            sum(report.confidence_guardrail_correct for report in reports),
            len(reports),
        ),
    )
    return MultimodalReport(
        manifest_path=_display_path(manifest_path),
        report_label=report_label,
        generated_at=generated_at,
        metrics=metrics,
        cases=reports,
    )


def _parse_case(case: MultimodalCase, samples_dir: Path):
    sample_path = _resolve_sample_path(case.sample_name, samples_dir)
    content = sample_path.read_bytes()
    filename = sample_path.name
    if case.document_type == "resume":
        return parse_resume_file(content, filename=filename, media_type=case.media_type)
    return parse_jd_file(content, filename=filename, media_type=case.media_type)


def _build_case_report(case: MultimodalCase, expected: MultimodalExpected, response):
    actual_warning_codes = {warning.warning_code for warning in response.warnings}
    actual_unsupported_reasons = {segment.reason for segment in response.unsupported_segments}
    missing_warning_codes = sorted(set(expected.expected_warning_codes) - actual_warning_codes)
    missing_unsupported_reasons = sorted(
        set(expected.expected_unsupported_reasons) - actual_unsupported_reasons
    )
    needs_ocr_detected = bool(
        actual_warning_codes.intersection({"image_requires_ocr", "pdf_scanned_needs_ocr"})
    )
    max_score_ok = (
        expected.max_parser_score is None
        or response.parser_confidence.score <= expected.max_parser_score
    )
    confidence_guardrail_correct = (
        response.parser_confidence.level == expected.parser_level
        and response.parser_confidence.extraction_complete is expected.extraction_complete
        and max_score_ok
    )
    return MultimodalCaseReport(
        case_id=case.case_id,
        document_type=case.document_type,
        parser_score=response.parser_confidence.score,
        parser_level=response.parser_confidence.level,
        extraction_complete=response.parser_confidence.extraction_complete,
        needs_ocr_detected=needs_ocr_detected,
        needs_ocr_correct=needs_ocr_detected is expected.needs_ocr,
        missing_warning_codes=missing_warning_codes,
        missing_unsupported_reasons=missing_unsupported_reasons,
        confidence_guardrail_correct=confidence_guardrail_correct,
    )


def _resolve_sample_path(value: str, samples_dir: Path) -> Path:
    explicit_path = REPO_ROOT / value
    if explicit_path.exists():
        return explicit_path
    return samples_dir / value


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    """Run the multimodal ingestion benchmark and print a JSON report."""
    report = run_multimodal_benchmark()
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
