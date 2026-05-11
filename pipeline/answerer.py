"""
Answerer — sends the prompt to Ollama (Qwen2.5 3B) and streams the reply.

Requires Ollama running locally:
  ollama serve          (if not already running as a service)
  ollama pull qwen2.5:3b
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Iterator

logger = logging.getLogger(__name__)

OLLAMA_URL  = "http://localhost:11434/api/chat"
MODEL_NAME  = "qwen2.5:3b"


def stream_answer(messages: list[dict[str, str]]) -> Iterator[str]:
    """
    Stream token chunks from Ollama.
    Yields string fragments as they arrive.
    Raises RuntimeError if Ollama is unreachable.
    """
    payload = json.dumps({
        "model":    MODEL_NAME,
        "messages": messages,
        "stream":   True,
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                token = obj.get("message", {}).get("content", "")
                if token:
                    yield token

                if obj.get("done"):
                    break

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach Ollama at {OLLAMA_URL}.\n"
            "Make sure Ollama is running:  ollama serve\n"
            f"And the model is pulled:      ollama pull {MODEL_NAME}\n"
            f"Original error: {exc}"
        ) from exc


def get_answer(messages: list[dict[str, str]]) -> str:
    """Non-streaming version — collects the full reply and returns it."""
    return "".join(stream_answer(messages))
