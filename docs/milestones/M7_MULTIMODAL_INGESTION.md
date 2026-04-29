# M7: Multimodal Ingestion Foundation

## Goal

Prepare ingestion for scanned PDFs, images, and richer document diagnostics while keeping matching and recommendation behavior deterministic and auditable.

## Allowed Scope

- Extend document input and normalized document contracts.
- Add page, segment, diagnostic, warning, and confidence fields where needed.
- Detect unsupported image/scanned-PDF cases clearly.
- Add OCR adapter interfaces and fixtures before adding heavy OCR runtime dependencies.
- Add multimodal ingestion tests and evaluation metrics for document quality.
- Document local and CI implications for future OCR dependencies.

## Out Of Scope

- LLM-assisted generation.
- Frontend workflow UI.
- Persistent storage.
- Hidden OCR fallback that bypasses confidence and warning fields.
- Changes to match scoring, blocker flags, or fit labels.
- Benchmark baseline refresh unless explicitly approved.

## Required Invariants

- Existing text, TXT, PDF, and DOCX behavior remains compatible.
- Low-confidence or unsupported multimodal input must not look like clean extracted text.
- Parser quality must stay distinguishable from matcher quality in reports.

## Completion Signal

- Multimodal document contracts are ready.
- Unsupported and needs-OCR cases are explicit.
- Evaluation can tell whether failures come from ingestion/OCR quality or matching logic.
