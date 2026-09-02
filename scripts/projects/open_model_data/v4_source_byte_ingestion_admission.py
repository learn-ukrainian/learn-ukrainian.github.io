#!/usr/bin/env python3
"""V4 source byte ingestion admission: the missing rights-bound admission
that a given *already-retained, already-rights-cleared* local byte store may
be opened and hashed for V4 A4 deterministic extraction.

A2's own public ``source_operation_ledger`` already establishes, per real
``source_unit_id``, whether a unit carries real byte content
(``metadata_only: false``) and whether ``deterministic_local_analysis`` is
``allowed``/``scope_bound``. What A2 never did -- and what
``v4_a4_deterministic_extraction.py``'s own docstring calls out as the
missing piece keeping ``extraction_ledger`` empty -- is bind *which local
store* backs each such unit and admit the one operation (hashing, never
transmission/training/publication/redistribution) A4's byte provider may
perform against it. This module is that admission, and its own byte
provider (``provide_bytes_for_admitted_unit``) is the only code in this
project allowed to open ``data/sources.db`` for V4 A4 purposes.

Scope is deliberately narrow and self-verifying:

- **Which units.** ``ADMITTED_SOURCE_UNIT_IDS`` covers only the four real
  ``db.*`` units A2 already marked non-``metadata_only`` with an
  allowed/scope_bound ``deterministic_local_analysis`` right --
  ``db.external_articles``, ``db.literary_texts``, ``db.textbooks.public``,
  ``db.wikipedia``. ``admitted_source_unit_ids_from_a2`` independently
  re-derives this exact set from A2's own public ledger so the hardcoded
  ``LOCAL_STORE_BINDINGS`` keys can never silently drift from what A2
  actually admits -- ``validate_receipt_independently`` refuses on any
  mismatch. The five ``historical.*`` units stay untouched: this module
  never opens a store for them (all are ``metadata_only`` in A2's ledger --
  no real byte content was ever admitted for them in the first place).
- **Which operation.** ``ADMITTED_OPERATION`` is the single string
  ``"deterministic_local_analysis"`` -- pinned as a schema ``const`` on the
  receipt so this admission can never silently widen into a claim about
  transmission, training, publication, or redistribution (all separately
  ``unknown``/``denied`` for these units in A2's own ledger).
- **Which bytes.** ``LOCAL_STORE_BINDINGS`` is a frozen, hashed descriptor of
  exactly which SQLite table/column/row-filter/ordering each admitted unit
  maps to (``LOCAL_STORE_BINDING_DESCRIPTOR_SHA256``). The one non-trivial
  filter -- excluding the eight private ULP/Ohoiko textbook references from
  ``db.textbooks.public`` -- names only already-public
  ``source_file`` values (see ``docs/corpus-inventory.md`` and
  ``inventory_existing_assets.PRIVATE_TEXTBOOK_SOURCES``, which this module
  imports rather than re-declaring, so the two lists can never drift).

``data/sources.db`` (~1.9 GiB, gitignored, SQLite) is never carried by any
dispatch worktree -- only the one shared **primary** checkout has it, the
same "primary, not ``__file__``" resolution
``v4_a3_heldout_family_assignment.PRIMARY_ROOT`` already uses for
``batch_state/``. ``local_sources_db_path`` reuses that exact discovery.
Every function in this module that as much as *touches* a row (
``local_bytes_reachable``, ``provide_bytes_for_admitted_unit``) fails
closed to ``False``/``None`` -- never an exception, never a fetch -- the
instant the file, the table, or a matching row is not actually there. This
module never fetches, scrapes, or writes anything into ``data/sources.db``;
it only ever opens it ``mode=ro``.

Two, deliberately different, questions this module answers:

- ``local_bytes_reachable(unit_id)`` -- a cheap ``LIMIT 1`` probe, content-
  blind (returns only ``True``/``False``, never a row), safe to run for
  *every* real candidate unit uniformly regardless of secret builder
  eligibility -- this is a fact about local infrastructure/rights state,
  never about which family A3 privately held out, so disclosing it (see
  ``v4_a4_deterministic_extraction.derive_source_unit_extraction_residuals``)
  never leaks complement membership.
- ``provide_bytes_for_admitted_unit(unit_id)`` -- the real byte provider
  wired as A4's production default. Only ever called by
  ``run_deterministic_extraction`` for units the private builder packet
  actually names (never for the held-out one), and only this function -- not
  the residual probe above -- ever reads real row *text*.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SELF_ROOT = Path(__file__).resolve().parents[3]
if str(_SELF_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELF_ROOT))

from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout
from scripts.projects.open_model_data.inventory_existing_assets import PRIVATE_TEXTBOOK_SOURCES

ROOT = heldout.ROOT
PRIMARY_ROOT = heldout.PRIMARY_ROOT

ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"

RECEIPT_PATH = ADMISSION / "dataset_v4_source_byte_ingestion_admission_receipt_v1.json"
SCHEMA_PATH = CONTRACTS / "dataset_v4_source_byte_ingestion_admission_receipt_v1.schema.json"
A2_RECEIPT_PATH = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

SOURCES_DB_RELATIVE_PATH = "data/sources.db"

# The one operation this admission ever covers. Never widened in place --
# a future admission of a different operation is a distinct, separately
# reviewed artifact, not an edit to this constant.
ADMITTED_OPERATION = "deterministic_local_analysis"


class ByteIngestionAdmissionError(ValueError):
    """The admission receipt cannot be built or verified safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ByteIngestionAdmissionError(message)


