---
name: careerfit-neat-execution
version: 1.0
project: CareerFit-Agent-Project
repo: https://github.com/SilviaRuth/CareerFit-Agent-Project
owner: SilviaRuth
purpose: >
  Project-specific clean-up and execution-readiness skill for CareerFit Agent.
  Use after each milestone or before starting implementation to reconcile docs,
  AGENT.md, plans, tests, schemas, and deterministic backend behavior.
triggers:
  - /neat
  - /sync
  - clean up docs
  - tidy up docs
  - neat execution
  - milestone done
  - before implementation
  - 整理文档
  - 收尾
  - 这个阶段做完了
  - 新人能直接上手
---

# CareerFit Neat Execution Skill

## Role

You are the project editor and execution-readiness reviewer for **CareerFit-Agent-Project**. Your job is not to append more notes. Your job is to reconcile the repository so that the next implementation pass can start with clean contracts, current docs, aligned tests, and no stale milestone assumptions.

Treat this project as a deterministic JD/resume matching backend. Do **not** introduce autonomous agents, LLM provider SDKs, OCR behavior, public API behavior changes, scoring rewrites, blocker rewrites, or benchmark refreshes unless the active milestone explicitly allows it.

## Current project context

The repository has a documentation-heavy workflow. At minimum, inspect these areas when present:

- `AGENT.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/CODE_REVIEW.md`
- `docs/CURRENT_STATE_AUDIT.md`
- `docs/DECISIONS.md`
- `docs/EVALUATION.md`
- `docs/PLAN.md`
- `docs/ROADMAP.md`
- `docs/PR_CONVENTIONS.md`
- `docs/*_API.md`
- `docs/milestones/*.md`
- `tests/`
- `app/` or backend source directories
- CI, Docker, and dependency files when present

For M6 specifically, preserve the milestone boundary:

- Allowed: shared workflow trace, step trace, document, and agent-result contracts; service boundary standardization; deterministic helper extraction; schema/helper/no-regression tests; docs/CI/Docker alignment.
- Forbidden: autonomous multi-agent orchestration, LLM/model calls, OCR/scanned-PDF parsing, frontend dashboard, persistent profile memory, score weighting or blocker semantic rewrites, public API contract changes, benchmark baseline refreshes.

## Non-negotiable invariants

1. Existing endpoints must keep current behavior.
2. Parse, match, generation, comparison, retrieval, and semantic helper behavior must remain deterministic unless explicitly scoped.
3. Existing benchmark metrics must be preserved.
4. Baseline artifacts must not be regenerated or refreshed unless the task explicitly says so.
5. Public API changes require explicit documentation and tests; otherwise avoid them.
6. If a helper is extracted, prove behavior parity with regression tests.
7. Documentation must describe the implemented code, not the intended future architecture.

## Execution process

### Step 1 — Inventory before judgment

Run these commands from the project root and inspect the results before editing:

```bash
pwd
find . -maxdepth 2 -type f -name "*.md" -not -path "*/.git/*" | sort
find docs -maxdepth 3 -type f -name "*.md" 2>/dev/null | sort
find app tests -maxdepth 3 -type f 2>/dev/null | sort
```

Create an internal inventory table with one row per relevant file:

| File | Purpose | Status |
|---|---|---|
| path | what this file controls | assessed / edit / skip |

Do not skip a markdown file simply because it looks unrelated. First classify it.

### Step 2 — Detect drift

Compare the active milestone, code, tests, and docs. Look for:

- docs claiming a route, schema, module, or command that does not exist;
- code behavior not represented in docs;
- duplicate milestone plans that conflict;
- stale TODOs already completed in code;
- relative time phrases such as `recently`, `today`, `last week`, `昨天`, `最近`;
- API docs inconsistent with route handlers or response models;
- architecture docs inconsistent with source folders;
- AGENT.md instructions that conflict with current scripts or project layout;
- tests missing for any new schema, contract, or helper extraction.

Use this impact matrix:

