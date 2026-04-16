"""Static configuration for the Milestone 1 deterministic matcher."""

from __future__ import annotations

from typing import Final

SECTION_HEADERS: Final[dict[str, str]] = {
    "summary": "Summary",
    "skills": "Skills",
    "experience": "Experience",
    "projects": "Projects",
    "education": "Education",
    "responsibilities": "Responsibilities",
    "required": "Required",
    "preferred": "Preferred",
}

SECTION_HEADER_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "summary": (
        "summary",
        "professional summary",
        "career summary",
        "profile",
        "about",
        "overview",
    ),
    "skills": (
        "skills",
        "technical skills",
        "core competencies",
        "competencies",
        "technologies",
        "tooling",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "career experience",
    ),
    "projects": (
        "projects",
        "project highlights",
        "selected projects",
        "projects and impact",
        "project work",
    ),
    "education": (
        "education",
        "academic background",
        "education and certifications",
        "education & certifications",
        "education requirements",
    ),
    "responsibilities": (
        "responsibilities",
        "what you'll do",
        "what you will do",
        "role overview",
        "about the role",
        "impact",
    ),
    "required": (
        "required",
        "requirements",
        "minimum qualifications",
        "must have",
        "must-have",
        "core requirements",
        "qualifications",
    ),
    "preferred": (
        "preferred",
        "preferred qualifications",
        "nice to have",
        "nice-to-have",
        "bonus",
        "bonus points",
        "pluses",
    ),
}

DOCUMENT_SECTION_ORDER: Final[dict[str, tuple[str, ...]]] = {
    "resume": ("summary", "skills", "experience", "projects", "education"),
    "job_description": ("responsibilities", "required", "preferred", "education"),
}

SUPPORTED_INGESTION_EXTENSIONS: Final[dict[str, str]] = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
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
