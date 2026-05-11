"""
Step 5 — Embedding Generation
Model: BAAI/bge-small-en-v1.5 (via sentence-transformers)
  • Strong retrieval performance
  • ~33M params — laptop-friendly
  • 512-token context window

BGE models benefit from a query-prefix at retrieval time, but documents
are embedded as-is (no prefix needed for indexing).
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-small-en-v1.5"
BATCH_SIZE = 64          # tune down if you hit OOM
NORMALIZE = True         # cosine similarity via dot-product after normalization


def generate_embeddings(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Attach an 'embedding' key (list[float]) to every chunk in-place.
    Returns the same list for convenience.
    """
    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model: %s", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)

    texts = [_text_for_embedding(c) for c in chunks]
    total = len(texts)
    logger.info("Encoding %d chunks in batches of %d …", total, BATCH_SIZE)

    all_embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=NORMALIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    for chunk, emb in zip(chunks, all_embeddings):
        chunk["embedding"] = emb.tolist()

    logger.info("Embeddings attached to %d chunks (dim=%d)", total, len(chunks[0]["embedding"]))
    return chunks


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _text_for_embedding(chunk: dict[str, Any]) -> str:
    """
    Construct the string to embed.
    We prepend section/subsection as context so the vector captures
    structural position, not just raw text.
    """
    parts: list[str] = []

    section = chunk.get("section")
    subsection = chunk.get("subsection")
    chunk_type = chunk.get("chunk_type", "")

    if subsection and subsection != section:
        parts.append(subsection)
    elif section:
        parts.append(section)

    if chunk_type == "table":
        parts.append("[TABLE]")

    text = chunk.get("text", "").strip()
    if text:
        parts.append(text)

    return " ".join(parts)
