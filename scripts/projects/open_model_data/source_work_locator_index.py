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
    staged = _stage(output, "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8"))
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
