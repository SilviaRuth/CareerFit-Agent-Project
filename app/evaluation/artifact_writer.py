"""Write benchmark and extraction reports to reviewable artifact files."""

from __future__ import annotations

from pathlib import Path

from app.evaluation.benchmark_runner import run_benchmark
from app.evaluation.extraction_runner import run_extraction_benchmark

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "data" / "eval" / "reports" / "baseline"


def write_evaluation_artifacts(output_dir: Path | None = None) -> list[Path]:
    """Generate JSON plus Markdown artifacts for offline regression review."""
    output_dir = output_dir or DEFAULT_REPORT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark_report = run_benchmark()
    extraction_report = run_extraction_benchmark()

    benchmark_path = output_dir / "benchmark_report.json"
    extraction_path = output_dir / "extraction_report.json"
    summary_path = output_dir / "summary.md"

    benchmark_path.write_text(
        benchmark_report.model_dump_json(indent=2),
        encoding="utf-8",
    )
    extraction_path.write_text(
        extraction_report.model_dump_json(indent=2),
        encoding="utf-8",
    )
    summary_lines = [
        "# Evaluation Baseline",
        "",
        "## Match Benchmark",
        "",
        f"- Cases: {benchmark_report.metrics.case_count}",
        f"- Fit label accuracy: {benchmark_report.metrics.fit_label_accuracy}",
        f"- Blocker flag accuracy: {benchmark_report.metrics.blocker_flag_accuracy}",
        f"- Required match recall: {benchmark_report.metrics.required_match_recall}",
        f"- Preferred match recall: {benchmark_report.metrics.preferred_match_recall}",
        f"- Top-gap coverage: {benchmark_report.metrics.top_gap_coverage}",
        "",
        "## Extraction Benchmark",
        "",
        f"- Cases: {extraction_report.metrics.case_count}",
        f"- Confidence accuracy: {extraction_report.metrics.confidence_accuracy}",
        f"- Field expectation accuracy: {extraction_report.metrics.field_expectation_accuracy}",
        f"- Unsupported segment coverage: {extraction_report.metrics.unsupported_segment_coverage}",
        "",
        "## Artifacts",
        "",
        f"- `{_display_path(benchmark_path)}`",
        f"- `{_display_path(extraction_path)}`",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    return [benchmark_path, extraction_path, summary_path]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    """Write the default evaluation artifact set."""
    for path in write_evaluation_artifacts():
        print(path.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
