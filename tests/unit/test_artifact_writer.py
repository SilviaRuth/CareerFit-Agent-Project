"""Unit tests for evaluation artifact generation."""

from __future__ import annotations

from pathlib import Path

from app.evaluation.artifact_writer import write_evaluation_artifacts


def test_artifact_writer_creates_reviewable_files(tmp_path: Path) -> None:
    paths = write_evaluation_artifacts(tmp_path)

    assert len(paths) == 5
    assert all(path.exists() for path in paths)
    assert (tmp_path / "benchmark_report.json").read_text(encoding="utf-8")
    assert (tmp_path / "extraction_report.json").read_text(encoding="utf-8")
    assert (tmp_path / "comparison_report.json").read_text(encoding="utf-8")
    assert (tmp_path / "artifact_manifest.json").read_text(encoding="utf-8")
    assert "Evaluation Snapshot" in (tmp_path / "summary.md").read_text(encoding="utf-8")


def test_artifact_writer_can_create_versioned_snapshot_comparison(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots" / "candidate"
    paths = write_evaluation_artifacts(snapshot_dir, snapshot_label="candidate")

    assert any(path.name == "snapshot_comparison.json" for path in paths)
