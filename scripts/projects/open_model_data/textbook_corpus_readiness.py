#!/usr/bin/env python3
"""Reconcile retained textbook PDFs, chunk JSONL files, and SQLite rows.

This is a read-only, text-free readiness receipt.  It recursively inventories
the configured retained store and reports only paths relative to that store,
file hashes, sizes, counts, and provenance metadata.  It never copies a PDF,
opens SQLite for writing, or emits chunk text.

The deterministic predicates are:

* ``ready``: at least one PDF, one non-empty/available chunk JSONL, and one
  SQLite ``textbooks`` row are present for the reconciled source, and the
  extraction is not suspect.
* ``pdf_without_chunks``: a PDF is present and no chunk JSONL is present.
* ``chunks_without_pdf``: a chunk JSONL is present and no PDF is present.
* ``chunks_not_ingested``: chunk JSONL is present but its reconciled SQLite
  row count is zero.
* ``db_without_chunks``: SQLite rows are present but no chunk JSONL is present.
* ``suspect_extraction``: a chunk JSONL has zero, one, or two non-empty rows,
  or a PDF has a known page count of at least 20 and fewer than 0.05 rows per
  page.  This intentionally flags a 273-page PDF with two rows without any
  network or PDF text extraction.
* ``missing_selected_source``: a selected source has no PDF, chunk JSONL, or
  SQLite rows after split-volume reconciliation.

Split components are recognized only by a terminal ``-1``, ``-2``, ``_1``,
``_2``, ``-part-1``/``-part-2`` (and equivalent ``part1``/``part2`` or
``vol1``/``vol2``) suffix.  A component is grouped with a selected common
slug only when the complete stem is that slug plus one of those suffixes;
numeric years and other terminal numbers are not stripped.

Chunk-payload hashes are SHA-256 hashes of canonical JSON for each parsed
non-empty JSONL row (or of the stripped raw bytes for an invalid row).  Raw
row/file occurrences remain visible in duplicate groups, while unique counts
are reported separately so duplicates do not inflate corpus counts.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml

try:
    from scripts.wiki.textbook_subjects import (
        AUTHOR_UK_BY_TRANSLIT,
        normalize_subject_slug,
        subject_for_source_file,
    )
except ModuleNotFoundError:
    # Preserve direct-script execution in addition to package execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from scripts.wiki.textbook_subjects import (
        AUTHOR_UK_BY_TRANSLIT,
        normalize_subject_slug,
        subject_for_source_file,
    )

SCHEMA_VERSION = "textbook_corpus_readiness_v1"
HASH_BLOCK_SIZE = 1024 * 1024
SUSPECT_MAX_ROWS = 2
SUSPECT_MIN_PAGES = 20
SUSPECT_ROWS_PER_PAGE = 0.05
PDF_SUFFIX = ".pdf"
JSONL_SUFFIX = ".jsonl"

_COMPONENT_RE = re.compile(
    r"(?i)^(?P<base>.+?)(?:[-_](?:(?:part|volume|vol|p)[-_]?)?(?P<number>[12]))$"
)
_MOJIBAKE_RE = re.compile(
    r"[À-ÿ]{2,}|(?:Р[°µЅ])|(?:С[Ѓ‚])|â€�"
)
_LOCATOR_KEYS = frozenset(
    {
        "url",
        "urls",
        "source_url",
        "source_urls",
        "acquisition_url",
        "acquisition_urls",
        "download_url",
        "download_urls",
        "pdf_url",
        "pdf_urls",
        "locator",
        "locators",
        "source_locator",
        "source_locators",
    }
)
_SOURCE_KEYS = (
    "source_file",
    "canonical_source",
    "source_slug",
    "slug",
    "book_slug",
    "book_id",
    "id",
    "name",
    "file",
    "filename",
)
_STATUS_ORDER = (
    "ready",
    "pdf_without_chunks",
    "chunks_without_pdf",
    "chunks_not_ingested",
    "db_without_chunks",
    "suspect_extraction",
    "missing_selected_source",
)
_PREDICATES = {
    "ready": (
        "pdf_present and chunks_present and db_row_count > 0 and not suspect_extraction"
    ),
    "pdf_without_chunks": "pdf_present and not chunks_present",
    "chunks_without_pdf": "chunks_present and not pdf_present",
    "chunks_not_ingested": "chunks_present and db_row_count == 0",
    "db_without_chunks": "db_row_count > 0 and not chunks_present",
    "suspect_extraction": (
        "any chunk file has <= 2 rows, or known_pdf_pages >= 20 and rows/pages < 0.05"
    ),
    "missing_selected_source": (
        "selected and not pdf_present and not chunks_present and db_row_count == 0"
    ),
}


class ReadinessError(ValueError):
    """Raised when a readiness input cannot be read safely."""


def canonical_json(value: Any) -> str:
    """Return the canonical UTF-8 JSON representation used by the receipt."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    """Hash a file in bounded blocks without exposing its contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(HASH_BLOCK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def _slug_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "-".join("".join(char if char.isalnum() else " " for char in normalized).split())


def _source_covers_grade(source_key: str, grade: int) -> bool:
    match = re.search(r"(?:^|-)(\d{1,2})(?:-(\d{1,2}))?-klas(?:-|$)", source_key)
    if match is None:
        return False
    first = int(match.group(1))
    last = int(match.group(2) or first)
    return first <= grade <= last


def _stem(value: str) -> str:
    text = Path(str(value or "")).name
    for suffix in (JSONL_SUFFIX, PDF_SUFFIX):
        if text.casefold().endswith(suffix):
            return text[: -len(suffix)]
    return text


def split_component(stem: str) -> tuple[str, str]:
    """Return ``(common_stem, component)`` using the documented suffix rule."""
    match = _COMPONENT_RE.match(_stem(stem))
    if not match:
        return _stem(stem), "base"
    return match.group("base"), f"part-{match.group('number')}"


def _safe_source_identifier(value: str) -> str:
    """Keep source IDs useful while preventing local mount paths from leaking."""
    text = str(value or "").strip()
    if not text:
        return "<empty-source-file>"
    if os.path.isabs(text) or text.casefold().startswith("file:"):
        return "<local-source-file-redacted>"
    return _stem(text)


def _safe_locator(value: str) -> str:
    """Retain external locators but redact local absolute paths."""
    text = str(value or "").strip()
    if not text:
        return ""
    if os.path.isabs(text) or text.casefold().startswith("file:"):
        return "<local-locator-redacted>"
    return text


def _read_yaml_or_json(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ReadinessError(f"cannot read input document: {path.name}") from exc


def _selection_items(document: Any) -> list[Mapping[str, Any] | str]:
    if isinstance(document, Mapping):
        for key in ("books", "selection", "sources", "items"):
            value = document.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, (Mapping, str))]
        # A simple source -> locator/metadata mapping is also accepted.
        return [dict({"slug": key}, **(value if isinstance(value, Mapping) else {})) for key, value in document.items()]
    if isinstance(document, list):
        return [item for item in document if isinstance(item, (Mapping, str))]
    return []


