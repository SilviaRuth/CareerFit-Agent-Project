"""Deterministic extraction with bounded diagnostics for Milestones 1 and 2A."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Generic, Iterable, TypeVar

from app.core.config import (
    CAPABILITY_PATTERNS,
    DOCUMENT_SECTION_ORDER,
    SECTION_HEADER_ALIASES,
    SECTION_HEADERS,
)
from app.schemas.common import (
    EducationItem,
    EvidenceSpan,
    ExperienceItem,
    ProjectItem,
    RequirementItem,
    SkillSignal,
)
from app.schemas.jd import JDSchema
from app.schemas.parse import ParserDiagnostic, UnsupportedSegment
from app.schemas.resume import ResumeSchema
from app.services.text_normalizer import normalize_text

SchemaT = TypeVar("SchemaT", ResumeSchema, JDSchema)

HEADER_LIKE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9 &'\/+-]{1,48}:?$")


@dataclass(slots=True)
class ExtractionResult(Generic[SchemaT]):
    """Structured extraction output used by the parse services."""

    schema: SchemaT
    warnings: list[ParserDiagnostic] = field(default_factory=list)
    unsupported_segments: list[UnsupportedSegment] = field(default_factory=list)


@dataclass(slots=True)
class SectionSplitResult:
    """Intermediate section split result with diagnostics."""

    intro_lines: list[str]
    sections: dict[str, str]
    warnings: list[ParserDiagnostic] = field(default_factory=list)
    unsupported_segments: list[UnsupportedSegment] = field(default_factory=list)


def extract_resume_schema(text: str) -> ResumeSchema:
    """Extract a constrained resume schema from deterministic or normalized text."""
    return analyze_resume_text(text).schema


def extract_jd_schema(text: str) -> JDSchema:
    """Extract a constrained JD schema from deterministic or normalized text."""
    return analyze_jd_text(text).schema


def analyze_resume_text(
    text: str, *, pre_normalized: bool = False
) -> ExtractionResult[ResumeSchema]:
    """Extract a resume schema and bounded extraction diagnostics."""
    normalized_text = text if pre_normalized else normalize_text(text, document_type="resume")
    all_lines = normalized_text.split("\n")
    non_empty_lines = [line for line in all_lines if line.strip()]
    warnings: list[ParserDiagnostic] = []

    candidate_name = non_empty_lines[0] if non_empty_lines else ""
    body_text = normalized_text.split("\n", 1)[1] if "\n" in normalized_text else ""
    section_result = _split_sections(body_text, DOCUMENT_SECTION_ORDER["resume"])
    warnings.extend(section_result.warnings)

    summary = section_result.sections.get("summary", "").strip()
    if not summary and section_result.intro_lines:
        summary = " ".join(line.strip() for line in section_result.intro_lines[:2]).strip()
        warnings.append(
            ParserDiagnostic(
                warning_code="summary_inferred_from_intro",
                message=(
                    "Summary section was missing; "
                    "summary text was inferred from leading content."
                ),
                section="summary",
                severity="warning",
                source="extraction",
            )
        )

    evidence_spans: list[EvidenceSpan] = []
    if summary:
        evidence_spans.append(
            _build_span(
                normalized_text,
                source_document="resume",
                section="summary",
                text=summary,
                normalized_value=None,
                explanation="Resume summary extracted deterministically.",
            )
        )

    skills = _extract_skills(
        section_result.sections.get("skills", ""),
        normalized_text,
        evidence_spans,
    )
    experience_items = _extract_experience_items(
        section_result.sections.get("experience", ""),
        normalized_text,
        evidence_spans,
    )
    project_items = _extract_project_items(
        section_result.sections.get("projects", ""),
        normalized_text,
        evidence_spans,
    )
    education_items = _extract_education_items(
        section_result.sections.get("education", ""),
        normalized_text,
        evidence_spans,
    )

    if not candidate_name:
        warnings.append(
            ParserDiagnostic(
                warning_code="missing_candidate_name",
                message="The parser could not identify a candidate name line.",
                section=None,
                severity="warning",
                source="extraction",
            )
        )

    warnings.extend(
        _missing_section_warnings(
            {
                "summary": summary,
                "skills": section_result.sections.get("skills", ""),
                "experience": section_result.sections.get("experience", ""),
                "projects": section_result.sections.get("projects", ""),
                "education": section_result.sections.get("education", ""),
            },
            required_sections=("summary", "skills", "experience"),
        )
    )

    schema = ResumeSchema(
        candidate_name=candidate_name,
        summary=summary,
        skills=skills,
        experience_items=experience_items,
        project_items=project_items,
        education_items=education_items,
        evidence_spans=evidence_spans,
        normalized_text=normalized_text,
        total_years_experience=_extract_total_years(summary, experience_items),
    )
    return ExtractionResult(
        schema=schema,
        warnings=_dedupe_diagnostics(warnings),
        unsupported_segments=section_result.unsupported_segments,
    )


def analyze_jd_text(text: str, *, pre_normalized: bool = False) -> ExtractionResult[JDSchema]:
    """Extract a JD schema and bounded extraction diagnostics."""
    normalized_text = (
        text if pre_normalized else normalize_text(text, document_type="job_description")
    )
    all_lines = normalized_text.split("\n")
    non_empty_lines = [line for line in all_lines if line.strip()]
    warnings: list[ParserDiagnostic] = []

    job_title = non_empty_lines[0] if non_empty_lines else ""
    company = non_empty_lines[1] if len(non_empty_lines) > 1 else ""
    body_text = _slice_after_n_non_empty_lines(normalized_text, 2)

    section_result = _split_sections(body_text, DOCUMENT_SECTION_ORDER["job_description"])
    warnings.extend(section_result.warnings)

    evidence_spans: list[EvidenceSpan] = []
    responsibility_lines = [line for line in section_result.intro_lines if line]
    explicit_responsibilities = [
        line
        for line in section_result.sections.get("responsibilities", "").split("\n")
        if line.strip()
    ]
    responsibilities = responsibility_lines + explicit_responsibilities
    for line in responsibilities:
        evidence_spans.append(
            _build_span(
                normalized_text,
                source_document="job_description",
                section="responsibilities",
                text=line,
                normalized_value=None,
                explanation="JD introductory responsibility text extracted deterministically.",
            )
        )

    required_requirements = _extract_requirements(
        section_result.sections.get("required", ""),
        priority="required",
        normalized_text=normalized_text,
        evidence_spans=evidence_spans,
    )
    preferred_requirements = _extract_requirements(
        section_result.sections.get("preferred", ""),
        priority="preferred",
        normalized_text=normalized_text,
        evidence_spans=evidence_spans,
    )
    education_requirements = _extract_requirements(
        section_result.sections.get("education", ""),
        priority="preferred",
        normalized_text=normalized_text,
        evidence_spans=evidence_spans,
        default_type="education",
    )

    if not job_title:
        warnings.append(
            ParserDiagnostic(
                warning_code="missing_job_title",
                message="The parser could not identify a job title line.",
                section=None,
                severity="warning",
                source="extraction",
            )
        )
    if not company:
        warnings.append(
            ParserDiagnostic(
                warning_code="missing_company_name",
                message="The parser could not identify a company line.",
                section=None,
                severity="warning",
                source="extraction",
            )
        )

    warnings.extend(
        _missing_section_warnings(
            {
                "responsibilities": section_result.sections.get("responsibilities", ""),
                "required": section_result.sections.get("required", ""),
                "preferred": section_result.sections.get("preferred", ""),
                "education": section_result.sections.get("education", ""),
            },
            required_sections=("required",),
        )
    )

    schema = JDSchema(
        job_title=job_title,
        company=company,
        required_requirements=required_requirements,
        preferred_requirements=preferred_requirements,
        responsibilities=responsibilities,
        education_requirements=education_requirements,
        seniority_hint=_infer_seniority_hint(job_title, required_requirements),
        domain_hint=_infer_domain_hint(normalized_text),
        evidence_spans=evidence_spans,
        normalized_text=normalized_text,
    )
    return ExtractionResult(
        schema=schema,
        warnings=_dedupe_diagnostics(warnings),
        unsupported_segments=section_result.unsupported_segments,
    )


def _split_sections(text: str, allowed_headers: Iterable[str]) -> SectionSplitResult:
    """Split a normalized document body into sections with alias support."""
    intro_lines: list[str] = []
    sections: dict[str, list[str]] = {}
    warnings: list[ParserDiagnostic] = []
    unsupported_segments: list[UnsupportedSegment] = []
    current_key: str | None = None
    unknown_header: str | None = None
    unknown_lines: list[str] = []
    alias_seen: set[tuple[str, str]] = set()

    for line in text.split("\n"):
        canonical_key = _canonical_section_key(line, allowed_headers)
        if canonical_key is not None:
            _flush_unknown_section(unknown_header, unknown_lines, unsupported_segments)
            unknown_header = None
            unknown_lines = []
            current_key = canonical_key
            sections.setdefault(current_key, [])

            normalized_line = _normalize_header_value(line)
            canonical_header = _normalize_header_value(SECTION_HEADERS[canonical_key])
            if normalized_line != canonical_header:
                alias_marker = (canonical_key, normalized_line)
                if alias_marker not in alias_seen:
                    alias_seen.add(alias_marker)
                    warnings.append(
                        ParserDiagnostic(
                            warning_code="section_header_alias_used",
                            message=(
                                f"Recognized section header variant '{line.strip()}' "
                                f"as '{SECTION_HEADERS[canonical_key]}'."
                            ),
                            section=canonical_key,
                            severity="info",
                            source="extraction",
                        )
                    )
            continue

        if _looks_like_header(line):
            _flush_unknown_section(unknown_header, unknown_lines, unsupported_segments)
            unknown_header = line.rstrip(":").strip()
            unknown_lines = []
            current_key = None
            warnings.append(
                ParserDiagnostic(
                    warning_code="unsupported_section_header",
                    message=(
                        f"Section header '{unknown_header}' "
                        "is not supported by the bounded parser."
                    ),
                    section=unknown_header.lower().replace(" ", "_") if unknown_header else None,
                    severity="warning",
                    source="extraction",
                )
            )
            continue

        if unknown_header is not None:
            unknown_lines.append(line)
            continue

        if current_key is None:
            if line:
                intro_lines.append(line)
            continue

        sections[current_key].append(line)

    _flush_unknown_section(unknown_header, unknown_lines, unsupported_segments)

    collapsed_sections = {key: "\n".join(value).strip() for key, value in sections.items()}
    return SectionSplitResult(
        intro_lines=intro_lines,
        sections=collapsed_sections,
        warnings=warnings,
        unsupported_segments=unsupported_segments,
    )


def _extract_skills(
    section_text: str,
    normalized_text: str,
    evidence_spans: list[EvidenceSpan],
) -> list[SkillSignal]:
    """Extract deterministic skill signals from the skills section."""
    if not section_text:
        return []

    skills: list[SkillSignal] = []
    for raw_skill in re.split(r",|\n", section_text):
        cleaned = raw_skill.strip().lstrip("- ").strip()
        if not cleaned:
            continue
        normalized_name = _normalize_capability(cleaned) or _slug(cleaned)
        span = _build_span(
            normalized_text,
            source_document="resume",
            section="skills",
            text=cleaned,
            normalized_value=normalized_name,
            explanation="Skill listed in resume skills section.",
        )
        evidence_spans.append(span)
        skills.append(
            SkillSignal(
                name=cleaned,
                normalized_name=normalized_name,
                evidence_strength="weak",
                evidence_spans=[span],
            )
        )
    return skills


def _extract_experience_items(
    section_text: str,
    normalized_text: str,
    evidence_spans: list[EvidenceSpan],
) -> list[ExperienceItem]:
    """Extract deterministic experience blocks separated by blank lines."""
    if not section_text:
        return []

    items: list[ExperienceItem] = []
    for block in _split_blocks(section_text):
        lines = [line for line in block.split("\n") if line]
        if not lines:
            continue
        heading = lines[0]
        details = [line.lstrip("- ").strip() for line in lines[1:]]
        summary = " ".join(details) if details else heading
        organization, start_year, end_year = _parse_role_heading(heading)
        span = _build_span(
            normalized_text,
            source_document="resume",
            section="experience",
            text=block,
            normalized_value=None,
            explanation="Experience block extracted deterministically.",
        )
        evidence_spans.append(span)
        items.append(
            ExperienceItem(
                heading=heading,
                organization=organization,
                summary=summary,
                start_year=start_year,
                end_year=end_year,
                evidence_spans=[span],
            )
        )
    return items


def _extract_project_items(
    section_text: str,
    normalized_text: str,
    evidence_spans: list[EvidenceSpan],
) -> list[ProjectItem]:
    """Extract deterministic project blocks."""
    if not section_text:
        return []

    items: list[ProjectItem] = []
    for block in _split_blocks(section_text):
        summary = block.replace("\n", " ").lstrip("- ").strip()
        if not summary:
            continue
        span = _build_span(
            normalized_text,
            source_document="resume",
            section="projects",
            text=block,
            normalized_value=None,
            explanation="Project block extracted deterministically.",
        )
        evidence_spans.append(span)
        items.append(ProjectItem(summary=summary, evidence_spans=[span]))
    return items


def _extract_education_items(
    section_text: str,
    normalized_text: str,
    evidence_spans: list[EvidenceSpan],
) -> list[EducationItem]:
    """Extract deterministic education blocks."""
    if not section_text:
        return []

    items: list[EducationItem] = []
    for block in _split_blocks(section_text):
        summary = block.replace("\n", " ").lstrip("- ").strip()
        if not summary:
            continue
        lower_summary = summary.lower()
        degree = "bachelor" if "b.s." in lower_summary or "bachelor" in lower_summary else None
        field = "computer science" if "computer science" in lower_summary else None
        span = _build_span(
            normalized_text,
            source_document="resume",
            section="education",
            text=block,
            normalized_value=field or degree,
            explanation="Education block extracted deterministically.",
        )
        evidence_spans.append(span)
        items.append(
            EducationItem(
                summary=summary,
                degree=degree,
                field=field,
                evidence_spans=[span],
            )
        )
    return items


def _extract_requirements(
    section_text: str,
    priority: str,
    normalized_text: str,
    evidence_spans: list[EvidenceSpan],
    default_type: str | None = None,
) -> list[RequirementItem]:
    """Extract normalized requirement items from JD bullets."""
    if not section_text:
        return []

    requirements: list[RequirementItem] = []
    for index, raw_line in enumerate(section_text.split("\n"), start=1):
        cleaned = raw_line.lstrip("- ").strip()
        if not cleaned:
            continue

        label = _derive_requirement_label(cleaned)
        normalized_label = _normalize_requirement(cleaned)
        requirement_type = default_type or _derive_requirement_type(cleaned)
        min_years = _extract_year_requirement(cleaned)
        span = _build_span(
            normalized_text,
            source_document="job_description",
            section=priority,
            text=cleaned,
            normalized_value=normalized_label,
            explanation=f"{priority.title()} requirement extracted deterministically.",
        )
        evidence_spans.append(span)
        requirements.append(
            RequirementItem(
                requirement_id=f"{priority}-{index}-{_slug(label)}",
                label=label,
                normalized_label=normalized_label,
                priority=priority,
                requirement_type=requirement_type,
                raw_text=cleaned,
                min_years=min_years,
                evidence_span=span,
            )
        )
    return requirements


def _split_blocks(section_text: str) -> list[str]:
    """Split a section into blocks separated by blank lines."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in section_text.split("\n"):
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return ["\n".join(block) for block in blocks]


