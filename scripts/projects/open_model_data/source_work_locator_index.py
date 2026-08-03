"""Create a deterministic, public-safe, metadata-only source/work locator index."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "data/projects/open_model_data/contracts/source_work_locator_v1.schema.json"
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
COMPACT_SCHEMA_VERSION = "source_work_locator_compact_v1"
COMPACT_OUTPUT_SUFFIX = ".compact.jsonl"
MAX_COMPACT_BYTES = 16 * 1024 * 1024
COMPACT_ROW_FIELDS = (
    "locator_id",
    "family_index",
    "source_id",
    "work_id",
    "source_locator_values",
    "work_locator_values",
    "canonical_url",
    "metadata_values",
    "metadata_publication_values",
    "affected_records",
    "missing_evidence_keys",
)
COMPACT_ORDERING = "source_family,source_id,work_id,source_locator canonical JSON"


class LocatorError(ValueError):
    """The public-safe locator index cannot be built safely."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def opaque_id(prefix: str, value: str) -> str:
    return f"{prefix}.{hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]}"


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocatorError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LocatorError(f"expected JSON object: {path}")
    return value


def _validator(schema: Mapping[str, Any], definition: str | None = None) -> Draft202012Validator:
    target: Mapping[str, Any] = (
        schema if definition is None else {"$ref": f"#/$defs/{definition}", "$defs": schema["$defs"]}
    )
    Draft202012Validator.check_schema(target)
    return Draft202012Validator(target)


