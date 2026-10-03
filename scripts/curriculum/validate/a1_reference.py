"""Words-only reference membership, independent of the planned learner state."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

from scripts.audit.source_inventory_intake import _SAFE_LOADER, _records_from_structured_inventory

INVENTORY_PATH = Path(__file__).resolve().parents[3] / "registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml"
CLOSED_CLASS_PATH = INVENTORY_PATH.with_name("a1-closed-class.yaml")


def normalize(text: str) -> str:
    """Compare NFC lexical spellings, ignoring stress and formula punctuation."""
    text = unicodedata.normalize("NFC", text.replace("\u0301", ""))
    text = text.translate(str.maketrans({"'": "’", "ʼ": "’", "!": "", "?": "", ",": "", ".": "", "…": ""}))
    return " ".join(text.casefold().split())


def reference_spellings(path: Path = INVENTORY_PATH) -> tuple[frozenset[str], frozenset[str]]:
    """Return all member spellings and common single-word alternatives (including variants)."""
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
        proper = record.lemma[:1].isupper() or any("prop" in tags.split(":") for tags in record.vesum_tags)
        for spelling in (record.lemma, *record.variants):
            spelling = normalize(spelling)
            if " " in spelling and record.kind != "phrase":
                continue  # multi-word records require a phrase entry, not isolated word variants
            members.add(spelling)
            if not proper and record.kind != "phrase" and " " not in spelling:
                words.add(spelling)
    return frozenset(members), frozenset(words)


def closed_class_a1(path: Path = CLOSED_CLASS_PATH) -> frozenset[tuple[str, str]]:
    """Read class-specific A1 attestations; POS alone never proves CEFR level."""
    return _closed_class_from_bytes(path.read_bytes())


@lru_cache(maxsize=2)
def _closed_class_from_bytes(content: bytes) -> frozenset[tuple[str, str]]:
    payload = yaml.load(content.decode("utf-8-sig"), Loader=_SAFE_LOADER)
    if not isinstance(payload, dict) or set(payload) != {"version", "kind", "sources"}:
        raise ValueError("invalid A1 closed-class inventory")
    _records_from_structured_inventory(payload, inventory_path="registry/lexicon/source-inventory/a1-closed-class.yaml")
    rows = [row for source in payload["sources"] for row in source["headwords"]]
    if not isinstance(rows, list) or not rows:
        raise ValueError("A1 closed-class words must be a nonempty list")
    members = set()
    supplemental = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("source") not in {"PULS", "reference_units"}:
            raise ValueError("invalid A1 closed-class source")
        fields = {"lemma", "kind", "class", "level", "source"}
        if row["source"] == "reference_units":
            fields.add("page")
        if (set(row) != fields or row.get("kind") != "word" or row.get("level") != "A1" or row.get("class") not in {"pron", "conj", "prep", "part"}
                or not isinstance(row.get("lemma"), str)
                or not re.fullmatch(r"[а-яіїєґ’\-]+", row["lemma"])
                or normalize(row["lemma"]) != row["lemma"]):
            raise ValueError("invalid A1 closed-class word")
        key = (row["lemma"], row["class"])
        if key in members:
            raise ValueError("duplicate A1 closed-class word/class")
        if row["source"] == "reference_units":
            expected = {("і", "conj"): 47, ("й", "conj"): 47, ("в", "prep"): 41, ("у", "prep"): 41}
            if key not in expected or type(row["page"]) is not int or row["page"] != expected[key]:
                raise ValueError("invalid reference_units attestation")
            supplemental.add(key)
        members.add(key)
    if supplemental != {("і", "conj"), ("й", "conj"), ("в", "prep"), ("у", "prep")}:
        raise ValueError("reference_units requires exactly the four approved words/classes")
    return frozenset(members)


def eligible_closed_class(lemma: str, form_tags: frozenset[str], attestations: frozenset[tuple[str, str]]) -> bool:
    """Use only the selected word record's tags, never another homonym's analyses."""
    classes = set()
    for tags in form_tags:
        parts = tags.split(":")
        if "pron" in parts:
            classes.add("pron")
        elif parts[0] in {"conj", "prep", "part"}:
            classes.add(parts[0])
    # A record mixing classes must have an A1 attestation for each selected class.
    return bool(classes) and all((normalize(lemma), cls) in attestations for cls in classes) and all(
        "pron" in tags.split(":") or tags.split(":")[0] in {"conj", "prep", "part"} for tags in form_tags
    )