canonical_json = heldout.canonical_json


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- frozen local-store binding (real, hashed, never touches row text) -----

LOCAL_STORE_BINDINGS: dict[str, dict[str, str]] = {
    "db.external_articles": {
        "sqlite_table": "external_articles",
        "text_column": "text",
        "row_filter": "none",
        "order_by": "id_ascending",
    },
    "db.literary_texts": {
        "sqlite_table": "literary_texts",
        "text_column": "text",
        "row_filter": "none",
        "order_by": "id_ascending",
    },
    "db.textbooks.public": {
        "sqlite_table": "textbooks",
        "text_column": "text",
        "row_filter": "source_file_not_in_private_textbook_sources",
        "order_by": "id_ascending",
    },
    "db.wikipedia": {
        "sqlite_table": "wikipedia",
        "text_column": "text",
        "row_filter": "none",
        "order_by": "id_ascending",
    },
}

ADMITTED_SOURCE_UNIT_IDS = frozenset(LOCAL_STORE_BINDINGS)

ROW_FILTER_DEFINITIONS: dict[str, str] = {
    "none": "no filter -- every row currently in the table is in scope",
    "source_file_not_in_private_textbook_sources": (
        "source_file NOT IN (the 8 private ULP/Ohoiko reference source_file values already "
        "public in docs/corpus-inventory.md and inventory_existing_assets.PRIVATE_TEXTBOOK_SOURCES)"
    ),
}

LOCAL_STORE_BINDING_DESCRIPTOR: dict[str, Any] = {
    "descriptor_id": "v4-source-byte-ingestion-local-store-binding-v1",
    "descriptor_version": "v1",
    "admitted_operation": ADMITTED_OPERATION,
    "content_blind": False,
    "text_emitted": False,
    "bindings": LOCAL_STORE_BINDINGS,
    "row_filter_definitions": ROW_FILTER_DEFINITIONS,
}

LOCAL_STORE_BINDING_DESCRIPTOR_SHA256 = sha256_text(canonical_json(LOCAL_STORE_BINDING_DESCRIPTOR))


def local_sources_db_path(primary_root: Path = PRIMARY_ROOT) -> Path:
    """Resolve ``data/sources.db`` against the shared **primary** checkout --
    never against ``Path(__file__)`` -- the same discovery
    ``v4_a3_heldout_family_assignment.PRIMARY_ROOT`` already uses for
    ``batch_state/``. A dispatch worktree never carries its own copy of this
    ~1.9 GiB, gitignored, machine-local file."""
    return primary_root / SOURCES_DB_RELATIVE_PATH


