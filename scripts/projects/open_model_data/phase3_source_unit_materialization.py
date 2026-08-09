#!/usr/bin/env python3
"""Materialize the frozen nonlexical Phase 3 units into a private JSONL file.

The freeze is the authority for unit membership.  This adapter only recreates
the private source-bearing rows needed by the later heldout steward; it makes
no selection, labeling, or Ukrainian-language decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_source_universe as source
from scripts.projects.open_model_data import verify_phase3_source_universe_freeze as freeze_verifier

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
DEFAULT_SOURCE_UNIVERSE = DATA / "evidence/source_universe_v1"
SCHEMA_PATH = DATA / "contracts/phase3_source_unit_materialization_receipt_v1.schema.json"
PRIVATE_FILENAME = "source_units_v1.jsonl"
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
IMPLEMENTATION_VERSION = "phase3_source_unit_materialization_v1"
FAMILIES = (
    "antonenko_style_guide", "ua_gec", "school_textbooks",
    "antonenko_textbook_representation", "calque_inventory",
    "pravopys_2019_complete", "pravopys_2026_complete",
    "other_normative_style_inventory",
)
FAMILY_TABLES = {
    "antonenko_style_guide": "style_guide",
    "ua_gec": "ua_gec_errors",
    "school_textbooks": "textbooks",
}


class MaterializationError(ValueError):
    """The frozen units cannot be rebuilt at a safe private boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MaterializationError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise MaterializationError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def receipt_body_sha256(receipt: Mapping[str, Any]) -> str:
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    return sha256_bytes((canonical_json(body) + "\n").encode("utf-8"))


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _lstat(path: Path, label: str) -> os.stat_result:
    try:
        result = path.lstat()
    except OSError as exc:
        raise MaterializationError(f"missing {label}: {path}") from exc
    require(not stat.S_ISLNK(result.st_mode), f"symlink is forbidden for {label}")
    return result


def _reject_symlink_components(path: Path, label: str) -> None:
    current = Path(_absolute(path).anchor)
    for component in _absolute(path).parts[1:]:
        current /= component
        if not current.exists() and not current.is_symlink():
            return
        _lstat(current, label)


