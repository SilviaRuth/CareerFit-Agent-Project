# Parse API Guide

This guide documents the Milestone 2 parsing and ingestion behavior for CareerFit Agent.

## Purpose

The parse layer moves the system from fixture-only text parsing to bounded real-world ingestion while keeping the same trust model:

- schema-first
- deterministic
- modular
- evidence-linked
- warning-aware

The parse endpoints do not generate new claims. They only ingest, normalize, and extract structured resume or JD schemas.

## Endpoints

### `POST /parse/resume`

Parse resume content into a `ResumeSchema` plus ingestion and extraction metadata.

### `POST /parse/jd`

Parse job-description content into a `JDSchema` plus ingestion and extraction metadata.

## Supported Inputs

Both endpoints support:

- JSON text input
- multipart text input
- multipart file upload

Supported file types:

- `.txt`
- `.pdf`
- `.docx`

Non-goals and current limits:

- no OCR
- no scanned image parsing
- no layout-aware table extraction
- no URL scraping
- no freeform generation

## Text Example

```bash
curl -X POST http://127.0.0.1:8000/parse/resume \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Alex Chen\n\nSummary\nBackend engineer with 6 years of experience building Python APIs.\n\nSkills\nPython, FastAPI, PostgreSQL",
    "source_name": "resume_text_input"
  }'
```

## File Example

```bash
curl -X POST http://127.0.0.1:8000/parse/jd \
  -F "file=@data/samples/strong_fit_jd.txt;type=text/plain"
```

## Response Shape

Both parse endpoints return the same outer envelope, with `schema` set to either `ResumeSchema` or `JDSchema`.

```json
{
  "source_type": "file",
  "source_name": "resume.docx",
  "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "raw_text": "Original extracted text...",
  "cleaned_text": "Normalized text...",
  "schema": {},
  "warnings": [
    {
      "warning_code": "section_header_alias_used",
      "message": "Recognized section header variant 'Professional Summary' as 'Summary'.",
      "section": "summary",
      "severity": "info",
      "source": "extraction"
    }
  ],
  "parser_confidence": {
    "score": 0.82,
    "level": "medium",
    "extraction_complete": true,
    "factors": [
      "info:section_header_alias_used"
    ]
  },
  "unsupported_segments": [
    {
      "text": "Maintainer for an internal tooling package.",
      "section": "Open Source",
      "reason": "unsupported_section_header",
      "source": "extraction"
    }
  ]
}
```

## Key Fields

### `raw_text`

The text as ingested from the request body or uploaded file before normalization.

### `cleaned_text`

Normalized text used by extraction. This may include:

- bullet normalization
- Unicode punctuation normalization
- colon-header normalization
- blank-line collapsing

### `schema`

Structured extracted output:

- resume parsing returns `candidate_name`, `summary`, `skills`, `experience_items`, `project_items`, `education_items`, `evidence_spans`, and related metadata
- JD parsing returns `job_title`, `company`, `required_requirements`, `preferred_requirements`, `responsibilities`, `education_requirements`, `seniority_hint`, `domain_hint`, `evidence_spans`, and related metadata

### `warnings`

Structured diagnostics emitted during:

- ingestion
- normalization
- extraction

Each warning includes:

- `warning_code`
- `message`
- `section`
- `severity`
- `source`

### `parser_confidence`

Bounded confidence metadata derived from parse completeness and warnings.

Fields:

- `score`: numeric value from `0.0` to `1.0`
- `level`: `high`, `medium`, or `low`
- `extraction_complete`: whether the minimum expected structure was found
- `factors`: compact reasoning trail for the confidence score

### `unsupported_segments`

Text blocks the bounded parser could not safely map into supported sections.

## Example Warning Patterns

Common warning codes include:

- `txt_decode_fallback`
- `pdf_page_without_text`
- `docx_tables_ignored`
- `unicode_punctuation_normalized`
- `bullet_format_normalized`
- `colon_headers_normalized`
- `blank_lines_collapsed`
- `section_header_alias_used`
- `unsupported_section_header`
- `missing_section`
- `missing_candidate_name`
- `missing_company_name`

The exact warnings depend on the input quality and document shape.

## Header Alias Behavior

The parser supports realistic section variants such as:

- `Professional Summary` -> `Summary`
- `Core Competencies` -> `Skills`
- `Work History` -> `Experience`
- `What You'll Do` -> `Responsibilities`
- `Must Have` -> `Required`
- `Nice to Have` -> `Preferred`

Unsupported headers are preserved as warnings plus `unsupported_segments` rather than being silently dropped.

## Reliability Model

The parse layer is designed for bounded extraction, not perfect document understanding.

Safe behavior includes:

- returning partial schemas when possible
- surfacing warnings instead of guessing silently
- lowering parser confidence when required structure is missing
- preserving unsupported content separately

The parse layer does not:

- infer missing achievements
- invent missing sections
- upgrade weak evidence into stronger claims
- claim OCR support where none exists
