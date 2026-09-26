"""Frozen outputs for deterministic Sources handlers (#8524).

Calls the handlers in process against the local ``data/sources.db`` opened
read-only. ``query_pravopys`` is not in this set: ``pravopys_lookup`` fetches
live HTML from pravopys.online. The nearest offline dictionary handler is
``search_style_guide``.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCES_SERVER_PATH = PROJECT_ROOT / ".mcp" / "servers" / "sources" / "server.py"
EXPECTED_PATH = Path(__file__).with_name("sources_golden_set.json")

# Fixed input. Every batch stays at or under the 500-word inspect cap.
GOLDEN_WORDS: tuple[str, ...] = (
    "мова",
    "вода",
    "дім",
    "книга",
    "школа",
    "учитель",
    "учень",
    "стіл",
    "вікно",
    "рука",
    "день",
    "ніч",
    "місто",
    "село",
    "хліб",
    "молоко",
    "сонце",
    "земля",
    "друг",
    "робота",
    "час",
)


def load_server():
    spec = importlib.util.spec_from_file_location("sources_server_golden", SOURCES_SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCES_SERVER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_golden"] = module
    spec.loader.exec_module(module)
    return module


def _present(result: Any) -> dict[str, Any]:
    if isinstance(result, tuple):
        content, outcome = result
        encoded = json.dumps(outcome, ensure_ascii=False, sort_keys=True, default=str)
        return {"text": content[0].text, "outcome": json.loads(encoded)}
    return {"text": result[0].text}


async def _capture(server: Any) -> dict[str, Any]:
    from wiki.sources_db import SOURCES_DB_PATH, using_connection

    if not SOURCES_DB_PATH.is_file():
        raise FileNotFoundError(SOURCES_DB_PATH)
    uri = f"file:{SOURCES_DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    words = list(GOLDEN_WORDS)
    try:
        with using_connection(conn):
            per_word: dict[str, dict[str, Any]] = {}
            for word in words:
                per_word[word] = {
                    "verify_word": _present(await server.handle_verify_word({"word": word})),
                    "verify_lemma": _present(await server.handle_verify_lemma({"lemma": word})),
                    "inspect_word": _present(await server.handle_inspect_word({"word": word})),
                    "query_cefr_level": _present(
                        await server.handle_dict_search({"query": word, "limit": 1}, "puls_cefr", "PULS CEFR")
                    ),
                    "search_definitions": _present(
                        await server.handle_dict_search({"query": word, "limit": 1}, "sum11", "СУМ-11")
                    ),
                    "search_style_guide": _present(
                        await server.handle_dict_search(
                            {"query": word, "limit": 1},
                            "style_guide",
                            "Антоненко-Давидович",
                        )
                    ),
                }
            batch = {
                "verify_words": _present(await server.handle_verify_words({"words": words})),
                "inspect_words": _present(await server.handle_inspect_words({"words": words})),
            }
    finally:
        conn.close()
    return {
        "words": words,
        "query_pravopys": (
            "omitted: pravopys_lookup fetches live pravopys.online HTML; "
            "search_style_guide is the nearest offline dictionary handler"
        ),
        "per_word": per_word,
        "batch": batch,
    }


def capture() -> dict[str, Any]:
    server = load_server()
    return asyncio.run(_capture(server))


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


if __name__ == "__main__":
    EXPECTED_PATH.write_bytes(canonical_bytes(capture()))
    print(EXPECTED_PATH)
