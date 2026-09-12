"""Hermetic tests for VESUM database activation and rollback (scripts/rag/activate_vesum_db.py)."""

from __future__ import annotations

import bz2
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.rag.activate_vesum_db import (
    ActivationError,
    activate_database,
    rollback_database,
    verify_shadow_database,
)
from scripts.rag.vesum_reingest import build_shadow_database
from scripts.verification.vesum import inspect_word, verify_word

SYNTHETIC_ACTIVATION_BLOCKS = """\
книга noun:inanim:f:v_naz
  книги noun:inanim:f:v_rod
Єгіпет noun:inanim:m:v_naz:bad
"""


@pytest.fixture
def synthetic_lock_and_shadow(tmp_path: Path) -> tuple[dict[str, object], Path]:
    asset_path = tmp_path / "synthetic_act.txt.bz2"
    with bz2.open(asset_path, "wt", encoding="utf-8") as target:
        target.write(SYNTHETIC_ACTIVATION_BLOCKS)

    shadow_path = tmp_path / "shadow.db"
    summary = build_shadow_database(asset_path, shadow_path)

    lock = {
        "release_asset": {
            "version": "test-v1",
            "url": "https://github.com/brown-uk/dict_uk/releases/download/test-v1/dict_corp_vis.txt.bz2",
            "sha256": "0" * 64,
            "size_bytes": 100,
        },
        "expected": summary.as_lock_expected(),
    }
    return lock, shadow_path


def test_verify_shadow_database_succeeds(
    synthetic_lock_and_shadow: tuple[dict[str, object], Path],
) -> None:
    lock, shadow_path = synthetic_lock_and_shadow
    summary = verify_shadow_database(shadow_path, lock)
    assert summary["forms_all_count"] == 3
    assert summary["forms_compatibility_count"] == 2
    assert summary["canonical_jsonl_sha256"] == lock["expected"]["canonical_jsonl_sha256"]


def test_verify_shadow_database_detects_hash_mismatch(
    synthetic_lock_and_shadow: tuple[dict[str, object], Path],
) -> None:
    lock, shadow_path = synthetic_lock_and_shadow
    bad_lock = dict(lock)
    bad_lock["expected"] = dict(lock["expected"])
    bad_lock["expected"]["canonical_jsonl_sha256"] = "0" * 64

    with pytest.raises(ActivationError, match="Metadata canonical JSONL SHA-256 mismatch"):
        verify_shadow_database(shadow_path, bad_lock)


def test_verify_shadow_database_detects_tampered_contents(
    synthetic_lock_and_shadow: tuple[dict[str, object], Path],
) -> None:
    lock, shadow_path = synthetic_lock_and_shadow
    # Tamper with row contents in shadow database without updating vesum_build_metadata
    conn = sqlite3.connect(shadow_path)
    conn.execute("UPDATE forms_all SET lemma = 'зміна' WHERE word_form = 'книга'")
    conn.commit()
    conn.close()

    with pytest.raises(ActivationError, match="Computed canonical JSONL SHA-256 mismatch"):
        verify_shadow_database(shadow_path, lock)


def test_verify_shadow_database_detects_missing_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE dummy (id INT)")
    conn.commit()
    conn.close()

    with pytest.raises(ActivationError, match="missing schema elements"):
        verify_shadow_database(db_path, {"expected": {}})


def test_activate_and_rollback_lifecycle(
    tmp_path: Path,
    synthetic_lock_and_shadow: tuple[dict[str, object], Path],
) -> None:
    lock, shadow_path = synthetic_lock_and_shadow
    lock_file = tmp_path / "lock.json"
    lock_file.write_text(json.dumps(lock), encoding="utf-8")

    # Create an initial legacy target DB
    target_path = tmp_path / "production.db"
    conn = sqlite3.connect(target_path)
    conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
    conn.execute("INSERT INTO forms VALUES ('старе', 'старе', 'adj:n:v_naz', 'adj')")
    conn.commit()
    conn.close()

    assert verify_word("старе", db_path=target_path) != []

    # 1. Activate shadow DB
    receipt = activate_database(shadow_path, target_path=target_path, lock_path=lock_file)
    assert receipt["status"] == "ACTIVATED"
    assert receipt["backup_path"] is not None
    backup_path = Path(receipt["backup_path"])
    assert backup_path.is_file()

    # Now target_path has the new schema
    res = inspect_word("книга", db_path=target_path)
    assert res.status.value == "CLEAN"
    assert len(res.clean_analyses) == 1
    assert verify_word("Єгіпет", db_path=target_path) == []

    # 2. Rollback
    rollback_receipt = rollback_database(backup_path, target_path=target_path)
    assert rollback_receipt["status"] == "ROLLED_BACK"

    # Now target_path is restored to legacy
    assert verify_word("старе", db_path=target_path) != []
    # And inspect fails closed with UNAVAILABLE
    res_rolled = inspect_word("книга", db_path=target_path)
    assert res_rolled.status.value == "UNAVAILABLE"
