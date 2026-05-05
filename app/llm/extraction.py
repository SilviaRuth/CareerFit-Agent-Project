"""Optional LLM-assisted extraction for natural-language resume/JD inputs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from typing import Any, Iterable

from pydantic import ValidationError

from app.core.config import CAPABILITY_PATTERNS
from app.llm.base import LLMClient
from app.llm.config import LLMSettings, load_llm_settings
from app.llm.errors import LLMError
from app.llm.prompts import build_extraction_prompt
from app.llm.providers import build_llm_client
from app.schemas.common import (
    EducationItem,
    EvidenceSpan,
    ExperienceItem,
    ProjectItem,
    RequirementItem,
    SkillSignal,
)
from app.schemas.jd import JDSchema
from app.schemas.llm_extraction import (
    MAX_EVIDENCE_REFS_PER_ITEM,
    MAX_JD_EDUCATION_REQUIREMENTS,
    MAX_JD_REQUIREMENTS,
    MAX_JD_RESPONSIBILITIES,
    MAX_RESUME_EDUCATION_ITEMS,
    MAX_RESUME_EXPERIENCE_ITEMS,
    MAX_RESUME_PROJECT_ITEMS,
    MAX_RESUME_SKILLS,
    LLMExtractionEvidenceDiagnostic,
    LLMExtractionEvidenceRef,
    LLMExtractionReport,
    LLMJDExtractionOutput,
    LLMNaturalLanguageExtractionOutput,
    LLMResumeExtractionOutput,
)
from app.schemas.resume import ResumeSchema

MIN_EXTRACTION_MAX_OUTPUT_TOKENS = 12000
EVIDENCE_UNICODE_REPLACEMENTS = str.maketrans(
    {
        "\u00a0": " ",
        "\u2002": " ",
        "\u2003": " ",
        "\u2009": " ",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\u2023": "-",
        "\u2043": "-",
        "\u2219": "-",
        "\u25aa": "-",
        "\u25cf": "-",
        "\u25e6": "-",
        "\uff1a": ":",
    }
)


@dataclass(frozen=True, slots=True)
class LLMExtractionResult:
    """Resolved schemas plus an optional extraction status report."""

    resume_schema: ResumeSchema
    jd_schema: JDSchema
    report: LLMExtractionReport | None = None


@dataclass(frozen=True, slots=True)
class LLMExtractionValidationResult:
    """Validation errors plus optional debug diagnostics for LLM evidence refs."""

    errors: list[str]
    evidence_diagnostics: list[LLMExtractionEvidenceDiagnostic]


def maybe_run_llm_extraction(
    *,
    resume_text: str,
    job_description_text: str,
    deterministic_resume: ResumeSchema,
    deterministic_jd: JDSchema,
    settings: LLMSettings | None = None,
    client: LLMClient | None = None,
) -> LLMExtractionResult:
    """Use LLM extraction only when deterministic extraction clearly needs help."""
    resolved_settings = settings or load_llm_settings()
    resume_needs_help = _resume_needs_assistance(deterministic_resume)
    jd_needs_help = _jd_needs_assistance(deterministic_jd)

    if not resolved_settings.enable_llm_extraction:
        return LLMExtractionResult(
            resume_schema=deterministic_resume,
            jd_schema=deterministic_jd,
            report=None,
        )

    base_report = {
        "enabled": True,
        "provider": resolved_settings.provider,
        "model": resolved_settings.model,
        "used_for_resume": resume_needs_help,
        "used_for_job_description": jd_needs_help,
    }
    if not resume_needs_help and not jd_needs_help:
        return LLMExtractionResult(
            resume_schema=deterministic_resume,
            jd_schema=deterministic_jd,
            report=LLMExtractionReport(status="not_needed", **base_report),
        )

    try:
        extraction_settings = _settings_for_extraction(resolved_settings)
        resolved_client = client or build_llm_client(extraction_settings)
        raw_output = resolved_client.generate_json(
            build_extraction_prompt(resume_text, job_description_text),
            "LLMNaturalLanguageExtractionOutput",
        )
    except LLMError as exc:
        return LLMExtractionResult(
            resume_schema=deterministic_resume,
            jd_schema=deterministic_jd,
            report=LLMExtractionReport(
                status="fallback",
                errors=[str(exc)],
                warnings=["LLM extraction fell back to deterministic extraction."],
                **base_report,
            ),
        )

    parsed_output, parse_errors = _parse_output(raw_output)
    if parsed_output is None:
        return LLMExtractionResult(
            resume_schema=deterministic_resume,
            jd_schema=deterministic_jd,
            report=LLMExtractionReport(status="fallback", errors=parse_errors, **base_report),
        )

    validation = _validate_extraction_output(
        parsed_output,
        resume_text=resume_text,
        job_description_text=job_description_text,
        validate_resume=resume_needs_help,
        validate_jd=jd_needs_help,
        include_diagnostics=resolved_settings.enable_llm_extraction_debug,
    )
    if validation.errors:
        return LLMExtractionResult(
            resume_schema=deterministic_resume,
            jd_schema=deterministic_jd,
            report=LLMExtractionReport(
                status="rejected",
                errors=validation.errors,
                warnings=["LLM extraction was rejected; deterministic extraction was used."],
                evidence_diagnostics=validation.evidence_diagnostics,
                **base_report,
            ),
        )

    resume_schema = (
        _to_resume_schema(parsed_output.resume, resume_text)
        if resume_needs_help
        else deterministic_resume
    )
    jd_schema = (
        _to_jd_schema(parsed_output.job_description, job_description_text)
        if jd_needs_help
        else deterministic_jd
    )
    return LLMExtractionResult(
        resume_schema=resume_schema,
        jd_schema=jd_schema,
        report=LLMExtractionReport(
            status="validated",
            evidence_diagnostics=validation.evidence_diagnostics,
            **base_report,
        ),
    )


def disabled_extraction_report(settings: LLMSettings | None = None) -> LLMExtractionReport:
    """Build a disabled status report for explicit diagnostics."""
    resolved_settings = settings or load_llm_settings()
    return LLMExtractionReport(
        enabled=False,
        status="disabled",
        provider=resolved_settings.provider,
        model=resolved_settings.model,
    )


def _parse_output(
    raw_output: dict[str, Any] | str,
) -> tuple[LLMNaturalLanguageExtractionOutput | None, list[str]]:
    try:
        candidate = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
        candidate = _bound_extraction_candidate(candidate)
        return LLMNaturalLanguageExtractionOutput.model_validate(candidate), []
    except (json.JSONDecodeError, TypeError, ValidationError) as exc:
        errors = [f"schema_validation_failed: {exc}"]
        if isinstance(exc, json.JSONDecodeError) and (
            "Unterminated string" in exc.msg or "Expecting value" in exc.msg
        ):
            errors.append(
                "model_output_may_be_truncated: increase LLM_MAX_OUTPUT_TOKENS or shorten input"
            )
        return None, errors


def _bound_extraction_candidate(candidate: Any) -> Any:
    """Trim over-produced LLM lists before strict schema validation."""
    if not isinstance(candidate, dict):
        return candidate

    bounded = dict(candidate)
    resume = _copy_dict(bounded.get("resume"))
    if resume is not None:
        bounded["resume"] = resume
        _trim_list(resume, "skills", MAX_RESUME_SKILLS)
        _trim_list(resume, "experience_items", MAX_RESUME_EXPERIENCE_ITEMS)
        _trim_list(resume, "project_items", MAX_RESUME_PROJECT_ITEMS)
        _trim_list(resume, "education_items", MAX_RESUME_EDUCATION_ITEMS)
        for field in ("skills", "experience_items", "project_items", "education_items"):
            _trim_item_evidence_refs(resume.get(field))

    jd = _copy_dict(bounded.get("job_description"))
    if jd is not None:
        bounded["job_description"] = jd
        _trim_list(jd, "responsibilities", MAX_JD_RESPONSIBILITIES)
        _trim_list(jd, "required_requirements", MAX_JD_REQUIREMENTS)
        _trim_list(jd, "preferred_requirements", MAX_JD_REQUIREMENTS)
        _trim_list(jd, "education_requirements", MAX_JD_EDUCATION_REQUIREMENTS)
        for field in (
            "required_requirements",
            "preferred_requirements",
            "education_requirements",
        ):
            _trim_item_evidence_refs(jd.get(field))

    return bounded


def _copy_dict(value: Any) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, dict) else None


def _trim_list(container: dict[str, Any], field: str, max_items: int) -> None:
    value = container.get(field)
    if isinstance(value, list):
        container[field] = value[:max_items]


def _trim_item_evidence_refs(items: Any) -> None:
    if not isinstance(items, list):
        return
    for index, item in enumerate(items):
        copied = _copy_dict(item)
        if copied is None:
            continue
        _trim_list(copied, "evidence_refs", MAX_EVIDENCE_REFS_PER_ITEM)
        items[index] = copied


def _settings_for_extraction(settings: LLMSettings) -> LLMSettings:
    """Use a larger minimum token budget for structured extraction JSON."""
    if settings.max_output_tokens >= MIN_EXTRACTION_MAX_OUTPUT_TOKENS:
        return settings
    return replace(settings, max_output_tokens=MIN_EXTRACTION_MAX_OUTPUT_TOKENS)


def _resume_needs_assistance(schema: ResumeSchema) -> bool:
    return not (
        schema.candidate_name.strip()
        and schema.summary.strip()
        and schema.skills
        and schema.experience_items
        and schema.evidence_spans
    )


def _jd_needs_assistance(schema: JDSchema) -> bool:
    return not (
        schema.job_title.strip()
        and (schema.required_requirements or schema.preferred_requirements)
        and schema.evidence_spans
    )


def _validate_extraction_output(
    output: LLMNaturalLanguageExtractionOutput,
    *,
    resume_text: str,
    job_description_text: str,
    validate_resume: bool,
    validate_jd: bool,
    include_diagnostics: bool,
) -> LLMExtractionValidationResult:
    errors: list[str] = []
    diagnostics: list[LLMExtractionEvidenceDiagnostic] = []
    if validate_resume:
        if not output.resume.skills and not output.resume.experience_items:
            errors.append("resume_missing_supported_skills_or_experience")
        evidence_validation = _validate_evidence_refs(
            "resume",
            _resume_refs(output.resume),
            source_text=resume_text,
            expected_source="resume",
            include_diagnostics=include_diagnostics,
        )
        errors.extend(evidence_validation.errors)
        diagnostics.extend(evidence_validation.evidence_diagnostics)
    if validate_jd:
        requirements = (
            output.job_description.required_requirements
            + output.job_description.preferred_requirements
            + output.job_description.education_requirements
        )
        if not requirements:
            errors.append("job_description_missing_supported_requirements")
        evidence_validation = _validate_evidence_refs(
            "job_description",
            _jd_refs(output.job_description),
            source_text=job_description_text,
            expected_source="job_description",
            include_diagnostics=include_diagnostics,
        )
        errors.extend(evidence_validation.errors)
        diagnostics.extend(evidence_validation.evidence_diagnostics)
    return LLMExtractionValidationResult(errors=errors, evidence_diagnostics=diagnostics)


def _resume_refs(output: LLMResumeExtractionOutput) -> Iterable[LLMExtractionEvidenceRef]:
    for item in output.skills:
        yield from item.evidence_refs
    for item in output.experience_items:
        yield from item.evidence_refs
    for item in output.project_items:
        yield from item.evidence_refs
    for item in output.education_items:
        yield from item.evidence_refs


def _jd_refs(output: LLMJDExtractionOutput) -> Iterable[LLMExtractionEvidenceRef]:
    for item in (
        output.required_requirements
        + output.preferred_requirements
        + output.education_requirements
    ):
        yield from item.evidence_refs


def _validate_evidence_refs(
    prefix: str,
    refs: Iterable[LLMExtractionEvidenceRef],
    *,
    source_text: str,
    expected_source: str,
    include_diagnostics: bool,
) -> LLMExtractionValidationResult:
    errors: list[str] = []
    diagnostics: list[LLMExtractionEvidenceDiagnostic] = []
    for index, ref in enumerate(refs, start=1):
        if ref.source != expected_source:
            errors.append(f"{prefix}_evidence_ref_{index}_source_mismatch")
            if include_diagnostics:
                diagnostics.append(
                    _build_evidence_diagnostic(
                        ref,
                        ref_index=index,
                        match_mode="source_mismatch",
                    )
                )
            continue
        match_mode = _evidence_match_mode(ref.text, source_text)
        if match_mode == "unsupported":
            errors.append(f"{prefix}_evidence_ref_{index}_unsupported_text")
        if include_diagnostics:
            diagnostics.append(
                _build_evidence_diagnostic(ref, ref_index=index, match_mode=match_mode)
            )
    return LLMExtractionValidationResult(errors=errors, evidence_diagnostics=diagnostics)


def _evidence_text_is_supported(evidence_text: str, source_text: str) -> bool:
    return _evidence_match_mode(evidence_text, source_text) != "unsupported"


def _evidence_match_mode(evidence_text: str, source_text: str) -> str:
    cleaned = evidence_text.strip()
    if not cleaned:
        return "unsupported"
    if cleaned.casefold() in source_text.casefold():
        return "exact"

    normalized_evidence = _normalize_evidence_for_match(cleaned)
    normalized_source = _normalize_evidence_for_match(source_text)
    if normalized_evidence and normalized_evidence in normalized_source:
        return "normalized"

    compact_evidence = _compact_evidence_for_match(cleaned)
    compact_source = _compact_evidence_for_match(source_text)
    if len(compact_evidence) >= 8 and compact_evidence in compact_source:
        return "compact"
    return "unsupported"


def _build_evidence_diagnostic(
    ref: LLMExtractionEvidenceRef,
    *,
    ref_index: int,
    match_mode: str,
) -> LLMExtractionEvidenceDiagnostic:
    return LLMExtractionEvidenceDiagnostic(
        source=ref.source,
        ref_index=ref_index,
        field=ref.field,
        match_mode=match_mode,
        matched=match_mode in {"exact", "normalized", "compact"},
        llm_text=ref.text,
    )


def _normalize_evidence_for_match(text: str) -> str:
    translated = text.translate(EVIDENCE_UNICODE_REPLACEMENTS)
    translated = translated.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    translated = translated.replace("\r\n", "\n").replace("\r", "\n")
    translated = re.sub(r"(?m)^\s*[-*+]\s*", "", translated)
    return re.sub(r"\s+", " ", translated).strip().casefold()


def _compact_evidence_for_match(text: str) -> str:
    return re.sub(r"\s+", "", _normalize_evidence_for_match(text))


def _to_resume_schema(output: LLMResumeExtractionOutput, source_text: str) -> ResumeSchema:
    evidence_spans: list[EvidenceSpan] = []
    summary_span = _build_span(
        source_text,
        source_document="resume",
        section="summary",
        text=output.summary,
        normalized_value=None,
        explanation="Resume summary extracted by validated LLM extraction.",
    )
    if summary_span is not None:
        evidence_spans.append(summary_span)

    skills: list[SkillSignal] = []
    for item in output.skills:
        spans = _spans_from_refs(
            item.evidence_refs,
            source_text,
            explanation="Resume skill extracted by validated LLM extraction.",
        )
        normalized_name = _normalize_capability(_join_texts([item.name, *[s.text for s in spans]]))
        normalized_name = normalized_name or _slug(item.name)
        evidence_spans.extend(spans)
        skills.append(
            SkillSignal(
                name=item.name,
                normalized_name=normalized_name,
                evidence_strength="weak",
                evidence_spans=spans,
            )
        )

    experience_items: list[ExperienceItem] = []
    for item in output.experience_items:
        spans = _spans_from_refs(
            item.evidence_refs,
            source_text,
            explanation="Resume experience extracted by validated LLM extraction.",
        )
        evidence_spans.extend(spans)
        experience_items.append(
            ExperienceItem(
                heading=item.heading,
                organization=item.organization,
                summary=item.summary,
                start_year=item.start_year,
                end_year=item.end_year,
                evidence_spans=spans,
            )
        )

    project_items: list[ProjectItem] = []
    for item in output.project_items:
        spans = _spans_from_refs(
            item.evidence_refs,
            source_text,
            explanation="Resume project extracted by validated LLM extraction.",
        )
        evidence_spans.extend(spans)
        project_items.append(ProjectItem(summary=item.summary, evidence_spans=spans))

    education_items: list[EducationItem] = []
    for item in output.education_items:
        spans = _spans_from_refs(
            item.evidence_refs,
            source_text,
            explanation="Resume education extracted by validated LLM extraction.",
        )
        evidence_spans.extend(spans)
        education_items.append(
            EducationItem(
                summary=item.summary,
                degree=item.degree,
                field=item.field,
                evidence_spans=spans,
            )
        )

    return ResumeSchema(
        candidate_name=output.candidate_name,
        summary=output.summary,
        skills=skills,
        experience_items=experience_items,
        project_items=project_items,
        education_items=education_items,
        evidence_spans=_dedupe_spans(evidence_spans),
        normalized_text=source_text,
        total_years_experience=output.total_years_experience,
    )


def _to_jd_schema(output: LLMJDExtractionOutput, source_text: str) -> JDSchema:
    evidence_spans: list[EvidenceSpan] = []
    required = [
        _to_requirement(item, source_text, index=index, priority="required")
        for index, item in enumerate(output.required_requirements, start=1)
    ]
    preferred = [
        _to_requirement(item, source_text, index=index, priority="preferred")
        for index, item in enumerate(output.preferred_requirements, start=1)
    ]
    education = [
        _to_requirement(item, source_text, index=index, priority="preferred")
        for index, item in enumerate(output.education_requirements, start=1)
    ]
    for item in required + preferred + education:
        evidence_spans.append(item.evidence_span)

    return JDSchema(
        job_title=output.job_title,
        company=output.company,
        required_requirements=required,
        preferred_requirements=preferred,
        responsibilities=output.responsibilities,
        education_requirements=education,
        seniority_hint=output.seniority_hint,
        domain_hint=output.domain_hint,
        evidence_spans=_dedupe_spans(evidence_spans),
        normalized_text=source_text,
    )


def _to_requirement(
    item,
    source_text: str,
    *,
    index: int,
    priority: str,
) -> RequirementItem:
    span = _spans_from_refs(
        item.evidence_refs,
        source_text,
        explanation=f"{priority.title()} requirement extracted by validated LLM extraction.",
    )[0]
    raw_text = item.raw_text or item.label
    normalized_label = _normalize_requirement(raw_text, item.label, item.min_years)
    requirement_type = _normalize_requirement_type(
        item.requirement_type,
        normalized_label,
        raw_text,
    )
    return RequirementItem(
        requirement_id=f"{priority}-{index}-{_slug(item.label)}",
        label=item.label.lower(),
        normalized_label=normalized_label,
        priority=priority,
        requirement_type=requirement_type,
        raw_text=raw_text,
        min_years=item.min_years or _extract_year_requirement(raw_text),
        evidence_span=span,
    )


def _spans_from_refs(
    refs: list[LLMExtractionEvidenceRef],
    source_text: str,
    *,
    explanation: str,
) -> list[EvidenceSpan]:
    spans = [
        span
        for ref in refs
        if (
            span := _build_span(
                source_text,
                source_document=ref.source,
                section=ref.field,
                text=ref.text,
                normalized_value=None,
                explanation=explanation,
            )
        )
        is not None
    ]
    return _dedupe_spans(spans)


def _build_span(
    source_text: str,
    *,
    source_document: str,
    section: str,
    text: str,
    normalized_value: str | None,
    explanation: str,
) -> EvidenceSpan | None:
    cleaned = text.strip()
    if not cleaned:
        return None
    start_char = source_text.casefold().find(cleaned.casefold())
    return EvidenceSpan(
        source_document=source_document,
        section=section,
        text=cleaned,
        start_char=start_char if start_char >= 0 else None,
        end_char=start_char + len(cleaned) if start_char >= 0 else None,
        normalized_value=normalized_value,
        explanation=explanation,
    )


def _normalize_requirement(raw_text: str, label: str, min_years: float | None) -> str:
    if min_years is not None or _extract_year_requirement(raw_text) is not None:
        return "years_experience"
    lower_text = f"{raw_text} {label}".casefold()
    if "computer science" in lower_text and "degree" in lower_text:
        return "computer_science_degree"
    return _normalize_capability(lower_text) or _slug(label or raw_text)


def _normalize_requirement_type(requirement_type: str, normalized_label: str, raw_text: str) -> str:
    if normalized_label == "years_experience" or "years" in raw_text.casefold():
        return "experience"
    if normalized_label == "computer_science_degree":
        return "education"
    if requirement_type in {"skill", "experience", "education", "domain"}:
        return requirement_type
    return "skill"


def _normalize_capability(text: str) -> str | None:
    lower_text = text.casefold()
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


def _extract_year_requirement(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\+?\s+years?", text.casefold())
    return float(match.group(1)) if match else None


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.casefold()).strip("_")


def _join_texts(texts: Iterable[str]) -> str:
    return " ".join(text for text in texts if text)


def _dedupe_spans(spans: Iterable[EvidenceSpan]) -> list[EvidenceSpan]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[EvidenceSpan] = []
    for span in spans:
        key = (span.source_document, span.section, span.text.casefold())
        if key in seen:
            continue
        seen.add(key)
        unique.append(span)
    return unique
