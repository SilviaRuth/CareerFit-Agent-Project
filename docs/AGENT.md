# AGENT.md

## Project
CareerFit Agent

An explainable AI agent system for matching resumes to job descriptions, identifying skill gaps, and generating actionable recommendations for resume improvement, learning plans, and interview preparation.

This repository is designed to be:
- modular
- testable
- evaluation-driven
- easy to review
- easy to extend toward agentic / multi-agent workflows later

---

## Purpose of this file

This file provides project-specific instructions for coding agents such as Codex.

Use this file to:
- understand the architecture and development priorities
- follow the repository conventions
- avoid unnecessary architectural drift
- implement features in a bounded and reviewable way
- keep the system explainable and evaluation-oriented

When in doubt:
- preserve clarity over cleverness
- preserve modularity over premature abstraction
- preserve testability over speed of implementation

---

## Product intent

This is **not** a generic chatbot project.

This project is an AI system for a recruiting / career workflow. Its primary job is to:
1. parse a job description into structured requirements
2. parse a resume into a structured candidate profile
3. normalize skills and evidence
4. compute deterministic fit analysis
5. explain strengths, gaps, and blockers
6. generate bounded rewrite and interview-prep guidance from grounded evidence
7. support offline regression review through checked-in fixtures and reports

Outputs should stay:

- structured
- explainable
- evidence-linked where possible
- safe and advisory rather than overly authoritative
- reviewable without hidden reasoning steps

Do not implement shallow keyword matching as the only logic unless explicitly requested for a baseline.

---

## Development priorities

Prioritize work in this order:

1. correctness of structured extraction
2. skill normalization quality
3. explainable matching logic
4. recommendation usefulness
5. retrieval grounding
6. evaluation coverage
7. API stability
8. UI polish

Do not jump to heavy frontend work unless explicitly asked.

---

## Architecture principles

Follow these principles:

### 1. Keep modules narrow
Prefer small, cohesive modules with clear responsibilities.

### 2. Separate concerns
Keep these concerns separate:
- preprocessing
- extraction
- normalization
- scoring
- recommendation
- retrieval
- evaluation
- API transport

### 3. Prefer structured outputs
Whenever possible, outputs should be validated against explicit schemas instead of free-form text.

### 4. Avoid premature multi-agent complexity
The default architecture is a single orchestrator plus specialized modules/services.
Do not introduce multi-agent orchestration unless the task explicitly calls for it.

### 5. Keep behavior inspectable
Avoid hidden magic. Favor explicit logic, readable flows, and reviewable outputs.

---

## Tech stack expectations

Default assumptions unless the task says otherwise:

- Python 3.11
- FastAPI
- Pydantic v2
- pytest
- sentence-transformers for embeddings if retrieval is added
- FAISS or Chroma for vector retrieval
- structured logging
- type hints throughout

Do not introduce major framework changes without justification.

Examples of framework changes that require justification:
- replacing FastAPI
- switching to a large orchestration framework
- introducing a database migration system too early
- adding frontend frameworks before backend MVP is stable

## Repository Shape

Current important paths:

- `app/api/routes/`: FastAPI transport layer
- `app/core/`: static config and core constants
- `app/schemas/`: Pydantic models and API contracts
- `app/services/`: parsing, matching, orchestration, comparison, and adaptation logic
- `app/services/generation/`: grounded rendering and generation guardrails
- `app/services/ingestion/`: bounded text, PDF, and DOCX ingestion
- `app/evaluation/`: offline benchmark and artifact helpers
- `data/samples/`: reviewable input fixtures
- `data/eval/`: expected outputs, manifests, and checked-in reports
- `tests/unit/` and `tests/integration/`: regression coverage
- `tests/` — unit/integration tests
- `docs/` — project docs and design notes

Do not collapse everything into a single script.

## Coding Preferences

- Use explicit Python with type hints on public and non-trivial internal functions.
- Prefer small functions and narrow modules.
- Avoid adding abstractions just for style.
- Fail clearly on invalid inputs.
- Do not swallow parsing failures.
- Preserve deterministic behavior on the parse and match critical path.

### Logging
- Add structured logs for non-trivial workflow steps.
- Do not log secrets or sensitive raw personal data unless explicitly required for a local debug mode.

### Comments and docstrings
- Add docstrings for public classes/functions.
- Add concise comments only when logic is non-obvious.
- Do not over-comment trivial code.

---

## Schema rules

Structured schemas are a core part of this project.

When implementing extraction or generation logic:
- always prefer validated Pydantic models
- avoid loose untyped dicts where a schema should exist
- preserve room for extension
- keep field names explicit and stable

Important:
- extracted fields should distinguish required vs preferred where relevant
- preserve raw extracted evidence when useful
- do not flatten everything into one score too early

---

## Matching logic rules

Matching should remain explainable and evidence-backed.

Typical output includes:

- overall score
- dimension scores
- required and preferred matches
- strengths
- gaps
- blocker flags
- explanations
- evidence spans
- additive adaptation metadata when relevant

