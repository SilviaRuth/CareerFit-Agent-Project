"""Shared test helpers for fixture-backed Milestone 1 tests."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "data" / "samples"
EVAL_DIR = REPO_ROOT / "data" / "eval"


def load_sample(name: str) -> str:
    """Load a sample text fixture by filename."""
    return (SAMPLES_DIR / name).read_text(encoding="utf-8")


def load_eval(name: str) -> dict:
    """Load a JSON evaluation fixture by filename."""
    return json.loads((EVAL_DIR / name).read_text(encoding="utf-8"))
