"""Static configuration for the Milestone 1 deterministic matcher."""

from __future__ import annotations

from typing import Final

SECTION_HEADERS: Final[dict[str, str]] = {
    "summary": "Summary",
    "skills": "Skills",
    "experience": "Experience",
    "projects": "Projects",
    "education": "Education",
    "required": "Required",
    "preferred": "Preferred",
}

MATCH_WEIGHTS: Final[dict[str, int]] = {
    "skills": 30,
    "experience": 30,
    "projects": 20,
    "domain_fit": 10,
    "education": 10,
}

CAPABILITY_PATTERNS: Final[dict[str, tuple[str, ...]]] = {
    "python": ("python",),
    "fastapi": ("fastapi",),
    "pytest": ("pytest",),
    "postgresql": ("postgresql", "postgres"),
    "docker": ("docker",),
    "aws": ("aws", "amazon web services"),
    "rest_api": ("rest api", "rest apis", "api design", "api development"),
    "healthcare": ("healthcare", "claims", "clinic"),
    "logistics": ("logistics", "supply chain", "fulfillment"),
    "cloud_platform": ("cloud platform", "platform services"),
    "computer_science_degree": ("computer science",),
}

ASSERTIVE_CLAIM_TERMS: Final[tuple[str, ...]] = ("claims", "expertise", "expert", "strong")
WEAK_PROJECT_TERMS: Final[tuple[str, ...]] = ("coursework", "small", "portfolio")
NEGATION_TERMS: Final[tuple[str, ...]] = ("did not", "no ", "without", "instead of")
