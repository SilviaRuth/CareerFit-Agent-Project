# API Walkthrough

This walkthrough uses synthetic sample data and the default deterministic
configuration.

## Start The Backend

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or with Docker:

```bash
docker run --rm --env-file .env.example -p 8000:8000 careerfit-agent
```

## Health Check

```bash
curl http://127.0.0.1:8000/health
```

Expected shape:

```json
{
  "status": "ok"
}
```

## Match A Resume To A Job Description

Request:

```bash
curl -s http://127.0.0.1:8000/match \
  -H "Content-Type: application/json" \
  --data @docs/examples/match_request.json
```

Key response fields:

- `overall_score`: weighted deterministic score
- `dimension_scores`: skills, experience, projects, domain fit, and education
- `required_matches`: required JD requirements with resume/JD evidence
- `preferred_matches`: preferred JD requirements with evidence
- `gaps`: missing or weak requirements
- `blocker_flags`: missing required skills, seniority mismatch, unsupported claims
- `evidence_summary`: reviewable evidence counts
- `adaptation_summary`: additive role/company emphasis metadata

The response is structured JSON only. It does not use a hidden LLM call.

## Parse Resume Or JD Text

```bash
curl -s http://127.0.0.1:8000/parse/resume \
  -H "Content-Type: application/json" \
  -d '{"text":"Alex Chen\n\nSummary\nBackend engineer...\n\nSkills\nPython, FastAPI"}'
```

```bash
curl -s http://127.0.0.1:8000/parse/jd \
  -H "Content-Type: application/json" \
  -d '{"text":"Senior Backend Engineer\n\nRequired\n- Python\n- REST APIs"}'
```

The parse responses include extracted schemas, confidence, warnings, normalized
text metadata, and unsupported segment diagnostics.

## Grounded Guidance Endpoints

The generation endpoints reuse the same resume/JD text fields as `/match`:

- `POST /rewrite`
- `POST /interview-prep`
- `POST /interview-sim`
- `POST /learning-plan`

They parse, match, gate, and render deterministic guidance from evidence. Their
outputs include warnings and gating metadata so low-confidence inputs remain
visible.

## Career Helper Endpoints

The current career helper surface includes:

- `POST /profile-memory`
- `POST /retrieve/evidence`
- `POST /semantic/match`
- `POST /compare/jobs`

These are request-scoped and additive. They do not persist a profile, rewrite
the deterministic score contract, or hide evidence.

## Optional LLM Advisory Endpoint

`POST /llm/advice` is disabled by default through `.env.example`.

When disabled, it still returns deterministic parse, match, evidence, and gate
artifacts with an LLM status that makes the fallback explicit. When enabled, LLM
output must pass strict schema and grounding validation before it appears under
`llm_advice`.

## OpenAPI Docs

With the backend running, inspect:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

Some multipart parse behavior is implemented through request parsing, so command
line examples remain the most reliable file-upload walkthrough.
