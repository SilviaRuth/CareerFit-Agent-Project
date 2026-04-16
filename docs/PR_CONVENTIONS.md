# PR Conventions

Milestone 1 PRs should stay small, schema-first, and test-backed.

## Required for merge

- keep route handlers thin
- place domain logic in `app/services/`
- update schemas when the contract changes
- update tests when scoring or extraction changes
- update fixtures or docs when public behavior changes

## PR scope rules

- one concern per PR
- avoid mixing architecture refactors with feature work
- avoid unrelated file churn
- prefer reviewable incremental changes over large rewrites

## Minimum checklist

- deterministic behavior for the changed path
- evidence traceability preserved
- required vs preferred logic covered by tests
- missing skill vs missing evidence covered by tests

