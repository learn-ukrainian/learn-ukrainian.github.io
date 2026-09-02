"""V4 source byte ingestion admission: local-store binding, byte provider,
and the public admission receipt's independent verification.

Every SQLite fixture here is synthetic (built in ``tmp_path``, never the real
``data/sources.db``); real-corpus reads are exercised only indirectly, via
functions parameterized on ``primary_root`` so no test needs the real
~1.9 GiB file to pass. ``PRIVATE_TEXTBOOK_SOURCES`` values are reused as-is
(already public) so the private-textbook-exclusion filter is exercised with
the exact real filter values.
"""

from __future__ import annotations

import copy
import inspect
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_source_byte_ingestion_admission as admission
from scripts.projects.open_model_data.inventory_existing_assets import PRIVATE_TEXTBOOK_SOURCES

ROOT = Path(__file__).resolve().parents[3]
A2_RECEIPT_PATH = admission.A2_RECEIPT_PATH


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _make_sources_db(tmp_path: Path, *, with_literary: bool = True) -> Path:
    """A synthetic ``data/sources.db`` under a fake primary root, shaped like
    the real one's four admitted tables (plus a private textbook row, to
    exercise the exclusion filter with real values)."""
    db_path = tmp_path / "data" / "sources.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE external_articles (id INTEGER PRIMARY KEY, text TEXT)")
    if with_literary:
        connection.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, text TEXT)")
        connection.execute("INSERT INTO literary_texts (text) VALUES ('Lit one.'), ('Lit two.')")
    connection.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, text TEXT, source_file TEXT)")
    connection.execute("CREATE TABLE wikipedia (id INTEGER PRIMARY KEY, text TEXT)")
    connection.execute("INSERT INTO external_articles (text) VALUES ('First article.'), ('Second article.')")
    connection.execute(
        "INSERT INTO textbooks (text, source_file) VALUES (?, ?), (?, ?)",
        ("Public chunk.", "public-book", "Private chunk.", PRIVATE_TEXTBOOK_SOURCES[0]),
    )
    connection.execute("INSERT INTO wikipedia (text) VALUES ('Wiki one.')")
    connection.commit()
    connection.close()
    return tmp_path


# --- local store path resolution --------------------------------------------


def test_local_sources_db_path_resolves_against_primary_root(tmp_path: Path) -> None:
    assert admission.local_sources_db_path(tmp_path) == tmp_path / "data/sources.db"


# --- byte provider: real, admitted-only, fails closed -----------------------


def test_provide_bytes_returns_none_for_a_non_admitted_unit(tmp_path: Path) -> None:
    _make_sources_db(tmp_path)
    assert admission.provide_bytes_for_admitted_unit("historical.some-unit", tmp_path) is None


def test_provide_bytes_returns_none_when_local_store_file_missing(tmp_path: Path) -> None:
    assert admission.provide_bytes_for_admitted_unit("db.wikipedia", tmp_path) is None


def test_provide_bytes_returns_none_when_table_missing(tmp_path: Path) -> None:
    _make_sources_db(tmp_path, with_literary=False)
    assert admission.provide_bytes_for_admitted_unit("db.literary_texts", tmp_path) is None


def test_provide_bytes_joins_rows_in_id_order_for_an_unfiltered_unit(tmp_path: Path) -> None:
    _make_sources_db(tmp_path)
    result = admission.provide_bytes_for_admitted_unit("db.external_articles", tmp_path)
    assert result == b"First article.\n\nSecond article."


def test_provide_bytes_excludes_private_textbook_sources(tmp_path: Path) -> None:
    _make_sources_db(tmp_path)
    result = admission.provide_bytes_for_admitted_unit("db.textbooks.public", tmp_path)
    assert result == b"Public chunk."
    assert b"Private chunk." not in (result or b"")


def test_provide_bytes_returns_none_when_filtered_rows_are_all_private(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "sources.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, text TEXT, source_file TEXT)")
    connection.execute(
        "INSERT INTO textbooks (text, source_file) VALUES (?, ?)", ("Private only.", PRIVATE_TEXTBOOK_SOURCES[0])
    )
    connection.commit()
    connection.close()
    assert admission.provide_bytes_for_admitted_unit("db.textbooks.public", tmp_path) is None


