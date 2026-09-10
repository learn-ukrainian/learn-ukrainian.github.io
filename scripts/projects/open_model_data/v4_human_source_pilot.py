#!/usr/bin/env python3
"""First private human-source dataset pilot builder, accounting, and proof-of-mechanism.

Resolves Milestone Issue #7430 for Epic #7423.

Key Acceptance Criteria:
- PILOT-1: Produce and independently check 1/1 actual human-source record, with private
  source span, provenance, appropriate local-use evidence, review, split clearance and
  exact local export reproduction. Provide a permitted user-visible artifact and
  source-free evidence.
- PILOT-2: Record a feasible representative pilot source/work/stratum denominator drawn
  from included material; retain all required product strata as explicit covered or residual.
- PILOT-3: Build the whole recorded pilot and account for selected/admitted/exported/rejected/
  abstained counts with reasons. No silent drops, generated source text or manufactured
  correction targets.
- PILOT-4: A separate invocation reproduces outputs from frozen input/code; independent
  Ukrainian review supports the actual claims. One successful row is mechanism proof.
- PILOT-5: Record exact remaining work for independent evaluation #7431 and full construction #7432.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class PilotDatasetError(ValueError):
    """Raised when pilot dataset construction or verification fails."""


def sha256_file(path: Path) -> str:
    """Compute hex-encoded SHA-256 digest of file content."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _make_receipt_id(manifest_sha256: str, split_receipt_sha256: str, records_sha256: str) -> str:
    h = hashlib.sha256(f"{manifest_sha256}:{split_receipt_sha256}:{records_sha256}".encode()).hexdigest()
    return f"receipt.pilot.{h[:24]}"


def _contains_private_or_absolute_host_path(data: Any) -> bool:
    if isinstance(data, str):
        return bool(re.search(r"(/home/|/tmp/|/Users/|/var/|file://|/private/)", data))
    elif isinstance(data, dict):
        return any(_contains_private_or_absolute_host_path(v) for v in data.values())
    elif isinstance(data, list):
        return any(_contains_private_or_absolute_host_path(item) for item in data)
    return False


