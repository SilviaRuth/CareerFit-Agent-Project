# CODE_REVIEW.md

## Purpose

This document defines the review standard for CareerFit Agent.

Review priority order:

1. correctness
2. evidence and grounding
3. maintainability
4. architectural fit
5. testability
6. performance
7. style and naming

## Core Rules

Must-have qualities:

- single responsibility per module
- clear function boundaries
- typed interfaces where practical
- deterministic behavior on critical paths
- explicit error handling
- minimal hidden side effects

Avoid:

- business logic in route handlers
- duplicated parsing or matching logic
- silent fallback behavior
- unbounded file handling
- contract changes without schema and doc updates
- prompt-heavy logic without validation guardrails

## Architecture Checks

Reviewers should ask:

- Does the change fit the intended module boundary?
- Is workflow logic in `services/` rather than routes?
- Does the change preserve evidence traceability?
- Did any public schema change silently?
- Does this introduce drift toward retrieval or multi-agent complexity without approval?

Red flags:

- route code doing parse plus match plus formatting directly
- one service depending on another service's internals
- ranking logic hidden in unrelated layers
- generation logic bypassing guardrails
- additive presentation metadata being used to silently rewrite score meaning

## Matching Review

Matching changes require extra scrutiny.

Verify:

- required and preferred requirements are treated differently
- missing evidence is not confused with missing skill
- blocker behavior remains explicit
- dimension scores stay interpretable
- weight or threshold changes are justified

If scoring or ranking behavior changes, include:

- rationale
- before and after examples when useful
- updated tests or fixtures
- refreshed evaluation artifacts when the checked-in baseline intentionally changes

## Parsing And Ingestion Review

Verify:

- malformed files fail in a bounded way
- uploads are size-limited
- warnings and confidence remain informative
- unsupported segments stay reviewable
- parser behavior does not silently flatten important failures into empty success output

## Generation Review

Verify:

- outputs are grounded in evidence spans
- unsupported claims are not amplified
- seniority and experience are not inflated
- output schemas are validated
- route handlers remain thin and orchestration stays in the service layer

## Comparison And Evaluation Review

Verify:

- multi-resume ranking is deterministic
- cross-JD ranking stays deterministic and keeps additive helper signals separate from the core score
- low-confidence resumes are handled intentionally
- profile-memory, retrieval, and semantic helper outputs stay explicit and auditable
- manifests, expected outputs, and tests move together
- baseline and snapshot artifacts are still reviewable

## Testing Expectations

For non-trivial changes, expect:

- a normal-case test
- an edge-case test
- a failure-case test when relevant

Specific review expectations:

- parser changes: clean input plus messy or malformed input coverage
- matching changes: required, preferred, missing evidence, and blocker coverage
- comparison changes: representative ranking coverage, including confidence-sensitive cases
- generation changes: schema validity and evidence-presence checks

## Documentation Review

A change is not complete if future maintainers cannot understand it.

Update docs when relevant:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/EVALUATION.md`
- public API docs
- fixtures or checked-in artifact notes

## Merge Criteria

A change is ready when:

- behavior is correct
- evidence grounding is preserved
- architecture remains coherent
- tests are adequate
- docs and contracts are aligned
- no important safety issue remains unresolved
