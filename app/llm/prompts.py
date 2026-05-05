"""Prompt builders that consume deterministic CareerFit artifacts only."""

from __future__ import annotations

import json

from app.schemas.llm_extraction import (
    MAX_EVIDENCE_REFS_PER_ITEM,
    MAX_EVIDENCE_TEXT_CHARS,
    MAX_JD_REQUIREMENTS,
    MAX_JD_RESPONSIBILITIES,
    MAX_RESUME_EXPERIENCE_ITEMS,
    MAX_RESUME_SKILLS,
)
from app.services.generation.context import GroundedFlowContext


def build_extraction_prompt(resume_text: str, job_description_text: str) -> str:
    """Build a bounded prompt for schema-only extraction from natural language."""
    payload = {
        "task": (
            "Extract resume and job-description facts as "
            "LLMNaturalLanguageExtractionOutput JSON."
        ),
        "rules": [
            "Extract only facts stated in the provided source text.",
            "Do not score, rank, recommend, infer missing qualifications, or improve wording.",
            "Every extracted skill, experience, project, education item, and requirement must "
            "include evidence_refs with text copied exactly from the source document.",
            f"Each evidence_refs text must be an exact short substring, not a full paragraph, "
            f"and must be at most {MAX_EVIDENCE_TEXT_CHARS} characters.",
            f"Use at most {MAX_EVIDENCE_REFS_PER_ITEM} evidence_refs per extracted item.",
            f"Limit resume skills to the strongest {MAX_RESUME_SKILLS} explicit skills and "
            f"experience_items to {MAX_RESUME_EXPERIENCE_ITEMS} entries.",
            f"Limit JD responsibilities to {MAX_JD_RESPONSIBILITIES} entries and each of "
            f"required_requirements and preferred_requirements to {MAX_JD_REQUIREMENTS} entries.",
            "Use source='resume' only for resume evidence and source='job_description' only "
            "for job-description evidence.",
            "If a value is missing, use an empty string, null, or an empty list instead of "
            "inventing it.",
            "For JD requirements, classify priority as required or preferred based only on the "
            "source text. If unclear but the text describes a must-have qualification, "
            "use required.",
        ],
        "resume_text": resume_text,
        "job_description_text": job_description_text,
        "output_schema": {
            "resume": {
                "candidate_name": "string",
                "summary": "string",
                "skills": [
                    {
                        "name": "string",
                        "evidence_refs": [
                            {
                                "source": "resume",
                                "field": "skills",
                                "text": "exact source text, 240 chars max",
                            }
                        ],
                    }
                ],
                "experience_items": [
                    {
                        "heading": "string",
                        "organization": "string|null",
                        "summary": "string",
                        "start_year": "integer|null",
                        "end_year": "integer|null",
                        "evidence_refs": [
                            {
                                "source": "resume",
                                "field": "experience",
                                "text": "exact source text, 240 chars max",
                            }
                        ],
                    }
                ],
                "project_items": [],
                "education_items": [],
                "total_years_experience": "number|null",
            },
            "job_description": {
                "job_title": "string",
                "company": "string",
                "responsibilities": ["string"],
                "required_requirements": [
                    {
                        "label": "string",
                        "raw_text": "string",
                        "priority": "required",
                        "requirement_type": "skill|experience|education|domain|seniority|other",
                        "min_years": "number|null",
                        "evidence_refs": [
                            {
                                "source": "job_description",
                                "field": "required",
                                "text": "exact source text, 240 chars max",
                            }
                        ],
                    }
                ],
                "preferred_requirements": [],
                "education_requirements": [],
                "seniority_hint": "string|null",
                "domain_hint": "string|null",
            },
        },
    }
    return json.dumps(payload, indent=2)


def build_advisory_prompt(context: GroundedFlowContext) -> str:
    """Build a bounded JSON prompt from parse, match, evidence, and gate outputs."""
    if context.gating is None:
        raise ValueError("LLM advisory prompts require populated gating metadata.")

    payload = {
        "task": "Return advisory career recommendations as LLMRecommendationOutput JSON.",
        "rules": [
            "Use only the deterministic evidence provided in this prompt.",
            "Every recommendation must include evidence_refs.",
            "Do not invent skills, seniority, companies, degrees, certifications, metrics, "
            "or project impact.",
            "Mark limitations instead of upgrading unsupported claims.",
        ],
        "match_result": {
            "overall_score": context.match_result.overall_score,
            "strengths": context.match_result.strengths,
            "gaps": [
                {
                    "requirement_id": gap.requirement_id,
                    "requirement_label": gap.requirement_label,
                    "gap_type": gap.gap_type,
                    "explanation": gap.explanation,
                }
                for gap in context.match_result.gaps
            ],
            "blocker_flags": context.match_result.blocker_flags.model_dump(mode="json"),
        },
        "generation_gate": context.gating.model_dump(mode="json"),
        "evidence": [
            {
                "source_document": span.source_document,
                "section": span.section,
                "field": span.normalized_value or span.section,
                "text": span.text,
                "explanation": span.explanation,
            }
            for span in context.evidence_registry[:40]
        ],
        "output_schema": {
            "summary": "string",
            "recommendations": [
                {
                    "category": "skills|experience|education|project|resume_wording",
                    "recommendation": "string",
                    "priority": "high|medium|low",
                    "evidence_refs": [
                        {
                            "source": "resume|job_description|match_result|generation_gate",
                            "field": "string",
                            "text": "must exactly match deterministic evidence text",
                        }
                    ],
                    "unsupported_claim_risk": "boolean",
                }
            ],
            "limitations": ["string"],
        },
    }
    return json.dumps(payload, indent=2)
