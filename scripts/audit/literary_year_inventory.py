#!/usr/bin/env python3
"""Read-only inventory of literary_fts label tokens against scraper life-year starts.

The walk matches the retained f5 year probe: dictionary insertion order, list
order, and a parent object's own literary_attestation before its children.
Author dicts are taken from the scraper with ast.literal_eval in ast.walk
order; the last duplicate name wins. Nothing in the scraper is imported or
executed, and the command writes only stdout.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

MIDDLE_DOT = "\u00b7"
NON_CLAIM = "Literal token equality does not establish source provenance, a birth date, or a publication date."
LIMITATION = (
    "Probe-compatible counts follow the retained f5 year probe. "
    "Each literary_fts dictionary attestation is one label. "
    'The probe-compatible label is str(value or "") for that field, including missing and false values. '
    "The string is split on U+00B7 MIDDLE DOT, each part is stripped, the first part is the author token, "
    "and the final part is the year token only when there are at least three parts and str.isdigit is true. "
    "Unicode digits satisfy str.isdigit. "
    "The scraper years start is the substring before the first ASCII hyphen-minus (U+002D); an en dash is not "
    "that hyphen. Author lookup uses ast.walk order and the last duplicate name wins. "
    "Duplicate JSON object keys are refused so the walk is unambiguous; the retained probe instead kept the "
    "last duplicate key. "
    "Row classes do not coerce non-string labels: missing and non-string values are unknown, and a year token "
    "on an unmatched author is not certified. A non-string scraper years value is refused before any inventory "
    "is written. List-valued literary_attestation values and dictionary attestations whose source is not the "
    "exact string literary_fts are outside the denominator and are counted separately. literary_texts rows are "
    "not walked. Coincident dates and non-ukrlib sources remain possible."
)
CLASS_NAMES = (
    "author_display_name_equals_scraper_name",
    "author_display_name_unmatched",
    "label_missing",
    "label_non_string",
    "label_unknown",
    "label_year_token_absent",
    "label_year_token_differs_from_scraper_years_start",
    "label_year_token_equals_scraper_years_start",
    "label_year_token_present_unmatched_author_not_certified",
)
_SHA256_HEX = frozenset("0123456789abcdefABCDEF")
_WITNESS_KEYS = ("chunk_id", "source", "source_url")


class InventoryError(Exception):
    """A pin or parse failure. The message is a fixed error code, never file content."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class _DuplicateJsonKey(Exception):
    """Internal signal for a repeated key. The key and value are not stored."""


class _NonstandardJsonConstant(Exception):
    """Internal signal for NaN/Infinity/-Infinity. The token is not stored."""


def canonical_json(value: object) -> str:
    """Return compact strict JSON with sorted object keys."""
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except ValueError as exc:
        if "Out of range float" not in str(exc):
            raise
        raise InventoryError("witness_nonfinite_number") from None
    except RecursionError:
        raise InventoryError("json_nesting_limit") from None


def _utf8_bytes(payload: str) -> bytes:
    try:
        return payload.encode("utf-8")
    except UnicodeEncodeError:
        raise InventoryError("json_string_not_utf8") from None


def _write_bytes(stream: Any, payload: bytes) -> None:
    stream.buffer.write(payload)
    stream.buffer.flush()


def _reject_json_constant(_token: str) -> None:
    raise _NonstandardJsonConstant


def _normalize_sha256(value: str, role: str) -> str:
    if len(value) != 64 or any(character not in _SHA256_HEX for character in value):
        raise InventoryError(f"{role}_sha256_invalid")
    return value.lower()


def _read_pinned(path: Path, expected: str, role: str) -> bytes:
    try:
        raw = path.read_bytes()
    except OSError:
        raise InventoryError(f"{role}_unreadable") from None
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise InventoryError(f"{role}_sha256_mismatch")
    return raw


