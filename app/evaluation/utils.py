"""Shared deterministic helpers for offline evaluation runners."""

from __future__ import annotations


def safe_ratio(numerator: int, denominator: int) -> float:
    """Return a rounded ratio, treating empty expectation sets as fully satisfied."""
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 3)