def _parse_role_heading(heading: str) -> tuple[str | None, int | None, int | None]:
    """Extract organization and year range from a deterministic role heading."""
    parts = [part.strip() for part in heading.split(",")]
    organization = parts[1] if len(parts) >= 3 else None

    start_year = None
    end_year = None
    year_match = re.search(r"(?P<start>\d{4})\s*-\s*(?P<end>\d{4})", heading)
    if year_match:
        start_year = int(year_match.group("start"))
        end_year = int(year_match.group("end"))
    return organization, start_year, end_year


def _extract_total_years(summary: str, experience_items: list[ExperienceItem]) -> float | None:
    """Estimate total years of experience with deterministic rules."""
    summary_match = re.search(r"(\d+(?:\.\d+)?)\s+years?", summary.lower())
    if summary_match:
        return float(summary_match.group(1))

    total = 0.0
    for item in experience_items:
        if (
            item.start_year is not None
            and item.end_year is not None
            and item.end_year >= item.start_year
        ):
            total += item.end_year - item.start_year
    return total or None


def _derive_requirement_label(text: str) -> str:
    """Keep a human-readable label while normalizing common phrases."""
    lower_text = text.lower()
    years = _extract_year_requirement(text)
    if years is not None:
        return f"{int(years)}+ years experience"
    if "rest api design" in lower_text:
        return "rest api design"
    if "rest api development" in lower_text:
        return "rest api development"
    if "aws deployment" in lower_text:
        return "aws deployment"
    if "computer science" in lower_text and "degree" in lower_text:
        return "computer science degree"
    normalized_capability = _normalize_capability(lower_text)
    if normalized_capability is not None:
        return normalized_capability.replace("_", " ")
    return text.lower()


