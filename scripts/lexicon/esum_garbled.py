"""Targeted handling for curated garbled ЕСУМ etymology rows."""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CURATED_GARBLED_ESUM_PATH = ROOT / "data" / "lexicon" / "esum_garbled_etymologies.json"

MOJIBAKE_MARKERS = (
    "Зпоц",
    "Эндзелин",
    "Зндзелин",
    "Веліа[",
    "Вегіа[",
    "Вехіа]",
    "Е55)",
    "Е55Л",
    "Е5)С",
    "Зспиз",
    "51ййсііа",
    "\\У",
)


_SPACE_RE = re.compile(r"\s+")
_APOSTROPHE_TRANSLATION = str.maketrans({"’": "'", "ʼ": "'", "`": "'"})


def lookup_key(value: str) -> str:
    """Return a stable key for Ukrainian lemma comparisons."""
    normalized = unicodedata.normalize("NFKD", str(value or "").strip())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = unicodedata.normalize("NFC", normalized)
    return normalized.translate(_APOSTROPHE_TRANSLATION).casefold()


@lru_cache(maxsize=1)
def load_garbled_esum_entries() -> dict[str, dict[str, Any]]:
    """Load curated garbled ЕСУМ entries keyed by normalized lemma."""
    try:
        payload = json.loads(CURATED_GARBLED_ESUM_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        lemma = str(entry.get("lemma") or "").strip()
        if lemma:
            out[lookup_key(lemma)] = entry
    return out


def garbled_esum_entry(lemma: str) -> dict[str, Any] | None:
    """Return curated garble metadata for lemma, if present."""
    return load_garbled_esum_entries().get(lookup_key(lemma))


def is_garbled_esum_lemma(lemma: str) -> bool:
    """Whether lemma is in the precision-first garbled ЕСУМ set."""
    return garbled_esum_entry(lemma) is not None


def strip_garbled_tail(text: str, lemma: str) -> str:
    """Strip only the curated garbled tail marker; never reconstruct text."""
    entry = garbled_esum_entry(lemma)
    clean = str(text or "")
    if not entry:
        return clean
    marker = str(entry.get("strip_after") or "")
    if marker and marker in clean:
        clean = clean.split(marker, 1)[0]
    clean = clean.rstrip(" ,;:-—")
    return _SPACE_RE.sub(" ", clean).strip()


def trim_curated_goroh_text(text: str, lemma: str, max_chars: int = 360) -> str:
    """Bound curated Горох extracts to avoid neighboring-card bleed-through."""
    clean = _SPACE_RE.sub(" ", str(text or "")).strip()
    if not garbled_esum_entry(lemma) or len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip(" ,;:-—") + "…"


def has_mojibake_marker(text: str) -> bool:
    """Detect only curated high-confidence mojibake markers."""
    return any(marker in str(text or "") for marker in MOJIBAKE_MARKERS)
