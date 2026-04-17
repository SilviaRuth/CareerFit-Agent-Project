# Evaluation Guide

This guide documents the first M4 benchmark scaffold for CareerFit Agent.

## Purpose

The current benchmark layer turns the existing gold fixtures into a repeatable offline check for:

- fit-label stability
- blocker-flag stability
- required/preferred match recall
- top-gap coverage
- score snapshots for regression review

This is a scaffold, not the full M4 benchmark yet. It starts from the 3 existing annotated pairs and is meant to expand as the cleaned dataset is labeled.

## Current Inputs

- benchmark manifest: `data/eval/benchmark_manifest.json`
- sample text fixtures: `data/samples/`
- expected outcome fixtures: `data/eval/*_expected.json`

## Run The Benchmark

```powershell
.venv\Scripts\Activate.ps1
python -m app.evaluation.benchmark_runner
```

The runner prints a JSON report with:

- aggregate metrics
- per-case fit label checks
- blocker flag comparisons
- missing expected required/preferred matches
- missing expected top gaps
- dimension score snapshots

## Run Extraction Benchmark

```powershell
.venv\Scripts\Activate.ps1
python -m app.evaluation.extraction_runner
```

The extraction benchmark checks parse confidence plus field-presence expectations across the manifest in `data/eval/extraction_manifest.json`.

## Refresh Baseline Artifacts

```powershell
.venv\Scripts\Activate.ps1
python -m app.evaluation.artifact_writer
```

This refreshes the reviewable baseline artifacts in `data/eval/reports/baseline/`:

- `benchmark_report.json`
- `extraction_report.json`
- `summary.md`

## Current Label Heuristic

The benchmark runner derives coarse fit labels from the deterministic match result for reporting only:

- `strong`: score >= 80 and no unsupported-claim, missing-required-skill, or seniority blockers
- `partial`: score >= 40 without missing-required-skill or seniority blockers
- `poor`: everything else

This heuristic is a benchmark convenience, not an API contract. If score interpretation changes later, update the runner, fixtures, checked-in artifacts, and docs together.

## What M4 Still Needs

The full M4 target in `docs/PLAN.md` is larger than the current scaffold. Remaining work includes:

- expanding beyond the first 3 annotated pairs
- adding extraction-oriented benchmark cases
- adding score consistency checks across larger fixture sets
- adding multi-resume comparison coverage
- saving versioned benchmark artifacts for regression review

## Benchmark Expansion Pattern

When adding new benchmark cases:

1. add a new resume/JD fixture pair under `data/samples/`
2. add the expected outcome JSON under `data/eval/`
3. add the case to `data/eval/benchmark_manifest.json`
4. add or update tests if the new case represents a bug fix or new supported behavior

Keep fixtures human-readable and small enough to review comfortably.
