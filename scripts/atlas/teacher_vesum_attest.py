"""Deterministic VESUM attestation for private teacher seed lemmas.

Teacher vocabulary may be title-cased, use a typographic apostrophe, or be a
multiword expression. Those input-shape differences must not turn a real
VESUM entry into a false ``no_hit``. This helper attests lexical forms only;
it neither derives an example sentence nor grants redistribution rights.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VESUM_DB = ROOT / "data" / "vesum.db"
_APOSTROPHE_FOLD = str.maketrans({"’": "'", "ʼ": "'", "ʻ": "'", "＇": "'"})
_WORD_RE = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*", re.UNICODE)


class VesumAttestation(TypedDict):
    """Structured VESUM evidence suitable for the private teacher package."""

    attested: bool
    method: str
    matched_forms: list[str]
    matched_lemmas: list[str]
    notes: list[str]


def normalize_lemma(value: str) -> str:
    """Normalize case and apostrophe variants without altering lexical content."""
    return " ".join(str(value or "").strip().translate(_APOSTROPHE_FOLD).casefold().split())


def content_tokens(value: str) -> list[str]:
    """Return normalized alphabetic lexical tokens, preserving internal apostrophes."""
    return [normalize_lemma(token) for token in _WORD_RE.findall(normalize_lemma(value))]


def _open_read_only(path: Path) -> sqlite3.Connection:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"VESUM database not found: {resolved}")
    connection = sqlite3.connect(f"file:{resolved.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _lookup(connection: sqlite3.Connection, term: str) -> tuple[list[str], list[str]]:
    """Look up a normalized term as either an attested form or a lemma.

    VESUM's stored lexical values are normalized lowercase. Normalizing the
    query with Unicode ``casefold`` gives title-cased teacher input the same
    lookup semantics without a table scan or SQLite's ASCII-only ``LOWER``.
    """
    rows = connection.execute(
        """
        SELECT word_form, lemma
        FROM forms
        WHERE word_form = ? OR lemma = ?
        ORDER BY word_form, lemma
        """,
        (term, term),
    ).fetchall()
    return (
        sorted({str(row["word_form"]) for row in rows}),
        sorted({str(row["lemma"]) for row in rows}),
    )


def _attest_with_connection(lemma: str, connection: sqlite3.Connection) -> VesumAttestation:
    """Attest one lemma using an already-open read-only VESUM connection."""
    normalized = normalize_lemma(lemma)
    if not normalized:
        return {
            "attested": False,
            "method": "none",
            "matched_forms": [],
            "matched_lemmas": [],
            "notes": ["empty_lemma"],
        }

    tokens = content_tokens(normalized)
    candidates: list[tuple[str, str]] = [("full_string", normalized)]
    if len(tokens) > 1:
        candidates.append(("head_token", tokens[0]))
        candidates.extend(("content_token", token) for token in tokens[1:] if len(token) >= 3)

    attempted: list[str] = []
    for method, term in candidates:
        if term in attempted:
            continue
        attempted.append(term)
        forms, lemmas = _lookup(connection, term)
        if forms or lemmas:
            return {
                "attested": True,
                "method": method,
                "matched_forms": forms,
                "matched_lemmas": lemmas,
                "notes": [f"normalized={normalized}", f"matched={term}"],
            }
    return {
        "attested": False,
        "method": "none",
        "matched_forms": [],
        "matched_lemmas": [],
        "notes": [f"normalized={normalized}", f"attempted={','.join(attempted)}"],
    }


def attest_lemma(lemma: str, *, vesum_db: Path = DEFAULT_VESUM_DB) -> VesumAttestation:
    """Attest one teacher lemma against VESUM, including phrase-head recovery.

    Lookup order is deterministic: normalized full string, the first content
    token (the expression head), then remaining alphabetic content tokens of
    at least three characters. A positive token match is lexical attestation
    for local recognition only, not sentence evidence.
    """
    with _open_read_only(vesum_db) as connection:
        return _attest_with_connection(lemma, connection)


def attest_lemmas(lemmas: Iterable[str], *, vesum_db: Path = DEFAULT_VESUM_DB) -> list[VesumAttestation]:
    """Attest a batch through one read-only connection in input order.

    The result is equivalent to calling :func:`attest_lemma` per value, but a
    package refresh avoids repeatedly opening a large shared SQLite artifact.
    """
    with _open_read_only(vesum_db) as connection:
        return [_attest_with_connection(lemma, connection) for lemma in lemmas]
