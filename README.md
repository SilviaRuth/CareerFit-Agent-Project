# CareerFit Agent

Schema-first backend for explainable resume-to-JD parsing, deterministic matching, grounded career guidance, multimodal ingestion diagnostics, additive workflow/document contracts, frontend-ready workflow traces, optional validated LLM advisory generation, and reviewable evaluation across Milestones 1 through 9.

## Current Scope

- Backend only
- Deterministic parsing, extraction, and rule-based matching
- Bounded file ingestion for `.txt`, `.pdf`, `.docx`, and explicit needs-OCR image/scanned-PDF diagnostics
- Evidence-linked JSON outputs
- Grounded rewrite and interview-prep guidance built on parse plus match results
- Grounded interview simulation aligned to responsibilities, strengths, and weak areas
- Grounded learning-plan guidance tied to explicit gaps, blockers, and supported strengths
- Single-orchestrator backend flow for grounded generation
- Request-scoped candidate profile memory with bounded evidence retrieval and additive semantic hints
- Optional `workflow_trace` metadata on selected match, comparison, retrieval, semantic, and ranking responses
- Optional LLM advisory generation under `/llm/advice`, disabled by default and stored separately as `llm_advice`
- Milestone 4 plus Milestone 5 evaluation coverage, multi-resume comparison, cross-JD comparison, adaptation summaries, and reviewable report snapshots

## Milestone Status

- Milestone 1: deterministic `/match` flow
- Milestone 2: parsing and ingestion via `/parse/resume` and `/parse/jd`
- Milestone 3: grounded `/rewrite` and `/interview-prep` via a single orchestrator service
- Milestone 4: expanded offline benchmark coverage, extraction evaluation, deterministic company/role adaptation summaries, multi-resume comparison, and reviewable report snapshots
- Milestone 5: grounded `/learning-plan`, `/interview-sim`, request-scoped `/profile-memory`, `/compare/jobs`, bounded `/retrieve/evidence`, additive `/semantic/match`, and recommendation evaluation
- Milestone 6 foundation: additive `WorkflowTrace`, `WorkflowStepTrace`, `WorkflowResult`, `DocumentInput`, `DocumentSegment`, and `NormalizedDocument` schemas without public endpoint behavior changes
- Milestone 7 foundation: scanned-PDF/image needs-OCR diagnostics, OCR adapter contracts, multimodal fixtures, and separate document-quality evaluation
- Milestone 8: frontend-ready workflow traces, stable step metadata, and documented dashboard view-model examples
- Milestone 9: optional schema-validated LLM advisory output with deterministic fallback and grounding validation

## Orchestration Pattern

Milestone 3 uses one deterministic orchestration layer in `app/services/orchestration_service.py`.

That layer coordinates:

- resume parsing
- JD parsing
- matching
- generation gating
- bounded rewrite or interview-prep rendering
- bounded interview-simulation rendering
- bounded learning-plan rendering

Generation modules are callable services, not autonomous agents. They stay subordinate to parse responses, match results, evidence spans, warnings, and gating metadata.

## Local Setup

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

On this machine, the most reliable command path is the repo venv interpreter:

```bash
./.venv/Scripts/python.exe -m pytest -q
```

## Run The App

```bash
uvicorn app.main:app --reload
```

The API exposes:

- `GET /health`
- `POST /match`
- `POST /parse/resume`
- `POST /parse/jd`
- `POST /rewrite`
- `POST /interview-prep`
- `POST /interview-sim`
- `POST /learning-plan`
- `POST /compare/resumes`
- `POST /profile-memory`
- `POST /compare/jobs`
- `POST /retrieve/evidence`
- `POST /semantic/match`
- `POST /llm/advice`

`/match` and `/compare/resumes` include an additive `adaptation_summary` so role/company emphasis is reviewable without changing the core scoring weights.

`/llm/advice` is advisory only. It first builds deterministic parse, match, evidence, and gating artifacts, then optionally asks an injected provider-neutral LLM client for JSON output. The default local configuration keeps this disabled:

```bash
ENABLE_LLM_GENERATION=false
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-mini
LLM_TEMPERATURE=0
LLM_MAX_OUTPUT_TOKENS=800
```

Missing API keys or invalid model output produce deterministic results plus `llm_status: "fallback"` or `llm_status: "rejected"` instead of breaking the request.

## Parsing Docs

- Parsing and ingestion guide: [docs/PARSE_API.md](docs/PARSE_API.md)
- Generation guide: [docs/GENERATION_API.md](docs/GENERATION_API.md)
- Evaluation guide: [docs/EVALUATION.md](docs/EVALUATION.md)
- Comparison guide: [docs/COMPARISON_API.md](docs/COMPARISON_API.md)
- Career workflow guide: [docs/CAREER_API.md](docs/CAREER_API.md)
- Frontend view-model guide: [docs/api/frontend_view_models.md](docs/api/frontend_view_models.md)

The parsing guide covers:

- supported file types and bounded-ingestion behavior
- JSON text and multipart file examples
- parse response structure
- warning and parser-confidence semantics
- non-goals such as OCR and scanned-image parsing

## Run Tests

```bash
./.venv/Scripts/python.exe -m pytest -q
```

## Run Lint

```bash
./.venv/Scripts/python.exe -m ruff check app tests
```

## Docker

Build and run the FastAPI backend image:

```bash
docker build -t careerfit-agent .
docker run --rm -p 8000:8000 careerfit-agent
```

This image runs the current backend only. It does not add OCR, LLM, vector-store, or frontend dependencies.

## Inspect Fixtures

- Sample resumes and JDs: `data/samples/`
- Expected outcomes: `data/eval/`

These fixtures cover deterministic matching, messy parsing inputs, low-confidence parsing, grounded generation flows, and representative multi-resume ranking scenarios.

## Run Offline Evaluation

```bash
./.venv/Scripts/python.exe -m app.evaluation.benchmark_runner
./.venv/Scripts/python.exe -m app.evaluation.extraction_runner
./.venv/Scripts/python.exe -m app.evaluation.comparison_runner
./.venv/Scripts/python.exe -m app.evaluation.recommendation_runner
./.venv/Scripts/python.exe -m app.evaluation.artifact_writer
./.venv/Scripts/python.exe -m app.evaluation.artifact_writer --snapshot-label m5-review
```

The evaluation runners use:

- `data/eval/benchmark_manifest.json`
- `data/eval/extraction_manifest.json`
- `data/eval/comparison_manifest.json`
- `data/eval/recommendation_manifest.json`

The artifact writer refreshes the checked-in baseline reports under `data/eval/reports/baseline/` and can write comparable snapshot reports under `data/eval/reports/snapshots/`, now including `recommendation_report.json`.
