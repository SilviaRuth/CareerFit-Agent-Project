"""Unit tests for evaluation artifact generation."""

from __future__ import annotations

from pathlib import Path

from app.evaluation.artifact_writer import write_evaluation_artifacts


def test_artifact_writer_creates_reviewable_files(tmp_path: Path) -> None:
    paths = write_evaluation_artifacts(tmp_path)

    assert len(paths) == 3
    assert all(path.exists() for path in paths)
    assert (tmp_path / "benchmark_report.json").read_text(encoding="utf-8")
    assert (tmp_path / "extraction_report.json").read_text(encoding="utf-8")
    assert "Evaluation Baseline" in (tmp_path / "summary.md").read_text(encoding="utf-8")
