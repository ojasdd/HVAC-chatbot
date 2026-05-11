"""
chat.py — Interactive terminal chat for the HVAC RAG system.

Usage:
    python chat.py

Commands inside the chat:
    /quit or /exit   — exit
    /top <n>         — change how many chunks to retrieve (default 5)
    /type <t>        — filter by chunk type: section | table | troubleshooting | all
    /sources         — show full source details for last answer
    /help            — show commands
"""

import sys
from pathlib import Path

# ── ensure project root is on sys.path ──────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from pipeline.retriever     import retrieve
from pipeline.prompt_builder import build_prompt
from pipeline.answerer       import stream_answer

DB_DIR = ROOT / "vector_db"

# ── ANSI colours (gracefully disabled on Windows if needed) ──────
try:
    import colorama
    colorama.init()
    C_RESET  = "\033[0m"
    C_BOLD   = "\033[1m"
    C_CYAN   = "\033[96m"
    C_YELLOW = "\033[93m"
    C_GREEN  = "\033[92m"
    C_GREY   = "\033[90m"
    C_RED    = "\033[91m"
except ImportError:
    C_RESET = C_BOLD = C_CYAN = C_YELLOW = C_GREEN = C_GREY = C_RED = ""


def print_banner():
    print(f"""
{C_CYAN}{C_BOLD}╔══════════════════════════════════════════════╗
║       HVAC Manual Assistant  (Qwen2.5 3B)    ║
║       Type /help for commands                ║
╚══════════════════════════════════════════════╝{C_RESET}
""")


def print_sources(chunks):
    print(f"\n{C_GREY}── Sources ─────────────────────────────────────")
    for i, c in enumerate(chunks, 1):
        label = c.get("subsection") or c.get("section") or "—"
        page  = c.get("page") or "?"
        ctype = c.get("chunk_type", "")
        imgs  = c.get("linked_images", [])
        img_str = f"  📷 {', '.join(imgs)}" if imgs else ""
        dist  = c.get("distance", "")
        print(f"  [{i}] {label}  |  p.{page}  |  {ctype}  |  score={dist}{img_str}")
    print(f"────────────────────────────────────────────{C_RESET}\n")


def print_help():
    print(f"""
{C_YELLOW}Commands:
  /quit  /exit        Exit the chat
  /top <n>            Set number of retrieved chunks (e.g. /top 8)
  /type <t>           Filter chunk type: section | table | troubleshooting | all
  /sources            Show sources from the last answer
  /help               Show this message{C_RESET}
""")


def main():
    print_banner()

    top_k       = 5
    chunk_type  = None   # None = no filter
    last_chunks = []

    while True:
        try:
            raw = input(f"{C_BOLD}{C_GREEN}You:{C_RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        # ── commands ─────────────────────────────────────────────
        if raw.lower() in ("/quit", "/exit"):
            print("Goodbye!")
            break

        if raw.lower() == "/help":
            print_help()
            continue

        if raw.lower() == "/sources":
            if last_chunks:
                print_sources(last_chunks)
            else:
                print(f"{C_GREY}No answer yet.{C_RESET}")
            continue

        if raw.lower().startswith("/top "):
            try:
                top_k = int(raw.split()[1])
                print(f"{C_GREY}Retrieving top {top_k} chunks.{C_RESET}")
            except (IndexError, ValueError):
                print(f"{C_RED}Usage: /top <number>{C_RESET}")
            continue

        if raw.lower().startswith("/type "):
            t = raw.split()[1].lower()
            chunk_type = None if t == "all" else t
            label = chunk_type or "all"
            print(f"{C_GREY}Chunk type filter: {label}{C_RESET}")
            continue

        # ── normal query ─────────────────────────────────────────
        try:
            chunks = retrieve(raw, DB_DIR, k=top_k, chunk_type=chunk_type)
        except Exception as exc:
            print(f"{C_RED}Retrieval error: {exc}{C_RESET}")
            continue

        last_chunks = chunks

        if not chunks:
            print(f"{C_GREY}No relevant chunks found.{C_RESET}\n")
            continue

        messages = build_prompt(raw, chunks)

        print(f"\n{C_CYAN}{C_BOLD}Assistant:{C_RESET} ", end="", flush=True)
        try:
            for token in stream_answer(messages):
                print(token, end="", flush=True)
        except RuntimeError as exc:
            print(f"\n{C_RED}{exc}{C_RESET}")
            continue

        print()          # newline after streamed answer
        print_sources(chunks)


if __name__ == "__main__":
    main()
