# M9: Validated Advisory Generation

## Goal

Introduce optional LLM-assisted generation behind strict schemas, evidence grounding, and validation gates while preserving deterministic parsing, matching, scoring, and blocker logic.

## Allowed Scope

- Add provider-neutral LLM adapter interfaces.
- Add prompt/input builders that consume deterministic parse, match, evidence, and gate outputs.
- Validate model outputs against Pydantic schemas.
- Add unsupported-claim, hallucination, and evidence-coverage checks.
- Add opt-in configuration so local deterministic workflows can still run without model access.
- Expand recommendation evaluation for LLM-assisted outputs.

### M9.1 — Provider-neutral LLM interface

Codex should create something like:

```text
app/llm/
  __init__.py
  base.py
  providers.py
  config.py
  errors.py
```

Core interface:

```python
class LLMClient(Protocol):
    def generate_json(self, prompt: str, schema_name: str) -> dict:
        ...
```

Important: this layer should not know about resume/JD business logic. It only handles provider abstraction, timeout, errors, and raw response.

### M9.2 — Generation schemas

Add strict Pydantic schemas for LLM outputs.

Possible schemas:

```text
app/schemas/llm_generation.py
```

Examples:

```python
class EvidenceRef(BaseModel):
    source: Literal["resume", "job_description", "match_result"]
    field: str
    text: str

class RecommendationItem(BaseModel):
    category: Literal["skills", "experience", "education", "project", "resume_wording"]
    recommendation: str
    priority: Literal["high", "medium", "low"]
    evidence_refs: list[EvidenceRef]
    unsupported_claim_risk: bool = False

class LLMRecommendationOutput(BaseModel):
    summary: str
    recommendations: list[RecommendationItem]
    limitations: list[str]
```

This prevents the model from returning vague free text.

### M9.3 — Grounding validator

This is the most important part.

You need a deterministic validation layer after the LLM response:

```text
app/llm/validators.py
```

Checks should include:

```text
1. Every recommendation must cite evidence_refs.
2. Every evidence_ref text must exist in deterministic inputs or outputs.
3. No new skill, company, degree, seniority, metric, certification, or experience may be introduced unless present in evidence.
4. Unsupported claims are either blocked or marked as limitations.
5. If coverage is too low, reject the LLM output and return deterministic-only fallback.
```


### M9.4 — Opt-in orchestration

The generation path should be explicitly enabled:

```env
ENABLE_LLM_GENERATION=false
ENABLE_LLM_EXTRACTION=false
LLM_EXTRACTION_DEBUG=false
LLM_PROVIDER=openai
LLM_MODEL=...
```

Default behavior:

```text
No API key + ENABLE_LLM_GENERATION=false = deterministic workflow still passes.
No API key + ENABLE_LLM_GENERATION=true = clean warning/fallback, not crash.
```

This directly matches your invariant that missing model access must not break local deterministic tests. 

## Out Of Scope

- Replacing deterministic extraction or matching with prompt-only behavior.
- Hidden model calls in default tests.
- Unsupported resume claims, invented metrics, or invented seniority.
- Autonomous tool loops without trace and review gates.
- Vector-store or persistent memory expansion unless explicitly scoped.

## Non-Negotiable Design Rules

- LLM generation must never modify parse_result, match_result, score_result, blocker_result, or benchmark_result.
- LLM generation may only create advisory fields under a separate key, e.g. `llm_advice`.
- All LLM outputs must pass schema validation before being returned.
- All LLM outputs must pass grounding validation before being shown as trusted advice.
- If validation fails, the system must return deterministic results plus a clear `llm_status: "rejected"` or `llm_status: "fallback"` field.
- Unit tests must use mock/fake LLM clients only.

## Required Invariants

- Deterministic parser, matcher, blocker flags, evidence spans, and benchmark reports remain the source of truth.
- LLM output must be advisory and grounded in available evidence.
- A missing model key or disabled model path must not break deterministic local tests.

## Completion Signal

- LLM-assisted generation is optional, schema-validated, and auditable.
- Grounding and hallucination checks are part of automated verification.
- Existing deterministic outputs remain available.

## Implemented Surface

- LLM adapter contracts live under `app/llm/`.
- Strict advisory schemas live in `app/schemas/llm_generation.py`.
- Strict extraction schemas live in `app/schemas/llm_extraction.py`.
- The public advisory endpoint is `POST /llm/advice`.
- Default behavior keeps `ENABLE_LLM_GENERATION=false` and `ENABLE_LLM_EXTRACTION=false`, so local deterministic workflows and tests do not require model access.
- Unit tests use `FakeLLMClient` and do not call external APIs.
- Grounding validation checks both cited evidence text and cited source provenance.
- Unsupported claims in summary or recommendation text are rejected even when `unsupported_claim_risk=true`; unsupported or missing claims may only appear as limitations.

The endpoint returns deterministic source-of-truth artifacts separately from optional model advice:

```json
{
  "deterministic_result": {
    "resume_parse": {},
    "jd_parse": {},
    "match_result": {},
    "gating": {}
  },
  "llm_status": "validated",
  "llm_advice": {
    "enabled": true,
    "status": "validated",
    "provider": "fake",
    "model": "gpt-5.4-mini",
    "summary": "Advisory text grounded in deterministic evidence.",
    "recommendations": [],
    "limitations": [],
    "warnings": []
  },
  "validation_report": {
    "schema_valid": true,
    "grounding_valid": true,
    "unsupported_claims": [],
    "evidence_coverage": 1.0,
    "errors": []
  }
}
```

Known limitations:

- The default app does not make hidden external calls. The built-in `openai` adapter is only used when an explicit LLM feature flag is enabled and credentials are configured.
- Grounding validation is deterministic and conservative; unsupported recommendation claims, missing evidence, or wrong-source citations cause fallback/rejection instead of partial trust.
- LLM extraction may provide validated schemas for natural-language inputs, but the deterministic matcher still owns scoring, blocker flags, evidence summaries, and benchmark behavior.

## output contract:

```json
{
  "deterministic_result": {},
  "llm_advice": {
    "enabled": true,
    "status": "validated",
    "summary": "...",
    "recommendations": []
  },
  "validation_report": {
    "schema_valid": true,
    "grounding_valid": true,
    "unsupported_claims": [],
    "evidence_coverage": 1.0
  }
}
```

## Model Selection Policy

M9 does not hard-code a specific LLM model.

The system must support provider/model selection through environment configuration:

- `ENABLE_LLM_GENERATION`
- `ENABLE_LLM_EXTRACTION`
- `LLM_EXTRACTION_DEBUG`
- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_TEMPERATURE`
- `LLM_MAX_OUTPUT_TOKENS`

Recommended default for development:

- Provider: `openai`
- Model: `gpt-5.4-mini`
- Temperature: `0`

The implementation must also include a `FakeLLMClient` for tests so CI and deterministic workflows do not require external API access.