def _connect_read_only(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _row_filter_clause(binding: dict[str, str]) -> tuple[str, tuple[Any, ...]]:
    if binding["row_filter"] == "source_file_not_in_private_textbook_sources":
        placeholders = ",".join("?" for _ in PRIVATE_TEXTBOOK_SOURCES)
        return f" WHERE source_file NOT IN ({placeholders})", tuple(PRIVATE_TEXTBOOK_SOURCES)
    return "", ()


def _select_sql(binding: dict[str, str]) -> tuple[str, tuple[Any, ...]]:
    where, parameters = _row_filter_clause(binding)
    table = binding["sqlite_table"]
    column = binding["text_column"]
    return f'SELECT "{column}" FROM "{table}"{where} ORDER BY id ASC', parameters


def _probe_sql(binding: dict[str, str]) -> tuple[str, tuple[Any, ...]]:
    where, parameters = _row_filter_clause(binding)
    table = binding["sqlite_table"]
    return f'SELECT 1 FROM "{table}"{where} LIMIT 1', parameters


def row_count_if_reachable(source_unit_id: str, primary_root: Path = PRIMARY_ROOT) -> int | None:
    """Live row count for an admitted unit, or ``None`` if unreachable right
    now (not admitted, store/table missing). Informational only -- never
    asserted against A2's own ``inventory_record_count`` snapshot, which is
    a point-in-time figure that legitimately drifts as the corpus grows."""
    if source_unit_id not in LOCAL_STORE_BINDINGS:
        return None
    db_path = local_sources_db_path(primary_root)
    if not db_path.is_file():
        return None
    binding = LOCAL_STORE_BINDINGS[source_unit_id]
    try:
        connection = _connect_read_only(db_path)
    except sqlite3.Error:
        return None
    try:
        if not _table_exists(connection, binding["sqlite_table"]):
            return None
        where, parameters = _row_filter_clause(binding)
        table = binding["sqlite_table"]
        return int(connection.execute(f'SELECT COUNT(*) FROM "{table}"{where}', parameters).fetchone()[0])
    except sqlite3.Error:
        return None
    finally:
        connection.close()


def local_bytes_reachable(source_unit_id: str, primary_root: Path = PRIMARY_ROOT) -> bool:
    """Cheap, content-blind ``LIMIT 1`` probe: ``True`` only if this unit is
    admitted *and* the local store file/table is present *and* at least one
    matching row exists right now. Never reads or returns any row's actual
    text. This is purely a fact about local infrastructure/rights state --
    independent of, and never a channel for, the private builder-eligible
    complement: every real candidate unit is probed identically regardless
    of secret eligibility, which is what makes it safe for
    ``v4_a4_deterministic_extraction.derive_source_unit_extraction_residuals``
    to disclose."""
    if source_unit_id not in LOCAL_STORE_BINDINGS:
        return False
    db_path = local_sources_db_path(primary_root)
    if not db_path.is_file():
        return False
    binding = LOCAL_STORE_BINDINGS[source_unit_id]
    try:
        connection = _connect_read_only(db_path)
    except sqlite3.Error:
        return False
    try:
        if not _table_exists(connection, binding["sqlite_table"]):
            return False
        sql, parameters = _probe_sql(binding)
        return connection.execute(sql, parameters).fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        connection.close()


def provide_bytes_for_admitted_unit(source_unit_id: str, primary_root: Path = PRIMARY_ROOT) -> bytes | None:
    """The real, production byte provider. Returns ``None`` -- never raises,
    never fetches anything remote -- for any unit outside
    ``ADMITTED_SOURCE_UNIT_IDS``, or when the local store file/table is
    missing, or when the query yields zero rows; callers must treat
    ``None`` exactly like "no bytes available", never as an error. Row text
    is joined in a fixed, deterministic order (ascending SQLite ``id``) with
    a fixed separator; this function never itself logs, prints, or persists
    the joined text -- the only caller
    (``v4_a4_deterministic_extraction.run_deterministic_extraction``) hashes
    it into per-span/output hashes immediately and discards it."""
    if source_unit_id not in LOCAL_STORE_BINDINGS:
        return None
    db_path = local_sources_db_path(primary_root)
    if not db_path.is_file():
        return None
    binding = LOCAL_STORE_BINDINGS[source_unit_id]
    try:
        connection = _connect_read_only(db_path)
    except sqlite3.Error:
        return None
    try:
        if not _table_exists(connection, binding["sqlite_table"]):
            return None
        sql, parameters = _select_sql(binding)
        rows = connection.execute(sql, parameters).fetchall()
    except sqlite3.Error:
        return None
    finally:
        connection.close()
    if not rows:
        return None
    text = "\n\n".join(str(value or "") for (value,) in rows)
    return text.encode("utf-8")


# --- admission scope re-derivation from A2's own public ledger -------------


def admitted_source_unit_ids_from_a2(a2_receipt: dict[str, Any]) -> frozenset[str]:
    """Independently re-derive which real ``source_unit_id``s qualify for
    this admission, purely from A2's own already-public fields: real byte
    content (``metadata_only`` false) and an already-allowed/scope_bound
    ``deterministic_local_analysis`` right. Guards against
    ``LOCAL_STORE_BINDINGS`` silently drifting from what A2 actually
    admits."""
    ids = set()
    for entry in a2_receipt["source_operation_ledger"]:
        if entry["metadata_only"]:
            continue
        if entry["operation_rights"]["deterministic_local_analysis"]["value"] not in ("allowed", "scope_bound"):
            continue
        ids.add(entry["source_unit_id"])
    return frozenset(ids)


# --- receipt assembly --------------------------------------------------------


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_receipt(root: Path = ROOT, primary_root: Path = PRIMARY_ROOT) -> dict[str, Any]:
    a2_receipt = _load(A2_RECEIPT_PATH)
    recomputed_ids = admitted_source_unit_ids_from_a2(a2_receipt)
    require(
        recomputed_ids == ADMITTED_SOURCE_UNIT_IDS,
        "ADMITTED_SOURCE_UNIT_IDS has drifted from what A2's own public source_operation_ledger "
        f"currently admits -- recomputed {sorted(recomputed_ids)} -- refusing",
    )

    admitted_units = []
    for source_unit_id in sorted(ADMITTED_SOURCE_UNIT_IDS):
        binding = LOCAL_STORE_BINDINGS[source_unit_id]
        admitted_units.append(
            {
                "source_unit_id": source_unit_id,
                "sqlite_table": binding["sqlite_table"],
                "text_column": binding["text_column"],
                "row_filter": binding["row_filter"],
                "order_by": binding["order_by"],
                "admitted_operation": ADMITTED_OPERATION,
                "local_store_reachable_at_admission": local_bytes_reachable(source_unit_id, primary_root),
                "row_count_observed_at_admission": row_count_if_reachable(source_unit_id, primary_root),
            }
        )

    return {
        "schema_version": "dataset_v4_source_byte_ingestion_admission_receipt_v1",
        "receipt_id": "dataset-v4-source-byte-ingestion-admission-v1",
        "status": "V4_SOURCE_BYTE_INGESTION_ADMITTED_HASHING_ONLY_TEXT_FREE",
        "text_free": True,
        "controlling_outcome_sha256": V4_SHA256,
        "control_surfaces": {"public_control_issue": 7423, "pilot_child_issue": 7430, "private_operational_board": 622},
        "bindings": {
            "a2_source_operation_admission": {
                "path": str(A2_RECEIPT_PATH.relative_to(root)),
                "sha256": sha256_file(A2_RECEIPT_PATH),
                "schema_version": "dataset_v4_a2_source_operation_admission_receipt_v1",
            },
            "local_store_binding_implementation": {
                "path": "scripts/projects/open_model_data/v4_source_byte_ingestion_admission.py",
                "sha256": sha256_file(root / "scripts/projects/open_model_data/v4_source_byte_ingestion_admission.py"),
                "schema_version": "v4_source_byte_ingestion_admission_script_v1",
            },
        },
        "admitted_operation": ADMITTED_OPERATION,
        "local_store_binding_descriptor": {
            "descriptor_id": LOCAL_STORE_BINDING_DESCRIPTOR["descriptor_id"],
            "descriptor_version": LOCAL_STORE_BINDING_DESCRIPTOR["descriptor_version"],
            "admitted_operation": LOCAL_STORE_BINDING_DESCRIPTOR["admitted_operation"],
            "content_blind": LOCAL_STORE_BINDING_DESCRIPTOR["content_blind"],
            "text_emitted": LOCAL_STORE_BINDING_DESCRIPTOR["text_emitted"],
            "row_filter_definitions": ROW_FILTER_DEFINITIONS,
            "descriptor_sha256": LOCAL_STORE_BINDING_DESCRIPTOR_SHA256,
        },
        "admitted_source_units": admitted_units,
        "execution_counters": {"dataset_rows_emitted": 0},
        "safety_assertions": {
            "rows_not_admitted": True,
            "text_emitted": False,
            "operations_admitted": [ADMITTED_OPERATION],
            "training_use_expanded": False,
            "publication_expanded": False,
            "redistribution_expanded": False,
            "transmission_to_external_service_expanded": False,
            "mac_corpus_copy_created": False,
            "prebuilder_state_claimed": False,
            "epic_done_claimed": False,
        },
    }


def _load_schema() -> dict[str, Any]:
    schema = _load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_receipt_schema(receipt: dict[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load_schema()).iter_errors(receipt), key=lambda e: list(e.path))
    require(not errors, f"receipt fails schema validation: {errors[0].message}" if errors else "")


def validate_bindings_hash_to_disk(receipt: dict[str, Any], root: Path) -> None:
    for name, binding in receipt["bindings"].items():
        bound_path = (root / binding["path"]).resolve()
        require(
            root.resolve() in bound_path.parents or bound_path == root.resolve(),
            f"binding {name!r} path escapes the repository root -- refusing: {binding['path']}",
        )
        require(bound_path.is_file(), f"binding {name!r} does not point at a file: {bound_path}")
        actual = sha256_file(bound_path)
        require(
            actual == binding["sha256"],
            f"binding {name!r} on-disk sha256 ({actual}) does not match the receipt's declared "
            f"sha256 ({binding['sha256']}) for {binding['path']} -- refusing",
        )


def validate_local_store_binding_descriptor(receipt: dict[str, Any]) -> None:
    descriptor = receipt["local_store_binding_descriptor"]
    require(
        descriptor["descriptor_sha256"] == LOCAL_STORE_BINDING_DESCRIPTOR_SHA256,
        "local_store_binding_descriptor.descriptor_sha256 does not match the locally recomputed frozen "
        "descriptor hash -- refusing",
    )
    require(
        descriptor["row_filter_definitions"] == ROW_FILTER_DEFINITIONS,
        "local_store_binding_descriptor.row_filter_definitions does not match the frozen definitions -- refusing",
    )


def validate_admitted_source_units_reproduce(receipt: dict[str, Any]) -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    recomputed_ids = admitted_source_unit_ids_from_a2(a2_receipt)
    require(
        recomputed_ids == ADMITTED_SOURCE_UNIT_IDS,
        "ADMITTED_SOURCE_UNIT_IDS has drifted from A2's live public source_operation_ledger -- refusing",
    )
    declared_ids = {unit["source_unit_id"] for unit in receipt["admitted_source_units"]}
    require(
        declared_ids == ADMITTED_SOURCE_UNIT_IDS,
        "admitted_source_units does not name exactly ADMITTED_SOURCE_UNIT_IDS -- refusing",
    )
    for unit in receipt["admitted_source_units"]:
        binding = LOCAL_STORE_BINDINGS[unit["source_unit_id"]]
        require(
            unit["sqlite_table"] == binding["sqlite_table"]
            and unit["text_column"] == binding["text_column"]
            and unit["row_filter"] == binding["row_filter"]
            and unit["order_by"] == binding["order_by"]
            and unit["admitted_operation"] == ADMITTED_OPERATION,
            f"admitted_source_units entry for {unit['source_unit_id']!r} does not match the frozen "
            "LOCAL_STORE_BINDINGS -- refusing",
        )


def validate_receipt_independently(receipt: dict[str, Any], root: Path = ROOT) -> None:
    validate_receipt_schema(receipt)
    validate_bindings_hash_to_disk(receipt, root)
    validate_local_store_binding_descriptor(receipt)
    validate_admitted_source_units_reproduce(receipt)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--receipt", type=Path, default=RECEIPT_PATH, help="admission receipt JSON to verify")
    parser.add_argument(
        "--write-receipt",
        action="store_true",
        help="(Re)build the admission receipt from the frozen local-store binding and write it to --receipt.",
    )
    args = parser.parse_args(argv)

    if args.write_receipt:
        receipt = build_receipt()
        validate_receipt_independently(receipt)
        args.receipt.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(canonical_json({"status": receipt["status"], "admitted_source_unit_count": len(receipt["admitted_source_units"])}))
        return

    receipt = _load(args.receipt)
    validate_receipt_independently(receipt)
    print(canonical_json({"status": receipt["status"]}))


if __name__ == "__main__":
    try:
        main()
    except ByteIngestionAdmissionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
