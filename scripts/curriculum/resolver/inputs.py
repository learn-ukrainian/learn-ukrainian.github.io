"""The resolver's two inputs: the expanded document and the allowlist.

The expanded document (`lesson-<n>.expanded.yaml`) is written by the engine
(#8431 (f), E3; its schema is the engine's). The resolver checks only the
fields it consumes. The allowlist is the contract's: planned learner state
plus the lesson's `core` and `incidental`, by word-store record. The resolver
takes it as given and never widens it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.evidence import lock, registry

from . import codes
from .tokenize import has_accent


class ResolverError(Exception):
    """A failure outcome that stops the whole run; carries the code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def canonical_sha256(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Unit:
    index: int
    tab: str
    activity: str | None
    item: int | None
    block: int | str
    role: str
    text: str

    def locator(self) -> dict[str, Any]:
        return {"tab": self.tab, "activity": self.activity, "item": self.item, "block": self.block}


@dataclass(frozen=True)
class ExpandedDocument:
    lesson: dict[str, Any]
    units: tuple[Unit, ...]
    sha256: str

    @classmethod
    def from_data(cls, data: Any, *, sha256: str | None = None) -> ExpandedDocument:
        if not isinstance(data, dict) or not isinstance(data.get("units"), list):
            raise ResolverError(codes.INVALID_INPUT, "the expanded document must be a mapping with a 'units' list")
        lesson = data.get("lesson")
        if not (
            isinstance(lesson, dict)
            and isinstance(lesson.get("level"), str)
            and isinstance(lesson.get("slug"), str)
            and isinstance(lesson.get("n"), int)
        ):
            raise ResolverError(codes.INVALID_INPUT, "the expanded document needs lesson: {level, slug, n}")
        units = []
        for index, raw in enumerate(data["units"]):
            units.append(_unit(index, raw))
        digest = sha256 if sha256 is not None else hashlib.sha256(lock.yaml_bytes(data)).hexdigest()
        return cls({"level": lesson["level"], "slug": lesson["slug"], "n": lesson["n"]}, tuple(units), digest)

    @classmethod
    def load(cls, path: Path) -> ExpandedDocument:
        path = Path(path)
        if not path.is_file():
            raise ResolverError(codes.INVALID_INPUT, f"expanded document {str(path)!r} does not exist")
        if Path(f"{path}.lock").exists():
            lock.require(path)
        content = path.read_bytes()
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as error:
            raise ResolverError(codes.INVALID_INPUT, f"{str(path)!r} is not valid YAML: {error}") from error
        return cls.from_data(data, sha256=hashlib.sha256(content).hexdigest())


def _unit(index: int, raw: Any) -> Unit:
    where = f"unit {index}"
    if not isinstance(raw, dict):
        raise ResolverError(codes.INVALID_INPUT, f"{where} is not a mapping")
    for key in ("tab", "activity", "item", "block", "role", "text"):
        if key not in raw:
            raise ResolverError(codes.INVALID_INPUT, f"{where} lacks {key!r}")
    if raw["tab"] not in codes.TABS:
        raise ResolverError(codes.INVALID_INPUT, f"{where} has unknown tab {raw['tab']!r}")
    if raw["role"] not in codes.ROLES:
        raise ResolverError(codes.INVALID_INPUT, f"{where} has unknown role {raw['role']!r}")
    if raw["activity"] is not None and not isinstance(raw["activity"], str):
        raise ResolverError(codes.INVALID_INPUT, f"{where} activity must be a string id or null")
    if raw["item"] is not None and (not isinstance(raw["item"], int) or isinstance(raw["item"], bool)):
        raise ResolverError(codes.INVALID_INPUT, f"{where} item must be an index or null")
    if isinstance(raw["block"], bool) or not isinstance(raw["block"], int | str):
        raise ResolverError(codes.INVALID_INPUT, f"{where} block must be an index or a field name")
    if not isinstance(raw["text"], str):
        raise ResolverError(codes.INVALID_INPUT, f"{where} text must be a string")
    unit = Unit(index, raw["tab"], raw["activity"], raw["item"], raw["block"], raw["role"], raw["text"])
    if has_accent(unit.text):
        raise ResolverError(
            codes.ACCENT_IN_INPUT,
            f"{where} {unit.locator()} carries a combining accent; the engine applies stress after "
            f"resolution: {unit.text!r}",
        )
    return unit


@dataclass(frozen=True)
class Allowlist:
    """Word-store records the lesson may use, plus what classification needs."""

    records: dict[str, dict[str, Any]]
    gloss_ids: frozenset[str]
    name_ids: frozenset[str]
    letters: frozenset[str]
    words_lock: str
    label: str

    @classmethod
    def from_records(
        cls,
        records: list[dict[str, Any]],
        *,
        gloss_ids: frozenset[str] | set[str] = frozenset(),
        name_ids: frozenset[str] | set[str] = frozenset(),
        letters: frozenset[str] | set[str] = frozenset(),
        words_lock: str | None = None,
        label: str = "allowlist",
    ) -> Allowlist:
        by_id: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                raise ResolverError(codes.INVALID_INPUT, f"allowlist record without an id: {record!r}")
            registry.number(record["id"])
            if record["id"] in by_id:
                raise ResolverError(codes.INVALID_INPUT, f"allowlist lists {record['id']} twice")
            by_id[record["id"]] = record
        ordered = {rid: by_id[rid] for rid in sorted(by_id, key=registry.number)}
        digest = (
            words_lock
            if words_lock is not None
            else hashlib.sha256(lock.yaml_bytes(list(ordered.values()))).hexdigest()
        )
        return cls(
            ordered,
            frozenset(gloss_ids),
            frozenset(name_ids),
            frozenset(letter.lower() for letter in letters),
            digest,
            label,
        )

    @classmethod
    def from_store(
        cls,
        store: dict[str, Any],
        ids: set[str] | frozenset[str],
        *,
        words_lock: str,
        **kwargs: Any,
    ) -> Allowlist:
        by_id = {record["id"]: record for record in store.get("words") or [] if isinstance(record, dict)}
        missing = sorted(set(ids) - set(by_id), key=registry.number)
        if missing:
            raise ResolverError(codes.UNKNOWN_WORD_ID, f"allowlist ids without a word-store record: {missing}")
        return cls.from_records([by_id[rid] for rid in ids], words_lock=words_lock, **kwargs)

    @property
    def sha256(self) -> str:
        return canonical_sha256(
            {
                "records": list(self.records),
                "gloss_ids": sorted(self.gloss_ids, key=registry.number),
                "name_ids": sorted(self.name_ids, key=registry.number),
                "letters": sorted(self.letters),
            }
        )
