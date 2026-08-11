#!/usr/bin/env python3
"""Build and enforce the one-time Phase 3 live-ingest authorization gate.

The gate does not weaken the complete v4 source policy. It binds the reviewed
policy, copied-database rehearsal, exact live database preimage, and recoverable
Google Drive backup into one single-use cutover authorization. Any source-set,
database, receipt, or byte drift fails before chunk loading or mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import phase3_source_policy_v4 as policy_v4

SCHEMA_VERSION = "phase3_live_ingest_gate_v1"
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_live_ingest_gate_v1.schema.json"
DEFAULT_GATE_PATH = ROOT / "data/projects/open_model_data/admission/phase3_live_ingest_gate_v1.json"
EXPECTED_GATE_SHA256 = "594b2de8ae357b4c33594a8d933d683284f4824c0c833624b20dffe75c6f6a63"
PR6631_MERGE_COMMIT = "c88928cf6deaeb84d7487681885314d7b2bb729c"
EXPECTED_LIVE_DB_SHA256 = "c7068a4e4b9e0e7fac3b4f918857bcd36c2f56e524f81e686d222e7155a78739"
EXPECTED_FOREIGN_KEY_HASH = "9938f7cbab6cca94bfd0a360eec114fdef404a357e02b24161da0f7cf5c6d9bb"
REQUESTED_SOURCES = tuple(sorted(policy_v4.STAGED_IDS))

EXPECTED_INPUT_HASHES = {
    "phase3_reboot_prompt_v3_sha256": "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d",
    "complete_source_policy_v4_sha256": policy_v4.EXPECTED_POLICY_SHA256,
    "copied_database_rehearsal_receipt_sha256": (
        "a50310fbb526bb68ebe93f6046af56778c860c7b7731a46488dd188465215183"
    ),
    "pr6631_drive_backup_receipt_sha256": (
        "8792d76bca226c603ebc45c8315dcf197231c955aace7c2a78768943ce7f177b"
    ),
    "pr6631_drive_provider_verification_sha256": (
        "10aa43b2c2722fc74c05f471363fe99f0f187a3c692d5f0367cd33b0dd5d4129"
    ),
    "pre_ingest_backup_receipt_sha256": (
        "f97faa4273a1079b76e6f47ddaf188a383aa516f91df768d1909c6e38409023a"
    ),
    "pre_ingest_backup_provider_verification_sha256": (
        "4cf978220e05aaaf4b999422db48d1239a35fd2245a17e1f8fc4bb5b293621ef"
    ),
    "compressed_pre_ingest_database_sha256": (
        "c89d8d2898b7aa7470e8f3888245fb0d85fe74c075d27a9483da262ad3147a5f"
    ),
    "independent_cross_family_review_sha256": (
        "e85a5d5a2681362765cdee879dc19bc7299ff329aa001d69f7ae5616bed55137"
    ),
    "pr6631_package_manifest_sha256": (
        "1c818a2a54ac1dbf57f9ab21d4bb114b365d9ef5205499504f59b5a5967046a5"
    ),
}

COUNTS_BEFORE = {
    "textbook_rows": 49568,
    "fts_rows": 49568,
    "section_rows": 35777,
    "source_count": 183,
    "university_rows": 3493,
    "university_source_count": 16,
}
COUNTS_AFTER = {
    "textbook_rows": 50153,
    "fts_rows": 50153,
    "section_rows": 36322,
    "source_count": 187,
    "university_rows": 4078,
    "university_source_count": 20,
}


class LiveIngestGateError(ValueError):
    """The one-time live-ingest gate is incomplete, stale, or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LiveIngestGateError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveIngestGateError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def write_text_atomic(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.is_symlink(), f"refusing symlink output: {path}")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _schema_errors(document: Mapping[str, Any]) -> list[Any]:
    schema = read_json(SCHEMA_PATH)
    return sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )


def _table_counts(value: Mapping[str, Any]) -> dict[str, int]:
    return {
        "textbook_rows": int(value["textbook_rows"]),
        "fts_rows": int(value["fts_rows"]),
        "section_rows": int(value["section_rows"]),
    }


