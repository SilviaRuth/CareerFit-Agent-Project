# CareerFit Agent

Schema-first backend for explainable resume-to-JD parsing, matching, and grounded guidance.

## Current Scope

- Backend only
- Deterministic parsing, extraction, and rule-based matching
- Bounded file ingestion for `.txt`, `.pdf`, and `.docx`
- Evidence-linked JSON outputs
- Grounded rewrite and interview-prep guidance built on parse plus match results
- Single-orchestrator backend flow for grounded generation

## Milestone Status

- Milestone 1: deterministic `/match` flow
- Milestone 2: parsing and ingestion via `/parse/resume` and `/parse/jd`
- Milestone 3: grounded `/rewrite` and `/interview-prep` via a single orchestrator service

## Orchestration Pattern

Milestone 3 uses one deterministic orchestration layer in `app/services/orchestration_service.py`.

That layer coordinates:

- resume parsing
- JD parsing
- matching
- generation gating
- bounded rewrite or interview-prep rendering

Generation modules are callable services, not autonomous agents. They stay subordinate to parse responses, match results, evidence spans, warnings, and gating metadata.

## Local Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run The App

```powershell
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

The API exposes:

- `GET /health`
- `POST /match`
- `POST /parse/resume`
- `POST /parse/jd`
- `POST /rewrite`
- `POST /interview-prep`

## Parsing Docs

- Parsing and ingestion guide: [docs/PARSE_API.md](docs/PARSE_API.md)

The parsing guide covers:

- supported file types and bounded-ingestion behavior
- JSON text and multipart file examples
- parse response structure
- warning and parser-confidence semantics
- non-goals such as OCR and scanned-image parsing

## Run Tests

```powershell
.venv\Scripts\Activate.ps1
python -m pytest -q
```

## Inspect Fixtures

- Sample resumes and JDs: `data/samples/`
- Expected outcomes: `data/eval/`

These fixtures cover deterministic matching, messy parsing inputs, low-confidence parsing, and grounded generation flows.
