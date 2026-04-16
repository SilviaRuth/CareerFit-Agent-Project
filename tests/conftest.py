"""Shared test helpers for fixture-backed Milestone 1 tests."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from docx import Document

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "data" / "samples"
EVAL_DIR = REPO_ROOT / "data" / "eval"


def load_sample(name: str) -> str:
    """Load a sample text fixture by filename."""
    return (SAMPLES_DIR / name).read_text(encoding="utf-8")


def load_eval(name: str) -> dict:
    """Load a JSON evaluation fixture by filename."""
    return json.loads((EVAL_DIR / name).read_text(encoding="utf-8"))


def build_docx_bytes(paragraphs: list[str]) -> bytes:
    """Create a small DOCX document for ingestion tests."""
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def build_pdf_bytes(lines: list[str]) -> bytes:
    """Create a minimal text PDF for ingestion tests without OCR."""
    content_lines = ["BT", "/F1 12 Tf", "72 720 Td"]
    for index, line in enumerate(lines):
        escaped_line = (
            line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        )
        if index > 0:
            content_lines.append("0 -16 Td")
        content_lines.append(f"({escaped_line}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("utf-8")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("ascii")
    )
    return bytes(pdf)
