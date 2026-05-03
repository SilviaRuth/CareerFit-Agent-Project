# Deployment Guide

CareerFit Agent is a backend-only FastAPI service. The release target is a
reviewable portfolio deployment, not a production SaaS platform.

## Runtime Shape

- Python 3.11
- FastAPI served by `uvicorn`
- no database
- no vector store
- no persistent profile memory
- no required secrets for deterministic local use
- optional LLM advisory configuration, disabled by default

Runtime dependencies live in `requirements.txt`. Development and test
dependencies live in `requirements-dev.txt` and in the `dev` optional dependency
group in `pyproject.toml`.

## Environment

Start from the checked-in example:

```bash
cp .env.example .env
```

For the default deterministic demo, keep:

```bash
ENABLE_LLM_GENERATION=false
```

Only set `OPENAI_API_KEY` or `LLM_API_KEY` in a private local environment when
testing the optional `/llm/advice` path, and replace the `LLM_MODEL`
placeholder with a valid provider model before enabling LLM generation. Do not
commit real resume, JD, or API key material.

## Local Backend

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If you use a virtual environment, activate it with your shell's normal
activation command before installing dependencies.

Optional Windows venv note:

```bash
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify the service:

```bash
curl http://127.0.0.1:8000/health
```

## Docker

Build and run the backend image:

```bash
docker build -t careerfit-agent .
docker run --rm --env-file .env.example -p 8000:8000 careerfit-agent
```

Or use Docker Compose:

```bash
docker compose up --build
```

Verify the container:

```bash
curl http://127.0.0.1:8000/health
```

The Docker image installs runtime dependencies only. It does not add OCR,
frontend, database, vector-store, or provider SDK dependencies.

## CI

`.github/workflows/ci.yml` is configured to run on pushes to `main` and pull
requests. It performs:

```bash
python -m ruff check app tests
python -m pytest -q
docker build -t careerfit-agent:ci .
docker run -d --rm --name careerfit-agent-ci -p 8000:8000 careerfit-agent:ci
curl-equivalent GET /health assertion for {"status": "ok"}
```

This verifies linting, tests, Docker image build readiness, and container
startup when a GitHub Actions run completes successfully. CI does not publish an
image or deploy the service.

## Deployment Notes

- Bind the container to the platform-provided port if the host requires it; the
  checked-in image defaults to port `8000`.
- Keep uploaded resume and JD data treated as sensitive input. The service does
  not persist profile memory, but deployment logs and reverse proxies may.
- Keep OCR, persistent storage, vector search, and long-running async workflows
  out of this release unless they are explicitly scoped and tested later.
- Use the checked-in evaluation artifacts under `data/eval/reports/baseline/`
  as release evidence, not as claims about production hiring outcomes.
