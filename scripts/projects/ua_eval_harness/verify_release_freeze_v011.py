#!/usr/bin/env python3
"""Build or verify the immutable public UA evaluation release 0.1.1 freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.ua_eval_harness import verify_release_freeze as v010
from scripts.projects.ua_eval_harness.evaluate_model import (
    import_model_responses,
    load_manifest,
    load_saved_responses,
    score_saved_run,
)
from scripts.projects.ua_eval_harness.run_model_batch import (
    load_run_config,
    load_source_only_packet,
)

SCHEMA_VERSION = "ua_eval_release_freeze.v2"
RELEASE_VERSION = "0.1.1"
RELEASE_ID = "ua-gec-calque-grammar-public-v0"
RELEASE_URL = (
    "https://github.com/learn-ukrainian/learn-ukrainian.github.io/"
    "releases/tag/0.1.1"
)
DEFAULT_OUTPUT = (
    ROOT
    / "data/projects/ua_eval_harness/releases/v0.1.1/freeze_manifest.json"
)
DEFAULT_SPLIT_OUTPUT = (
    ROOT
    / "data/projects/ua_eval_harness/releases/v0.1.1/split_integrity.json"
)
V010_FREEZE = Path(
    "data/projects/ua_eval_harness/releases/v0.1.0/freeze_manifest.json"
)
V010_SPLIT = Path(
    "data/projects/ua_eval_harness/releases/v0.1.0/split_integrity.json"
)
V010_FREEZE_SHA256 = (
    "b88765eec0d8cfe08fd98fca2bd01d47c4fe284d4c23c1e0c980a9040a808800"
)
V010_SPLIT_SHA256 = (
    "c10b1bba913364aff6ad0c0d9cbbafa9b611b3fb733a94e7fe73081be4b5b7c5"
)
HELDOUT_MANIFEST = Path("data/projects/ua_eval_harness/heldout_manifest_v1.json")
HELDOUT_CONFIG = Path("data/projects/ua_eval_harness/heldout_manifest_config.json")
PROMPT = Path("data/projects/ua_eval_harness/minimal_edit_prompt_v1.txt")
REQUESTS = Path(
    "data/projects/ua_eval_harness/baselines/v1/generation_requests.jsonl"
)
VESUM_LOCK = Path("scripts/config/vesum_source.lock.json")
V011_SPLIT = Path(
    "data/projects/ua_eval_harness/releases/v0.1.1/split_integrity.json"
)
V2_BASELINE = Path("data/projects/ua_eval_harness/baselines/v2")
GEMMA_STEM = "gemma-4-31b-it"
GEMMA_PATHS = {
    "failed_attempts": V2_BASELINE / f"{GEMMA_STEM}.failed-attempts.jsonl",
    "metadata": V2_BASELINE / f"{GEMMA_STEM}.metadata.json",
    "model_output": V2_BASELINE / f"{GEMMA_STEM}.model-output.jsonl",
    "raw_output": V2_BASELINE / f"{GEMMA_STEM}.raw-provider-output.jsonl",
    "report": V2_BASELINE / f"{GEMMA_STEM}.report.json",
    "responses": V2_BASELINE / f"{GEMMA_STEM}.responses.jsonl",
    "run_config": V2_BASELINE / f"{GEMMA_STEM}.run-config.json",
}
EXPECTED_REQUEST_COUNT = 677
EXPECTED_BATCH_COUNT = 34
EXPECTED_FAILED_ATTEMPTS = 2
EXPECTED_GEMMA_MODEL = "google/gemma-4-31b-it"
EXPECTED_GEMMA_PROVIDER = "OpenRouter"
EXPECTED_PACKET_SHA256 = (
    "77afe3da4ea590e060602af53b60ac8f350369f8a323521dee99f42100815fca"
)
EXPECTED_PROMPT_SHA256 = (
    "f121546dcbaf602c58c7d85977ad792eb9be402dd1e01a6a556ba966dac2c96a"
)
EXPECTED_GEMMA_METRICS = {
    "edit_precision": 0.24516129032258063,
    "edit_recall": 0.10477941176470588,
    "edit_f0_5": 0.19335142469470828,
    "headline_calque_recall": 0.09523809523809523,
    "exact_sentence_accuracy": 0.10782865583456426,
    "exact_sentence_correct": 73,
}

HISTORICAL_ARTIFACTS: tuple[tuple[Path, str], ...] = tuple(
    (path, f"v0.1.0_{role}") for path, role in v010.FROZEN_ARTIFACTS
)
V011_ARTIFACTS: tuple[tuple[Path, str], ...] = (
    (V010_FREEZE, "v0.1.0_release_manifest"),
    (
        Path("scripts/projects/ua_eval_harness/verify_release_freeze.py"),
        "v0.1.0_compatibility_verifier",
    ),
    (V011_SPLIT, "v0.1.1_upstream_split_integrity_receipt"),
    (Path("docs/projects/ua-eval-harness/README.md"), "public_package_guide"),
    (
        Path("docs/projects/ua-eval-harness/DATA_CARD.en.md"),
        "public_data_card",
    ),
    (
        Path("docs/projects/ua-eval-harness/RELEASE_NOTES.md"),
        "public_release_notes",
    ),
    (
        Path("docs/projects/ua-eval-harness/REPRODUCING.md"),
        "public_reproduction_guide",
    ),
    (
        Path("docs/projects/ua-eval-harness/THIRD_PARTY_NOTICES.md"),
        "public_third_party_notices",
    ),
    (
        Path("docs/projects/ua-eval-harness/contamination-policy.md"),
        "public_contamination_policy",
    ),
    (
        Path("scripts/projects/ua_eval_harness/run_model_batch.py"),
        "provider_neutral_model_runner",
    ),
    (
        Path("data/projects/ua_eval_harness/model_run_config_schema_v1.json"),
        "provider_neutral_run_config_schema",
    ),
    (
        Path("data/projects/ua_eval_harness/model_run_config.example.json"),
        "provider_neutral_run_config_example",
    ),
    (V2_BASELINE / "README.md", "gemma_baseline_guide"),
    (GEMMA_PATHS["failed_attempts"], "gemma_rejected_attempt_evidence"),
    (GEMMA_PATHS["metadata"], "gemma_generation_metadata"),
    (GEMMA_PATHS["model_output"], "gemma_normalized_model_output"),
    (GEMMA_PATHS["raw_output"], "gemma_successful_raw_provider_output"),
    (GEMMA_PATHS["report"], "gemma_aggregate_report"),
    (GEMMA_PATHS["responses"], "gemma_saved_responses"),
    (GEMMA_PATHS["run_config"], "gemma_run_configuration"),
    (
        Path(
            "scripts/projects/ua_eval_harness/"
            "verify_release_freeze_v011.py"
        ),
        "v0.1.1_release_verifier",
    ),
    (
        Path("scripts/projects/ua_eval_harness/smoke_public_v011.py"),
        "v0.1.1_public_smoke_test",
    ),
    (
        Path("tests/test_ua_eval_public_v011.py"),
        "v0.1.1_smoke_regression_test",
    ),
)
FROZEN_ARTIFACTS = HISTORICAL_ARTIFACTS + V011_ARTIFACTS


class FreezeError(ValueError):
    """A release receipt or frozen artifact is invalid."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreezeError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FreezeError(f"expected JSON object in {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FreezeError(f"cannot read JSONL {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        if not line:
            raise FreezeError(f"blank JSONL line at {path}:{line_number}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FreezeError(
                f"invalid JSONL at {path}:{line_number}: {exc}"
            ) from exc
        if not isinstance(row, dict):
            raise FreezeError(f"expected object at {path}:{line_number}")
        rows.append(row)
    if not rows:
        raise FreezeError(f"empty JSONL file: {path}")
    return rows


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise FreezeError(f"cannot hash {path}: {exc}") from exc


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _artifact(path: Path, role: str) -> dict[str, str]:
    return {
        "path": path.as_posix(),
        "role": role,
        "sha256": _sha256(ROOT / path),
    }


def _validated_v010_freeze() -> dict[str, Any]:
    if _sha256(ROOT / V010_FREEZE) != V010_FREEZE_SHA256:
        raise FreezeError("v0.1.0 release manifest bytes changed")
    if _sha256(ROOT / V010_SPLIT) != V010_SPLIT_SHA256:
        raise FreezeError("v0.1.0 split receipt bytes changed")
    freeze = _read_json(ROOT / V010_FREEZE)
    try:
        v010.validate_freeze(freeze)
    except ValueError as exc:
        raise FreezeError(f"v0.1.0 freeze validation failed: {exc}") from exc
    return freeze


def build_split_receipt() -> dict[str, Any]:
    """Derive the 0.1.1 split receipt from the validated historical split."""
    heldout = _read_json(ROOT / HELDOUT_MANIFEST)
    config = _read_json(ROOT / HELDOUT_CONFIG)
    historical = _read_json(ROOT / V010_SPLIT)
    try:
        v010.validate_split_receipt(
            historical,
            heldout=heldout,
            config=config,
        )
    except ValueError as exc:
        raise FreezeError(f"historical split validation failed: {exc}") from exc
    return {**historical, "release_version": RELEASE_VERSION}


def validate_split_receipt(receipt: Mapping[str, Any]) -> dict[str, int]:
    """Validate the 0.1.1 receipt against the unchanged benchmark split."""
    if receipt.get("release_version") != RELEASE_VERSION:
        raise FreezeError("v0.1.1 split receipt release version mismatch")
    historical_shape = {**receipt, "release_version": v010.RELEASE_VERSION}
    heldout = _read_json(ROOT / HELDOUT_MANIFEST)
    config = _read_json(ROOT / HELDOUT_CONFIG)
    try:
        return v010.validate_split_receipt(
            historical_shape,
            heldout=heldout,
            config=config,
        )
    except ValueError as exc:
        raise FreezeError(f"v0.1.1 split validation failed: {exc}") from exc


def _validate_gemma_baseline() -> dict[str, Any]:
    try:
        packet_header, requests, packet_sha256 = load_source_only_packet(
            ROOT / REQUESTS
        )
        run_config = load_run_config(ROOT / GEMMA_PATHS["run_config"])
    except ValueError as exc:
        raise FreezeError(f"Gemma source-only contract failed: {exc}") from exc
    if packet_sha256 != EXPECTED_PACKET_SHA256:
        raise FreezeError("Gemma request packet receipt drift")
    if packet_header["prompt_sha256"] != EXPECTED_PROMPT_SHA256:
        raise FreezeError("Gemma prompt receipt drift")
    if len(requests) != EXPECTED_REQUEST_COUNT:
        raise FreezeError("Gemma request count mismatch")
    expected_ids = [row["item_id"] for row in requests]

    metadata = _read_json(ROOT / GEMMA_PATHS["metadata"])
    if metadata.get("schema_version") != "ua_eval_model_run_metadata.v1":
        raise FreezeError("Gemma metadata schema mismatch")
    for field in ("run_id", "provider", "model", "model_version", "decoding"):
        if metadata.get(field) != run_config.get(field):
            raise FreezeError(f"Gemma metadata/config mismatch: {field}")
    if (
        metadata.get("provider") != EXPECTED_GEMMA_PROVIDER
        or metadata.get("model") != EXPECTED_GEMMA_MODEL
    ):
        raise FreezeError("Gemma provider or model identity mismatch")
    if run_config.get("auth_environment") != []:
        raise FreezeError("published Gemma config must not name credentials")

    generation = metadata.get("generation_metadata")
    if not isinstance(generation, Mapping):
        raise FreezeError("Gemma generation metadata is missing")
    required_generation = {
        "response_count": EXPECTED_REQUEST_COUNT,
        "request_packet_sha256": EXPECTED_PACKET_SHA256,
        "prompt_sha256": EXPECTED_PROMPT_SHA256,
        "batch_size": 20,
        "workers": 1,
        "transport_protocol": "tagged_text_blocks.v1",
        "gold_fields_supplied": [],
    }
    for field, expected in required_generation.items():
        if generation.get(field) != expected:
            raise FreezeError(f"Gemma generation receipt mismatch: {field}")
    if generation.get("config_sha256") != _sha256_text(
        _canonical_json(run_config)
    ):
        raise FreezeError("Gemma canonical run-config receipt mismatch")

    batch_receipts = generation.get("batch_receipts")
    if not isinstance(batch_receipts, list) or len(batch_receipts) != (
        EXPECTED_BATCH_COUNT
    ):
        raise FreezeError("Gemma batch receipt count mismatch")
    if [row.get("batch_index") for row in batch_receipts] != list(
        range(EXPECTED_BATCH_COUNT)
    ):
        raise FreezeError("Gemma batch receipt order mismatch")
    retries = generation.get("retry_counts")
    if not isinstance(retries, Mapping):
        raise FreezeError("Gemma retry receipt is missing")
    if sum(int(value) for value in retries.values()) != (
        EXPECTED_FAILED_ATTEMPTS
    ):
        raise FreezeError("Gemma retry total mismatch")

    model_output_rows = _read_jsonl(ROOT / GEMMA_PATHS["model_output"])
    if [row.get("item_id") for row in model_output_rows] != expected_ids:
        raise FreezeError("Gemma normalized outputs do not match packet order")
    if any(set(row) != {"item_id", "raw_response"} for row in model_output_rows):
        raise FreezeError("Gemma normalized output has unsupported fields")
    if generation.get("model_output_sha256") != _sha256(
        ROOT / GEMMA_PATHS["model_output"]
    ):
        raise FreezeError("Gemma normalized-output hash mismatch")

    raw_rows = _read_jsonl(ROOT / GEMMA_PATHS["raw_output"])
    if len(raw_rows) != EXPECTED_BATCH_COUNT:
        raise FreezeError("Gemma raw successful batch count mismatch")
    if [row.get("batch_index") for row in raw_rows] != list(
        range(EXPECTED_BATCH_COUNT)
    ):
        raise FreezeError("Gemma raw successful batch order mismatch")
    if generation.get("raw_output_sha256") != _sha256(
        ROOT / GEMMA_PATHS["raw_output"]
    ):
        raise FreezeError("Gemma raw-output hash mismatch")

    failed_rows = _read_jsonl(ROOT / GEMMA_PATHS["failed_attempts"])
    failed_receipts = generation.get("failed_attempts")
    if (
        not isinstance(failed_receipts, list)
        or len(failed_rows) != EXPECTED_FAILED_ATTEMPTS
        or len(failed_receipts) != EXPECTED_FAILED_ATTEMPTS
    ):
        raise FreezeError("Gemma failed-attempt evidence count mismatch")
    for published, receipt in zip(failed_rows, failed_receipts, strict=True):
        retained = {
            key: value
            for key, value in published.items()
            if key not in {"raw_provider_output", "provider_stderr"}
        }
        if retained != receipt:
            raise FreezeError("Gemma failed-attempt receipt mismatch")
        if _sha256_text(str(published["raw_provider_output"])) != (
            receipt["stdout_sha256"]
        ):
            raise FreezeError("Gemma failed-attempt stdout hash mismatch")
        if _sha256_text(str(published["provider_stderr"])) != (
            receipt["stderr_sha256"]
        ):
            raise FreezeError("Gemma failed-attempt stderr hash mismatch")

    manifest, items = load_manifest(ROOT / HELDOUT_MANIFEST)
    try:
        saved_header, saved_responses = load_saved_responses(
            ROOT / GEMMA_PATHS["responses"],
            manifest=manifest,
            items=items,
        )
    except ValueError as exc:
        raise FreezeError(f"Gemma saved-response validation failed: {exc}") from exc
    if list(saved_responses) != expected_ids:
        raise FreezeError("Gemma saved responses do not match packet order")
    if saved_header.get("generation_metadata") != generation:
        raise FreezeError("Gemma saved-response generation receipt mismatch")
    if saved_header.get("gold_fields_supplied") != []:
        raise FreezeError("Gemma saved responses declare supplied gold fields")
    if saved_header.get("input_fields") != [
        "item_id",
        "source",
        "source_sha256",
        "prompt_sha256",
    ]:
        raise FreezeError("Gemma saved-response inputs violate the gold firewall")

    try:
        imported = import_model_responses(
            requests_path=ROOT / REQUESTS,
            model_output_path=ROOT / GEMMA_PATHS["model_output"],
            metadata_path=ROOT / GEMMA_PATHS["metadata"],
        )
    except ValueError as exc:
        raise FreezeError(f"Gemma import reproduction failed: {exc}") from exc
    imported_text = "".join(_canonical_json(row) + "\n" for row in imported)
    if imported_text != (ROOT / GEMMA_PATHS["responses"]).read_text(
        encoding="utf-8"
    ):
        raise FreezeError("Gemma imported responses are not byte-reproducible")

    report = _read_json(ROOT / GEMMA_PATHS["report"])
    try:
        reproduced = score_saved_run(GEMMA_PATHS["responses"])
    except ValueError as exc:
        raise FreezeError(f"Gemma scoring reproduction failed: {exc}") from exc
    if report != reproduced:
        raise FreezeError("Gemma aggregate report is not reproducible")
    edit = report["edit_correction"]
    headline = report["headline_calque"]
    exact = report["exact_sentence"]
    observed_metrics = {
        "edit_precision": edit["precision"],
        "edit_recall": edit["recall"],
        "edit_f0_5": edit["f0_5"],
        "headline_calque_recall": headline["recall"],
        "exact_sentence_accuracy": exact["accuracy"],
        "exact_sentence_correct": exact["correct"],
    }
    if observed_metrics != EXPECTED_GEMMA_METRICS:
        raise FreezeError("Gemma frozen metrics changed")
    if exact["total"] != EXPECTED_REQUEST_COUNT:
        raise FreezeError("Gemma scored response count mismatch")

    return {
        "provider": metadata["provider"],
        "route": generation["route"],
        "model": metadata["model"],
        "model_version": metadata["model_version"],
        "run_id": metadata["run_id"],
        "runner_version": metadata["runner_version"],
        "request_count": EXPECTED_REQUEST_COUNT,
        "request_packet_sha256": packet_sha256,
        "prompt_sha256": packet_header["prompt_sha256"],
        "batch_count": EXPECTED_BATCH_COUNT,
        "failed_attempt_count": EXPECTED_FAILED_ATTEMPTS,
        "gold_fields_supplied": [],
        "saved_response_path": GEMMA_PATHS["responses"].as_posix(),
        "saved_response_sha256": _sha256(ROOT / GEMMA_PATHS["responses"]),
        "report_path": GEMMA_PATHS["report"].as_posix(),
        "report_sha256": _sha256(ROOT / GEMMA_PATHS["report"]),
        "metrics": observed_metrics,
    }


def build_freeze() -> dict[str, Any]:
    """Build the 0.1.1 receipt from the exact public release artifacts."""
    historical = _validated_v010_freeze()
    split_receipt = _read_json(ROOT / V011_SPLIT)
    split = validate_split_receipt(split_receipt)
    gemma = _validate_gemma_baseline()
    vesum = _read_json(ROOT / VESUM_LOCK)["release_asset"]
    return {
        "schema_version": SCHEMA_VERSION,
        "release": {
            "id": RELEASE_ID,
            "version": RELEASE_VERSION,
            "status": "immutable",
            "release_url": RELEASE_URL,
        },
        "compatibility": {
            "previous_version": "0.1.0",
            "previous_freeze_path": V010_FREEZE.as_posix(),
            "previous_freeze_sha256": V010_FREEZE_SHA256,
            "previous_artifact_count": len(v010.FROZEN_ARTIFACTS),
            "dataset_task_scorer_and_v0.1.0_results": "unchanged",
        },
        "task_contract": historical["task_contract"],
        "upstream": historical["upstream"],
        "split_integrity": {
            "receipt_path": V011_SPLIT.as_posix(),
            "receipt_sha256": _sha256(ROOT / V011_SPLIT),
            "train_documents": split["train_documents"],
            "test_documents": split["test_documents"],
            "train_authors": split["train_authors"],
            "test_authors": split["test_authors"],
            "train_test_document_overlap": split[
                "train_test_document_overlap"
            ],
            "train_test_author_overlap": split["train_test_author_overlap"],
            "included_sentences": EXPECTED_REQUEST_COUNT,
        },
        "vesum": {
            "project": vesum["project"],
            "version": vesum["version"],
            "upstream_commit": vesum["upstream_commit"],
            "asset_url": vesum["url"],
            "asset_size_bytes": vesum["size_bytes"],
            "asset_sha256": vesum["sha256"],
            "retrieved": "2026-07-30",
            "license": vesum["license"],
        },
        "provider_neutral_workflow": {
            "runner": (
                "scripts/projects/ua_eval_harness/run_model_batch.py"
            ),
            "config_schema": (
                "data/projects/ua_eval_harness/"
                "model_run_config_schema_v1.json"
            ),
            "config_example": (
                "data/projects/ua_eval_harness/"
                "model_run_config.example.json"
            ),
            "generation_and_scoring_are_separate": True,
            "complete_coverage_required": EXPECTED_REQUEST_COUNT,
        },
        "baselines": {
            "historical_saved_runs": 3,
            "historical_results_version": "0.1.0",
            "gemma_4_reference": gemma,
            "total_saved_runs": 4,
        },
        "reporting": {
            "aggregate_reports_exclude_item_content": True,
            "generation_evidence_is_stored_separately": True,
            "raw_successful_output_is_separate": True,
            "rejected_attempt_evidence_is_separate": True,
        },
        "artifacts": [
            _artifact(path, role) for path, role in FROZEN_ARTIFACTS
        ],
        "version_policy": {
            "in_place_edits": "forbidden",
            "historical_freezes": "retained and independently verifiable",
            "any_frozen_byte_change": (
                "requires a new semantic version and freeze directory"
            ),
        },
    }


def validate_freeze(freeze: Mapping[str, Any]) -> None:
    """Fail closed if metadata is stale or any frozen byte drifted."""
    if freeze.get("schema_version") != SCHEMA_VERSION:
        raise FreezeError("unsupported v0.1.1 freeze schema")
    release = freeze.get("release")
    if (
        not isinstance(release, Mapping)
        or release.get("id") != RELEASE_ID
        or release.get("version") != RELEASE_VERSION
        or release.get("status") != "immutable"
    ):
        raise FreezeError("v0.1.1 release identity mismatch")
    artifacts = freeze.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != len(
        FROZEN_ARTIFACTS
    ):
        raise FreezeError("v0.1.1 artifact inventory mismatch")
    expected = {
        path.as_posix(): role for path, role in FROZEN_ARTIFACTS
    }
    actual: dict[str, str] = {}
    for artifact in artifacts:
        if not isinstance(artifact, Mapping):
            raise FreezeError("invalid v0.1.1 artifact receipt")
        path = str(artifact.get("path", ""))
        role = str(artifact.get("role", ""))
        if path in actual or expected.get(path) != role:
            raise FreezeError(f"unexpected v0.1.1 artifact receipt: {path}")
        if artifact.get("sha256") != _sha256(ROOT / path):
            raise FreezeError(f"frozen artifact hash mismatch: {path}")
        actual[path] = role
    if actual != expected:
        raise FreezeError("v0.1.1 frozen artifact paths do not match")
    rebuilt = build_freeze()
    if freeze != rebuilt:
        raise FreezeError("v0.1.1 freeze metadata is stale or edited in place")


def _write_versioned_receipt(
    path: Path,
    value: Mapping[str, Any],
) -> None:
    if path.parent.name != f"v{RELEASE_VERSION}":
        raise FreezeError(
            f"freeze path does not match release {RELEASE_VERSION}: {path}"
        )
    serialized = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise FreezeError(f"cannot read existing receipt {path}: {exc}") from exc
        if existing != serialized:
            raise FreezeError(
                f"refusing to overwrite immutable v{RELEASE_VERSION} "
                f"receipt {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--split-receipt",
        type=Path,
        default=DEFAULT_SPLIT_OUTPUT,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--write-split-receipt", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write_split_receipt:
            receipt = build_split_receipt()
            _write_versioned_receipt(args.split_receipt, receipt)
            print(
                "UA evaluation v0.1.1 split receipt valid: "
                f"{len(receipt['train_document_ids'])} train documents, "
                f"{len(receipt['test_document_ids'])} test documents"
            )
            return 0
        if args.write:
            freeze = build_freeze()
            _write_versioned_receipt(args.freeze, freeze)
        else:
            freeze = _read_json(args.freeze)
            validate_freeze(freeze)
        print(
            f"UA evaluation freeze valid: {freeze['release']['id']} "
            f"v{freeze['release']['version']}, "
            f"{len(freeze['artifacts'])} artifacts"
        )
        return 0
    except (FreezeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
