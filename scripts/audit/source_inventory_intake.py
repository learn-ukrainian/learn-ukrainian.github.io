#!/usr/bin/env python3
"""Parse curated source inventories for Word Atlas growth candidates."""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.lemma_normalization import strip_acute_stress

INVENTORY_KIND = "atlas_source_inventory"
INVENTORY_VERSION = 1
_TEXT_ENCODING = "utf-8-sig"

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")

_TOP_LEVEL_FIELDS = {"version", "kind", "sources"}
_SOURCE_FIELDS = {
    "id",
    "source_family",
    "extraction_mode",
    "title",
    "url",
    "path",
    "locator",
    "notes",
    "headwords",
}
_HEADWORD_FIELDS = {"lemma", "headword", "word", "pos", "gloss", "locator", "context", "notes"}
_FLAT_FIELDS = {
    "lemma",
    "source_family",
    "extraction_mode",
    "source_id",
    "source_title",
    "source_url",
    "source_path",
    "source_locator",
    "context",
    "pos",
    "gloss",
    "notes",
}
_FLAT_ALIASES = {
    "headword": "lemma",
    "word": "lemma",
    "family": "source_family",
    "source": "source_family",
    "mode": "extraction_mode",
    "extraction": "extraction_mode",
    "id": "source_id",
    "title": "source_title",
    "url": "source_url",
    "path": "source_path",
    "locator": "source_locator",
    "snippet": "context",
    "example": "context",
    "part_of_speech": "pos",
    "translation": "gloss",
}


class SourceInventoryError(ValueError):
    """Raised when a source inventory is malformed."""


@dataclass(frozen=True)
class SourceInventoryRecord:
    """One source-backed Atlas headword row."""

    lemma: str
    source_family: str
    extraction_mode: str
    inventory_path: str
    inventory_locator: str
    source_id: str | None = None
    source_title: str | None = None
    source_url: str | None = None
    source_path: str | None = None
    source_locator: str | None = None
    context: str | None = None
    pos: str | None = None
    gloss: str | None = None
    notes: str | None = None

    def provenance_payload(self) -> dict[str, Any]:
        """Return JSON-ready provenance for a candidate entry."""
        payload: dict[str, Any] = {
            "source_family": self.source_family,
            "extraction_mode": self.extraction_mode,
            "inventory_path": self.inventory_path,
            "inventory_locator": self.inventory_locator,
        }
        optional = {
            "source_id": self.source_id,
            "source_title": self.source_title,
            "source_url": self.source_url,
            "source_path": self.source_path,
            "source_locator": self.source_locator,
            "context": self.context,
            "notes": self.notes,
        }
        payload.update({key: value for key, value in optional.items() if value})
        return payload


@dataclass(frozen=True)
class SourceInventoryCandidate:
    """One deduped Atlas candidate plus merged source provenance."""

    lemma: str
    pos: str | None
    gloss: str | None
    source_provenance: tuple[dict[str, Any], ...]


def read_source_inventories(
    paths: Sequence[Path],
    *,
    project_root: Path | None = None,
) -> list[SourceInventoryRecord]:
    """Read and validate one or more source inventory files."""
    records: list[SourceInventoryRecord] = []
    for path in paths:
        records.extend(read_source_inventory(path, project_root=project_root))
    return records


def read_source_inventory(
    path: Path,
    *,
    project_root: Path | None = None,
) -> list[SourceInventoryRecord]:
    """Read a CSV/TSV/JSONL row inventory or YAML/JSON source inventory."""
    if not path.exists():
        raise SourceInventoryError(f"source inventory not found: {path}")

    suffix = path.suffix.lower()
    inventory_path = _display_path(path, project_root)
    if suffix == ".csv":
        return _read_delimited_inventory(path, delimiter=",", inventory_path=inventory_path)
    if suffix == ".tsv":
        return _read_delimited_inventory(path, delimiter="\t", inventory_path=inventory_path)
    if suffix == ".jsonl":
        return _read_jsonl_inventory(path, inventory_path=inventory_path)
    if suffix in {".yaml", ".yml"}:
        return _records_from_structured_inventory(
            yaml.safe_load(path.read_text(encoding=_TEXT_ENCODING)),
            inventory_path=inventory_path,
        )
    if suffix == ".json":
        return _records_from_json_payload(
            json.loads(path.read_text(encoding=_TEXT_ENCODING)),
            inventory_path=inventory_path,
        )
    raise SourceInventoryError(
        f"unsupported source inventory extension for {inventory_path}; use csv, tsv, jsonl, json, or yaml"
    )


