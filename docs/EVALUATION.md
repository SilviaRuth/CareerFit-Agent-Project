# Evaluation Guide

This guide documents the Milestone 4 evaluation workflow for CareerFit Agent.

## Purpose

The M4 evaluation layer turns the checked-in fixtures into repeatable offline checks for:

- fit-label stability
- blocker-flag stability
- required/preferred match recall
- top-gap coverage
- score snapshots for regression review
- extraction confidence and field-presence stability
- multi-resume ranking stability
- low-confidence resume ordering in comparison scenarios

Current checked-in coverage:

- 15 match benchmark cases
- 13 extraction benchmark cases
- 3 multi-resume comparison scenarios
- baseline and snapshot-capable report artifacts

## Current Inputs

- benchmark manifest: `data/eval/benchmark_manifest.json`
- extraction manifest: `data/eval/extraction_manifest.json`
- comparison manifest: `data/eval/comparison_manifest.json`
- sample text fixtures: `data/samples/`
- expected outcome fixtures: `data/eval/*_expected.json`

## Run The Match Benchmark

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

## Run The Extraction Benchmark

```powershell
.venv\Scripts\Activate.ps1
python -m app.evaluation.extraction_runner
```

The extraction benchmark checks parse confidence plus field-presence expectations across `data/eval/extraction_manifest.json`.

## Run The Comparison Benchmark

```powershell
.venv\Scripts\Activate.ps1
python -m app.evaluation.comparison_runner
```

The comparison benchmark checks representative multi-resume ranking scenarios from `data/eval/comparison_manifest.json`, including same-candidate resume variants and low-confidence resume ordering.

## Refresh Reviewable Artifacts

```powershell
.venv\Scripts\Activate.ps1
python -m app.evaluation.artifact_writer
python -m app.evaluation.artifact_writer --snapshot-label m4-review
```

`baseline` refreshes the checked-in reference bundle under `data/eval/reports/baseline/`.

Any non-`baseline` label writes a comparable snapshot under `data/eval/reports/snapshots/<label>/`.

Each artifact set includes:

- `benchmark_report.json`
- `extraction_report.json`
- `comparison_report.json`
- `artifact_manifest.json`
- `summary.md`

Snapshot runs also write `snapshot_comparison.json` when the checked-in baseline is available.

## Current Label Heuristic

The benchmark runner derives coarse fit labels from the deterministic match result for reporting only:

- `strong`: score >= 80 and no unsupported-claim, missing-required-skill, or seniority blockers
- `partial`: score >= 40 without missing-required-skill or seniority blockers
- `poor`: everything else

This heuristic is a benchmark convenience, not an API contract. If score interpretation changes later, update the runner, fixtures, checked-in artifacts, and docs together.

## Benchmark Expansion Pattern

When adding new benchmark cases:

1. add a new resume/JD fixture pair under `data/samples/` or a curated `dataset/` sample path
2. add the expected outcome JSON under `data/eval/`
3. add the case to the relevant manifest
4. add or update tests if the new case represents a bug fix or newly supported behavior

Keep fixtures human-readable and small enough to review comfortably.

When changing scoring or ranking logic:

1. update the relevant expected JSON fixtures
2. run the three evaluation runners
3. refresh the baseline artifacts only when the behavior change is intentional
4. write a labeled snapshot when you want a comparable review bundle without replacing baseline