def _regular_file(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    require(stat.S_ISREG(_lstat(path, label).st_mode), f"{label} must be a regular file")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    _regular_file(path, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MaterializationError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _read_ledger(path: Path, family_id: str) -> list[dict[str, Any]]:
    _regular_file(path, f"frozen {family_id} ledger")
    rows: list[dict[str, Any]] = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            value = json.loads(line)
            require(isinstance(value, dict), f"invalid frozen ledger row: {family_id}:{line_number}")
            rows.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise MaterializationError(f"cannot read frozen {family_id} ledger") from exc
    for ordinal, row in enumerate(rows, start=1):
        require(row.get("family_id") == family_id and row.get("ordinal") == ordinal, f"frozen {family_id} ledger order drift")
    return rows


def _load_freeze(source_universe: Path) -> tuple[dict[str, list[dict[str, Any]]], str]:
    _reject_symlink_components(source_universe, "source universe")
    require(source_universe.is_dir() and not source_universe.is_symlink(), "source universe must be a real directory")
    children = list(source_universe.iterdir())
    for child in children:
        _regular_file(child, "source-universe artifact")
    require({child.name for child in children} == source.EXPECTED_OUTPUT_FILES, "source universe file set drift")
    try:
        freeze_verifier.validate(source_universe, repo_root=ROOT)
    except freeze_verifier.IntegrityError as exc:
        raise MaterializationError("source universe integrity verification failed") from exc
    receipt_path = source_universe / source.RECEIPT_FILE
    receipt = _read_json(receipt_path, "source-universe receipt")
    require(receipt.get("schema_version") == "phase3_source_universe_freeze_v1", "wrong source-universe receipt")
    declared = {item.get("family_id"): item for item in receipt.get("families", []) if isinstance(item, Mapping)}
    require(set(FAMILIES) <= set(declared), "source universe lacks a required nonlexical family")
    ledgers: dict[str, list[dict[str, Any]]] = {}
    for family_id in FAMILIES:
        detail = declared[family_id]
        name = detail.get("ledger_file")
        require(isinstance(name, str) and name == f"{family_id}.units.jsonl", f"wrong frozen ledger name: {family_id}")
        ledger = _read_ledger(source_universe / name, family_id)
        require(detail.get("unit_count") == len(ledger), f"frozen {family_id} count drift")
        require(detail.get("ledger_sha256") == sha256_file(source_universe / name), f"frozen {family_id} ledger hash drift")
        ledgers[family_id] = ledger
    require({family: len(rows) for family, rows in ledgers.items()} == {
        "antonenko_style_guide": 342, "ua_gec": 8937, "school_textbooks": 54979,
        "antonenko_textbook_representation": 169, "calque_inventory": 58,
        "pravopys_2019_complete": 1090, "pravopys_2026_complete": 1466,
        "other_normative_style_inventory": 0,
    }, "frozen nonlexical denominator drift")
    return ledgers, sha256_file(receipt_path)


def _family_descriptor(ledger: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not ledger:
        return {"input_identity": {"unit_grain": "zero_additional_family_inventory"}, "rights": {"source_text_committed": False, "locator_only_allowed": True, "rights_limited_disposition": source.RIGHTS_PROVENANCE_CLASSIFICATION}}
    row = ledger[0]
    return {"input_identity": {"unit_grain": row["provenance"]["unit_grain"]}, "rights": row["rights"]}


def _database_rows(connection: Any, table: str) -> list[dict[str, Any]]:
    columns = [row[1] for row in connection.execute(f"PRAGMA table_info({source._safe_name(table)})")]
    require(columns, f"missing table: {table}")
    pk = [row[1] for row in connection.execute(f"PRAGMA table_info({source._safe_name(table)})") if row[5]]
    select = "*" if pk else "rowid AS __freeze_rowid__, *"
    order = ", ".join(source._safe_name(column) for column in pk) if pk else "__freeze_rowid__"
    return [dict(row) for row in connection.execute(f"SELECT {select} FROM {source._safe_name(table)} ORDER BY {order}")]


def _text_from_row(row: Mapping[str, Any]) -> str:
    for key in ("text", "content", "error", "sentence", "chunk"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    return canonical_json(source._normal(dict(row)))


def _identity(family_id: str, raw: Mapping[str, Any], frozen: Mapping[str, Any]) -> str:
    if family_id == "ua_gec":
        value = raw.get("doc_id")
        require(isinstance(value, str) and value, "UA-GEC row has no doc_id")
        # This intentionally matches heldout.document_identity_for_ua_gec:
        # NFC-normalized raw doc_id, canonical JSON with a newline, then SHA-256.
        return f"doc.ua_gec.{sha256_bytes((canonical_json(source._normal(value)) + chr(10)).encode('utf-8'))}"
    elif family_id == "school_textbooks":
        value = raw.get("source_file")
        require(isinstance(value, str) and value, "school textbook row has no source_file")
    elif family_id == "antonenko_style_guide":
        value = raw.get("source") or raw.get("book") or raw.get("source_file")
        require(isinstance(value, str) and value, "Antonenko style row has no source/book identity")
    elif family_id == "antonenko_textbook_representation":
        value = "antonenko-davydovych-yak-my-hovorymo"
    elif family_id == "calque_inventory":
        locator = frozen["locator"]
        value = locator["collection"]
    elif family_id.startswith("pravopys_"):
        value = family_id
    else:
        raise MaterializationError(f"unsupported identity family: {family_id}")
    namespace = "collection.calque_inventory" if family_id == "calque_inventory" else f"document_or_edition.{family_id}"
    return source._opaque_id(namespace, value)


def _assert_frozen(family_id: str, frozen: Sequence[Mapping[str, Any]], rebuilt: Sequence[Mapping[str, Any]]) -> None:
    require(len(frozen) == len(rebuilt), f"incomplete or extra frozen unit set: {family_id}")
    for ordinal, (expected, actual) in enumerate(zip(frozen, rebuilt, strict=True), start=1):
        require(expected.get("ordinal") == actual.get("ordinal") == ordinal, f"reordered frozen unit set: {family_id}:{ordinal}")
        for key in ("unit_id", "unit_sha256"):
            require(expected.get(key) == actual.get(key), f"frozen {key} mismatch: {family_id}:{ordinal}")
        require(source._unit_hash(expected.get("locator")) == source._unit_hash(actual.get("locator")), f"frozen locator hash mismatch: {family_id}:{ordinal}")


def _rebuild_database(connection: Any, family_id: str, ledger: Sequence[Mapping[str, Any]], source_hash: str) -> list[dict[str, Any]]:
    family = _family_descriptor(ledger)
    if family_id == "antonenko_textbook_representation":
        rebuilt = list(source._antonenko_textbook_units(connection, family, source_hash))
        rows = [row for row in _database_rows(connection, "textbooks") if row.get("source_file") == "antonenko-davydovych-yak-my-hovorymo"]
    else:
        table = FAMILY_TABLES[family_id]
        rebuilt = list(source._database_units(connection, table, family_id, family, source_hash))
        rows = _database_rows(connection, table)
    _assert_frozen(family_id, ledger, rebuilt)
    require(len(rows) == len(rebuilt), f"raw row sequence drift: {family_id}")
    return [_private_row(family_id, frozen, _text_from_row(raw), source._normal(raw), _identity(family_id, raw, frozen)) for frozen, raw in zip(rebuilt, rows, strict=True)]


def _rebuild_calques(path: Path, ledger: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    family = _family_descriptor(ledger)
    rebuilt = source._calque_units(path, family)
    _assert_frozen("calque_inventory", ledger, rebuilt)
    module = source._load_module(path)
    values: list[Any] = []
    for collection in ("CURATED_CALQUES", "PHRASAL_CALQUES", "SENSE_RESTRICTED_CALQUES"):
        mapping = getattr(module, collection)
        values.extend(value for _, value in sorted(mapping.items(), key=lambda item: str(item[0])))
    require(len(values) == len(rebuilt), "calque entry sequence drift")
    return [_private_row("calque_inventory", frozen, canonical_json(source._normal(value)), source._normal(value), _identity("calque_inventory", {}, frozen)) for frozen, value in zip(rebuilt, values, strict=True)]


def _pdf_texts(path: Path, units: Sequence[Mapping[str, Any]], pdftotext: Path) -> list[str]:
    pages = source.extract_pdf_pages(path, pdftotext)
    lines = [(page, line, text) for page, body in enumerate(pages, start=1) for line, text in enumerate(body.splitlines(), start=1)]
    indexes = {(page, line): index for index, (page, line, _) in enumerate(lines)}
    texts: list[str] = []
    for unit in units:
        locator = unit["locator"]
        try:
            start = indexes[(locator["page"], locator["line"])]
            end = indexes[(locator["end_page"], locator["end_line"])]
        except KeyError as exc:
            raise MaterializationError("PDF locator no longer resolves") from exc
        require(start <= end, "PDF locator range is inverted")
        texts.append("\n".join(text for _, _, text in lines[start:end + 1]))
    return texts


def _rebuild_pdf(path: Path, family_id: str, ledger: Sequence[Mapping[str, Any]], pdftotext: Path) -> list[dict[str, Any]]:
    family = _family_descriptor(ledger)
    rebuilt, _ = source._pdf_units(path, family_id, family, pdftotext)
    _assert_frozen(family_id, ledger, rebuilt)
    texts = _pdf_texts(path, rebuilt, pdftotext)
    return [_private_row(family_id, frozen, text, {"text": text}, _identity(family_id, {}, frozen)) for frozen, text in zip(rebuilt, texts, strict=True)]


def _private_row(family_id: str, frozen: Mapping[str, Any], text: str, record: Any, identity: str) -> dict[str, Any]:
    return {
        "family_id": family_id, "unit_id": frozen["unit_id"], "unit_sha256": frozen["unit_sha256"],
        "frozen_locator": source._normal(frozen["locator"]),
        "frozen_locator_sha256": source._unit_hash(frozen["locator"]),
        "document_or_edition_identity": identity, "source_text": text,
        "source_record": record, "source_text_sha256": sha256_bytes(text.encode("utf-8")),
    }


def reconstruct(*, source_universe: Path, sources_db: Path, pravopys_2019_pdf: Path, pravopys_2026_pdf: Path, calque_module: Path, pdftotext: Path) -> tuple[list[dict[str, Any]], str]:
    for path, label in ((sources_db, "sources database"), (pravopys_2019_pdf, "2019 PDF"), (pravopys_2026_pdf, "2026 PDF"), (calque_module, "calque module"), (pdftotext, "pdftotext")):
        _regular_file(path, label)
    ledgers, freeze_receipt_hash = _load_freeze(source_universe)
    source_hash = sha256_file(sources_db)
    connection = source._connect(sources_db)
    try:
        rows: list[dict[str, Any]] = []
        for family_id in ("antonenko_style_guide", "ua_gec", "school_textbooks", "antonenko_textbook_representation"):
            rows.extend(_rebuild_database(connection, family_id, ledgers[family_id], source_hash))
        other, _ = source._other_normative_units(connection, _family_descriptor(ledgers["other_normative_style_inventory"]), source_hash)
        _assert_frozen("other_normative_style_inventory", ledgers["other_normative_style_inventory"], other)
        rows.extend(_rebuild_calques(calque_module, ledgers["calque_inventory"]))
        rows.extend(_rebuild_pdf(pravopys_2019_pdf, "pravopys_2019_complete", ledgers["pravopys_2019_complete"], pdftotext))
        rows.extend(_rebuild_pdf(pravopys_2026_pdf, "pravopys_2026_complete", ledgers["pravopys_2026_complete"], pdftotext))
    finally:
        connection.close()
    require(len(rows) == 67041, "nonlexical materialization denominator drift")
    require(len({row["unit_id"] for row in rows}) == len(rows), "duplicate materialized unit identity")
    return rows, freeze_receipt_hash


def _prepare_private_dir(path: Path) -> Path:
    _reject_symlink_components(path, "private materialization directory")
    if path.exists() or path.is_symlink():
        require(stat.S_ISDIR(_lstat(path, "private materialization directory").st_mode), "private materialization path must be a directory")
        require((path.stat().st_mode & 0o777) == PRIVATE_DIR_MODE, "private materialization directory permissions drift")
    else:
        path.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
        os.chmod(path, PRIVATE_DIR_MODE)
    entries = list(path.iterdir())
    for entry in entries:
        _regular_file(entry, "private materialization entry")
        require(entry.name == PRIVATE_FILENAME, "unexpected stale output file in private materialization directory")
        require((entry.stat().st_mode & 0o777) == PRIVATE_FILE_MODE, "private materialization file permissions drift")
    return path / PRIVATE_FILENAME


def _prepare_public_path(path: Path) -> None:
    _reject_symlink_components(path, "public materialization receipt")
    if path.exists() or path.is_symlink():
        _regular_file(path, "public materialization receipt")
    ancestor = path.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    require(stat.S_ISDIR(_lstat(ancestor, "public materialization receipt parent").st_mode), "public receipt parent must be a directory")


def _atomic_write(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            os.fchmod(handle.fileno(), mode)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            os.replace(temporary, path)
            os.chmod(path, mode)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise


def _validate_public(receipt: Mapping[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH, "materialization receipt schema")
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    require(not errors, f"public receipt schema violation: {errors[0].message if errors else ''}")
    require(receipt_body_sha256(receipt) == receipt.get("receipt_sha256"), "public receipt body hash drift")
    forbidden = ("source_text", "source_record", "unit_id", "locator", "document_or_edition_identity", "identity")
    serialized = canonical_json(receipt)
    require(not any(token in serialized for token in forbidden), "public receipt leaks private source fields")


def materialize(*, source_universe: Path, sources_db: Path, pravopys_2019_pdf: Path, pravopys_2026_pdf: Path, calque_module: Path, pdftotext: Path, private_dir: Path, public_receipt: Path) -> dict[str, Any]:
    private_absolute, public_absolute = _absolute(private_dir), _absolute(public_receipt)
    require(private_absolute not in public_absolute.parents and public_absolute != private_absolute / PRIVATE_FILENAME, "public receipt may not be inside or alias private materialization")
    for input_path in (source_universe, sources_db, pravopys_2019_pdf, pravopys_2026_pdf, calque_module):
        input_absolute = _absolute(input_path)
        require(input_absolute not in private_absolute.parents and input_absolute not in public_absolute.parents, "output may not be inside an input artifact")
    _prepare_public_path(public_receipt)
    private_path = _prepare_private_dir(private_dir)
    rows, freeze_receipt_hash = reconstruct(source_universe=source_universe, sources_db=sources_db, pravopys_2019_pdf=pravopys_2019_pdf, pravopys_2026_pdf=pravopys_2026_pdf, calque_module=calque_module, pdftotext=pdftotext)
    payload = "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")
    _atomic_write(private_path, payload, PRIVATE_FILE_MODE)
    counts = {family_id: sum(row["family_id"] == family_id for row in rows) for family_id in FAMILIES}
    receipt: dict[str, Any] = {
        "schema_version": "phase3_source_unit_materialization_receipt_v1", "text_free": True,
        "implementation_version": IMPLEMENTATION_VERSION, "no_leakage": True,
        "source_universe_receipt_sha256": freeze_receipt_hash, "private_jsonl_sha256": sha256_bytes(payload),
        "private_record_count": len(rows), "family_counts": counts,
    }
    receipt["receipt_sha256"] = receipt_body_sha256(receipt)
    _validate_public(receipt)
    _atomic_write(public_receipt, (canonical_json(receipt) + "\n").encode("utf-8"), PRIVATE_FILE_MODE)
    return receipt


def verify(**kwargs: Any) -> dict[str, Any]:
    private_dir = Path(kwargs["private_dir"])
    public_receipt = Path(kwargs["public_receipt"])
    private_path = _prepare_private_dir(private_dir)
    _prepare_public_path(public_receipt)
    rows, freeze_receipt_hash = reconstruct(**{key: value for key, value in kwargs.items() if key not in {"private_dir", "public_receipt"}})
    expected = "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")
    require(private_path.read_bytes() == expected, "private materialization content drift")
    require((private_path.stat().st_mode & 0o777) == PRIVATE_FILE_MODE, "private materialization file permissions drift")
    receipt = _read_json(public_receipt, "public materialization receipt")
    _validate_public(receipt)
    require(receipt["source_universe_receipt_sha256"] == freeze_receipt_hash, "public receipt source-universe binding drift")
    require(receipt["private_jsonl_sha256"] == sha256_bytes(expected), "public receipt private payload hash drift")
    return {"ok": True, "private_record_count": len(rows), "receipt_sha256": receipt["receipt_sha256"]}


def _arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-universe", type=Path, default=DEFAULT_SOURCE_UNIVERSE)
    parser.add_argument("--sources-db", type=Path, required=True)
    parser.add_argument("--pravopys-2019-pdf", type=Path, required=True)
    parser.add_argument("--pravopys-2026-pdf", type=Path, required=True)
    parser.add_argument("--calque-module", type=Path, required=True)
    parser.add_argument("--pdftotext", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--public-receipt", type=Path, required=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build")
    verify_parser = commands.add_parser("verify")
    _arguments(build_parser)
    _arguments(verify_parser)
    args = parser.parse_args(argv)
    try:
        values = {key: value for key, value in vars(args).items() if key != "command"}
        result = materialize(**values) if args.command == "build" else verify(**values)
    except MaterializationError as exc:
        parser.error(str(exc))
    sys.stdout.write(canonical_json(result) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