| Change type | Must check/update |
|---|---|
| New shared schema or contract | `docs/ARCHITECTURE.md`, relevant `docs/*_API.md`, tests, `AGENT.md` if it affects agent workflow |
| New or changed route | relevant `docs/*_API.md`, `docs/ARCHITECTURE.md`, tests, README if user-facing |
| Helper extraction | tests, `docs/CODE_REVIEW.md` if it changes review expectations |
| Milestone completion | `docs/milestones/<milestone>.md`, `docs/ROADMAP.md`, `docs/CURRENT_STATE_AUDIT.md` |
| Environment/config change | README, `AGENT.md`, Docker/CI docs if present |
| Evaluation/benchmark change | `docs/EVALUATION.md`, benchmark tests, artifact policy |
| Decision made | `docs/DECISIONS.md` with date and rationale |

### Step 3 — Make edits, do not only describe edits

When cleanup is requested, actually modify files. Use focused patches, not large rewrites.

Editing principles:

- Prefer updating existing sections over appending duplicates.
- Delete obsolete notes when the code proves them outdated.
- Convert vague roadmap language into executable milestone tasks.
- Keep docs concise and onboarding-friendly.
- Keep implementation plans separated from public API documentation.
- Use absolute dates in decisions and audit notes.
- Preserve M6 scope boundaries strictly.

### Step 4 — M6 execution-readiness checklist

Before implementation starts, verify that M6 has a crisp definition of done:

- [ ] Exact contract names are listed.
- [ ] Exact target files/modules are listed.
- [ ] Public API non-change policy is stated.
- [ ] No LLM/OCR/autonomous agent work is included.
- [ ] Tests are mapped to each contract/helper change.
- [ ] Benchmark preservation is testable.
- [ ] Docs to update are named.
- [ ] Rollback or no-regression strategy is clear.

Recommended M6 deliverables:

1. `WorkflowTrace` schema.
2. `StepTrace` schema.
3. `DocumentArtifact` or equivalent document contract.
4. `AgentResult` or `WorkflowResult` contract.
5. Adapter layer wrapping deterministic services without changing endpoint behavior.
6. Tests for schema serialization, required fields, deterministic helper parity, and endpoint no-regression.
7. Documentation update across architecture, current-state audit, roadmap, and milestone file.

### Step 5 — Verification commands

Run the project’s real commands. If unknown, discover them from README, `pyproject.toml`, `requirements.txt`, Makefile, or CI.

Typical checks:

```bash
python -m pytest
python -m ruff check . 2>/dev/null || true
python -m mypy . 2>/dev/null || true
```

Only report checks as passed if they were actually run and completed successfully. If a tool is not configured, say so precisely.

### Step 6 — Final summary format

After edits and verification, respond with:

```markdown
## Neat execution complete

### Changed files
- `path` — what changed and why

### Verified
- command — result

### Preserved invariants
- endpoint behavior: preserved / not verified
- deterministic behavior: preserved / not verified
- benchmark artifacts: preserved / not verified

### Remaining risks
- risk or `None`

### Next implementation step
- one concrete next action
```

Do not claim a file was checked, changed, or verified unless it actually was.

## Codex handoff prompt

Use this prompt when asking Codex to run the skill:

```text
Run the CareerFit neat execution skill before implementation.

Project: CareerFit-Agent-Project
Milestone: M6 Agent Standardization Foundation
Goal: prepare deterministic backend contracts for future agent-style workflows without changing public API behavior.

Strict scope:
- Define shared workflow trace, step trace, document, and result contracts.
- Standardize service boundaries around current deterministic capabilities.
- Extract duplicated deterministic helpers only when behavior is identical.
- Add schema, helper parity, and endpoint no-regression tests.
- Keep CI, Docker, and docs aligned.

Out of scope:
- Autonomous agents.
- LLM provider SDKs or model calls.
- OCR/scanned-PDF parsing.
- Frontend dashboard.
- Persistent profile memory.
- Score weighting, blocker semantics, or match contract rewrites.
- Benchmark baseline refreshes.

First, inventory all root markdown files, docs files, app/backend source files, tests, CI, Docker, and dependency files. Then identify drift between docs, milestone plans, and code. Make focused cleanup edits only. Finally run available tests/lint and report changed files, verified commands, preserved invariants, risks, and the next implementation step.
```
