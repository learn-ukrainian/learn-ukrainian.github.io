"""Frozen outputs for deterministic Sources handlers (#8524).

Calls the handlers in process against the local ``data/sources.db`` and
``data/vesum.db`` opened read-only.

Determinism & Crawl Isolation:
The ULIF crawler (`fetch_ulif_homonyms` / `import_ulif_dump`) writes
continuously to ``spellings``, ``responses``, ``meta``, ``register_pages``,
``register_rows``, and ``ulif_dictua_*`` tables.
To remain deterministic while the crawl runs, this golden set is restricted
strictly to tools and inputs whose source tables are never written by the crawl:
- `verify_word`, `verify_words`, `verify_lemma`, `inspect_word`, `inspect_words`:
  read-only from static `data/vesum.db` (`forms_all`, `form_markers`).
- `query_cefr_level`: read-only from static `data/sources.db` table `puls_cefr`.
- `search_definitions`: read-only from static `data/sources.db` table `sum11`.
- `search_style_guide`: read-only from static `data/sources.db` table `style_guide`.

Tools backed by tables modified by the crawl (e.g. `query_ulif*`) or external
network fetches (e.g. `query_pravopys` which scrapes pravopys.online) are
deliberately excluded.

Copyrighted dictionary prose is not stored. ``sum11`` and ``style_guide``
keep a sha256 of the entry text, its length, the headword, and the hit
count. PULS and VESUM-derived output stay, minus SQLite row ids and the
VESUM ``source_version`` hash, which change on a legitimate rebuild.
Style-guide probes are headwords, so each hit is the entry about that
probe rather than a body-text mention of an unrelated word.
"""

from __future__ import annotations

import asyncio
import hashlib
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

# Exact style-guide headwords. A common noun such as "вода" matches an
# unrelated entry through body text; these probes match the headword.
STYLE_GUIDE_PROBES: tuple[str, ...] = (
    "Міроприємство",
    "Книга й книжка",
    "Дружний і дружній",
    "Робочий і робітничий",
    "Банкет чи бенкет",
    "Навшпиньках чи навшпиньки",
    "Приймати чи сприймати",
    "Госпіталь чи шпиталь",
)

_DICTIONARY_FINGERPRINT_KEYS = ("headword", "hit_count", "text_length", "text_sha256")
_DROP_KEYS = frozenset({
    "entry_id",
    "source_version",
    "canonical_jsonl_sha256",
    "evidence_identifiers",
})


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


def _dictionary_body(hit: dict[str, Any]) -> str:
    for key in ("text", "definition", "excerpt_full"):
        value = hit.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def fingerprint_dictionary_result(presented: dict[str, Any]) -> dict[str, Any]:
    """sha256, length, headword, and hit count. No dictionary prose."""
    outcome = presented.get("outcome") if isinstance(presented, dict) else None
    hits = outcome.get("hits") if isinstance(outcome, dict) else None
    if not isinstance(hits, list):
        hits = []
    bodies: list[str] = []
    headword = ""
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        if not headword:
            word = hit.get("word", hit.get("words", ""))
            headword = word if isinstance(word, str) else str(word or "")
        bodies.append(_dictionary_body(hit))
    text = "\n".join(bodies)
    return {
        "headword": headword,
        "hit_count": len([hit for hit in hits if isinstance(hit, dict)]),
        "text_length": len(text),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def _strip_embedded_payload(text: str) -> str:
    marker = "Raw payload:"
    index = text.find(marker)
    if index == -1:
        return text
    prefix = text[: index + len(marker)]
    rest = text[index + len(marker):]
    stripped_lead = rest.lstrip()
    if not stripped_lead.startswith(("{", "[")):
        return text
    try:
        payload = json.loads(stripped_lead)
    except json.JSONDecodeError:
        return text
    cleaned = strip_unstable_ids(payload)
    lead_len = len(rest) - len(stripped_lead)
    return prefix + rest[:lead_len] + json.dumps(cleaned, ensure_ascii=False)


def strip_unstable_ids(value: Any) -> Any:
    """Drop SQLite row ids and the VESUM source-version hash from a payload."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key in _DROP_KEYS:
                continue
            if key == "id" and isinstance(item, int):
                continue
            cleaned[key] = strip_unstable_ids(item)
        return cleaned
    if isinstance(value, list):
        return [strip_unstable_ids(item) for item in value]
    if isinstance(value, str):
        return _strip_embedded_payload(value)
    return value


def _require_style_guide_headword(probe: str, fingerprint: dict[str, Any]) -> None:
    from wiki.sources_db import _fold_dict_key

    headword = str(fingerprint.get("headword") or "")
    if fingerprint.get("hit_count", 0) < 1:
        raise RuntimeError(f"style-guide probe {probe!r} returned no entry")
    if _fold_dict_key(headword) != _fold_dict_key(probe):
        raise RuntimeError(
            f"style-guide probe {probe!r} hit {headword!r}, which is not that headword"
        )


async def _capture(server: Any) -> dict[str, Any]:
    from wiki.sources_db import SOURCES_DB_PATH, using_connection

    from scripts.rag.config import VESUM_DB_PATH

    if not SOURCES_DB_PATH.is_file():
        raise FileNotFoundError(SOURCES_DB_PATH)
    if not Path(VESUM_DB_PATH).is_file():
        raise FileNotFoundError(VESUM_DB_PATH)
    uri = f"file:{SOURCES_DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    words = list(GOLDEN_WORDS)
    probes = list(STYLE_GUIDE_PROBES)
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
                    "search_definitions": fingerprint_dictionary_result(
                        _present(
                            await server.handle_dict_search({"query": word, "limit": 1}, "sum11", "СУМ-11")
                        )
                    ),
                }
            style_guide: dict[str, dict[str, Any]] = {}
            for probe in probes:
                fingerprint = fingerprint_dictionary_result(
                    _present(
                        await server.handle_dict_search(
                            {"query": probe, "limit": 1},
                            "style_guide",
                            "Антоненко-Давидович",
                        )
                    )
                )
                _require_style_guide_headword(probe, fingerprint)
                style_guide[probe] = fingerprint
            batch = {
                "verify_words": _present(await server.handle_verify_words({"words": words})),
                "inspect_words": _present(await server.handle_inspect_words({"words": words})),
            }
    finally:
        conn.close()
    return strip_unstable_ids({
        "words": words,
        "style_guide_probes": probes,
        "query_pravopys": (
            "omitted: pravopys_lookup fetches live pravopys.online HTML; "
            "search_style_guide is the nearest offline dictionary handler"
        ),
        "per_word": per_word,
        "style_guide": style_guide,
        "batch": batch,
    })


def capture() -> dict[str, Any]:
    server = load_server()
    return asyncio.run(_capture(server))


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


if __name__ == "__main__":
    EXPECTED_PATH.write_bytes(canonical_bytes(capture()))
    print(EXPECTED_PATH)
    print(EXPECTED_PATH.stat().st_size)