def _validate_rehearsal(receipt: Mapping[str, Any]) -> None:
    require(receipt.get("schema_version") == "incremental-textbook-ingest.v2", "rehearsal schema drift")
    require(receipt.get("status") == "committed", "copied-database rehearsal was not committed")
    require(
        receipt.get("execution_scope") == "copied_database_rehearsal",
        "receipt is not a copied-database rehearsal",
    )
    require(
        receipt.get("university_source_policy_sha256") == policy_v4.EXPECTED_POLICY_SHA256,
        "rehearsal policy binding drift",
    )
    require(
        receipt.get("requested_replace_sources") == list(REQUESTED_SOURCES),
        "rehearsal source denominator drift",
    )
    require(receipt.get("requested_quarantine_sources") == [], "rehearsal unexpectedly quarantined sources")
    require(_table_counts(receipt["before"]) == _table_counts(COUNTS_BEFORE), "rehearsal pre-count drift")
    require(_table_counts(receipt["after_transaction"]) == _table_counts(COUNTS_AFTER), "rehearsal post-count drift")
    require(receipt.get("integrity_check") == "ok", "rehearsal integrity check failed")
    require(receipt.get("foreign_key_failures_unchanged") is True, "rehearsal foreign-key baseline changed")
    require(
        receipt.get("foreign_key_failure_count_before") == 134836
        and receipt.get("foreign_key_failure_count_after") == 134836,
        "rehearsal foreign-key count drift",
    )
    require(
        receipt.get("foreign_key_failure_hash_before") == EXPECTED_FOREIGN_KEY_HASH
        and receipt.get("foreign_key_failure_hash_after") == EXPECTED_FOREIGN_KEY_HASH,
        "rehearsal foreign-key hash drift",
    )
    per_source = {entry["source_file"]: entry for entry in receipt.get("per_source", [])}
    require(set(per_source) == set(REQUESTED_SOURCES), "rehearsal per-source set drift")
    for source_id in REQUESTED_SOURCES:
        entry = per_source[source_id]
        expected_rows = policy_v4.STAGED_EXPECTED_ROWS[source_id]
        require(entry.get("inserted_rows") == expected_rows, f"{source_id}: rehearsal row-count drift")
        require(entry.get("linked_rows") == expected_rows, f"{source_id}: rehearsal linkage drift")
        require(entry.get("fts", {}).get("parity") is True, f"{source_id}: rehearsal FTS parity failed")


def _validate_pr_backup(receipt: Mapping[str, Any]) -> None:
    pull_request = receipt.get("pull_request", {})
    require(pull_request.get("number") == 6631, "PR backup receipt number drift")
    require(pull_request.get("merge_commit") == PR6631_MERGE_COMMIT, "PR backup merge binding drift")
    require(pull_request.get("review_verdict") == "APPROVED", "PR backup lacks approved review")
    require(receipt.get("outcome") == "merged_and_incrementally_backed_up", "PR backup is incomplete")
    require(receipt.get("live_ingest_authorized") is False, "PR backup unexpectedly authorized live ingest")
    evidence = receipt.get("exact_evidence", {})
    require(
        evidence.get("complete_source_policy_v4_sha256") == policy_v4.EXPECTED_POLICY_SHA256,
        "PR backup policy binding drift",
    )
    require(
        evidence.get("copied_database_rehearsal_receipt_sha256")
        == EXPECTED_INPUT_HASHES["copied_database_rehearsal_receipt_sha256"],
        "PR backup rehearsal binding drift",
    )
    require(receipt.get("phase3_certified") is False and receipt.get("phase4_blocked") is True, "phase drift")


def _validate_pr_provider_verification(receipt: Mapping[str, Any]) -> None:
    require(receipt.get("pull_request") == 6631, "provider receipt PR drift")
    require(receipt.get("merge_commit") == PR6631_MERGE_COMMIT, "provider receipt merge drift")
    require(receipt.get("status") == "provider_uploaded_and_verified", "provider upload is unverified")
    require(receipt.get("provider_uploaded_count") == receipt.get("verified_file_count"), "provider upload gap")
    require(receipt.get("provider_uploading_count") == 0, "provider upload is still active")
    require(receipt.get("drive_item_id_count") == receipt.get("verified_file_count"), "Drive item ID gap")
    require(receipt.get("readback_sha256_verified") is True, "provider read-back hash was not verified")


