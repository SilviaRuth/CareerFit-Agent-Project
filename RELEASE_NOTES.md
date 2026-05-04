# Release Notes

## Frontend Backend Integration

Release date: 2026-05-04

- Wired the frontend `Run Analysis` workflow to the real backend `POST /match`
  endpoint at `http://127.0.0.1:8000/match`.
- Added typed frontend adapters that convert backend snake_case response fields
  into the existing dashboard data shape.
- Added local development CORS support for Vite origins.
- Kept mock analysis mode available through `VITE_USE_MOCK_ANALYSIS=true`.
- Added clear backend-unavailable error messaging.

## Frontend Mock UI

Release date: 2026-05-04

- Added a standalone Vite, React, TypeScript, Tailwind CSS frontend under
  `frontend/`.
- Added typed mock analysis data for resume-to-JD matching so the UI can run
  without backend API dependency.
- Added modular input, dashboard, evidence comparison, gap analysis, and report
  export panels.
- Frontend export markdown and PDF actions are placeholders for later API or
  client-side export integration.

## M10 Deployment And Portfolio Release

Release date: 2026-05-03

### M10.1 Release-Readiness Cleanup

- Main setup, check, API, and evaluation commands now use OS-neutral
  `python -m ...` examples.
- Windows `.venv/Scripts/python.exe` commands are kept only as optional notes.
- CI is configured to smoke-test the built Docker container with `GET /health`
  after image build.
- CI docs now say the workflow is configured to run checks unless a passing
  GitHub Actions run has been verified.
- `.env.example` uses a placeholder `LLM_MODEL` and requires replacement with a
  valid provider model before enabling LLM generation.

### Summary

M10 packages CareerFit Agent as a reviewable backend portfolio release. It does
not add a new product feature; it clarifies how an external reviewer can install,
run, test, inspect, and evaluate the existing backend.

### Included

- Reviewer-focused README navigation and release story.
- `.env.example` with conservative default LLM settings.
- Runtime-only `requirements.txt` plus `requirements-dev.txt` for local checks.
- Hardened Docker image that installs runtime dependencies only and runs as a
  non-root user.
- `docker-compose.yml` with a backend service and health check.
- CI workflow configured for Docker build and container smoke verification
  alongside Ruff and pytest.
- Deployment guide, API walkthrough, and demo guide.
- Synthetic `/match` request example under `docs/examples/`.

### Current Backend Surface

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

### Verification Target

The release is considered reviewable when these commands pass or are statically
verified:

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check app tests
python -m pytest -q
docker build -t careerfit-agent .
docker run --rm --env-file .env.example -p 8000:8000 careerfit-agent
curl http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/match -H "Content-Type: application/json" --data @docs/examples/match_request.json
```

Optional Windows venv note:

```bash
./.venv/Scripts/python.exe -m ruff check app tests
./.venv/Scripts/python.exe -m pytest -q
```

### Known Limitations

- No production hosting target is configured.
- No frontend is included.
- No OCR runtime support is included.
- No persistent database, vector store, or background job queue is included.
- Optional LLM advisory generation remains disabled by default and requires
  private credentials only when intentionally enabled.
