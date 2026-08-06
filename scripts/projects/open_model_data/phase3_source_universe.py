#!/usr/bin/env python3
"""Freeze the Phase 3 source universe without publishing source text.

This utility is deliberately an inventory/freezer only.  It neither classifies
Ukrainian rules nor emits the words, definitions, or PDF text it reads.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import unicodedata
from collections.abc import Iterable, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = ROOT / "data/projects/open_model_data/evidence/correction_protection_coverage_contract_v1.json"
EXPECTED_2019_SHA256 = "9adcb3e7e6b68db62719a4e8b0c34d7b1f4abde2986c694ab77662f2791ad24c"
EXPECTED_2026_SHA256 = "E593956BFBA6737D991A76FA86970DB9C10A5CD7FD8895BAE67F2B9A950C3A92"
EXPECTED_PARAGRAPH_COUNT = 168
PRAVOPYS_2019_OFFICIAL_DOWNLOAD_LOCATOR = (
    "https://mon.gov.ua/storage/app/media/zagalna%20serednya/05062019-onovl-pravo.pdf"
)
PRAVOPYS_2026_DECISION_LOCATOR = (
    "https://mova.gov.ua/rozyasnennya/rishennia-2026/berezen-2026/"
    "rishennia-47-vid-1-bereznia"
)
PRAVOPYS_2026_OFFICIAL_DOWNLOAD_LOCATOR = (
    "https://mova.gov.ua/storage/app/sites/19/2026/rishennja-komisiji/01-03/"
    "sdm-ukrayinskii-pravopis-vidannia.pdf"
)
RIGHTS_PROVENANCE_CLASSIFICATION = "rights_limited_locator_only"
ISO_8601_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
GIT_SHA40 = re.compile(r"^[0-9a-f]{40}$")
FREEZER_IMPLEMENTATION_VERSION = "phase3_source_universe_freezer_v2"
FREEZER_SCRIPT_PATH = "scripts/projects/open_model_data/phase3_source_universe.py"

SOURCES_FAMILIES = {
    "lexical_balla_en_uk": "balla_en_uk",
    "lexical_dmklinger_uk_en": "dmklinger_uk_en",
    "lexical_esum_cognate_forms": "esum_cognate_forms",
    "lexical_esum_etymology": "esum_etymology",
    "lexical_frazeolohichnyi": "frazeolohichnyi",
    "lexical_grinchenko": "grinchenko",
    "lexical_puls_cefr": "puls_cefr",
    "lexical_sum11": "sum11",
    "lexical_ukrajinet": "ukrajinet",
    "lexical_wiktionary": "wiktionary",
    "antonenko_style_guide": "style_guide",
    "ua_gec": "ua_gec_errors",
    "school_textbooks": "textbooks",
    "lexical_ulif": "ulif_dictua_entries",
}
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
NORMATIVE_TABLE = re.compile(r"(?:style|normative|antonenko)", re.IGNORECASE)
PARAGRAPH_MARKER = re.compile(r"^\s*§\s*(\d+)\s*\.")
PART_MARKER = re.compile(r"^\s*(\d+)\.\s+")
POINT_MARKER = re.compile(r"^\s*(\d+)\)\s+")
SUBPOINT_MARKER = re.compile(r"^\s*([а-щьюяіїєґ])\)\s+", re.IGNORECASE)
DECIMAL_MARKER = re.compile(r"^\s*(\d+(?:\.\d+){1,})\.\s+")
HEADING_MARKER = re.compile(
    r"^\s*(?:(?P<kind>РОЗДІЛ|ЧАСТИНА)\s+(?P<number>[IVXLC]+|\d+)\b|"
    r"(?P<number_first>\d+(?:\.\d+)*)[.)]?\s+(?P<kind_last>РОЗДІЛ|ЧАСТИНА)\b)",
    re.IGNORECASE,
)
# A contents leader is a long trailing run, or a three-mark run followed by a page
# number; unlike ordinary ``(...)`` title punctuation, the shorter form needs digits.
TOC_LEADER = re.compile(r"(?:[.…]{3,}\s*\d+|[.…]{4,})\s*$")
PAYLOAD_FILES = frozenset({
    "antonenko_style_guide.units.jsonl",
    "antonenko_textbook_representation.units.jsonl",
    "calque_inventory.units.jsonl",
    "lexical_structural_freeze_v1.json",
    "other_normative_style_inventory.units.jsonl",
    "pravopys_2019_complete.units.jsonl",
    "pravopys_2026_complete.units.jsonl",
    "school_textbooks.units.jsonl",
    "ua_gec.units.jsonl",
})
RECEIPT_FILE = "source-universe-freeze-receipt.json"
EXPECTED_OUTPUT_FILES = frozenset({*PAYLOAD_FILES, RECEIPT_FILE})


class FreezeError(ValueError):
    """The submitted input universe cannot be frozen safely."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_merged_main_binding(merged_main_sha: str) -> dict[str, str]:
    """Bind the freezer executable to the exact current origin/main commit."""
    require(GIT_SHA40.fullmatch(merged_main_sha) is not None, "merged-main SHA must be 40 lowercase hex characters")
    try:
        remote_head = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "origin/main"],
            check=False,
            capture_output=True,
        )
        merged_script = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{merged_main_sha}:{FREEZER_SCRIPT_PATH}"],
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise FreezeError(f"unable to verify merged-main binding: {exc}") from exc
    require(remote_head.returncode == 0, "unable to resolve origin/main for freeze binding")
    require(remote_head.stdout.decode("ascii").strip() == merged_main_sha, "freeze SHA is not the current origin/main head")
    require(merged_script.returncode == 0, "freezer implementation is absent from the merged-main SHA")
    current_script = ROOT / FREEZER_SCRIPT_PATH
    require(merged_script.stdout == current_script.read_bytes(), "running freezer bytes differ from merged-main freezer bytes")
    return {
        "implementation_version": FREEZER_IMPLEMENTATION_VERSION,
        "script_path": FREEZER_SCRIPT_PATH,
        "script_sha256": sha256_file(current_script),
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FreezeError(message)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreezeError(f"cannot read JSON input: {path}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def _safe_name(value: str) -> str:
    require(IDENTIFIER.fullmatch(value) is not None, f"unsafe SQLite identifier: {value!r}")
    return f'"{value}"'


def _connect(path: Path) -> sqlite3.Connection:
    require(path.is_file() and path.stat().st_size > 0, f"missing SQLite input: {path}")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _normal(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"bytes_sha256": sha256_bytes(value)}
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Mapping):
        return {str(key): _normal(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normal(item) for item in value]
    return value


def _opaque_id(namespace: str, value: Any) -> str:
    return f"{namespace}.{sha256_bytes(canonical_json(_normal(value)).encode('utf-8'))}"


def _unit_hash(value: Any) -> str:
    return sha256_bytes(canonical_json(_normal(value)).encode("utf-8"))


def _primary_key_locator(identity: Mapping[str, Any]) -> dict[str, Any]:
    """Expose retrievable PK structure without publishing source-bearing values."""
    return {
        "primary_key_fields": sorted(str(key) for key in identity),
        "primary_key_sha256": _unit_hash(identity),
    }


def _expected_families(contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    families = contract.get("mandatory_families")
    require(isinstance(families, list), "coverage contract lacks mandatory families")
    result: dict[str, Mapping[str, Any]] = {}
    for item in families:
        require(isinstance(item, Mapping) and isinstance(item.get("family_id"), str), "invalid family descriptor")
        family_id = str(item["family_id"])
        require(family_id not in result, f"duplicate family descriptor: {family_id}")
        result[family_id] = item
    require(len(result) == 21, "coverage contract must declare exactly 21 mandatory families")
    return result


def _rights(family: Mapping[str, Any]) -> dict[str, Any]:
    rights = family.get("rights")
    require(isinstance(rights, Mapping), f"family lacks rights: {family.get('family_id')}")
    require(rights.get("source_text_committed") is False, "source text may not be committed")
    return {
        "source_text_committed": False,
        "locator_only_allowed": bool(rights.get("locator_only_allowed")),
        "rights_limited_disposition": str(rights.get("rights_limited_disposition", "")),
    }


def _expected_count(family: Mapping[str, Any]) -> int | None:
    value = family.get("input_identity", {}).get("observed_input_total")
    return value if isinstance(value, int) else None


def _database_units(connection: sqlite3.Connection, table: str, family_id: str, family: Mapping[str, Any], input_hash: str) -> Iterable[dict[str, Any]]:
    columns = [row[1] for row in connection.execute(f"PRAGMA table_info({_safe_name(table)})")]
    require(columns, f"missing table for {family_id}: {table}")
    pk_columns = [row[1] for row in connection.execute(f"PRAGMA table_info({_safe_name(table)})") if row[5]]
    select = "*" if pk_columns else "rowid AS __freeze_rowid__, *"
    order = ", ".join(_safe_name(column) for column in pk_columns) if pk_columns else "__freeze_rowid__"
    rows = connection.execute(f"SELECT {select} FROM {_safe_name(table)} ORDER BY {order}")
    for ordinal, row in enumerate(rows, start=1):
        raw = dict(row)
        identity = {key: raw[key] for key in pk_columns} if pk_columns else {"rowid": raw["__freeze_rowid__"]}
        normalized_row = _normal(raw)
        duplicate_basis = {key: value for key, value in normalized_row.items() if key not in {*identity, "__freeze_rowid__"}}
        yield {
            "family_id": family_id,
            "unit_id": _opaque_id(f"unit.{family_id}", {"table": table, "identity": identity}),
            "unit_sha256": _unit_hash(normalized_row),
            "ordinal": ordinal,
            "locator": {"kind": "sqlite_row", "table": table, **_primary_key_locator(identity)},
            "duplicate_group_id": _opaque_id(f"duplicate.{family_id}", duplicate_basis),
            "parse_status": "parsed",
            "rights": _rights(family),
            "provenance": {"input_sha256": input_hash, "unit_grain": family["input_identity"]["unit_grain"]},
        }


def _antonenko_textbook_units(connection: sqlite3.Connection, family: Mapping[str, Any], input_hash: str) -> Iterable[dict[str, Any]]:
    table = "textbooks"
    columns = {row[1] for row in connection.execute(f"PRAGMA table_info({_safe_name(table)})")}
    require({"id", "source_file"} <= columns, "textbooks cannot identify Antonenko representation")
    rows = connection.execute(
        'SELECT * FROM "textbooks" WHERE "source_file" = ? ORDER BY "id"',
        ("antonenko-davydovych-yak-my-hovorymo",),
    )
    for ordinal, row in enumerate(rows, start=1):
        raw = dict(row)
        normalized = _normal(raw)
        identity = {"id": raw["id"]}
        duplicate = {key: value for key, value in normalized.items() if key != "id"}
        yield {
            "family_id": "antonenko_textbook_representation",
            "unit_id": _opaque_id("unit.antonenko_textbook_representation", identity),
            "unit_sha256": _unit_hash(normalized), "ordinal": ordinal,
            "locator": {"kind": "sqlite_row", "table": table, **_primary_key_locator(identity)},
            "duplicate_group_id": _opaque_id("duplicate.antonenko_textbook_representation", duplicate),
            "parse_status": "parsed", "rights": _rights(family),
            "provenance": {"input_sha256": input_hash, "unit_grain": family["input_identity"]["unit_grain"]},
        }


def _load_module(path: Path) -> ModuleType:
    require(path.is_file(), f"missing calque module: {path}")
    spec = importlib.util.spec_from_file_location("phase3_frozen_calque_module", path)
    require(spec is not None and spec.loader is not None, "cannot load calque module")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # Module code is an explicit supplied input.
        raise FreezeError("cannot load calque module") from exc
    return module


def _calque_units(path: Path, family: Mapping[str, Any]) -> list[dict[str, Any]]:
    module = _load_module(path)
    entries: list[tuple[str, str, Any]] = []
    for collection in ("CURATED_CALQUES", "PHRASAL_CALQUES", "SENSE_RESTRICTED_CALQUES"):
        value = getattr(module, collection, None)
        require(isinstance(value, Mapping), f"calque module lacks mapping: {collection}")
        entries.extend((collection, str(key), item) for key, item in value.items())
    entries.sort(key=lambda item: (item[0], item[1]))
    module_hash = sha256_file(path)
    return [{
        "family_id": "calque_inventory",
        "unit_id": _opaque_id("unit.calque_inventory", {"collection": collection, "key": key}),
        "unit_sha256": _unit_hash(value), "ordinal": ordinal,
        "locator": {"kind": "python_mapping_entry", "collection": collection, "entry_id_sha256": _unit_hash(key)},
        "duplicate_group_id": _opaque_id("duplicate.calque_inventory", value), "parse_status": "parsed",
        "rights": _rights(family),
        "provenance": {"input_sha256": module_hash, "unit_grain": family["input_identity"]["unit_grain"]},
    } for ordinal, (collection, key, value) in enumerate(entries, start=1)]


def _r2u_units(path: Path, family: Mapping[str, Any]) -> list[dict[str, Any]]:
    cache = _read_json(path)
    entries = cache.get("entries")
    require(isinstance(entries, list), "R2U cache lacks entries")
    normalized_entries = [_normal(item) for item in entries]
    claimed = cache.get("entries_sha256")
    require(isinstance(claimed, str), "R2U cache lacks entries hash")
    require(_unit_hash(normalized_entries) == claimed, "R2U cache entries hash mismatch")
    input_hash = sha256_file(path)
    units: list[dict[str, Any]] = []
    for ordinal, entry in enumerate(normalized_entries, start=1):
        require(isinstance(entry, Mapping), "invalid R2U cache entry")
        units.append({
            "family_id": "lexical_r2u", "unit_id": _opaque_id("unit.lexical_r2u", entry),
            "unit_sha256": _unit_hash(entry), "ordinal": ordinal,
            "locator": {"kind": "r2u_cache_entry", "entry_sha256": _unit_hash(entry)},
            "duplicate_group_id": _opaque_id("duplicate.lexical_r2u", entry), "parse_status": "parsed",
            "rights": _rights(family),
            "provenance": {"input_sha256": input_hash, "cache_id_sha256": _unit_hash(cache.get("cache_id")), "unit_grain": family["input_identity"]["unit_grain"]},
        })
    return units


def extract_pdf_pages(path: Path, pdftotext: Path) -> list[str]:
    """Return normalized page strings without retaining or publishing them."""
    require(pdftotext.is_file() and os.access(pdftotext, os.X_OK), f"missing pdftotext executable: {pdftotext}")
    result = subprocess.run([str(pdftotext), "-layout", str(path), "-"], check=False, capture_output=True)
    require(result.returncode == 0, f"pdftotext failed for {path.name}")
    text = result.stdout.decode("utf-8", errors="strict")
    pages = [unicodedata.normalize("NFC", page).replace("\r\n", "\n").strip() for page in text.split("\f")]
    if pages and pages[-1] == "":
        pages.pop()  # pdftotext terminates its final logical page with form feed.
    return pages


def _pdf_units(
    path: Path,
    family_id: str,
    family: Mapping[str, Any],
    pdftotext: Path,
    *,
    retrieved_at: str | None = None,
    retrieval_locator: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    input_hash = sha256_file(path)
    expected = EXPECTED_2019_SHA256 if family_id == "pravopys_2019_complete" else EXPECTED_2026_SHA256.lower()
    require(input_hash.lower() == expected.lower(), f"official {family_id} PDF hash mismatch")
    pages = extract_pdf_pages(path, pdftotext)
    require(pages and any(pages), f"official {family_id} PDF has no extractable pages")
    lines = [(page, line_number, line) for page, text in enumerate(pages, start=1) for line_number, line in enumerate(text.splitlines(), start=1)]
    anchors: list[tuple[int, int, int, tuple[str, ...], int]] = []
    structural: list[str] = []
    decimal_stack: list[str] = []
    current_paragraph: str | None = None
    current_part: str | None = None
    current_point: str | None = None
    seen_paragraphs: set[int] = set()
    paragraphs_started = False
    content_end = len(lines)
    for index, (page, line_number, line) in enumerate(lines):
        paragraph_match = PARAGRAPH_MARKER.match(line)
        if paragraph_match and int(paragraph_match.group(1)) in seen_paragraphs:
            if seen_paragraphs == set(range(1, EXPECTED_PARAGRAPH_COUNT + 1)):
                content_end = index
                break  # A trailing contents/index begins after the complete body.
            raise FreezeError(
                f"{family_id} PDF has duplicate paragraph marker {paragraph_match.group(1)}; "
                "possible unfiltered navigation capture"
            )
        if TOC_LEADER.search(line):
            continue  # Contents/index labels are navigation, never source units.
        if match := HEADING_MARKER.match(line):
            heading_kind = str(match.group("kind") or match.group("kind_last")).casefold()
            heading_number = str(match.group("number") or match.group("number_first")).casefold()
            kind = "chapter" if heading_kind == "розділ" else "part_heading"
            token = f"{kind}:{heading_number}"
            structural = [token] if kind == "chapter" else [*structural[:1], token]
            decimal_stack = []
            current_paragraph = current_part = current_point = None
            anchors.append((index, 0, page, tuple(structural), line_number))
        elif (match := DECIMAL_MARKER.match(line)) and paragraphs_started:
            components = match.group(1).split(".")
            decimal_stack = [f"decimal:{'.'.join(components[:depth])}" for depth in range(1, len(components) + 1)]
            current_paragraph = current_part = current_point = None
            anchors.append((index, 1, page, tuple([*structural, *decimal_stack]), line_number))
        elif match := paragraph_match:
            paragraph_number = int(match.group(1))
            if paragraph_number == 1:
                paragraphs_started = True
            if not paragraphs_started:
                continue  # The 2026 contents/index precedes the first paragraph.
            seen_paragraphs.add(paragraph_number)
            current_paragraph = f"paragraph:{paragraph_number}"
            current_part = current_point = None
            anchors.append((index, 2, page, tuple([*structural, *decimal_stack, current_paragraph]), line_number))
        elif current_paragraph is not None and (match := PART_MARKER.match(line)):
            current_part = f"part:{int(match.group(1))}"
            current_point = None
            anchors.append((index, 3, page, tuple([*structural, *decimal_stack, current_paragraph, current_part]), line_number))
        elif current_paragraph is not None and (match := POINT_MARKER.match(line)):
            current_point = f"point:{int(match.group(1))}"
            parent = [*structural, *decimal_stack, current_paragraph, *([current_part] if current_part else [])]
            anchors.append((index, 4, page, tuple([*parent, current_point]), line_number))
        elif current_paragraph is not None and (match := SUBPOINT_MARKER.match(line)):
            parent = [*structural, *decimal_stack, current_paragraph, *([current_part] if current_part else []), *([current_point] if current_point else [])]
            anchors.append((index, 5, page, tuple([*parent, f"subpoint:{match.group(1).casefold()}"]), line_number))
    require(anchors, f"official {family_id} PDF exposes no stable numbered hierarchy")
    unique_anchors: list[tuple[int, int, int, tuple[str, ...], int]] = []
    seen_paths: set[tuple[str, ...]] = set()
    for anchor in anchors:
        if anchor[3] not in seen_paths:
            unique_anchors.append(anchor)
            seen_paths.add(anchor[3])
    anchors = unique_anchors
    # A structural heading can prefix a paragraph path; find the paragraph token instead.
    paragraph_numbers = {
        int(token.split(":", 1)[1]) for _, level, _, path_tokens, _ in anchors if level == 2
        for token in path_tokens if token.startswith("paragraph:")
    }
    require(paragraph_numbers == set(range(1, EXPECTED_PARAGRAPH_COUNT + 1)), f"{family_id} PDF does not represent every required paragraph")
    paths = [anchor[3] for anchor in anchors]
    require(len(paths) == len(set(paths)), f"{family_id} PDF has duplicate structural section paths")
    units: list[dict[str, Any]] = []
    for ordinal, (start, level, page, section_path, line_number) in enumerate(anchors, start=1):
        end = content_end
        for candidate_start, candidate_level, *_ in anchors[ordinal:]:
            if candidate_level <= level:
                end = candidate_start
                break
        text = "\n".join(line for _, _, line in lines[start:end])
        end_page, end_line, _ = lines[end - 1] if end > start else lines[start]
        units.append({
            "family_id": family_id,
            "unit_id": _opaque_id(f"unit.{family_id}", {"edition_sha256": input_hash, "section_path": section_path}),
            "unit_sha256": sha256_bytes(text.encode("utf-8")), "normalized_text_sha256": sha256_bytes(text.encode("utf-8")), "ordinal": ordinal,
            "locator": {"kind": "pdf_numbered_hierarchy", "edition_sha256": input_hash, "page": page, "line": line_number, "end_page": end_page, "end_line": end_line, "section_path": list(section_path)},
            "duplicate_group_id": _opaque_id(f"duplicate.{family_id}", text), "parse_status": "numbered_hierarchy_parsed",
            "rights": _rights(family), "provenance": {"input_sha256": input_hash, "unit_grain": "pdf_numbered_hierarchy"},
        })
    unit_ids = [unit["unit_id"] for unit in units]
    require(len(unit_ids) == len(set(unit_ids)), f"{family_id} PDF has duplicate unit IDs")
    report: dict[str, Any] = {
        "edition_identity": family_id,
        "input_sha256": input_hash,
        "page_count_extracted": len(pages),
        "stable_grain": "pdf_numbered_hierarchy",
        "paragraph_count": len(paragraph_numbers),
        "source_text_committed": False,
        "rights_provenance_classification": RIGHTS_PROVENANCE_CLASSIFICATION,
    }
    if retrieved_at is not None or retrieval_locator is not None:
        require(
            isinstance(retrieved_at, str) and ISO_8601_UTC.fullmatch(retrieved_at) is not None,
            f"{family_id} retrieval time must be canonical UTC ISO-8601",
        )
        require(
            isinstance(retrieval_locator, str) and retrieval_locator.startswith("https://"),
            f"{family_id} retrieval locator must be HTTPS",
        )
        report.update({
            "official_download_locator": (
                PRAVOPYS_2019_OFFICIAL_DOWNLOAD_LOCATOR
                if family_id == "pravopys_2019_complete"
                else PRAVOPYS_2026_OFFICIAL_DOWNLOAD_LOCATOR
            ),
            "retrieval_locator": retrieval_locator,
            "retrieved_at": retrieved_at,
        })
        if family_id == "pravopys_2026_complete":
            report["official_decision_locator"] = PRAVOPYS_2026_DECISION_LOCATOR
    return units, report


def _other_normative_units(connection: sqlite3.Connection, family: Mapping[str, Any], input_hash: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    candidates = [name for name in tables if NORMATIVE_TABLE.search(name) and name != "style_guide"]
    additions: list[dict[str, Any]] = []
    for table in candidates:
        additions.extend(_database_units(connection, table, "other_normative_style_inventory", family, input_hash))
    # The allocated Antonenko table is only zero-additional when every source tag is Antonenko.
    style_columns = {row[1] for row in connection.execute('PRAGMA table_info("style_guide")')}
    if "source" in style_columns:
        foreign_rows = [
            row for row in connection.execute('SELECT * FROM "style_guide" ORDER BY "id"').fetchall()
            if "антоненко" not in str(row["source"] or "").casefold()
        ]
        if foreign_rows:
            additions.extend(_rows_to_units(foreign_rows, "style_guide", "other_normative_style_inventory", family, input_hash))
    textbook_columns = {row[1] for row in connection.execute('PRAGMA table_info("textbooks")')}
    if "source_file" in textbook_columns:
        tagged_rows = [
            row for row in connection.execute('SELECT * FROM "textbooks" ORDER BY "id"').fetchall()
            if str(row["source_file"] or "").casefold() != "antonenko-davydovych-yak-my-hovorymo"
            and NORMATIVE_TABLE.search(str(row["source_file"] or ""))
        ]
        if tagged_rows:
            additions.extend(_rows_to_units(tagged_rows, "textbooks", "other_normative_style_inventory", family, input_hash))
    discovery = {"candidate_tables": candidates, "additional_family_count": len(additions), "zero_additional_family_inventory": not additions}
    return additions, discovery


def _rows_to_units(rows: Iterable[sqlite3.Row], table: str, family_id: str, family: Mapping[str, Any], input_hash: str) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for ordinal, row in enumerate(rows, start=1):
        raw = dict(row)
        identity = {"id": raw["id"]} if "id" in raw else {"ordinal": ordinal}
        normalized = _normal(raw)
        units.append({
            "family_id": family_id, "unit_id": _opaque_id(f"unit.{family_id}", {"table": table, "identity": identity}),
            "unit_sha256": _unit_hash(normalized), "ordinal": ordinal,
            "locator": {"kind": "sqlite_row", "table": table, **_primary_key_locator(identity)},
            "duplicate_group_id": _opaque_id(f"duplicate.{family_id}", {key: value for key, value in normalized.items() if key != "id"}),
            "parse_status": "parsed", "rights": _rights(family),
            "provenance": {"input_sha256": input_hash, "unit_grain": family["input_identity"]["unit_grain"]},
        })
    return units


def _validate_count(family_id: str, family: Mapping[str, Any], count: int) -> None:
    expected = _expected_count(family)
    if expected is not None:
        require(count == expected, f"frozen unit count mismatch for {family_id}: expected {expected}, got {count}")


def _stage(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        return Path(handle.name)


def _stage_ledger(path: Path, units: Iterable[Mapping[str, Any]]) -> tuple[Path, int, str]:
    """Stream one canonical JSONL ledger to a private sibling temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    count = 0
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            for unit in units:
                encoded = (canonical_json(unit) + "\n").encode("utf-8")
                handle.write(encoded)
                digest.update(encoded)
                count += 1
            handle.flush()
            os.fsync(handle.fileno())
        return temporary, count, digest.hexdigest()
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _structural_summary(family_id: str, units: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Stream a complete lexical structural audit without retaining unit rows."""
    rolling = hashlib.sha256()
    count = 0
    parse_counts: dict[str, int] = {}
    provenance: Mapping[str, Any] | None = None
    for unit in units:
        binding = {
            "unit_id": unit["unit_id"], "unit_sha256": unit["unit_sha256"],
            "duplicate_group_id": unit["duplicate_group_id"], "parse_status": unit["parse_status"],
            "provenance": unit["provenance"],
        }
        encoded = canonical_json(binding).encode("utf-8")
        rolling.update(len(encoded).to_bytes(8, "big"))
        rolling.update(encoded)
        status = str(unit["parse_status"])
        parse_counts[status] = parse_counts.get(status, 0) + 1
        current_provenance = unit["provenance"]
        require(isinstance(current_provenance, Mapping), f"lexical unit lacks provenance: {family_id}")
        if provenance is None:
            provenance = current_provenance
        else:
            require(dict(provenance) == dict(current_provenance), f"lexical provenance drift: {family_id}")
        count += 1
    require(provenance is not None, f"lexical family has no units: {family_id}")
    return {
        "family_id": family_id, "unit_count": count, "ordered_rolling_sha256": rolling.hexdigest(),
        "parse_status_counts": dict(sorted(parse_counts.items())),
        "binding_fields": ["unit_id", "unit_sha256", "duplicate_group_id", "parse_status", "provenance"],
        "provenance": dict(provenance),
    }


def freeze(
    *,
    coverage_contract: Path,
    sources_db: Path,
    vesum_db: Path,
    pravopys_2019_pdf: Path,
    pravopys_2026_pdf: Path,
    pravopys_2019_retrieved_at: str,
    pravopys_2019_retrieval_locator: str,
    pravopys_2026_retrieved_at: str,
    pravopys_2026_retrieval_locator: str,
    calque_module: Path,
    r2u_cache: Path,
    output_dir: Path,
    pdftotext: Path,
    merged_main_sha: str,
) -> dict[str, Any]:
    """Validate every family first, then atomically publish text-free ledgers."""
    for path, label in ((coverage_contract, "coverage contract"), (sources_db, "sources database"), (vesum_db, "VESUM database"), (pravopys_2019_pdf, "2019 PDF"), (pravopys_2026_pdf, "2026 PDF"), (calque_module, "calque module"), (r2u_cache, "R2U cache")):
        require(path.is_file(), f"missing {label}: {path}")
    freezer_binding = _verify_merged_main_binding(merged_main_sha)
    if output_dir.exists():
        unexpected = {path.name for path in output_dir.iterdir()} - EXPECTED_OUTPUT_FILES
        require(not unexpected, f"output directory contains stale or unexpected files: {sorted(unexpected)}")
    contract = _read_json(coverage_contract)
    families = _expected_families(contract)
    source_hash, vesum_hash = sha256_file(sources_db), sha256_file(vesum_db)
    source = _connect(sources_db)
    vesum: sqlite3.Connection | None = None
    try:
        vesum = _connect(vesum_db)
        staged: list[tuple[Path, Path]] = []
        receipt_families = []
        lexical_summaries: list[dict[str, Any]] = []

        def stage_family(family_id: str, units: Iterable[Mapping[str, Any]]) -> None:
            lexical = families[family_id].get("coverage_mode") == "lexical_structural_and_used_subset"
            if lexical:
                summary = _structural_summary(family_id, units)
                _validate_count(family_id, families[family_id], int(summary["unit_count"]))
                lexical_summaries.append(summary)
                return
            target = output_dir / f"{family_id}.units.jsonl"
            temporary, count, digest = _stage_ledger(target, units)
            try:
                _validate_count(family_id, families[family_id], count)
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
            staged.append((temporary, target))
            receipt_families.append({"family_id": family_id, "unit_count": count, "ledger_sha256": digest, "ledger_file": target.name})

        for family_id, table in SOURCES_FAMILIES.items():
            require(family_id in families, f"coverage contract missing required family: {family_id}")
            stage_family(family_id, _database_units(source, table, family_id, families[family_id], source_hash))
        stage_family("antonenko_textbook_representation", _antonenko_textbook_units(source, families["antonenko_textbook_representation"], source_hash))
        stage_family("lexical_vesum", _database_units(vesum, "forms", "lexical_vesum", families["lexical_vesum"], vesum_hash))
        stage_family("calque_inventory", _calque_units(calque_module, families["calque_inventory"]))
        stage_family("lexical_r2u", _r2u_units(r2u_cache, families["lexical_r2u"]))
        units2019, pdf2019 = _pdf_units(
            pravopys_2019_pdf, "pravopys_2019_complete", families["pravopys_2019_complete"], pdftotext,
            retrieved_at=pravopys_2019_retrieved_at, retrieval_locator=pravopys_2019_retrieval_locator,
        )
        stage_family("pravopys_2019_complete", units2019)
        units2026, pdf2026 = _pdf_units(
            pravopys_2026_pdf, "pravopys_2026_complete", families["pravopys_2026_complete"], pdftotext,
            retrieved_at=pravopys_2026_retrieved_at, retrieval_locator=pravopys_2026_retrieval_locator,
        )
        stage_family("pravopys_2026_complete", units2026)
        other_units, discovery = _other_normative_units(source, families["other_normative_style_inventory"], source_hash)
        stage_family("other_normative_style_inventory", other_units)
        lexical_artifact = {
            "schema_version": "lexical_structural_freeze_v1", "text_free": True,
            "families": sorted(lexical_summaries, key=lambda item: str(item["family_id"])),
        }
        lexical_target = output_dir / "lexical_structural_freeze_v1.json"
        lexical_content = (canonical_json(lexical_artifact) + "\n").encode("utf-8")
        lexical_digest = sha256_bytes(lexical_content)
        staged.append((_stage(lexical_target, lexical_content), lexical_target))
        for summary in lexical_summaries:
            receipt_families.append({
                "family_id": summary["family_id"], "unit_count": summary["unit_count"],
                "structural_receipt_file": lexical_target.name,
                "structural_receipt_sha256": lexical_digest,
                "structural_universe_sha256": summary["ordered_rolling_sha256"],
            })
        require({item["family_id"] for item in receipt_families} == set(families), "not every mandatory source family was frozen")
        payload_files = sorted(
            (
                {"path": target.name, "sha256": sha256_file(temporary), "byte_count": temporary.stat().st_size}
                for temporary, target in staged
            ),
            key=lambda item: str(item["path"]),
        )
        require({str(item["path"]) for item in payload_files} == PAYLOAD_FILES, "source-freeze payload file set changed")
        receipt = {
            "schema_version": "phase3_source_universe_freeze_v1", "text_free": True,
            "status": "SOURCE_UNIVERSE_FROZEN_NOT_COVERAGE_READY",
            "merged_main_sha": merged_main_sha,
            "freezer": freezer_binding,
            "coverage_contract_sha256": sha256_file(coverage_contract),
            "input_sha256": {"sources_db": source_hash, "vesum_db": vesum_hash, "calque_module": sha256_file(calque_module), "r2u_cache": sha256_file(r2u_cache), "pravopys_2019_pdf": pdf2019["input_sha256"], "pravopys_2026_pdf": pdf2026["input_sha256"]},
            "pdf_editions": {"pravopys_2019_complete": pdf2019, "pravopys_2026_complete": pdf2026},
            "other_normative_style_inventory": discovery, "families": receipt_families,
            "blocking_requirements": [
                "source_unit_dispositions_and_dual_population_audits",
                "textbook_nonhit_audit",
                "pravopys_2019_2026_delta_coverage_and_audit",
                "lexical_used_subset_census",
            ],
            "artifact_manifest": {
                "artifact_count": len(EXPECTED_OUTPUT_FILES),
                "payload_file_count": len(payload_files),
                "payloads": payload_files,
                "payload_manifest_sha256": _unit_hash(payload_files),
                "receipt_file": RECEIPT_FILE,
            },
        }
        receipt_bytes = (canonical_json(receipt) + "\n").encode("utf-8")
        staged.append((_stage(output_dir / RECEIPT_FILE, receipt_bytes), output_dir / RECEIPT_FILE))
        for temporary, target in staged:
            os.replace(temporary, target)
        return receipt
    except Exception:
        for temporary, _ in locals().get("staged", []):
            temporary.unlink(missing_ok=True)
        raise
    finally:
        source.close()
        if vesum is not None:
            vesum.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze all 21 Phase 3 source families without emitting source text.")
    parser.add_argument("--coverage-contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--sources-db", type=Path, required=True)
    parser.add_argument("--vesum-db", type=Path, required=True)
    parser.add_argument("--pravopys-2019-pdf", type=Path, required=True)
    parser.add_argument("--pravopys-2026-pdf", type=Path, required=True)
    parser.add_argument("--pravopys-2019-retrieved-at", required=True)
    parser.add_argument("--pravopys-2019-retrieval-locator", required=True)
    parser.add_argument("--pravopys-2026-retrieved-at", required=True)
    parser.add_argument("--pravopys-2026-retrieval-locator", required=True)
    parser.add_argument("--calque-module", type=Path, required=True)
    parser.add_argument("--r2u-cache", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pdftotext", type=Path, required=True)
    parser.add_argument("--merged-main-sha", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        receipt = freeze(**vars(args))
    except FreezeError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    print(canonical_json({"ok": True, "receipt": "source-universe-freeze-receipt.json", "families": len(receipt["families"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