def _validate_pre_ingest_backup(
    backup_receipt: Mapping[str, Any], provider_receipt: Mapping[str, Any]
) -> None:
    artifact = backup_receipt.get("artifacts", {}).get("sources-c7068a4e4b9e.db.gz", {})
    require(artifact.get("sha256") == EXPECTED_INPUT_HASHES["compressed_pre_ingest_database_sha256"], "backup gzip drift")
    require(artifact.get("restored_database_sha256") == EXPECTED_LIVE_DB_SHA256, "backup restore hash drift")
    require(
        artifact.get("integrity") == "gzip_passed_and_restored_hash_matched",
        "backup gzip or restored hash was not verified",
    )
    require(provider_receipt.get("status") == "preimage_recoverable_and_provider_uploaded", "preimage backup unverified")
    live = provider_receipt.get("live_database", {})
    require(live.get("sha256") == EXPECTED_LIVE_DB_SHA256, "pre-backup live database identity drift")
    require(
        {key: live.get(key) for key in COUNTS_BEFORE} == COUNTS_BEFORE,
        "pre-backup database count drift",
    )
    drive = provider_receipt.get("google_drive", {})
    require(drive.get("compressed_database_sha256") == artifact.get("sha256"), "provider gzip binding drift")
    require(drive.get("restored_database_sha256") == EXPECTED_LIVE_DB_SHA256, "provider restore binding drift")
    require(drive.get("gzip_test_passed") is True, "pre-ingest gzip test failed")
    require(drive.get("provider_uploaded") is True, "pre-ingest backup is not uploaded")
    require(drive.get("provider_uploading") is False, "pre-ingest backup is still uploading")
    require(drive.get("drive_item_id_present") is True, "pre-ingest backup lacks a Drive item ID")
    require(
        drive.get("backup_receipt_sha256") == EXPECTED_INPUT_HASHES["pre_ingest_backup_receipt_sha256"],
        "provider backup-receipt binding drift",
    )


def validate_bound_inputs(paths: Mapping[str, Path]) -> None:
    require(set(paths) == set(EXPECTED_INPUT_HASHES), "bound input path set is incomplete")
    for key, expected_sha256 in EXPECTED_INPUT_HASHES.items():
        path = Path(paths[key])
        require(path.is_file(), f"missing bound input artifact: {key}")
        require(sha256_file(path) == expected_sha256, f"bound input artifact drift: {key}")


