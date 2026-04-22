"""Unit tests for recommendation benchmark reporting."""

from __future__ import annotations

from app.evaluation.recommendation_runner import run_recommendation_benchmark


def test_recommendation_runner_reports_grounded_m5_metrics() -> None:
    report = run_recommendation_benchmark()

    assert report.metrics.case_count >= 3
    assert report.metrics.grounding_accuracy >= 0.0
    assert report.metrics.hallucination_rate >= 0.0
    assert report.cases
