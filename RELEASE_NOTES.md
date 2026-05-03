# Release Notes

## M10 Deployment And Portfolio Release

Release date: 2026-05-03

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
- CI Docker build verification alongside Ruff and pytest.
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
pip install -r requirements-dev.txt
./.venv/Scripts/python.exe -m ruff check app tests
./.venv/Scripts/python.exe -m pytest -q
docker build -t careerfit-agent .
docker run --rm --env-file .env.example -p 8000:8000 careerfit-agent
curl http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/match -H "Content-Type: application/json" --data @docs/examples/match_request.json
```

### Known Limitations

- No production hosting target is configured.
- No frontend is included.
- No OCR runtime support is included.
- No persistent database, vector store, or background job queue is included.
- Optional LLM advisory generation remains disabled by default and requires
  private credentials only when intentionally enabled.
