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
    parser.add_argument("--source-inventory-root", type=Path, default=ROOT / "data/lexicon/source-inventory")
    parser.add_argument(
        "--decision-root", type=Path, default=ROOT / "data/lexicon/source-inventory-review-decisions"
    )
    parser.add_argument("--cloze-path", type=Path, default=ROOT / "site/src/data/lexicon-teacher-cloze.json")
    parser.add_argument("--drive-source-root", type=Path, required=True)
    args = parser.parse_args(argv)
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
