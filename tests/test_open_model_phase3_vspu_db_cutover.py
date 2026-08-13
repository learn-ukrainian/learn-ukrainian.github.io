"""Hermetic tests for the one-source VSPU database cutover."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_vspu_db_cutover as cutover
from scripts.projects.open_model_data import university_source_policy
from scripts.wiki.extract_sections import ensure_schema

TEXTBOOK_SCHEMA = """
CREATE TABLE textbooks (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT,
    title TEXT,
    text TEXT,
    source_file TEXT,
    subject TEXT,
    grade TEXT,
    author TEXT,
    author_uk TEXT DEFAULT '',
    char_count INTEGER,
    parent_section_id INTEGER REFERENCES textbook_sections(section_id)
);
CREATE VIRTUAL TABLE textbooks_fts USING fts5(
    title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
    INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
"""


def _jsonl_row(page: int) -> dict[str, object]:
    text = f"Навчальний текст сторінки {page}."
    return {
        "schema_version": "phase3-vspu-page-unit.v1",
        "chunk_id": f"{cutover.SOURCE_ID}_p{page:04d}",
        "title": f"Сторінка {page}",
        "section_title": f"Сторінка {page}",
        "text": text,
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "source_file": cutover.SOURCE_ID,
        "source_pdf_sha256": "a" * 64,
        "subject": "ukrmova",
        "grade": "university",
        "author": "Гороф’янюк та ін.",
        "author_uk": "Гороф’янюк І. В. та ін.",
        "page_start": page,
        "page_end": page,
        "extraction_mode": "native_pdf_text",
        "page_extraction_mode": "native_pdf_text",
        "exactness": {
            "normalization_applied": False,
            "ocr_used": False,
            "repairs_applied": False,
        },
    }


def _write_policy(path: Path, jsonl: Path) -> str:
    rows = university_source_policy.load_jsonl_rows(jsonl)
    policy = {
        "schema_version": university_source_policy.V3_SCHEMA_VERSION,
        "status": university_source_policy.STATUS,
        "default_disposition": university_source_policy.V3_DEFAULT_DISPOSITION,
        "source_count": 1,
        "sources": [
            {
                "source_file": cutover.SOURCE_ID,
                "audience_class": "A_ukrainian_university_audience",
                "subject_role": "ukrainian_linguistics",
                "content_disposition": "contextual_only",
                "allowed_lanes": ["contextual_retrieval", "corpus_ingest"],
                "evidence": {
                    "kind": "jsonl_front_matter",
                    "jsonl_sha256": cutover.sha256_file(jsonl),
                    "page_start": 1,
                    "page_end": 2,
                    "rows_sha256": university_source_policy.evidence_rows_sha256(
                        rows,
                        page_start=1,
                        page_end=2,
                    ),
                    "summary": "Fixture native-university front matter.",
                },
            }
        ],
    }
    path.write_text(json.dumps(policy, ensure_ascii=False), encoding="utf-8")
    return cutover.sha256_file(path)


def _create_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
        connection.executescript(TEXTBOOK_SCHEMA)
        ensure_schema(connection)
        connection.execute(
            "INSERT INTO textbooks "
            "(chunk_id,title,text,source_file,subject,grade,author,author_uk,char_count) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                "existing_s0001",
                "Сторінка 1",
                "Наявний корпусний текст.",
                "9-klas-ukrmova-existing-2024",
                "ukrmova",
                "grade-09",
                "Автор",
                "Автор",
                len("Наявний корпусний текст."),
            ),
        )
        cursor = connection.execute(
            "INSERT INTO textbook_sections "
            "(source_file,grade,section_title,section_number,page_start,page_end,chunk_count,full_text) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                "9-klas-ukrmova-existing-2024",
                9,
                "Сторінка 1",
                None,
                1,
                1,
                1,
                "Наявний корпусний текст.",
            ),
        )
        connection.execute(
            "UPDATE textbooks SET parent_section_id=? WHERE chunk_id='existing_s0001'",
            (cursor.lastrowid,),
        )
        connection.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
        connection.commit()
        assert connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone() == (0, 0, 0)


def _fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path, str]:
    database = tmp_path / "sources.db"
    _create_database(database)
    expected_pre_sha256 = cutover.sha256_file(database)

    chunks = tmp_path / "private" / "grade-00"
    chunks.mkdir(parents=True)
    jsonl = chunks / f"{cutover.SOURCE_ID}.jsonl"
    jsonl.write_text(
        "".join(json.dumps(_jsonl_row(page), ensure_ascii=False, separators=(",", ":")) + "\n" for page in (1, 2)),
        encoding="utf-8",
    )
    os.chmod(jsonl, 0o600)
    policy = tmp_path / "policy.json"
    policy_sha256 = _write_policy(policy, jsonl)

    before_counts = {
        "textbook_rows": 1,
        "fts_rows": 1,
        "section_rows": 1,
        "source_count": 1,
        "university_rows": 0,
        "university_source_count": 0,
    }
    after_counts = {
        "textbook_rows": 3,
        "fts_rows": 3,
        "section_rows": 3,
        "source_count": 2,
        "university_rows": 2,
        "university_source_count": 1,
    }
    empty_foreign_hash = hashlib.sha256(b"[]").hexdigest()
    monkeypatch.setattr(cutover, "EXPECTED_SOURCE_ROWS", 2)
    monkeypatch.setattr(cutover, "EXPECTED_PRE_DB_SHA256", expected_pre_sha256)
    monkeypatch.setattr(cutover, "EXPECTED_PRIVATE_JSONL_SHA256", cutover.sha256_file(jsonl))
    monkeypatch.setattr(cutover, "EXPECTED_ADDITIVE_POLICY_SHA256", policy_sha256)
    monkeypatch.setattr(cutover, "EXPECTED_FOREIGN_KEY_COUNT", 0)
    monkeypatch.setattr(cutover, "EXPECTED_FOREIGN_KEY_SHA256", empty_foreign_hash)
    monkeypatch.setattr(cutover, "COUNTS_BEFORE", before_counts)
    monkeypatch.setattr(cutover, "COUNTS_AFTER", after_counts)
    monkeypatch.setattr(
        cutover,
        "_validate_materialization_and_policy",
        lambda **_kwargs: ({}, {}),
    )
    monkeypatch.setattr(cutover, "_validate_preimage_backup", lambda **_kwargs: {})
    monkeypatch.setattr(cutover, "_schema_validator", lambda: Draft202012Validator({}))
    return database, jsonl, policy, expected_pre_sha256


def _reconcile(
    *,
    database: Path,
    jsonl: Path,
    policy: Path,
    output: Path | None = None,
    apply: bool = False,
) -> dict[str, object]:
    return cutover.reconcile(
        database_path=database,
        private_jsonl_path=jsonl,
        preimage_backup_receipt_path=jsonl,
        compressed_preimage_path=jsonl,
        output_receipt_path=output,
        additive_policy_path=policy,
        apply_in_place=apply,
        expected_live_db_path=database,
        require_google_drive_output=False,
    )


def test_tracked_additive_policy_is_exactly_one_contextual_source() -> None:
    policy, policy_sha256 = university_source_policy.load_policy(cutover.ADDITIVE_POLICY_PATH)
    assert policy_sha256 == cutover.EXPECTED_ADDITIVE_POLICY_SHA256
    assert policy["source_count"] == 1
    source = policy["sources"][0]
    assert source["source_file"] == cutover.SOURCE_ID
    assert source["content_disposition"] == "contextual_only"
    assert source["allowed_lanes"] == ["contextual_retrieval", "corpus_ingest"]
    assert "linguistic_rule_evidence" not in source["allowed_lanes"]


def test_cutover_schema_is_valid_and_closes_receipt_shape() -> None:
    schema = json.loads(cutover.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    assert schema["properties"]["phase_boundaries"]["additionalProperties"] is False


def test_dry_run_is_text_free_and_does_not_mutate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, expected = _fixture(tmp_path, monkeypatch)
    result = _reconcile(database=database, jsonl=jsonl, policy=policy)
    assert result["mode"] == "dry_run"
    assert result["text_free"] is True and result["provider_calls"] is False
    assert cutover.sha256_file(database) == expected
    with sqlite3.connect(database) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM textbooks WHERE source_file=?",
                (cutover.SOURCE_ID,),
            ).fetchone()[0]
            == 0
        )


def test_generic_ingest_cannot_bypass_the_dedicated_vspu_cutover(tmp_path: Path) -> None:
    disposable_db = tmp_path / "copy.db"
    disposable_db.touch()

    with pytest.raises(
        cutover.textbook_ingest.IngestError,
        match="requires its dedicated database cutover",
    ):
        cutover.textbook_ingest.ingest(
            [cutover.SOURCE_ID],
            db_path=disposable_db,
            dry_run=False,
            chunks_root=tmp_path / "missing-chunks",
            university_policy_path=cutover.ADDITIVE_POLICY_PATH,
        )


def test_generic_ingest_cannot_delete_vspu_via_direct_quarantine(tmp_path: Path) -> None:
    disposable_db = tmp_path / "copy.db"
    disposable_db.touch()

    with pytest.raises(
        cutover.textbook_ingest.IngestError,
        match="requires its dedicated database cutover",
    ):
        cutover.textbook_ingest.ingest(
            [],
            quarantine_slugs=[cutover.SOURCE_ID],
            db_path=disposable_db,
            dry_run=False,
            chunks_root=tmp_path / "missing-chunks",
            university_policy_path=cutover.ADDITIVE_POLICY_PATH,
        )


def test_vspu_quarantine_is_refused_even_during_copied_rehearsal(tmp_path: Path) -> None:
    disposable_db = tmp_path / "copy.db"
    disposable_db.touch()

    with pytest.raises(
        cutover.textbook_ingest.IngestError,
        match="requires its dedicated database cutover",
    ):
        cutover.textbook_ingest.ingest(
            [],
            quarantine_slugs=[cutover.SOURCE_ID],
            db_path=disposable_db,
            dry_run=False,
            chunks_root=tmp_path / "missing-chunks",
            university_policy_path=cutover.ADDITIVE_POLICY_PATH,
            copied_database_rehearsal=True,
            additional_rehearsal_policy_sha256=(cutover.EXPECTED_ADDITIVE_POLICY_SHA256),
        )


def test_in_place_cutover_rehearses_copy_preserves_inode_and_cleans_temps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, _ = _fixture(tmp_path, monkeypatch)
    output = tmp_path / "cutover-receipt.json"
    inode = database.stat().st_ino
    receipt = _reconcile(
        database=database,
        jsonl=jsonl,
        policy=policy,
        output=output,
        apply=True,
    )
    assert receipt["mode"] == "in_place_sqlite_backup"
    assert receipt["copied_database_rehearsal"]["execution_scope"] == ("copied_database_rehearsal")
    assert receipt["database"]["live_inode_preserved"] is True
    assert database.stat().st_ino == inode
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    with sqlite3.connect(database) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM textbooks WHERE source_file=?",
                (cutover.SOURCE_ID,),
            ).fetchone()[0]
            == 2
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM textbook_sections WHERE source_file=?",
                (cutover.SOURCE_ID,),
            ).fetchone()[0]
            == 2
        )
    assert not list(tmp_path.glob(".sources.db.vspu-*"))


def test_in_place_cutover_waits_for_new_receipt_drive_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, _ = _fixture(tmp_path, monkeypatch)
    output = tmp_path / "cutover-receipt.json"
    observed: list[Path] = []

    def record_identity_wait(path: Path) -> str:
        observed.append(path)
        assert path.is_file()
        return "drive-item-id"

    monkeypatch.setattr(cutover, "_wait_for_drive_item_id", record_identity_wait)
    cutover.reconcile(
        database_path=database,
        private_jsonl_path=jsonl,
        preimage_backup_receipt_path=jsonl,
        compressed_preimage_path=jsonl,
        output_receipt_path=output,
        additive_policy_path=policy,
        apply_in_place=True,
        expected_live_db_path=database,
        require_google_drive_output=True,
    )

    assert observed == [output]


def test_candidate_ingest_failure_keeps_live_database_and_receipt_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, expected = _fixture(tmp_path, monkeypatch)
    output = tmp_path / "never.json"
    monkeypatch.setattr(
        cutover.textbook_ingest,
        "ingest",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(cutover.textbook_ingest.IngestError("fixture ingest failure")),
    )
    with pytest.raises(cutover.VspuDatabaseCutoverError, match="fixture ingest failure"):
        _reconcile(
            database=database,
            jsonl=jsonl,
            policy=policy,
            output=output,
            apply=True,
        )
    assert cutover.sha256_file(database) == expected
    assert not output.exists()
    assert not list(tmp_path.glob(".sources.db.vspu-*"))


def test_live_postcondition_failure_restores_exact_prestate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, expected = _fixture(tmp_path, monkeypatch)
    original_validate = cutover._validate_post_database
    calls = 0

    def fail_live(after: dict[str, object], before: dict[str, object]) -> None:
        nonlocal calls
        calls += 1
        original_validate(after, before)
        if calls == 2:
            raise cutover.VspuDatabaseCutoverError("fixture live postcondition failure")

    monkeypatch.setattr(cutover, "_validate_post_database", fail_live)
    with pytest.raises(cutover.VspuDatabaseCutoverError, match="live postcondition failure"):
        _reconcile(
            database=database,
            jsonl=jsonl,
            policy=policy,
            output=tmp_path / "never.json",
            apply=True,
        )
    assert cutover.sha256_file(database) == expected
    assert not list(tmp_path.glob(".sources.db.vspu-*"))


def test_receipt_write_failure_restores_exact_prestate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, expected = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        cutover,
        "_atomic_write_private",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("fixture write failure")),
    )
    with pytest.raises(OSError, match="fixture write failure"):
        _reconcile(
            database=database,
            jsonl=jsonl,
            policy=policy,
            output=tmp_path / "never.json",
            apply=True,
        )
    assert cutover.sha256_file(database) == expected
    assert not (tmp_path / "never.json").exists()


def test_restore_failure_retains_private_predecessor_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, expected = _fixture(tmp_path, monkeypatch)
    original_backup = cutover._sqlite_backup
    interrupted = False

    def copy_then_fail(source: Path, target: Path) -> None:
        nonlocal interrupted
        original_backup(source, target)
        if target == database and not interrupted:
            interrupted = True
            raise cutover.VspuDatabaseCutoverError("fixture cutover failure")

    def fail_restore(*_args: object, **_kwargs: object) -> None:
        raise cutover.VspuDatabaseCutoverError("fixture restore failure")

    monkeypatch.setattr(cutover, "_sqlite_backup", copy_then_fail)
    monkeypatch.setattr(cutover, "_restore_exact_prestate", fail_restore)
    with pytest.raises(
        cutover.VspuDatabaseCutoverError,
        match="private predecessor retained",
    ) as caught:
        _reconcile(
            database=database,
            jsonl=jsonl,
            policy=policy,
            output=tmp_path / "never.json",
            apply=True,
        )
    retained = list(tmp_path.glob(".sources.db.vspu-*.candidate"))
    assert len(retained) == 1
    assert str(retained[0]) in str(caught.value)
    assert cutover.sha256_file(retained[0]) == expected
    assert stat.S_IMODE(retained[0].stat().st_mode) == 0o600


def test_preimage_drift_is_rechecked_before_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, _ = _fixture(tmp_path, monkeypatch)
    original_evidence = cutover._database_evidence
    calls = 0

    def mutate_after_initial_evidence(path: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        evidence = original_evidence(path)
        if calls == 1:
            with sqlite3.connect(path) as connection:
                connection.execute("UPDATE textbooks SET text='Змінено.' WHERE chunk_id='existing_s0001'")
                connection.commit()
                assert connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone() == (
                    0,
                    0,
                    0,
                )
        return evidence

    monkeypatch.setattr(cutover, "_database_evidence", mutate_after_initial_evidence)
    with pytest.raises(cutover.VspuDatabaseCutoverError, match="drifted before rehearsal"):
        _reconcile(
            database=database,
            jsonl=jsonl,
            policy=policy,
            output=tmp_path / "never.json",
            apply=True,
        )
    assert not list(tmp_path.glob(".sources.db.vspu-*"))


def test_receipt_rejects_semantic_authority_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, _ = _fixture(tmp_path, monkeypatch)
    receipt = _reconcile(
        database=database,
        jsonl=jsonl,
        policy=policy,
        output=tmp_path / "receipt.json",
        apply=True,
    )
    broken = copy.deepcopy(receipt)
    broken["rights_and_authority"]["semantic_gold"] = True
    broken["receipt_sha256"] = cutover.receipt_sha256(broken)
    with pytest.raises(cutover.VspuDatabaseCutoverError, match="semantic gold"):
        cutover.validate_receipt(broken)


def test_receipt_rejects_legal_reuse_overclaim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, _ = _fixture(tmp_path, monkeypatch)
    receipt = _reconcile(
        database=database,
        jsonl=jsonl,
        policy=policy,
        output=tmp_path / "receipt.json",
        apply=True,
    )
    broken = copy.deepcopy(receipt)
    broken["rights_and_authority"]["legal_reuse_authorization_established"] = True
    broken["receipt_sha256"] = cutover.receipt_sha256(broken)
    with pytest.raises(cutover.VspuDatabaseCutoverError, match="legal reuse authorization"):
        cutover.validate_receipt(broken)


def test_receipt_rejects_legacy_operator_authorization_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, _ = _fixture(tmp_path, monkeypatch)
    receipt = _reconcile(
        database=database,
        jsonl=jsonl,
        policy=policy,
        output=tmp_path / "receipt.json",
        apply=True,
    )
    broken = copy.deepcopy(receipt)
    broken["rights_and_authority"]["private_operator_authorized_use_only"] = True
    broken["receipt_sha256"] = cutover.receipt_sha256(broken)
    with pytest.raises(cutover.VspuDatabaseCutoverError, match="legacy operator authorization field"):
        cutover.validate_receipt(broken)


def test_receipt_rejects_incomplete_database_ingest_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, _ = _fixture(tmp_path, monkeypatch)
    receipt = _reconcile(
        database=database,
        jsonl=jsonl,
        policy=policy,
        output=tmp_path / "receipt.json",
        apply=True,
    )
    broken = copy.deepcopy(receipt)
    broken["phase_boundaries"]["database_ingest_complete"] = False
    broken["receipt_sha256"] = cutover.receipt_sha256(broken)
    with pytest.raises(
        cutover.VspuDatabaseCutoverError,
        match="database_ingest_complete",
    ):
        cutover.validate_receipt(broken)

    real_schema = json.loads(cutover.SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_errors = list(Draft202012Validator(real_schema).iter_errors(broken))
    assert any(
        list(error.absolute_path) == ["phase_boundaries", "database_ingest_complete"] and error.validator == "const"
        for error in schema_errors
    )


def test_private_receipt_is_immutable_and_rejects_symlink(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    cutover._atomic_write_private(receipt, {"ok": True})
    cutover._atomic_write_private(receipt, {"ok": True})
    with pytest.raises(cutover.VspuDatabaseCutoverError, match="immutable"):
        cutover._atomic_write_private(receipt, {"ok": False})
    receipt.unlink()
    target = tmp_path / "target.json"
    target.write_text("target", encoding="utf-8")
    receipt.symlink_to(target)
    with pytest.raises(cutover.VspuDatabaseCutoverError, match="symlink"):
        cutover._atomic_write_private(receipt, {"ok": True})


def test_new_drive_receipt_identity_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    def delayed_identity(_path: Path) -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise cutover.DriveIdentityPendingError("private artifact lacks Google Drive provider identity")
        return "drive-item-id"

    monkeypatch.setattr(cutover, "_drive_item_id", delayed_identity)
    monkeypatch.setattr(cutover.time, "sleep", lambda _seconds: None)

    assert (
        cutover._wait_for_drive_item_id(
            Path("receipt.json"),
            timeout_seconds=1,
            poll_seconds=0,
        )
        == "drive-item-id"
    )
    assert attempts == 3


def test_new_drive_receipt_identity_timeout_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cutover,
        "_drive_item_id",
        lambda _path: (_ for _ in ()).throw(
            cutover.DriveIdentityPendingError("private artifact lacks Google Drive provider identity")
        ),
    )

    with pytest.raises(
        cutover.VspuDatabaseCutoverError,
        match="did not acquire Google Drive provider identity within 0 seconds",
    ):
        cutover._wait_for_drive_item_id(
            Path("receipt.json"),
            timeout_seconds=0,
            poll_seconds=0,
        )


def test_new_drive_receipt_structural_error_is_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def structural_failure(_path: Path) -> str:
        nonlocal attempts
        attempts += 1
        raise cutover.VspuDatabaseCutoverError("private artifact is not inside exactly one Google Drive mount")

    monkeypatch.setattr(cutover, "_drive_item_id", structural_failure)
    monkeypatch.setattr(
        cutover.time,
        "sleep",
        lambda _seconds: pytest.fail("structural errors must not be retried"),
    )

    with pytest.raises(cutover.VspuDatabaseCutoverError, match="not inside exactly one"):
        cutover._wait_for_drive_item_id(
            Path("receipt.json"),
            timeout_seconds=120,
            poll_seconds=1,
        )
    assert attempts == 1


def test_drive_identity_timeout_restores_exact_prestate_and_removes_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, jsonl, policy, expected = _fixture(tmp_path, monkeypatch)
    output = tmp_path / "never.json"
    original_wait = cutover._wait_for_drive_item_id
    monkeypatch.setattr(
        cutover,
        "_drive_item_id",
        lambda _path: (_ for _ in ()).throw(
            cutover.DriveIdentityPendingError("private artifact lacks Google Drive provider identity")
        ),
    )
    monkeypatch.setattr(
        cutover,
        "_wait_for_drive_item_id",
        lambda path: original_wait(path, timeout_seconds=0, poll_seconds=0),
    )

    with pytest.raises(
        cutover.VspuDatabaseCutoverError,
        match="did not acquire Google Drive provider identity within 0 seconds",
    ):
        cutover.reconcile(
            database_path=database,
            private_jsonl_path=jsonl,
            preimage_backup_receipt_path=jsonl,
            compressed_preimage_path=jsonl,
            output_receipt_path=output,
            additive_policy_path=policy,
            apply_in_place=True,
            expected_live_db_path=database,
            require_google_drive_output=True,
        )

    assert cutover.sha256_file(database) == expected
    assert not output.exists()
    assert not list(tmp_path.glob(".sources.db.vspu-*"))
