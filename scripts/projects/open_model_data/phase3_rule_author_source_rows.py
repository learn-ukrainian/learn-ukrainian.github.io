#!/usr/bin/env python3
"""Materialize explicitly cleared UA-GEC source rows for the rule-author lane.

This steward-only adapter has one narrow authority: turn the exact private
author-clearance allowlist into the private JSONL input accepted by
``phase3_rule_author_packets --sources``.  It never derives an allowlist from
a complement, opens a held-out seal, or makes Ukrainian classification,
disposition, or rule decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as functional_roles
from scripts.projects.open_model_data import phase3_heldout_partition as heldout
from scripts.projects.open_model_data import phase3_near_duplicate as near_duplicate
from scripts.projects.open_model_data import phase3_rule_author_packets as packets

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_rule_author_source_rows_v1.schema.json"
PACKET_SCHEMA_PATH = DATA / "contracts/phase3_rule_author_packet_bundle_v1.schema.json"
SCRIPT_PATH = "scripts/projects/open_model_data/phase3_rule_author_source_rows.py"
PACKET_SCRIPT_PATH = "scripts/projects/open_model_data/phase3_rule_author_packets.py"
IMPLEMENTATION_VERSION = "phase3_rule_author_source_rows_v2_1"
ROWS_FILENAME = "rule_author_source_rows_v1.jsonl"
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
SHA256_LENGTH = 64


class SourceRowsError(ValueError):
    """A private source-row boundary cannot be established safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceRowsError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SourceRowsError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def receipt_body_sha256(receipt: Mapping[str, Any]) -> str:
    return sha256_bytes((canonical_json({key: value for key, value in receipt.items() if key != "receipt_sha256"}) + "\n").encode("utf-8"))


def _lstat(path: Path, label: str) -> os.stat_result:
    try:
        result = path.lstat()
    except OSError as exc:
        raise SourceRowsError(f"missing {label}: {path}") from exc
    require(not stat.S_ISLNK(result.st_mode), f"symlink is forbidden for {label}")
    return result


def _absolute_lexical(path: Path) -> Path:
    """Make a path absolute without resolving a terminal or parent symlink."""
    return Path(os.path.abspath(os.fspath(path)))


def _reject_symlink_components(path: Path, label: str) -> None:
    """Reject a symlink in any existing lexical component of ``path``."""
    absolute = _absolute_lexical(path)
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if not current.exists() and not current.is_symlink():
            return
        _lstat(current, label)


