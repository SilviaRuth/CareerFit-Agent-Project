# CareerFit Agent

CareerFit Agent is a schema-first FastAPI backend for explainable resume-to-job
description analysis. It parses resumes and JDs into explicit Pydantic schemas,
runs deterministic matching with evidence spans and blocker flags, and returns
grounded career guidance that can be reviewed through tests and benchmark
artifacts.

This release packages the project as a portfolio-ready backend. An external
reviewer can install it, run it locally or in Docker, send a synthetic matching
request, inspect the JSON output, and review the checked-in evaluation reports
without private context.

## What It Demonstrates

- deterministic resume/JD parsing and rule-based matching
- evidence-linked strengths, gaps, blockers, and explanations
- bounded `.txt`, `.pdf`, and `.docx` ingestion
- explicit needs-OCR diagnostics for images and scanned PDFs
- grounded rewrite, interview-prep, interview-simulation, and learning-plan outputs
- request-scoped profile memory, evidence retrieval, semantic hints, and cross-JD ranking
- optional `/llm/advice` output that is disabled by default and kept separate as `llm_advice`
- workflow traces on selected responses for frontend-ready diagnostics
- offline benchmark reports for regression review

## Architecture

The backend follows a thin-route, service-oriented shape:

- `app/api/routes/`: FastAPI transport layer
- `app/schemas/`: explicit request/response contracts
- `app/services/ingestion/`: bounded file and document ingestion
- `app/services/extraction_service.py`: deterministic schema extraction
- `app/services/matching_service.py`: scoring, blockers, gaps, and evidence
- `app/services/orchestration_service.py`: single deterministic orchestration for grounded guidance
- `app/llm/`: optional advisory LLM boundary with schema and grounding validation
- `app/evaluation/`: benchmark runners and artifact writer

The deterministic parser, matcher, blocker flags, evidence model, and benchmark
reports remain the source of truth. The project does not implement autonomous
agents, hidden external LLM calls, vector stores, persistent profile storage, or
OCR runtime support.

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Install

Use Python 3.11.

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements-dev.txt
```

Runtime-only dependencies are in `requirements.txt`. Development and test
dependencies are in `requirements-dev.txt` and the `.[dev]` package extra.

## Configuration

The deterministic backend does not require secrets.

```bash
cp .env.example .env
```

Default local behavior keeps optional LLM advisory generation disabled:

```bash
ENABLE_LLM_GENERATION=false
```

Only set `OPENAI_API_KEY` or `LLM_API_KEY` in a private environment when
intentionally testing `/llm/advice`.

## Run Locally

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify the backend:

```bash
curl http://127.0.0.1:8000/health
```

Interactive OpenAPI docs are available at:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

## Run With Docker

```bash
docker build -t careerfit-agent .
docker run --rm --env-file .env.example -p 8000:8000 careerfit-agent
```

Or:

```bash
docker compose up --build
```

The image runs the current backend only. It does not install OCR, frontend,
database, vector-store, or provider SDK dependencies.

## Run Checks

```bash
./.venv/Scripts/python.exe -m ruff check app tests
./.venv/Scripts/python.exe -m pytest -q
```

CI runs Ruff, pytest, and a Docker image build through
[.github/workflows/ci.yml](.github/workflows/ci.yml).

## API Walkthrough

With the backend running, send the synthetic matching request:

```bash
curl -s http://127.0.0.1:8000/match \
  -H "Content-Type: application/json" \
  --data @docs/examples/match_request.json
```

Inspect these response fields:

- `overall_score`
- `dimension_scores`
- `required_matches`
- `preferred_matches`
- `gaps`
- `blocker_flags`
- `evidence_spans`
- `evidence_summary`
- `adaptation_summary`

Current public endpoints:

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
- `POST /retrieve/evidence`
- `POST /semantic/match`
- `POST /compare/jobs`
- `POST /llm/advice`

Full walkthrough: [docs/API_WALKTHROUGH.md](docs/API_WALKTHROUGH.md).

## Benchmark And Evaluation Artifacts

Run individual evaluation checks:

```bash
./.venv/Scripts/python.exe -m app.evaluation.benchmark_runner
./.venv/Scripts/python.exe -m app.evaluation.extraction_runner
./.venv/Scripts/python.exe -m app.evaluation.multimodal_runner
./.venv/Scripts/python.exe -m app.evaluation.comparison_runner
./.venv/Scripts/python.exe -m app.evaluation.recommendation_runner
```

Refresh the checked-in baseline bundle only when behavior changes intentionally:

```bash
./.venv/Scripts/python.exe -m app.evaluation.artifact_writer
```

Baseline artifacts:

- `data/eval/reports/baseline/summary.md`
- `data/eval/reports/baseline/benchmark_report.json`
- `data/eval/reports/baseline/extraction_report.json`
- `data/eval/reports/baseline/comparison_report.json`
- `data/eval/reports/baseline/recommendation_report.json`
- `data/eval/reports/baseline/artifact_manifest.json`

Evaluation guide: [docs/EVALUATION.md](docs/EVALUATION.md).

## Reviewer Guides

- Deployment: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Demo path: [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)
- API walkthrough: [docs/API_WALKTHROUGH.md](docs/API_WALKTHROUGH.md)
- Release notes: [RELEASE_NOTES.md](RELEASE_NOTES.md)

## Data Handling

Resume and JD content can contain sensitive personal or company information.
Use synthetic examples for demos. The backend does not persist profile memory,
but local logs, shell history, CI output, and deployment platforms may retain
request data.

## Current Limitations

- backend only; no frontend UI
- no production hosting target
- no OCR runtime for scanned PDFs or images
- no persistent database, vector store, or background job queue
- fixed deterministic scoring and capability vocabulary
- optional LLM advisory generation is disabled by default and cannot override deterministic results

## Milestone Status

Milestones 1 through 9 are implemented in the current backend. M10 is the
deployment and portfolio release packaging layer: docs, configuration examples,
Docker/CI readiness, demo flow, and benchmark navigation.
