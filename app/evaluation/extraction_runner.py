"""Offline extraction benchmark runner for parse-service regression coverage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.services.parse_service import parse_jd_text, parse_resume_text

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLES_DIR = REPO_ROOT / "data" / "samples"
DEFAULT_EVAL_DIR = REPO_ROOT / "data" / "eval"
DEFAULT_MANIFEST_PATH = DEFAULT_EVAL_DIR / "extraction_manifest.json"


class ExtractionCase(BaseModel):
    """Manifest entry for one extraction benchmark case."""

    case_id: str
    document_type: Literal["resume", "job_description"]
    sample_name: str
    expected_eval: str


class ExtractionMetrics(BaseModel):
    """Aggregate metrics for the extraction benchmark."""

    case_count: int
    confidence_accuracy: float
    field_expectation_accuracy: float
    unsupported_segment_coverage: float


class ExtractionCaseReport(BaseModel):
    """Detailed extraction benchmark result for one case."""

    case_id: str
    document_type: Literal["resume", "job_description"]
    parser_score: float
    parser_level: str
    extraction_complete: bool
    confidence_correct: bool
    field_expectation_accuracy: float
    unsupported_segment_coverage: float
    missing_expected_fields: list[str] = Field(default_factory=list)
    missing_expected_unsupported_sections: list[str] = Field(default_factory=list)


class ExtractionReport(BaseModel):
    """Structured extraction benchmark output."""

    manifest_path: str
    report_label: str | None = None
    generated_at: str | None = None
    metrics: ExtractionMetrics
    cases: list[ExtractionCaseReport]


def run_extraction_benchmark(
    manifest_path: Path | None = None,
    *,
    samples_dir: Path | None = None,
    eval_dir: Path | None = None,
    report_label: str | None = None,
    generated_at: str | None = None,
) -> ExtractionReport:
    """Run the parse benchmark across the extraction fixture manifest."""
    manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
    samples_dir = samples_dir or DEFAULT_SAMPLES_DIR
    eval_dir = eval_dir or DEFAULT_EVAL_DIR

    manifest = _load_json(manifest_path)
    cases = [ExtractionCase.model_validate(item) for item in manifest["cases"]]
    reports: list[ExtractionCaseReport] = []
    field_total = 0
    field_correct = 0
    unsupported_total = 0
    unsupported_correct = 0

    for case in cases:
        expected = _load_json(eval_dir / case.expected_eval)
        text = _resolve_text_path(case.sample_name, samples_dir).read_text(encoding="utf-8")
        response = (
            parse_resume_text(text) if case.document_type == "resume" else parse_jd_text(text)
        )

        report = _build_case_report(case, expected, response)
        reports.append(report)

        field_total += len(expected["required_fields"])
        field_correct += len(expected["required_fields"]) - len(report.missing_expected_fields)
        unsupported_total += len(expected["unsupported_sections"])
        unsupported_correct += len(expected["unsupported_sections"]) - len(
            report.missing_expected_unsupported_sections
        )

    metrics = ExtractionMetrics(
        case_count=len(reports),
        confidence_accuracy=_safe_ratio(
            sum(report.confidence_correct for report in reports),
            len(reports),
        ),
        field_expectation_accuracy=_safe_ratio(field_correct, field_total),
        unsupported_segment_coverage=_safe_ratio(unsupported_correct, unsupported_total),
    )
    return ExtractionReport(
        manifest_path=str(manifest_path.relative_to(REPO_ROOT)),
        report_label=report_label,
        generated_at=generated_at,
        metrics=metrics,
        cases=reports,
    )


def _build_case_report(case: ExtractionCase, expected: dict, response) -> ExtractionCaseReport:
    actual_unsupported_sections = {segment.section for segment in response.unsupported_segments}
    missing_fields: list[str] = []
    actual_fields: dict[str, object]

    if case.document_type == "resume":
        schema = response.parsed_schema
        actual_fields = {
            "candidate_name": schema.candidate_name,
            "summary": schema.summary,
            "skills_count": len(schema.skills),
            "experience_count": len(schema.experience_items),
            "education_count": len(schema.education_items),
        }
    else:
        schema = response.parsed_schema
        actual_fields = {
            "job_title": schema.job_title,
            "company": schema.company,
            "required_count": len(schema.required_requirements),
            "preferred_count": len(schema.preferred_requirements),
            "education_count": len(schema.education_requirements),
        }

    for field_name, expected_value in expected["required_fields"].items():
        actual_value = actual_fields.get(field_name)
        if actual_value != expected_value:
            missing_fields.append(field_name)

    missing_unsupported_sections = sorted(
        set(expected["unsupported_sections"]) - actual_unsupported_sections
    )
    confidence_correct = (
        response.parser_confidence.level == expected["parser_level"]
        and response.parser_confidence.score >= expected["min_score"]
        and response.parser_confidence.extraction_complete is expected["extraction_complete"]
    )

    return ExtractionCaseReport(
        case_id=case.case_id,
        document_type=case.document_type,
        parser_score=response.parser_confidence.score,
        parser_level=response.parser_confidence.level,
        extraction_complete=response.parser_confidence.extraction_complete,
        confidence_correct=confidence_correct,
        field_expectation_accuracy=_safe_ratio(
            len(expected["required_fields"]) - len(missing_fields),
            len(expected["required_fields"]),
        ),
        unsupported_segment_coverage=_safe_ratio(
            len(expected["unsupported_sections"]) - len(missing_unsupported_sections),
            len(expected["unsupported_sections"]),
        ),
        missing_expected_fields=missing_fields,
        missing_expected_unsupported_sections=missing_unsupported_sections,
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_text_path(value: str, samples_dir: Path) -> Path:
    explicit_path = REPO_ROOT / value
    if explicit_path.exists():
        return explicit_path
    return samples_dir / value


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 3)


def main() -> None:
    """Run the extraction benchmark and print a JSON report."""
    report = run_extraction_benchmark()
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
