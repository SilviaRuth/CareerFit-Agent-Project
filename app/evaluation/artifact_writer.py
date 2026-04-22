"""Write benchmark and extraction reports to reviewable artifact files."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from app.evaluation.benchmark_runner import run_benchmark
from app.evaluation.comparison_runner import run_comparison_benchmark
from app.evaluation.extraction_runner import run_extraction_benchmark
from app.evaluation.recommendation_runner import run_recommendation_benchmark

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_ROOT = REPO_ROOT / "data" / "eval" / "reports"
DEFAULT_REPORT_DIR = DEFAULT_REPORT_ROOT / "baseline"
DEFAULT_SNAPSHOT_DIR = DEFAULT_REPORT_ROOT / "snapshots"


def write_evaluation_artifacts(
    output_dir: Path | None = None,
    *,
    snapshot_label: str = "baseline",
) -> list[Path]:
    """Generate JSON plus Markdown artifacts for offline regression review."""
    output_dir = output_dir or _resolve_output_dir(snapshot_label)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()

    benchmark_report = run_benchmark(report_label=snapshot_label, generated_at=generated_at)
    extraction_report = run_extraction_benchmark(
        report_label=snapshot_label,
        generated_at=generated_at,
    )
    comparison_report = run_comparison_benchmark(
        report_label=snapshot_label,
        generated_at=generated_at,
    )
    recommendation_report = run_recommendation_benchmark(
        report_label=snapshot_label,
        generated_at=generated_at,
    )

    benchmark_path = output_dir / "benchmark_report.json"
    extraction_path = output_dir / "extraction_report.json"
    comparison_path = output_dir / "comparison_report.json"
    recommendation_path = output_dir / "recommendation_report.json"
    manifest_path = output_dir / "artifact_manifest.json"
    summary_path = output_dir / "summary.md"

    benchmark_path.write_text(
        benchmark_report.model_dump_json(indent=2),
        encoding="utf-8",
    )
    extraction_path.write_text(
        extraction_report.model_dump_json(indent=2),
        encoding="utf-8",
    )
    comparison_path.write_text(
        comparison_report.model_dump_json(indent=2),
        encoding="utf-8",
    )
    recommendation_path.write_text(
        recommendation_report.model_dump_json(indent=2),
        encoding="utf-8",
    )
    comparison_to_baseline_path = _write_snapshot_comparison(
        output_dir=output_dir,
        snapshot_label=snapshot_label,
        benchmark_report=benchmark_report.model_dump(),
        extraction_report=extraction_report.model_dump(),
        comparison_report=comparison_report.model_dump(),
        recommendation_report=recommendation_report.model_dump(),
    )
    manifest_payload = {
        "snapshot_label": snapshot_label,
        "generated_at": generated_at,
        "reports": {
            "benchmark_manifest_path": benchmark_report.manifest_path,
            "extraction_manifest_path": extraction_report.manifest_path,
            "comparison_manifest_path": comparison_report.manifest_path,
            "recommendation_manifest_path": recommendation_report.manifest_path,
        },
        "report_files": [
            _display_path(benchmark_path),
            _display_path(extraction_path),
            _display_path(comparison_path),
            _display_path(recommendation_path),
        ],
    }
    if comparison_to_baseline_path is not None:
        manifest_payload["report_files"].append(_display_path(comparison_to_baseline_path))
    manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")
    summary_lines = [
        "# Evaluation Snapshot",
        "",
        f"- Snapshot label: `{snapshot_label}`",
        f"- Generated at: `{generated_at}`",
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
        "## Comparison Benchmark",
        "",
        f"- Scenarios: {comparison_report.metrics.scenario_count}",
        f"- Ranking accuracy: {comparison_report.metrics.ranking_accuracy}",
        f"- Fit label accuracy: {comparison_report.metrics.fit_label_accuracy}",
        (
            "- Low-confidence ordering accuracy: "
            f"{comparison_report.metrics.low_confidence_order_accuracy}"
        ),
        "",
        "## Recommendation Benchmark",
        "",
        f"- Cases: {recommendation_report.metrics.case_count}",
        f"- Usefulness accuracy: {recommendation_report.metrics.usefulness_accuracy}",
        f"- Grounding accuracy: {recommendation_report.metrics.grounding_accuracy}",
        (
            "- Blocker guardrail accuracy: "
            f"{recommendation_report.metrics.blocker_guardrail_accuracy}"
        ),
        f"- Hallucination rate: {recommendation_report.metrics.hallucination_rate}",
        "",
        "## Artifacts",
        "",
        f"- `{_display_path(benchmark_path)}`",
        f"- `{_display_path(extraction_path)}`",
        f"- `{_display_path(comparison_path)}`",
        f"- `{_display_path(recommendation_path)}`",
        f"- `{_display_path(manifest_path)}`",
    ]
    if comparison_to_baseline_path is not None:
        summary_lines.append(f"- `{_display_path(comparison_to_baseline_path)}`")
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    generated_paths = [
        benchmark_path,
        extraction_path,
        comparison_path,
        recommendation_path,
        manifest_path,
        summary_path,
    ]
    if comparison_to_baseline_path is not None:
        generated_paths.append(comparison_to_baseline_path)
    return generated_paths


def _resolve_output_dir(snapshot_label: str) -> Path:
    if snapshot_label == "baseline":
        return DEFAULT_REPORT_DIR
    return DEFAULT_SNAPSHOT_DIR / snapshot_label


def _write_snapshot_comparison(
    *,
    output_dir: Path,
    snapshot_label: str,
    benchmark_report: dict,
    extraction_report: dict,
    comparison_report: dict,
    recommendation_report: dict,
) -> Path | None:
    if snapshot_label == "baseline":
        return None

    baseline_dir = DEFAULT_REPORT_DIR
    baseline_benchmark_path = baseline_dir / "benchmark_report.json"
    baseline_extraction_path = baseline_dir / "extraction_report.json"
    baseline_comparison_path = baseline_dir / "comparison_report.json"
    baseline_recommendation_path = baseline_dir / "recommendation_report.json"
    if not (
        baseline_benchmark_path.exists()
        and baseline_extraction_path.exists()
        and baseline_comparison_path.exists()
        and baseline_recommendation_path.exists()
    ):
        return None

    baseline_benchmark = json.loads(baseline_benchmark_path.read_text(encoding="utf-8"))
    baseline_extraction = json.loads(baseline_extraction_path.read_text(encoding="utf-8"))
    baseline_comparison = json.loads(baseline_comparison_path.read_text(encoding="utf-8"))
    baseline_recommendation = json.loads(
        baseline_recommendation_path.read_text(encoding="utf-8")
    )

    diff_payload = {
        "snapshot_label": snapshot_label,
        "compared_to": "baseline",
        "benchmark_metric_delta": _metric_delta(
            baseline_benchmark["metrics"],
            benchmark_report["metrics"],
        ),
        "extraction_metric_delta": _metric_delta(
            baseline_extraction["metrics"],
            extraction_report["metrics"],
        ),
        "comparison_metric_delta": _metric_delta(
            baseline_comparison["metrics"],
            comparison_report["metrics"],
        ),
        "recommendation_metric_delta": _metric_delta(
            baseline_recommendation["metrics"],
            recommendation_report["metrics"],
        ),
    }
    diff_path = output_dir / "snapshot_comparison.json"
    diff_path.write_text(json.dumps(diff_payload, indent=2) + "\n", encoding="utf-8")
    return diff_path


def _metric_delta(baseline_metrics: dict, current_metrics: dict) -> dict[str, float]:
    delta: dict[str, float] = {}
    for key, value in current_metrics.items():
        baseline_value = baseline_metrics.get(key)
        if isinstance(value, (int, float)) and isinstance(baseline_value, (int, float)):
            delta[key] = round(value - baseline_value, 3)
    return delta


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    """Write the default evaluation artifact set."""
    parser = argparse.ArgumentParser(description="Write reviewable evaluation artifacts.")
    parser.add_argument(
        "--snapshot-label",
        default="baseline",
        help=(
            "Snapshot label to write under data/eval/reports/. "
            "Use 'baseline' for the checked-in baseline."
        ),
    )
    args = parser.parse_args()
    for path in write_evaluation_artifacts(snapshot_label=args.snapshot_label):
        print(path.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
