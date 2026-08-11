#!/usr/bin/env python3
"""Materialize the complete admitted open historical-corpus lanes.

This runner is deliberately separate from the bounded canary materializer. It
requires an exact reviewed gate and the exact successful canary bytes, then
streams every eligible ``orv-uk`` UD sentence and every PluG2 document whose
source-language metadata is exactly ``UK`` into immutable private output.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import zipfile
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.projects.open_model_data import phase3_historical_materialization as base
from scripts.projects.open_model_data import phase3_historical_representation as historical
from scripts.projects.open_model_data import phase3_linguistic_representation as linguistic
from scripts.projects.open_model_data.phase3_linguistic_representation import (
    canonical_json,
    sha256_value,
)

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
GATE_SCHEMA_PATH = DATA / "contracts/phase3_historical_full_materialization_gate_v1.schema.json"
RECEIPT_SCHEMA_PATH = (
    DATA / "contracts/phase3_historical_full_materialization_receipt_v1.schema.json"
)
DEFAULT_GATE_PATH = DATA / "admission/phase3_historical_full_materialization_gate_v1.json"
PERIODIZATION_FREEZE_PATH = (
    DATA / "admission/phase3_historical_periodization_freeze_v1.json"
)
HISTORICAL_REPRESENTATION_SCHEMA_PATH = (
    DATA / "contracts/phase3_historical_representation_v3.schema.json"
)

GATE_SCHEMA_VERSION = "phase3_historical_full_materialization_gate_v1"
RECEIPT_SCHEMA_VERSION = "phase3_historical_full_materialization_receipt_v1"
EXPECTED_GATE_FILE_SHA256 = "a2bad8d9e0374ac5cfffa9a8c0303bca536ffffd4915d58c74f34ad984ca657c"

V2_PROMPT_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
V3_PROMPT_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
PERIODIZATION_FREEZE_SHA256 = "94d07a2e4e2fe453334a494007bc823cf4be7ce07f0a21779c73163ac821a198"
HISTORICAL_REPRESENTATION_SCHEMA_SHA256 = (
    "37db223de63aaa3ce05dc154193b86ae4db8022c6f14f49a9035ebb5d37d4441"
)
HISTORICAL_REPRESENTATION_IMPLEMENTATION_SHA256 = (
    "7783583b7422f77b8ddfb53d984ea748e8a998b2d4a76cef7a8a326416f6d9f4"
)
LINGUISTIC_REPRESENTATION_IMPLEMENTATION_SHA256 = (
    "0609635b31b2af469ff8427751bc3a5161b160d84d1d9e6065d85e0afffc58b5"
)
LINGUISTIC_REPRESENTATION_SCHEMA_SHA256 = (
    "07dffdbc6220adfd088a1e3a19d369093d6331c67fa648880c59ca10d56b2489"
)
CANARY_MATERIALIZER_SHA256 = "c513800757bf8c421a1163398932c68e4ad390e0b2774c1d6dd24049692ce829"
CANARY_RECEIPT_FILE_SHA256 = "ef4bb2e499b6338fbcef90930052eef2de06a9176f4f1143fa74b2e2f3517071"
CANARY_UD_OUTPUT_SHA256 = "5c2ea7d88aa44adb300b7765a6854569afa4651738bd3ec554b1a501931cc710"
CANARY_PLUG2_OUTPUT_SHA256 = "4903747b4a8f079b75732aa7c983958e64c9b6ddf8f598afa733e900f0f03716"

OUTPUT_CEILING_BYTES = int(base.OUTPUT_CEILING_GIB * 1024**3)
MINIMUM_FREE_DISK_GIB = 8.0
PROJECTED_COMPRESSED_GIB = 1.8481288392973172
OUTPUT_DIRECTORY_NAME = "phase3-v3-full-ud-orv-uk-plug2-uk-v1"
RECEIPT_FILENAME = "historical-full-materialization-receipt-v1.json"


class HistoricalFullMaterializationError(ValueError):
    """The full materialization gate, inputs, or output invariants failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HistoricalFullMaterializationError(message)


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoricalFullMaterializationError(f"cannot read {label}: {path}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _schema(path: Path) -> dict[str, Any]:
    value = read_json(path, "schema")
    Draft202012Validator.check_schema(value)
    return value


def _validate_schema(value: Mapping[str, Any], path: Path, label: str) -> None:
    errors = sorted(
        Draft202012Validator(_schema(path)).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or label
        raise HistoricalFullMaterializationError(
            f"{label} schema violation at {location}: {errors[0].message}"
        )


def _with_receipt_sha256(body: Mapping[str, Any]) -> dict[str, Any]:
    return {**body, "receipt_sha256": sha256_value(body)}


def _receipt_hash_is_valid(value: Mapping[str, Any]) -> bool:
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    return value.get("receipt_sha256") == sha256_value(body)


def build_gate(
    *,
    ud_file_sha256: Mapping[str, str] = base.UD_EXPECTED_SHA256,
    plug2_archive_sha256: str = base.PLUG2_ARCHIVE_SHA256,
    plug2_metadata_sha256: str = base.PLUG2_METADATA_SHA256,
    ud_denominator: Mapping[str, int] = base.UD_EXPECTED_DENOMINATOR,
    plug2_denominator: Mapping[str, int] = base.PLUG2_EXPECTED_DENOMINATOR,
    plug2_uk_token_sum: int = 71802066,
) -> dict[str, Any]:
    """Build the deterministic text-free full-run authorization."""
    body: dict[str, Any] = {
        "schema_version": GATE_SCHEMA_VERSION,
        "text_free": True,
        "status": "AUTHORIZED_FOR_EXACT_FULL_MATERIALIZATION",
        "bindings": {
            "phase3_recovery_prompt_v2_sha256": V2_PROMPT_SHA256,
            "phase3_reboot_prompt_v3_sha256": V3_PROMPT_SHA256,
            "historical_periodization_freeze_sha256": PERIODIZATION_FREEZE_SHA256,
            "historical_representation_schema_sha256": (
                HISTORICAL_REPRESENTATION_SCHEMA_SHA256
            ),
            "historical_representation_implementation_sha256": (
                HISTORICAL_REPRESENTATION_IMPLEMENTATION_SHA256
            ),
            "linguistic_representation_implementation_sha256": (
                LINGUISTIC_REPRESENTATION_IMPLEMENTATION_SHA256
            ),
            "linguistic_representation_schema_sha256": (
                LINGUISTIC_REPRESENTATION_SCHEMA_SHA256
            ),
            "historical_materializer_sha256": CANARY_MATERIALIZER_SHA256,
            "canary_receipt_file_sha256": CANARY_RECEIPT_FILE_SHA256,
            "canary_ud_output_sha256": CANARY_UD_OUTPUT_SHA256,
            "canary_plug2_output_sha256": CANARY_PLUG2_OUTPUT_SHA256,
        },
        "source_denominators": {
            "ud": {
                "dataset_id": base.UD_COLLECTION_ID,
                "commit_sha": base.UD_COMMIT,
                "file_sha256": dict(sorted(ud_file_sha256.items())),
                "eligible_language": "orv-uk",
                **dict(ud_denominator),
            },
            "plug2": {
                "dataset_id": base.PLUG2_COLLECTION_ID,
                "doi": base.PLUG2_DOI,
                "archive_sha256": plug2_archive_sha256,
                "metadata_sha256": plug2_metadata_sha256,
                "eligible_original_language": "UK",
                **dict(plug2_denominator),
                "uk_token_sum": plug2_uk_token_sum,
            },
        },
        "rights": {
            "ud_license": "CC BY-SA 4.0",
            "plug2_license": "CC BY 4.0",
            "attribution_required": True,
            "public_training_permitted": True,
            "source_specific_rights_preserved": True,
        },
        "execution": {
            "full_materialization_authorized": True,
            "selection_algorithm": "all_eligible_units_sorted_by_immutable_identity",
            "immutable_output": True,
            "output_outside_git_required": True,
            "canonical_output_directory": OUTPUT_DIRECTORY_NAME,
            "output_ceiling_gib": base.OUTPUT_CEILING_GIB,
            "minimum_free_disk_gib": MINIMUM_FREE_DISK_GIB,
            "projected_compressed_gib": PROJECTED_COMPRESSED_GIB,
            "provider_calls_authorized": False,
            "stop_conditions": [
                "input_hash_drift",
                "denominator_drift",
                "metadata_archive_set_mismatch",
                "non_utf8_source_member",
                "historical_representation_validation_failure",
                "compressed_output_ceiling_exceeded",
                "minimum_free_disk_not_met",
            ],
        },
        "residuals": {
            "periodization_assignment_pending_qualified_review": True,
            "saint_sophia_current_database_reconciliation_pending": True,
            "nimchuk_primary_full_text_pending": True,
        },
        "phase_boundaries": {
            "source_freeze_ready": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    gate = _with_receipt_sha256(body)
    validate_gate_document(gate)
    return gate


def validate_gate_document(gate: Mapping[str, Any]) -> dict[str, Any]:
    _validate_schema(gate, GATE_SCHEMA_PATH, "full materialization gate")
    require(_receipt_hash_is_valid(gate), "full materialization gate receipt hash drift")
    bindings = gate["bindings"]
    require(bindings["phase3_recovery_prompt_v2_sha256"] == V2_PROMPT_SHA256, "v2 prompt drift")
    require(bindings["phase3_reboot_prompt_v3_sha256"] == V3_PROMPT_SHA256, "v3 prompt drift")
    require(
        bindings["historical_periodization_freeze_sha256"] == PERIODIZATION_FREEZE_SHA256,
        "historical periodization binding drift",
    )
    require(
        bindings["historical_representation_schema_sha256"]
        == HISTORICAL_REPRESENTATION_SCHEMA_SHA256,
        "historical representation binding drift",
    )
    require(
        bindings["historical_representation_implementation_sha256"]
        == HISTORICAL_REPRESENTATION_IMPLEMENTATION_SHA256,
        "historical representation implementation binding drift",
    )
    require(
        bindings["linguistic_representation_implementation_sha256"]
        == LINGUISTIC_REPRESENTATION_IMPLEMENTATION_SHA256,
        "linguistic representation implementation binding drift",
    )
    require(
        bindings["linguistic_representation_schema_sha256"]
        == LINGUISTIC_REPRESENTATION_SCHEMA_SHA256,
        "linguistic representation schema binding drift",
    )
    require(
        bindings["historical_materializer_sha256"] == CANARY_MATERIALIZER_SHA256,
        "reviewed canary materializer binding drift",
    )
    require(bindings["canary_receipt_file_sha256"] == CANARY_RECEIPT_FILE_SHA256, "canary receipt drift")
    require(bindings["canary_ud_output_sha256"] == CANARY_UD_OUTPUT_SHA256, "UD canary output drift")
    require(
        bindings["canary_plug2_output_sha256"] == CANARY_PLUG2_OUTPUT_SHA256,
        "PluG2 canary output drift",
    )
    execution = gate["execution"]
    require(execution["provider_calls_authorized"] is False, "gate authorizes provider calls")
    require(execution["full_materialization_authorized"] is True, "full run is not authorized")
    require(
        execution["canonical_output_directory"] == OUTPUT_DIRECTORY_NAME,
        "canonical output directory drift",
    )
    require(gate["phase_boundaries"]["phase4_blocked"] is True, "Phase 4 boundary drift")
    return dict(gate)


def verify_runtime_bindings() -> None:
    """Fail closed if an imported reviewed implementation or schema drifted."""
    runtime_bindings = {
        Path(base.__file__).resolve(): CANARY_MATERIALIZER_SHA256,
        Path(historical.__file__).resolve(): HISTORICAL_REPRESENTATION_IMPLEMENTATION_SHA256,
        Path(linguistic.__file__).resolve(): LINGUISTIC_REPRESENTATION_IMPLEMENTATION_SHA256,
        PERIODIZATION_FREEZE_PATH: PERIODIZATION_FREEZE_SHA256,
        HISTORICAL_REPRESENTATION_SCHEMA_PATH: HISTORICAL_REPRESENTATION_SCHEMA_SHA256,
        linguistic.SCHEMA_PATH: LINGUISTIC_REPRESENTATION_SCHEMA_SHA256,
    }
    for path, expected_sha256 in runtime_bindings.items():
        require(path.is_file(), f"missing bound runtime file: {path}")
        require(
            base.file_sha256(path) == expected_sha256,
            f"bound runtime file drift: {path.name}",
        )


def load_gate(path: Path = DEFAULT_GATE_PATH) -> tuple[dict[str, Any], str]:
    require(Path(path).is_file(), f"missing full materialization gate: {path}")
    file_sha256 = base.file_sha256(Path(path))
    require(file_sha256 == EXPECTED_GATE_FILE_SHA256, "full materialization gate byte drift")
    return validate_gate_document(read_json(Path(path), "full materialization gate")), file_sha256


def verify_canary(
    *,
    receipt_path: Path,
    ud_output_path: Path,
    plug2_output_path: Path,
) -> None:
    require(base.file_sha256(receipt_path) == CANARY_RECEIPT_FILE_SHA256, "canary receipt file drift")
    receipt = read_json(receipt_path, "canary receipt")
    require(receipt.get("mode") == "canary", "bound receipt is not a canary")
    require(receipt.get("residuals", {}).get("full_materialization_authorized") is False, "canary boundary drift")
    require(base.file_sha256(ud_output_path) == CANARY_UD_OUTPUT_SHA256, "UD canary bytes drift")
    require(base.file_sha256(plug2_output_path) == CANARY_PLUG2_OUTPUT_SHA256, "PluG2 canary bytes drift")
    require(receipt["outputs"]["ud"]["sha256"] == CANARY_UD_OUTPUT_SHA256, "UD canary receipt drift")
    require(
        receipt["outputs"]["plug2"]["sha256"] == CANARY_PLUG2_OUTPUT_SHA256,
        "PluG2 canary receipt drift",
    )


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    _validate_schema(receipt, RECEIPT_SCHEMA_PATH, "full materialization receipt")
    require(_receipt_hash_is_valid(receipt), "full materialization receipt hash drift")
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def materialize_full(
    *,
    gate: Mapping[str, Any],
    gate_file_sha256: str,
    ud_dir: Path,
    plug2_archive: Path,
    plug2_metadata: Path,
    private_output_dir: Path,
    receipt_output: Path,
    progress: Callable[[str, int, int], None] | None = None,
) -> dict[str, Any]:
    """Stream the exact complete eligible source sets into protected records."""
    gate = validate_gate_document(gate)
    verify_runtime_bindings()
    source_denominators = gate["source_denominators"]
    expected_ud_sha256 = source_denominators["ud"]["file_sha256"]
    expected_plug2_archive_sha256 = source_denominators["plug2"]["archive_sha256"]
    expected_plug2_metadata_sha256 = source_denominators["plug2"]["metadata_sha256"]

    require(not base._inside_git_checkout(private_output_dir.resolve()), "private text output cannot be inside a Git checkout")
    require(private_output_dir.name == OUTPUT_DIRECTORY_NAME, "output directory name is not the frozen value")
    require(receipt_output.parent.resolve() == private_output_dir.resolve(), "receipt must be inside immutable output")
    require(receipt_output.name == RECEIPT_FILENAME, "receipt filename is not the frozen value")
    require(not private_output_dir.exists(), "immutable full output directory already exists")
    free_gib = shutil.disk_usage(private_output_dir.parent).free / (1024**3)
    require(
        free_gib >= gate["execution"]["minimum_free_disk_gib"],
        "minimum free disk is not available for full materialization",
    )

    def verify_source_hashes() -> None:
        for filename, expected_hash in expected_ud_sha256.items():
            base._verify_hash(ud_dir / filename, expected_hash)
        base._verify_hash(plug2_archive, expected_plug2_archive_sha256)
        base._verify_hash(plug2_metadata, expected_plug2_metadata_sha256)

    verify_source_hashes()

    all_ud: list[base.UdSentence] = []
    for filename in sorted(expected_ud_sha256):
        all_ud.extend(
            base.parse_conllu(
                ud_dir / filename,
                source_file_sha256=expected_ud_sha256[filename],
            )
        )
    ud_candidates = sorted(
        (item for item in all_ud if item.language == "orv-uk"),
        key=lambda item: item.sent_id,
    )
    ud_ids = [item.sent_id for item in ud_candidates]
    require(len(ud_ids) == len(set(ud_ids)), "duplicate UD candidate sent_id")
    actual_ud_denominator = {
        "documents": len({item.document_id for item in ud_candidates}),
        "sentences": len(ud_candidates),
        "token_rows": sum(len(item.tokens) for item in ud_candidates),
    }
    expected_ud_denominator = {
        key: source_denominators["ud"][key] for key in ("documents", "sentences", "token_rows")
    }
    require(actual_ud_denominator == expected_ud_denominator, "UD candidate denominator drift")

    rows = base.load_plug2_metadata(plug2_metadata)
    archive_files = base.inspect_plug2_archive(plug2_archive)
    require({row["path"] for row in rows} == set(archive_files), "PluG2 metadata/archive path-set mismatch")
    uk_rows = {row["path"]: row for row in rows if row.get("doc.original") == "UK"}
    plug2_paths = sorted(uk_rows)
    token_sum = sum(base._metadata_nonnegative_int(row, "doc.tokenCount") for row in rows)
    uk_token_sum = sum(base._metadata_nonnegative_int(row, "doc.tokenCount") for row in uk_rows.values())
    actual_plug2_denominator = {
        "documents": len(rows),
        "token_sum": token_sum,
        "uk_documents": len(uk_rows),
        "non_uk_or_unknown_documents": len(rows) - len(uk_rows),
    }
    expected_plug2_denominator = {
        key: source_denominators["plug2"][key]
        for key in ("documents", "token_sum", "uk_documents", "non_uk_or_unknown_documents")
    }
    require(actual_plug2_denominator == expected_plug2_denominator, "PluG2 denominator drift")
    require(uk_token_sum == source_denominators["plug2"]["uk_token_sum"], "PluG2 UK token denominator drift")

    plug2_record_counter = 0

    def plug2_records() -> Iterator[Mapping[str, Any]]:
        nonlocal plug2_record_counter
        with zipfile.ZipFile(plug2_archive) as archive:
            for document_index, member_path in enumerate(plug2_paths, start=1):
                raw_bytes = archive.read(archive_files[member_path])
                try:
                    document_text = raw_bytes.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise HistoricalFullMaterializationError(
                        f"PluG2 member is not UTF-8: {member_path}"
                    ) from exc
                units = base.paragraph_units(document_text)
                require(bool(units), f"PluG2 document has no non-empty paragraphs: {member_path}")
                for paragraph_index, (start, end, value) in enumerate(units):
                    plug2_record_counter += 1
                    yield base.build_plug2_record(
                        row=uk_rows[member_path],
                        member_bytes=raw_bytes,
                        paragraph_index=paragraph_index,
                        paragraph_start=start,
                        paragraph_end=end,
                        paragraph_text=value,
                        archive_sha256=expected_plug2_archive_sha256,
                        metadata_sha256=expected_plug2_metadata_sha256,
                    )
                if progress is not None and (document_index % 1000 == 0 or document_index == len(plug2_paths)):
                    progress("plug2_documents", document_index, len(plug2_paths))

    private_output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".{private_output_dir.name}.staging-", dir=private_output_dir.parent)
    )
    try:
        ud_output = staging_dir / "ud-orv-uk-full.jsonl.gz"
        ud_record_count, ud_output_bytes, ud_output_sha256 = base._write_jsonl_gzip(
            ud_output,
            (base.build_ud_record(item) for item in ud_candidates),
        )
        if progress is not None:
            progress("ud_sentences", len(ud_candidates), len(ud_candidates))

        plug2_output = staging_dir / "plug2-uk-full.jsonl.gz"
        plug2_record_count, plug2_output_bytes, plug2_output_sha256 = base._write_jsonl_gzip(
            plug2_output,
            plug2_records(),
        )
        require(plug2_record_count == plug2_record_counter, "PluG2 record counter drift")
        total_bytes = ud_output_bytes + plug2_output_bytes
        require(total_bytes <= OUTPUT_CEILING_BYTES, "compressed output ceiling exceeded")
        verify_source_hashes()

        body: dict[str, Any] = {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "mode": "full",
            "text_free": True,
            "gate_sha256": gate_file_sha256,
            "inputs": {
                "canary_receipt_file_sha256": gate["bindings"]["canary_receipt_file_sha256"],
                "ud_file_sha256": dict(sorted(expected_ud_sha256.items())),
                "plug2_archive_sha256": expected_plug2_archive_sha256,
                "plug2_metadata_sha256": expected_plug2_metadata_sha256,
            },
            "denominators": {
                "ud_explicit_orv_uk": actual_ud_denominator,
                "ud_other_or_unresolved_sentences": len(all_ud) - len(ud_candidates),
                "plug2": actual_plug2_denominator,
                "plug2_candidate_uk_token_sum": uk_token_sum,
            },
            "selection": {
                "algorithm": "all_eligible_units_sorted_by_immutable_identity",
                "ud_selected_sentences": len(ud_ids),
                "ud_selection_sha256": sha256_value(ud_ids),
                "plug2_selected_documents": len(plug2_paths),
                "plug2_selection_sha256": sha256_value(plug2_paths),
            },
            "outputs": {
                "ud": {
                    "filename": ud_output.name,
                    "records": ud_record_count,
                    "bytes": ud_output_bytes,
                    "sha256": ud_output_sha256,
                },
                "plug2": {
                    "filename": plug2_output.name,
                    "records": plug2_record_count,
                    "bytes": plug2_output_bytes,
                    "sha256": plug2_output_sha256,
                },
                "total_compressed_bytes": total_bytes,
                "total_compressed_gib": total_bytes / (1024**3),
                "ceiling_gib": base.OUTPUT_CEILING_GIB,
            },
            "coverage": {
                "full_materialization_complete": True,
                "ud_eligible_set_equal": len(ud_ids) == actual_ud_denominator["sentences"],
                "plug2_eligible_set_equal": len(plug2_paths) == actual_plug2_denominator["uk_documents"],
                "non_eligible_inputs_excluded": True,
                "periodization_assignment_state": "unresolved_pending_qualified_historical_review",
            },
            "safeguards": {
                "historical_forms_protected": True,
                "modern_correction_eligible": False,
                "source_bytes_preserved": True,
                "provider_calls": False,
                "phase4_authorized": False,
            },
            "phase_boundaries": {
                "source_freeze_ready": False,
                "source_coverage_ready": False,
                "phase3_complete": False,
                "phase4_blocked": True,
            },
        }
        receipt = _with_receipt_sha256(body)
        _write_receipt(staging_dir / receipt_output.name, receipt)
        os.replace(staging_dir, private_output_dir)
        return receipt
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, default=DEFAULT_GATE_PATH)
    parser.add_argument("--canary-receipt", type=Path, required=True)
    parser.add_argument("--canary-ud-output", type=Path, required=True)
    parser.add_argument("--canary-plug2-output", type=Path, required=True)
    parser.add_argument("--ud-dir", type=Path, required=True)
    parser.add_argument("--plug2-archive", type=Path, required=True)
    parser.add_argument("--plug2-metadata", type=Path, required=True)
    parser.add_argument("--private-output-dir", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    return parser.parse_args(argv)


def _progress(kind: str, completed: int, total: int) -> None:
    print(canonical_json({"kind": kind, "completed": completed, "total": total}), file=sys.stderr, flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        gate, gate_file_sha256 = load_gate(args.gate)
        verify_canary(
            receipt_path=args.canary_receipt,
            ud_output_path=args.canary_ud_output,
            plug2_output_path=args.canary_plug2_output,
        )
        receipt = materialize_full(
            gate=gate,
            gate_file_sha256=gate_file_sha256,
            ud_dir=args.ud_dir,
            plug2_archive=args.plug2_archive,
            plug2_metadata=args.plug2_metadata,
            private_output_dir=args.private_output_dir,
            receipt_output=args.receipt_output,
            progress=_progress,
        )
    except (HistoricalFullMaterializationError, base.HistoricalMaterializationError) as exc:
        print(canonical_json({"status": "blocked", "error": str(exc)}))
        return 2
    print(
        canonical_json(
            {
                "status": "full_materialization_complete",
                "receipt_sha256": receipt["receipt_sha256"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
