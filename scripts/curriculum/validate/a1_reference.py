"""Words-only reference membership, independent of the planned learner state."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

from scripts.audit.source_inventory_intake import _SAFE_LOADER, _records_from_structured_inventory

from .quote_bytes import VesumUnavailable

INVENTORY_PATH = Path(__file__).resolve().parents[3] / "registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml"
CLOSED_CLASS_PATH = Path(__file__).with_name("data") / "a1-closed-class.yaml"


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
    _records_from_structured_inventory(payload, inventory_path="scripts/curriculum/validate/data/a1-closed-class.yaml")
    rows = [row for source in payload["sources"] for row in source["headwords"]]
    if not isinstance(rows, list) or not rows:
        raise ValueError("A1 closed-class words must be a nonempty list")
    members = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("source") != "PULS":
            raise ValueError("invalid A1 closed-class source")
        fields = {"lemma", "kind", "class", "level", "source"}
        if (
            set(row) != fields
            or row.get("kind") != "word"
            or row.get("level") != "A1"
            or row.get("class") not in {"pron", "conj", "prep", "part"}
            or not isinstance(row.get("lemma"), str)
            or not re.fullmatch(r"[а-яіїєґ’\-]+", row["lemma"])
            or normalize(row["lemma"]) != row["lemma"]
        ):
            raise ValueError("invalid A1 closed-class word")
        key = (row["lemma"], row["class"])
        if key in members:
            raise ValueError("duplicate A1 closed-class word/class")
        members.add(key)
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
    return (
        bool(classes)
        and all((normalize(lemma), cls) in attestations for cls in classes)
        and all("pron" in tags.split(":") or tags.split(":")[0] in {"conj", "prep", "part"} for tags in form_tags)
    )


def lemma_form_tags(spelling: str) -> frozenset[str]:
    """Read VESUM tags bound to the candidate lemma; failed lookup stays unknown."""
    from scripts.verification.vesum import verify_word

    try:
        analyses = verify_word(spelling)
    except (OSError, sqlite3.Error) as error:
        raise VesumUnavailable("replacement VESUM lookup failed") from error
    return frozenset(row["tags"] for row in analyses if normalize(row["lemma"]) == normalize(spelling))


def teaching_replacements(
    form_tags: frozenset[str], readable, lemma_tags, path: Path = INVENTORY_PATH
) -> tuple[str, ...]:
    """Teaching replacements: same POS, open class, common word, >=3 letters."""
    positions = {tags.split(":")[0] for tags in form_tags}
    if not positions & {"noun", "adj", "verb", "adv", "numr", "intj", "noninfl"}:
        return ()  # no supported open-class POS can match an inventory candidate
    closed = {lemma for lemma, _ in closed_class_a1()}
    _, common = reference_spellings(path)
    choices = set()
    for record in _records_from_structured_inventory(
        yaml.load(path.read_bytes().decode("utf-8-sig"), Loader=_SAFE_LOADER),
        inventory_path=str(path),
    ):
        if record.kind == "phrase":
            continue
        record_positions = set(record.vesum_pos or ()) if record.pos == "unlabelled" else {record.pos}
        if not positions & record_positions or record_positions & {"conj", "prep", "part"}:
            continue
        for spelling in (record.lemma, *record.variants):
            spelling = normalize(spelling)
            if (
                spelling not in common
                or spelling in closed
                or sum(c.isalpha() for c in spelling) < 3
                or not readable(spelling)
            ):
                continue
            tags = lemma_tags(spelling)
            if not tags or any(
                "pron" in t.split(":") or t.split(":")[0] in {"prep", "conj", "part"} or "prop" in t.split(":")
                for t in tags
            ):
                continue
            choices.add(spelling)
    return tuple(sorted(choices))


def teaching_replacement_text(form_tags: frozenset[str], readable, lemma_tags, path: Path = INVENTORY_PATH) -> str:
    """Render at most three teaching candidates, or the explicit no-replacement result."""
    choices = teaching_replacements(form_tags, readable, lemma_tags, path)
    return ", ".join(choices[:3]) if choices else "no replacement found"
