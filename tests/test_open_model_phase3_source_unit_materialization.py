"""Boundary tests for private Phase 3 source-unit materialization."""

from __future__ import annotations

import json
import os
import sqlite3
import stat
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_heldout_partition as heldout
from scripts.projects.open_model_data import phase3_source_unit_materialization as materializer
from scripts.projects.open_model_data import phase3_source_universe as source


def _database(path: Path, text: str = "secret source sentence") -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE ua_gec_errors (id INTEGER PRIMARY KEY, doc_id TEXT, error TEXT)")
        connection.execute("INSERT INTO ua_gec_errors VALUES (1, 'private-document', ?)", (text,))


def _ledger_for_database(path: Path) -> list[dict[str, object]]:
    with source._connect(path) as connection:
        family = {
            "input_identity": {"unit_grain": "fixture"},
            "rights": {
                "source_text_committed": False,
                "locator_only_allowed": True,
                "rights_limited_disposition": source.RIGHTS_PROVENANCE_CLASSIFICATION,
            },
        }
        return list(source._database_units(connection, "ua_gec_errors", "ua_gec", family, source.sha256_file(path)))


def test_repacked_sqlite_accepts_identical_relevant_rows_but_mutation_fails(tmp_path: Path) -> None:
    first, repacked = tmp_path / "first.sqlite", tmp_path / "repacked.sqlite"
    _database(first)
    # A VACUUM/metadata-container change is allowed when frozen row bindings match.
    _database(repacked)
    with repacked.open("ab") as handle:
        handle.write(b"container-only-trailing-bytes")
    ledger = _ledger_for_database(first)
    assert source.sha256_file(first) != source.sha256_file(repacked)
    with source._connect(repacked) as connection:
        rows = materializer._rebuild_database(connection, "ua_gec", ledger, source.sha256_file(repacked))
    assert rows[0]["source_text"] == "secret source sentence"
    with sqlite3.connect(repacked) as connection:
        connection.execute("UPDATE ua_gec_errors SET error = 'mutated source sentence' WHERE id = 1")
    with source._connect(repacked) as connection:
        with pytest.raises(materializer.MaterializationError, match="unit_sha256 mismatch"):
            materializer._rebuild_database(connection, "ua_gec", ledger, source.sha256_file(repacked))


def test_ua_gec_identity_matches_heldout_partition_and_calques_are_collection_scoped() -> None:
    ua_identity = materializer._identity("ua_gec", {"doc_id": "документ"}, {})
    assert ua_identity == heldout.document_identity_for_ua_gec("документ")
    identities = {
        materializer._identity("calque_inventory", {}, {"locator": {"collection": collection, "entry_id_sha256": f"{index}" * 64}})
        for index, collection in enumerate(("CURATED_CALQUES", "PHRASAL_CALQUES", "SENSE_RESTRICTED_CALQUES"), start=1)
    }
    assert len(identities) == 3
    assert materializer._identity("calque_inventory", {}, {"locator": {"collection": "CURATED_CALQUES", "entry_id_sha256": "a" * 64}}) == materializer._identity("calque_inventory", {}, {"locator": {"collection": "CURATED_CALQUES", "entry_id_sha256": "b" * 64}})


def test_private_row_retains_the_exact_frozen_locator() -> None:
    locator = {"kind": "sqlite_row", "table": "ua_gec_errors", "primary_key_fields": ["id"], "primary_key_sha256": "a" * 64}
    row = materializer._private_row(
        "ua_gec", {"unit_id": "unit.ua_gec.fixture", "unit_sha256": "b" * 64, "locator": locator},
        "secret source sentence", {"doc_id": "private-document"}, "doc.ua_gec.fixture",
    )
    assert row["frozen_locator"] == locator
    assert row["frozen_locator_sha256"] == source._unit_hash(locator)


def _rows() -> list[dict[str, object]]:
    counts = {
        "antonenko_style_guide": 342, "ua_gec": 8937, "school_textbooks": 54979,
        "antonenko_textbook_representation": 169, "calque_inventory": 58,
        "pravopys_2019_complete": 1090, "pravopys_2026_complete": 1466,
        "other_normative_style_inventory": 0,
    }
    rows: list[dict[str, object]] = []
    for family, count in counts.items():
        for ordinal in range(count):
            text = f"private source {family} {ordinal}"
            rows.append({
                "family_id": family, "unit_id": f"unit.{family}.{ordinal}", "unit_sha256": "a" * 64,
                "frozen_locator_sha256": "b" * 64, "document_or_edition_identity": f"identity.{ordinal}",
                "source_text": text, "source_record": {"raw_id": ordinal, "payload": text},
                "source_text_sha256": materializer.sha256_bytes(text.encode()),
            })
    return rows


def test_materialize_keeps_private_text_private_and_enforces_permissions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rows = _rows()
    monkeypatch.setattr(materializer, "reconstruct", lambda **_: (rows, "c" * 64))
    private_dir, public = tmp_path / "private", tmp_path / "public.json"
    receipt = materializer.materialize(
        source_universe=tmp_path / "universe", sources_db=tmp_path / "db", pravopys_2019_pdf=tmp_path / "2019",
        pravopys_2026_pdf=tmp_path / "2026", calque_module=tmp_path / "calques", pdftotext=tmp_path / "pdftotext",
        private_dir=private_dir, public_receipt=public,
    )
    assert receipt["private_record_count"] == 67041
    assert (private_dir.stat().st_mode & 0o777) == 0o700
    assert ((private_dir / materializer.PRIVATE_FILENAME).stat().st_mode & 0o777) == 0o600
    public_text = public.read_text(encoding="utf-8")
    assert "private source" not in public_text
    assert "raw_id" not in public_text
    assert "identity" not in public_text
    assert "locator" not in public_text
    assert "frozen_locator" not in public_text
    assert json.loads(public_text)["no_leakage"] is True


def test_rejects_stale_private_file_and_public_inside_private(tmp_path: Path) -> None:
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    os.chmod(private, 0o700)
    (private / "stale.json").write_text("{}", encoding="utf-8")
    with pytest.raises(materializer.MaterializationError, match="unexpected stale"):
        materializer._prepare_private_dir(private)
    private.joinpath("stale.json").unlink()
    output = materializer._prepare_private_dir(private)
    assert output.name == materializer.PRIVATE_FILENAME
    assert stat.S_IMODE(private.stat().st_mode) == 0o700


def test_rejects_outputs_nested_in_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(materializer, "reconstruct", lambda **_: (_rows(), "c" * 64))
    source_universe = tmp_path / "source-universe"
    source_universe.mkdir()
    with pytest.raises(materializer.MaterializationError, match="output may not be inside"):
        materializer.materialize(
            source_universe=source_universe, sources_db=tmp_path / "db", pravopys_2019_pdf=tmp_path / "2019",
            pravopys_2026_pdf=tmp_path / "2026", calque_module=tmp_path / "calques", pdftotext=tmp_path / "pdftotext",
            private_dir=source_universe / "private", public_receipt=tmp_path / "public.json",
        )
