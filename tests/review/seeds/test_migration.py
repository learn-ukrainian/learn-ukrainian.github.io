"""The findings database migration (version 2 to 3) and the typed review parameters (#8430 R3-A)."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.review import findings_db as db

OLD_TABLES = ("attempts", "findings", "budgets", "settle_items", "agreement")
NEW_TABLES = ("seed_results", "clean_results", "seed_identities")

ATTEMPT = {
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
FINDING = {
    "id": "F-01",
    "status": "active",
    "locations": [{"tab": "urok", "quote": "q"}],
    "dimension": "job",
    "severity": "MAJOR",
    "claim": "A claim.",
    "evidence": {"receipt": "r-1"},
}


def make_v2(path: Path) -> None:
    """A database exactly as R2b-A wrote it: the five tables, schema_version 2, rows in every one of them."""
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    for statement in db._TABLES.split(";"):  # the R2b-A schema is exactly what _TABLES still holds
        if statement.strip():
            conn.execute(statement)
    conn.execute("INSERT INTO schema_version (version) VALUES (2)")
    marks = ", ".join("?" for _ in ATTEMPT)
    conn.execute(f"INSERT INTO attempts ({', '.join(ATTEMPT)}) VALUES ({marks})", tuple(ATTEMPT.values()))
    conn.execute(
        "INSERT INTO attempts (review_id, attempt_id, kind, level, slug, lesson_n, manifest_sha256, reviewer_model,"
        " reviewer_family, harness, verdict, validated_at, task_id, role, seed_id)"
        " VALUES ('R2', 'A2', 'lesson', 'a1', 'm', 3, ?, 'gpt-6-astra', 'openai', 'codex', 'APPROVE', 'now', 't-2',"
        " 'first', 'seed-old')",
        ("ef" * 32,),
    )
    conn.execute(
        "INSERT INTO findings (review_id, attempt_id, finding_id, status, dimension, sub_dimension, severity, claim,"
        " evidence_kind, receipts_json, locations_json, could_be_a_gate, layer, seed_id, finding_json)"
        " VALUES ('R1', 'A1', 'F-01', 'active', 'job', NULL, 'MAJOR', 'A claim.', 'evidence', '[\"r-1\"]', '[]', NULL,"
        " NULL, NULL, '{}')"
    )
    conn.execute("INSERT INTO budgets (level, slug, lesson_n, revise_rounds) VALUES ('a1', 'm', 2, 1)")
    conn.execute(
        "INSERT INTO settle_items (finding_ref, kind, level, slug, lesson_n, manifest_sha256, opened_at)"
        " VALUES ('R1/A1/F-01', 'unsupported_by_source', 'a1', 'm', 2, 'x', 'now')"
    )
    conn.execute(
        "INSERT INTO agreement (level, slug, lesson_n, attempt_a, attempt_b, agreed, disagreed_json)"
        " VALUES ('a1', 'm', 2, 'A1', 'A2', 1, '[]')"
    )
    conn.close()


def dump(path: Path, tables: tuple[str, ...] = OLD_TABLES) -> dict[str, list[tuple]]:
    conn = sqlite3.connect(path)
    try:
        return {name: conn.execute(f"SELECT * FROM {name} ORDER BY rowid").fetchall() for name in tables}
    finally:
        conn.close()


def table_names(path: Path) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    finally:
        conn.close()


def versions(path: Path) -> list[int]:
    conn = sqlite3.connect(path)
    try:
        return [row[0] for row in conn.execute("SELECT version FROM schema_version")]
    finally:
        conn.close()


def test_the_schema_version_is_three_and_a_fresh_database_has_the_measurement_tables(tmp_path: Path) -> None:
    assert db.SCHEMA_VERSION == 3
    conn = db.connect(tmp_path / "fresh.sqlite")
    conn.close()
    assert {*OLD_TABLES, *NEW_TABLES, "schema_version"} <= table_names(tmp_path / "fresh.sqlite")
    assert versions(tmp_path / "fresh.sqlite") == [3]


def test_a_populated_version_two_database_upgrades_to_three_and_keeps_every_row(tmp_path: Path) -> None:
    path = tmp_path / "a1.sqlite"
    make_v2(path)
    before = dump(path)
    assert all(before[name] for name in OLD_TABLES), "the fixture has rows in every existing table"
    assert versions(path) == [2] and not set(NEW_TABLES) & table_names(path)

    conn = db.connect(path)
    conn.close()

    assert versions(path) == [3]
    assert set(NEW_TABLES) <= table_names(path)
    assert dump(path) == before, "every existing row is byte-for-byte what it was"
    assert all(dump(path, NEW_TABLES)[name] == [] for name in NEW_TABLES)


def test_the_upgraded_database_takes_measurement_rows_and_its_foreign_keys_hold(tmp_path: Path) -> None:
    path = tmp_path / "a1.sqlite"
    make_v2(path)
    conn = db.connect(path)
    try:
        with db.transaction(conn):
            db.insert_seed_result(
                conn,
                seed_id="seed-old",
                review_id="R2",
                attempt_id="A2",
                planted_found=True,
                planted_blocking=False,
                mapping=[{"finding_id": "F-01", "class": "planted", "reason": "x"}],
                adjudicator_model="m",
                adjudicator_family="f",
            )
        assert db.get_seed_result(conn, "R2", "A2")["planted_found"] == 1
        with pytest.raises(sqlite3.IntegrityError), db.transaction(conn):  # an unknown attempt is refused
            db.insert_clean_result(
                conn,
                clean_id="clean-x",
                review_id="R9",
                attempt_id="A9",
                false_findings=0,
                falsely_blocked=False,
                mapping=[],
                adjudicator_model="m",
                adjudicator_family="f",
            )
    finally:
        conn.close()


def test_opening_an_upgraded_database_again_changes_nothing(tmp_path: Path) -> None:
    path = tmp_path / "a1.sqlite"
    make_v2(path)
    db.connect(path).close()
    first = dump(path, (*OLD_TABLES, *NEW_TABLES))
    db.connect(path).close()
    assert dump(path, (*OLD_TABLES, *NEW_TABLES)) == first and versions(path) == [3]


def test_a_failing_migration_leaves_the_version_two_database_as_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "a1.sqlite"
    make_v2(path)
    before = dump(path)
    monkeypatch.setattr(db, "_TABLES_V3", db._TABLES_V3 + "; CREATE TABLE broken (")
    with pytest.raises(sqlite3.OperationalError):
        db.connect(path)
    monkeypatch.undo()
    assert versions(path) == [2] and not set(NEW_TABLES) & table_names(path), "one transaction: all or nothing"
    assert dump(path) == before


@pytest.mark.parametrize("version", [0, 1, 4, 99])
def test_a_database_of_an_unknown_version_is_still_refused_and_left_untouched(tmp_path: Path, version: int) -> None:
    path = tmp_path / "a1.sqlite"
    make_v2(path)
    conn = sqlite3.connect(path)
    conn.execute("UPDATE schema_version SET version = ?", (version,))
    conn.commit()
    conn.close()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(db.VersionMismatch):
        db.connect(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_more_than_one_version_row_and_tables_without_a_version_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "two-rows.sqlite"
    make_v2(path)
    conn = sqlite3.connect(path)
    conn.execute("INSERT INTO schema_version (version) VALUES (3)")
    conn.commit()
    conn.close()
    with pytest.raises(db.VersionMismatch):
        db.connect(path)
    bare = tmp_path / "bare.sqlite"
    conn = sqlite3.connect(bare)
    conn.execute("CREATE TABLE attempts (x)")
    conn.commit()
    conn.close()
    with pytest.raises(db.VersionMismatch):
        db.connect(bare)


def test_a_version_two_database_that_already_has_a_measurement_table_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "a1.sqlite"
    make_v2(path)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE seed_results (x)")
    conn.commit()
    conn.close()
    with pytest.raises(db.VersionMismatch, match="seed_results"):
        db.connect(path)
    assert versions(path) == [2]


# --- typed parameters ---------------------------------------------------------------------------


def test_the_existing_integer_parameters_keep_their_names_and_values() -> None:
    values = db.load_parameters()
    assert {name: values[name] for name in db._INT_PARAMETERS[:6]} == {
        "second_seat_divisor": 10,
        "max_revise_rounds": 2,
        "regeneration_factor": 2,
        "review_failures_terminal_at": 3,
        "unsupported_claim_lessons_to_operator": 3,
        "settle_call_budget": 12,
    }
    assert values["gate_candidate_pattern"] == "^yes .+$"
    assert all(type(values[name]) is int for name in db._INT_PARAMETERS)


def test_the_new_parameters_are_typed_and_the_threshold_is_null_by_default() -> None:
    values = db.load_parameters()
    assert (values["min_planted_per_dimension"], values["min_clean_lessons"], values["rolling_one_in"]) == (22, 30, 30)
    assert values["interval_confidence_percent"] == 95
    assert values["interval_method_proportion"] == "wilson"
    assert values["interval_method_rate"] == "poisson_exact"
    assert values["paired_test"] == "mcnemar_exact"
    assert "admission_threshold" in values and values["admission_threshold"] is None


def test_every_parameter_carries_a_decision_date_and_a_basis() -> None:
    document = yaml.safe_load(db.PARAMETERS_PATH.read_text(encoding="utf-8"))
    names = [key for key in document if key != "parameters_schema"]
    assert {"min_planted_per_dimension", "min_clean_lessons", "rolling_one_in", "admission_threshold"} <= set(names)
    for name in names:
        assert set(document[name]) == {"value", "decided", "basis"}, name
        assert len(document[name]["decided"]) == 10 and document[name]["basis"].strip(), name


def _load_with(tmp_path: Path, mutate) -> dict:
    document = yaml.safe_load(db.PARAMETERS_PATH.read_text(encoding="utf-8"))
    mutate(document)
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    return db.load_parameters(path)


def test_the_operator_can_write_the_threshold_as_a_fraction(tmp_path: Path) -> None:
    assert _load_with(tmp_path, lambda d: d["admission_threshold"].update(value=0.8))["admission_threshold"] == 0.8


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["admission_threshold"].update(value=0),
        lambda d: d["admission_threshold"].update(value=1.5),
        lambda d: d["admission_threshold"].update(value="80 %"),
        lambda d: d["admission_threshold"].update(value=True),
        lambda d: d["admission_threshold"].pop("decided"),
        lambda d: d.pop("admission_threshold"),
        lambda d: d["interval_method_proportion"].update(value="clopper_pearson"),
        lambda d: d["interval_method_rate"].update(value="wald"),
        lambda d: d["paired_test"].update(value="chi_squared"),
        lambda d: d["min_planted_per_dimension"].update(value=0),
        lambda d: d["min_clean_lessons"].update(value="30"),
        lambda d: d["rolling_one_in"].update(value=True),
        lambda d: d["interval_confidence_percent"].update(value=100),
        lambda d: d["interval_method_proportion"].update(decided="soon"),
    ],
)
def test_a_badly_typed_parameter_is_refused(tmp_path: Path, mutate) -> None:
    with pytest.raises(db.FindingsDbError):
        _load_with(tmp_path, mutate)
