"""Unit tests for optional LLM-assisted natural-language extraction."""

from __future__ import annotations

from app.llm.config import LLMSettings
from app.llm.extraction import _parse_output, maybe_run_llm_extraction
from app.llm.providers import FakeLLMClient
from app.services.extraction_service import extract_jd_schema, extract_resume_schema
from app.services.matching_service import match_resume_to_jd
from tests.conftest import load_sample


def test_match_uses_validated_llm_extraction_for_natural_language_inputs() -> None:
    resume_text = (
        "Alex Chen is a backend engineer with 6 years of experience. "
        "He built Python FastAPI services and designed REST APIs for healthcare workflows."
    )
    jd_text = (
        "CareBridge is hiring a Senior Backend Engineer. The role requires Python, "
        "FastAPI, REST API design, and 4+ years of backend experience. Preferred: "
        "healthcare workflow experience."
    )
    fake_client = FakeLLMClient(_valid_extraction_output())

    result = match_resume_to_jd(
        resume_text,
        jd_text,
        llm_settings=LLMSettings(enable_llm_extraction=True, provider="fake"),
        llm_client=fake_client,
    )
    matched_required = {
        match.requirement_label for match in result.required_matches if match.status == "matched"
    }

    assert result.llm_extraction is not None
    assert result.llm_extraction.status == "validated"
    assert result.llm_extraction.used_for_resume is True
    assert result.llm_extraction.used_for_job_description is True
    assert fake_client.calls[0][1] == "LLMNaturalLanguageExtractionOutput"
    assert {"python", "fastapi", "rest api design", "4+ years experience"}.issubset(
        matched_required
    )
    assert result.evidence_summary.total_evidence_spans > 0
    assert result.workflow_trace is not None
    assert any(
        step.step_name == "llm_extract_natural_language"
        and step.metadata["status"] == "validated"
        for step in result.workflow_trace.steps
    )


def test_llm_extraction_rejects_unsupported_evidence_and_falls_back() -> None:
    fake_output = _valid_extraction_output()
    fake_output["job_description"]["required_requirements"][0]["evidence_refs"][0][
        "text"
    ] = "This requirement text is not in the source document."
    fake_client = FakeLLMClient(fake_output)

    result = match_resume_to_jd(
        "Alex Chen is a backend engineer with 6 years of experience.",
        "The role requires Python and FastAPI.",
        llm_settings=LLMSettings(
            enable_llm_extraction=True,
            enable_llm_extraction_debug=True,
            provider="fake",
        ),
        llm_client=fake_client,
    )

    assert result.llm_extraction is not None
    assert result.llm_extraction.status == "rejected"
    assert "job_description_evidence_ref_1_unsupported_text" in result.llm_extraction.errors
    assert any(
        diagnostic.match_mode == "unsupported" and diagnostic.matched is False
        for diagnostic in result.llm_extraction.evidence_diagnostics
    )
    assert result.required_matches == []


def test_llm_extraction_accepts_grounded_evidence_with_normalized_spacing() -> None:
    fake_output = _valid_extraction_output()
    supported_jd_evidence = (
        "Python, FastAPI, REST API design, and 4+ years of backend experience"
    )
    for requirement in fake_output["job_description"]["required_requirements"]:
        requirement["evidence_refs"][0]["text"] = supported_jd_evidence

    result = match_resume_to_jd(
        (
            "Alex Chen is a backend engineer with 6 years of experience. "
            "He built\nPython FastAPI services and designed REST APIs for healthcare workflows."
        ),
        (
            "CareBridge is hiring a Senior Backend Engineer.\n"
            "The role requires:\n"
            "- Python, FastAPI, REST API design, and 4+ years of backend experience.\n"
            "Preferred: healthcare workflow experience."
        ),
        llm_settings=LLMSettings(
            enable_llm_extraction=True,
            enable_llm_extraction_debug=True,
            provider="fake",
        ),
        llm_client=FakeLLMClient(fake_output),
    )

    assert result.llm_extraction is not None
    assert result.llm_extraction.status == "validated"
    assert any(
        diagnostic.match_mode == "normalized" and diagnostic.matched is True
        for diagnostic in result.llm_extraction.evidence_diagnostics
    )