def _normalize_requirement(text: str) -> str:
    """Normalize a requirement into a matching capability key."""
    lower_text = text.lower()
    if _extract_year_requirement(text) is not None:
        return "years_experience"
    if "computer science" in lower_text and "degree" in lower_text:
        return "computer_science_degree"
    return _normalize_capability(lower_text) or _slug(lower_text)


def _normalize_capability(text: str) -> str | None:
    """Map raw text to a stable capability key."""
    lower_text = text.lower()
    best_match: tuple[int, int, str] | None = None

    for capability, patterns in CAPABILITY_PATTERNS.items():
        for pattern in patterns:
            start_index = lower_text.find(pattern)
            if start_index < 0:
                continue

            candidate = (len(pattern), -start_index, capability)
            if best_match is None or candidate > best_match:
                best_match = candidate

    return best_match[2] if best_match is not None else None


def _derive_requirement_type(text: str) -> str:
    """Classify a requirement into a deterministic type bucket."""
    lower_text = text.lower()
    if "healthcare" in lower_text or "logistics" in lower_text or "supply chain" in lower_text:
        return "domain"
    if any(
        skill_term in lower_text
        for skill_term in ("python", "fastapi", "pytest", "postgres", "docker", "aws", "api")
    ):
        return "skill"
    if _extract_year_requirement(text) is not None or "years" in lower_text:
        return "experience"
    if "degree" in lower_text or "education" in lower_text:
        return "education"
    if "experience" in lower_text:
        return "experience"
    return "skill"