def test_provide_bytes_never_raises_on_a_corrupt_file(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "sources.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b"not a real sqlite file")
    assert admission.provide_bytes_for_admitted_unit("db.wikipedia", tmp_path) is None
    assert admission.local_bytes_reachable("db.wikipedia", tmp_path) is False


# --- streaming row provider: memory-bounded, real production default --------


def test_iter_admitted_unit_row_texts_matches_provide_bytes_for_admitted_unit(tmp_path: Path) -> None:
    """The streaming and whole-blob providers must agree: joining every
    streamed row with the same separator reproduces the whole-blob output
    exactly, for every admitted unit."""
    _make_sources_db(tmp_path)
    for unit_id in admission.ADMITTED_SOURCE_UNIT_IDS:
        streamed = list(admission.iter_admitted_unit_row_texts(unit_id, tmp_path))
        whole = admission.provide_bytes_for_admitted_unit(unit_id, tmp_path)
        if not streamed:
            assert whole is None
        else:
            assert "\n\n".join(streamed).encode("utf-8") == whole


def test_iter_admitted_unit_row_texts_yields_nothing_for_a_non_admitted_unit(tmp_path: Path) -> None:
    _make_sources_db(tmp_path)
    assert list(admission.iter_admitted_unit_row_texts("historical.some-unit", tmp_path)) == []


def test_iter_admitted_unit_row_texts_yields_nothing_when_local_store_file_missing(tmp_path: Path) -> None:
    assert list(admission.iter_admitted_unit_row_texts("db.wikipedia", tmp_path)) == []


def test_iter_admitted_unit_row_texts_yields_nothing_when_table_missing(tmp_path: Path) -> None:
    _make_sources_db(tmp_path, with_literary=False)
    assert list(admission.iter_admitted_unit_row_texts("db.literary_texts", tmp_path)) == []


def test_iter_admitted_unit_row_texts_excludes_private_textbook_sources(tmp_path: Path) -> None:
    _make_sources_db(tmp_path)
    rows = list(admission.iter_admitted_unit_row_texts("db.textbooks.public", tmp_path))
    assert rows == ["Public chunk."]


def test_iter_admitted_unit_row_texts_never_raises_on_a_corrupt_file(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "sources.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b"not a real sqlite file")
    assert list(admission.iter_admitted_unit_row_texts("db.wikipedia", tmp_path)) == []


def test_iter_admitted_unit_row_texts_is_a_generator_function() -> None:
    """A generator function cannot itself hold a fully-materialized
    ``.fetchall()``/``.fetchmany()`` result list across the whole call --
    each ``yield`` suspends with only the current row's text live. (Its
    body is additionally verified never to call ``sqlite3.Cursor.fetchall``/
    ``fetchmany`` at all -- see the module source; those C-level cursor
    methods are immutable and cannot be monkeypatched to assert this
    behaviourally.)"""
    assert inspect.isgeneratorfunction(admission.iter_admitted_unit_row_texts)


def test_iter_admitted_unit_row_texts_streams_a_large_table_row_by_row(tmp_path: Path) -> None:
    """Behavioral proxy for "streams, never buffers the whole result set":
    a few thousand rows, consumed lazily one at a time, in the same
    ascending-id order the whole-blob provider uses."""
    db_path = tmp_path / "data" / "sources.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE wikipedia (id INTEGER PRIMARY KEY, text TEXT)")
    connection.executemany("INSERT INTO wikipedia (text) VALUES (?)", [(f"Row {i}.",) for i in range(5000)])
    connection.commit()
    connection.close()

    generator = admission.iter_admitted_unit_row_texts("db.wikipedia", tmp_path)
    first = next(generator)
    assert first == "Row 0."  # proves at least one row is available before the rest are consumed
    remaining = list(generator)
    assert len(remaining) == 4999
    assert remaining[-1] == "Row 4999."


# --- reachability probe: cheap, content-blind --------------------------------


def test_local_bytes_reachable_true_only_for_admitted_and_present(tmp_path: Path) -> None:
    _make_sources_db(tmp_path)
    assert admission.local_bytes_reachable("db.wikipedia", tmp_path) is True
    assert admission.local_bytes_reachable("historical.some-unit", tmp_path) is False


def test_local_bytes_reachable_false_when_store_missing(tmp_path: Path) -> None:
    assert admission.local_bytes_reachable("db.wikipedia", tmp_path) is False


def test_local_bytes_reachable_false_when_zero_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "sources.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE wikipedia (id INTEGER PRIMARY KEY, text TEXT)")
    connection.commit()
    connection.close()
    assert admission.local_bytes_reachable("db.wikipedia", tmp_path) is False


