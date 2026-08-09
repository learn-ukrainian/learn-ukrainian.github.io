#!/usr/bin/env python3
"""Audit textbook JSONL for objective native logical-text anomalies.

This command never repairs text.  It records exact source hashes, chunk ids,
pages, and detector findings so affected rows can be quarantined without
inventing replacement characters or silently changing the source corpus.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.rag.extract_text import detect_native_text_anomalies

SCHEMA_VERSION = "textbook-native-exactness-audit.v1"
BLOCK_SIZE = 1024 * 1024


class ExactnessAuditError(RuntimeError):
    """Raised when an input cannot be audited without ambiguity."""


def recorded_anomaly_requires_visual_verification(value: Any) -> bool:
    """Interpret recorded detector metadata under the current blocking policy.

    Earlier extraction runs counted single-letter token runs as findings. Those
    runs are common, legitimate layout in equations, diagrams, and spelling
    exercises. Keep them as auditable observations, but do not perpetuate a
    production block when they are the only recorded signal.
    """
    if not isinstance(value, dict) or not value.get("requires_visual_verification"):
        return False
    blocking_fields = (
        "adjacent_duplicate_line_pairs",
        "adjacent_first_character_truncation_pairs",
        "intraline_duplicate_token_spans",
    )
    if any(value.get(field) for field in blocking_fields):
        return True
    # Single-letter-only legacy shapes are observations; every other unknown
    # or older shape remains fail-closed.
    return not bool(value.get("single_letter_token_runs"))


def require_production_eligible_entry(entry: dict[str, Any], *, source_file: str) -> None:
    """Reject OCR or anomalous native text without exact page-image evidence."""
    extraction_mode = entry.get("extraction_mode")
    page_extraction_mode = entry.get("page_extraction_mode")
    declared_modes = {mode for mode in (extraction_mode, page_extraction_mode) if mode is not None}
    if len(declared_modes) > 1:
        raise ExactnessAuditError(f"{source_file}: conflicting extraction-mode metadata")

    quality = entry.get("quality")
    verification = quality.get("visual_verification") if isinstance(quality, dict) else None
    verification_status = verification.get("status") if isinstance(verification, dict) else None
    evidence_id = verification.get("evidence_id") if isinstance(verification, dict) else None
    layout = entry.get("layout")
    recorded_anomalies = layout.get("native_text_anomalies") if isinstance(layout, dict) else None
    recorded_anomaly = recorded_anomaly_requires_visual_verification(recorded_anomalies)
    detected_anomaly = bool(
        detect_native_text_anomalies(str(entry.get("text") or ""))["requires_visual_verification"]
    )
    requires_verification = (
        "apple_vision_ocr" in declared_modes
        or verification_status in {"required", "verified"}
        or recorded_anomaly
        or detected_anomaly
    )
    if not requires_verification:
        return
    if verification_status != "verified" or not isinstance(evidence_id, str) or not evidence_id.strip():
        chunk_id = str(entry.get("chunk_id") or "<missing-chunk-id>")
        raise ExactnessAuditError(
            f"{source_file}: chunk {chunk_id} requires exact page-image verification "
            "with a non-empty evidence_id before production ingest"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(BLOCK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            Path(temporary).unlink()
        raise


def load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ExactnessAuditError(f"{path}:{line_number}: invalid JSON") from exc
            if not isinstance(row, dict):
                raise ExactnessAuditError(f"{path}:{line_number}: JSONL row is not an object")
            rows.append(row)
    return rows


def apply_visual_verifications(
    chunks_root: Path,
    verifications: dict[str, str],
) -> dict[str, Any]:
    """Mark exact anomalous chunks verified without changing extracted text."""
    if not verifications:
        raise ExactnessAuditError("at least one --verify CHUNK_ID=EVIDENCE_ID is required")

    files = sorted(Path(chunks_root).glob("grade-*/*.jsonl"))
    if not files:
        raise ExactnessAuditError(f"no grade-*/*.jsonl files under {chunks_root}")

    rows_by_file = {path: load_jsonl_rows(path) for path in files}
    matches: dict[str, list[tuple[Path, dict[str, Any]]]] = {
        chunk_id: [] for chunk_id in verifications
    }
    for path, rows in rows_by_file.items():
        for row in rows:
            chunk_id = str(row.get("chunk_id") or "")
            if chunk_id in matches:
                matches[chunk_id].append((path, row))

    invalid_counts = {
        chunk_id: len(found) for chunk_id, found in matches.items() if len(found) != 1
    }
    if invalid_counts:
        raise ExactnessAuditError(
            f"verification chunk ids must exist exactly once: {invalid_counts}"
        )

    for chunk_id, found in matches.items():
        _path, row = found[0]
        evidence_id = verifications[chunk_id].strip()
        if not evidence_id:
            raise ExactnessAuditError(f"{chunk_id}: evidence id is empty")
        findings = detect_native_text_anomalies(str(row.get("text") or ""))
        layout = row.get("layout")
        recorded = layout.get("native_text_anomalies") if isinstance(layout, dict) else None
        recorded_anomaly = recorded_anomaly_requires_visual_verification(recorded)
        if not findings["requires_visual_verification"] and not recorded_anomaly:
            raise ExactnessAuditError(f"{chunk_id}: no current native-text anomaly to verify")
        quality = row.setdefault("quality", {})
        if not isinstance(quality, dict):
            raise ExactnessAuditError(f"{chunk_id}: quality metadata is not an object")
        quality["visual_verification"] = {
            "status": "verified",
            "evidence_id": evidence_id,
        }

    changed_files: list[dict[str, Any]] = []
    for path, rows in rows_by_file.items():
        changed_ids = sorted(
            chunk_id for chunk_id, found in matches.items() if found[0][0] == path
        )
        if not changed_ids:
            continue

        input_sha256 = sha256_file(path)
        payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
        atomic_write(path, payload)
        changed_files.append(
            {
                "relative_jsonl": path.relative_to(chunks_root).as_posix(),
                "input_sha256": input_sha256,
                "output_sha256": sha256_file(path),
                "verified_chunk_ids": sorted(changed_ids),
            }
        )

    return {
        "schema_version": "textbook-native-visual-verification.v1",
        "policy": "Verification metadata only; extracted text is unchanged.",
        "verified_chunk_count": len(verifications),
        "files": changed_files,
    }


def apply_quarantine_exclusions(
    chunks_root: Path,
    exclusions: dict[str, str],
    *,
    quarantine_dir: Path,
) -> dict[str, Any]:
    """Archive and remove exact anomalous chunks without repairing their text."""
    if not exclusions:
        raise ExactnessAuditError("at least one --exclude CHUNK_ID=EVIDENCE_ID is required")

    files = sorted(Path(chunks_root).glob("grade-*/*.jsonl"))
    if not files:
        raise ExactnessAuditError(f"no grade-*/*.jsonl files under {chunks_root}")

    rows_by_file = {path: load_jsonl_rows(path) for path in files}
    matches: dict[str, list[tuple[Path, dict[str, Any]]]] = {
        chunk_id: [] for chunk_id in exclusions
    }
    for path, rows in rows_by_file.items():
        for row in rows:
            chunk_id = str(row.get("chunk_id") or "")
            if chunk_id in matches:
                matches[chunk_id].append((path, row))

    invalid_counts = {
        chunk_id: len(found) for chunk_id, found in matches.items() if len(found) != 1
    }
    if invalid_counts:
        raise ExactnessAuditError(f"exclusion chunk ids must exist exactly once: {invalid_counts}")

    for chunk_id, found in matches.items():
        if not exclusions[chunk_id].strip():
            raise ExactnessAuditError(f"{chunk_id}: evidence id is empty")
        row = found[0][1]
        findings = detect_native_text_anomalies(str(row.get("text") or ""))
        layout = row.get("layout")
        recorded = layout.get("native_text_anomalies") if isinstance(layout, dict) else None
        recorded_anomaly = recorded_anomaly_requires_visual_verification(recorded)
        if not findings["requires_visual_verification"] and not recorded_anomaly:
            raise ExactnessAuditError(f"{chunk_id}: no current native-text anomaly to exclude")

    changed_files: list[dict[str, Any]] = []
    for path, rows in rows_by_file.items():
        excluded_ids = sorted(
            chunk_id for chunk_id, found in matches.items() if found[0][0] == path
        )
        if not excluded_ids:
            continue

        excluded_id_set = set(excluded_ids)
        archived_rows = [
            row for row in rows if str(row.get("chunk_id") or "") in excluded_id_set
        ]
        retained_rows = [
            row for row in rows if str(row.get("chunk_id") or "") not in excluded_id_set
        ]
        input_sha256 = sha256_file(path)
        archive_path = Path(quarantine_dir) / path.relative_to(chunks_root)
        archive_payload = "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in archived_rows
        )
        atomic_write(archive_path, archive_payload)
        payload = "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in retained_rows
        )
        atomic_write(path, payload)
        changed_files.append(
            {
                "relative_jsonl": path.relative_to(chunks_root).as_posix(),
                "input_sha256": input_sha256,
                "output_sha256": sha256_file(path),
                "archive_relative_jsonl": archive_path.relative_to(quarantine_dir).as_posix(),
                "archive_sha256": sha256_file(archive_path),
                "excluded_chunks": [
                    {"chunk_id": chunk_id, "evidence_id": exclusions[chunk_id]}
                    for chunk_id in excluded_ids
                ],
            }
        )

    return {
        "schema_version": "textbook-native-quarantine-exclusion.v1",
        "policy": "Exact anomalous rows are archived and excluded; text is never repaired.",
        "excluded_chunk_count": len(exclusions),
        "files": changed_files,
    }


def audit_chunk_files(chunks_root: Path) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Return a complete audit receipt and exact flagged source rows."""
    chunks_root = Path(chunks_root)
    files = sorted(chunks_root.glob("grade-*/*.jsonl"))
    if not files:
        raise ExactnessAuditError(f"no grade-*/*.jsonl files under {chunks_root}")

    sources: list[dict[str, Any]] = []
    quarantined_rows: dict[str, list[dict[str, Any]]] = {}
    chunk_total = 0
    flagged_chunk_total = 0
    verified_flagged_chunk_total = 0
    flagged_pages: set[tuple[str, int]] = set()

    for path in files:
        rows = load_jsonl_rows(path)
        chunk_total += len(rows)
        source_findings: list[dict[str, Any]] = []
        source_flagged_rows: list[dict[str, Any]] = []
        seen_chunk_ids: set[str] = set()
        for row in rows:
            chunk_id = str(row.get("chunk_id") or "").strip()
            if not chunk_id:
                raise ExactnessAuditError(f"{path}: row lacks chunk_id")
            if chunk_id in seen_chunk_ids:
                raise ExactnessAuditError(f"{path}: duplicate chunk_id {chunk_id}")
            seen_chunk_ids.add(chunk_id)
            result = detect_native_text_anomalies(str(row.get("text") or ""))
            layout = row.get("layout")
            recorded_anomalies = (
                layout.get("native_text_anomalies") if isinstance(layout, dict) else None
            )
            recorded_anomaly = recorded_anomaly_requires_visual_verification(
                recorded_anomalies
            )
            if not result["requires_visual_verification"] and not recorded_anomaly:
                continue
            page = int(row.get("page_start") or 0)
            quality = row.get("quality")
            visual_verification = (
                quality.get("visual_verification") if isinstance(quality, dict) else None
            )
            verification_status = (
                visual_verification.get("status")
                if isinstance(visual_verification, dict)
                else None
            )
            verification_evidence_id = (
                visual_verification.get("evidence_id")
                if isinstance(visual_verification, dict)
                else None
            )
            is_verified = bool(
                verification_status == "verified"
                and isinstance(verification_evidence_id, str)
                and verification_evidence_id.strip()
            )
            verified_flagged_chunk_total += int(is_verified)
            source_findings.append(
                {
                    "chunk_id": chunk_id,
                    "page_start": page,
                    "page_end": int(row.get("page_end") or page),
                    "anomalies": result,
                    "recorded_page_anomalies": recorded_anomalies,
                    "detection_scope": (
                        "chunk_and_recorded_page"
                        if result["requires_visual_verification"] and recorded_anomaly
                        else "chunk"
                        if result["requires_visual_verification"]
                        else "recorded_page"
                    ),
                    "visual_verification_status": verification_status,
                    "visual_verification_evidence_id": verification_evidence_id,
                }
            )
            source_flagged_rows.append(row)
            flagged_pages.add((path.stem, page))

        flagged_chunk_total += len(source_findings)
        if source_findings:
            quarantined_rows[path.stem] = source_flagged_rows
        sources.append(
            {
                "source_file": path.stem,
                "relative_jsonl": path.relative_to(chunks_root).as_posix(),
                "jsonl_sha256": sha256_file(path),
                "chunk_total": len(rows),
                "flagged_chunk_count": len(source_findings),
                "affected_pages": sorted({item["page_start"] for item in source_findings}),
                "findings": source_findings,
            }
        )

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "policy": (
            "No text repair or inference. Findings require exact page-image verification; "
            "unverified rows are not production-eligible."
        ),
        "chunks_root": str(chunks_root),
        "source_count": len(files),
        "chunk_total": chunk_total,
        "flagged_source_count": len(quarantined_rows),
        "flagged_chunk_count": flagged_chunk_total,
        "verified_flagged_chunk_count": verified_flagged_chunk_total,
        "unverified_flagged_chunk_count": flagged_chunk_total - verified_flagged_chunk_total,
        "flagged_page_count": len(flagged_pages),
        "clean_chunk_count": chunk_total - flagged_chunk_total,
        "sources": sources,
    }
    return receipt, quarantined_rows


