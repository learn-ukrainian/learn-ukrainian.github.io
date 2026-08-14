from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_school_context_negative_recovery as negrec

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/projects/open_model_data/contracts/phase3_school_context_negative_recovery_receipt_v1.schema.json"
PUBLIC_RECEIPT = ROOT / "data/projects/open_model_data/inventory/phase3_school_context_negative_recovery_receipt_v1.json"


def _school_row(
    *,
    unit_suffix: str,
    source_file: str,
    record_id: int,
    chunk_id: str,
    parent_section_id: str | None,
    text: str = "x",
) -> dict[str, object]:
    unit_id = f"unit.school_textbooks.{unit_suffix}"
    unit_sha = negrec.sha256_bytes(f"{unit_id}:{text}".encode())
    return {
        "family_id": "school_textbooks",
        "unit_id": unit_id,
        "unit_sha256": unit_sha,
        "source_text": text,
        "source_text_sha256": negrec.sha256_bytes(text.encode()),
        "source_record": {
            "id": record_id,
            "chunk_id": chunk_id,
            "source_file": source_file,
            "parent_section_id": parent_section_id,
            "text": text,
        },
    }


def _partition_row(source_row: dict[str, object]) -> dict[str, object]:
    return {
        "family_id": "school_textbooks",
        "unit_id": source_row["unit_id"],
        "unit_sha256": source_row["unit_sha256"],
        "reason": "evaluation_only",
        "candidate_lane": "phenomenon_strata",
        "source_text_sha256": source_row["source_text_sha256"],
        "frozen_locator_sha256": "0" * 64,
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_bytes(b"".join(negrec.canonical_bytes(row) for row in rows))
    os.chmod(path, 0o600)


def test_schema_and_committed_receipt_validate() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    receipt = json.loads(PUBLIC_RECEIPT.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(receipt)
    assert negrec.receipt_sha256(receipt) == receipt["receipt_sha256"]
    assert receipt["disposition"] == "school_complete_parent_or_sentence_context_not_recoverable"
    assert receipt["gates"]["phase4_blocked"] is True
    assert receipt["gates"]["school_complete_context_ready"] is False
    assert receipt["context_retained"]["complete_sentence_context"] is False


def test_canonical_and_quarantine_invariants() -> None:
    negrec._assert_reanchor_invariants()


def test_synthetic_census_matches_expected_split(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Scale-down fixture: 3 held-out school rows, 2 null-parent, 1 complete section sibling pair.
    complete_a = _school_row(
        unit_suffix="complete-a",
        source_file="book-a.jsonl",
        record_id=1,
        chunk_id="c1",
        parent_section_id="sec-1",
        text="aa",
    )
    complete_b = _school_row(
        unit_suffix="complete-b",
        source_file="book-a.jsonl",
        record_id=2,
        chunk_id="c2",
        parent_section_id="sec-1",
        text="bb",
    )
    null_a = _school_row(
        unit_suffix="null-a",
        source_file="book-b.jsonl",
        record_id=3,
        chunk_id="c3",
        parent_section_id=None,
        text="cc",
    )
    null_b = _school_row(
        unit_suffix="null-b",
        source_file="book-b.jsonl",
        record_id=4,
        chunk_id="c4",
        parent_section_id=None,
        text="dd",
    )
    source_rows = [complete_a, complete_b, null_a, null_b]
    heldout = [complete_a, null_a, null_b]

    source_path = tmp_path / "source_units_v1.jsonl"
    partition_path = tmp_path / "partition_manifest_v1.jsonl"
    _write_jsonl(source_path, source_rows)
    _write_jsonl(partition_path, [_partition_row(row) for row in heldout])

    monkeypatch.setattr(negrec, "PINNED_SOURCE_UNITS_JSONL_SHA256", negrec.sha256_file(source_path))
    monkeypatch.setattr(negrec, "PINNED_PARTITION_SHA256", negrec.sha256_file(partition_path))
    monkeypatch.setattr(negrec, "SCHOOL_UNIVERSE", 4)
    monkeypatch.setattr(negrec, "SCHOOL_HELDOUT", 3)
    monkeypatch.setattr(negrec, "PARENT_NULL_HELDOUT", 2)
    monkeypatch.setattr(negrec, "PARENT_COMPLETE_HELDOUT", 1)
    monkeypatch.setattr(negrec, "SCHOOL_NULL_PARENT_ROWS", 2)
    monkeypatch.setattr(negrec, "NON_NULL_PARENT_GROUPS", 1)

    census = negrec.compute_parent_section_census(
        source_jsonl=source_path,
        partition_path=partition_path,
    )
    assert census == {
        "heldout_with_null_parent_section_id": 2,
        "heldout_in_complete_ordered_parent_section": 1,
        "school_rows_with_null_parent_section_id": 2,
        "non_null_parent_section_groups": 1,
        "freeze_section_grain_target": 7250,
    }


def test_null_parent_majority_is_required_for_negative_seal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    row = _school_row(
        unit_suffix="only",
        source_file="book.jsonl",
        record_id=1,
        chunk_id="c1",
        parent_section_id="sec",
        text="zz",
    )
    source_path = tmp_path / "source_units_v1.jsonl"
    partition_path = tmp_path / "partition_manifest_v1.jsonl"
    _write_jsonl(source_path, [row])
    _write_jsonl(partition_path, [_partition_row(row)])

    monkeypatch.setattr(negrec, "PINNED_SOURCE_UNITS_JSONL_SHA256", negrec.sha256_file(source_path))
    monkeypatch.setattr(negrec, "PINNED_PARTITION_SHA256", negrec.sha256_file(partition_path))
    monkeypatch.setattr(negrec, "SCHOOL_UNIVERSE", 1)
    monkeypatch.setattr(negrec, "SCHOOL_HELDOUT", 1)
    monkeypatch.setattr(negrec, "PARENT_NULL_HELDOUT", 0)
    monkeypatch.setattr(negrec, "PARENT_COMPLETE_HELDOUT", 1)
    monkeypatch.setattr(negrec, "SCHOOL_NULL_PARENT_ROWS", 0)
    monkeypatch.setattr(negrec, "NON_NULL_PARENT_GROUPS", 1)

    # If production constants still expect the sealed 4479 null majority, census must fail closed.
    monkeypatch.setattr(negrec, "PARENT_NULL_HELDOUT", 4479)
    with pytest.raises(negrec.SchoolContextNegativeRecoveryError, match="held-out null parent_section_id drift"):
        negrec.compute_parent_section_census(source_jsonl=source_path, partition_path=partition_path)


def test_candidate_database_matching_freeze_pin_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = tmp_path / "sources.db"
    candidate.write_bytes(b"not-the-freeze-db")
    negrec._assert_candidate_database_not_freeze(candidate)

    def _fake(path: Path) -> str:
        if path == candidate:
            return negrec.PINNED_FREEZE_DATABASE_SHA256
        return negrec.sha256_bytes(path.read_bytes())

    monkeypatch.setattr(negrec, "sha256_file", _fake)
    with pytest.raises(negrec.SchoolContextNegativeRecoveryError, match="unexpectedly matches freeze pin"):
        negrec._assert_candidate_database_not_freeze(candidate)


def test_public_ledger_parent_boundary_probe() -> None:
    negrec._assert_public_ledger_lacks_parent_boundaries()


def test_symlink_receipt_rejected(tmp_path: Path) -> None:
    target = tmp_path / "real.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    with pytest.raises(negrec.SchoolContextNegativeRecoveryError, match="symlink forbidden"):
        negrec._regular_file(link, "receipt")
