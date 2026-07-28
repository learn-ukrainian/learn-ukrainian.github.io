#!/usr/bin/env python3
"""Build or verify the immutable public UA evaluation release freeze."""

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

from scripts.projects.ua_eval_harness.build_heldout_manifest import (
    load_metadata,
    parse_m2,
    validate_manifest,
    verify_upstream,
)
from scripts.projects.ua_eval_harness.evaluate_model import load_manifest, load_saved_responses

SCHEMA_VERSION = "ua_eval_release_freeze.v1"
RELEASE_VERSION = "0.1.0"
DEFAULT_OUTPUT = ROOT / "data/projects/ua_eval_harness/releases/v0.1.0/freeze_manifest.json"
DEFAULT_SPLIT_OUTPUT = ROOT / "data/projects/ua_eval_harness/releases/v0.1.0/split_integrity.json"
DEFAULT_UA_GEC_ROOT = ROOT / "data/ua-gec"
HELDOUT_MANIFEST = Path("data/projects/ua_eval_harness/heldout_manifest_v1.json")
HELDOUT_CONFIG = Path("data/projects/ua_eval_harness/heldout_manifest_config.json")
SPLIT_RECEIPT = Path("data/projects/ua_eval_harness/releases/v0.1.0/split_integrity.json")
DEV_FIXTURES = Path("data/projects/ua_eval_harness/evalset_v1.jsonl")
PROMPT = Path("data/projects/ua_eval_harness/minimal_edit_prompt_v1.txt")
OUTPUT_SCHEMA = Path("data/projects/ua_eval_harness/model_output_schema_v1.json")
EVALUATOR = Path("scripts/projects/ua_eval_harness/evaluate_model.py")
EXTRACTOR = Path("scripts/projects/ua_eval_harness/build_heldout_manifest.py")
RUNNER = Path("scripts/projects/ua_eval_harness/run_codex_baseline.py")
BASELINE_DIR = Path("data/projects/ua_eval_harness/baselines/v1")
RESPONSE_FILES = (
    BASELINE_DIR / "identity.responses.jsonl",
    BASELINE_DIR / "fixture-rules.responses.jsonl",
    BASELINE_DIR / "gpt-5.6-terra.responses.jsonl",
)
REPORT_FILES = (
    BASELINE_DIR / "identity.report.json",
    BASELINE_DIR / "fixture-rules.report.json",
    BASELINE_DIR / "gpt-5.6-terra.report.json",
)
FROZEN_ARTIFACTS: tuple[tuple[Path, str], ...] = (
    (HELDOUT_CONFIG, "dataset_configuration"),
    (HELDOUT_MANIFEST, "heldout_gold_manifest"),
    (SPLIT_RECEIPT, "upstream_split_integrity_receipt"),
    (DEV_FIXTURES, "development_fixture_excluded_from_results"),
    (PROMPT, "task_instruction"),
    (OUTPUT_SCHEMA, "model_output_contract"),
    (EXTRACTOR, "dataset_extractor"),
    (EVALUATOR, "saved_response_scorer"),
    (RUNNER, "optional_live_model_runner"),
    (BASELINE_DIR / "generation_requests.jsonl", "source_only_generation_requests"),
    (RESPONSE_FILES[0], "identity_saved_responses"),
    (REPORT_FILES[0], "identity_aggregate_report"),
    (RESPONSE_FILES[1], "deterministic_saved_responses"),
    (REPORT_FILES[1], "deterministic_aggregate_report"),
    (RESPONSE_FILES[2], "real_model_saved_responses"),
    (REPORT_FILES[2], "real_model_aggregate_report"),
)
REPORT_FORBIDDEN_KEYS = frozenset(
    {
        "item_id",
        "source_sha256",
        "target",
        "target_sha256",
        "reference",
        "references",
        "raw_response",
        "response_sha256",
        "edit",
        "edits",
        "exclusions",
    }
)


