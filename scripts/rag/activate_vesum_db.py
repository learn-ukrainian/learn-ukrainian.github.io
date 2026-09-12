"""Atomically activate the marker-preserving VESUM database.

This script safely and atomically switches data/vesum.db from the legacy
flat table to the marker-preserving schema (forms_all + form_markers + forms view),
with rigorous pre-activation validation, automatic backup, post-activation
health checks, and rollback support.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.rag.vesum_reingest import (
    DEFAULT_LOCK_PATH,
    PRODUCTION_DB_PATH,
    load_lock,
    sha256_file,
)
from scripts.verification.vesum import (
    InspectionStatus,
    close_vesum_conn,
    inspect_word,
    verify_word,
)

DEFAULT_SHADOW_PATH = PROJECT_ROOT / "data" / "vesum_shadow_v680.db"


class ActivationError(RuntimeError):
    """Raised when database activation or rollback validation fails."""


def verify_shadow_database(
    shadow_path: Path,
    lock: dict[str, Any],
) -> dict[str, Any]:
    """Verify shadow database schema, row counts, metadata, and probes before activation."""
    if not shadow_path.is_file() or shadow_path.stat().st_size == 0:
        raise ActivationError(f"Shadow database not found or empty: {shadow_path}")

    expected = lock.get("expected", {})
    if not isinstance(expected, dict):
        raise ActivationError("Source lock has no expected semantic summary")

    conn = sqlite3.connect(f"file:{shadow_path}?mode=ro", uri=True)
    try:
        # 1. Schema check
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            )
        }
        required_elements = {"forms_all", "form_markers", "forms", "vesum_build_metadata"}
        missing = required_elements - tables
        if missing:
            raise ActivationError(f"Shadow database missing schema elements: {missing}")

        # 2. Foreign keys check
        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise ActivationError(f"Foreign key violations found: {len(fk_errors)}")

        # 3. Metadata check
        metadata = dict(conn.execute("SELECT key, value FROM vesum_build_metadata").fetchall())
        canonical_sha256 = metadata.get("canonical_jsonl_sha256")
        expected_sha256 = expected.get("canonical_jsonl_sha256")
        if canonical_sha256 != expected_sha256:
            raise ActivationError(
                f"Canonical JSONL SHA-256 mismatch: expected {expected_sha256}, got {canonical_sha256}"
            )

        # 4. Row counts check
        forms_all_count = conn.execute("SELECT COUNT(*) FROM forms_all").fetchone()[0]
        if forms_all_count != expected.get("forms_all_count"):
            raise ActivationError(
                f"forms_all count mismatch: expected {expected.get('forms_all_count')}, got {forms_all_count}"
            )

        forms_compat_count = conn.execute("SELECT COUNT(*) FROM forms").fetchone()[0]
        if forms_compat_count != expected.get("forms_compatibility_count"):
            raise ActivationError(
                f"forms compatibility count mismatch: expected {expected.get('forms_compatibility_count')}, got {forms_compat_count}"
            )

    finally:
        conn.close()

    # 5. Semantic probes via verification & inspection API
    clean_probe = inspect_word("книга", db_path=shadow_path)
    if clean_probe.status != InspectionStatus.CLEAN or len(clean_probe.clean_analyses) == 0:
        raise ActivationError(f"Clean probe 'книга' failed: status={clean_probe.status}")

    bad_probe = inspect_word("Єгіпет", db_path=shadow_path)
    if bad_probe.status != InspectionStatus.KNOWN_INVALID or "bad" not in bad_probe.effective_markers:
        raise ActivationError(f"Bad probe 'Єгіпет' failed: status={bad_probe.status}")

    legacy_clean = verify_word("книга", db_path=shadow_path)
    if not legacy_clean:
        raise ActivationError("Legacy verify_word('книга') returned empty on compatibility view")

    legacy_bad = verify_word("Єгіпет", db_path=shadow_path)
    if legacy_bad:
        raise ActivationError("Legacy verify_word('Єгіпет') returned rows for bad-only word")

    return {
        "forms_all_count": forms_all_count,
        "forms_compatibility_count": forms_compat_count,
        "canonical_jsonl_sha256": canonical_sha256,
        "schema_version": metadata.get("schema_version"),
        "marker_policy_version": metadata.get("marker_policy_version"),
    }


def activate_database(
    shadow_path: Path,
    target_path: Path = PRODUCTION_DB_PATH,
    lock_path: Path = DEFAULT_LOCK_PATH,
    *,
    backup: bool = True,
) -> dict[str, Any]:
    """Atomically activate shadow database into target path with pre/post verification."""
    lock = load_lock(lock_path)
    summary = verify_shadow_database(shadow_path, lock)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path: Path | None = None

    if target_path.exists() and backup:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = target_path.with_name(f"{target_path.name}.bak.{timestamp}")
        shutil.copy2(target_path, backup_path)
        # Maintain latest backup symlink/copy pointer
        latest_backup = target_path.with_name(f"{target_path.name}.bak")
        latest_backup.unlink(missing_ok=True)
        try:
            latest_backup.symlink_to(backup_path.name)
        except OSError:
            shutil.copy2(backup_path, latest_backup)

    # Atomic swap: copy to temporary file in the same directory, then rename
    temp_target = target_path.with_name(f".{target_path.name}.activating.{os.getpid()}")
    temp_target.unlink(missing_ok=True)
    try:
        shutil.copy2(shadow_path, temp_target)
        os.replace(temp_target, target_path)
        close_vesum_conn()
    except Exception as exc:
        temp_target.unlink(missing_ok=True)
        raise ActivationError(f"Failed to replace target database: {exc}") from exc

    # Post-activation health verification
    post_clean = inspect_word("книга", db_path=target_path)
    if post_clean.status != InspectionStatus.CLEAN:
        raise ActivationError(f"Post-activation check failed for 'книга': {post_clean.status}")

    post_bad = inspect_word("Єгіпет", db_path=target_path)
    if post_bad.status != InspectionStatus.KNOWN_INVALID:
        raise ActivationError(f"Post-activation check failed for 'Єгіпет': {post_bad.status}")

    target_size = target_path.stat().st_size
    target_sha256 = sha256_file(target_path)

    receipt = {
        "status": "ACTIVATED",
        "timestamp": datetime.now(UTC).isoformat(),
        "target_path": str(target_path),
        "target_size_bytes": target_size,
        "target_sha256": target_sha256,
        "shadow_source": str(shadow_path),
        "backup_path": str(backup_path) if backup_path else None,
        "summary": summary,
        "release_asset": lock.get("release_asset"),
    }
    return receipt


def rollback_database(
    backup_path: Path,
    target_path: Path = PRODUCTION_DB_PATH,
) -> dict[str, Any]:
    """Roll back production database to a specified backup."""
    if not backup_path.is_file() or backup_path.stat().st_size == 0:
        raise ActivationError(f"Backup file not found or empty: {backup_path}")

    # Validate backup can be read
    conn = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
    try:
        conn.execute("SELECT 1 FROM forms LIMIT 1").fetchall()
    except Exception as exc:
        raise ActivationError(f"Backup file is not a valid VESUM SQLite database: {exc}") from exc
    finally:
        conn.close()

    temp_target = target_path.with_name(f".{target_path.name}.rolling_back.{os.getpid()}")
    temp_target.unlink(missing_ok=True)
    try:
        shutil.copy2(backup_path, temp_target)
        os.replace(temp_target, target_path)
        close_vesum_conn()
    except Exception as exc:
        temp_target.unlink(missing_ok=True)
        raise ActivationError(f"Failed to roll back target database: {exc}") from exc

    receipt = {
        "status": "ROLLED_BACK",
        "timestamp": datetime.now(UTC).isoformat(),
        "target_path": str(target_path),
        "restored_from": str(backup_path),
        "target_size_bytes": target_path.stat().st_size,
        "target_sha256": sha256_file(target_path),
    }
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Activate or rollback marker-preserving VESUM database")
    parser.add_argument("--shadow", type=Path, default=DEFAULT_SHADOW_PATH, help="Verified shadow database path")
    parser.add_argument("--target", type=Path, default=PRODUCTION_DB_PATH, help="Target production database path")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK_PATH, help="Source lockfile path")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup of target database")
    parser.add_argument("--rollback", type=Path, help="Roll back target database from specified backup path")
    args = parser.parse_args()

    if args.rollback:
        receipt = rollback_database(args.rollback, target_path=args.target)
    else:
        receipt = activate_database(
            args.shadow,
            target_path=args.target,
            lock_path=args.lock,
            backup=not args.no_backup,
        )

    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
