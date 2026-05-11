"""
Retriever — embeds the user query and fetches top-K chunks from ChromaDB.

BGE models require a query prefix at retrieval time (not at index time):
  "Represent this sentence for searching relevant passages: <query>"
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MODEL_NAME   = "BAAI/bge-small-en-v1.5"
COLLECTION   = "hvac_manual"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def retrieve(
    query: str,
    db_dir: Path,
    k: int = 5,
    chunk_type: str | None = None,   # "section" | "table" | "troubleshooting" | None
) -> list[dict[str, Any]]:
    """
    Embed *query* and return the top-*k* matching chunks from ChromaDB.
    Each result dict contains: text, metadata, distance.
    """
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer

    # ── embed query ───────────────────────────────────────────────
    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode(
        QUERY_PREFIX + query,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).tolist()

    # ── query ChromaDB ────────────────────────────────────────────
    client = chromadb.PersistentClient(
        path=str(db_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_collection(COLLECTION)

    where_filter = {"chunk_type": chunk_type} if chunk_type else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    # ── flatten into list of dicts ────────────────────────────────
    chunks: list[dict[str, Any]] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # linked_images was stored as a JSON string
        linked_images = meta.get("linked_images", "[]")
        if isinstance(linked_images, str):
            try:
                linked_images = json.loads(linked_images)
            except Exception:
                linked_images = []

        chunks.append({
            "chunk_id":     meta.get("chunk_id", ""),
            "chunk_type":   meta.get("chunk_type", ""),
            "section":      meta.get("section", ""),
            "subsection":   meta.get("subsection", ""),
            "page":         meta.get("page", ""),
            "linked_images": linked_images,
            "text":         doc,
            "distance":     round(dist, 4),
        })

    return chunks