Important distinctions must stay visible:

- missing skill vs missing evidence
- required vs preferred requirements
- score vs blocker severity








## Parsing And Generation Expectations

- Supported ingestion inputs are text, `.txt`, `.pdf`, and `.docx`.
- File handling must stay bounded and safe.
- Parse responses must surface warnings, unsupported segments, and parser confidence.
- Rewrite and interview-prep outputs must not invent experience, seniority, metrics, or missing
  tools.
- Any richer generated output must remain grounded in evidence already present in the resume or JD.

## Retrieval rules

If retrieval / RAG is implemented:
- keep the first version simple
- prefer a lightweight pipeline
- document data sources clearly
- separate indexing from retrieval from answer generation
- keep grounding optional and testable

Do not add retrieval just for buzzwords.
Use retrieval only where it materially improves grounding, consistency, or recommendation quality.

## Evaluation Expectations

Evaluation is a first-class concern in this repository.

Any important new logic should be testable and, where practical, evaluable offline.

Prefer adding:
- unit tests for deterministic logic
- small gold examples for extraction/matching
- evaluation scripts for scoring consistency and comparison stability
- regression tests for bug fixes

When adding evaluation:
- keep datasets small and understandable first
- prefer human-readable fixtures
- document assumptions
- refresh checked-in baseline artifacts only when the behavior change is intentional

Do not rely only on subjective eyeballing.

The current M4 evaluation layer covers:

- match benchmarks
- extraction benchmarks
- multi-resume comparison scenarios
- baseline reports
- snapshot-capable artifact output


## Testing expectations

For non-trivial code changes, add tests.

At minimum:
- normal-case test
- edge-case test
- invalid-input or failure-case test when relevant

For bug fixes:
- add a regression test

Preferred test layout:
- `tests/unit/` for narrow logic
- `tests/integration/` for module interactions

Do not merge logic changes without reasonable test coverage unless explicitly instructed.

## Safe handling of resume / JD content

This repository may handle personal and career-related documents.

Default rules:
- prefer sanitized sample data
- avoid exposing full sensitive personal data in logs
- avoid inventing claims about a candidate
- present outputs as advisory, not authoritative hiring decisions

If implementing UI or output templates:
- avoid phrasing that implies guaranteed hiring outcomes
- avoid biased or overly certain language

---

## How to work on tasks

When implementing a task, follow this sequence:

1. understand the exact scope
2. inspect related schemas and existing module boundaries
3. propose or infer the narrowest clean implementation
4. implement only what is necessary
5. add/update tests
6. make sure the code is easy to review
7. summarize design choices and limitations if requested

If the task is underspecified:
- make the smallest reasonable choice
- avoid expanding scope unnecessarily
- do not redesign unrelated modules

---

## Change scope discipline

Unless explicitly requested, do not:
- rename large parts of the codebase
- introduce major new dependencies
- refactor unrelated modules
- rewrite working code for style alone
- add a frontend
- add multi-agent orchestration
- add database complexity beyond project needs

Prefer targeted changes over sweeping rewrites.

---

## What to do before introducing a new dependency

Before adding a dependency, ask whether it is truly needed.

A new dependency should usually satisfy at least one of:
- significantly reduces complexity
- clearly improves correctness
- clearly improves maintainability
- is standard for the task
- cannot be reasonably replaced by existing tools

If added, explain briefly:
- why it is needed
- what problem it solves
- why lighter alternatives were not used

---

## Preferred implementation style for this project

Good:
- schema-first
- test-backed
- modular
- explicit
- explainable
- incremental

Bad:
- giant end-to-end scripts
- opaque scoring magic
- over-engineered abstractions
- untested prompt-heavy logic
- framework sprawl
- “agentic” complexity without product need

## Review Checklist

Before calling work complete, verify:

- correctness
- schema alignment
- evidence traceability
- thin route boundaries
- adequate tests
- docs updated if public behavior changed
- no hidden architectural drift toward retrieval or multi-agent complexity

## Default task preferences

If asked to choose, prefer:
- baseline implementation first
- simple deterministic logic before advanced agent loops
- schema stability before optimization
- reviewable code before clever code
- useful evaluation before fancy demos

## If asked to implement agent behavior

Default approach:
- start with a single orchestrator
- keep specialist modules as services/functions
- add planner/router only when needed
- add reflection/reviewer steps only after the baseline is stable

Do not introduce a complex multi-agent graph by default.

---

## Delivery expectations

When completing a meaningful task, prefer to include:
- code changes
- tests
- brief note on design choices
- brief note on limitations or next steps when useful

If a task cannot be completed cleanly because of missing context, state the blocker clearly rather than guessing wildly.

---

## Final rule

This repository values:
- practical usefulness
- engineering clarity
- explainable outputs
- measured iteration

Build the project so it can become a strong portfolio-quality AI agent system, not just a prompt demo.
