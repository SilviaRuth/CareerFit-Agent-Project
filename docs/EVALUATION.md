# Evaluation Guide

This guide documents the offline evaluation workflow for CareerFit Agent.

## Purpose

The checked-in evaluation layer turns fixtures into repeatable offline checks for:

- fit-label stability
- blocker-flag stability
- required/preferred match recall
- top-gap coverage
- extraction confidence and field-presence stability
- multimodal ingestion diagnostics and needs-OCR guardrails
- multi-resume ranking stability
- recommendation usefulness and hallucination rate
- snapshot-friendly regression review

## Current Checked-In Coverage

- 15 match benchmark cases
- 13 extraction benchmark cases
- 2 multimodal ingestion-quality cases
- 3 multi-resume comparison scenarios
- 3 recommendation acceptance cases
- baseline and snapshot-capable report artifacts

## Run The Match Benchmark

```bash
./.venv/Scripts/python.exe -m app.evaluation.benchmark_runner
```

## Run The Extraction Benchmark

```bash
./.venv/Scripts/python.exe -m app.evaluation.extraction_runner
```

## Run The Multimodal Ingestion Benchmark

```bash
./.venv/Scripts/python.exe -m app.evaluation.multimodal_runner
```

The multimodal benchmark is separate from the checked-in baseline artifact
bundle. It verifies document-quality behavior before OCR is added:

- needs-OCR detection accuracy
- diagnostic coverage
- unsupported-reason coverage
- low-confidence guardrail accuracy

## Run The Comparison Benchmark

```bash
./.venv/Scripts/python.exe -m app.evaluation.comparison_runner
```

## Run The Recommendation Benchmark

```bash
./.venv/Scripts/python.exe -m app.evaluation.recommendation_runner
```

The recommendation benchmark checks grounded M5 outputs for:

- usefulness accuracy
- grounding accuracy
- blocker-guardrail accuracy
- hallucination rate

## Refresh Reviewable Artifacts

```bash
./.venv/Scripts/python.exe -m app.evaluation.artifact_writer
./.venv/Scripts/python.exe -m app.evaluation.artifact_writer --snapshot-label m5-review
```

Each artifact set includes:

- `benchmark_report.json`
- `extraction_report.json`
- `comparison_report.json`
- `recommendation_report.json`
- `artifact_manifest.json`
- `summary.md`

Snapshot runs also write `snapshot_comparison.json` when the checked-in baseline is available.

## Benchmark Expansion Pattern

When adding new benchmark cases:

1. add or update the relevant sample fixture under `data/samples/`
2. add the expected outcome JSON under `data/eval/`
3. add the case to the relevant manifest
4. add or update tests if the case represents a bug fix or newly supported behavior

For multimodal ingestion cases, use `data/eval/multimodal_manifest.json` plus
small reviewable fixtures under `data/samples/`. Expected outputs should focus on
warning codes, unsupported reasons, parser confidence, and extraction-complete
status so document quality stays separate from match quality.

Keep fixtures human-readable and small enough to review comfortably.

When changing scoring, ranking, or recommendation behavior:

1. update the relevant expected JSON fixtures
2. run the affected evaluation runner or the full artifact writer
3. refresh the baseline artifacts only when the behavior change is intentional
4. write a labeled snapshot when you want a comparable review bundle without replacing baseline
