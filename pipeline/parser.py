"""
Step 1 — PDF Parsing
Primary:  unstructured  (rich element types, heading detection)
Fallback: PyMuPDF       (if unstructured fails or is not installed)
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def parse_pdf(pdf_path: Path, output_dir: Path) -> list[dict[str, Any]]:
    """
    Parse *pdf_path* and return a list of element dicts.
    Also writes parsed_elements.json into *output_dir*.
    """
    try:
        elements = _parse_with_unstructured(pdf_path)
        method = "unstructured"
    except Exception as exc:
        logger.warning("unstructured failed (%s); falling back to PyMuPDF", exc)
        elements = _parse_with_pymupdf(pdf_path)
        method = "pymupdf"

    logger.info("Parsed %d elements via %s", len(elements), method)

    out_file = output_dir / "parsed_elements.json"
    out_file.write_text(json.dumps(elements, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved parsed elements → %s", out_file)

    return elements


# ──────────────────────────────────────────────
# Parsing backends
# ──────────────────────────────────────────────

def _parse_with_unstructured(pdf_path: Path) -> list[dict[str, Any]]:
    from unstructured.partition.pdf import partition_pdf

    raw = partition_pdf(
        filename=str(pdf_path),
        strategy="fast",            # no OCR/Tesseract needed for text-based PDFs
        infer_table_structure=True,
        include_page_breaks=True,
    )

    elements: list[dict[str, Any]] = []
    for el in raw:
        meta = el.metadata if el.metadata else {}
        page = getattr(meta, "page_number", None)
        element_type = type(el).__name__   # Title, NarrativeText, Table, Image, …

        entry: dict[str, Any] = {
            "element_id": el.id if hasattr(el, "id") else None,
            "type": element_type,
            "text": str(el),
            "page": page,
        }

        # Table: also capture HTML representation when available
        if element_type == "Table":
            entry["table_html"] = getattr(el.metadata, "text_as_html", None)

        # Image: record coordinates / filename if present
        if element_type == "Image":
            entry["image_path"] = getattr(el.metadata, "filename", None)

        elements.append(entry)

    return elements


def _parse_with_pymupdf(pdf_path: Path) -> list[dict[str, Any]]:
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    elements: list[dict[str, Any]] = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            btype = block.get("type")

            if btype == 0:  # text block
                full_text = ""
                is_heading = False
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        full_text += span["text"] + " "
                        # Heuristic: large/bold font → likely a heading
                        flags = span.get("flags", 0)
                        size = span.get("size", 0)
                        if (flags & 16) or size >= 14:   # bold flag or large size
                            is_heading = True

                text = full_text.strip()
                if not text:
                    continue

                elements.append({
                    "element_id": None,
                    "type": "Title" if is_heading else "NarrativeText",
                    "text": text,
                    "page": page_num,
                })

            elif btype == 1:  # image block
                elements.append({
                    "element_id": None,
                    "type": "Image",
                    "text": "",
                    "page": page_num,
                    "image_path": None,
                })

    doc.close()
    return elements