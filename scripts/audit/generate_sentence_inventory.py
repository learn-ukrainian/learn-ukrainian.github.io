"""Extract short, source-attested examples for the Word Atlas daily pool.

The committed inventory contains only learner-facing sentences plus an
attribution-safe provenance record.  It intentionally never copies a local
ULP filename, transcript identifier, URL, or any other private locator.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

DEFAULT_DAILY_POOL = Path("site/src/data/lexicon-daily-pool.json")
DEFAULT_SOURCES_DB = Path("data/sources.db")
DEFAULT_VESUM_DB = Path("data/vesum.db")
DEFAULT_OUT = Path("site/src/data/lexicon-sentence-inventory.json")

UK_TOKEN_RE = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[ʼ'’-][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
SPACE_RE = re.compile(r"\s+")

TEXTBOOK_LICENSE = {
    "status": "not_openly_licensed",
    "useBasis": "short educational quotation with attribution",
}
ULP_LICENSE = {
    "status": "copyrighted_source",
    "useBasis": "short educational quotation with attribution",
}


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _normalise(text: str) -> str:
    # OCR frequently breaks a word at the end of a visual line (``до-\nпомогу``).
    text = re.sub(r"(?<=[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ])-\s+(?=[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ])", "", text)
    return SPACE_RE.sub(" ", text).strip()


def _tokens(text: str) -> list[str]:
    return UK_TOKEN_RE.findall(text)


def _exact_target_present(sentence: str, lemma: str) -> bool:
    target = lemma.casefold()
    return any(token.casefold() == target for token in _tokens(sentence))


class VesumSentenceVerifier:
    """Small cached VESUM lookup used only for sentence-shape screening."""

    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self.cache: dict[str, bool] = {}

    def has_verb(self, tokens: Iterable[str]) -> bool:
        for token in tokens:
            key = token.casefold()
            known = self.cache.get(key)
            if known is None:
                known = (
                    self.conn.execute(
                        "SELECT 1 FROM forms WHERE word_form IN (?, ?) AND pos = 'verb' LIMIT 1",
                        (token, key),
                    ).fetchone()
                    is not None
                )
                self.cache[key] = known
            if known:
                return True
        return False

    def close(self) -> None:
        self.conn.close()


def _candidate_sentences(text: str, lemma: str, *, vesum: VesumSentenceVerifier | None = None) -> Iterable[str]:
    """Yield readable, short sentences containing the exact daily lemma.

    We deliberately require the surface to equal the daily lemma.  This keeps
    the initial inventory lemma-linked without making unverified morphology
    claims; a later cloze workflow can VESUM-check a separately selected form.
    """
    for raw_sentence in SENTENCE_SPLIT_RE.split(_normalise(text)):
        sentence = raw_sentence.strip(" \t\n—–")
        tokens = _tokens(sentence)
        if not (3 <= len(tokens) <= 18 and 15 <= len(sentence) <= 180):
            continue
        if sentence.isupper() or not sentence.endswith((".", "!", "?")):
            continue
        if not _exact_target_present(sentence, lemma):
            continue
        # OCR headings, web addresses, and mixed-language transcript noise are
        # poor daily-practice examples even when the FTS match is exact.
        if "http" in sentence.casefold() or sentence.count("*") > 1:
            continue
        if vesum is not None and not vesum.has_verb(tokens):
            continue
        yield sentence


def _fts_rows(
    conn: sqlite3.Connection,
    *,
    fts_table: str,
    content_table: str,
    lemma: str,
    where_sql: str = "",
) -> Iterable[sqlite3.Row]:
    query = f'"{lemma.replace(chr(34), "")}"'
    sql = f"""
        SELECT source.text, source.title, source.chunk_id
        FROM {fts_table} AS fts
        JOIN {content_table} AS source ON source.id = fts.rowid
        WHERE {fts_table} MATCH ? {where_sql}
        ORDER BY bm25({fts_table})
        LIMIT 20
    """
    yield from conn.execute(sql, (query,))


def _first_source_sentence(
    conn: sqlite3.Connection,
    *,
    target: dict[str, str],
    source_kind: str,
    vesum: VesumSentenceVerifier | None = None,
) -> dict[str, Any] | None:
    lemma = target["lemma"]
    if source_kind == "textbook":
        rows = _fts_rows(
            conn,
            fts_table="textbooks_fts",
            content_table="textbooks",
            lemma=lemma,
        )
        source_label = "Ukrainian school textbook"
        license_info = TEXTBOOK_LICENSE
    else:
        rows = _fts_rows(
            conn,
            fts_table="external_fts",
            content_table="external_articles",
            lemma=lemma,
            where_sql="AND source.source_file = 'ulp_youtube'",
        )
        # No local identifier is committed for this source family.
        source_label = "Ukrainian Lessons Podcast"
        license_info = ULP_LICENSE

    for row in rows:
        text = _text(row["text"])
        if text is None:
            continue
        for sentence in _candidate_sentences(text, lemma, vesum=vesum):
            provenance: dict[str, Any] = {
                "source": source_kind,
                "label": source_label,
            }
            if source_kind == "textbook":
                # This is a public textbook chunk identifier, sufficient for
                # attribution while keeping the inventory independent of DB ids.
                provenance["locator"] = _text(row["chunk_id"])
                provenance["title"] = _text(row["title"])
            return {
                "lemma": lemma,
                "lemmaId": target["lemmaId"],
                "sentence": sentence,
                "targetForm": lemma,
                "cefr": target.get("cefr"),
                "uses": ["example"],
                "provenance": provenance,
                "license": dict(license_info),
            }
    return None


def load_daily_lemmas(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("daily pool must be a JSON list")
    lemmas = {_text(row.get("lemma")) for row in payload if isinstance(row, dict)}
    return sorted(lemma for lemma in lemmas if lemma is not None)


def load_daily_targets(path: Path) -> list[dict[str, str]]:
    """Load daily lemma ids and CEFR labels without relying on a manifest checkout."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("daily pool must be a JSON list")
    targets: dict[str, dict[str, str]] = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        lemma = _text(row.get("lemma"))
        lemma_id = _text(row.get("slug"))
        if lemma is None or lemma_id is None:
            continue
        target = {"lemma": lemma, "lemmaId": lemma_id}
        cefr = _text(row.get("cefr"))
        if cefr is not None:
            target["cefr"] = cefr
        targets[lemma] = target
    return [targets[lemma] for lemma in sorted(targets)]