def _decode_utf8(raw: bytes, role: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InventoryError(f"{role}_utf8_decode_failed") from None


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise _DuplicateJsonKey
        obj[key] = value
    return obj


def _parse_manifest(raw: bytes) -> Any:
    text = _decode_utf8(raw, "manifest")
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except _DuplicateJsonKey:
        raise InventoryError("duplicate_json_key") from None
    except _NonstandardJsonConstant:
        raise InventoryError("json_nonstandard_constant") from None
    except json.JSONDecodeError:
        raise InventoryError("json_parse_failed") from None
    except ValueError as exc:
        if "integer string conversion" not in str(exc):
            raise
        raise InventoryError("json_integer_limit") from None
    except RecursionError:
        raise InventoryError("json_nesting_limit") from None


def _split_label(label: str) -> tuple[str, str | None]:
    """Probe-compatible author and year tokens. Year is absent unless the rule matches."""
    parts = [part.strip() for part in label.split(MIDDLE_DOT)]
    author = parts[0] if parts else ""
    year = parts[-1] if len(parts) >= 3 and parts[-1].isdigit() else None
    return author, year


def _years_start(years: str) -> str:
    return years.split("-")[0]


def _parse_scraper_authors(raw: bytes) -> tuple[dict[str, str], int, int]:
    """Return last-wins name map, record count, and collision count.

    Collisions are extra records whose name was already seen. The distinct-name
    count is the length of the returned map (the retained probe's author total).
    """
    text = _decode_utf8(raw, "scraper")
    try:
        tree = ast.parse(text)
    except (SyntaxError, MemoryError, RecursionError):
        raise InventoryError("scraper_parse_failed") from None
    years_by_name: dict[str, str] = {}
    record_count = 0
    collision_count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for value in node.values:
            if not isinstance(value, ast.Dict):
                continue
            try:
                evaluated = ast.literal_eval(value)
            except (MemoryError, RecursionError):
                raise InventoryError("scraper_parse_failed") from None
            except (ValueError, SyntaxError, TypeError):
                # The retained probe skips any dict that is not a pure literal.
                # TypeError is an unhashable literal key, which is not a parser limit.
                continue
            if not isinstance(evaluated, dict) or "years" not in evaluated or "name" not in evaluated:
                continue
            years = evaluated["years"]
            if not isinstance(years, str):
                raise InventoryError("scraper_years_non_string")
            name = evaluated["name"]
            try:
                already_present = name in years_by_name
            except TypeError:
                raise InventoryError("scraper_author_name_unhashable") from None
            record_count += 1
            if already_present:
                collision_count += 1
            years_by_name[name] = years
    return years_by_name, record_count, collision_count


def _label_value_type(attestation: Mapping[str, Any]) -> str:
    if "source_label" not in attestation:
        return "missing"
    value = attestation["source_label"]
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, str):
        return "str"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return "other"


def _witness_refusal(key: str, value: Any) -> str | None:
    """Return a fixed error code when a present witness cannot be emitted unchanged."""
    if key not in ("chunk_id", "source_url"):
        return None
    if value is None or isinstance(value, (str, bool, int)):
        return None
    if isinstance(value, float):
        if math.isfinite(value):
            return None
        return "witness_nonfinite_number"
    return "witness_value_unsupported"