def _regular_file(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    result = _lstat(path, label)
    require(stat.S_ISREG(result.st_mode), f"{label} must be a regular file")


def read_json(path: Path, label: str = "JSON artifact") -> dict[str, Any]:
    _regular_file(path, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceRowsError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _schema_validator(definition: str) -> Draft202012Validator:
    schema = read_json(SCHEMA_PATH, "adapter schema")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator({"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"})


def _validate(value: Mapping[str, Any], definition: str, label: str) -> None:
    errors = sorted(_schema_validator(definition).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise SourceRowsError(f"{label} schema violation at {location}: {errors[0].message}")


def _prepare_private_dir(private_dir: Path) -> Path:
    _reject_symlink_components(private_dir, "private source-row directory")
    if private_dir.exists() or private_dir.is_symlink():
        result = _lstat(private_dir, "private source-row directory")
        require(stat.S_ISDIR(result.st_mode), "private source-row path must be a directory")
        require((result.st_mode & 0o777) == PRIVATE_DIR_MODE, "private source-row directory permissions too open")
    else:
        private_dir.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
        os.chmod(private_dir, PRIVATE_DIR_MODE)
    entries = list(private_dir.iterdir())
    for entry in entries:
        _lstat(entry, "private source-row directory entry")
        require(entry.name == ROWS_FILENAME and entry.is_file(), "unexpected file in private source-row directory")
        require((entry.stat().st_mode & 0o777) == PRIVATE_FILE_MODE, "private source-row file permissions drift")
    return private_dir / ROWS_FILENAME


def _prepare_public_receipt_path(path: Path) -> None:
    """Reject symlinked receipt destinations before an atomic replacement."""
    _reject_symlink_components(path, "public source-row receipt")
    if path.exists() or path.is_symlink():
        _regular_file(path, "public source-row receipt")
    ancestor = path.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    result = _lstat(ancestor, "public source-row receipt parent")
    require(stat.S_ISDIR(result.st_mode), "public source-row receipt parent must be a directory")


def _same_path(left: Path, right: Path) -> bool:
    if _absolute_lexical(left) == _absolute_lexical(right):
        return True
    try:
        return left.exists() and right.exists() and os.path.samefile(left, right)
    except OSError:
        return False


def _assert_output_paths_safe(
    *, private_dir: Path, public_receipt_path: Path, inputs: Sequence[Path], input_directories: Sequence[Path]
) -> None:
    rows_path = private_dir / ROWS_FILENAME
    private_absolute = _absolute_lexical(private_dir)
    public_absolute = _absolute_lexical(public_receipt_path)
    require(public_absolute != private_absolute and private_absolute not in public_absolute.parents, "public receipt may not be inside private source-row directory")
    require(not _same_path(public_receipt_path, rows_path), "public receipt aliases private source rows")
    for input_path in inputs:
        require(not _same_path(rows_path, input_path), "private source rows alias an input artifact")
        require(not _same_path(public_receipt_path, input_path), "public receipt aliases an input artifact")
    for input_directory in input_directories:
        directory_absolute = _absolute_lexical(input_directory)
        for output_path, label in (
            (private_absolute, "private source-row directory"),
            (_absolute_lexical(rows_path), "private source rows"),
            (public_absolute, "public receipt"),
        ):
            require(
                output_path != directory_absolute and directory_absolute not in output_path.parents,
                f"{label} may not be inside an input directory",
            )


def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            os.fchmod(handle.fileno(), mode)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            os.replace(temporary, path)
            os.chmod(path, mode)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise


_SAFE_BINDING_KEYS = frozenset(
    {
        "role",
        "role_name",
        "actor_role",
        "task_id",
        "attestation_task_id",
        "seat_id",
        "runtime_id",
        "binding_id",
    }
)


def _binding_identity_strings(binding: Mapping[str, Any]) -> set[str]:
    """Allow only known identity fields — never every nested string recursively."""
    allowed: set[str] = set()
    for key, value in binding.items():
        key_l = str(key).lower()
        if key_l not in _SAFE_BINDING_KEYS and not key_l.endswith("_id"):
            continue
        if isinstance(value, str) and value:
            allowed.add(value)
    return allowed


def _assert_public_safe(
    value: Any,
    *,
    path: str = "$",
    approved_strings: frozenset[str] | None = None,
) -> None:
    forbidden = ("unit_id", "locator", "fingerprint", "source_text", "corrected_text", "source_record", "error", "correct", "doc_id", "body")
    approved = approved_strings or frozenset(
        {
            "phase3_rule_author_source_rows_receipt_v2_1",
            IMPLEMENTATION_VERSION,
        }
    )
    if isinstance(value, Mapping):
        for key, item in value.items():
            lower = str(key).lower()
            if lower.endswith("policy_fingerprint_sha256") or lower == "partition_public_receipt_body_sha256":
                _assert_public_safe(item, path=f"{path}.{key}", approved_strings=approved)
                continue
            require(not any(token in lower for token in forbidden), f"receipt exposes forbidden field at {path}.{key}")
            _assert_public_safe(item, path=f"{path}.{key}", approved_strings=approved)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_public_safe(item, path=f"{path}[{index}]", approved_strings=approved)
    elif isinstance(value, str):
        require(
            value in approved
            or (len(value) == SHA256_LENGTH and all(char in "0123456789abcdef" for char in value))
            or (
                value.startswith("phase3_functional_action:")
                and len(value) == len("phase3_functional_action:") + SHA256_LENGTH
                and all(char in "0123456789abcdef" for char in value.removeprefix("phase3_functional_action:"))
            )
            or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is not None,
            f"receipt contains unapproved text at {path}",
        )


def _clearance_and_bindings(
    *,
    clearance_path: Path,
    public_partition_receipt_path: Path,
    source_universe_dir: Path,
    sources_db: Path,
    evaluation_path: Path,
    coverage_path: Path,
    role_path: Path,
    near_duplicate_policy_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, str], str, str]:
    clearance = read_json(clearance_path, "author clearance")
    partition_receipt = read_json(public_partition_receipt_path, "partition public receipt")
    _reject_symlink_components(source_universe_dir, "source-universe directory")
    source_dir_stat = _lstat(source_universe_dir, "source-universe directory")
    require(stat.S_ISDIR(source_dir_stat.st_mode), "source-universe path must be a directory")
    source_freeze_receipt = source_universe_dir / packets.LEDGER_RECEIPT
    _regular_file(source_freeze_receipt, "source-universe receipt")
    freeze_receipt = read_json(source_freeze_receipt, "source-universe receipt")
    families = freeze_receipt.get("families")
    require(isinstance(families, list), "source-universe family ledgers missing")
    ua_ledgers = [item for item in families if isinstance(item, Mapping) and item.get("family_id") == "ua_gec"]
    require(len(ua_ledgers) == 1, "source-universe lacks one UA-GEC ledger")
    ledger_name = ua_ledgers[0].get("ledger_file")
    require(isinstance(ledger_name, str) and Path(ledger_name).name == ledger_name, "unsafe UA-GEC ledger path")
    ledger_path = source_universe_dir / ledger_name
    _regular_file(ledger_path, "frozen UA-GEC ledger")
    ledger_sha = ua_ledgers[0].get("ledger_sha256")
    require(isinstance(ledger_sha, str) and ledger_sha == sha256_file(ledger_path), "frozen UA-GEC ledger hash drift")
    _regular_file(sources_db, "sources DB")
    _regular_file(evaluation_path, "evaluation contract")
    _regular_file(coverage_path, "coverage contract")
    _regular_file(role_path, "role contract")
    _regular_file(near_duplicate_policy_path, "near-duplicate policy")
    _regular_file(ROOT / PACKET_SCRIPT_PATH, "packet compiler")
    _regular_file(PACKET_SCHEMA_PATH, "packet compiler schema")

    try:
        near_duplicate.policy_for_governed_use(
            "public_canary_neighbour_exclusion",
            path=near_duplicate_policy_path,
            expected_fingerprint=near_duplicate.PINNED_POLICY_FINGERPRINT,
        )
    except near_duplicate.NearDuplicatePolicyError as exc:
        raise SourceRowsError(str(exc)) from exc

    clearance_file_sha = sha256_file(clearance_path)
    freeze_sha = sha256_file(source_freeze_receipt)
    try:
        packets.validate_clearance(
            clearance,
            clearance_sha256=clearance_file_sha,
            receipt_sha256=freeze_sha,
            evaluation_path=evaluation_path,
            coverage_path=coverage_path,
            role_path=role_path,
    )
    except packets.PacketCompilerError as exc:
        raise SourceRowsError(str(exc)) from exc
    require(partition_receipt.get("schema_version") == "phase3_heldout_public_receipt_v2_1", "wrong partition public receipt")
    require(partition_receipt.get("text_free") is True, "partition public receipt is not text-free")
    require(heldout.receipt_body_sha256(partition_receipt) == partition_receipt.get("receipt_sha256"), "partition public receipt hash drift")
    role_contract = read_json(role_path, "role contract")
    try:
        functional_roles.verify_value(role_contract)
        expected_steward = heldout.verify_role_binding(role_contract)
    except (functional_roles.FunctionalRoleError, heldout.PartitionError) as exc:
        raise SourceRowsError(str(exc)) from exc
    require(clearance.get("role_binding") == expected_steward, "clearance is not bound to assigned heldout steward")
    try:
        author = packets._derive_role_actor(role_contract, "rule_author_extractor")
    except packets.PacketCompilerError as exc:
        raise SourceRowsError(str(exc)) from exc
    require(author["task_id"] != expected_steward["task_id"], "heldout steward and rule author task IDs must be distinct")
    public_bindings = partition_receipt.get("input_bindings")
    require(isinstance(public_bindings, Mapping), "partition public input bindings missing")
    clearance_bindings = clearance["input_bindings"]
    for key, actual in {
        "phase3_v2_contract_sha256": functional_roles.BASE_SHA256,
        "phase3_v2_1_amendment_sha256": functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": functional_roles.COMBINED_SHA256,
        "source_universe_receipt_sha256": freeze_sha,
        "evaluation_contract_sha256": sha256_file(evaluation_path),
        "coverage_contract_sha256": sha256_file(coverage_path),
        "role_contract_sha256": sha256_file(role_path),
        "near_duplicate_policy_fingerprint_sha256": near_duplicate.PINNED_POLICY_FINGERPRINT,
    }.items():
        require(clearance_bindings.get(key) == actual, f"clearance {key} binding drift")
        require(public_bindings.get(key) == actual, f"partition public {key} binding drift")
    require(public_bindings.get("sources_db_sha256") == sha256_file(sources_db), "sources DB binding drift")
    for key in ("ua_eval_exclusion_manifest_sha256", "public_canary_exclusion_manifest_sha256"):
        require(clearance_bindings.get(key) == public_bindings.get(key), f"clearance {key} binding drift")
    action_receipt = clearance.get("action_receipt")
    require(isinstance(action_receipt, Mapping), "clearance action receipt missing")
    try:
        expected_action_receipt = heldout.build_action_receipt(
            role_contract=role_contract,
            role_contract_path=role_path,
            input_bindings=clearance_bindings,
            output=clearance.get("cleared_units"),
            execution_metadata=heldout.execution_metadata_from_action(action_receipt),
        )
    except heldout.PartitionError as exc:
        raise SourceRowsError(str(exc)) from exc
    require(action_receipt == expected_action_receipt, "clearance action receipt drift")
    artifact_hashes = partition_receipt.get("artifact_hashes")
    require(isinstance(artifact_hashes, Mapping), "partition artifact hashes missing")
    require(artifact_hashes.get("author_clearance_sha256") == clearance.get("receipt_sha256"), "clearance receipt binding drift")
    require(partition_receipt.get("action_receipt") == clearance.get("action_receipt"), "partition action evidence drift")
    for field in ("heldout_excluded", "ua_eval_exclusion_enforced", "public_canary_exclusion_enforced"):
        require(clearance.get(field) is True, f"clearance {field} is not exactly true")
    require(clearance.get("heldout_complement_encoded") is False, "clearance encodes a heldout complement")
    return clearance, partition_receipt, expected_steward, author, clearance_file_sha, str(ledger_sha)


def _row_from_reconstructed(row: Mapping[str, Any]) -> dict[str, Any]:
    require(row.get("family_id") == "ua_gec", "reconstructed non-UA-GEC row")
    require(row.get("split") == "train", "non-train row cannot enter source rows")
    source_record = row.get("source_record")
    require(isinstance(source_record, Mapping), "reconstruction lacks exact source record")
    normalized = packets.source_universe._normal(source_record)
    require(isinstance(normalized, Mapping), "source record normalization failed")
    require(row.get("unit_sha256") == packets.source_universe._unit_hash(normalized), "source record unit hash drift")
    source_text = normalized.get("error")
    corrected_text = normalized.get("correct")
    require(isinstance(source_text, str) and source_text and isinstance(corrected_text, str), "source text pair malformed")
    for field in ("error_type", "annotator_id", "is_native", "source_lang"):
        require(normalized.get(field) == row.get(field), f"reconstructed {field} drift")
    locator = heldout.frozen_locator_binding(row["locator"])
    output = {
        "family_id": "ua_gec",
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "source_locator": locator,
        "source_text": source_text,
        "corrected_text": corrected_text,
        "source_record": normalized,
        "span_start": 0,
        "span_end": len(source_text),
        "source_sha256": sha256_bytes(source_text.encode("utf-8")),
        "candidate_signals": [],
        "heldout": False,
        "ua_eval": False,
        "public_canary_neighbour": False,
    }
    _validate(output, "sourceRow", "source row")
    try:
        packets._item_from_row(output, "0" * SHA256_LENGTH, near_duplicate.PINNED_POLICY_FINGERPRINT)
    except packets.PacketCompilerError as exc:
        raise SourceRowsError(f"adapter output is not packet-compiler compatible: {exc}") from exc
    return output


def build(
    *,
    clearance_path: Path,
    source_universe_dir: Path,
    sources_db: Path,
    public_partition_receipt_path: Path,
    evaluation_path: Path,
    coverage_path: Path,
    role_path: Path,
    near_duplicate_policy_path: Path,
    private_dir: Path,
    public_receipt_path: Path,
) -> dict[str, Any]:
    """Build exact allowlisted private rows and a text-free aggregate receipt."""
    inputs = (
        clearance_path,
        source_universe_dir,
        sources_db,
        public_partition_receipt_path,
        evaluation_path,
        coverage_path,
        role_path,
        near_duplicate_policy_path,
        SCHEMA_PATH,
        PACKET_SCHEMA_PATH,
        ROOT / PACKET_SCRIPT_PATH,
        ROOT / SCRIPT_PATH,
    )
    for input_path in inputs:
        _reject_symlink_components(input_path, "input artifact")
    _prepare_public_receipt_path(public_receipt_path)
    _assert_output_paths_safe(
        private_dir=private_dir,
        public_receipt_path=public_receipt_path,
        inputs=inputs,
        input_directories=(source_universe_dir,),
    )
    rows_path = _prepare_private_dir(private_dir)
    clearance, partition_receipt, steward, author, clearance_file_sha, ledger_sha = _clearance_and_bindings(
        clearance_path=clearance_path,
        public_partition_receipt_path=public_partition_receipt_path,
        source_universe_dir=source_universe_dir,
        sources_db=sources_db,
        evaluation_path=evaluation_path,
        coverage_path=coverage_path,
        role_path=role_path,
        near_duplicate_policy_path=near_duplicate_policy_path,
    )
    freeze_units = heldout._load_freeze_ua_gec_units(source_universe_dir)
    try:
        reconstructed = heldout.reconstruct_ua_gec_rows(sources_db=sources_db, freeze_units=freeze_units)
    except heldout.PartitionError as exc:
        raise SourceRowsError(str(exc)) from exc
    cleared = clearance.get("cleared_units")
    require(isinstance(cleared, list), "clearance cleared units missing")
    allowed = {(item.get("family_id"), item.get("unit_id")): item.get("unit_sha256") for item in cleared if isinstance(item, Mapping)}
    require(len(allowed) == len(cleared), "clearance has duplicate or malformed units")
    require(clearance.get("cleared_unit_count") == len(allowed), "clearance count drift")
    live = {(item["family_id"], item["unit_id"]): item for item in reconstructed}
    require(set(allowed) <= set(live), "clearance references missing frozen source unit")
    rows: list[dict[str, Any]] = []
    for key in sorted(allowed):
        row = live[key]
        require(allowed[key] == row["unit_sha256"], "clearance unit hash drift")
        rows.append(_row_from_reconstructed(row))
    actual = {(row["family_id"], row["unit_id"]) for row in rows}
    require(actual == set(allowed), "source rows must equal clearance exactly; complement inference is forbidden")
    payload = "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")
    _atomic_write(rows_path, payload, PRIVATE_FILE_MODE)
    require((rows_path.stat().st_mode & 0o777) == PRIVATE_FILE_MODE, "private source-row file permissions too open")
    receipt = {
        "schema_version": "phase3_rule_author_source_rows_receipt_v2_1",
        "text_free": True,
        "implementation_version": IMPLEMENTATION_VERSION,
        "role_binding": steward,
        "rule_author_binding": author,
        "action_receipt": clearance["action_receipt"],
        "input_bindings": {
            "phase3_v2_contract_sha256": clearance["input_bindings"]["phase3_v2_contract_sha256"],
            "phase3_v2_1_amendment_sha256": clearance["input_bindings"]["phase3_v2_1_amendment_sha256"],
            "combined_contract_sha256": clearance["input_bindings"]["combined_contract_sha256"],
            "source_universe_receipt_sha256": sha256_file(source_universe_dir / packets.LEDGER_RECEIPT),
            "ua_gec_ledger_sha256": ledger_sha,
            "sources_db_sha256": sha256_file(sources_db),
            "evaluation_contract_sha256": sha256_file(evaluation_path),
            "coverage_contract_sha256": sha256_file(coverage_path),
            "role_contract_sha256": sha256_file(role_path),
            "conflict_graph_sha256": functional_roles.conflict_graph_sha256(read_json(role_path, "role contract")),
            "near_duplicate_policy_sha256": sha256_file(near_duplicate_policy_path),
            "near_duplicate_policy_fingerprint_sha256": near_duplicate.PINNED_POLICY_FINGERPRINT,
            "author_clearance_receipt_sha256": clearance["receipt_sha256"],
            "author_clearance_file_sha256": clearance_file_sha,
            "partition_public_receipt_body_sha256": partition_receipt["receipt_sha256"],
            "partition_public_receipt_file_sha256": sha256_file(public_partition_receipt_path),
            "compiler_script_sha256": sha256_file(ROOT / PACKET_SCRIPT_PATH),
            "compiler_schema_sha256": sha256_file(PACKET_SCHEMA_PATH),
            "adapter_script_sha256": sha256_file(ROOT / SCRIPT_PATH),
            "adapter_schema_sha256": sha256_file(SCHEMA_PATH),
        },
        "exclusions": {
            "heldout_excluded": True,
            "ua_eval_exclusion_enforced": True,
            "public_canary_exclusion_enforced": True,
            "complement_inference_used": False,
            "all_rows_train": True,
            "clearance_source_row_set_equal": True,
        },
        "aggregates": {"source_row_count": len(rows)},
        "source_rows_sha256": sha256_bytes(payload),
    }
    receipt["receipt_sha256"] = receipt_body_sha256(receipt)
    _validate(receipt, "receipt", "source-row receipt")
    approved = frozenset(
        {
            "phase3_rule_author_source_rows_receipt_v2_1",
            IMPLEMENTATION_VERSION,
            "heldout_steward",
            "rule_author_extractor",
            "phase3-v2-1-heldout-stewardship",
            "phase3-v2-1-rule-author-extraction",
            "partition_seal_and_clear_author_units",
            "local",
            "phase3-heldout-partition-v1",
            "deterministic",
            "local-python",
            "phase3-v2-1-evaluation-cycle-001",
            "completed",
            * _binding_identity_strings(steward),
            * _binding_identity_strings(author),
        }
    )
    _assert_public_safe(receipt, approved_strings=approved)
    _atomic_write(public_receipt_path, (canonical_json(receipt) + "\n").encode("utf-8"), PRIVATE_FILE_MODE)
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clearance", type=Path, required=True)
    parser.add_argument("--source-universe", type=Path, required=True)
    parser.add_argument("--sources-db", type=Path, required=True)
    parser.add_argument("--partition-public-receipt", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--role", type=Path, required=True)
    parser.add_argument("--near-duplicate-policy", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--public-receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = build(
            clearance_path=args.clearance, source_universe_dir=args.source_universe,
            sources_db=args.sources_db, public_partition_receipt_path=args.partition_public_receipt,
            evaluation_path=args.evaluation, coverage_path=args.coverage, role_path=args.role,
            near_duplicate_policy_path=args.near_duplicate_policy, private_dir=args.private_dir,
            public_receipt_path=args.public_receipt,
        )
    except SourceRowsError as exc:
        parser.error(str(exc))
    sys.stdout.write(canonical_json(receipt) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