def source_inventory_candidates(
    records: Sequence[SourceInventoryRecord],
) -> list[SourceInventoryCandidate]:
    """Canonicalize source rows into deterministic, deduped candidates."""
    grouped: dict[str, dict[str, Any]] = {}
    for record in records:
        key = _lemma_key(record.lemma)
        group = grouped.setdefault(
            key,
            {
                "lemma": record.lemma,
                "pos": record.pos,
                "gloss": record.gloss,
                "source_provenance": [],
            },
        )
        existing_pos = group["pos"]
        if record.pos and existing_pos and record.pos != existing_pos:
            raise SourceInventoryError(
                f"conflicting pos for {record.lemma!r}: {existing_pos!r} vs {record.pos!r}"
            )
        if record.pos and not existing_pos:
            group["pos"] = record.pos
        existing_gloss = group["gloss"]
        if record.gloss and existing_gloss and record.gloss != existing_gloss:
            raise SourceInventoryError(
                f"conflicting gloss for {record.lemma!r}: {existing_gloss!r} vs {record.gloss!r}"
            )
        if record.gloss and not existing_gloss:
            group["gloss"] = record.gloss
        group["source_provenance"].append(record.provenance_payload())

    candidates = [
            SourceInventoryCandidate(
                lemma=str(group["lemma"]),
                pos=group["pos"],
                gloss=group["gloss"],
                source_provenance=tuple(group["source_provenance"]),
            )
        for group in grouped.values()
    ]
    return sorted(candidates, key=lambda item: _lemma_key(item.lemma))


def _read_delimited_inventory(
    path: Path,
    *,
    delimiter: str,
    inventory_path: str,
) -> list[SourceInventoryRecord]:
    with path.open(newline="", encoding=_TEXT_ENCODING) as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            raise SourceInventoryError(f"{inventory_path}: missing header row")
        return [
            _record_from_flat_row(row, inventory_path=inventory_path, locator=f"row {line_number}")
            for line_number, row in enumerate(reader, start=2)
        ]