def _witnesses(attestation: Mapping[str, Any]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for key in _WITNESS_KEYS:
        if key not in attestation:
            continue
        value = attestation[key]
        refusal = _witness_refusal(key, value)
        if refusal is not None:
            raise InventoryError(refusal)
        if value is None or isinstance(value, (str, int, float, bool)):
            found[key] = value
    return found


def _classify_string(label: str, years_by_name: Mapping[str, str]) -> tuple[str, str | None, list[str]]:
    author, year = _split_label(label)
    classes: list[str] = []
    matched = author in years_by_name
    if matched:
        classes.append("author_display_name_equals_scraper_name")
    else:
        classes.append("author_display_name_unmatched")
    if year is None:
        classes.append("label_year_token_absent")
    elif matched and _years_start(years_by_name[author]) == year:
        classes.append("label_year_token_equals_scraper_years_start")
    elif matched:
        classes.append("label_year_token_differs_from_scraper_years_start")
    else:
        classes.append("label_year_token_present_unmatched_author_not_certified")
    return author, year, sorted(classes)


def _build_row(
    attestation: Mapping[str, Any],
    coordinate: list[str | int],
    ordinal: int,
    years_by_name: Mapping[str, str],
    probe: dict[str, int],
) -> dict[str, Any]:
    probe_author, probe_year = _split_label(str(attestation.get("source_label") or ""))
    probe["labels"] += 1
    if probe_year:
        probe["labels_with_year"] += 1
    if probe_author in years_by_name:
        probe["labels_ukrlib_author"] += 1
        if probe_year and _years_start(years_by_name[probe_author]) == probe_year:
            probe["labels_ukrlib_year_eq_author_years_start"] += 1

    value_type = _label_value_type(attestation)
    if value_type == "str":
        label = attestation["source_label"]
        parsed_author, parsed_year, classes = _classify_string(label, years_by_name)
        label_sha256: str | None = hashlib.sha256(_utf8_bytes(label)).hexdigest()
    elif value_type == "missing":
        parsed_author = None
        parsed_year = None
        classes = ["label_missing", "label_unknown"]
        label_sha256 = None
    else:
        parsed_author = None
        parsed_year = None
        classes = ["label_non_string", "label_unknown"]
        label_sha256 = None

    row: dict[str, Any] = {
        "classes": classes,
        "coordinate": list(coordinate),
        "label_sha256": label_sha256,
        "label_value_type": value_type,
        "ordinal": ordinal,
        "parsed_author": parsed_author,
        "parsed_year": parsed_year,
    }
    row.update(_witnesses(attestation))
    return row


def _consider_attestation(
    value: Any,
    coordinate: list[str | int],
    years_by_name: Mapping[str, str],
    rows: list[dict[str, Any]],
    probe: dict[str, int],
    excluded: dict[str, int],
) -> None:
    if isinstance(value, dict):
        if value.get("source") == "literary_fts":
            rows.append(_build_row(value, coordinate, len(rows), years_by_name, probe))
        else:
            excluded["other_source"] += 1
        return
    if isinstance(value, list):
        excluded["list_valued"] += 1
        return
    excluded["other_non_dict"] += 1


def _walk(
    node: Any,
    coordinate: list[str | int],
    years_by_name: Mapping[str, str],
    rows: list[dict[str, Any]],
    probe: dict[str, int],
    excluded: dict[str, int],
) -> None:
    # Emit this object's literary_attestation before descending, matching the probe.
    if isinstance(node, dict):
        if "literary_attestation" in node:
            _consider_attestation(
                node["literary_attestation"],
                [*coordinate, "literary_attestation"],
                years_by_name,
                rows,
                probe,
                excluded,
            )
        for key, value in node.items():
            _walk(value, [*coordinate, key], years_by_name, rows, probe, excluded)
        return
    if isinstance(node, list):
        for index, value in enumerate(node):
            _walk(value, [*coordinate, index], years_by_name, rows, probe, excluded)


def _class_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {name: 0 for name in CLASS_NAMES}
    for row in rows:
        for name in row["classes"]:
            counts[name] += 1
    return counts


def build_inventory(manifest_raw: bytes, scraper_raw: bytes) -> dict[str, Any]:
    """Build the diagnostic document from bytes that have already been pinned."""
    manifest = _parse_manifest(manifest_raw)
    years_by_name, record_count, collision_count = _parse_scraper_authors(scraper_raw)
    rows: list[dict[str, Any]] = []
    probe = {
        "labels": 0,
        "labels_ukrlib_author": 0,
        "labels_ukrlib_year_eq_author_years_start": 0,
        "labels_with_year": 0,
    }
    excluded = {"list_valued": 0, "other_non_dict": 0, "other_source": 0}
    try:
        _walk(manifest, [], years_by_name, rows, probe, excluded)
    except RecursionError:
        raise InventoryError("json_nesting_limit") from None
    probe["ukrlib_authors_parsed"] = len(years_by_name)
    membership = hashlib.sha256(_utf8_bytes(canonical_json(rows))).hexdigest()
    return {
        "class_counts": _class_counts(rows),
        "denominator": {"literary_fts_dictionary_attestations": len(rows)},
        "excluded_literary_attestation_counts": excluded,
        "inputs": {
            "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "scraper_sha256": hashlib.sha256(scraper_raw).hexdigest(),
        },
        "kind": "literary_year_inventory",
        "limitation": LIMITATION,
        "non_claim": NON_CLAIM,
        "probe_compatible_counts": probe,
        "rows": rows,
        "rows_membership_sha256": membership,
        "scraper_author_records": {
            "collision_count": collision_count,
            "distinct_name_count": len(years_by_name),
            "record_count": record_count,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="scripts/audit/literary_year_inventory.py",
        description=(
            "Enumerate literary_fts label tokens and compare them to scraper life-year starts.\n"
            "Use this read-only diagnostic to list every qualifying attestation with coordinates "
            "before any later migration; do not use it to certify publication dates, birth dates, "
            "or source provenance."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/audit/literary_year_inventory.py \\\n"
            "    --manifest site/src/data/lexicon-manifest.json \\\n"
            "    --manifest-sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \\\n"
            "    --scraper scripts/rag/scrape_ukrlib.py \\\n"
            "    --scraper-sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef\n"
            "\n"
            "Outputs:\n"
            "  stdout only, and only after both SHA-256 pins match and parsing succeeds: one\n"
            "  canonical JSON document (UTF-8, sorted object keys, compact separators). It binds\n"
            "  both input hashes, the literary_fts dictionary denominator, probe-compatible counts,\n"
            "  per-class counts, scraper record, distinct-name and collision counts, and\n"
            "  rows_membership_sha256 (SHA-256 of the canonical JSON of the ordered rows array).\n"
            "  Row fields are only ordinal, coordinate (string keys and integer indexes), source,\n"
            "  chunk_id and source_url when those present values are JSON null, booleans, strings\n"
            "  or finite numbers, label_sha256 (null when the label is not a string),\n"
            "  label_value_type, parsed_author, parsed_year and classes. Objects, arrays and\n"
            "  non-finite numbers in chunk_id or source_url are refused before any inventory is\n"
            "  written. Raw labels, text and body are not emitted. This command does not write\n"
            "  files, modify either input, import or execute the scraper, or contact a network,\n"
            "  database or other service.\n"
            "\n"
            "Parsing:\n"
            "  A qualifying row is one dictionary under a literary_attestation key whose source is\n"
            "  the exact string literary_fts. The parent object is recorded before its children.\n"
            "  Labels are split on U+00B7 MIDDLE DOT. The year token is the final part only when\n"
            "  there are at least three parts and str.isdigit is true, so Unicode digits count.\n"
            "  The scraper years start is the text before the first ASCII hyphen-minus. Author\n"
            "  names follow ast.walk order and the last duplicate name wins. Duplicate JSON keys\n"
            "  are refused. The retained probe kept the last duplicate key instead. NaN, Infinity\n"
            "  and -Infinity tokens are refused. A finite JSON number that overflows the\n"
            "  interpreter float range is refused when it is a chunk_id or source_url value.\n"
            "  Unpaired UTF-16 surrogates are refused when a label, emitted witness or coordinate\n"
            "  key must be encoded as UTF-8. Inputs that exceed the interpreter integer-digit or\n"
            "  nesting limits are refused; those limits are left unchanged.\n"
            "\n"
            "Exit codes:\n"
            "  0  inventory JSON on stdout\n"
            "  1  pin, UTF-8, JSON, duplicate-key, unsupported witness, non-finite number,\n"
            "     surrogate, nesting-limit, integer-limit or scraper-parse failure; stdout empty;\n"
            '     stderr is one JSON object {"error":"<code>"} and does not echo label, witness\n'
            "     or body values\n"
            "  2  usage error (missing or unrecognized arguments)\n"
            "\n"
            "Related:\n"
            "  Issue #10853, supporting #8579 R-F5. Diagnostic only: not a migration, not source\n"
            "  provenance, and not an acceptance authority.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def _add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manifest",
        required=True,
        metavar="PATH",
        help=(
            "UTF-8 JSON file to walk (example: site/src/data/lexicon-manifest.json). "
            "The file is read once and never written."
        ),
    )
    parser.add_argument(
        "--manifest-sha256",
        required=True,
        metavar="HEX64",
        help=(
            "Required SHA-256 of the manifest bytes, exactly 64 hexadecimal characters, with no "
            "default. Any other shape or a byte mismatch exits 1 and writes no inventory "
            "(example: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef)."
        ),
    )
    parser.add_argument(
        "--scraper",
        required=True,
        metavar="PATH",
        help=(
            "Python file whose nested author dicts are read with ast.literal_eval "
            "(example: scripts/rag/scrape_ukrlib.py). The file is not imported or executed."
        ),
    )
    parser.add_argument(
        "--scraper-sha256",
        required=True,
        metavar="HEX64",
        help=(
            "Required SHA-256 of the scraper bytes, exactly 64 hexadecimal characters, with no "
            "default. Any other shape or a byte mismatch exits 1 and writes no inventory "
            "(example: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef)."
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the inventory. Returns a process status; stdout receives JSON only on success."""
    parser = build_parser()
    _add_arguments(parser)
    try:
        args = parser.parse_args(None if argv is None else list(argv))
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return int(code)
    try:
        manifest_sha = _normalize_sha256(args.manifest_sha256, "manifest")
        scraper_sha = _normalize_sha256(args.scraper_sha256, "scraper")
        manifest_raw = _read_pinned(Path(args.manifest), manifest_sha, "manifest")
        scraper_raw = _read_pinned(Path(args.scraper), scraper_sha, "scraper")
        document = build_inventory(manifest_raw, scraper_raw)
        payload = _utf8_bytes(canonical_json(document) + "\n")
    except InventoryError as exc:
        _write_bytes(sys.stderr, _utf8_bytes(canonical_json({"error": exc.code}) + "\n"))
        return 1
    _write_bytes(sys.stdout, payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
