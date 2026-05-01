"""Prompt builders that consume deterministic CareerFit artifacts only."""

from __future__ import annotations

import json

from app.services.generation.context import GroundedFlowContext


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