def _selection_source(
    item: Mapping[str, Any] | str,
) -> tuple[str, str, set[str], dict[str, Any]] | None:
    if isinstance(item, str):
        value = _stem(item)
        return value, value, {_slug_key(value)}, {}
    values = {key: str(item.get(key) or "").strip() for key in _SOURCE_KEYS}
    display = next(
        (
            values[key]
            for key in (
                "source_file",
                "slug",
                "book_slug",
                "canonical_source",
                "file",
                "filename",
                "id",
                "name",
            )
            if values[key]
        ),
        "",
    )
    if not display:
        return None
    display = _stem(display)
    aliases = {_slug_key(display)}
    for value in values.values():
        if value:
            aliases.add(_slug_key(_stem(value)))
    selection_id = _safe_source_identifier(values.get("id") or display)
    metadata: dict[str, Any] = {}
    with contextlib.suppress(KeyError, TypeError, ValueError):
        metadata["grade"] = int(item["grade"])
    with contextlib.suppress(KeyError, TypeError, ValueError):
        metadata["year"] = int(item["year"])
    subject = normalize_subject_slug(str(item.get("subject") or ""))
    if subject:
        metadata["subject"] = subject
    author = unicodedata.normalize("NFKC", str(item.get("author") or "")).casefold().strip()
    if author:
        metadata["author"] = author
        metadata["author_tokens"] = sorted(
            latin.casefold()
            for latin, cyrillic in AUTHOR_UK_BY_TRANSLIT.items()
            if cyrillic.casefold() in author
        )
    return display, selection_id, aliases, metadata


