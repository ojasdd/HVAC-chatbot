"""
HVAC Manual RAG Pipeline
Runs: PDF → parse → chunk → images → embeddings → ChromaDB
"""

import argparse
import sys
from pathlib import Path

from pipeline.parser import parse_pdf
from pipeline.chunker import build_chunks
from pipeline.image_extractor import extract_images
from pipeline.embedder import generate_embeddings
from pipeline.vector_store import build_vector_db


def run_pipeline(pdf_path: str, reset_db: bool = False):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        sys.exit(1)

    base_dir = Path(__file__).parent
    parsed_dir = base_dir / "parsed"
    images_dir = base_dir / "images"
    vector_db_dir = base_dir / "vector_db"

    for d in [parsed_dir, images_dir, vector_db_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  HVAC RAG Ingestion Pipeline")
    print("=" * 60)

    # Step 1 — Parse PDF
    print("\n[1/5] Parsing PDF …")
    elements = parse_pdf(pdf_path, parsed_dir)
    print(f"      → {len(elements)} elements extracted")

    # Step 2 — Extract images
    print("\n[2/5] Extracting images …")
    image_meta = extract_images(pdf_path, images_dir)
    print(f"      → {len(image_meta)} images saved")

    # Step 3 — Build structured chunks
    print("\n[3/5] Building chunks …")
    chunks = build_chunks(elements, image_meta, parsed_dir)
    print(f"      → {len(chunks)} chunks created")

    # Step 4 — Generate embeddings
    print("\n[4/5] Generating embeddings …")
    chunks_with_embeddings = generate_embeddings(chunks)
    print(f"      → embeddings attached to {len(chunks_with_embeddings)} chunks")

    # Step 5 — Persist to ChromaDB
    print("\n[5/5] Building vector database …")
    build_vector_db(chunks_with_embeddings, vector_db_dir, reset=reset_db)
    print(f"      → vector DB saved to {vector_db_dir}")

    print("\n" + "=" * 60)
    print("  Pipeline complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HVAC Manual RAG ingestion pipeline")
    parser.add_argument("pdf", help="Path to the HVAC manual PDF")
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Drop and recreate the ChromaDB collection",
    )
    args = parser.parse_args()
    run_pipeline(args.pdf, reset_db=args.reset_db)
