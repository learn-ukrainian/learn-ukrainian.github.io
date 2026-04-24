"""Vocabulary sidecar coverage checks for plan-required terms."""

from __future__ import annotations

import sqlite3
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VESUM_DB_PATH = PROJECT_ROOT / "data" / "vesum.db"
_TRAILING_PUNCTUATION = "?!."


@dataclass(frozen=True)
class VocabCoverageResult:
    passed: bool
    missing_terms: tuple[str, ...]
    present_mapping: dict[str, str]


def _strip_stress_marks(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value).replace("\u0301", "")
    return unicodedata.normalize("NFC", decomposed)


def _normalize_term(value: str) -> str:
    return _strip_stress_marks(value).lower().strip().rstrip(_TRAILING_PUNCTUATION).strip()


def _extract_ukrainian_term(hint: str) -> str:
    return str(hint).split(" (", maxsplit=1)[0].strip()


def _load_required_terms(plan_path: Path) -> tuple[str, ...]:
    payload = yaml.safe_load(plan_path.read_text("utf-8")) or {}
    vocabulary_hints = payload.get("vocabulary_hints") or {}
    required = vocabulary_hints.get("required") or []
    return tuple(
        term
        for item in required
        if (term := _extract_ukrainian_term(str(item)))
    )


def _load_vocab_words(vocab_yaml_path: Path) -> tuple[str, ...]:
    payload = yaml.safe_load(vocab_yaml_path.read_text("utf-8")) or {}
    entries = payload.get("vocabulary") if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        return ()

    words: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        word = entry.get("word")
        if isinstance(word, str) and word.strip():
            words.append(word.strip())
    return tuple(words)


def _vesum_lemma_lookup(term: str, db_path: Path = VESUM_DB_PATH) -> str | None:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return None

    normalized = _normalize_term(term)
    if not normalized:
        return None

    try:
        with sqlite3.connect(str(db_path)) as db:
            # Current contract for this validator: data/vesum.db exposes
            # vesum(form, lemma). Older local imports used forms(word_form, lemma),
            # so keep that fallback to avoid making the validator environment-fragile.
            for query in (
                "SELECT lemma FROM vesum WHERE form = ? LIMIT 1",
                "SELECT lemma FROM forms WHERE word_form = ? LIMIT 1",
                "SELECT lemma FROM forms WHERE lemma = ? LIMIT 1",
            ):
                try:
                    row = db.execute(query, (normalized,)).fetchone()
                except sqlite3.OperationalError:
                    continue
                if row and row[0]:
                    return _normalize_term(str(row[0]))
    except sqlite3.Error:
        return None
    return None


@lru_cache(maxsize=4096)
def _lemma_key(term: str) -> str | None:
    normalized = _normalize_term(term)
    if not normalized:
        return None

    direct = _vesum_lemma_lookup(normalized)
    if direct:
        return direct

    tokens = normalized.split()
    if len(tokens) <= 1:
        return None

    lemmas = [_vesum_lemma_lookup(token) for token in tokens]
    if all(lemmas):
        return " ".join(str(lemma) for lemma in lemmas)
    return None


def _terms_match(plan_term: str, vocab_word: str) -> bool:
    if _normalize_term(plan_term) == _normalize_term(vocab_word):
        return True

    plan_lemma = _lemma_key(plan_term)
    vocab_lemma = _lemma_key(vocab_word)
    return bool(plan_lemma and vocab_lemma and plan_lemma == vocab_lemma)


def check_vocab_coverage(
    plan_path: Path,
    vocab_yaml_path: Path,
) -> VocabCoverageResult:
    """Check that every plan-required vocabulary term is present in словник YAML."""
    required_terms = _load_required_terms(plan_path)
    vocab_words = _load_vocab_words(vocab_yaml_path)

    missing: list[str] = []
    present_mapping: dict[str, str] = {}

    for term in required_terms:
        matched_word = next((word for word in vocab_words if _terms_match(term, word)), None)
        if matched_word is None:
            missing.append(term)
        else:
            present_mapping[term] = matched_word

    return VocabCoverageResult(
        passed=not missing,
        missing_terms=tuple(missing),
        present_mapping=present_mapping,
    )