class FreezeError(ValueError):
    """A release freeze or one of its pinned artifacts is invalid."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreezeError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FreezeError(f"expected JSON object in {path}")
    return value


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise FreezeError(f"cannot hash {path}: {exc}") from exc


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FreezeError(f"cannot read JSONL {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FreezeError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise FreezeError(f"expected object at {path}:{line_number}")
        rows.append(row)
    if not rows:
        raise FreezeError(f"empty JSONL file: {path}")
    return rows


def _artifact(path: Path, role: str) -> dict[str, str]:
    return {"path": path.as_posix(), "role": role, "sha256": _sha256(ROOT / path)}


def build_split_receipt(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    """Derive exact train/test document and author sets from pinned UA-GEC."""
    try:
        verify_upstream(root, config)
        metadata, train_authors, test_authors = load_metadata(root / "data/metadata.csv")
        test_sentences = parse_m2(root / "data/gec-fluency/test/gec-fluency.test.m2")
    except ValueError as exc:
        raise FreezeError(f"cannot build split receipt: {exc}") from exc
    train_documents = sorted(doc_id for doc_id, row in metadata.items() if row["partition"] == "train")
    test_documents = sorted(doc_id for doc_id, row in metadata.items() if row["partition"] == "test")
    m2_documents = {sentence.doc_id for sentence in test_sentences}
    if set(test_documents) != m2_documents:
        raise FreezeError("upstream test M2 documents do not match metadata")
    if set(train_documents) & set(test_documents):
        raise FreezeError("upstream train/test document overlap detected")
    if train_authors & test_authors:
        raise FreezeError("upstream train/test author overlap detected")
    upstream = config["upstream"]
    return {
        "schema_version": "ua_eval_split_integrity.v1",
        "release_version": RELEASE_VERSION,
        "upstream_commit": upstream["commit"],
        "metadata_sha256": upstream["files"]["data/metadata.csv"],
        "test_m2_sha256": upstream["files"]["data/gec-fluency/test/gec-fluency.test.m2"],
        "train_document_ids": train_documents,
        "test_document_ids": test_documents,
        "train_author_ids": sorted(train_authors),
        "test_author_ids": sorted(test_authors),
    }


def _validated_id_set(receipt: Mapping[str, Any], field: str) -> set[str]:
    values = receipt.get(field)
    if not isinstance(values, list) or not values or any(not isinstance(value, str) or not value for value in values):
        raise FreezeError(f"invalid split receipt field: {field}")
    if values != sorted(values) or len(values) != len(set(values)):
        raise FreezeError(f"split receipt field is not sorted and unique: {field}")
    return set(values)


def validate_split_receipt(
    receipt: Mapping[str, Any],
    *,
    heldout: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, int]:
    """Prove the pinned upstream split is writer- and document-disjoint."""
    if receipt.get("schema_version") != "ua_eval_split_integrity.v1":
        raise FreezeError("unsupported split receipt schema")
    if receipt.get("release_version") != RELEASE_VERSION:
        raise FreezeError("split receipt release version mismatch")
    upstream = config["upstream"]
    if receipt.get("upstream_commit") != upstream["commit"]:
        raise FreezeError("split receipt upstream commit mismatch")
    if receipt.get("metadata_sha256") != upstream["files"]["data/metadata.csv"]:
        raise FreezeError("split receipt metadata hash mismatch")
    if receipt.get("test_m2_sha256") != upstream["files"]["data/gec-fluency/test/gec-fluency.test.m2"]:
        raise FreezeError("split receipt test M2 hash mismatch")
    train_documents = _validated_id_set(receipt, "train_document_ids")
    test_documents = _validated_id_set(receipt, "test_document_ids")
    train_authors = _validated_id_set(receipt, "train_author_ids")
    test_authors = _validated_id_set(receipt, "test_author_ids")
    document_overlap = len(train_documents & test_documents)
    author_overlap = len(train_authors & test_authors)
    if document_overlap or author_overlap:
        raise FreezeError("split receipt contains train/test overlap")
    manifest_documents = {str(row[1]) for row in [*heldout["items"], *heldout["exclusions"]]}
    if test_documents != manifest_documents:
        raise FreezeError("split receipt test documents do not match the held-out manifest")
    counts = heldout["counts"]
    if len(test_documents) != counts["upstream_test_documents"]:
        raise FreezeError("split receipt test document count mismatch")
    if len(test_authors) != counts["upstream_test_authors"]:
        raise FreezeError("split receipt test author count mismatch")
    if len(train_authors) != counts["upstream_train_authors"]:
        raise FreezeError("split receipt train author count mismatch")
    return {
        "train_documents": len(train_documents),
        "test_documents": len(test_documents),
        "train_authors": len(train_authors),
        "test_authors": len(test_authors),
        "train_test_document_overlap": document_overlap,
        "train_test_author_overlap": author_overlap,
    }


def _forbidden_report_keys(value: Any, *, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in REPORT_FORBIDDEN_KEYS:
                findings.append(child_path)
            findings.extend(_forbidden_report_keys(child, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_forbidden_report_keys(child, path=f"{path}[{index}]"))
    return findings


def _validate_reports_do_not_expose_items(
    heldout: Mapping[str, Any],
    reports: Sequence[Mapping[str, Any]],
) -> None:
    item_ids = {str(row[0]) for row in heldout["items"]}
    protected_texts = {str(row[8]) for row in heldout["items"]}
    protected_texts.update(str(reference[1]) for row in heldout["items"] for reference in row[12])
    protected_hashes = {str(row[9]) for row in heldout["items"]}
    protected_hashes.update(str(row[3]) for row in heldout["exclusions"])
    protected_hashes.update(str(reference[2]) for row in heldout["items"] for reference in row[12])
    for report_path, report in zip(REPORT_FILES, reports, strict=True):
        forbidden = _forbidden_report_keys(report)
        if forbidden:
            raise FreezeError(f"aggregate report exposes item fields: {report_path}: {forbidden[0]}")
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
        if any(item_id in serialized for item_id in item_ids):
            raise FreezeError(f"aggregate report exposes held-out item IDs: {report_path}")
        if any(text in serialized for text in protected_texts):
            raise FreezeError(f"aggregate report exposes held-out source or target text: {report_path}")
        if any(receipt in serialized for receipt in protected_hashes):
            raise FreezeError(f"aggregate report exposes protected content hashes: {report_path}")


def _run_receipt(report: Mapping[str, Any]) -> dict[str, Any]:
    saved = report["saved_run"]
    return {
        "run_id": saved["run_id"],
        "generator_kind": saved["generator_kind"],
        "provider": saved["provider"],
        "model": saved["model"],
        "model_version": saved["model_version"],
        "decoding": saved["decoding"],
        "runner": saved["runner"],
        "runner_version": saved["runner_version"],
        "prompt_sha256": saved["prompt_sha256"],
        "saved_response_path": saved["path"],
        "saved_response_sha256": saved["sha256"],
        "gold_fields_supplied": saved["gold_fields_supplied"],
    }


def build_freeze() -> dict[str, Any]:
    """Build a freeze receipt from the exact committed public artifacts."""
    heldout = _read_json(ROOT / HELDOUT_MANIFEST)
    config = _read_json(ROOT / HELDOUT_CONFIG)
    split_receipt = _read_json(ROOT / SPLIT_RECEIPT)
    development_fixtures = _read_jsonl(ROOT / DEV_FIXTURES)
    try:
        validate_manifest(heldout)
    except ValueError as exc:
        raise FreezeError(f"held-out manifest validation failed: {exc}") from exc
    split = validate_split_receipt(split_receipt, heldout=heldout, config=config)
    reports = [_read_json(ROOT / path) for path in REPORT_FILES]
    _validate_reports_do_not_expose_items(heldout, reports)
    expanded_manifest, expanded_items = load_manifest(ROOT / HELDOUT_MANIFEST)
    for response_path in RESPONSE_FILES:
        try:
            load_saved_responses(
                ROOT / response_path,
                manifest=expanded_manifest,
                items=expanded_items,
            )
        except ValueError as exc:
            raise FreezeError(f"saved response validation failed: {response_path}: {exc}") from exc

    report_by_response = {str(report["saved_run"]["path"]): report for report in reports}
    if set(report_by_response) != {path.as_posix() for path in RESPONSE_FILES}:
        raise FreezeError("baseline reports do not cover the frozen response files exactly")
    if any(report["manifest"]["payload_sha256"] != heldout["integrity"]["payload_sha256"] for report in reports):
        raise FreezeError("baseline report manifest receipt drift")
    if any(report["saved_run"]["prompt_sha256"] != _sha256(ROOT / PROMPT) for report in reports):
        raise FreezeError("baseline prompt receipt drift")
    if any(report["scorer"]["implementation_sha256"] != _sha256(ROOT / EVALUATOR) for report in reports):
        raise FreezeError("baseline scorer receipt drift")
    if any(report["saved_run"]["gold_fields_supplied"] != [] for report in reports):
        raise FreezeError("baseline report declares supplied gold fields")
    fixture_ids = {str(row.get("id", "")) for row in development_fixtures}
    if len(development_fixtures) != 52 or len(fixture_ids) != 52 or "" in fixture_ids:
        raise FreezeError("development fixture inventory is not the frozen 52 unique records")
    heldout_ids = {str(row[0]) for row in heldout["items"]}
    if fixture_ids & heldout_ids:
        raise FreezeError("development fixture IDs overlap held-out results")

    counts = heldout["counts"]
    integrity = heldout["integrity"]
    upstream = config["upstream"]
    return {
        "schema_version": SCHEMA_VERSION,
        "release": {
            "id": "ua-gec-calque-grammar-public-v0",
            "version": RELEASE_VERSION,
            "status": "immutable",
            "issue": 4626,
            "parent_epic": 2156,
        },
        "task_contract": {
            "task": heldout["task"],
            "manifest_id": heldout["manifest_id"],
            "predicate": heldout["predicate"],
            "prompt_sha256": _sha256(ROOT / PROMPT),
            "model_output_schema_sha256": _sha256(ROOT / OUTPUT_SCHEMA),
            "scorer_id": reports[0]["scorer"]["id"],
            "scorer_sha256": _sha256(ROOT / EVALUATOR),
        },
        "upstream": {
            "dataset": "UA-GEC",
            "repository": upstream["repository"],
            "commit": upstream["commit"],
            "version": upstream["version"],
            "license": upstream["license"],
            "license_url": upstream["license_url"],
            "citation": upstream["citation"],
            "file_sha256": upstream["files"],
        },
        "split_integrity": {
            "partition": heldout["predicate"]["partition"],
            "annotation_layer": heldout["predicate"]["annotation_layer"],
            "manifest_payload_sha256": integrity["payload_sha256"],
            "upstream_test_documents": counts["upstream_test_documents"],
            "upstream_test_authors": counts["upstream_test_authors"],
            "upstream_train_authors": counts["upstream_train_authors"],
            "upstream_train_documents": split["train_documents"],
            "train_test_author_overlap": split["train_test_author_overlap"],
            "train_test_document_overlap": split["train_test_document_overlap"],
            "document_proof": (
                "The frozen split receipt retains the exact pinned metadata document and "
                "author ID sets; the verifier recomputes both intersections and requires "
                "its test documents to equal the held-out manifest document set."
            ),
            "sentence_disposition": {
                "upstream_test": counts["upstream_test_sentences"],
                "included": counts["included_sentences"],
                "excluded": counts["excluded_sentences"],
            },
            "development_fixture_count": len(development_fixtures),
            "development_fixtures_in_heldout_results": 0,
        },
        "contamination": {
            "disclosures": [
                "The public task instruction contains no examples.",
                "The deterministic literal-rule baseline derives rules from 52 train-only development fixtures.",
                "A two-item source-only transport smoke informed one formatting clarification; no gold or score was inspected.",
                "The real model route was selected from the operator's pre-existing model assignment, not benchmark scores.",
                "No held-out target, edit, or score entered model generation.",
            ],
            "forbidden_destinations": [
                "Daily Practice inventories",
                "training or fine-tuning inventories",
                "synthetic-data, DPO, or preference-data pipelines",
            ],
            "excluded_data_classes": [
                "Hramatka and teacher feedback",
                "Atlas or other product-private state",
                "factuality or BIO fixtures",
                "private canaries",
                "curriculum and learner payloads",
            ],
        },
        "reporting": {
            "aggregate_only": True,
            "forbidden_item_fields": sorted(REPORT_FORBIDDEN_KEYS),
            "verified_report_paths": [path.as_posix() for path in REPORT_FILES],
        },
        "baselines": [_run_receipt(report) for report in reports],
        "artifacts": [_artifact(path, role) for path, role in FROZEN_ARTIFACTS],
        "version_policy": {
            "in_place_edits": "forbidden",
            "any_frozen_byte_change": "requires a new semantic version and freeze directory",
            "patch": "documentation or packaging correction with unchanged dataset, task, scorer, and baseline results",
            "minor": "backward-compatible task, scorer, runner, or baseline addition",
            "major": "dataset, eligibility predicate, gold, split, primary metric, or incompatible contract change",
            "historical_freezes": "retained and independently verifiable",
        },
    }


def validate_freeze(freeze: Mapping[str, Any]) -> None:
    """Fail closed if the receipt is malformed or any frozen byte drifted."""
    if freeze.get("schema_version") != SCHEMA_VERSION:
        raise FreezeError("unsupported freeze schema")
    release = freeze.get("release")
    if not isinstance(release, Mapping) or release.get("version") != RELEASE_VERSION:
        raise FreezeError("release identity mismatch")
    if release.get("status") != "immutable":
        raise FreezeError("release is not marked immutable")
    artifacts = freeze.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != len(FROZEN_ARTIFACTS):
        raise FreezeError("frozen artifact inventory mismatch")
    expected = {path.as_posix(): role for path, role in FROZEN_ARTIFACTS}
    actual: dict[str, str] = {}
    for artifact in artifacts:
        if not isinstance(artifact, Mapping):
            raise FreezeError("invalid artifact receipt")
        path = str(artifact.get("path", ""))
        role = str(artifact.get("role", ""))
        if path in actual or expected.get(path) != role:
            raise FreezeError(f"unexpected artifact receipt: {path}")
        if artifact.get("sha256") != _sha256(ROOT / path):
            raise FreezeError(f"frozen artifact hash mismatch: {path}")
        actual[path] = role
    if actual != expected:
        raise FreezeError("frozen artifact paths do not match the v0.1.0 contract")
    rebuilt = build_freeze()
    if freeze != rebuilt:
        raise FreezeError("freeze metadata is stale or has been edited in place")


def _write_versioned_receipt(path: Path, value: Mapping[str, Any], *, version: str) -> None:
    if path.parent.name != f"v{version}":
        raise FreezeError(f"freeze path does not match release version {version!r}: {path}")
    serialized = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise FreezeError(f"cannot read existing freeze {path}: {exc}") from exc
        if existing != serialized:
            raise FreezeError(f"refusing to overwrite immutable freeze {path}; create a new semantic version directory")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")


def write_freeze(path: Path, freeze: Mapping[str, Any]) -> None:
    version = str(freeze.get("release", {}).get("version", ""))
    _write_versioned_receipt(path, freeze, version=version)


def write_split_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    version = str(receipt.get("release_version", ""))
    _write_versioned_receipt(path, receipt, version=version)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--split-receipt", type=Path, default=DEFAULT_SPLIT_OUTPUT)
    parser.add_argument("--ua-gec-root", type=Path, default=DEFAULT_UA_GEC_ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--write-split-receipt", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write_split_receipt:
            config = _read_json(ROOT / HELDOUT_CONFIG)
            receipt = build_split_receipt(args.ua_gec_root, config)
            write_split_receipt(args.split_receipt, receipt)
            print(
                f"UA evaluation split receipt valid: "
                f"{len(receipt['train_document_ids'])} train documents, "
                f"{len(receipt['test_document_ids'])} test documents"
            )
            return 0
        if args.write:
            freeze = build_freeze()
            write_freeze(args.freeze, freeze)
        else:
            freeze = _read_json(args.freeze)
            validate_freeze(freeze)
        print(
            f"UA evaluation freeze valid: {freeze['release']['id']} "
            f"v{freeze['release']['version']}, {len(freeze['artifacts'])} artifacts"
        )
        return 0
    except FreezeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