def _validate(value: Mapping[str, Any], validator: Draft202012Validator, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        where = ".".join(str(item) for item in error.path) or "<root>"
        raise LocatorError(f"{label} schema failure at {where}: {error.message}")


def _identifier(value: str) -> str:
    if IDENTIFIER_RE.fullmatch(value) is None:
        raise LocatorError(f"unsafe SQLite identifier: {value!r}")
    return f'"{value}"'


def _connect(path: Path) -> sqlite3.Connection:
    if not path.is_file() or path.stat().st_size == 0:
        raise LocatorError(f"missing SQLite input: {path}")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _as_group_value(value: Any) -> str:
    """Match Phase 1's opaque-ID input exactly, including its unknown fallback."""
    return str(value or "unknown")


def _as_public_value(value: Any) -> str | None:
    return None if value is None or str(value).strip() == "" else str(value)


def _normalized_metadata(value: Any) -> str | None:
    public = _as_public_value(value)
    return public.strip() if public is not None else None


def _stage(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _replace(source: Path, target: Path) -> None:
    """Test seam for the sole atomic publication operation."""
    os.replace(source, target)


def _semantic_jsonl(rows: list[Mapping[str, Any]]) -> bytes:
    try:
        content = "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise LocatorError("locator rows cannot be encoded as UTF-8") from exc
    return content


def _family_descriptor(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_family": row["source_family"],
        "inventory_asset_id": row["inventory_asset_id"],
        "source_locator_columns": sorted(row["source_locator"]),
        "work_locator_columns": sorted(row["work_locator"]),
        "metadata_columns": sorted(row["metadata"]),
    }


def compact_jsonl(rows: list[Mapping[str, Any]]) -> bytes:
    """Encode complete semantic rows in the strict compact UTF-8 transport."""
    semantic = _semantic_jsonl(rows)
    descriptors: dict[str, dict[str, Any]] = {}
    for row in rows:
        descriptor = _family_descriptor(row)
        prior = descriptors.setdefault(row["source_family"], descriptor)
        if prior != descriptor:
            raise LocatorError(f"inconsistent compact family descriptor: {row['source_family']}")
    families = [descriptors[name] for name in sorted(descriptors)]
    family_index = {family["source_family"]: index for index, family in enumerate(families)}
    header = {
        "schema_version": COMPACT_SCHEMA_VERSION,
        "semantic_schema_version": "source_work_locator_v1",
        "row_fields": list(COMPACT_ROW_FIELDS),
        "families": families,
        "records": len(rows),
        "ordering": COMPACT_ORDERING,
        "semantic_jsonl_sha256": hashlib.sha256(semantic).hexdigest(),
    }
    compact_rows: list[list[Any]] = []
    for row in rows:
        family = families[family_index[row["source_family"]]]
        compact_rows.append(
            [
                row["locator_id"],
                family_index[row["source_family"]],
                row["source_id"],
                row["work_id"],
                [row["source_locator"][column] for column in family["source_locator_columns"]],
                [row["work_locator"][column] for column in family["work_locator_columns"]],
                row["canonical_url"],
                [row["metadata"][column] for column in family["metadata_columns"]],
                [row["metadata_publication"][column] for column in family["metadata_columns"]],
                row["affected_records"],
                row["missing_evidence_keys"],
            ]
        )
    content = _semantic_jsonl([header, *compact_rows])
    if b"\0" in content:
        raise LocatorError("compact locator rows contain a NUL byte")
    if len(content) >= MAX_COMPACT_BYTES:
        raise LocatorError(f"compact locator output must be smaller than {MAX_COMPACT_BYTES} bytes")
    return content


def _compact_header(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "semantic_schema_version",
        "row_fields",
        "families",
        "records",
        "ordering",
        "semantic_jsonl_sha256",
    }:
        raise LocatorError("invalid compact locator header")
    if value["schema_version"] != COMPACT_SCHEMA_VERSION:
        raise LocatorError("invalid compact locator header schema version")
    if value["semantic_schema_version"] != "source_work_locator_v1":
        raise LocatorError("invalid compact semantic schema version")
    if value["row_fields"] != list(COMPACT_ROW_FIELDS):
        raise LocatorError("invalid compact row field order")
    if value["ordering"] != COMPACT_ORDERING:
        raise LocatorError("invalid compact ordering")
    if not isinstance(value["records"], int) or isinstance(value["records"], bool) or value["records"] < 0:
        raise LocatorError("invalid compact record count")
    if not isinstance(value["semantic_jsonl_sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", value["semantic_jsonl_sha256"]) is None:
        raise LocatorError("invalid compact semantic hash")
    families = value["families"]
    if not isinstance(families, list) or any(not isinstance(family, dict) for family in families):
        raise LocatorError("invalid compact family descriptor")
    if families != sorted(families, key=lambda item: item.get("source_family", "")):
        raise LocatorError("compact families are not sorted")
    seen: set[str] = set()
    for family in families:
        if set(family) != {
            "source_family",
            "inventory_asset_id",
            "source_locator_columns",
            "work_locator_columns",
            "metadata_columns",
        }:
            raise LocatorError("invalid compact family descriptor")
        name = family["source_family"]
        if not isinstance(name, str) or not name or name in seen:
            raise LocatorError("invalid compact family descriptor")
        seen.add(name)
        if not isinstance(family["inventory_asset_id"], str) or not family["inventory_asset_id"]:
            raise LocatorError("invalid compact family inventory asset")
        for key in ("source_locator_columns", "work_locator_columns", "metadata_columns"):
            columns = family[key]
            if not isinstance(columns, list) or columns != sorted(columns) or len(columns) != len(set(columns)):
                raise LocatorError("invalid compact family column order")
            if any(not isinstance(column, str) or not column for column in columns):
                raise LocatorError("invalid compact family column name")
    return families


def compact_rows(path: Path) -> list[dict[str, Any]]:
    """Read, expand, and validate a compact locator as complete semantic rows."""
    try:
        if path.stat().st_size >= MAX_COMPACT_BYTES:
            raise LocatorError(f"compact locator input must be smaller than {MAX_COMPACT_BYTES} bytes")
        if b"\0" in path.read_bytes():
            raise LocatorError("compact locator contains a NUL byte")
        with path.open(encoding="utf-8") as handle:
            first = handle.readline()
            if not first.endswith("\n") or not first.strip():
                raise LocatorError("compact locator has a missing or unterminated header")
            try:
                header = json.loads(first)
            except json.JSONDecodeError as exc:
                raise LocatorError("compact locator has invalid JSON header") from exc
            families = _compact_header(header)
            rows: list[dict[str, Any]] = []
            row_validator = _validator(_read(CONTRACT))
            for line_number, line in enumerate(handle, start=2):
                if not line.endswith("\n") or not line.strip():
                    raise LocatorError(f"compact locator has a blank or unterminated row at {line_number}")
                try:
                    encoded = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise LocatorError(f"compact locator has invalid JSON at {line_number}") from exc
                if not isinstance(encoded, list) or len(encoded) != len(COMPACT_ROW_FIELDS):
                    raise LocatorError(f"compact locator has invalid row length at {line_number}")
                family_number = encoded[1]
                if not isinstance(family_number, int) or isinstance(family_number, bool) or not 0 <= family_number < len(families):
                    raise LocatorError(f"compact locator has invalid family index at {line_number}")
                family = families[family_number]
                source_values, work_values, metadata_values, publication_values = encoded[4], encoded[5], encoded[7], encoded[8]
                expected_lengths = (
                    (source_values, family["source_locator_columns"]),
                    (work_values, family["work_locator_columns"]),
                    (metadata_values, family["metadata_columns"]),
                    (publication_values, family["metadata_columns"]),
                )
                if any(not isinstance(values, list) or len(values) != len(columns) for values, columns in expected_lengths):
                    raise LocatorError(f"compact locator has invalid value-array length at {line_number}")
                row = {
                    "schema_version": "source_work_locator_v1",
                    "locator_id": encoded[0],
                    "source_family": family["source_family"],
                    "inventory_asset_id": family["inventory_asset_id"],
                    "source_id": encoded[2],
                    "work_id": encoded[3],
                    "source_locator": dict(zip(family["source_locator_columns"], source_values, strict=True)),
                    "work_locator": dict(zip(family["work_locator_columns"], work_values, strict=True)),
                    "canonical_url": encoded[6],
                    "metadata": dict(zip(family["metadata_columns"], metadata_values, strict=True)),
                    "metadata_publication": dict(zip(family["metadata_columns"], publication_values, strict=True)),
                    "affected_records": encoded[9],
                    "missing_evidence_keys": encoded[10],
                }
                _validate(row, row_validator, f"compact locator row {line_number}")
                rows.append(row)
    except (OSError, UnicodeDecodeError) as exc:
        raise LocatorError(f"cannot read compact locator {path}: {exc}") from exc
    if len(rows) != header["records"]:
        raise LocatorError("compact locator record count disagrees with header")
    ordered = sorted(rows, key=lambda row: (row["source_family"], row["source_id"], row["work_id"], canonical_json(row["source_locator"])))
    if rows != ordered:
        raise LocatorError("compact locator rows are reordered")
    semantic = _semantic_jsonl(rows)
    if hashlib.sha256(semantic).hexdigest() != header["semantic_jsonl_sha256"]:
        raise LocatorError("compact locator semantic hash disagrees with header")
    return rows


def expanded_compact_jsonl(path: Path) -> bytes:
    """Return canonical full-object JSONL after strict compact validation."""
    return _semantic_jsonl(compact_rows(path))


def _canonical_url(family: Mapping[str, Any], raw: sqlite3.Row) -> str | None:
    column = family.get("canonical_url_column")
    value = _as_public_value(raw[column]) if column else None
    if value is None:
        return None
    # Literary rows carry PDF-page fragments per chunk; the underlying source
    # locator is the fragment-free source_url, never a page-level text locator.
    if family["source_family"] == "literary":
        parts = urlsplit(value)
        value = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise LocatorError(f"invalid canonical URL for {family['source_family']}")
    return value


def _row(
    family: Mapping[str, Any], raw: sqlite3.Row, affected_records: int, canonical_url: str | None
) -> dict[str, Any]:
    source_value = _as_group_value(raw[family["source_column"]])
    work_value = _as_group_value(raw[family["work_column"]])
    metadata = {column: _as_public_value(raw[column]) for column in family["metadata_columns"]}
    source_locator = {column: _as_public_value(raw[column]) for column in family["source_locator_columns"]}
    work_locator = {column: _as_public_value(raw[column]) for column in family["work_locator_columns"]}
    source_id = opaque_id(f"source.{family['source_family']}", source_value)
    work_id = opaque_id(f"work.{family['source_family']}", work_value)
    return {
        "schema_version": "source_work_locator_v1",
        "locator_id": opaque_id(
            "locator", canonical_json([family["source_family"], source_id, work_id, source_locator, work_locator])
        ),
        "source_family": family["source_family"],
        "inventory_asset_id": family["inventory_asset_id"],
        "source_id": source_id,
        "work_id": work_id,
        "source_locator": source_locator,
        "work_locator": work_locator,
        "canonical_url": canonical_url,
        "metadata": metadata,
        "metadata_publication": {
            key: "public_metadata" if value is not None else "missing" for key, value in metadata.items()
        },
        "affected_records": affected_records,
        "missing_evidence_keys": [] if canonical_url is not None else ["canonical_source_url"],
    }


def _family_rows(
    connection: sqlite3.Connection, family: Mapping[str, Any], validator: Draft202012Validator
) -> list[dict[str, Any]]:
    fields = list(
        dict.fromkeys(
            [
                family["source_column"],
                family["work_column"],
                *family["source_locator_columns"],
                *family["work_locator_columns"],
                *family["metadata_columns"],
                *([family["canonical_url_column"]] if family.get("canonical_url_column") else []),
            ]
        )
    )
    table = _identifier(family["table"])
    actual = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}
    missing = sorted(set(fields) - actual)
    if missing:
        raise LocatorError(f"missing allowlisted metadata columns for {family['source_family']}: {', '.join(missing)}")
    select = ", ".join(_identifier(column) for column in fields)
    query = f"SELECT {select} FROM {table}"
    parameters: tuple[str, ...] = ()
    excluded = tuple(family["exclude"])
    if excluded:
        query += f" WHERE {_identifier(family['source_column'])} NOT IN ({','.join('?' for _ in excluded)})"
        parameters = excluded
    groups: dict[tuple[str, str, str], tuple[int, sqlite3.Row, set[str | None]]] = {}
    source_work_locators: dict[tuple[str, str], str] = {}
    source_work_metadata: dict[tuple[str, str], str] = {}
    for raw in connection.execute(query, parameters):
        source_value, work_value = (
            _as_group_value(raw[family["source_column"]]),
            _as_group_value(raw[family["work_column"]]),
        )
        locator_shape = canonical_json(
            {
                "source": {column: _as_public_value(raw[column]) for column in family["source_locator_columns"]},
                "work": {column: _as_public_value(raw[column]) for column in family["work_locator_columns"]},
            }
        )
        pair = (source_value, work_value)
        previous_shape = source_work_locators.setdefault(pair, locator_shape)
        if previous_shape != locator_shape:
            raise LocatorError(f"ambiguous locator mapping for {family['source_family']} source/work pair")
        metadata_shape = canonical_json(
            {column: _normalized_metadata(raw[column]) for column in family["metadata_columns"]}
        )
        previous_metadata = source_work_metadata.setdefault(pair, metadata_shape)
        if previous_metadata != metadata_shape:
            raise LocatorError(f"ambiguous metadata mapping for {family['source_family']} source/work pair")
        key = (source_value, work_value, locator_shape)
        prior = groups.get(key)
        urls = set(prior[2]) if prior else set()
        urls.add(_canonical_url(family, raw))
        groups[key] = ((prior[0] if prior else 0) + 1, prior[1] if prior else raw, urls)
    rows = []
    for count, raw, urls in groups.values():
        known_urls = {value for value in urls if value is not None}
        if len(known_urls) > 1:
            raise LocatorError(f"ambiguous canonical URL for {family['source_family']} source/work pair")
        rows.append(_row(family, raw, count, next(iter(known_urls), None)))
    for row in rows:
        _validate(row, validator, f"locator row {row['locator_id']}")
    return rows


def build(*, config_path: Path, input_root: Path, output: Path) -> dict[str, Any]:
    schema = _read(CONTRACT)
    config = _read(config_path)
    _validate(config, _validator(schema, "config"), "locator config")
    row_validator = _validator(schema)
    database = input_root / config["database"]
    with _connect(database) as connection:
        rows = [row for family in config["families"] for row in _family_rows(connection, family, row_validator)]
    rows.sort(
        key=lambda row: (row["source_family"], row["source_id"], row["work_id"], canonical_json(row["source_locator"]))
    )
    identities = {(row["source_id"], row["work_id"]) for row in rows}
    if len(identities) != len(rows):
        raise LocatorError("duplicate source/work mapping after locator construction")
    content = compact_jsonl(rows) if output.name.endswith(COMPACT_OUTPUT_SUFFIX) else _semantic_jsonl(rows)
    staged = _stage(output, content)
    try:
        _replace(staged, output)
    finally:
        staged.unlink(missing_ok=True)
    return {
        "records": len(rows),
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        "by_family": {
            family: sum(row["source_family"] == family for row in rows)
            for family in sorted({row["source_family"] for row in rows})
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = build(config_path=args.config, input_root=args.input_root, output=args.output)
    except (LocatorError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