def test_llm_extraction_omits_evidence_diagnostics_by_default() -> None:
    result = match_resume_to_jd(
        (
            "Alex Chen is a backend engineer with 6 years of experience. "
            "He built Python FastAPI services and designed REST APIs for healthcare workflows."
        ),
        (
            "CareBridge is hiring a Senior Backend Engineer. The role requires Python, "
            "FastAPI, REST API design, and 4+ years of backend experience."
        ),
        llm_settings=LLMSettings(enable_llm_extraction=True, provider="fake"),
        llm_client=FakeLLMClient(_valid_extraction_output()),
    )

    assert result.llm_extraction is not None
    assert result.llm_extraction.status == "validated"
    assert result.llm_extraction.evidence_diagnostics == []


def test_llm_extraction_is_not_called_when_deterministic_extraction_is_sufficient() -> None:
    fake_client = FakeLLMClient(_valid_extraction_output())

    result = match_resume_to_jd(
        load_sample("strong_fit_resume.txt"),
        load_sample("strong_fit_jd.txt"),
        llm_settings=LLMSettings(enable_llm_extraction=True, provider="fake"),
        llm_client=fake_client,
    )

    assert result.llm_extraction is not None
    assert result.llm_extraction.status == "not_needed"
    assert fake_client.calls == []
    assert result.overall_score == 89


def test_llm_extraction_uses_larger_token_budget_for_provider_client(monkeypatch) -> None:
    captured: dict[str, int] = {}

    def fake_build_client(settings: LLMSettings) -> FakeLLMClient:
        captured["max_output_tokens"] = settings.max_output_tokens
        return FakeLLMClient(_valid_extraction_output())

    monkeypatch.setattr("app.llm.extraction.build_llm_client", fake_build_client)
    resume_text = "Alex Chen is a backend engineer with 6 years of experience."
    jd_text = "The role requires Python and FastAPI."

    result = maybe_run_llm_extraction(
        resume_text=resume_text,
        job_description_text=jd_text,
        deterministic_resume=extract_resume_schema(resume_text),
        deterministic_jd=extract_jd_schema(jd_text),
        settings=LLMSettings(enable_llm_extraction=True, provider="openai", api_key="test-key"),
    )

    assert captured["max_output_tokens"] == 12000
    assert result.report is not None
    assert result.report.status in {"validated", "rejected"}


def test_llm_extraction_parse_error_flags_likely_truncation() -> None:
    parsed, errors = _parse_output('{"resume":{"candidate_name":"Alex')

    assert parsed is None
    assert any("schema_validation_failed" in error for error in errors)
    assert (
        "model_output_may_be_truncated: increase LLM_MAX_OUTPUT_TOKENS or shorten input"
        in errors
    )


def test_llm_extraction_accepts_up_to_twenty_project_items() -> None:
    output = _valid_extraction_output()
    output["resume"]["project_items"] = [
        {
            "summary": f"Project {index}",
            "evidence_refs": [
                {
                    "source": "resume",
                    "field": "projects",
                    "text": "built Python FastAPI services and designed REST APIs",
                }
            ],
        }
        for index in range(1, 7)
    ]

    parsed, errors = _parse_output(output)

    assert errors == []
    assert parsed is not None
    assert len(parsed.resume.project_items) == 6


def test_llm_extraction_bounds_overproduced_lists_before_schema_validation() -> None:
    output = _valid_extraction_output()
    output["resume"]["project_items"] = [
        {
            "summary": f"Project {index}",
            "evidence_refs": [
                {
                    "source": "resume",
                    "field": "projects",
                    "text": "built Python FastAPI services and designed REST APIs",
                }
            ],
        }
        for index in range(1, 26)
    ]
    output["job_description"]["required_requirements"] = [
        {
            "label": f"Requirement {index}",
            "raw_text": "requires Python",
            "priority": "required",
            "requirement_type": "skill",
            "min_years": None,
            "evidence_refs": [
                {
                    "source": "job_description",
                    "field": "required",
                    "text": "requires Python",
                }
            ],
        }
        for index in range(1, 26)
    ]

    parsed, errors = _parse_output(output)

    assert errors == []
    assert parsed is not None
    assert len(parsed.resume.project_items) == 20
    assert len(parsed.job_description.required_requirements) == 20


