"""
Step 6 — Vector Database (ChromaDB)
Persists embeddings, text, and full chunk metadata.
Collection: hvac_manual
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

COLLECTION_NAME = "hvac_manual"


def build_vector_db(
    chunks: list[dict[str, Any]],
    db_dir: Path,
    reset: bool = False,
) -> None:
    """
    Upsert *chunks* (with embeddings) into a persistent ChromaDB collection.

    Parameters
    ----------
    chunks   : chunk dicts that already have an 'embedding' key
    db_dir   : directory where ChromaDB will persist its files
    reset    : if True, delete and recreate the collection before inserting
    """
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=str(db_dir),
        settings=Settings(anonymized_telemetry=False),
    )

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info("Dropped existing collection '%s'", COLLECTION_NAME)
        except Exception:
            pass  # collection didn't exist yet

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # ChromaDB upsert in batches to avoid large payloads
    BATCH_SIZE = 256
    total = len(chunks)
    inserted = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunks[batch_start : batch_start + BATCH_SIZE]

        ids         = [c["chunk_id"]  for c in batch]
        embeddings  = [c["embedding"] for c in batch]
        documents   = [c.get("text", "") for c in batch]
        metadatas   = [_safe_metadata(c) for c in batch]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        inserted += len(batch)
        logger.info("Upserted %d / %d chunks", inserted, total)

    logger.info(
        "ChromaDB collection '%s' now has %d documents",
        COLLECTION_NAME,
        collection.count(),
    )


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

_ALLOWED_META_TYPES = (str, int, float, bool)


def _safe_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    """
    ChromaDB metadata values must be str | int | float | bool.
    Lists (e.g. linked_images) are JSON-serialised to strings.
    The 'embedding' key is excluded (stored natively).
    """
    import json

    skip_keys = {"embedding", "text", "table_html"}
    meta: dict[str, Any] = {}

    for key, val in chunk.items():
        if key in skip_keys:
            continue
        if isinstance(val, _ALLOWED_META_TYPES):
            meta[key] = val
        elif val is None:
            meta[key] = ""         # Chroma doesn't accept None
        elif isinstance(val, list):
            meta[key] = json.dumps(val)
        else:
            meta[key] = str(val)

    return meta
