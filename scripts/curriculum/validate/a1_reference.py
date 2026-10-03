"""Words-only reference membership, independent of the planned learner state."""

from __future__ import annotations

import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

from scripts.audit.source_inventory_intake import _SAFE_LOADER, _records_from_structured_inventory

INVENTORY_PATH = Path(__file__).resolve().parents[3] / "registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml"


def normalize(text: str) -> str:
    """Compare NFC lexical spellings, ignoring stress and formula punctuation."""
    text = unicodedata.normalize("NFC", text.replace("\u0301", ""))
    text = text.translate(str.maketrans({"'": "’", "ʼ": "’", "!": "", "?": "", ",": "", ".": "", "…": ""}))
    return " ".join(text.casefold().split())


def reference_spellings(path: Path = INVENTORY_PATH) -> tuple[frozenset[str], frozenset[str]]:
    """Return all member spellings and single-word alternatives (including variants)."""
    # Content, rather than timestamps or a writable digest sidecar, invalidates the cache.
    return _spellings_from_bytes(path.read_bytes())


@lru_cache(maxsize=2)
def _spellings_from_bytes(content: bytes) -> tuple[frozenset[str], frozenset[str]]:
    """Parse each exact inventory once; immutable results cannot be changed by callers."""
    members: set[str] = set()
    words: set[str] = set()
    for record in _records_from_structured_inventory(
        yaml.load(content.decode("utf-8-sig"), Loader=_SAFE_LOADER),
        inventory_path="registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml",
    ):
        for spelling in (record.lemma, *record.variants):
            spelling = normalize(spelling)
            if " " in spelling and record.kind != "phrase":
                continue  # multi-word records require a phrase entry, not isolated word variants
            members.add(spelling)
            if record.kind != "phrase" and " " not in spelling:
                words.add(spelling)
    return frozenset(members), frozenset(words)