def test_local_bytes_reachable_never_returns_row_text() -> None:
    """Content-blind by construction: the probe SQL is ``SELECT 1 ... LIMIT
    1``, never the text column."""
    binding = admission.LOCAL_STORE_BINDINGS["db.wikipedia"]
    sql, _ = admission._probe_sql(binding)
    assert sql.startswith("SELECT 1 FROM")
    assert sql.rstrip().endswith("LIMIT 1")
    assert f'"{binding["text_column"]}"' not in sql


def test_row_count_if_reachable(tmp_path: Path) -> None:
    _make_sources_db(tmp_path)
    assert admission.row_count_if_reachable("db.external_articles", tmp_path) == 2
    assert admission.row_count_if_reachable("db.textbooks.public", tmp_path) == 1
    assert admission.row_count_if_reachable("historical.some-unit", tmp_path) is None
    assert admission.row_count_if_reachable("db.literary_texts", tmp_path.parent) is None


# --- admission scope re-derivation from A2 -----------------------------------


def test_admitted_source_unit_ids_from_a2_matches_the_real_hardcoded_set() -> None:
    a2_receipt = _load(A2_RECEIPT_PATH)
    assert admission.admitted_source_unit_ids_from_a2(a2_receipt) == admission.ADMITTED_SOURCE_UNIT_IDS


def test_admitted_source_unit_ids_from_a2_excludes_metadata_only_and_denied() -> None:
    synthetic = {
        "source_operation_ledger": [
            {
                "source_unit_id": "synthetic.metadata-only",
                "metadata_only": True,
                "operation_rights": {"deterministic_local_analysis": {"value": "allowed"}},
            },
            {
                "source_unit_id": "synthetic.denied",
                "metadata_only": False,
                "operation_rights": {"deterministic_local_analysis": {"value": "denied"}},
            },
            {
                "source_unit_id": "synthetic.admitted",
                "metadata_only": False,
                "operation_rights": {"deterministic_local_analysis": {"value": "scope_bound"}},
            },
        ]
    }
    assert admission.admitted_source_unit_ids_from_a2(synthetic) == frozenset({"synthetic.admitted"})


# --- frozen descriptor --------------------------------------------------------


def test_local_store_binding_descriptor_is_frozen_and_hashed() -> None:
    recomputed = admission.sha256_text(admission.canonical_json(admission.LOCAL_STORE_BINDING_DESCRIPTOR))
    assert recomputed == admission.LOCAL_STORE_BINDING_DESCRIPTOR_SHA256


def test_admitted_source_unit_ids_is_exactly_the_four_real_db_units() -> None:
    assert {
        "db.external_articles",
        "db.literary_texts",
        "db.textbooks.public",
        "db.wikipedia",
    } == admission.ADMITTED_SOURCE_UNIT_IDS


# --- real production receipt: schema + independent verification ------------


def _receipt() -> dict[str, Any]:
    return _load(admission.RECEIPT_PATH)