def test_llm_extraction_bounds_overproduced_evidence_refs() -> None:
    output = _valid_extraction_output()
    output["resume"]["skills"][0]["evidence_refs"] = [
        {
            "source": "resume",
            "field": "skills",
            "text": "built Python FastAPI services and designed REST APIs",
        },
        {
            "source": "resume",
            "field": "skills",
            "text": "built Python FastAPI services and designed REST APIs",
        },
        {
            "source": "resume",
            "field": "skills",
            "text": "built Python FastAPI services and designed REST APIs",
        },
    ]

    parsed, errors = _parse_output(output)

    assert errors == []
    assert parsed is not None
    assert len(parsed.resume.skills[0].evidence_refs) == 2


def _valid_extraction_output() -> dict:
    return {
        "resume": {
            "candidate_name": "Alex Chen",
            "summary": "Alex Chen is a backend engineer with 6 years of experience.",
            "skills": [
                {
                    "name": "Python",
                    "evidence_refs": [
                        {
                            "source": "resume",
                            "field": "skills",
                            "text": "built Python FastAPI services and designed REST APIs",
                        }
                    ],
                },
                {
                    "name": "FastAPI",
                    "evidence_refs": [
                        {
                            "source": "resume",
                            "field": "skills",
                            "text": "built Python FastAPI services and designed REST APIs",
                        }
                    ],
                },
            ],
            "experience_items": [
                {
                    "heading": "Backend engineer",
                    "organization": None,
                    "summary": "built Python FastAPI services and designed REST APIs",
                    "start_year": None,
                    "end_year": None,
                    "evidence_refs": [
                        {
                            "source": "resume",
                            "field": "experience",
                            "text": "built Python FastAPI services and designed REST APIs",
                        }
                    ],
                }
            ],
            "project_items": [],
            "education_items": [],
            "total_years_experience": 6.0,
        },
        "job_description": {
            "job_title": "Senior Backend Engineer",
            "company": "CareBridge",
            "responsibilities": ["Build backend services for healthcare workflows."],
            "required_requirements": [
                {
                    "label": "Python",
                    "raw_text": "requires Python",
                    "priority": "required",
                    "requirement_type": "skill",
                    "min_years": None,
                    "evidence_refs": [
                        {
                            "source": "job_description",
                            "field": "required",
                            "text": (
                                "requires Python, FastAPI, REST API design, and 4+ years "
                                "of backend experience"
                            ),
                        }
                    ],
                },
                {
                    "label": "FastAPI",
                    "raw_text": "requires FastAPI",
                    "priority": "required",
                    "requirement_type": "skill",
                    "min_years": None,
                    "evidence_refs": [
                        {
                            "source": "job_description",
                            "field": "required",
                            "text": (
                                "requires Python, FastAPI, REST API design, and 4+ years "
                                "of backend experience"
                            ),
                        }
                    ],
                },
                {
                    "label": "REST API design",
                    "raw_text": "REST API design",
                    "priority": "required",
                    "requirement_type": "skill",
                    "min_years": None,
                    "evidence_refs": [
                        {
                            "source": "job_description",
                            "field": "required",
                            "text": (
                                "requires Python, FastAPI, REST API design, and 4+ years "
                                "of backend experience"
                            ),
                        }
                    ],
                },
                {
                    "label": "4+ years experience",
                    "raw_text": "4+ years of backend experience",
                    "priority": "required",
                    "requirement_type": "experience",
                    "min_years": 4.0,
                    "evidence_refs": [
                        {
                            "source": "job_description",
                            "field": "required",
                            "text": (
                                "requires Python, FastAPI, REST API design, and 4+ years "
                                "of backend experience"
                            ),
                        }
                    ],
                },
            ],
            "preferred_requirements": [],
            "education_requirements": [],
            "seniority_hint": "senior",
            "domain_hint": "healthcare",
        },
    }
