# M10: Deployment and Portfolio Release

## Goal

Package CareerFit Agent as a stable, reviewable portfolio backend with clear deployment, evaluation, and demo instructions.

## Allowed Scope

- Harden Docker and CI workflows.
- Split runtime and development dependency guidance if needed.
- Add production configuration documentation.
- Add release notes, portfolio narrative, demo scripts, and API walkthroughs.
- Verify benchmark reports and snapshots as part of release readiness.
- Clean stale docs and align public examples with current behavior.

## Out Of Scope

- Major new product features.
- New OCR, LLM, frontend, or storage architecture.
- Score or blocker semantics changes.
- Baseline metric changes without explicit release rationale.
- Large refactors unrelated to release readiness.

## Required Invariants

- The release story must match the checked-in code and artifacts.
- The demo path must be runnable from a clean environment.
- Sensitive resume/JD content handling remains documented and conservative.

## Completion Signal

- A reviewer can install, run, test, inspect benchmarks, and understand the project value without private context.
- CI and Docker support the documented backend workflow.
- Docs, examples, and release notes match current behavior.