def _validator() -> Draft202012Validator:
    schema = _load(admission.SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_receipt_schema_and_v4_binding() -> None:
    receipt = _receipt()
    errors = sorted(_validator().iter_errors(receipt), key=lambda error: list(error.path))
    assert not errors
    assert receipt["controlling_outcome_sha256"] == admission.V4_SHA256
    assert receipt["text_free"] is True
    assert receipt["admitted_operation"] == "deterministic_local_analysis"


def test_receipt_admits_exactly_the_four_real_db_units() -> None:
    receipt = _receipt()
    ids = {unit["source_unit_id"] for unit in receipt["admitted_source_units"]}
    assert ids == admission.ADMITTED_SOURCE_UNIT_IDS


def test_receipt_never_carries_source_text() -> None:
    """No row body ever appears -- only structural metadata (including the
    literal column *name* ``"text"``, which is fine; that names a schema
    shape, not row content)."""
    receipt = _receipt()
    forbidden = {"content", "source_body", "source_text", "prompt", "label", "gold"}
    assert not (set(receipt) & forbidden)
    for unit in receipt["admitted_source_units"]:
        assert not (set(unit) & forbidden)
        assert unit["text_column"] == "text"


def test_validate_receipt_independently_passes_for_the_checked_in_receipt() -> None:
    admission.validate_receipt_independently(_receipt())  # must not raise


def test_validate_receipt_independently_refuses_a_tampered_binding_hash() -> None:
    tampered = copy.deepcopy(_receipt())
    tampered["bindings"]["a2_source_operation_admission"]["sha256"] = "0" * 64
    with pytest.raises(admission.ByteIngestionAdmissionError):
        admission.validate_receipt_independently(tampered)


def test_validate_receipt_independently_refuses_a_tampered_descriptor_hash() -> None:
    tampered = copy.deepcopy(_receipt())
    tampered["local_store_binding_descriptor"]["descriptor_sha256"] = "0" * 64
    with pytest.raises(admission.ByteIngestionAdmissionError, match="descriptor_sha256"):
        admission.validate_receipt_independently(tampered)


def test_validate_receipt_independently_refuses_a_dropped_admitted_unit() -> None:
    """Dropping a unit shrinks ``admitted_source_units`` below the schema's
    ``minItems: 4`` -- caught by schema validation, which runs first; still
    a refusal either way."""
    tampered = copy.deepcopy(_receipt())
    tampered["admitted_source_units"].pop()
    with pytest.raises(admission.ByteIngestionAdmissionError, match="too short"):
        admission.validate_receipt_independently(tampered)


def test_validate_admitted_source_units_reproduce_refuses_a_dropped_unit_directly() -> None:
    """Isolates ``validate_admitted_source_units_reproduce`` from schema
    validation to exercise its own ``ADMITTED_SOURCE_UNIT_IDS`` cross-check."""
    tampered = copy.deepcopy(_receipt())
    tampered["admitted_source_units"].pop()
    with pytest.raises(admission.ByteIngestionAdmissionError, match="ADMITTED_SOURCE_UNIT_IDS"):
        admission.validate_admitted_source_units_reproduce(tampered)


def test_validate_receipt_independently_refuses_a_binding_mismatch() -> None:
    tampered = copy.deepcopy(_receipt())
    tampered["admitted_source_units"][0]["sqlite_table"] = "not_the_real_table"
    with pytest.raises(admission.ByteIngestionAdmissionError, match="frozen LOCAL_STORE_BINDINGS"):
        admission.validate_receipt_independently(tampered)


# --- build_receipt against a synthetic local store --------------------------


def test_build_receipt_records_live_reachability_against_a_synthetic_store(tmp_path: Path) -> None:
    _make_sources_db(tmp_path)
    receipt = admission.build_receipt(root=ROOT, primary_root=tmp_path)
    admission.validate_receipt_independently(receipt, root=ROOT)
    by_id = {unit["source_unit_id"]: unit for unit in receipt["admitted_source_units"]}
    assert by_id["db.external_articles"]["local_store_reachable_at_admission"] is True
    assert by_id["db.external_articles"]["row_count_observed_at_admission"] == 2
    assert by_id["db.textbooks.public"]["row_count_observed_at_admission"] == 1


def test_build_receipt_records_unreachable_when_local_store_absent(tmp_path: Path) -> None:
    receipt = admission.build_receipt(root=ROOT, primary_root=tmp_path)
    for unit in receipt["admitted_source_units"]:
        assert unit["local_store_reachable_at_admission"] is False
        assert unit["row_count_observed_at_admission"] is None


# --- CLI ---------------------------------------------------------------


def test_cli_default_verifies_the_checked_in_receipt(capsys: pytest.CaptureFixture) -> None:
    admission.main([])
    printed = json.loads(capsys.readouterr().out)
    assert printed["status"] == "V4_SOURCE_BYTE_INGESTION_ADMITTED_HASHING_ONLY_TEXT_FREE"
