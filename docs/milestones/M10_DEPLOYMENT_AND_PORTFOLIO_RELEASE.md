# M10: Deployment and Portfolio Release

Status: implemented as the release-packaging layer on 2026-05-03. This milestone
does not change core parsing, matching, scoring, blocker, OCR, LLM, frontend, or
storage behavior.

## Goal

Package CareerFit Agent as a stable, reviewable portfolio backend with clear deployment, evaluation, benchmark, and demo instructions.

The final release should allow an external reviewer to understand the project value, run the backend from a clean environment, inspect the API behavior, review benchmark artifacts, and evaluate the project without private context.

## Allowed Scope

- Harden Docker and CI workflows.
- Verify backend startup in a clean local environment.
- Verify backend startup through Docker or Docker Compose.
- Split runtime and development dependency guidance if needed.
- Add or update production configuration documentation.
- Add release notes, portfolio narrative, demo scripts, and API walkthroughs.
- Verify benchmark reports and snapshots as part of release readiness.
- Clean stale docs and align public examples with current behavior.
- Add `.env.example` and conservative configuration guidance if missing.
- Improve README navigation and reviewer-facing documentation.

## Out Of Scope

- Major new product features.
- New OCR, LLM, frontend, or storage architecture.
- Score or blocker semantics changes.
- Baseline metric changes without explicit release rationale.
- Large refactors unrelated to release readiness.
- Rewriting core matching logic unless required to fix a release-blocking bug.
- Adding claims to docs that are not supported by checked-in code, tests, examples, or artifacts.

## Required Invariants

- The release story must match the checked-in code and artifacts.
- The demo path must be runnable from a clean environment.
- Sensitive resume/JD content handling remains documented and conservative.
- Public examples must use synthetic or non-sensitive data only.
- Benchmark, evaluation, and snapshot descriptions must match actual artifact names and paths.
- CI/Docker documentation must reflect commands that were actually tested.

## Required Deliverables

- Updated `README.md` with:
  - project overview
  - architecture summary
  - install instructions
  - local run instructions
  - Docker run instructions
  - test instructions
  - API walkthrough
  - benchmark/evaluation artifact guide
  - portfolio/demo narrative

- Add or update:
  - `docs/DEPLOYMENT.md`
  - `docs/DEMO_GUIDE.md`
  - `docs/API_WALKTHROUGH.md`
  - `RELEASE_NOTES.md`
  - `.env.example`
  - CI workflow documentation if applicable

## Implemented Deliverables

- `README.md` now covers overview, architecture, setup, local run, Docker,
  checks, API walkthrough, benchmark artifacts, and reviewer guidance.
- `docs/DEPLOYMENT.md` documents local, Docker, Docker Compose, environment,
  and CI release paths.
- `docs/DEMO_GUIDE.md` provides a reviewer demo script with synthetic data.
- `docs/API_WALKTHROUGH.md` provides health, match, parse, guidance, career
  helper, and optional LLM advisory walkthrough notes.
- `RELEASE_NOTES.md` summarizes the M10 release packaging.
- `.env.example` documents conservative default runtime configuration.
- `requirements.txt` is runtime-only and `requirements-dev.txt` carries local
  development/test dependencies.
- `docker-compose.yml` defines the API service and health check.
- `.github/workflows/ci.yml` runs Ruff, pytest, and Docker image build
  verification.
- `docs/examples/match_request.json` provides the synthetic `/match`
  walkthrough payload.

## Clean Environment Acceptance Path

A reviewer should be able to complete the following from a fresh clone:

1. Install dependencies or build the Docker image.
2. Configure environment variables using `.env.example`.
3. Run the test suite.
4. Start the backend.
5. Send at least one sample resume/JD matching request.
6. Inspect the response JSON.
7. Locate benchmark/evaluation artifacts.
8. Understand project value, limitations, and next-step roadmap from the README and release docs.

## Verification Checklist

Before marking M10 complete, Codex must report:

- Exact commands used for local setup.
- Exact commands used for Docker setup.
- Exact commands used for tests.
- Exact endpoint/request used for the API walkthrough.
- Whether CI passes or, if not executable locally, what was statically verified.
- Files changed.
- Any stale docs removed or corrected.
- Any known limitations that remain.

## Completion Signal

- A reviewer can install, run, test, inspect benchmarks, and understand the project value without private context.
- CI and Docker support the documented backend workflow.
- Docs, examples, and release notes match current behavior.
- No release or portfolio claim exceeds what the codebase can demonstrate.