def _read_jsonl_inventory(path: Path, *, inventory_path: str) -> list[SourceInventoryRecord]:
    records: list[SourceInventoryRecord] = []
    for line_number, line in enumerate(path.read_text(encoding=_TEXT_ENCODING).splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SourceInventoryError(f"{inventory_path}: row {line_number}: invalid JSON") from exc
        if not isinstance(row, Mapping):
            raise SourceInventoryError(f"{inventory_path}: row {line_number}: expected JSON object")
        records.append(
            _record_from_flat_row(row, inventory_path=inventory_path, locator=f"row {line_number}")
        )
    return records


def _records_from_json_payload(payload: object, *, inventory_path: str) -> list[SourceInventoryRecord]:
    if isinstance(payload, list):
        records: list[SourceInventoryRecord] = []
        for index, row in enumerate(payload, start=1):
            if not isinstance(row, Mapping):
                raise SourceInventoryError(f"{inventory_path}: row {index}: expected JSON object")
            records.append(_record_from_flat_row(row, inventory_path=inventory_path, locator=f"row {index}"))
        return records
    return _records_from_structured_inventory(payload, inventory_path=inventory_path)


def _records_from_structured_inventory(
    payload: object,
    *,
    inventory_path: str,
) -> list[SourceInventoryRecord]:
    if not isinstance(payload, Mapping):
        raise SourceInventoryError(f"{inventory_path}: expected mapping inventory")
    _reject_unknown_fields(payload, _TOP_LEVEL_FIELDS, f"{inventory_path}: top level")
    if payload.get("version") != INVENTORY_VERSION:
        raise SourceInventoryError(f"{inventory_path}: version must be {INVENTORY_VERSION}")
    if payload.get("kind") != INVENTORY_KIND:
        raise SourceInventoryError(f"{inventory_path}: kind must be {INVENTORY_KIND!r}")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SourceInventoryError(f"{inventory_path}: sources must be a non-empty list")

    records: list[SourceInventoryRecord] = []
    seen_source_ids: set[str] = set()
    for source_index, source in enumerate(sources, start=1):
        if not isinstance(source, Mapping):
            raise SourceInventoryError(f"{inventory_path}: sources[{source_index}] must be a mapping")
        locator = f"sources[{source_index}]"
        _reject_unknown_fields(source, _SOURCE_FIELDS, f"{inventory_path}: {locator}")
        source_id = _required_text(source.get("id"), "id", inventory_path, locator)
        if source_id in seen_source_ids:
            raise SourceInventoryError(f"{inventory_path}: duplicate source id {source_id!r}")
        seen_source_ids.add(source_id)
        family = _required_slug(source.get("source_family"), "source_family", inventory_path, locator)
        mode = _required_slug(source.get("extraction_mode"), "extraction_mode", inventory_path, locator)
        headwords = source.get("headwords")
        if not isinstance(headwords, list) or not headwords:
            raise SourceInventoryError(f"{inventory_path}: {locator}.headwords must be a non-empty list")
        for headword_index, headword in enumerate(headwords, start=1):
            headword_locator = f"{locator}.headwords[{headword_index}]"
            record = _record_from_structured_headword(
                headword,
                source=source,
                source_id=source_id,
                source_family=family,
                extraction_mode=mode,
                inventory_path=inventory_path,
                inventory_locator=headword_locator,
            )
            records.append(record)
    return records


def _record_from_structured_headword(
    headword: object,
    *,
    source: Mapping[str, object],
    source_id: str,
    source_family: str,
    extraction_mode: str,
    inventory_path: str,
    inventory_locator: str,
) -> SourceInventoryRecord:
    if isinstance(headword, str):
        row: Mapping[str, object] = {"lemma": headword}
    elif isinstance(headword, Mapping):
        _reject_unknown_fields(headword, _HEADWORD_FIELDS, f"{inventory_path}: {inventory_locator}")
        row = headword
    else:
        raise SourceInventoryError(f"{inventory_path}: {inventory_locator} must be string or mapping")

    return SourceInventoryRecord(
        lemma=_required_lemma(_first_present(row, ("lemma", "headword", "word")), inventory_path, inventory_locator),
        source_family=source_family,
        extraction_mode=extraction_mode,
        inventory_path=inventory_path,
        inventory_locator=inventory_locator,
        source_id=source_id,
        source_title=_optional_text(source.get("title")),
        source_url=_optional_text(source.get("url")),
        source_path=_optional_text(source.get("path")),
        source_locator=_optional_text(_first_present(row, ("locator",))) or _optional_text(source.get("locator")),
        context=_optional_text(row.get("context")),
        pos=_optional_slug(row.get("pos"), "pos", inventory_path, inventory_locator),
        gloss=_optional_text(row.get("gloss")),
        notes=_optional_text(row.get("notes")) or _optional_text(source.get("notes")),
    )


def _record_from_flat_row(
    row: Mapping[object, object],
    *,
    inventory_path: str,
    locator: str,
) -> SourceInventoryRecord:
    if None in row:
        raise SourceInventoryError(f"{inventory_path}: {locator}: row has more columns than headers")
    normalized = _normalize_flat_row(row, inventory_path=inventory_path, locator=locator)
    return SourceInventoryRecord(
        lemma=_required_lemma(normalized.get("lemma"), inventory_path, locator),
        source_family=_required_slug(normalized.get("source_family"), "source_family", inventory_path, locator),
        extraction_mode=_required_slug(normalized.get("extraction_mode"), "extraction_mode", inventory_path, locator),
        inventory_path=inventory_path,
        inventory_locator=locator,
        source_id=_optional_text(normalized.get("source_id")),
        source_title=_optional_text(normalized.get("source_title")),
        source_url=_optional_text(normalized.get("source_url")),
        source_path=_optional_text(normalized.get("source_path")),
        source_locator=_optional_text(normalized.get("source_locator")),
        context=_optional_text(normalized.get("context")),
        pos=_optional_slug(normalized.get("pos"), "pos", inventory_path, locator),
        gloss=_optional_text(normalized.get("gloss")),
        notes=_optional_text(normalized.get("notes")),
    )


def _normalize_flat_row(
    row: Mapping[object, object],
    *,
    inventory_path: str,
    locator: str,
) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for raw_key, value in row.items():
        key = _normalize_key(raw_key)
        key = _FLAT_ALIASES.get(key, key)
        if key not in _FLAT_FIELDS:
            raise SourceInventoryError(f"{inventory_path}: {locator}: unknown field {raw_key!r}")
        if key in normalized:
            raise SourceInventoryError(f"{inventory_path}: {locator}: duplicate field {key!r}")
        normalized[key] = value
    return normalized


def _reject_unknown_fields(
    row: Mapping[object, object],
    allowed: set[str],
    context: str,
) -> None:
    for key in row:
        if not isinstance(key, str) or key not in allowed:
            raise SourceInventoryError(f"{context}: unknown field {key!r}")


def _required_lemma(value: object, inventory_path: str, locator: str) -> str:
    lemma = strip_acute_stress(_required_text(value, "lemma", inventory_path, locator))
    if not lemma:
        raise SourceInventoryError(f"{inventory_path}: {locator}: lemma is required")
    return lemma


def _required_slug(value: object, field: str, inventory_path: str, locator: str) -> str:
    slug = _required_text(value, field, inventory_path, locator).casefold()
    if not _SLUG_RE.fullmatch(slug):
        raise SourceInventoryError(f"{inventory_path}: {locator}: {field} must be a lowercase slug")
    return slug


def _optional_slug(value: object, field: str, inventory_path: str, locator: str) -> str | None:
    text = _optional_text(value)
    if not text:
        return None
    slug = text.casefold()
    if not _SLUG_RE.fullmatch(slug):
        raise SourceInventoryError(f"{inventory_path}: {locator}: {field} must be a lowercase slug")
    return slug


def _required_text(value: object, field: str, inventory_path: str, locator: str) -> str:
    text = _optional_text(value)
    if not text:
        raise SourceInventoryError(f"{inventory_path}: {locator}: {field} is required")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_present(row: Mapping[str, object], keys: Sequence[str]) -> object | None:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _normalize_key(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


def _display_path(path: Path, project_root: Path | None) -> str:
    if project_root is not None:
        try:
            return str(path.resolve().relative_to(project_root.resolve()))
        except ValueError:
            pass
    return str(path)