def write_quarantine_rows(
    quarantine_dir: Path,
    receipt: dict[str, Any],
    rows_by_source: dict[str, list[dict[str, Any]]],
) -> None:
    """Atomically preserve exact flagged rows plus the complete audit receipt."""
    quarantine_dir = Path(quarantine_dir)
    for source_file, rows in sorted(rows_by_source.items()):
        payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
        atomic_write(quarantine_dir / f"{source_file}.jsonl", payload)
    atomic_write(
        quarantine_dir / "textbook-native-exactness-audit-v1.json",
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def unverified_quarantine_packet(
    receipt: dict[str, Any],
    rows_by_source: dict[str, list[dict[str, Any]]],
    *,
    full_audit_sha256: str,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Derive an exact quarantine packet that excludes verified findings."""
    filtered_sources: list[dict[str, Any]] = []
    filtered_rows: dict[str, list[dict[str, Any]]] = {}
    flagged_pages: set[tuple[str, int]] = set()
    flagged_chunks = 0
    for source in receipt.get("sources", []):
        findings = [
            finding
            for finding in source.get("findings", [])
            if finding.get("visual_verification_status") != "verified"
        ]
        current = {
            **source,
            "findings": findings,
            "flagged_chunk_count": len(findings),
            "affected_pages": sorted({int(finding["page_start"]) for finding in findings}),
        }
        filtered_sources.append(current)
        if not findings:
            continue
        source_file = str(source["source_file"])
        finding_ids = {str(finding["chunk_id"]) for finding in findings}
        rows = [
            row
            for row in rows_by_source.get(source_file, [])
            if str(row.get("chunk_id") or "") in finding_ids
        ]
        if {str(row.get("chunk_id") or "") for row in rows} != finding_ids:
            raise ExactnessAuditError(
                f"{source_file}: unverified quarantine rows do not match filtered findings"
            )
        filtered_rows[source_file] = rows
        flagged_chunks += len(findings)
        flagged_pages.update((source_file, int(finding["page_start"])) for finding in findings)

    packet = {
        **receipt,
        "policy": (
            "Exact unverified native-text findings only. Page-verified findings remain "
            "production-eligible and are excluded from this quarantine packet."
        ),
        "derived_from_full_audit_sha256": full_audit_sha256,
        "flagged_source_count": len(filtered_rows),
        "flagged_chunk_count": flagged_chunks,
        "verified_flagged_chunk_count": 0,
        "unverified_flagged_chunk_count": flagged_chunks,
        "flagged_page_count": len(flagged_pages),
        "clean_chunk_count": int(receipt["chunk_total"]) - flagged_chunks,
        "sources": filtered_sources,
    }
    return packet, filtered_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chunks-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quarantine-dir", type=Path)
    parser.add_argument(
        "--quarantine-unverified-only",
        action="store_true",
        help="exclude page-verified findings from the quarantine packet",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="CHUNK_ID=EVIDENCE_ID",
        help="archive and exclude one visually confirmed damaged chunk",
    )
    parser.add_argument("--exclusion-dir", type=Path)
    parser.add_argument("--exclusion-receipt", type=Path)
    parser.add_argument("--fail-on-findings", action="store_true")
    parser.add_argument(
        "--verify",
        action="append",
        default=[],
        metavar="CHUNK_ID=EVIDENCE_ID",
        help="mark one objectively anomalous chunk visually verified",
    )
    parser.add_argument("--verification-receipt", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.exclude:
            if args.exclusion_dir is None or args.exclusion_receipt is None:
                raise ExactnessAuditError(
                    "--exclusion-dir and --exclusion-receipt are required with --exclude"
                )
            exclusions: dict[str, str] = {}
            for item in args.exclude:
                chunk_id, separator, evidence_id = item.partition("=")
                if not separator or not chunk_id.strip() or not evidence_id.strip():
                    raise ExactnessAuditError(
                        "--exclude must use non-empty CHUNK_ID=EVIDENCE_ID"
                    )
                if chunk_id in exclusions:
                    raise ExactnessAuditError(f"duplicate exclusion chunk id: {chunk_id}")
                exclusions[chunk_id] = evidence_id
            exclusion_receipt = apply_quarantine_exclusions(
                args.chunks_root,
                exclusions,
                quarantine_dir=args.exclusion_dir,
            )
            atomic_write(
                args.exclusion_receipt,
                json.dumps(exclusion_receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
        if args.verify:
            verifications: dict[str, str] = {}
            for item in args.verify:
                chunk_id, separator, evidence_id = item.partition("=")
                if not separator or not chunk_id.strip() or not evidence_id.strip():
                    raise ExactnessAuditError(
                        "--verify must use non-empty CHUNK_ID=EVIDENCE_ID"
                    )
                if chunk_id in verifications:
                    raise ExactnessAuditError(f"duplicate verification chunk id: {chunk_id}")
                verifications[chunk_id] = evidence_id
            verification_receipt = apply_visual_verifications(args.chunks_root, verifications)
            if args.verification_receipt:
                atomic_write(
                    args.verification_receipt,
                    json.dumps(verification_receipt, ensure_ascii=False, indent=2, sort_keys=True)
                    + "\n",
                )
        receipt, rows_by_source = audit_chunk_files(args.chunks_root)
        payload = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            atomic_write(args.output, payload)
        if args.quarantine_dir:
            quarantine_receipt = receipt
            quarantine_rows = rows_by_source
            if args.quarantine_unverified_only:
                quarantine_receipt, quarantine_rows = unverified_quarantine_packet(
                    receipt,
                    rows_by_source,
                    full_audit_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                )
            write_quarantine_rows(
                args.quarantine_dir,
                quarantine_receipt,
                quarantine_rows,
            )
    except (ExactnessAuditError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    print(
        f"sources={receipt['source_count']} chunks={receipt['chunk_total']} "
        f"flagged_sources={receipt['flagged_source_count']} "
        f"flagged_chunks={receipt['flagged_chunk_count']} "
        f"flagged_pages={receipt['flagged_page_count']}"
    )
    if args.fail_on_findings and receipt["flagged_chunk_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
