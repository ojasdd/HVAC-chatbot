"""
Step 2 — Image Extraction
Uses PyMuPDF to pull every embedded raster image out of the PDF.
Saves PNGs to the images/ directory and returns structured metadata.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Minimum pixel area to skip tiny icons / bullets
MIN_PIXELS = 100 * 100


def extract_images(pdf_path: Path, images_dir: Path) -> list[dict[str, Any]]:
    """
    Extract images from *pdf_path*, save to *images_dir*.
    Returns a list of image-metadata dicts; also writes images_metadata.json.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    metadata: list[dict[str, Any]] = []
    img_counter = 0

    for page_num, page in enumerate(doc, start=1):
        image_list = page.get_images(full=True)
        for img_info in image_list:
            xref = img_info[0]
            base_image = doc.extract_image(xref)

            width = base_image.get("width", 0)
            height = base_image.get("height", 0)
            if width * height < MIN_PIXELS:
                logger.debug("Skipping tiny image xref=%d (%dx%d)", xref, width, height)
                continue

            img_counter += 1
            img_id = f"img_{img_counter:03d}"
            ext = base_image.get("ext", "png")
            filename = f"{img_id}.{ext}"
            save_path = images_dir / filename

            save_path.write_bytes(base_image["image"])
            logger.debug("Saved %s (page %d, %dx%d)", filename, page_num, width, height)

            meta_entry: dict[str, Any] = {
                "image_id": img_id,
                "page": page_num,
                "path": str(save_path),
                "filename": filename,
                "width": width,
                "height": height,
                "colorspace": base_image.get("colorspace", None),
                "caption": None,    # placeholder — captioning not in scope yet
            }
            metadata.append(meta_entry)

    doc.close()

    # Persist metadata alongside images
    meta_file = images_dir / "images_metadata.json"
    meta_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    logger.info("Extracted %d images → %s", len(metadata), images_dir)

    return metadata
