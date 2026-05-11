"""
Prompt Builder — assembles the system + user prompt from retrieved chunks.
"""

from typing import Any

SYSTEM_PROMPT = """You are an expert HVAC technician assistant. \
Answer questions strictly based on the provided manual excerpts. \
Be concise and technical. If the answer is not in the context, say so — do not guess. \
When relevant, mention the section or page number from the manual."""


def build_prompt(query: str, chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """
    Returns an OpenAI-style messages list ready for the Ollama /api/chat endpoint.
    """
    context_blocks: list[str] = []

    for i, chunk in enumerate(chunks, start=1):
        header_parts = [f"[{i}]"]
        if chunk.get("subsection"):
            header_parts.append(chunk["subsection"])
        elif chunk.get("section"):
            header_parts.append(chunk["section"])
        if chunk.get("page"):
            header_parts.append(f"p.{chunk['page']}")
        if chunk.get("chunk_type") == "table":
            header_parts.append("(table)")
        if chunk.get("chunk_type") == "troubleshooting":
            header_parts.append("(troubleshooting)")

        header = " | ".join(header_parts)
        context_blocks.append(f"{header}\n{chunk['text'].strip()}")

    context_text = "\n\n---\n\n".join(context_blocks)

    user_message = (
        f"Use the following excerpts from the HVAC manual to answer the question.\n\n"
        f"{context_text}\n\n"
        f"Question: {query}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]
