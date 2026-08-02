#!/usr/bin/env python3
"""Build and score the open-weight-first Ukrainian evaluation suite.

The suite keeps UA Eval 0.1.1 byte-for-byte frozen as its human-gold anchor.
All additional cases are deterministic derivatives or explicitly labelled
controlled silver. Generation requests never contain expected answers, and
scoring consumes saved output without an LLM judge.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.ua_eval_harness.evaluate_model import load_manifest

RELEASE_ROOT = ROOT / "data/projects/ua_open_weight_eval/v0.1.0"
CONFIG_PATH = RELEASE_ROOT / "build_config.json"
SEEDS_PATH = RELEASE_ROOT / "controlled_seeds.jsonl"
CASES_PATH = RELEASE_ROOT / "cases.jsonl"
RECEIPT_PATH = RELEASE_ROOT / "release_receipt.json"
V011_FREEZE = ROOT / "data/projects/ua_eval_harness/releases/v0.1.1/freeze_manifest.json"
V011_MANIFEST = ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
V02_PACKET = ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl"
PUBLICATION_TAG = "ua-open-weight-eval-v0.1.0"
PUBLICATION_DOC_ROOT = ROOT / "docs/projects/ua-open-weight-eval"
PUBLICATION_FILES = (
    (CONFIG_PATH, "build_config.json", "MIT", "deterministic build configuration"),
    (CASES_PATH, "cases.jsonl", "LicenseRef-Row-Specific", "frozen evaluation cases"),
    (SEEDS_PATH, "controlled_seeds.jsonl", "MIT", "project-authored silver seeds"),
    (
        RELEASE_ROOT / "local_run_config.example.json",
        "local_run_config.example.json",
        "MIT",
        "offline runner configuration example",
    ),
    (
        RECEIPT_PATH,
        "release_receipt.json",
        "MIT",
        "frozen release and upstream hash receipt",
    ),
    (
        RELEASE_ROOT / "saved_response.schema.json",
        "saved_response.schema.json",
        "MIT",
        "saved-output JSON Schema",
    ),
    (
        PUBLICATION_DOC_ROOT / "HUGGING_FACE_README.md",
        "README.md",
        "MIT",
        "Hugging Face dataset card and bilingual quickstart",
    ),
    (
        PUBLICATION_DOC_ROOT / "DATA_CARD.md",
        "DATA_CARD.md",
        "MIT",
        "full data card and limitations",
    ),
    (
        PUBLICATION_DOC_ROOT / "CONTAMINATION_POLICY.md",
        "CONTAMINATION_POLICY.md",
        "MIT",
        "evaluation and learning-view separation policy",
    ),
    (
        PUBLICATION_DOC_ROOT / "THIRD_PARTY_NOTICES.md",
        "THIRD_PARTY_NOTICES.md",
        "MIT",
        "license, attribution, and modification notices",
    ),
    (
        ROOT / "scripts/projects/ua_open_weight_eval/run_mlx_model.py",
        "run_mlx_model.py",
        "MIT",
        "resumable source-only MLX open-weight runner",
    ),
    (ROOT / "LICENSE", "LICENSE-MIT.txt", "MIT", "repository-authored byte license text"),
)
CASE_RIGHTS_RULES = [
    {
        "case_id_prefix": "uaw-011-",
        "cases": 2000,
        "license_expression": "CC-BY-4.0",
        "notice": "UA-GEC-derived error and control rows; retain attribution and modification notice.",
    },
    {
        "case_id_prefix": "uaw-silver-",
        "cases": 2000,
        "license_expression": "MIT",
        "notice": "Project-authored controlled or source-backed silver rows; external evidence bytes are not included.",
    },
]

FROZEN_UPSTREAM_HASHES = {
    "data/projects/ua_eval_harness/releases/v0.1.1/freeze_manifest.json": (
        "b95edea210ae9133059181a4e2d161c8682108bfcacdde50f98adaae2221e65f"
    ),
    "data/projects/ua_eval_harness/heldout_manifest_v1.json": (
        "56eb4fc17a5ed6967c5c13fbdc9fde964d1b8fb08bde7da7f15cf535486735dd"
    ),
    "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl": (
        "9b436a1a6c7c442f3dafaa468d358446a8cb66995562749e2801eac07b211add"
    ),
}
CASE_SCHEMA = "ua_open_weight_eval_case.v1"
REQUEST_SCHEMA = "ua_open_weight_eval_requests.v1"
RESPONSE_SCHEMA = "ua_open_weight_eval_responses.v1"
REPORT_SCHEMA = "ua_open_weight_eval_track_report.v1"
ALLOWED_ACTIONS = frozenset({"correct", "preserve", "abstain"})
ALLOWED_BACKENDS = frozenset({"transformers", "llama.cpp", "vllm", "custom_local"})
RUN_CONFIG_FIELDS = frozenset(
    {
        "backend",
        "command",
        "model_path",
        "model_revision",
        "model_sha256",
        "network_allowed",
        "provider",
    }
)
FORBIDDEN_COMMAND_EXECUTABLES = frozenset({"anthropic", "claude", "curl", "openai", "ssh", "wget"})


class SuiteError(ValueError):
    """A suite artifact or local-run contract is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_path(path: Path) -> str:
    """Hash one model file or a deterministic, symlink-free model tree."""
    if path.is_file():
        return sha256_file(path)
    _require(path.is_dir(), "model_path must be a file or directory")
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file() or item.is_symlink())
    _require(files, "model directory contains no files")
    for item in files:
        _require(not item.is_symlink(), "model directory cannot contain symlinks")
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        size = item.stat().st_size
        digest.update(size.to_bytes(8, "big"))
        with item.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SuiteError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SuiteError(f"expected JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SuiteError(f"cannot read JSONL {path}: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SuiteError(f"invalid JSONL {path}:{number}: {exc}") from exc
        if not isinstance(row, dict):
            raise SuiteError(f"expected object at {path}:{number}")
        rows.append(row)
    if not rows:
        raise SuiteError(f"empty JSONL: {path}")
    return rows


def encode_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    return "".join(canonical_json(dict(row)) + "\n" for row in rows)


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SuiteError(message)


def verify_upstream_freezes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative, expected in FROZEN_UPSTREAM_HASHES.items():
        path = ROOT / relative
        _require(path.is_file(), f"missing frozen upstream artifact: {relative}")
        actual = sha256_file(path)
        _require(actual == expected, f"frozen upstream drift: {relative}")
        hashes[relative] = actual
    return hashes


def _validate_config(config: Mapping[str, Any]) -> None:
    tracks = config.get("tracks")
    category_counts = config.get("category_counts")
    contexts = config.get("contexts")
    _require(isinstance(tracks, list) and len(tracks) == 14, "exactly fourteen tracks are required")
    _require(len(set(tracks)) == len(tracks), "duplicate evaluation track")
    _require(isinstance(category_counts, dict), "category_counts must be an object")
    _require(
        set(category_counts) == {"error", "correct_control", "protected", "unresolved"},
        "category set drift",
    )
    _require(all(isinstance(value, int) and value > 0 for value in category_counts.values()), "invalid category count")
    _require(sum(category_counts.values()) == config.get("case_count"), "case count arithmetic drift")
    _require(isinstance(contexts, list) and contexts, "contexts must be nonempty")
    _require(all(isinstance(value, list) and len(value) == 2 for value in contexts), "invalid context pair")


def _tracks_for_reference(reference: Mapping[str, Any]) -> list[str]:
    tags = {str(edit.get("tag", "")) for edit in reference["edits"]}
    tracks: set[str] = set()
    if any(tag.startswith("G/") or tag == "Punctuation" for tag in tags):
        tracks.add("grammar")
    if any(
        tag == "Spelling"
        or any(fragment in tag for fragment in ("Noun", "Verb", "Adj", "Case", "Gender", "Number", "Aspect"))
        for tag in tags
    ):
        tracks.add("morphology")
    if "F/Calque" in tags:
        tracks.update({"calques", "russian_interference"})
    if any(tag.startswith("F/") and tag != "F/Calque" for tag in tags):
        tracks.add("register")
    return sorted(tracks or {"grammar"})


def _contextualize(text: str, context: Sequence[str]) -> str:
    return f"{context[0]}{text}{context[1]}"


def _case(
    *,
    case_id: str,
    category: str,
    tracks: Sequence[str],
    source: str,
    expected_action: str,
    accepted_texts: Sequence[str],
    evidence_grade: str,
    evidence_ref: str,
    transformation: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": CASE_SCHEMA,
        "case_id": case_id,
        "category": category,
        "tracks": sorted(set(tracks)),
        "source": source,
        "source_sha256": sha256_text(source),
        "expected": {
            "action": expected_action,
            "accepted_texts": list(dict.fromkeys(accepted_texts)),
        },
        "evidence": {
            "grade": evidence_grade,
            "ref": evidence_ref,
            "transformation": dict(transformation),
        },
        "data_handling": {
            "classification": "evaluation_only",
            "foundry_learning_eligible": False,
        },
    }
    payload["case_sha256"] = sha256_text(canonical_json(payload))
    return payload


def build_cases() -> list[dict[str, Any]]:
    verify_upstream_freezes()
    config = read_json(CONFIG_PATH)
    _validate_config(config)
    _, items = load_manifest(V011_MANIFEST)
    seeds = read_jsonl(SEEDS_PATH)
    tracks = set(config["tracks"])
    contexts = config["contexts"]
    seed_counts = Counter(str(seed.get("category")) for seed in seeds)
    _require(seed_counts == {"protected": 14, "unresolved": 14}, "need one seed per track and silver category")
    _require({seed.get("track") for seed in seeds} == tracks, "controlled seeds do not cover every track")
    cases: list[dict[str, Any]] = []

    for category in ("error", "correct_control"):
        target_count = config["category_counts"][category]
        for index in range(target_count):
            item = items[index % len(items)]
            context_index = (index // len(items)) % len(contexts)
            context = contexts[context_index]
            references = item["references"]
            accepted = [_contextualize(reference["target"], context) for reference in references]
            if category == "error":
                source = _contextualize(item["source"], context)
                action = "correct"
                grade = "human_gold"
            else:
                source = accepted[index % len(accepted)]
                accepted = [source]
                action = "preserve"
                grade = "human_gold_derived_control"
            selected_reference = references[index % len(references)]
            cases.append(
                _case(
                    case_id=f"uaw-011-{category}-{index + 1:04d}",
                    category=category,
                    tracks=_tracks_for_reference(selected_reference),
                    source=source,
                    expected_action=action,
                    accepted_texts=accepted,
                    evidence_grade=grade,
                    evidence_ref=f"data/projects/ua_eval_harness/heldout_manifest_v1.json#{item['id']}",
                    transformation={
                        "kind": "context_wrapper" if context_index else "identity",
                        "context_index": context_index,
                        "anchor_item_id": item["id"],
                    },
                )
            )

    for category in ("protected", "unresolved"):
        category_seeds = [seed for seed in seeds if seed["category"] == category]
        target_count = config["category_counts"][category]
        for index in range(target_count):
            seed = category_seeds[index % len(category_seeds)]
            context_index = (index // len(category_seeds)) % len(contexts)
            context = contexts[context_index]
            source = _contextualize(seed["text"], context)
            cases.append(
                _case(
                    case_id=f"uaw-silver-{category}-{index + 1:04d}",
                    category=category,
                    tracks=[seed["track"]],
                    source=source,
                    expected_action=seed["expected_action"],
                    accepted_texts=[source],
                    evidence_grade=seed["evidence_grade"],
                    evidence_ref=seed["evidence_ref"],
                    transformation={
                        "kind": "controlled_context_wrapper" if context_index else "identity",
                        "context_index": context_index,
                        "seed_id": seed["seed_id"],
                    },
                )
            )

    _validate_cases(cases, config)
    return sorted(cases, key=lambda row: row["case_id"])


def _validate_cases(cases: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> None:
    _require(len(cases) == config["case_count"], "built case count drift")
    _require(len({case.get("case_id") for case in cases}) == len(cases), "duplicate case id")
    counts = Counter(str(case.get("category")) for case in cases)
    _require(counts == config["category_counts"], "category balance drift")
    covered = {track for case in cases for track in case.get("tracks", [])}
    _require(covered == set(config["tracks"]), "track coverage drift")
    for case in cases:
        _require(case.get("schema_version") == CASE_SCHEMA, "case schema drift")
        source = case.get("source")
        _require(isinstance(source, str) and source, "case source must be nonempty")
        _require(case.get("source_sha256") == sha256_text(source), "case source hash mismatch")
        expected = case.get("expected")
        _require(isinstance(expected, dict) and expected.get("action") in ALLOWED_ACTIONS, "invalid expected action")
        _require(
            case.get("data_handling", {}).get("foundry_learning_eligible") is False, "evaluation leakage flag drift"
        )
        without_hash = dict(case)
        claimed = without_hash.pop("case_sha256", None)
        _require(claimed == sha256_text(canonical_json(without_hash)), "case hash mismatch")


def build_release() -> dict[str, Any]:
    cases = build_cases()
    encoded = encode_jsonl(cases)
    write_text_atomic(CASES_PATH, encoded)
    config = read_json(CONFIG_PATH)
    receipt = {
        "schema_version": "ua_open_weight_eval_release_receipt.v1",
        "release_id": config["release_id"],
        "policy": {
            "human_gold_anchor": "ua_eval_harness.v0.1.1",
            "human_gold_anchor_mutated": False,
            "parked_v0.2_mutated": False,
            "closed_api_required": False,
            "closed_model_judge_allowed": False,
            "single_quality_score_produced": False,
            "foundry_learning_eligible": False,
        },
        "counts": {
            "total": len(cases),
            "by_category": dict(sorted(Counter(case["category"] for case in cases).items())),
            "by_evidence_grade": dict(sorted(Counter(case["evidence"]["grade"] for case in cases).items())),
            "by_track": dict(sorted(Counter(track for case in cases for track in case["tracks"]).items())),
        },
        "artifacts": {
            "build_config": sha256_file(CONFIG_PATH),
            "controlled_seeds": sha256_file(SEEDS_PATH),
            "cases": sha256_text(encoded),
            "foundry_firewall": sha256_file(ROOT / "scripts/projects/open_model_data/model_view_exporter.py"),
            "local_run_config_example": sha256_file(RELEASE_ROOT / "local_run_config.example.json"),
            "saved_response_schema": sha256_file(RELEASE_ROOT / "saved_response.schema.json"),
            "suite_cli": sha256_file(Path(__file__)),
        },
        "upstream_freezes": verify_upstream_freezes(),
    }
    write_text_atomic(RECEIPT_PATH, json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return receipt


def verify_release() -> dict[str, Any]:
    _require(CASES_PATH.is_file() and RECEIPT_PATH.is_file(), "release artifacts are missing")
    expected_cases = encode_jsonl(build_cases())
    _require(CASES_PATH.read_text(encoding="utf-8") == expected_cases, "cases do not reproduce exactly")
    receipt = read_json(RECEIPT_PATH)
    expected_artifacts = {
        "build_config": sha256_file(CONFIG_PATH),
        "controlled_seeds": sha256_file(SEEDS_PATH),
        "cases": sha256_text(expected_cases),
        "foundry_firewall": sha256_file(ROOT / "scripts/projects/open_model_data/model_view_exporter.py"),
        "local_run_config_example": sha256_file(RELEASE_ROOT / "local_run_config.example.json"),
        "saved_response_schema": sha256_file(RELEASE_ROOT / "saved_response.schema.json"),
        "suite_cli": sha256_file(Path(__file__)),
    }
    _require(receipt.get("artifacts") == expected_artifacts, "release artifact receipt mismatch")
    _require(receipt.get("upstream_freezes") == verify_upstream_freezes(), "upstream receipt drift")
    policies = receipt.get("policy", {})
    _require(policies.get("closed_api_required") is False, "closed API policy drift")
    _require(policies.get("closed_model_judge_allowed") is False, "closed judge policy drift")
    _require(policies.get("single_quality_score_produced") is False, "single score policy drift")
    return receipt


def _validate_source_revision(source_revision: str) -> None:
    _require(
        len(source_revision) == 40 and all(character in "0123456789abcdef" for character in source_revision),
        "source revision must be a full lowercase Git SHA",
    )


def publication_manifest(source_revision: str) -> dict[str, Any]:
    """Return the complete, hash-bound public payload manifest."""
    _validate_source_revision(source_revision)
    receipt = verify_release()
    cases = read_jsonl(CASES_PATH)
    rights_counts = Counter(
        "CC-BY-4.0" if str(case.get("case_id", "")).startswith("uaw-011-") else "MIT" for case in cases
    )
    _require(
        rights_counts == {"CC-BY-4.0": 2000, "MIT": 2000},
        "case rights selectors do not cover the frozen suite exactly",
    )

    files: list[dict[str, Any]] = []
    output_names: set[str] = set()
    for source, output_name, license_expression, role in PUBLICATION_FILES:
        _require(source.is_file(), f"missing publication source: {source.relative_to(ROOT)}")
        _require(output_name not in output_names, f"duplicate publication output: {output_name}")
        _require(
            Path(output_name).name == output_name,
            f"nested publication output forbidden: {output_name}",
        )
        output_names.add(output_name)
        files.append(
            {
                "bytes": source.stat().st_size,
                "license_expression": license_expression,
                "output_path": output_name,
                "role": role,
                "sha256": sha256_file(source),
                "source_path": source.relative_to(ROOT).as_posix(),
            }
        )

    return {
        "schema_version": "ua_open_weight_eval_publication_manifest.v1",
        "release_id": receipt["release_id"],
        "release_tag": PUBLICATION_TAG,
        "source_revision": source_revision,
        "files": files,
        "case_rights": {
            "manifest_scope": "cases.jsonl",
            "rules": CASE_RIGHTS_RULES,
        },
        "exclusions": [
            "model weights and adapters",
            "provider raw output and failed-attempt logs",
            "private corpus and Google Drive bytes",
            "non-redistributable literary or textbook content",
            "VESUM dictionary data and derived evidence artifacts",
            "UA Eval v0.2 pending-review material",
        ],
        "policies": {
            "closed_model_judge_allowed": False,
            "foundry_learning_eligible": False,
            "global_quality_score_allowed": False,
            "independent_human_judgments_claimed": 1000,
            "total_cases": 4000,
        },
    }


def _write_deterministic_zip(package_dir: Path, archive_path: Path) -> None:
    _require(not archive_path.exists(), f"refusing to replace archive: {archive_path}")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = PUBLICATION_TAG
    temporary = archive_path.with_name(f".{archive_path.name}.tmp")
    _require(not temporary.exists(), f"temporary archive already exists: {temporary}")
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for path in sorted(item for item in package_dir.iterdir() if item.is_file()):
                info = zipfile.ZipInfo(f"{prefix}/{path.name}", date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(
                    info,
                    path.read_bytes(),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        temporary.replace(archive_path)
    finally:
        temporary.unlink(missing_ok=True)


def package_publication(*, output_dir: Path, source_revision: str, archive_path: Path | None = None) -> dict[str, Any]:
    """Create the exact GitHub/Hugging Face publication payload."""
    _require(not output_dir.exists(), f"refusing to replace output directory: {output_dir}")
    manifest = publication_manifest(source_revision)
    output_dir.mkdir(parents=True)
    try:
        for item in manifest["files"]:
            shutil.copyfile(ROOT / item["source_path"], output_dir / item["output_path"])
        manifest_path = output_dir / "PUBLICATION_MANIFEST.json"
        write_text_atomic(
            manifest_path,
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        checksum_files = sorted(path for path in output_dir.iterdir() if path.is_file())
        checksums = "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_files)
        write_text_atomic(output_dir / "SHA256SUMS", checksums)
        verification = verify_publication_package(output_dir)
        if archive_path is not None:
            _write_deterministic_zip(output_dir, archive_path)
            verification["archive"] = {
                "path": str(archive_path),
                "bytes": archive_path.stat().st_size,
                "sha256": sha256_file(archive_path),
            }
        return verification
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise


def verify_publication_package(package_dir: Path) -> dict[str, Any]:
    """Verify a staged publication directory and reject extra bytes."""
    _require(package_dir.is_dir(), "publication package directory is missing")
    manifest_path = package_dir / "PUBLICATION_MANIFEST.json"
    checksums_path = package_dir / "SHA256SUMS"
    manifest = read_json(manifest_path)
    _require(
        manifest.get("schema_version") == "ua_open_weight_eval_publication_manifest.v1",
        "publication manifest schema drift",
    )
    _require(manifest.get("release_tag") == PUBLICATION_TAG, "publication tag drift")
    _validate_source_revision(str(manifest.get("source_revision", "")))
    case_rights = manifest.get("case_rights")
    _require(
        isinstance(case_rights, dict) and case_rights.get("rules") == CASE_RIGHTS_RULES,
        "publication case-rights drift",
    )
    files = manifest.get("files")
    _require(isinstance(files, list) and files, "publication file manifest is empty")
    expected_names = {item["output_path"] for item in files}
    expected_names.update({manifest_path.name, checksums_path.name})
    package_children = list(package_dir.iterdir())
    _require(all(path.is_file() for path in package_children), "publication package has nested data")
    actual_names = {path.name for path in package_children}
    _require(actual_names == expected_names, "publication package has missing or extra files")
    for item in files:
        path = package_dir / item["output_path"]
        _require(path.stat().st_size == item["bytes"], f"publication byte count drift: {path.name}")
        _require(sha256_file(path) == item["sha256"], f"publication hash drift: {path.name}")
    expected_checksums = "".join(
        f"{sha256_file(path)}  {path.name}\n"
        for path in sorted(
            (package_dir / name for name in expected_names if name != checksums_path.name),
            key=lambda path: path.name,
        )
    )
    _require(checksums_path.read_text(encoding="utf-8") == expected_checksums, "SHA256SUMS drift")
    return {
        "status": "passed",
        "release_id": manifest["release_id"],
        "release_tag": manifest["release_tag"],
        "source_revision": manifest["source_revision"],
        "files": len(expected_names),
        "manifest_sha256": sha256_file(manifest_path),
        "sha256sums_sha256": sha256_file(checksums_path),
    }


def prepare_requests(output: Path) -> dict[str, Any]:
    verify_release()
    cases = read_jsonl(CASES_PATH)
    instruction = (
        "Return one JSON object with item_id, action, and output_text. "
        "action must be correct, preserve, or abstain. Correct only when warranted; "
        "preserve quotations, names, historical or regional language, register, and ambiguity."
    )
    rows: list[dict[str, Any]] = [
        {
            "type": "request_run",
            "schema_version": REQUEST_SCHEMA,
            "release_id": read_json(CONFIG_PATH)["release_id"],
            "case_count": len(cases),
            "input_fields": ["item_id", "source", "source_sha256", "instruction_sha256"],
            "gold_fields_supplied": [],
            "instruction": instruction,
            "instruction_sha256": sha256_text(instruction),
        }
    ]
    for position, case in enumerate(cases, 1):
        payload = {
            "item_id": request_item_id(position),
            "source": case["source"],
            "source_sha256": case["source_sha256"],
            "instruction_sha256": sha256_text(instruction),
        }
        rows.append({"type": "request", **payload, "request_sha256": sha256_text(canonical_json(payload))})
    encoded = encode_jsonl(rows)
    write_text_atomic(output, encoded)
    return {"requests": len(cases), "path": str(output), "sha256": sha256_text(encoded)}


def request_item_id(position: int) -> str:
    _require(position > 0, "request position must be positive")
    return f"uaw-request-{position:04d}"


def validate_run_config(path: Path) -> dict[str, Any]:
    config = read_json(path)
    _require(set(config) == RUN_CONFIG_FIELDS, "local run config field set drift")
    _require(config.get("backend") in ALLOWED_BACKENDS, "unsupported local backend")
    _require(config.get("provider") in (None, "local"), "provider must be local")
    model_path_raw = config.get("model_path")
    _require(isinstance(model_path_raw, str) and model_path_raw, "model_path is required")
    model_path = Path(model_path_raw).expanduser()
    _require(model_path.exists(), "model_path must already exist; downloads are not performed")
    revision = config.get("model_revision")
    _require(isinstance(revision, str) and revision, "model_revision is required")
    claimed_hash = config.get("model_sha256")
    _require(
        isinstance(claimed_hash, str)
        and len(claimed_hash) == 64
        and all(character in "0123456789abcdef" for character in claimed_hash),
        "model_sha256 must be a lowercase SHA-256",
    )
    _require(sha256_path(model_path) == claimed_hash, "model path hash mismatch")
    command = config.get("command")
    _require(
        isinstance(command, list) and command and all(isinstance(part, str) for part in command),
        "command must be a nonempty string array",
    )
    _require(
        "{requests}" in command and "{responses}" in command, "command requires requests and responses placeholders"
    )
    executable = Path(command[0]).expanduser()
    _require(executable.is_absolute() and executable.is_file(), "runner executable must be an existing absolute file")
    _require(
        executable.name.casefold() not in FORBIDDEN_COMMAND_EXECUTABLES,
        "network or closed-service client cannot be a local runner",
    )
    _require(
        not any("http://" in part.casefold() or "https://" in part.casefold() for part in command),
        "runner command cannot contain a network URL",
    )
    _require(config.get("network_allowed") is False, "network_allowed must be false")
    return config


def run_local(config_path: Path, requests: Path, responses: Path, receipt_path: Path) -> dict[str, Any]:
    config = validate_run_config(config_path)
    _require(requests.is_file(), "request packet is missing")
    command = [
        part.replace("{requests}", str(requests.resolve())).replace("{responses}", str(responses.resolve()))
        for part in config["command"]
    ]
    environment = {key: os.environ[key] for key in ("LANG", "LC_ALL", "PATH", "TMPDIR") if key in os.environ}
    environment.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
            "UA_EVAL_NETWORK_ALLOWED": "0",
        }
    )
    completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    _require(completed.returncode == 0, f"local runner exited {completed.returncode}")
    _require(responses.is_file(), "local runner did not create responses")
    receipt = {
        "schema_version": "ua_open_weight_eval_local_run_receipt.v1",
        "backend": config["backend"],
        "model_path": str(Path(config["model_path"]).resolve()),
        "model_revision": config["model_revision"],
        "model_sha256": config["model_sha256"],
        "network_allowed": False,
        "closed_api_used": False,
        "command": command,
        "requests_sha256": sha256_file(requests),
        "responses_sha256": sha256_file(responses),
    }
    write_text_atomic(receipt_path, json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return receipt


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def score_saved(responses_path: Path, output: Path) -> dict[str, Any]:
    verify_release()
    cases = {request_item_id(position): row for position, row in enumerate(read_jsonl(CASES_PATH), 1)}
    raw_rows = read_jsonl(responses_path)
    if raw_rows[0].get("type") == "run":
        header = raw_rows.pop(0)
        _require(header.get("schema_version") == RESPONSE_SCHEMA, "response header schema drift")
        run_metadata = {key: value for key, value in header.items() if key not in {"score", "judge"}}
    else:
        run_metadata = {"schema_version": RESPONSE_SCHEMA, "source": "headerless_saved_output"}
    responses: dict[str, dict[str, Any]] = {}
    for row in raw_rows:
        item_id = row.get("item_id")
        _require(item_id in cases, f"unknown response item: {item_id}")
        _require(item_id not in responses, f"duplicate response item: {item_id}")
        _require(row.get("action") in ALLOWED_ACTIONS, f"invalid action for {item_id}")
        _require(isinstance(row.get("output_text"), str), f"missing output_text for {item_id}")
        responses[item_id] = row
    _require(set(responses) == set(cases), "saved output must contain every case exactly once")

    buckets: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for item_id, case in cases.items():
        response = responses[item_id]
        expected = case["expected"]
        action_ok = response["action"] == expected["action"]
        accepted = {_normalized_text(text) for text in expected["accepted_texts"]}
        text_ok = _normalized_text(response["output_text"]) in accepted
        for track in case["tracks"]:
            bucket = buckets[(track, case["category"])]
            bucket["cases"] += 1
            bucket["action_correct"] += int(action_ok)
            bucket["text_exact"] += int(text_ok)
            bucket["overcorrected"] += int(case["category"] in {"correct_control", "protected"} and not text_ok)
            bucket["abstained_correctly"] += int(case["category"] == "unresolved" and action_ok)

    tracks: dict[str, Any] = {}
    for track in read_json(CONFIG_PATH)["tracks"]:
        categories: dict[str, Any] = {}
        for category in ("error", "correct_control", "protected", "unresolved"):
            counts = buckets[(track, category)]
            total = counts["cases"]
            categories[category] = {
                "cases": total,
                "action_accuracy": counts["action_correct"] / total if total else None,
                "exact_text_accuracy": counts["text_exact"] / total if total else None,
                "overcorrection_rate": counts["overcorrected"] / total if total else None,
                "correct_abstention_rate": counts["abstained_correctly"] / total if total else None,
            }
        tracks[track] = {"categories": categories}
    report = {
        "schema_version": REPORT_SCHEMA,
        "release_id": read_json(CONFIG_PATH)["release_id"],
        "run": run_metadata,
        "scoring": {
            "judge": "deterministic_exact_match",
            "closed_model_judge_used": False,
            "global_quality_score": None,
            "global_score_prohibited": True,
        },
        "tracks": tracks,
        "responses_sha256": sha256_file(responses_path),
        "cases_sha256": sha256_file(CASES_PATH),
    }
    write_text_atomic(output, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return report


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build", help="rebuild the deterministic 4,000-case release")
    commands.add_parser("verify", help="verify frozen inputs and exact reproduction")
    package = commands.add_parser(
        "package-publication",
        help="build the verified GitHub and Hugging Face payload",
    )
    package.add_argument("--output", type=Path, required=True)
    package.add_argument("--source-revision", required=True)
    package.add_argument("--archive", type=Path)
    verify_package = commands.add_parser(
        "verify-publication-package",
        help="verify a staged publication payload",
    )
    verify_package.add_argument("--package", type=Path, required=True)
    prepare = commands.add_parser("prepare", help="write a source-only request packet")
    prepare.add_argument("--output", type=Path, required=True)
    validate = commands.add_parser("validate-run-config", help="validate an offline open-weight runner config")
    validate.add_argument("--config", type=Path, required=True)
    run = commands.add_parser("run-local", help="execute a preinstalled local open-weight runner")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--requests", type=Path, required=True)
    run.add_argument("--responses", type=Path, required=True)
    run.add_argument("--receipt", type=Path, required=True)
    score = commands.add_parser("score", help="score complete saved output per track")
    score.add_argument("--responses", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "build":
            result = build_release()
        elif args.command == "verify":
            result = verify_release()
        elif args.command == "package-publication":
            result = package_publication(
                output_dir=args.output,
                source_revision=args.source_revision,
                archive_path=args.archive,
            )
        elif args.command == "verify-publication-package":
            result = verify_publication_package(args.package)
        elif args.command == "prepare":
            result = prepare_requests(args.output)
        elif args.command == "validate-run-config":
            result = validate_run_config(args.config)
        elif args.command == "run-local":
            result = run_local(args.config, args.requests, args.responses, args.receipt)
        else:
            result = score_saved(args.responses, args.output)
    except (OSError, SuiteError) as exc:
        print(f"ua-open-weight-eval: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
