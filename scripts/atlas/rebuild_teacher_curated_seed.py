"""Create a quarantined, dual-written teacher curated-seed recovery package.

The original curated-table selection is the only authority for the teacher
Practice seed.  This tool deliberately does not infer that selection from
historical inventories, approval ledgers, or cloze cards.  Until that table is
available, it writes an empty package plus source-recon evidence and requires
an independently mirrored Drive copy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SCHEMA = "teacher-curated-seed-recovery-v1"
EXPECTED_ORIGINAL_ROWS = 1018
PACKAGE_FILES = (
    "curated-seed.jsonl",
    "rights-ledger.jsonl",
    "practice-admission.jsonl",
    "source-recon.json",
    "package-manifest.json",
)
PRIVATE_LOCAL = "private_local"
PENDING_REDISTRIBUTION_GO = "pending_operator_redistribution_go"
NO_HIT_REASON = "no_document_hit_vesum_forms"


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"JSONL rows must be objects: {path}")
    return rows


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _source_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.yaml") if path.is_file())


def inventory_counts(source_inventory_root: Path) -> dict[str, int]:
    """Count historical teacher records without emitting their lexical content."""
    files = 0
    records = 0
    lemmas: set[str] = set()
    for path in _source_files(source_inventory_root):
        document = _read_yaml(path)
        if not isinstance(document, Mapping):
            continue
        sources = document.get("sources")
        if not isinstance(sources, list):
            continue
        matching_sources = [
            source
            for source in sources
            if isinstance(source, Mapping) and source.get("source_family") == "teacher_lesson"
        ]
        if not matching_sources:
            continue
        files += 1
        for source in matching_sources:
            headwords = source.get("headwords")
            if not isinstance(headwords, list):
                continue
            for headword in headwords:
                if not isinstance(headword, Mapping):
                    continue
                lemma = str(headword.get("lemma") or "").strip()
                if lemma:
                    records += 1
                    lemmas.add(lemma.casefold())
    return {"files": files, "headword_records": records, "unique_lemmas": len(lemmas)}


def decision_counts(decision_root: Path) -> dict[str, int]:
    """Count teacher-family decisions without treating them as a seed selection."""
    files = 0
    records = 0
    approved = 0
    for path in _source_files(decision_root):
        document = _read_yaml(path)
        if not isinstance(document, Mapping):
            continue
        decisions = document.get("decisions")
        if not isinstance(decisions, list):
            continue
        matching = [
            decision
            for decision in decisions
            if isinstance(decision, Mapping)
            and isinstance(decision.get("source_inventory"), Mapping)
            and decision["source_inventory"].get("source_family") == "teacher_lesson"
        ]
        if not matching:
            continue
        files += 1
        records += len(matching)
        approved += sum(decision.get("decision") == "approve_for_publish" for decision in matching)
    return {"files": files, "decision_records": records, "approved_records": approved}


def cloze_counts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cards = payload.get("cloze") if isinstance(payload, Mapping) else payload
    if not isinstance(cards, list):
        raise ValueError(f"{path}: expected a cloze list")
    lemmas = {
        str(card.get("lemma") or "").strip().casefold()
        for card in cards
        if isinstance(card, Mapping) and str(card.get("lemma") or "").strip()
    }
    return {"cards": len(cards), "unique_lemmas": len(lemmas)}


def drive_counts(path: Path) -> dict[str, object]:
    if not path.is_dir():
        return {"available": False, "files": 0, "suffixes": {}, "candidate_teacher_tables": 0}
    files = sorted(item for item in path.rglob("*") if item.is_file())
    suffixes = Counter(item.suffix.lower() or "[none]" for item in files)
    candidate_tables = sum(
        "teacher" in item.name.casefold() or "curated" in item.name.casefold() for item in files
    )
    return {
        "available": True,
        "files": len(files),
        "suffixes": dict(sorted(suffixes.items())),
        "candidate_teacher_tables": candidate_tables,
    }


def build_source_recon(
    *,
    source_inventory_root: Path,
    decision_root: Path,
    cloze_path: Path,
    drive_source_root: Path,
) -> dict[str, object]:
    """Return safe counts and the explicit missing-table blocker."""
    return {
        "schema": "teacher-curated-source-recon-v1",
        "expected_original_table_rows": EXPECTED_ORIGINAL_ROWS,
        "original_table": {
            "status": "absent",
            "reason": "No authoritative curated table was found; historical sources cannot select its rows.",
        },
        "sources": {
            "drive_curriculum": drive_counts(drive_source_root),
            "cloze_evidence_only": cloze_counts(cloze_path),
            "committed_historical_inventory": inventory_counts(source_inventory_root),
            "committed_historical_decisions": decision_counts(decision_root),
        },
        "admission": "blocked_pending_authoritative_original_table",
    }


def _empty_jsonl(path: Path) -> None:
    path.write_text("", encoding="utf-8")


def _package_manifest(source_recon: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema": PACKAGE_SCHEMA,
        "state": "quarantined_missing_authoritative_table",
        "row_counts": {"curated_seed": 0, "rights_ledger": 0, "practice_admission": 0},
        "files": {
            "curated_seed": {
                "path": "curated-seed.jsonl",
                "required_fields": [
                    "seedRow",
                    "lemma",
                    "gloss",
                    "sentenceStatus",
                    "provenance",
                    "rights",
                    "admission",
                ],
            },
            "rights_ledger": {
                "path": "rights-ledger.jsonl",
                "required_fields": ["seedRow", "sentenceStatus", "rightsStatus", "locator"],
            },
            "practice_admission": {
                "path": "practice-admission.jsonl",
                "required_fields": ["seedRow", "practice", "mode", "reason"],
            },
        },
        "admission_rule": "No rows may be admitted until the authoritative curated table is restored and reviewed.",
        "source_recon_sha256": hashlib.sha256(
            json.dumps(source_recon, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def _package_checksums(root: Path, names: Iterable[str] = PACKAGE_FILES) -> dict[str, str]:
    return {name: _sha256(root / name) for name in names}


def _tree_checksums(root: Path) -> dict[str, str]:
    """Hash every mirrored package file except its self-referential receipt."""
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "receipt.json"
    }


def _has_locator(value: object) -> bool:
    if isinstance(value, Mapping):
        return bool(value)
    return bool(str(value or "").strip())


def classify_rights_admission(sentence_status: str, locator: object) -> tuple[dict[str, object], dict[str, object]]:
    """Return fail-closed row rights and Practice admission for a restored seed row.

    A document hit is not redistribution permission.  The only candidate state
    below remains local-only until an operator explicitly grants redistribution.
    """
    if sentence_status == "no_hit_strict_vesum":
        return (
            {
                "status": PRIVATE_LOCAL,
                "redistributable": False,
                "reason": NO_HIT_REASON,
            },
            {
                "practice": False,
                "mode": "quarantined_no_document_hit",
                "reason": NO_HIT_REASON,
            },
        )
    if sentence_status == "has_candidates":
        if not _has_locator(locator):
            return (
                {
                    "status": "quarantined_missing_document_locator",
                    "redistributable": False,
                    "reason": "has_candidates_without_document_locator",
                },
                {
                    "practice": False,
                    "mode": "quarantined_missing_document_locator",
                    "reason": "has_candidates_without_document_locator",
                },
            )
        return (
            {
                "status": PRIVATE_LOCAL,
                "redistributable": False,
                "reason": "private_local_teacher_material_pending_operator_redistribution_go",
            },
            {
                "practice": False,
                "mode": PENDING_REDISTRIBUTION_GO,
                "reason": "private_local_rights_require_operator_redistribution_go",
            },
        )
    return (
        {
            "status": "quarantined_unreviewed_sentence_status",
            "redistributable": False,
            "reason": f"unsupported_sentence_status_{sentence_status or 'missing'}",
        },
        {
            "practice": False,
            "mode": "quarantined_unreviewed_sentence_status",
            "reason": f"unsupported_sentence_status_{sentence_status or 'missing'}",
        },
    )


def _sync_tree(source: Path, destination: Path) -> None:
    """Copy a staged package file-by-file without relying on cloud dir-renames."""
    for path in sorted(source.rglob("*")):
        if path.is_dir():
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def _restore_tree(backup: Path, destination: Path) -> None:
    """Restore a verified pre-refresh copy after a dual-write failure."""
    backup_files = {path.relative_to(backup) for path in backup.rglob("*") if path.is_file()}
    backup_directories = {path.relative_to(backup) for path in backup.rglob("*") if path.is_dir()}
    for path in sorted(destination.rglob("*"), reverse=True):
        if path.is_file() and path.relative_to(destination) not in backup_files:
            path.unlink()
        elif path.is_dir() and path.relative_to(destination) not in backup_directories:
            path.rmdir()
    _sync_tree(backup, destination)
    if _tree_checksums(backup) != _tree_checksums(destination):
        raise RuntimeError(f"rollback checksum mismatch: {destination}")


def refresh_rights_ledger(*, package_root: Path, drive_root: Path) -> dict[str, object]:
    """Refresh explicit rights/admission records and mirror the whole private package.

    This path never derives a sentence, locator, CEFR value, or redistribution
    permission.  It only classifies the restored strict-VESUM retrieval states.
    """
    if not package_root.is_dir():
        raise ValueError(f"package root does not exist: {package_root}")
    if not drive_root.is_dir():
        raise ValueError(f"Drive mirror root does not exist: {drive_root}")
    if _tree_checksums(package_root) != _tree_checksums(drive_root):
        raise ValueError("local package and Drive mirror differ before refresh; inspect before replacing either copy")

    seed_rows = _read_jsonl(package_root / "curated-seed.jsonl")
    ledger_rows = _read_jsonl(package_root / "rights-ledger.jsonl")
    ledger_by_row = {row.get("seedRow"): row for row in ledger_rows}
    if len(ledger_by_row) != len(ledger_rows):
        raise ValueError("rights ledger contains duplicate seedRow values")
    if {row.get("seedRow") for row in seed_rows} != set(ledger_by_row):
        raise ValueError("curated seed and rights ledger seedRow values differ")

    refreshed_seed: list[dict[str, object]] = []
    refreshed_ledger: list[dict[str, object]] = []
    admissions: list[dict[str, object]] = []
    for seed in seed_rows:
        seed_row = seed.get("seedRow")
        ledger = dict(ledger_by_row[seed_row])
        status = str(seed.get("sentenceStatus") or "").strip()
        ledger_status = str(ledger.get("sentenceStatus") or "").strip()
        if ledger_status != status:
            raise ValueError(f"seed row {seed_row} has mismatched rights-ledger sentence status")
        rights, admission = classify_rights_admission(status, ledger.get("locator"))
        refreshed = dict(seed)
        refreshed["rights"] = rights
        refreshed["admission"] = admission
        refreshed_seed.append(refreshed)
        ledger["rightsStatus"] = rights["status"]
        ledger["redistributable"] = rights["redistributable"]
        ledger["rightsReason"] = rights["reason"]
        refreshed_ledger.append(ledger)
        admissions.append(
            {
                "seedRow": seed_row,
                "lemma": seed.get("lemma"),
                "practice": admission["practice"],
                "mode": admission["mode"],
                "reason": admission["reason"],
                "exampleCount": ledger.get("exampleCount", 0),
            }
        )

    parent = package_root.parent
    with tempfile.TemporaryDirectory(prefix=f".{package_root.name}.refresh-", dir=parent) as temporary:
        staged_root = Path(temporary) / package_root.name
        shutil.copytree(package_root, staged_root)
        _write_jsonl(staged_root / "curated-seed.jsonl", refreshed_seed)
        _write_jsonl(staged_root / "rights-ledger.jsonl", refreshed_ledger)
        _write_jsonl(staged_root / "practice-admission.jsonl", admissions)
        manifest_path = staged_root / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError(f"package manifest must be an object: {manifest_path}")
        manifest["state"] = "rights_ledger_refreshed_pending_operator_redistribution_go"
        admission_modes = Counter(str(row["admission"]["mode"]) for row in refreshed_seed)
        rights_statuses = Counter(str(row["rights"]["status"]) for row in refreshed_seed)
        manifest["row_counts"] = {
            "curated_seed": len(refreshed_seed),
            "rights_ledger": len(refreshed_ledger),
            "practice_admission": len(admissions),
            "rows_no_hit": sum(row.get("sentenceStatus") == "no_hit_strict_vesum" for row in refreshed_seed),
            "rows_with_candidates": sum(row.get("sentenceStatus") == "has_candidates" for row in refreshed_seed),
            "rights_private_local": sum(row["rights"]["status"] == PRIVATE_LOCAL for row in refreshed_seed),
            "practice_admitted": sum(row["admission"]["practice"] is True for row in refreshed_seed),
            "quarantined_missing_document_locator": admission_modes["quarantined_missing_document_locator"],
            "quarantined_unreviewed_sentence_status": admission_modes[
                "quarantined_unreviewed_sentence_status"
            ],
        }
        manifest["rights_admission_policy"] = {
            "redistribution": "operator GO required before redistributable may become true",
            "has_candidates_with_locator": {
                "rights_status": PRIVATE_LOCAL,
                "admission_mode": PENDING_REDISTRIBUTION_GO,
            },
            "no_hit_strict_vesum": {
                "admission_mode": "quarantined_no_document_hit",
                "reason": NO_HIT_REASON,
            },
        }
        _write_json(manifest_path, manifest)
        source_recon_path = staged_root / "source-recon.json"
        source_recon = json.loads(source_recon_path.read_text(encoding="utf-8"))
        if not isinstance(source_recon, dict):
            raise ValueError(f"source recon must be an object: {source_recon_path}")
        source_recon["admission"] = "rights_ledger_refreshed_pending_operator_redistribution_go"
        source_recon["rights_refresh"] = {
            "rights_statuses": dict(sorted(rights_statuses.items())),
            "admission_modes": dict(sorted(admission_modes.items())),
            "practice_admitted": manifest["row_counts"]["practice_admitted"],
        }
        _write_json(source_recon_path, source_recon)
        receipt = {
            "schema": "teacher-curated-seed-recovery-receipt-v1",
            "created_at": datetime.now(UTC).isoformat(),
            "state": manifest["state"],
            "document_policy": "master_docx private vault only",
            "row_count": len(refreshed_seed),
            "rows_no_hit": manifest["row_counts"]["rows_no_hit"],
            "rows_with_candidates": manifest["row_counts"]["rows_with_candidates"],
            "practice_admitted": manifest["row_counts"]["practice_admitted"],
            "drive_mirror": str(drive_root),
            "package_sha256": _tree_checksums(staged_root),
        }
        _write_json(staged_root / "receipt.json", receipt)

        with (
            tempfile.TemporaryDirectory(prefix=f".{package_root.name}.backup-", dir=parent) as local_temporary,
            tempfile.TemporaryDirectory(prefix=f".{drive_root.name}.backup-", dir=drive_root.parent) as drive_temporary,
        ):
            local_backup = Path(local_temporary) / package_root.name
            drive_backup = Path(drive_temporary) / drive_root.name
            shutil.copytree(package_root, local_backup)
            shutil.copytree(drive_root, drive_backup)
            try:
                _sync_tree(staged_root, drive_root)
                if _tree_checksums(staged_root) != _tree_checksums(drive_root):
                    raise RuntimeError("Drive mirror checksum mismatch after refresh")
                _sync_tree(staged_root, package_root)
                if _tree_checksums(staged_root) != _tree_checksums(package_root):
                    raise RuntimeError("local package checksum mismatch after refresh")
            except Exception:
                _restore_tree(drive_backup, drive_root)
                _restore_tree(local_backup, package_root)
                raise
    return receipt


def build_package(
    *,
    package_root: Path,
    drive_root: Path | None,
    replace_existing: bool = False,
    source_inventory_root: Path,
    decision_root: Path,
    cloze_path: Path,
    drive_source_root: Path,
) -> dict[str, object]:
    """Create the local package and a verified Drive mirror, or fail before writing."""
    if drive_root is None:
        raise ValueError("--drive-root is required; a local-only recovery package is forbidden")
    if package_root.exists() and not replace_existing:
        raise ValueError(f"package root already exists: {package_root}")
    if drive_root.exists() and not replace_existing:
        raise ValueError(f"Drive mirror root already exists: {drive_root}")

    source_recon = build_source_recon(
        source_inventory_root=source_inventory_root,
        decision_root=decision_root,
        cloze_path=cloze_path,
        drive_source_root=drive_source_root,
    )
    if replace_existing:
        if package_root.exists() and not package_root.is_dir():
            raise ValueError(f"package root is not a directory: {package_root}")
        if drive_root.exists() and not drive_root.is_dir():
            raise ValueError(f"Drive mirror root is not a directory: {drive_root}")
        if package_root.exists():
            shutil.rmtree(package_root)
        if drive_root.exists():
            shutil.rmtree(drive_root)
    package_root.mkdir(parents=True)
    _empty_jsonl(package_root / "curated-seed.jsonl")
    _empty_jsonl(package_root / "rights-ledger.jsonl")
    _empty_jsonl(package_root / "practice-admission.jsonl")
    _write_json(package_root / "source-recon.json", source_recon)
    _write_json(package_root / "package-manifest.json", _package_manifest(source_recon))
    checksums = _package_checksums(package_root)
    receipt = {
        "schema": "teacher-curated-seed-recovery-receipt-v1",
        "created_at": datetime.now(UTC).isoformat(),
        "state": "quarantined_missing_authoritative_table",
        "package_file_count": len(checksums),
        "package_sha256": checksums,
        "drive_mirror": str(drive_root),
    }
    _write_json(package_root / "receipt.json", receipt)

    drive_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(package_root, drive_root)
    mirrored = _package_checksums(drive_root)
    if mirrored != checksums:
        raise RuntimeError("Drive mirror checksum mismatch")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--drive-root", type=Path)
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument(
        "--refresh-rights-ledger",
        action="store_true",
        help="Refresh explicit local-only rights/admission states for a restored package.",
    )
    parser.add_argument("--source-inventory-root", type=Path, default=ROOT / "data/lexicon/source-inventory")
    parser.add_argument(
        "--decision-root", type=Path, default=ROOT / "data/lexicon/source-inventory-review-decisions"
    )
    parser.add_argument("--cloze-path", type=Path, default=ROOT / "site/src/data/lexicon-teacher-cloze.json")
    parser.add_argument("--drive-source-root", type=Path)
    args = parser.parse_args(argv)
    if args.refresh_rights_ledger:
        if args.drive_root is None:
            parser.error("--refresh-rights-ledger requires --drive-root")
        receipt = refresh_rights_ledger(package_root=args.package_root, drive_root=args.drive_root)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    if args.drive_source_root is None:
        parser.error("--drive-source-root is required unless --refresh-rights-ledger is used")
    receipt = build_package(
        package_root=args.package_root,
        drive_root=args.drive_root,
        replace_existing=args.replace_existing,
        source_inventory_root=args.source_inventory_root,
        decision_root=args.decision_root,
        cloze_path=args.cloze_path,
        drive_source_root=args.drive_source_root,
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
