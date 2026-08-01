#!/usr/bin/env python3
"""Build non-human safety probes and fail-closed treatment preflight evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
PREREG_SCHEMA = CONTRACTS / "treatment_preregistration_v1.schema.json"
AUTH_SCHEMA = CONTRACTS / "treatment_authorization_v1.schema.json"
PRODUCTION_SCHEMA = CONTRACTS / "model_ready_view_production_v1.schema.json"
TOKENIZER_SCHEMA = CONTRACTS / "tokenizer_diagnostics_v1.schema.json"
PROBE_RECEIPT_SCHEMA = CONTRACTS / "treatment_safety_probe_receipt_v1.schema.json"
MODEL_SNAPSHOT_SCHEMA = CONTRACTS / "hf_model_snapshot_manifest_v1.schema.json"
PREFLIGHT_SCHEMA = CONTRACTS / "treatment_stage0_preflight_v1.schema.json"
SPLIT_NAMESPACE = "gemma4-it-wikipedia-mask-ablation-v1"
SPLIT_MODULUS = 1000
VALIDATION_BUCKETS = 200
MODEL_IDENTIFIER = "google/gemma-4-31B-it"
MODEL_REVISION = "842da3794eaa0b77d5f08bae87a17459d91ff475"
SENTENCE_BOUNDARY = re.compile(r"[.!?…][\"'»”)]*\s+")


class TreatmentError(ValueError):
    """A preregistration, input artifact, or safety-probe contract is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TreatmentError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TreatmentError(f"expected JSON object in {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise TreatmentError(f"expected object at {path}:{line_number}")
                rows.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise TreatmentError(f"cannot read JSONL {path}: {exc}") from exc
    if not rows:
        raise TreatmentError(f"empty JSONL file: {path}")
    return rows


def validate_schema(value: Mapping[str, Any], schema_path: Path, *, label: str) -> None:
    schema = read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise TreatmentError(f"{label} schema error at {location}: {error.message}")


def write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(raw_temp_path)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def artifact(path: Path, *, records: int) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "records": records, "sha256": sha256_file(path)}


def split_bucket(source_payload_id: str) -> int:
    payload = f"{SPLIT_NAMESPACE}\0{source_payload_id}".encode()
    return int(hashlib.sha256(payload).hexdigest(), 16) % SPLIT_MODULUS


def project_loss_labels(
    input_ids: Sequence[int],
    offsets: Sequence[tuple[int, int]],
    special_tokens_mask: Sequence[int],
    attention_mask: Sequence[int],
    character_mask_spans: Sequence[Mapping[str, Any]],
    *,
    apply_character_masks: bool,
) -> list[int]:
    """Project character masks to causal-LM labels before record-local chunking."""
    lengths = {len(input_ids), len(offsets), len(special_tokens_mask), len(attention_mask)}
    if len(lengths) != 1:
        raise TreatmentError("token IDs, offsets, special mask, and attention mask length drift")
    spans = [(int(span["start_char"]), int(span["end_char"])) for span in character_mask_spans]
    if any(start < 0 or end <= start for start, end in spans):
        raise TreatmentError("invalid character mask span")
    labels: list[int] = []
    for token_id, (start, end), is_special, attended in zip(
        input_ids,
        offsets,
        special_tokens_mask,
        attention_mask,
        strict=True,
    ):
        ignored = not attended or bool(is_special)
        if apply_character_masks and start < end:
            ignored = ignored or any(start < mask_end and end > mask_start for mask_start, mask_end in spans)
        labels.append(-100 if ignored else int(token_id))
    return labels


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for match in SENTENCE_BOUNDARY.finditer(text):
        end = match.end() - (len(match.group()) - len(match.group().rstrip()))
        if end > start:
            spans.append((start, end))
        start = match.end()
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def _usable_sentence(text: str) -> bool:
    stripped = text.strip()
    letters = sum(character.isalpha() for character in stripped)
    return 40 <= len(stripped) <= 700 and letters >= 24