def build_gate(
    *,
    source_policy: Mapping[str, Any],
    rehearsal_receipt: Mapping[str, Any],
    pr_backup_receipt: Mapping[str, Any],
    pr_provider_receipt: Mapping[str, Any],
    pre_ingest_backup_receipt: Mapping[str, Any],
    pre_ingest_provider_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the deterministic one-time authorization from exact evidence."""
    policy_v4.validate_policy_document(source_policy)
    require(source_policy["database_ingest"]["live_ingest_authorized"] is False, "v4 policy boundary drift")
    _validate_rehearsal(rehearsal_receipt)
    _validate_pr_backup(pr_backup_receipt)
    _validate_pr_provider_verification(pr_provider_receipt)
    _validate_pre_ingest_backup(pre_ingest_backup_receipt, pre_ingest_provider_receipt)

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "status": "AUTHORIZED_ONCE_FOR_EXACT_PREIMAGE",
        "bindings": {**EXPECTED_INPUT_HASHES, "pr6631_merge_commit": PR6631_MERGE_COMMIT},
        "requested_sources": list(REQUESTED_SOURCES),
        "database": {
            "target_locator": "primary_checkout:data/sources.db",
            "sha256_before": EXPECTED_LIVE_DB_SHA256,
            "counts_before": COUNTS_BEFORE,
            "counts_after_expected": COUNTS_AFTER,
            "foreign_key_failure_count": 134836,
            "foreign_key_failure_hash": EXPECTED_FOREIGN_KEY_HASH,
            "integrity_check": "ok",
            "journal_mode": "wal",
            "requested_sources_absent_before": True,
        },
        "copied_database_rehearsal": {
            "execution_scope": "copied_database_rehearsal",
            "status": "committed",
            "database_sha256_before": rehearsal_receipt["db_sha256_before"],
            "database_sha256_after": rehearsal_receipt["db_sha256_after"],
            "counts_before": _table_counts(rehearsal_receipt["before"]),
            "counts_after": _table_counts(rehearsal_receipt["after_transaction"]),
            "inserted_rows": sum(policy_v4.STAGED_EXPECTED_ROWS.values()),
            "source_count": len(REQUESTED_SOURCES),
            "integrity_check": rehearsal_receipt["integrity_check"],
            "foreign_key_failures_unchanged": rehearsal_receipt["foreign_key_failures_unchanged"],
            "per_source_fts_and_linkage_passed": True,
        },
        "pre_ingest_backup": {
            "google_drive_relative_path": (
                "Projects/learn-ukrainian-data/backups/phase3-6375/20260811T090325Z"
            ),
            "compressed_database_filename": "sources-c7068a4e4b9e.db.gz",
            "compressed_database_sha256": EXPECTED_INPUT_HASHES["compressed_pre_ingest_database_sha256"],
            "restored_database_sha256": EXPECTED_LIVE_DB_SHA256,
            "gzip_test_passed": True,
            "provider_uploaded": True,
            "provider_uploading": False,
            "drive_item_id_present": True,
        },
        "execution": {
            "live_ingest_authorized": True,
            "single_use": True,
            "exact_preimage_required": True,
            "exact_source_set_required": True,
            "receipt_required": True,
            "post_ingest_backup_required": True,
            "provider_work_authorized": False,
        },
        "source_freeze_ready": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }
    gate = {
        **body,
        "receipt_sha256": hashlib.sha256((canonical_json(body) + "\n").encode("utf-8")).hexdigest(),
    }
    validate_gate_document(gate)
    return gate


def validate_gate_document(gate: Mapping[str, Any]) -> dict[str, Any]:
    """Validate schema and the non-reusable live-cutover invariants."""
    errors = _schema_errors(gate)
    require(not errors, f"live ingest gate schema violation: {errors[0].message if errors else ''}")
    body = {key: value for key, value in gate.items() if key != "receipt_sha256"}
    receipt_sha256 = hashlib.sha256((canonical_json(body) + "\n").encode("utf-8")).hexdigest()
    require(gate["receipt_sha256"] == receipt_sha256, "live ingest gate receipt hash drift")
    require(
        gate["bindings"] == {**EXPECTED_INPUT_HASHES, "pr6631_merge_commit": PR6631_MERGE_COMMIT},
        "live ingest gate bindings drift",
    )
    require(tuple(gate["requested_sources"]) == REQUESTED_SOURCES, "live ingest source set drift")
    require(gate["database"]["counts_before"] == COUNTS_BEFORE, "live database pre-count drift")
    require(gate["database"]["counts_after_expected"] == COUNTS_AFTER, "live database post-count drift")
    require(
        gate["database"]["foreign_key_failure_hash"] == EXPECTED_FOREIGN_KEY_HASH,
        "live database foreign-key hash drift",
    )
    execution = gate["execution"]
    require(
        execution["live_ingest_authorized"] is True
        and execution["single_use"] is True
        and execution["exact_preimage_required"] is True
        and execution["post_ingest_backup_required"] is True,
        "live ingest execution boundary drift",
    )
    require(execution["provider_work_authorized"] is False, "gate unexpectedly authorizes provider work")
    require(gate["source_freeze_ready"] is False and gate["phase3_complete"] is False, "phase completion drift")
    require(gate["phase4_blocked"] is True, "Phase 4 boundary drift")
    return dict(gate)


def load_gate(path: Path = DEFAULT_GATE_PATH) -> tuple[dict[str, Any], str]:
    require(Path(path).is_file(), f"live ingest gate is missing: {path}")
    gate_sha256 = sha256_file(path)
    require(gate_sha256 == EXPECTED_GATE_SHA256, "live ingest gate byte drift")
    return validate_gate_document(read_json(path)), gate_sha256


def _foreign_key_evidence(conn: sqlite3.Connection) -> tuple[int, str]:
    failures = sorted(tuple(row) for row in conn.execute("PRAGMA foreign_key_check").fetchall())
    digest = hashlib.sha256(
        json.dumps(failures, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return len(failures), digest


def _database_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "textbook_rows": conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0],
        "fts_rows": conn.execute("SELECT COUNT(*) FROM textbooks_fts").fetchone()[0],
        "section_rows": conn.execute("SELECT COUNT(*) FROM textbook_sections").fetchone()[0],
        "source_count": conn.execute("SELECT COUNT(DISTINCT source_file) FROM textbooks").fetchone()[0],
        "university_rows": conn.execute("SELECT COUNT(*) FROM textbooks WHERE grade='university'").fetchone()[0],
        "university_source_count": conn.execute(
            "SELECT COUNT(DISTINCT source_file) FROM textbooks WHERE grade='university'"
        ).fetchone()[0],
    }


def validate_database_preimage(
    gate: Mapping[str, Any],
    *,
    db_path: Path,
    expected_live_db_path: Path,
) -> None:
    """Prove the exact live database preimage and single-use absence state."""
    db_path = Path(db_path)
    expected_live_db_path = Path(expected_live_db_path)
    require(db_path.is_file(), "live ingest database target does not exist")
    require(not db_path.is_symlink(), "live ingest refuses a symlink database target")
    require(
        db_path.resolve() == expected_live_db_path.resolve(),
        "live ingest gate is restricted to the primary checkout sources database",
    )
    require(
        os.path.samefile(db_path, expected_live_db_path),
        "live ingest target is not the primary checkout database inode",
    )
    database_gate = gate["database"]
    require(sha256_file(db_path) == database_gate["sha256_before"], "live database preimage SHA-256 drift")

    uri = f"file:{db_path.resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30.0)
    try:
        journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        require(journal_mode == database_gate["journal_mode"], "live database journal-mode drift")
        require(_database_counts(conn) == database_gate["counts_before"], "live database count preimage drift")
        placeholders = ",".join("?" for _ in REQUESTED_SOURCES)
        staged_rows = conn.execute(
            f"SELECT COUNT(*) FROM textbooks WHERE source_file IN ({placeholders})",
            REQUESTED_SOURCES,
        ).fetchone()[0]
        require(staged_rows == 0, "single-use gate is stale: requested sources are already present")
        integrity_rows = [str(row[0]) for row in conn.execute("PRAGMA integrity_check").fetchall()]
        require(integrity_rows == [database_gate["integrity_check"]], "live database integrity check failed")
        failure_count, failure_hash = _foreign_key_evidence(conn)
        require(
            failure_count == database_gate["foreign_key_failure_count"],
            "live database foreign-key count drift",
        )
        require(failure_hash == database_gate["foreign_key_failure_hash"], "live database foreign-key hash drift")
    finally:
        conn.close()


def validate_live_ingest_preconditions(
    *,
    gate_path: Path,
    db_path: Path,
    expected_live_db_path: Path,
    source_ids: Sequence[str],
    quarantine_source_ids: Sequence[str],
    source_policy_sha256: str,
    dry_run: bool,
    copied_database_rehearsal: bool,
    receipt_path: Path | None,
) -> str:
    """Fail closed before any chunk read or live mutation."""
    gate, gate_sha256 = load_gate(gate_path)
    require(not dry_run, "live ingest gate authorizes an exact committed cutover, not a dry-run")
    require(not copied_database_rehearsal, "live ingest gate cannot be combined with copied-database rehearsal")
    require(receipt_path is not None, "live ingest gate requires an explicit receipt path")
    require(tuple(sorted(source_ids)) == REQUESTED_SOURCES, "live ingest gate requires the exact four-source set")
    require(not quarantine_source_ids, "live ingest gate does not authorize quarantine mutations")
    require(
        source_policy_sha256 == gate["bindings"]["complete_source_policy_v4_sha256"],
        "live ingest gate source-policy binding drift",
    )
    validate_database_preimage(gate, db_path=db_path, expected_live_db_path=expected_live_db_path)
    return gate_sha256


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase3-reboot-prompt-v3", type=Path, required=True)
    parser.add_argument("--complete-source-policy-v4", type=Path, required=True)
    parser.add_argument("--copied-database-rehearsal-receipt", type=Path, required=True)
    parser.add_argument("--pr6631-drive-backup-receipt", type=Path, required=True)
    parser.add_argument("--pr6631-drive-provider-verification", type=Path, required=True)
    parser.add_argument("--pre-ingest-backup-receipt", type=Path, required=True)
    parser.add_argument("--pre-ingest-backup-provider-verification", type=Path, required=True)
    parser.add_argument("--compressed-pre-ingest-database", type=Path, required=True)
    parser.add_argument("--independent-cross-family-review", type=Path, required=True)
    parser.add_argument("--pr6631-package-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    paths = {
        "phase3_reboot_prompt_v3_sha256": args.phase3_reboot_prompt_v3,
        "complete_source_policy_v4_sha256": args.complete_source_policy_v4,
        "copied_database_rehearsal_receipt_sha256": args.copied_database_rehearsal_receipt,
        "pr6631_drive_backup_receipt_sha256": args.pr6631_drive_backup_receipt,
        "pr6631_drive_provider_verification_sha256": args.pr6631_drive_provider_verification,
        "pre_ingest_backup_receipt_sha256": args.pre_ingest_backup_receipt,
        "pre_ingest_backup_provider_verification_sha256": args.pre_ingest_backup_provider_verification,
        "compressed_pre_ingest_database_sha256": args.compressed_pre_ingest_database,
        "independent_cross_family_review_sha256": args.independent_cross_family_review,
        "pr6631_package_manifest_sha256": args.pr6631_package_manifest,
    }
    validate_bound_inputs(paths)
    gate = build_gate(
        source_policy=read_json(args.complete_source_policy_v4),
        rehearsal_receipt=read_json(args.copied_database_rehearsal_receipt),
        pr_backup_receipt=read_json(args.pr6631_drive_backup_receipt),
        pr_provider_receipt=read_json(args.pr6631_drive_provider_verification),
        pre_ingest_backup_receipt=read_json(args.pre_ingest_backup_receipt),
        pre_ingest_provider_receipt=read_json(args.pre_ingest_backup_provider_verification),
    )
    encoded = json.dumps(gate, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(encoded, end="")
    else:
        write_text_atomic(args.output, encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