class _SourceIndex:
    """Match file/DB/map identifiers to selected or discovered source groups."""

    def __init__(self, items: Sequence[Mapping[str, Any] | str]) -> None:
        self.selected: dict[str, dict[str, Any]] = {}
        self.aliases: dict[str, str] = {}
        for item in items:
            parsed = _selection_source(item)
            if parsed is None:
                continue
            display, selection_id, aliases, metadata = parsed
            key = _slug_key(display)
            selected = self.selected.setdefault(
                key,
                {
                    "source": display,
                    "selection_ids": set(),
                    "aliases": set(),
                    "metadata": metadata,
                },
            )
            selected["selection_ids"].add(selection_id)
            selected["aliases"].update(aliases)
            for alias in aliases:
                self.aliases[alias] = key

    def _metadata_match(self, raw: str) -> str | None:
        """Resolve renamed retained files by explicit selection metadata.

        Acquisition-page slugs often start with a website numeric ID, while
        retained files use canonical ``grade-subject-author-year`` names.  A
        match is accepted only when grade, subject, and a verified author token
        agree and exactly one selection row qualifies.  If the retained name
        carries a four-digit year, it must also agree; an absent year is allowed
        because a few legacy canonical names omit it.
        """
        raw_key = _slug_key(raw)
        raw_subject = subject_for_source_file(raw_key)
        raw_years = {int(value) for value in re.findall(r"(?<!\d)(20\d{2})(?!\d)", raw_key)}
        matches: list[str] = []
        for key, selected in self.selected.items():
            metadata = selected.get("metadata") or {}
            grade = metadata.get("grade")
            subject = metadata.get("subject")
            author_tokens = metadata.get("author_tokens") or []
            if not grade or not subject or not author_tokens:
                continue
            if not _source_covers_grade(raw_key, int(grade)):
                continue
            if raw_subject != subject and not (
                int(grade) == 1 and subject == "ukrmova" and raw_subject == "bukvar"
            ):
                continue
            if not any(re.search(rf"(?:^|-){re.escape(token)}(?:-|$)", raw_key) for token in author_tokens):
                continue
            year = metadata.get("year")
            if raw_years and year not in raw_years:
                continue
            matches.append(key)
        return matches[0] if len(matches) == 1 else None

    def resolve(self, value: str) -> tuple[str, str, str]:
        raw = _stem(value)
        raw_key = _slug_key(raw)
        if raw_key in self.aliases:
            selected_key = self.aliases[raw_key]
            return selected_key, self.selected[selected_key]["source"], "base"

        base, component = split_component(raw)
        base_key = _slug_key(base)
        if base_key in self.aliases:
            selected_key = self.aliases[base_key]
            return selected_key, self.selected[selected_key]["source"], component

        selected_key = self._metadata_match(base)
        if selected_key is not None:
            return selected_key, self.selected[selected_key]["source"], component

        return base_key, base, component

    def ensure_discovered(self, key: str, source: str) -> dict[str, Any]:
        # Discovered inventory sources must not become selected sources.  The
        # selected mapping is intentionally limited to the selection input so
        # missing_selected_source remains meaningful.
        return self.selected.get(
            key,
            {"source": source, "selection_ids": set(), "aliases": set(), "metadata": {}},
        )


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _enumerate_files(root: Path, suffix: str) -> list[Path]:
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.casefold() == suffix),
        key=lambda path: _relative_path(root, path),
    )


def _pdf_page_count(path: Path) -> int | None:
    """Read page count without extracting or emitting PDF text."""
    try:
        from pypdf import PdfReader

        count = len(PdfReader(str(path), strict=False).pages)
        if count:
            return count
    except Exception:
        pass

    page_pattern = re.compile(rb"/Type\s*/Page(?:\s|/|>)")
    count_pattern = re.compile(rb"/Count\s+(\d+)")
    page_count = 0
    tree_count = 0
    tail = b""
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(HASH_BLOCK_SIZE), b""):
                data = tail + block
                page_count += len(page_pattern.findall(data)) - len(page_pattern.findall(tail))
                counts = [int(value) for value in count_pattern.findall(data)]
                if counts:
                    tree_count = max(tree_count, *counts)
                tail = data[-64:]
    except OSError:
        return None
    return page_count or tree_count or None