def _extract_year_requirement(text: str) -> float | None:
    """Extract the minimum years requirement from a JD line."""
    match = re.search(r"(\d+(?:\.\d+)?)\+\s+years?", text.lower())
    if match:
        return float(match.group(1))
    return None


def _infer_seniority_hint(
    job_title: str,
    required_requirements: list[RequirementItem],
) -> str | None:
    """Infer a coarse seniority hint from title and experience requirements."""
    lower_title = job_title.lower()
    if "senior" in lower_title:
        return "senior"
    max_years = (
        max((item.min_years or 0.0) for item in required_requirements)
        if required_requirements
        else 0.0
    )
    if max_years >= 5:
        return "senior"
    if max_years >= 3:
        return "mid"
    if max_years > 0:
        return "junior"
    return None


def _infer_domain_hint(text: str) -> str | None:
    """Infer a single domain hint from the normalized JD text."""
    lower_text = text.lower()
    if "healthcare" in lower_text:
        return "healthcare"
    if "logistics" in lower_text or "supply chain" in lower_text or "fulfillment" in lower_text:
        return "logistics"
    if "cloud platform" in lower_text or "platform services" in lower_text:
        return "cloud_platform"
    return None


def _build_span(
    normalized_text: str,
    source_document: str,
    section: str,
    text: str,
    normalized_value: str | None,
    explanation: str,
) -> EvidenceSpan:
    """Build an evidence span with best-effort character offsets."""
    start_char = normalized_text.lower().find(text.lower())
    end_char = start_char + len(text) if start_char >= 0 else None
    return EvidenceSpan(
        source_document=source_document,
        section=section,
        text=text,
        start_char=start_char if start_char >= 0 else None,
        end_char=end_char,
        normalized_value=normalized_value,
        explanation=explanation,
    )