def build_inventory(
    targets: Iterable[dict[str, str]],
    sources_db: Path,
    *,
    include_ulp: bool = False,
    vesum_db: Path | None = None,
) -> list[dict[str, Any]]:
    conn = sqlite3.connect(sources_db)
    conn.row_factory = sqlite3.Row
    vesum = VesumSentenceVerifier(vesum_db) if vesum_db is not None and vesum_db.exists() else None
    try:
        rows: list[dict[str, Any]] = []
        for target in sorted(targets, key=lambda row: row["lemma"]):
            row = _first_source_sentence(conn, target=target, source_kind="textbook", vesum=vesum)
            if row is None and include_ulp:
                row = _first_source_sentence(conn, target=target, source_kind="ulp", vesum=vesum)
            if row is not None:
                rows.append(row)
        return rows
    finally:
        conn.close()
        if vesum is not None:
            vesum.close()


def write_inventory(rows: list[dict[str, Any]], out_path: Path) -> None:
    payload = {
        "schema": "atlas-sentence-inventory",
        "schemaVersion": 1,
        "rows": rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily-pool", type=Path, default=DEFAULT_DAILY_POOL)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--include-ulp", action="store_true")
    args = parser.parse_args(argv)
    rows = build_inventory(
        load_daily_targets(args.daily_pool), args.sources_db, include_ulp=args.include_ulp, vesum_db=args.vesum_db
    )
    write_inventory(rows, args.out)
    print(f"sentence inventory: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
