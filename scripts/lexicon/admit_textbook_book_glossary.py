#!/usr/bin/env python3
"""Admit VESUM-verified textbook headword candidates into a per-book glossary.

Reads a capped candidate list produced from
``extract_textbook_chunk_headword_inventory.py`` output (lemma/pos/count/
locators, already VESUM-attested) and admits only lemmas that additionally
clear two real, source-backed gates:

- a public Ukrainian definition from СУМ-20 (``newsum``) or ВТС (``vts``) —
  never СУМ-11 (docs/runbooks/word-atlas-entry-model.md, #7453);
- a learner English gloss from dmklinger (UK->EN, Wiktionary-derived), with
  slovnyk.me's ``ukreng`` as a second real dictionary fallback.

Nothing is invented: a candidate missing either gate stays in the residual
bucket with the reason recorded, never a guessed definition or gloss.

СУМ-20/ВТС/ukreng live behind Cloudflare, which blocks a plain ``requests``
client but accepts a polite curl User-Agent (matches
``fill_slovnyk_sum20_cache.py``) — this script fetches with curl and writes
into the same one-file-per-lemma cache
(``data/lexicon/slovnyk_cache/<lemma>.json``, schema v4) so the fetch is
reusable by ``enrich_manifest.py`` and future grade passes.

Run from the repository root::

    .venv/bin/python scripts/lexicon/admit_textbook_book_glossary.py \\
      --candidates /tmp/g1-candidates/bukvar.json \\
      --book-id bukvar-zaharijchuk-grade1-2025 \\
      --title "Захарійчук М. Українська мова. Буквар. 1 клас, 2025" \\
      --subject bukvar \\
      --out data/lexicon/source-inventory/grade-01/bukvar-zaharijchuk-grade1-2025-glossary.yaml \\
      --report
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.parse
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scripts.storage.topology import (
        ActiveDatabaseNetworkError,
        is_network_filesystem_path,
    )
except ImportError:
    try:
        from storage.topology import (  # type: ignore[no-redef]
            ActiveDatabaseNetworkError,
            is_network_filesystem_path,
        )
    except ImportError:

        class ActiveDatabaseNetworkError(ValueError):  # type: ignore[no-redef]
            """Raised when a caller tries to use a network path as active sources.db."""

        def is_network_filesystem_path(path: Path) -> bool:  # type: ignore[no-redef]
            s = str(path)
            return (
                s.startswith("//")
                or s.startswith("\\\\")
                or "/volumes/ukrainiandata" in s.lower()
                or "\\ukrainiandata\\" in s.lower()
            )


from scripts.lexicon.enrich_manifest import (
    _SLOVNYK_CACHE_SCHEMA_VERSION,
    _definition_body,
    _dmklinger_key,
    _load_slovnyk_cache_file,
    _parse_slovnyk_entry,
    _slovnyk_cache_path,
    _slovnyk_lookup_word,
)
from scripts.lexicon.extract_book_headword_inventory import _atomic_write_yaml

USER_AGENT = "learn-ukrainian-word-atlas/1.0 (noncommercial educational per-lemma lookup; issue #7551)"
SLOVNYK_SLUGS = ("newsum", "vts", "ukreng")
SLEEP_SECONDS = 0.3
DEFINITION_CHAR_LIMIT = 320
GLOSS_MAX_SENSES = 3


@lru_cache(maxsize=16)
def _cached_resolve_main_root(path_str: str) -> Path | None:
    try:
        from scripts.guardrails.worktree_containment import (
            NotAGitRepositoryError,
            resolve_main_root,
        )
    except ImportError:
        try:
            from guardrails.worktree_containment import (  # type: ignore[no-redef]
                NotAGitRepositoryError,
                resolve_main_root,
            )
        except ImportError:
            return None
    try:
        return resolve_main_root(Path(path_str))
    except (NotAGitRepositoryError, RuntimeError):
        return None


def _resolve_primary_checkout(root: Path | None = None) -> Path | None:
    """Primary checkout root via the shared ``.git`` common dir (#6571, #7551).

    Dispatch worktrees sparse-exclude the large ``data/`` artifacts, so they
    live only in the primary checkout. Resolve that root from git (works on any
    operator's machine) instead of a hardcoded absolute path. Returns None
    outside a git repo so callers fall back honestly.
    """
    target = root if root is not None else PROJECT_ROOT
    return _cached_resolve_main_root(str(target))


def is_valid_sources_db(path: Path) -> bool:
    """True if path exists, is a regular file, and contains SQLite format 3 data."""
    try:
        if not path.is_file() or path.stat().st_size < 100:
            return False
        with path.open("rb") as f:
            header = f.read(16)
        return header == b"SQLite format 3\x00"
    except OSError:
        return False


def resolve_sources_db(
    explicit: Path | str | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Resolve active sources.db: worktree path if valid, else primary checkout.

    Never symlinks. Refuses network/SMB paths. Fails closed with FileNotFoundError
    if neither exists.
    """
    root = project_root if project_root is not None else PROJECT_ROOT

    # 1. Explicit override or environment variable
    candidate_str = explicit or os.environ.get("SOURCES_DB_PATH") or os.environ.get("LU_SOURCES_DB")
    if candidate_str:
        candidate = Path(candidate_str).expanduser()
        if is_network_filesystem_path(candidate) or (
            candidate.exists() and is_network_filesystem_path(candidate.resolve())
        ):
            raise ActiveDatabaseNetworkError(
                f"Active sources.db must remain on local storage; refused network path: {candidate}"
            )
        if is_valid_sources_db(candidate):
            return candidate
        raise FileNotFoundError(
            f"sources.db specified at '{candidate}' does not exist or is not a valid SQLite database"
        )

    # 2. Worktree path if present and valid
    worktree_db = root / "data" / "sources.db"
    if is_network_filesystem_path(worktree_db) or (
        worktree_db.exists() and is_network_filesystem_path(worktree_db.resolve())
    ):
        raise ActiveDatabaseNetworkError(
            f"Active sources.db must remain on local storage; refused network path: {worktree_db}"
        )
    if is_valid_sources_db(worktree_db):
        return worktree_db

    # 3. Primary-checkout fallback
    primary = _resolve_primary_checkout(root)
    if primary is not None and primary.resolve() != root.resolve():
        primary_db = primary / "data" / "sources.db"
        if is_network_filesystem_path(primary_db) or (
            primary_db.exists() and is_network_filesystem_path(primary_db.resolve())
        ):
            raise ActiveDatabaseNetworkError(
                f"Active sources.db must remain on local storage; refused network path: {primary_db}"
            )
        if is_valid_sources_db(primary_db):
            return primary_db
        raise FileNotFoundError(
            f"sources.db not found: checked worktree '{worktree_db}' and primary checkout '{primary_db}'"
        )

    primary_desc = (
        f"'{primary / 'data' / 'sources.db'}'" if primary is not None else "could not resolve primary checkout"
    )
    raise FileNotFoundError(f"sources.db not found: checked worktree '{worktree_db}' and {primary_desc}")


def fetch_slovnyk_curl(word: str, slug: str, *, timeout: int = 15) -> tuple[int, str]:
    url = f"https://slovnyk.me/dict/{slug}/{urllib.parse.quote(word)}"
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "-A", USER_AGENT, "--max-time", str(timeout), url]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    except subprocess.TimeoutExpired:
        return 0, ""
    if res.returncode != 0:
        return 0, ""
    parts = res.stdout.rsplit("\n", 1)
    if len(parts) == 2:
        body, code_str = parts
        try:
            return int(code_str.strip()), body
        except ValueError:
            return 0, body
    return 0, ""


def load_dmklinger_index(conn: sqlite3.Connection) -> dict[str, list[tuple[str, str]]]:
    index: dict[str, list[tuple[str, str]]] = {}
    for word, pos, translations in conn.execute("SELECT word, pos, translations FROM dmklinger_uk_en"):
        index.setdefault(_dmklinger_key(str(word or "")), []).append((str(pos or ""), str(translations or "")))
    return index


def dmklinger_gloss(index: dict[str, list[tuple[str, str]]], lemma: str) -> str | None:
    rows = index.get(_dmklinger_key(lemma))
    if not rows:
        return None
    senses: list[str] = []
    seen: set[str] = set()
    for _pos, raw in rows:
        try:
            items = json.loads(raw) if raw else []
        except (TypeError, ValueError):
            items = []
        for item in items if isinstance(items, list) else []:
            text = " ".join(str(item).split())
            key = text.casefold()
            if text and key not in seen:
                seen.add(key)
                senses.append(text)
    if not senses:
        return None
    return "; ".join(senses[:GLOSS_MAX_SENSES])


def ensure_slovnyk_cache(lemma: str) -> dict[str, Any]:
    """Curl-fetch any missing СУМ-20/ВТС/ukreng lookups and persist them.

    Idempotent: an already-attempted slug (hit or a genuine 404 miss) is
    never re-fetched. A transient failure (Cloudflare challenge, timeout,
    non-200/404 status) is left unset so a later run retries it instead of
    being cached as a false miss.
    """
    path = _slovnyk_cache_path(lemma)
    cache = _load_slovnyk_cache_file(path)
    if not cache or cache.get("schema_version") != _SLOVNYK_CACHE_SCHEMA_VERSION:
        cache = {
            "schema_version": _SLOVNYK_CACHE_SCHEMA_VERSION,
            "lemma": lemma,
            "lookup_word": _slovnyk_lookup_word(lemma),
            "fetched_at": "",
            "lookups": {},
        }
    lookups = cache.setdefault("lookups", {})
    lookup_word = _slovnyk_lookup_word(lemma)
    changed = False
    for slug in SLOVNYK_SLUGS:
        if slug in lookups:
            continue
        code, body = fetch_slovnyk_curl(lookup_word, slug)
        time.sleep(SLEEP_SECONDS)
        if code == 200 and "Just a moment" not in body and "<title>Just a moment" not in body:
            url = f"https://slovnyk.me/dict/{slug}/{urllib.parse.quote(lookup_word)}"
            row = _parse_slovnyk_entry(body, lemma=lemma, lookup_word=lookup_word, slug=slug, url=url)
            lookups[slug] = row
            changed = True
        elif code == 404:
            lookups[slug] = None
            changed = True
        # else: transient (403 challenge / timeout / 5xx) — leave unset, retry later.
    if changed:
        import datetime as dt

        cache["fetched_at"] = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cache


def uk_definition(cache: dict[str, Any], lemma: str) -> tuple[str, str, str] | None:
    """Return ``(text, source_slug, source_url)`` from СУМ-20 first, then ВТС."""
    lookups = cache.get("lookups") or {}
    lookup_word = str(cache.get("lookup_word") or lemma)
    for slug, label in (("newsum", "sum20"), ("vts", "vts")):
        row = lookups.get(slug)
        if not isinstance(row, dict) or not row.get("text"):
            continue
        text = _definition_body(
            row["text"],
            headword=str(row.get("word") or lookup_word),
            strip_leading_headword=True,
            limit=DEFINITION_CHAR_LIMIT,
        )
        if text:
            return text, label, str(row.get("source_url") or "")
    return None


def en_gloss(
    cache: dict[str, Any], lemma: str, dmklinger_index: dict[str, list[tuple[str, str]]]
) -> tuple[str, str] | None:
    gloss = dmklinger_gloss(dmklinger_index, lemma)
    if gloss:
        return gloss, "dmklinger"
    lookups = cache.get("lookups") or {}
    row = lookups.get("ukreng")
    if isinstance(row, dict) and row.get("text"):
        text = _definition_body(
            row["text"], headword=str(row.get("word") or lemma), strip_leading_headword=True, limit=200
        )
        if text:
            return text, "ukreng"
    return None


def admit_candidates(
    candidates: list[dict[str, Any]],
    *,
    dmklinger_index: dict[str, list[tuple[str, str]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    admitted: list[dict[str, Any]] = []
    residual: list[dict[str, Any]] = []
    for candidate in candidates:
        lemma = str(candidate["lemma"])
        pos = str(candidate["pos"])
        cache = ensure_slovnyk_cache(lemma)
        definition = uk_definition(cache, lemma)
        gloss = en_gloss(cache, lemma, dmklinger_index)
        if definition and gloss:
            def_text, def_source, def_url = definition
            gloss_text, gloss_source = gloss
            admitted.append(
                {
                    "lemma": lemma,
                    "pos": pos,
                    "count": candidate.get("count"),
                    "locator": (candidate.get("locators") or ["unknown"])[0],
                    "gloss": gloss_text,
                    "gloss_source": gloss_source,
                    "context": def_text,
                    "context_source": def_source,
                    "context_url": def_url,
                }
            )
        else:
            reasons = []
            if not definition:
                reasons.append("no_uk_definition")
            if not gloss:
                reasons.append("no_en_gloss")
            residual.append({"lemma": lemma, "pos": pos, "count": candidate.get("count"), "reasons": reasons})
    return admitted, residual


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True, help="Capped candidate JSON (attempted list)")
    parser.add_argument("--book-id", required=True, help="Atlas source-inventory id for this book glossary")
    parser.add_argument("--title", required=True, help="Human-readable book title")
    parser.add_argument("--subject", help="Optional subject label")
    parser.add_argument("--out", type=Path, required=True, help="Glossary YAML destination")
    parser.add_argument("--report", action="store_true", help="Print admission stats")
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=None,
        help="Optional path to sources.db (default: auto-resolved from worktree or primary checkout)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    payload = json.loads(args.candidates.read_text(encoding="utf-8"))
    attempted = payload["attempted"]

    sources_db = resolve_sources_db(args.sources_db)
    conn = sqlite3.connect(str(sources_db))
    try:
        dmklinger_index = load_dmklinger_index(conn)
    finally:
        conn.close()

    admitted, residual = admit_candidates(attempted, dmklinger_index=dmklinger_index)
    admitted.sort(key=lambda item: (-(item["count"] or 0), item["lemma"]))
    residual.sort(key=lambda item: (-(item["count"] or 0), item["lemma"]))

    richness = len(admitted) / len(attempted) if attempted else 0.0
    stats = {
        "total_content_candidates": payload.get("total_content_candidates"),
        "attempted": len(attempted),
        "admitted": len(admitted),
        "residual_this_batch": len(residual),
        "residual_not_attempted": len(payload.get("residual_not_attempted") or []),
        "richness": round(richness, 4),
    }

    source: dict[str, Any] = {
        "id": args.book_id,
        "source_family": "textbook",
        "extraction_mode": "headword_inventory",
        "title": args.title,
        "notes": (
            "Admission gate: VESUM (upstream extraction) + public UK definition "
            "(СУМ-20/ВТС, never СУМ-11) + learner English gloss (dmklinger UK->EN, "
            "slovnyk.me ukreng fallback). Residual candidates missing either gate "
            "are listed separately, never guessed."
        ),
        "headwords": admitted,
    }
    if args.subject:
        source["subject"] = args.subject
    out_payload = {
        "version": 1,
        "kind": "atlas_source_inventory",
        "sources": [source],
        "residual": residual,
        "stats": stats,
    }
    _atomic_write_yaml(out_payload, args.out)
    if args.report:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        print(f"WROTE glossary={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