def _has_mojibake(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_MOJIBAKE_RE.search(value))
    if isinstance(value, Mapping):
        return any(_has_mojibake(key) or _has_mojibake(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_has_mojibake(item) for item in value)
    return False


def _jsonl_stats(path: Path, relative: str) -> tuple[dict[str, Any], dict[str, list[int]]]:
    digest = hashlib.sha256()
    row_count = invalid_rows = mojibake_rows = total_bytes = 0
    payload_counts: Counter[str] = Counter()
    occurrences: dict[str, list[int]] = defaultdict(list)
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            digest.update(raw_line)
            total_bytes += len(raw_line)
            stripped = raw_line.strip()
            if not stripped:
                continue
            row_count += 1
            try:
                decoded = stripped.decode("utf-8")
                row = json.loads(decoded)
            except (UnicodeDecodeError, json.JSONDecodeError):
                invalid_rows += 1
                payload = stripped
                mojibake_rows += int(bool(_MOJIBAKE_RE.search(stripped.decode("utf-8", errors="replace"))))
            else:
                payload = canonical_json(row).encode("utf-8")
                mojibake_rows += int(_has_mojibake(row))
            payload_hash = hashlib.sha256(payload).hexdigest()
            payload_counts[payload_hash] += 1
            occurrences[payload_hash].append(line_number)

    stats = {
        "path": relative,
        "byte_size": total_bytes,
        "sha256": digest.hexdigest(),
        "row_count": row_count,
        "unique_payload_count": len(payload_counts),
        "duplicate_payload_count": row_count - len(payload_counts),
        "invalid_row_count": invalid_rows,
        "mojibake_rows": mojibake_rows,
    }
    return stats, occurrences


def _read_db(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "available": path.is_file(),
        "table_present": False,
        "row_count": 0,
        "rows_by_source": {},
        "error": None,
    }
    if not path.is_file():
        result["error"] = "database_missing"
        return result

    uri = f"file:{quote(str(path.resolve()), safe='/')}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
    except (OSError, sqlite3.Error):
        result["error"] = "database_unreadable"
        return result
    try:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'textbooks'"
        ).fetchone()
        if table is None:
            result["error"] = "textbooks_table_missing"
            return result
        result["table_present"] = True
        columns = {row[1] for row in connection.execute("PRAGMA table_info(textbooks)")}
        if "source_file" in columns:
            rows = connection.execute(
                "SELECT source_file, COUNT(*) FROM textbooks GROUP BY source_file ORDER BY source_file"
            ).fetchall()
            by_source: dict[str, int] = {}
            for source_file, count in rows:
                key = _safe_source_identifier(str(source_file or ""))
                by_source[key] = by_source.get(key, 0) + int(count)
            result["rows_by_source"] = by_source
        else:
            total = int(connection.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0])
            result["rows_by_source"] = {"<missing-source-file>": total} if total else {}
        result["row_count"] = sum(result["rows_by_source"].values())
    except sqlite3.Error:
        result["error"] = "textbooks_table_unreadable"
    finally:
        connection.close()
    return result