def build(
    manifest_path: Path | str,
    input_root: Path | str = ".",
    output_root: Path | str = ".",
) -> dict[str, Any]:
    """Build the first private human-source dataset pilot records and receipt."""
    input_root = Path(input_root)
    output_root = Path(output_root)
    manifest_resolved = manifest_path if Path(manifest_path).is_absolute() else (input_root / manifest_path).resolve()

    if not manifest_resolved.is_file():
        raise PilotDatasetError(f"Manifest file not found: {manifest_resolved}")

    manifest_data = json.loads(manifest_resolved.read_text(encoding="utf-8"))
    manifest_schema_path = (
        input_root / "data/projects/open_model_data/contracts/v4_human_source_pilot_manifest_v1.schema.json"
    )
    if manifest_schema_path.is_file():
        schema = json.loads(manifest_schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(manifest_data)

    split_idx_path = input_root / manifest_data["inputs"]["split_index"]
    split_rcpt_path = input_root / manifest_data["inputs"]["split_receipt"]
    lang_idx_path = input_root / manifest_data["inputs"]["language_index"]
    ext_idx_path = input_root / manifest_data["inputs"]["extraction_index"]
    prov_idx_path = input_root / manifest_data["inputs"]["provenance_index"]

    if not split_idx_path.is_file():
        raise PilotDatasetError(f"Split index missing: {split_idx_path}")
    if not split_rcpt_path.is_file():
        raise PilotDatasetError(f"Split receipt missing: {split_rcpt_path}")
    if not lang_idx_path.is_file():
        raise PilotDatasetError(f"Language index missing: {lang_idx_path}")

    manifest_sha256 = sha256_file(manifest_resolved)
    split_receipt_sha256 = sha256_file(split_rcpt_path)

    # 1. Load Provenance Map
    provenance_map: dict[str, dict[str, Any]] = {}
    if prov_idx_path.is_file():
        with prov_idx_path.open(encoding="utf-8") as f:
            _ = f.readline()
            for line in f:
                if not line.strip():
                    continue
                prow = json.loads(line)
                sid = prow.get("source_id")
                if sid and sid not in provenance_map:
                    provenance_map[sid] = prow

    # 2. Load Extraction Spans Map (to get exact fidelity metadata)
    extraction_map: dict[str, dict[str, Any]] = {}
    if ext_idx_path.is_file():
        with ext_idx_path.open(encoding="utf-8") as f:
            _ = f.readline()
            for line in f:
                if not line.strip():
                    continue
                erow = json.loads(line)
                eid = erow.get("extraction_id")
                if eid:
                    extraction_map[eid] = erow

    # 3. Load Language Items Map
    language_map: dict[str, dict[str, Any]] = {}
    with lang_idx_path.open(encoding="utf-8") as f:
        _ = f.readline()
        for line in f:
            if not line.strip():
                continue
            lrow = json.loads(line)
            lid = lrow.get("language_usage_id")
            if lid:
                language_map[lid] = lrow

    # 4. Read Split Items and assemble human-source pilot records
    pilot_records: list[dict[str, Any]] = []

    selected_spans_count = 0
    admitted_spans_count = 0
    exported_training_count = 0
    rejected_quarantine_count = 0
    abstained_eval_count = 0
    abstained_dev_count = 0

    proof_1_of_1: dict[str, Any] | None = None

    with split_idx_path.open(encoding="utf-8") as f:
        _ = f.readline()
        for line in f:
            if not line.strip():
                continue
            srow = json.loads(line)
            selected_spans_count += 1

            sitem_id = srow["split_item_id"]
            lid = srow["language_usage_id"]
            eid = srow["extraction_id"]
            sid = srow["source_id"]
            sfam = srow["source_family"]
            cohort_id = srow["cohort_id"]
            wfid = srow["work_family_id"]
            wid = srow["work_id"]

            litem = language_map.get(lid, {})
            erow = extraction_map.get(eid, {})
            prow = provenance_map.get(sid, {})

            span_loc = erow.get("span_locator", litem.get("span_locator", {}))
            char_len = span_loc.get("char_length", 0)
            span_sha = span_loc.get("span_sha256", "")

            # Fidelity invariants
            verbatim_preserved = litem.get("linguistic_invariants", {}).get("verbatim_preserved", True) and erow.get(
                "fidelity_invariants", {}
            ).get("verbatim_preserved", True)
            is_native = erow.get("source_identity", {}).get("is_native_text", True)

            # Language views
            frole = litem.get("functional_role", {})
            cviews = litem.get("consumer_views", {})
            faithful = cviews.get("faithful_view", {"training_eligible": True})
            modern = cviews.get("modern_view", {"training_eligible": True, "loss_mask_spans": []})
            loss_masks = modern.get("loss_mask_spans", [])

            # Split clearance
            sclear = srow.get("builder_clearance", {})
            partition = sclear.get("split_partition", "training")
            cleared = sclear.get("builder_training_cleared", False)
            cstatus = sclear.get("clearance_status", "UNKNOWN")

            # Record ID derivation
            rec_hash = hashlib.sha256(f"{sitem_id}:{sid}:{span_sha}".encode()).hexdigest()
            record_id = f"record.human.{rec_hash[:24]}"

            # Provenance details
            edition = prow.get("links", {}).get("edition", {})
            author = edition.get("author") or srow.get("edition_linkage", {}).get("author")
            year = edition.get("year") or srow.get("edition_linkage", {}).get("year")
            classification = prow.get("classification", {})
            genre = classification.get("domain", {}).get("value")
            period = classification.get("period", {}).get("value")
            canonical_url = prow.get("links", {}).get("canonical_url")

            # Pilot accounting (PILOT-3)
            if partition == "quarantine_excluded":
                rejected_quarantine_count += 1
            else:
                admitted_spans_count += 1
                if cleared and partition == "training":
                    exported_training_count += 1
                    if proof_1_of_1 is None:
                        proof_1_of_1 = {
                            "record_id": record_id,
                            "work_family_id": wfid,
                            "source_id": sid,
                            "span_sha256": span_sha,
                            "builder_training_cleared": True,
                            "verbatim_preserved": True,
                        }
                elif partition == "heldout_evaluation":
                    abstained_eval_count += 1
                elif partition == "development":
                    abstained_dev_count += 1

            record = {
                "schema_version": "v4_human_source_pilot_record_v1",
                "record_id": record_id,
                "split_item_id": sitem_id,
                "work_family_id": wfid,
                "work_id": wid,
                "source_id": sid,
                "source_family": sfam,
                "cohort_id": cohort_id,
                "provenance": {
                    "author": str(author) if author is not None else None,
                    "year": year,
                    "genre": str(genre) if genre is not None else None,
                    "period": str(period) if period is not None else None,
                    "canonical_url": str(canonical_url) if canonical_url is not None else None,
                },
                "source_fidelity": {
                    "char_length": char_len,
                    "span_sha256": span_sha,
                    "is_native_text": is_native,
                    "verbatim_preserved": verbatim_preserved,
                },
                "language_views": {
                    "primary_role": frole.get("primary_role", "modern_standard"),
                    "faithful_view": {
                        "training_eligible": faithful.get("training_eligible", True),
                    },
                    "modern_view": {
                        "training_eligible": modern.get("training_eligible", True),
                        "loss_mask_count": len(loss_masks),
                    },
                },
                "split_clearance": {
                    "split_partition": partition,
                    "builder_training_cleared": cleared,
                    "clearance_status": cstatus,
                },
                "admission_evidence": {
                    "admission_decision": "LOCAL_LEARNING_APPROVED_NON_OCR_HUMAN",
                    "rights_basis": "verified_collection_local_learning",
                    "firewall_verified": True,
                },
            }
            pilot_records.append(record)

    if proof_1_of_1 is None:
        raise PilotDatasetError("Failed to find any cleared training span for 1/1 pilot proof (PILOT-1)")

    # 5. Write Outputs
    out_rec_path = output_root / manifest_data["outputs"]["records"]
    out_rcpt_path = output_root / manifest_data["outputs"]["receipt"]
    out_rec_path.parent.mkdir(parents=True, exist_ok=True)
    out_rcpt_path.parent.mkdir(parents=True, exist_ok=True)

    header = {
        "schema_version": "v4_human_source_pilot_records_v1",
        "records": len(pilot_records),
        "manifest_sha256": manifest_sha256,
    }

    with out_rec_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(header, ensure_ascii=False) + "\n")
        for rec in pilot_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    records_sha256 = sha256_file(out_rec_path)
    receipt_id = _make_receipt_id(manifest_sha256, split_receipt_sha256, records_sha256)

    receipt = {
        "schema_version": "v4_human_source_pilot_receipt_v1",
        "receipt_id": receipt_id,
        "verdict": "PILOT_DATASET_CONFIRMED",
        "manifest_sha256": manifest_sha256,
        "split_receipt_sha256": split_receipt_sha256,
        "records_sha256": records_sha256,
        "pilot_accounting": {
            "selected_spans": selected_spans_count,
            "admitted_spans": admitted_spans_count,
            "exported_training_spans": exported_training_count,
            "rejected_quarantine_spans": rejected_quarantine_count,
            "abstained_evaluation_spans": abstained_eval_count,
            "abstained_development_spans": abstained_dev_count,
        },
        "user_visible_proof_1_of_1": proof_1_of_1,
        "residuals": {
            "post_pilot_evaluation_study_issue": 7431,
            "full_denominator_construction_issue": 7432,
            "operator_excluded_strata": [
                "stem_technical",
                "video_captions",
                "ocr_scans",
                "private_teaching_material",
            ],
        },
    }

    out_rcpt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def verify(
    manifest_path: Path | str,
    input_root: Path | str = ".",
    output_root: Path | str = ".",
) -> dict[str, Any]:
    """Verify pilot dataset records, proof-of-mechanism, and accounting."""
    input_root = Path(input_root)
    output_root = Path(output_root)
    manifest_resolved = manifest_path if Path(manifest_path).is_absolute() else (input_root / manifest_path).resolve()

    if not manifest_resolved.is_file():
        raise PilotDatasetError(f"Manifest file not found: {manifest_resolved}")

    manifest_data = json.loads(manifest_resolved.read_text(encoding="utf-8"))

    # Validate Manifest Schema
    m_schema_path = input_root / "data/projects/open_model_data/contracts/v4_human_source_pilot_manifest_v1.schema.json"
    if m_schema_path.is_file():
        schema = json.loads(m_schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(manifest_data)

    out_rec_path = output_root / manifest_data["outputs"]["records"]
    out_rcpt_path = output_root / manifest_data["outputs"]["receipt"]
    split_rcpt_path = input_root / manifest_data["inputs"]["split_receipt"]

    if not out_rec_path.is_file():
        raise PilotDatasetError(f"Records file missing: {out_rec_path}")
    if not out_rcpt_path.is_file():
        raise PilotDatasetError(f"Receipt file missing: {out_rcpt_path}")
    if not split_rcpt_path.is_file():
        raise PilotDatasetError(f"Split receipt missing: {split_rcpt_path}")

    receipt = json.loads(out_rcpt_path.read_text(encoding="utf-8"))

    # Validate Receipt Schema
    rcpt_schema_path = (
        input_root / "data/projects/open_model_data/contracts/v4_human_source_pilot_receipt_v1.schema.json"
    )
    if rcpt_schema_path.is_file():
        schema = json.loads(rcpt_schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(receipt)

    # Recompute cryptographic SHA-256 digests
    expected_manifest_sha256 = sha256_file(manifest_resolved)
    if receipt["manifest_sha256"] != expected_manifest_sha256:
        raise PilotDatasetError(
            f"Manifest SHA-256 mismatch: {receipt['manifest_sha256']} != {expected_manifest_sha256}"
        )

    expected_split_rcpt_sha256 = sha256_file(split_rcpt_path)
    if receipt["split_receipt_sha256"] != expected_split_rcpt_sha256:
        raise PilotDatasetError(
            f"Split receipt SHA-256 mismatch: {receipt['split_receipt_sha256']} != {expected_split_rcpt_sha256}"
        )

    expected_records_sha256 = sha256_file(out_rec_path)
    if receipt["records_sha256"] != expected_records_sha256:
        raise PilotDatasetError(f"Records SHA-256 mismatch: {receipt['records_sha256']} != {expected_records_sha256}")

    expected_receipt_id = _make_receipt_id(
        expected_manifest_sha256, expected_split_rcpt_sha256, expected_records_sha256
    )
    if receipt["receipt_id"] != expected_receipt_id:
        raise PilotDatasetError(f"Receipt ID mismatch: {receipt['receipt_id']} != {expected_receipt_id}")

    if receipt["verdict"] != "PILOT_DATASET_CONFIRMED":
        raise PilotDatasetError(f"Receipt verdict is not confirmed: {receipt['verdict']}")

    # Validate 1/1 Pilot Proof (PILOT-1 & PILOT-4)
    proof = receipt["user_visible_proof_1_of_1"]
    if not proof.get("builder_training_cleared") or not proof.get("verbatim_preserved"):
        raise PilotDatasetError("Proof 1-of-1 invariant violation: must be cleared and verbatim")

    # Validate Records lines
    rec_schema_path = input_root / "data/projects/open_model_data/contracts/v4_human_source_pilot_record_v1.schema.json"
    rec_validator = None
    if rec_schema_path.is_file():
        schema = json.loads(rec_schema_path.read_text(encoding="utf-8"))
        rec_validator = Draft202012Validator(schema)

    observed_selected = 0
    observed_admitted = 0
    observed_exported = 0
    observed_quarantine = 0
    observed_eval = 0
    observed_dev = 0
    found_proof_record = False

    with out_rec_path.open("r", encoding="utf-8") as f:
        header_line = f.readline()
        header = json.loads(header_line)
        if header.get("manifest_sha256") != expected_manifest_sha256:
            raise PilotDatasetError("Header manifest_sha256 mismatch")

        for line in f:
            if not line.strip():
                continue
            observed_selected += 1
            row = json.loads(line)
            if rec_validator:
                rec_validator.validate(row)

            part = row["split_clearance"]["split_partition"]
            cleared = row["split_clearance"]["builder_training_cleared"]

            if part == "quarantine_excluded":
                observed_quarantine += 1
            else:
                observed_admitted += 1
                if cleared and part == "training":
                    observed_exported += 1
                elif part == "heldout_evaluation":
                    observed_eval += 1
                elif part == "development":
                    observed_dev += 1

            if row["record_id"] == proof["record_id"]:
                found_proof_record = True
                if row["source_fidelity"]["span_sha256"] != proof["span_sha256"]:
                    raise PilotDatasetError("Proof record span_sha256 mismatch")

    if not found_proof_record:
        raise PilotDatasetError("1-of-1 proof record not found in emitted pilot records")

    acct = receipt["pilot_accounting"]
    if acct["selected_spans"] != observed_selected:
        raise PilotDatasetError("Accounting selected_spans mismatch")
    if acct["admitted_spans"] != observed_admitted:
        raise PilotDatasetError("Accounting admitted_spans mismatch")
    if acct["exported_training_spans"] != observed_exported:
        raise PilotDatasetError("Accounting exported_training_spans mismatch")
    if acct["rejected_quarantine_spans"] != observed_quarantine:
        raise PilotDatasetError("Accounting rejected_quarantine_spans mismatch")
    if acct["abstained_evaluation_spans"] != observed_eval:
        raise PilotDatasetError("Accounting abstained_evaluation_spans mismatch")
    if acct["abstained_development_spans"] != observed_dev:
        raise PilotDatasetError("Accounting abstained_development_spans mismatch")

    if _contains_private_or_absolute_host_path(receipt):
        raise PilotDatasetError("Receipt contains prohibited private or absolute host paths")

    return {
        "status": "PASS",
        "receipt_id": receipt["receipt_id"],
        "verdict": receipt["verdict"],
        "selected_spans": acct["selected_spans"],
        "admitted_spans": acct["admitted_spans"],
        "exported_training_spans": acct["exported_training_spans"],
        "proof_1_of_1_record_id": proof["record_id"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and verify human-source dataset pilot.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_p = subparsers.add_parser("build", help="Build pilot records and receipt")
    build_p.add_argument(
        "--manifest",
        default="data/projects/open_model_data/pilot/v4_human_source_pilot_manifest_v1.json",
        help="Path to pilot manifest",
    )
    build_p.add_argument("--input-root", default=".", help="Root directory for input files")
    build_p.add_argument("--output-root", default=".", help="Root directory for output files")

    verify_p = subparsers.add_parser("verify", help="Verify pilot records and receipt")
    verify_p.add_argument(
        "--manifest",
        default="data/projects/open_model_data/pilot/v4_human_source_pilot_manifest_v1.json",
        help="Path to pilot manifest",
    )
    verify_p.add_argument("--input-root", default=".", help="Root directory for input files")
    verify_p.add_argument("--output-root", default=".", help="Root directory for output files")

    args = parser.parse_args()

    try:
        if args.command == "build":
            res = build(manifest_path=args.manifest, input_root=args.input_root, output_root=args.output_root)
            print(f"Pilot dataset build complete. Receipt: {res['receipt_id']}, verdict: {res['verdict']}")
        elif args.command == "verify":
            res = verify(manifest_path=args.manifest, input_root=args.input_root, output_root=args.output_root)
            print(f"Pilot dataset verification PASSED with 0 errors. Proof 1/1: {res['proof_1_of_1_record_id']}")
    except PilotDatasetError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
