# Demo Guide

Use this guide to show the project to a reviewer without private context.

## Demo Story

CareerFit Agent is a schema-first backend that turns a resume and job
description into explainable, evidence-linked career fit output. The core value
is not a black-box prediction; it is a reviewable pipeline:

1. parse resume and JD text into explicit schemas
2. match required and preferred requirements with deterministic rules
3. expose blockers, gaps, strengths, and evidence spans
4. generate bounded guidance only after parse and match artifacts exist
5. preserve regression evidence through checked-in benchmark reports

## Five-Minute Path

1. Start the backend:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

2. Verify health:

```bash
curl http://127.0.0.1:8000/health
```

3. Run the synthetic match request:

```bash
curl -s http://127.0.0.1:8000/match \
  -H "Content-Type: application/json" \
  --data @docs/examples/match_request.json
```

4. Point out these response fields:

- `overall_score`
- `required_matches`
- `preferred_matches`
- `gaps`
- `blocker_flags`
- `evidence_spans`
- `evidence_summary`
- `adaptation_summary`

5. Open the benchmark summary:

```bash
cat data/eval/reports/baseline/summary.md
```

## Docker Demo Path

```bash
docker build -t careerfit-agent .
docker run --rm --env-file .env.example -p 8000:8000 careerfit-agent
```

Then repeat the health and `/match` requests above.

## Reviewer Talking Points

- The backend is deterministic by default and has no required external service.
- The optional LLM advisory layer is disabled by default and structurally
  separate from deterministic results.
- Every match explanation is grounded in parsed resume/JD evidence.
- Benchmark artifacts are checked into `data/eval/reports/baseline/`.
- Multimodal support currently means explicit image/scanned-PDF diagnostics, not
  OCR runtime support.
- Candidate profile memory is request-scoped and non-persistent.

## Limitations To State Clearly

- This is not a hiring decision system.
- The matcher uses a fixed capability vocabulary and rule-based scoring.
- OCR, persistent storage, frontend UI, vector search, background jobs, and
  deployed hosting are outside this release.
- Synthetic examples should be used for demos; real resumes and JDs may contain
  sensitive personal or company information.