def _looks_like_locator(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    return text.startswith(("http://", "https://", "ftp://"))


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _strings(item)


def _map_source_key(value: Mapping[str, Any], inherited: str | None) -> str | None:
    for key in _SOURCE_KEYS:
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return _stem(candidate)
    return inherited


def _extract_locators(value: Any, inherited: str | None = None) -> dict[str, list[str]]:
    extracted: dict[str, list[str]] = defaultdict(list)

    def visit(node: Any, source: str | None) -> None:
        if isinstance(node, Mapping):
            current = _map_source_key(node, source)
            for key, child in node.items():
                key_text = str(key).casefold()
                if key_text in _LOCATOR_KEYS:
                    for locator in _strings(child):
                        if _looks_like_locator(locator) and current:
                            extracted[current].append(locator.strip())
                    continue
                if isinstance(child, str) and _looks_like_locator(child):
                    extracted[_stem(str(key))].append(child.strip())
                elif isinstance(child, (Mapping, list, tuple)):
                    visit(child, current or (_stem(str(key)) if isinstance(child, Mapping) else source))
        elif isinstance(node, list):
            for child in node:
                visit(child, source)

    visit(value, inherited)
    return {key: sorted(set(values)) for key, values in sorted(extracted.items())}


def _load_url_maps(paths: Sequence[Path]) -> tuple[list[dict[str, Any]], dict[int, dict[str, list[str]]]]:
    metadata: list[dict[str, Any]] = []
    maps: dict[int, dict[str, list[str]]] = {}
    for index, path in enumerate(paths):
        record: dict[str, Any] = {"index": index, "present": path.is_file(), "source_count": 0, "locator_count": 0}
        if not path.is_file():
            record["error"] = "map_missing"
            metadata.append(record)
            continue
        try:
            values = _extract_locators(_read_yaml_or_json(path))
        except ReadinessError:
            values = {}
            record["error"] = "map_unreadable"
        maps[index] = values
        record["source_count"] = len(values)
        record["locator_count"] = sum(len(locators) for locators in values.values())
        metadata.append(record)
    return metadata, maps


def _duplicate_pdf_groups(pdf_files: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_hash: dict[str, list[str]] = defaultdict(list)
    for record in pdf_files:
        by_hash[str(record["sha256"])].append(str(record["path"]))
    return [
        {"sha256": digest, "count": len(paths), "paths": sorted(paths)}
        for digest, paths in sorted(by_hash.items())
        if len(paths) > 1
    ]


def _duplicate_payload_groups(occurrences: Mapping[str, list[tuple[str, int]]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for digest, values in sorted(occurrences.items()):
        if len(values) < 2:
            continue
        by_path: dict[str, list[int]] = defaultdict(list)
        for path, line_number in values:
            by_path[path].append(line_number)
        groups.append(
            {
                "sha256": digest,
                "count": len(values),
                "occurrences": [
                    {"path": path, "row_numbers": sorted(numbers)}
                    for path, numbers in sorted(by_path.items())
                ],
            }
        )
    return groups


def _ordered_states(states: Iterable[str]) -> list[str]:
    order = {name: index for index, name in enumerate(_STATUS_ORDER)}
    return sorted(set(states), key=lambda value: (order.get(value, len(order)), value))


def _source_states(
    *,
    selected: bool,
    pdf_present: bool,
    chunks_present: bool,
    db_rows: int,
    suspect: bool,
) -> tuple[str, list[str]]:
    states: list[str] = []
    if selected and not pdf_present and not chunks_present and db_rows == 0:
        states.append("missing_selected_source")
    if pdf_present and not chunks_present:
        states.append("pdf_without_chunks")
    if chunks_present and not pdf_present:
        states.append("chunks_without_pdf")
    if chunks_present and db_rows == 0:
        states.append("chunks_not_ingested")
    if db_rows > 0 and not chunks_present:
        states.append("db_without_chunks")
    if suspect:
        states.append("suspect_extraction")
    if pdf_present and chunks_present and db_rows > 0 and not suspect:
        states.append("ready")
    states = _ordered_states(states)
    if "missing_selected_source" in states:
        primary = "missing_selected_source"
    elif "suspect_extraction" in states:
        primary = "suspect_extraction"
    elif "ready" in states:
        primary = "ready"
    elif states:
        primary = states[0]
    else:
        primary = "untracked"
    return primary, states


def build_report(
    *,
    gdrive_root: Path,
    db_path: Path,
    selection_path: Path,
    url_maps: Sequence[Path] = (),
) -> dict[str, Any]:
    """Build a deterministic text-free readiness report from local inputs."""
    root = Path(gdrive_root).expanduser()
    if not root.exists() or not root.is_dir():
        raise ReadinessError("gdrive root is missing or not a directory")
    root = root.resolve()
    # The configured Drive root also contains literary and reference corpora.
    # Restrict a normal project layout to its two textbook stores; retain the
    # direct-root fallback for small standalone fixtures and explicit stores.
    pdf_root = root / "textbooks" if (root / "textbooks").is_dir() else root
    chunks_root = (
        root / "textbook_chunks"
        if (root / "textbook_chunks").is_dir()
        else root
    )

    selection = _read_yaml_or_json(Path(selection_path))
    selection_items = _selection_items(selection)
    index = _SourceIndex(selection_items)
    url_map_metadata, loaded_maps = _load_url_maps([Path(path) for path in url_maps])

    pdf_records: list[dict[str, Any]] = []
    jsonl_records: list[dict[str, Any]] = []
    payload_occurrences: dict[str, list[tuple[str, int]]] = defaultdict(list)
    source_data: dict[str, dict[str, Any]] = {}

    def source_bucket(key: str, source: str) -> dict[str, Any]:
        bucket = source_data.setdefault(
            key,
            {
                "source": source,
                "pdfs": [],
                "chunks": [],
                "db_rows": 0,
                "db_sources": [],
                "payload_hashes": set(),
                "components": defaultdict(
                    lambda: {"pdfs": [], "chunks": [], "db_rows": 0, "db_sources": []}
                ),
            },
        )
        if source < bucket["source"]:
            bucket["source"] = source
        return bucket

    for key, selected in index.selected.items():
        source_bucket(key, selected["source"])

    for path in _enumerate_files(pdf_root, PDF_SUFFIX):
        relative = _relative_path(root, path)
        key, source, component = index.resolve(path.stem)
        index.ensure_discovered(key, source)
        record = {
            "path": relative,
            "byte_size": path.stat().st_size,
            "sha256": sha256_file(path),
            "page_count": _pdf_page_count(path),
            "source": source,
            "component": component,
        }
        pdf_records.append(record)
        bucket = source_bucket(key, source)
        bucket["pdfs"].append(record)
        bucket["components"][component]["pdfs"].append(record)

    for path in _enumerate_files(chunks_root, JSONL_SUFFIX):
        relative = _relative_path(root, path)
        key, source, component = index.resolve(path.stem)
        index.ensure_discovered(key, source)
        stats, row_occurrences = _jsonl_stats(path, relative)
        stats.update({"source": source, "component": component})
        jsonl_records.append(stats)
        bucket = source_bucket(key, source)
        bucket["chunks"].append(stats)
        bucket["components"][component]["chunks"].append(stats)
        bucket["payload_hashes"].update(row_occurrences)
        for payload_hash, row_numbers in row_occurrences.items():
            payload_occurrences[payload_hash].extend((relative, number) for number in row_numbers)

    db = _read_db(Path(db_path).expanduser())
    if not db["available"] or db["error"] is not None or not db["table_present"]:
        raise ReadinessError(
            f"textbook database is not readable: {db['error'] or 'unknown_database_error'}"
        )
    for raw_source, row_count in sorted(db["rows_by_source"].items()):
        key, source, component = index.resolve(raw_source)
        index.ensure_discovered(key, source)
        bucket = source_bucket(key, source)
        bucket["db_rows"] += int(row_count)
        bucket["db_sources"].append(_safe_source_identifier(raw_source))
        bucket["components"][component]["db_rows"] += int(row_count)
        bucket["components"][component]["db_sources"].append(_safe_source_identifier(raw_source))

    locator_data: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for map_index, values in loaded_maps.items():
        for raw_source, locators in values.items():
            key, source, _component = index.resolve(raw_source)
            index.ensure_discovered(key, source)
            source_bucket(key, source)
            for locator in locators:
                safe = _safe_locator(locator)
                if safe:
                    locator_data[key].append({"map_index": map_index, "locator": safe})

    sources: list[dict[str, Any]] = []
    for key in sorted(source_data, key=lambda value: (value, source_data[value]["source"])):
        bucket = source_data[key]
        selected = index.selected.get(key)
        pdfs = sorted(bucket["pdfs"], key=lambda record: record["path"])
        chunks = sorted(bucket["chunks"], key=lambda record: record["path"])
        db_rows = int(bucket["db_rows"])
        total_rows = sum(int(record["row_count"]) for record in chunks)
        page_counts = [record["page_count"] for record in pdfs if record["page_count"] is not None]
        suspect = any(int(record["row_count"]) <= SUSPECT_MAX_ROWS for record in chunks)
        if page_counts and total_rows:
            suspect = suspect or any(
                pages >= SUSPECT_MIN_PAGES and total_rows / pages < SUSPECT_ROWS_PER_PAGE
                for pages in page_counts
            )
        elif page_counts and chunks and total_rows == 0:
            suspect = True
        primary, states = _source_states(
            selected=selected is not None,
            pdf_present=bool(pdfs),
            chunks_present=bool(chunks),
            db_rows=db_rows,
            suspect=suspect,
        )

        components: list[dict[str, Any]] = []
        component_data = bucket["components"]
        for component in sorted(component_data):
            values = component_data[component]
            components.append(
                {
                    "component": component,
                    "pdf_paths": sorted(record["path"] for record in values["pdfs"]),
                    "chunk_paths": sorted(record["path"] for record in values["chunks"]),
                    "db_source_files": sorted(set(values["db_sources"])),
                    "db_row_count": int(values["db_rows"]),
                }
            )

        locators = sorted(
            set(
                (int(item["map_index"]), str(item["locator"]))
                for item in locator_data.get(key, [])
            )
        )
        source_record = {
            "source": bucket["source"],
            "selected": selected is not None,
            "selection_ids": sorted(selected["selection_ids"]) if selected else [],
            "status": primary,
            "states": states,
            "pdf": {
                "present": bool(pdfs),
                "file_count": len(pdfs),
                "byte_size": sum(int(record["byte_size"]) for record in pdfs),
                "paths": [record["path"] for record in pdfs],
                "page_counts": page_counts,
            },
            "chunks": {
                "present": bool(chunks),
                "file_count": len(chunks),
                "row_count": total_rows,
                "unique_payload_count": len(bucket["payload_hashes"]),
                "mojibake_rows": sum(int(record["mojibake_rows"]) for record in chunks),
                "paths": [record["path"] for record in chunks],
            },
            "db": {"row_count": db_rows, "source_files": sorted(set(bucket["db_sources"]))},
            "components": components,
            "acquisition_locators": [
                {"map_index": map_index, "locator": locator}
                for map_index, locator in locators
            ],
        }
        sources.append(source_record)

    pdf_hashes = [str(record["sha256"]) for record in pdf_records]
    chunk_row_count = sum(int(record["row_count"]) for record in jsonl_records)
    unique_chunk_payload_count = len(payload_occurrences)
    mojibake_files = [record for record in jsonl_records if int(record["mojibake_rows"]) > 0]

    report = {
        "schema_version": SCHEMA_VERSION,
        "predicates": dict(_PREDICATES),
        "split_volume_rule": (
            "terminal -1/-2, _1/_2, -part-1/-part-2, -part1/-part2, "
            "-vol1/-vol2, -volume-1/-volume-2, or -p1/-p2 only"
        ),
        "selection": {
            "selected_count": len(index.selected),
            "selected_sources": [
                {
                    "source": index.selected[key]["source"],
                    "selection_ids": sorted(index.selected[key]["selection_ids"]),
                }
                for key in sorted(index.selected)
            ],
        },
        "url_maps": url_map_metadata,
        "database": {
            "available": bool(db["available"]),
            "table_present": bool(db["table_present"]),
            "row_count": int(db["row_count"]),
            "source_count": len(db["rows_by_source"]),
            "error": db["error"],
        },
        "counts": {
            "pdf_files": len(pdf_records),
            "unique_pdf_hashes": len(set(pdf_hashes)),
            "chunk_files": len(jsonl_records),
            "chunk_rows": chunk_row_count,
            "unique_chunk_payloads": unique_chunk_payload_count,
            "db_rows": int(db["row_count"]),
        },
        "files": {
            "pdfs": [
                {
                    "path": record["path"],
                    "byte_size": record["byte_size"],
                    "sha256": record["sha256"],
                    "page_count": record["page_count"],
                }
                for record in sorted(pdf_records, key=lambda item: item["path"])
            ],
            "chunks": [
                {
                    key: record[key]
                    for key in (
                        "path",
                        "byte_size",
                        "sha256",
                        "row_count",
                        "unique_payload_count",
                        "duplicate_payload_count",
                        "invalid_row_count",
                        "mojibake_rows",
                    )
                }
                for record in sorted(jsonl_records, key=lambda item: item["path"])
            ],
        },
        "duplicates": {
            "duplicate_pdf_hashes": _duplicate_pdf_groups(pdf_records),
            "duplicate_chunk_payload_hashes": _duplicate_payload_groups(payload_occurrences),
        },
        "mojibake": {
            "jsonl_files": len(mojibake_files),
            "rows": sum(int(record["mojibake_rows"]) for record in jsonl_records),
            "files": sorted(record["path"] for record in mojibake_files),
        },
        "sources": sources,
    }
    # A source map may identify a source with a locator but no retained bytes;
    # it is intentionally represented as an untracked source, not a selected
    # missing source.  All emitted paths above are root-relative by construction.
    return report


build_readiness_report = build_report
reconcile_corpus = build_report


def write_atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    """Write canonical JSON atomically in the output file's directory."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(canonical_json(value))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gdrive-root", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--url-map", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_report(
            gdrive_root=args.gdrive_root,
            db_path=args.db,
            selection_path=args.selection,
            url_maps=args.url_map,
        )
        write_atomic_json(args.output, report)
    except (OSError, ReadinessError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote deterministic readiness receipt: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
