"""The findings database (#8430 R2b-A): schema, lossless rows, settle items, budgets, parameters."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.review import findings_db as db

FINDING = {
    "id": "F-01",
    "status": "active",
    "locations": [{"tab": "urok", "quote": "q"}],
    "dimension": "language",
    "sub_dimension": "calque",
    "severity": "MINOR",
    "claim": "A claim.",
    "unsupported_by_source": {
        "searches": [{"receipt": "r-1", "outcome": "no_hits"}, {"receipt": "r-2", "outcome": "hits_but_no_support"}]
    },
    "could_be_a_gate": "yes - a script could look it up",
}


def attempt_row(**overrides) -> dict:
    row = {
        "review_id": "R1",
        "attempt_id": "A1",
        "kind": "lesson",
        "level": "a1",
        "slug": "m",
        "lesson_n": 2,
        "manifest_sha256": "ab" * 32,
        "reviewer_model": "claude-sonnet-5",
        "reviewer_family": "anthropic",
        "harness": "claude",
        "prompt_sha256": "cd" * 32,
        "verdict": "REVISE",
        "validated_at": "2026-09-25T00:00:00+00:00",
        "task_id": "t-1",
    }
    row.update(overrides)
    return row


@pytest.fixture
def conn(tmp_path: Path):
    connection = db.connect(tmp_path / "a1.sqlite")
    yield connection
    connection.close()


def test_the_database_has_the_contracts_tables_and_a_schema_version(conn: sqlite3.Connection) -> None:
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"attempts", "findings", "budgets", "settle_items", "agreement", "schema_version"} <= tables
    assert [row[0] for row in conn.execute("SELECT version FROM schema_version")] == [db.SCHEMA_VERSION]
    columns = {row[1] for row in conn.execute("PRAGMA table_info(attempts)")}
    assert {"rejection_codes_json", "task_id", "reviewer_family", "validated_at"} <= columns
    assert {"receipts_json", "finding_json", "layer", "seed_id"} <= {
        row[1] for row in conn.execute("PRAGMA table_info(findings)")
    }
    assert "receipt_id" not in {row[1] for row in conn.execute("PRAGMA table_info(findings)")}
    assert {"item_id", "opened_at", "outcome"} <= {row[1] for row in conn.execute("PRAGMA table_info(settle_items)")}


def test_opening_twice_is_idempotent_and_keeps_the_rows(tmp_path: Path) -> None:
    path = tmp_path / "a1.sqlite"
    first = db.connect(path)
    with db.transaction(first):
        db.insert_attempt(first, attempt_row())
    first.close()
    second = db.connect(path)
    assert second.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 1
    assert second.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 1
    second.close()


def test_a_database_with_another_schema_version_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "a1.sqlite"
    db.connect(path).close()
    raw = sqlite3.connect(path)
    raw.execute("UPDATE schema_version SET version = ?", (db.SCHEMA_VERSION + 1,))
    raw.commit()
    raw.close()
    with pytest.raises(db.VersionMismatch, match="refusing to open"):
        db.connect(path)


def test_tables_without_a_version_are_refused_not_adopted(tmp_path: Path) -> None:
    path = tmp_path / "a1.sqlite"
    raw = sqlite3.connect(path)
    raw.execute("CREATE TABLE attempts (x INTEGER)")
    raw.commit()
    raw.close()
    with pytest.raises(db.VersionMismatch):
        db.connect(path)


def test_the_path_is_per_level_under_batch_state(tmp_path: Path) -> None:
    assert db.db_path("a1", tmp_path) == tmp_path / "batch_state" / "review-findings" / "a1.sqlite"
    with pytest.raises(db.FindingsDbError):
        db.db_path("../a1", tmp_path)


def test_a_finding_is_stored_whole_with_every_receipt(conn: sqlite3.Connection) -> None:
    with db.transaction(conn):
        db.insert_attempt(conn, attempt_row())
        db.insert_finding(conn, "R1", "A1", FINDING, layer="pack", seed_id=None)
    row = conn.execute("SELECT * FROM findings").fetchone()
    assert json.loads(row["finding_json"]) == FINDING
    assert json.loads(row["receipts_json"]) == ["r-1", "r-2"]
    assert (
        row["evidence_kind"] == "unsupported_by_source" and row["layer"] == "pack" and row["sub_dimension"] == "calque"
    )
    assert row["could_be_a_gate"] == FINDING["could_be_a_gate"]
    conflict = {
        **{k: v for k, v in FINDING.items() if k != "unsupported_by_source"},
        "id": "F-02",
        "source_conflict": {"a": {"receipt": "x"}, "b": {"receipt": "y"}},
    }
    assert db.cited_receipts(conflict) == ["x", "y"]
    assert db.cited_receipts({"id": "F-3", "evidence": {"receipt": "z"}}) == ["z"]
    with pytest.raises(db.FindingsDbError):
        db.evidence_kind({"id": "F-4"})


def test_an_attempt_and_its_finding_are_unique_and_a_finding_needs_its_attempt(conn: sqlite3.Connection) -> None:
    with db.transaction(conn):
        db.insert_attempt(conn, attempt_row())
    with pytest.raises(sqlite3.IntegrityError), db.transaction(conn):
        db.insert_attempt(conn, attempt_row())
    with pytest.raises(sqlite3.IntegrityError), db.transaction(conn):
        db.insert_finding(conn, "R9", "A9", FINDING, layer=None, seed_id=None)  # no such attempt
    with pytest.raises(sqlite3.IntegrityError), db.transaction(conn):
        db.insert_attempt(conn, attempt_row(attempt_id="A2", verdict="MAYBE"))


def test_a_failed_transaction_leaves_nothing(conn: sqlite3.Connection) -> None:
    with pytest.raises(RuntimeError), db.transaction(conn):
        db.insert_attempt(conn, attempt_row())
        raise RuntimeError("boom")
    assert conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0


def test_counters_are_keyed_by_level_slug_and_lesson(conn: sqlite3.Connection) -> None:
    with db.transaction(conn):
        assert db.bump_budget(conn, "a1", "m", 2, "revise_rounds") == 1
        assert db.bump_budget(conn, "a1", "m", 2, "revise_rounds") == 2
        db.bump_budget(conn, "a1", "m", 2, "regenerations")
        db.bump_budget(conn, "a1", "m", 3, "review_failures")
        db.bump_budget(conn, "a1", "other", 2, "revise_rounds")
    budgets = db.module_budgets(conn, "a1", "m")
    assert budgets[2] == {"revise_rounds": 2, "regenerations": 1, "review_failures": 0, "disputed": None}
    assert budgets[3]["review_failures"] == 1 and set(budgets) == {2, 3}
    with pytest.raises(db.FindingsDbError):
        db.bump_budget(conn, "a1", "m", 2, "x; DROP TABLE budgets")


def open_item(conn: sqlite3.Connection, ref: str = "R1/A1/F-01", kind: str = "unsupported_by_source") -> int:
    with db.transaction(conn):
        return db.open_settle_item(
            conn, ref=ref, kind=kind, level="a1", slug="m", lesson_n=2, manifest_sha256="ab" * 32, opened_at="t0"
        )


def test_a_finding_opens_exactly_one_item_of_a_kind(conn: sqlite3.Connection) -> None:
    first = open_item(conn)
    assert open_item(conn) == first
    assert open_item(conn, kind="second_seat_disagreement") != first  # another kind of item on the same finding
    [item] = [row for row in db.module_settle_items(conn, "a1", "m") if row["kind"] == "unsupported_by_source"]
    assert db.is_open(item) and not db.is_waiting_for_operator(item)


def test_an_item_takes_exactly_one_outcome(conn: sqlite3.Connection) -> None:
    item = open_item(conn)
    db.record_settle_outcome(conn, item, "refuted", ["r-3"], "settle-seat", decided_at="t1")
    row = db.module_settle_items(conn, "a1", "m")[0]
    assert (
        row["outcome"] == "refuted"
        and json.loads(row["receipts_json"]) == ["r-3"]
        and row["decided_by"] == "settle-seat"
    )
    assert not db.is_open(row) and not db.is_waiting_for_operator(row)
    with pytest.raises(db.SettleAlreadyDecided):
        db.record_settle_outcome(conn, item, "supported_defect", [], "settle-seat")
    assert db.module_settle_items(conn, "a1", "m")[0]["outcome"] == "refuted"
    with pytest.raises(db.FindingsDbError, match="no settle item"):
        db.record_settle_outcome(conn, 999, "refuted", [], "x")
    with pytest.raises(db.FindingsDbError, match="unknown settle outcome"):
        db.record_settle_outcome(conn, open_item(conn, "R1/A1/F-02"), "maybe", [], "x")


@pytest.mark.parametrize("outcome", ["source_conflict", "unresolved"])
def test_conflict_and_unresolved_go_to_the_operator_until_decided(conn: sqlite3.Connection, outcome: str) -> None:
    item = open_item(conn)
    db.record_settle_outcome(conn, item, outcome, ["r-1"], "settle-seat")
    row = db.module_settle_items(conn, "a1", "m")[0]
    assert db.is_waiting_for_operator(row)
    db.record_operator_decision(conn, item, "keep the construction")
    row = db.module_settle_items(conn, "a1", "m")[0]
    assert not db.is_waiting_for_operator(row) and row["operator_decision"] == "keep the construction"
    with pytest.raises(db.FindingsDbError, match="not waiting"):
        db.record_operator_decision(conn, item, "again")


def test_the_operator_cannot_decide_an_item_the_seat_has_not_sent(conn: sqlite3.Connection) -> None:
    item = open_item(conn)
    with pytest.raises(db.FindingsDbError):
        db.record_operator_decision(conn, item, "x")
    db.record_settle_outcome(conn, item, "refuted", [], "settle-seat")
    with pytest.raises(db.FindingsDbError):
        db.record_operator_decision(conn, item, "x")


def test_the_real_parameters_file_carries_a_decision_date_beside_every_parameter() -> None:
    document = yaml.safe_load(db.PARAMETERS_PATH.read_text(encoding="utf-8"))
    names = [key for key in document if key != "parameters_schema"]
    assert {
        "second_seat_divisor",
        "max_revise_rounds",
        "regeneration_factor",
        "review_failures_terminal_at",
        "unsupported_claim_lessons_to_operator",
        "settle_call_budget",
        "gate_candidate_pattern",
    } <= set(names)
    for name in names:
        assert set(document[name]) == {"value", "decided", "basis"}, name
        assert len(document[name]["decided"]) == 10 and document[name]["decided"][4] == "-", name
    values = db.load_parameters()
    assert (
        values["second_seat_divisor"] == 10 and values["max_revise_rounds"] == 2 and values["regeneration_factor"] == 2
    )
    assert values["unsupported_claim_lessons_to_operator"] == 3 and values["settle_call_budget"] >= 1
    assert values["gate_candidate_pattern"] == "^yes .+$"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["second_seat_divisor"].pop("decided"),
        lambda d: d["second_seat_divisor"].update(decided="soon"),
        lambda d: d["second_seat_divisor"].update(value=0),
        lambda d: d["second_seat_divisor"].update(value="10"),
        lambda d: d["max_revise_rounds"].update(basis=" "),
        lambda d: d.pop("settle_call_budget"),
        lambda d: d.update(parameters_schema=2),
        lambda d: d["gate_candidate_pattern"].update(value="(unclosed"),
    ],
)
def test_a_parameter_without_a_date_a_basis_or_a_sane_value_is_refused(tmp_path: Path, mutate) -> None:
    document = yaml.safe_load(db.PARAMETERS_PATH.read_text(encoding="utf-8"))
    mutate(document)
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    with pytest.raises(db.FindingsDbError):
        db.load_parameters(path)