def _slug(text: str) -> str:
    """Create a simple deterministic slug."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _slice_after_n_non_empty_lines(text: str, count: int) -> str:
    """Return the substring after the first N non-empty lines."""
    seen = 0
    offset = 0
    for line in text.split("\n"):
        offset += len(line) + 1
        if line.strip():
            seen += 1
            if seen == count:
                return text[offset:]
    return ""


def _canonical_section_key(line: str, allowed_headers: Iterable[str]) -> str | None:
    """Map a header line to its canonical section key."""
    normalized_line = _normalize_header_value(line)
    for key in allowed_headers:
        aliases = {SECTION_HEADERS[key], *SECTION_HEADER_ALIASES.get(key, ())}
        if normalized_line in {_normalize_header_value(alias) for alias in aliases}:
            return key
    return None


def _normalize_header_value(value: str) -> str:
    """Normalize header labels for alias matching."""
    lowered = value.strip().rstrip(":").lower()
    lowered = lowered.replace("&", " and ").replace("/", " ")
    lowered = re.sub(r"[^a-z0-9 ]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _looks_like_header(line: str) -> bool:
    """Heuristic for unsupported header detection."""
    stripped = line.strip()
    return bool(stripped) and bool(HEADER_LIKE_PATTERN.fullmatch(stripped))


def _flush_unknown_section(
    unknown_header: str | None,
    unknown_lines: list[str],
    unsupported_segments: list[UnsupportedSegment],
) -> None:
    """Persist an unsupported section block when present."""
    if not unknown_header:
        return
    text = "\n".join(line for line in unknown_lines if line.strip()).strip()
    if not text:
        return
    unsupported_segments.append(
        UnsupportedSegment(
            text=text,
            section=unknown_header,
            reason="unsupported_section_header",
            source="extraction",
        )
    )


def _missing_section_warnings(
    sections: dict[str, str],
    required_sections: tuple[str, ...],
) -> list[ParserDiagnostic]:
    """Create warnings when expected sections are absent."""
    warnings: list[ParserDiagnostic] = []
    for section, value in sections.items():
        if value.strip():
            continue
        severity = "warning" if section in required_sections else "info"
        warnings.append(
            ParserDiagnostic(
                warning_code="missing_section",
                message=f"Expected section '{section}' was not found.",
                section=section,
                severity=severity,
                source="extraction",
            )
        )
    return warnings


def _dedupe_diagnostics(warnings: list[ParserDiagnostic]) -> list[ParserDiagnostic]:
    """Deduplicate diagnostics while preserving order."""
    seen: set[tuple[str, str | None, str, str]] = set()
    unique: list[ParserDiagnostic] = []
    for warning in warnings:
        key = (
            warning.warning_code,
            warning.section,
            warning.severity,
            warning.source,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(warning)
    return unique
