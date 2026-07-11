"""Shared schema and normalization helpers for relation-pair corpus data."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from collections.abc import Callable

from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.verification.vesum import verify_word

RELATION_TYPES = frozenset({"synonym", "antonym", "paronym", "homonym"})
_UKRAINIAN_WORD_RE = re.compile(r"^[А-Яа-яЄєІіЇїҐґ'’ʼ-]+$")
_STRESS_MARK_RE = re.compile("[\u0300\u0301]")


def ensure_relation_pairs_schema(conn: sqlite3.Connection) -> None:
    """Create the durable, provenance-preserving relation-pair corpus schema."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS relation_pairs (
            id INTEGER PRIMARY KEY,
            relation TEXT NOT NULL CHECK (relation IN ('synonym', 'antonym', 'paronym', 'homonym')),
            word_a TEXT NOT NULL,
            word_b TEXT NOT NULL,
            gloss_a TEXT DEFAULT '',
            gloss_b TEXT DEFAULT '',
            source TEXT NOT NULL,
            source_url TEXT DEFAULT '',
            confidence TEXT DEFAULT 'medium' CHECK (confidence IN ('high', 'medium', 'low')),
            review_status TEXT DEFAULT 'candidate' CHECK (review_status IN ('candidate', 'approved', 'rejected')),
            added_at TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_relation_pairs_pair_source
            ON relation_pairs(relation, word_a, word_b, source);
        CREATE INDEX IF NOT EXISTS idx_relation_pairs_relation_word_a
            ON relation_pairs(relation, word_a);
        CREATE INDEX IF NOT EXISTS idx_relation_pairs_relation_word_b
            ON relation_pairs(relation, word_b);
        """
    )


def normalize_relation_word(value: object) -> str | None:
    """Return a single Ukrainian lemma key with VESUM-compatible apostrophes."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = _STRESS_MARK_RE.sub("", text)
    text = unicodedata.normalize("NFC", text)
    text = strip_acute_stress(text).replace("`", "'").replace("’", "'").replace("ʼ", "'")
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return text if _UKRAINIAN_WORD_RE.fullmatch(text) else None


def is_exact_vesum_lemma(
    word: str,
    *,
    verifier: Callable[[str], list[dict]] = verify_word,
) -> bool:
    """Fail closed unless VESUM records ``word`` exactly as a lemma."""
    normalized = normalize_relation_word(word)
    if not normalized:
        return False
    try:
        return any(normalize_relation_word(row.get("lemma")) == normalized for row in verifier(normalized))
    except Exception:
        return False