def _priority(*parts: object) -> str:
    return sha256_bytes("\0".join(str(part) for part in parts).encode("utf-8"))


def _id_digest(values: Iterable[str]) -> str:
    return sha256_bytes(("\n".join(sorted(values)) + "\n").encode("utf-8"))


def build_safety_probes(
    *,
    faithful_path: Path,
    modern_path: Path,
    output_path: Path,
    receipt_path: Path,
    clean_count: int = 120,
    protected_count: int = 180,
) -> dict[str, Any]:
    faithful_rows = read_jsonl(faithful_path)
    modern_rows = read_jsonl(modern_path)
    faithful_by_source = {str(row["lineage"]["source_payload_id"]): row for row in faithful_rows}
    modern_by_source = {str(row["lineage"]["source_payload_id"]): row for row in modern_rows}
    if len(faithful_by_source) != len(faithful_rows) or len(modern_by_source) != len(modern_rows):
        raise TreatmentError("duplicate source_payload_id in a continued-pretraining view")
    if set(faithful_by_source) != set(modern_by_source):
        raise TreatmentError("faithful and modern views do not contain the same source records")

    training_ids = sorted(source_id for source_id in faithful_by_source if split_bucket(source_id) >= VALIDATION_BUCKETS)
    validation_ids = sorted(set(faithful_by_source) - set(training_ids))
    clean_candidates: list[tuple[str, dict[str, Any]]] = []
    protected_candidates: list[tuple[str, dict[str, Any]]] = []
    validation_records_with_no_masks = 0
    available_protected_spans = 0

    for source_id in validation_ids:
        faithful = faithful_by_source[source_id]
        modern = modern_by_source[source_id]
        faithful_text = str(faithful["payload"]["text"])
        modern_text = str(modern["payload"]["text"])
        if faithful_text != modern_text:
            raise TreatmentError(f"paired view text drift for {source_id}")
        masks = modern["payload"]["character_mask_spans"]
        sentence_spans = _sentence_spans(modern_text)
        if not masks:
            validation_records_with_no_masks += 1
            for start, end in sentence_spans:
                sentence = modern_text[start:end].strip()
                if not _usable_sentence(sentence):
                    continue
                priority = _priority("clean_no_change", source_id, start, end, sentence)
                clean_candidates.append(
                    (
                        priority,
                        {
                            "gold_status": "deterministic_non_human_proxy_not_linguistic_gold",
                            "kind": "clean_no_change",
                            "probe_id": f"probe:{priority}",
                            "source": sentence,
                            "source_payload_id": source_id,
                            "source_sha256": sha256_bytes(sentence.encode("utf-8")),
                            "type": "safety_probe",
                        },
                    )
                )
        for mask in masks:
            mask_start = int(mask["start_char"])
            mask_end = int(mask["end_char"])
            available_protected_spans += 1
            containing = next(
                ((start, end) for start, end in sentence_spans if start <= mask_start and mask_end <= end),
                None,
            )
            if containing is None:
                continue
            start, end = containing
            sentence = modern_text[start:end].strip()
            left_trim = len(modern_text[start:end]) - len(modern_text[start:end].lstrip())
            relative_start = mask_start - start - left_trim
            relative_end = mask_end - start - left_trim
            if not _usable_sentence(sentence) or relative_start < 0 or relative_end > len(sentence):
                continue
            protected_text = sentence[relative_start:relative_end]
            if not protected_text.strip():
                continue
            priority = _priority("protected_span", source_id, mask_start, mask_end, protected_text)
            protected_candidates.append(
                (
                    priority,
                    {
                        "gold_status": "deterministic_non_human_proxy_not_linguistic_gold",
                        "kind": "protected_span",
                        "probe_id": f"probe:{priority}",
                        "protected": {
                            "end_char": relative_end,
                            "reason": str(mask["reason"]),
                            "sha256": sha256_bytes(protected_text.encode("utf-8")),
                            "start_char": relative_start,
                            "text": protected_text,
                        },
                        "source": sentence,
                        "source_payload_id": source_id,
                        "source_sha256": sha256_bytes(sentence.encode("utf-8")),
                        "type": "safety_probe",
                    },
                )
            )

    clean_rows = [row for _, row in sorted(clean_candidates)[:clean_count]]
    protected_rows = [row for _, row in sorted(protected_candidates)[:protected_count]]
    if len(clean_rows) != clean_count:
        raise TreatmentError(f"only {len(clean_rows)} clean no-change probes available; need {clean_count}")
    if len(protected_rows) != protected_count:
        raise TreatmentError(f"only {len(protected_rows)} protected-span probes available; need {protected_count}")
    rows = sorted([*clean_rows, *protected_rows], key=lambda row: str(row["probe_id"]))
    output_bytes = "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")
    write_atomic(output_path, output_bytes)
    output_binding = artifact(output_path, records=len(rows))
    identity = {
        "faithful_sha256": sha256_file(faithful_path),
        "modern_sha256": sha256_file(modern_path),
        "output_sha256": output_binding["sha256"],
        "split_namespace": SPLIT_NAMESPACE,
    }
    receipt = {
        "counts": {
            "available_protected_spans": available_protected_spans,
            "clean_no_change": len(clean_rows),
            "protected_span": len(protected_rows),
            "total": len(rows),
            "validation_records_with_no_masks": validation_records_with_no_masks,
        },
        "determinism": {
            "paired_view_text_identity": True,
            "selection": "validation partition only; deterministic sentence extraction; ascending SHA-256 priority",
            "serialization": "UTF-8 canonical JSON with sorted keys and LF",
            "timestamps_omitted": True,
        },
        "limitations": [
            "automated_non_human_proxy_not_linguistic_gold",
            "no_detector_candidate_is_not_proof_that_a_sentence_is_error_free",
            "protected_span_preservation_does_not_measure_all_contextual_acceptability",
            "probe_source_records_are_excluded_from_both_training_arms",
        ],
        "output": output_binding,
        "probe_inventory_id": f"treatment-safety-probes:{sha256_bytes(canonical_json(identity).encode('utf-8'))}",
        "safety": {
            "human_gold_created": False,
            "model_call_performed": False,
            "publication_performed": False,
            "training_performed": False,
            "upload_performed": False,
        },
        "schema_version": "treatment_safety_probe_receipt_v1",
        "source_views": {
            "faithful": artifact(faithful_path, records=len(faithful_rows)),
            "modern": artifact(modern_path, records=len(modern_rows)),
        },
        "split": {
            "key": "lineage.source_payload_id",
            "modulus": SPLIT_MODULUS,
            "namespace": SPLIT_NAMESPACE,
            "training_record_ids_sha256": _id_digest(training_ids),
            "training_records": len(training_ids),
            "validation_buckets": VALIDATION_BUCKETS,
            "validation_record_ids_sha256": _id_digest(validation_ids),
            "validation_records": len(validation_ids),
        },
    }
    validate_schema(receipt, PROBE_RECEIPT_SCHEMA, label="safety-probe receipt")
    write_atomic(receipt_path, (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return receipt


def _bound_artifacts(preregistration: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    by_role: dict[str, Mapping[str, Any]] = {}
    for binding in preregistration["artifacts"]:
        role = str(binding["role"])
        if role in by_role:
            raise TreatmentError(f"duplicate artifact role: {role}")
        by_role[role] = binding
    return by_role


def _verify_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    logical_path = str(binding["logical_path"])
    path = ROOT / logical_path
    if not path.is_file():
        raise TreatmentError(f"missing bound artifact: {logical_path}")
    actual = artifact(path, records=int(binding["records"]))
    if actual["bytes"] != binding["bytes"] or actual["sha256"] != binding["sha256"]:
        raise TreatmentError(f"artifact drift: {logical_path}")
    if logical_path.endswith(".jsonl"):
        records = sum(1 for line in path.open(encoding="utf-8") if line.strip())
        if records != binding["records"]:
            raise TreatmentError(f"record-count drift: {logical_path}")
    return {"role": binding["role"], **actual}


def preflight(
    preregistration_path: Path,
    authorization_path: Path | None = None,
    model_directory: Path | None = None,
) -> dict[str, Any]:
    preregistration = read_json(preregistration_path)
    validate_schema(preregistration, PREREG_SCHEMA, label="treatment preregistration")
    preregistration_sha256 = sha256_file(preregistration_path)
    artifacts = _bound_artifacts(preregistration)
    required_roles = {
        "production_receipt",
        "faithful_view",
        "faithful_view_receipt",
        "modern_view",
        "modern_view_receipt",
        "tokenizer_diagnostics",
        "heldout_evaluation_view",
        "heldout_manifest",
        "minimal_edit_prompt",
        "scoring_dispositions",
        "scoring_disposition_config",
        "safety_probe_receipt",
        "safety_probe_inventory",
        "model_snapshot_manifest",
    }
    if set(artifacts) != required_roles:
        raise TreatmentError(f"artifact roles differ from the frozen set: {sorted(set(artifacts) ^ required_roles)}")
    verified_artifacts = [_verify_binding(artifacts[role]) for role in sorted(artifacts)]

    production = read_json(ROOT / str(artifacts["production_receipt"]["logical_path"]))
    validate_schema(production, PRODUCTION_SCHEMA, label="model-ready production receipt")
    firewall = production["evaluation_firewall"]
    if firewall["state"] != "verified" or firewall["exact_overlap_count"] or firewall["near_overlap_count"]:
        raise TreatmentError("evaluation firewall is not clean")
    if production["continued_pretraining_views"]["faithful"]["artifact"]["sha256"] != artifacts["faithful_view"]["sha256"]:
        raise TreatmentError("faithful view is not the Phase 3 bound artifact")
    if production["continued_pretraining_views"]["modern"]["artifact"]["sha256"] != artifacts["modern_view"]["sha256"]:
        raise TreatmentError("modern view is not the Phase 3 bound artifact")
    if firewall["heldout_evaluation_view"]["artifact"]["sha256"] != artifacts["heldout_evaluation_view"]["sha256"]:
        raise TreatmentError("held-out evaluation binding drift")

    diagnostics = read_json(ROOT / str(artifacts["tokenizer_diagnostics"]["logical_path"]))
    validate_schema(diagnostics, TOKENIZER_SCHEMA, label="tokenizer diagnostics")
    if diagnostics["tokenizer"]["identifier"] != MODEL_IDENTIFIER or diagnostics["tokenizer"]["revision"] != MODEL_REVISION:
        raise TreatmentError("diagnostics are not for the frozen IT tokenizer")
    counters = diagnostics["metrics"]["mask_projection"]["counters"]
    if counters["projection_failures"] != 0 or counters["zero_loss_tokens"] <= 0:
        raise TreatmentError("tokenizer mask projection is unsafe")

    probe_receipt = read_json(ROOT / str(artifacts["safety_probe_receipt"]["logical_path"]))
    validate_schema(probe_receipt, PROBE_RECEIPT_SCHEMA, label="safety-probe receipt")
    if probe_receipt["source_views"]["faithful"]["sha256"] != artifacts["faithful_view"]["sha256"]:
        raise TreatmentError("safety probes do not bind the faithful view")
    if probe_receipt["source_views"]["modern"]["sha256"] != artifacts["modern_view"]["sha256"]:
        raise TreatmentError("safety probes do not bind the modern view")
    probe_output = artifacts["safety_probe_inventory"]
    if any(probe_receipt["output"][field] != probe_output[field] for field in ("bytes", "records", "sha256")):
        raise TreatmentError("safety-probe inventory does not match its receipt")

    model_snapshot = read_json(ROOT / str(artifacts["model_snapshot_manifest"]["logical_path"]))
    validate_schema(model_snapshot, MODEL_SNAPSHOT_SCHEMA, label="model snapshot manifest")
    if model_snapshot["identifier"] != preregistration["model"]["identifier"]:
        raise TreatmentError("model snapshot identifier mismatch")
    if model_snapshot["revision"] != preregistration["model"]["revision"]:
        raise TreatmentError("model snapshot revision mismatch")

    blockers = ["operator_authorization_pending", "immutable_model_snapshot_pending"]
    authorization_sha256: str | None = None
    if authorization_path is not None:
        authorization = read_json(authorization_path)
        validate_schema(authorization, AUTH_SCHEMA, label="treatment authorization")
        authorization_sha256 = sha256_file(authorization_path)
        if authorization["experiment_id"] != preregistration["experiment_id"]:
            raise TreatmentError("authorization experiment mismatch")
        if authorization["preregistration_sha256"] != preregistration_sha256:
            raise TreatmentError("authorization preregistration hash mismatch")
        if authorization["model"] != {
            "download_authorized": True,
            "identifier": preregistration["model"]["identifier"],
            "revision": preregistration["model"]["revision"],
        }:
            raise TreatmentError("authorization model mismatch")
        if authorization["ceilings"]["all_inclusive_usd"] > preregistration["compute"]["all_inclusive_ceiling_usd"]:
            raise TreatmentError("authorization exceeds the preregistered compute ceiling")
        blockers.remove("operator_authorization_pending")
    if model_directory is not None:
        for file_binding in model_snapshot["files"]:
            model_path = model_directory / str(file_binding["path"])
            if not model_path.is_file():
                raise TreatmentError(f"model snapshot file missing: {file_binding['path']}")
            if model_path.stat().st_size != file_binding["bytes"] or sha256_file(model_path) != file_binding["sha256"]:
                raise TreatmentError(f"model snapshot file drift: {file_binding['path']}")
        blockers.remove("immutable_model_snapshot_pending")

    receipt = {
        "authorization_sha256": authorization_sha256,
        "blockers": blockers,
        "decision": "REVISE" if blockers else "PROCEED",
        "experiment_id": preregistration["experiment_id"],
        "preregistration_ready": True,
        "preregistration_sha256": preregistration_sha256,
        "safety": {
            "model_call_performed": False,
            "publication_performed": False,
            "training_performed": False,
            "upload_performed": False,
        },
        "schema_version": "treatment_stage0_preflight_v1",
        "verified_artifacts": verified_artifacts,
        "verified_conditions": [
            "phase3_model_ready_views",
            "exact_it_tokenizer_mask_projection",
            "evaluation_firewall",
            "common_training_validation_split",
            "deterministic_non_human_safety_inventory",
            "paired_arm_contract",
            "bounded_compute_ladder",
        ],
    }
    validate_schema(receipt, PREFLIGHT_SCHEMA, label="treatment Stage 0 preflight")
    return receipt


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    probes = subparsers.add_parser("build-probes")
    probes.add_argument("--faithful-view", type=Path, required=True)
    probes.add_argument("--modern-view", type=Path, required=True)
    probes.add_argument("--output", type=Path, required=True)
    probes.add_argument("--receipt", type=Path, required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--preregistration", type=Path, required=True)
    preflight_parser.add_argument("--authorization", type=Path)
    preflight_parser.add_argument("--model-directory", type=Path)
    preflight_parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "build-probes":
            result = build_safety_probes(
                faithful_path=args.faithful_view,
                modern_path=args.modern_view,
                output_path=args.output,
                receipt_path=args.receipt,
            )
        else:
            result = preflight(args.preregistration, args.authorization, args.model_directory)
            if args.output:
                write_atomic(
                    args.output,
                    (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
                )
        print(canonical_json(result))
    except TreatmentError as exc:
        print(f"treatment preparation failed: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
