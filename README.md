# CareerFit Agent

Deterministic backend MVP for explainable resume-to-JD matching.

## Milestone 1 Scope

- Backend only
- Plain-text resume and JD inputs
- Deterministic extraction and rule-based matching
- Evidence-linked JSON output

## Local Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run The App

```powershell
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

The API exposes:

- `GET /health`
- `POST /match`

## Run Tests

```powershell
.venv\Scripts\Activate.ps1
python -m pytest -q
```

## Inspect Fixtures

- Sample resumes and JDs: `data/samples/`
- Expected outcomes: `data/eval/`

These fixtures define the constrained Milestone 1 parsing and matching behavior.
