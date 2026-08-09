#!/usr/bin/env python3
"""Deterministic private transport for the Phase 3 v2.1 heldout label lane.

This module prepares private packets, records already-obtained reviewer bytes,
and assembles sealed labels.  It never calls a provider and never transports
author packets.  The only accepted reviewer lane is OpenAI/Codex gpt-5.6-sol.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as roles

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
DEFAULT_SCHEMA = DATA / "contracts/phase3_heldout_label_transport_bundle_v1.schema.json"
DEFAULT_LABEL_PROMPT = DATA / "contracts/phase3_heldout_clean_modern_label_prompt_v1.md"
DEFAULT_ROLE_CONTRACT = DATA / "evidence/correction_protection_functional_role_contract_v2_1.json"
DEFAULT_EVALUATION_CONTRACT = DATA / "evidence/correction_protection_evaluation_contract_v1.json"
DEFAULT_CYCLE002_LABEL_PROMPT = DATA / "contracts/phase3_heldout_semantic_gold_label_prompt_v1.md"
DEFAULT_CYCLE002_ROLE_CONTRACT = DATA / "evidence/correction_protection_functional_role_contract_v2_2.json"
DEFAULT_CYCLE002_EVALUATION_CONTRACT = DATA / "evidence/correction_protection_evaluation_contract_v2_2.json"
ROW_COUNT = 2000
MATERIALIZATION_COUNT = 67041
LABEL_PROMPT_SHA256 = "d607e77fd20ef037385bce365f8854fe51e308ce3b05cafc71ea795e32e37195"
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
ROLE_ID = "heldout_label_reviewer"
TASK_ID = "phase3-v2-1-heldout-label-review"
ACTOR = {
    "role_id": ROLE_ID,
    "task_id": TASK_ID,
    "provider": "openai",
    "model_family": "openai",
    "harness": "codex",
    "exact_model": "gpt-5.6-sol",
}
MANIFEST_NAME = "manifest.json"
REJECT_CODES = frozenset(
    {
        "reject_fragment_or_too_short",
        "reject_exercise_or_task_prompt",
        "reject_error_or_contrast_example",
        "reject_table_list_formula_code",
        "reject_metalinguistic_or_grammar_talk",
        "reject_quoted_literary_or_anthology",
        "reject_archaic_historical_language",
        "reject_dialectal_regional_surzhyk",
        "reject_foreign_or_translation_artifact",
        "reject_learner_or_simplified_broken",
        "reject_parallel_norm_or_pre2026_only",
        "reject_mixed_or_uncertain",
        "reject_insufficient_locator_evidence",
    }
)
AGREE_GENRES = frozenset({"expository_narrative", "scientific_expository", "instructional_content_expository"})

# Cycle002 deliberately reuses the sealed cycle001 identity population.  These
# are input custody pins, not a source of text or labels.
CYCLE002_ID = "phase3-v2-1-evaluation-cycle-002"
CYCLE002_ROW_COUNT = 9392
CYCLE002_PARTITION_SHA256 = "3797e005d7c461f192dacb06e23a9028121bd73cb240f2c2851953a83955aa7d"
CYCLE002_MATERIALIZATION_SHA256 = "e9d89b8fae5193a29a8c3dd055f464fc1290c18f507b669f3efb0720644f6d8c"
CYCLE002_PACKET_LIMIT = 40
CYCLE002_PACKET_BYTE_LIMIT = 196_608
CYCLE002_LABEL_PROMPT_SHA256 = "25d8f5a0d13323fc793860d233e903bcb800799641fc2ea19f3f9de731efce9b"
CYCLE002_PHENOMENA = (
    "direct_address_vocative",
    "impersonal_no_to_expressed_agent",
    "prepositional_government_valency",
    "pravopys_parallel_norms",
    "participial_versus_lexicalized_chyi",
    "numeral_agreement",
    "semantic_false_friends_interlanguage_homonyms",
    "lexical_interference",
    "phrase_collocation",
    "orthography",
    "punctuation",
    "syntactic_calque",
)
CYCLE002_ROLES = frozenset({"positive", "acceptable_control", "protected"})
CYCLE002_GENRES = AGREE_GENRES
CYCLE002_ACTORS = {
    "a": {
        "role_id": "heldout_label_reviewer",
        "task_id": "phase3-v2-2-heldout-semantic-label-pass-a",
        "provider": "openai",
        "model_family": "openai",
        "harness": "codex",
        "exact_model": "gpt-5.6-sol",
    },
    "b": {
        "role_id": "heldout_label_reviewer",
        "task_id": "phase3-v2-2-heldout-semantic-label-pass-b",
        "provider": "openai",
        "model_family": "openai",
        "harness": "codex",
        "exact_model": "gpt-5.6-sol",
    },
}


class HeldoutLabelTransportError(ValueError):
    """Raised when private heldout-label custody or bindings drift."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise HeldoutLabelTransportError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes((canonical_json(value) + "\n").encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise HeldoutLabelTransportError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _reject_symlink_components(path: Path, label: str) -> None:
    current = Path(_absolute(path).anchor)
    for component in _absolute(path).parts[1:]:
        current /= component
        if not current.exists() and not current.is_symlink():
            return
        require(not current.is_symlink(), f"symlink forbidden for {label}")


def _regular(path: Path, label: str) -> None:
    _reject_symlink_components(path, label)
    try:
        state = path.lstat()
    except OSError as exc:
        raise HeldoutLabelTransportError(f"missing {label}") from exc
    require(stat.S_ISREG(state.st_mode) and not path.is_symlink(), f"{label} must be a regular non-symlink file")


def _strict_json_bytes(raw: bytes, label: str, top: type[Any] = dict) -> Any:
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HeldoutLabelTransportError(f"invalid strict JSON: {label}") from exc
    require(isinstance(value, top), f"{label} top-level type drift")
    return value


def _read_json(path: Path, label: str, top: type[Any] = dict) -> Any:
    _regular(path, label)
    return _strict_json_bytes(path.read_bytes(), label, top)


def _private_root(path: Path, *, create: bool) -> Path:
    _reject_symlink_components(path, "private directory")
    if create:
        path.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
        os.chmod(path, PRIVATE_DIR_MODE)
    require(path.is_dir() and not path.is_symlink(), "private directory must be real")
    require(stat.S_IMODE(path.stat().st_mode) == PRIVATE_DIR_MODE, "private directory must be mode 0700")
    return path


def _assert_private_tree(root: Path) -> None:
    for path in root.rglob("*"):
        require(not path.is_symlink(), "symlink forbidden in private transport tree")
        if path.is_dir():
            require(stat.S_IMODE(path.stat().st_mode) == PRIVATE_DIR_MODE, "private directory mode drift")
        elif path.is_file():
            require(stat.S_IMODE(path.stat().st_mode) == PRIVATE_FILE_MODE, "private file mode drift")
        else:
            raise HeldoutLabelTransportError("private transport tree has unsafe entry")


def _write_private(path: Path, payload: bytes) -> str:
    _reject_symlink_components(path.parent, "private output parent")
    path.parent.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    os.chmod(path.parent, PRIVATE_DIR_MODE)
    if path.exists() or path.is_symlink():
        _regular(path, "private output")
        require(stat.S_IMODE(path.stat().st_mode) == PRIVATE_FILE_MODE, "private output must be mode 0600")
        require(path.read_bytes() == payload, "immutable private output drift")
        return sha256_bytes(payload)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), PRIVATE_FILE_MODE)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_FILE_MODE)
    except BaseException:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise
    return sha256_bytes(payload)


def _write_private_json(path: Path, value: Any) -> str:
    return _write_private(path, (canonical_json(value) + "\n").encode("utf-8"))


def _assert_output_not_in_inputs(outputs: Sequence[Path], inputs: Sequence[Path]) -> None:
    for output in outputs:
        candidate = _absolute(output)
        for source in inputs:
            source_abs = _absolute(source)
            require(
                candidate != source_abs and source_abs not in candidate.parents and candidate not in source_abs.parents,
                "output may not be inside an input artifact",
            )


def _validate_schema(value: Mapping[str, Any], schema_path: Path, definition: str) -> None:
    schema = _read_json(schema_path, "transport schema")
    Draft202012Validator.check_schema(schema)
    wrapper = (
        schema
        if definition == "manifest"
        else {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"}
    )
    errors = sorted(Draft202012Validator(wrapper).iter_errors(value), key=lambda error: list(error.path))
    require(not errors, f"{definition} schema violation: {errors[0].message if errors else ''}")


def _actor(value: Mapping[str, Any] | None = None) -> dict[str, str]:
    supplied = dict(ACTOR if value is None else value)
    require(supplied == ACTOR, "only OpenAI/Codex gpt-5.6-sol heldout_label_reviewer is allowed")
    return dict(ACTOR)


def _role_contract(path: Path) -> tuple[dict[str, Any], str]:
    value = _read_json(path, "functional role contract")
    try:
        roles.verify_value(value)
    except roles.FunctionalRoleError as exc:
        raise HeldoutLabelTransportError(str(exc)) from exc
    entry = next(item for item in value["functional_roles"] if item["role_id"] == ROLE_ID)
    require(
        {key: entry[key] for key in ("role_id", "task_id", "exact_model", "model_family", "harness")}
        == {key: ACTOR[key] for key in ("role_id", "task_id", "exact_model", "model_family", "harness")},
        "heldout label role binding drift",
    )
    return value, sha256_file(path)


def _evaluation_contract(path: Path, cycle: str) -> str:
    value = _read_json(path, "evaluation contract")
    require(
        value.get("functional_role_evaluation_cycle", {}).get("evaluation_cycle_id") == cycle,
        "evaluation-cycle binding drift",
    )
    return sha256_file(path)


def _label_prompt(path: Path) -> str:
    """Verify the exact tracked rubric without exposing source packets."""
    _regular(path, "heldout label prompt")
    digest = sha256_file(path)
    require(digest == LABEL_PROMPT_SHA256, "heldout label prompt hash drift")
    return digest


def _materialization(path: Path, receipt_path: Path) -> tuple[list[dict[str, Any]], str, str]:
    receipt = _read_json(receipt_path, "materialization receipt")
    _regular(path, "materialization JSONL")
    raw = path.read_bytes()
    require(
        receipt.get("schema_version") == "phase3_source_unit_materialization_receipt_v1",
        "materialization receipt schema drift",
    )
    require(receipt.get("private_record_count") == MATERIALIZATION_COUNT, "materialization denominator drift")
    require(receipt.get("private_jsonl_sha256") == sha256_bytes(raw), "materialization receipt hash drift")
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(raw.splitlines(), start=1):
        row = _strict_json_bytes(line, f"materialization row {number}")
        require(
            set(row)
            == {
                "family_id",
                "unit_id",
                "unit_sha256",
                "frozen_locator",
                "frozen_locator_sha256",
                "document_or_edition_identity",
                "source_text",
                "source_record",
                "source_text_sha256",
            },
            "materialization row shape drift",
        )
        rows.append(row)
    require(
        len(rows) == MATERIALIZATION_COUNT and len({row["unit_id"] for row in rows}) == MATERIALIZATION_COUNT,
        "materialization bijection drift",
    )
    return rows, sha256_file(receipt_path), sha256_bytes(raw)


def _partition(
    path: Path, freeze_receipt_path: Path, materialization_hash: str, cycle: str
) -> tuple[list[dict[str, Any]], str, str]:
    receipt = _read_json(freeze_receipt_path, "evaluation freeze receipt")
    _regular(path, "frozen partition manifest")
    raw = path.read_bytes()
    require(
        receipt.get("schema_version") == "phase3_evaluation_partition_receipt_v1",
        "evaluation freeze receipt schema drift",
    )
    bindings = receipt.get("input_bindings")
    require(
        isinstance(bindings, Mapping) and bindings.get("evaluation_cycle_id") == cycle, "evaluation freeze cycle drift"
    )
    require(
        bindings.get("source_materialization_jsonl_sha256") == materialization_hash,
        "evaluation freeze materialization binding drift",
    )
    require(
        receipt.get("artifact_hashes", {}).get("partition_manifest_sha256") == sha256_bytes(raw),
        "frozen partition hash drift",
    )
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(raw.splitlines(), start=1):
        row = _strict_json_bytes(line, f"partition row {number}")
        require(
            set(row)
            == {
                "family_id",
                "unit_id",
                "unit_sha256",
                "reason",
                "candidate_lane",
                "source_text_sha256",
                "frozen_locator_sha256",
            },
            "partition row shape drift",
        )
        rows.append(row)
    require(len(rows) == 9392 and len({row["unit_id"] for row in rows}) == 9392, "frozen partition denominator drift")
    selected = [row for row in rows if row["candidate_lane"] == "clean_modern"]
    require(len(selected) == ROW_COUNT, "clean_modern selection must be exactly 2,000")
    require(all(row["reason"] == "evaluation_only" for row in selected), "non-selected row entered heldout label lane")
    return selected, sha256_file(freeze_receipt_path), sha256_bytes(raw)


def _identity(row: Mapping[str, Any]) -> list[str]:
    unit_id, unit_sha256 = row.get("unit_id"), row.get("unit_sha256")
    require(
        isinstance(unit_id, str) and unit_id and isinstance(unit_sha256, str) and len(unit_sha256) == 64,
        "unit identity drift",
    )
    return [unit_id, unit_sha256]


def _packet_rows(
    selected: Sequence[Mapping[str, Any]], materialized: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    by_identity = {(row["unit_id"], row["unit_sha256"]): row for row in materialized}
    require(len(by_identity) == MATERIALIZATION_COUNT, "materialization identity duplicate")
    output: list[dict[str, Any]] = []
    for row in selected:
        key = (row["unit_id"], row["unit_sha256"])
        source = by_identity.get(key)
        require(source is not None, "selected partition row is absent from materialization")
        require(
            source["family_id"] == row["family_id"]
            and source["source_text_sha256"] == row["source_text_sha256"]
            and source["frozen_locator_sha256"] == row["frozen_locator_sha256"],
            "selected/materialization join drift",
        )
        output.append(dict(source))
    require(len({_identity(row)[0] for row in output}) == ROW_COUNT, "selected materialization bijection drift")
    return output


def _bindings(
    *,
    role_hash: str,
    graph_hash: str,
    cycle: str,
    evaluation_hash: str,
    materialization_receipt_hash: str,
    materialization_hash: str,
    freeze_receipt_hash: str,
    partition_hash: str,
    label_prompt_hash: str,
    selected: Sequence[Mapping[str, Any]],
    packet_order: Sequence[int],
) -> dict[str, Any]:
    return {
        "base_contract_sha256": roles.BASE_SHA256,
        "amendment_sha256": roles.AMENDMENT_SHA256,
        "combined_contract_sha256": roles.COMBINED_SHA256,
        "functional_role_contract_sha256": role_hash,
        "conflict_graph_sha256": graph_hash,
        "evaluation_cycle_id": cycle,
        "evaluation_contract_sha256": evaluation_hash,
        "label_prompt_sha256": label_prompt_hash,
        "materialization_receipt_sha256": materialization_receipt_hash,
        "materialization_jsonl_sha256": materialization_hash,
        "evaluation_freeze_receipt_sha256": freeze_receipt_hash,
        "partition_manifest_sha256": partition_hash,
        "selection_set_sha256": sha256_value([_identity(row) for row in selected]),
        "packet_order_sha256": sha256_value(list(packet_order)),
    }


def _packet(
    packet_index: int, packet_count: int, rows: Sequence[Mapping[str, Any]], bindings: Mapping[str, Any]
) -> dict[str, Any]:
    value = {
        "schema_version": "phase3_heldout_label_packet_v1",
        "packet_index": packet_index,
        "packet_count": packet_count,
        "bindings": dict(bindings),
        "actor": dict(ACTOR),
        "rows": list(rows),
    }
    value["packet_id"] = "heldout_label_packet:" + sha256_value(value)
    return value


def prepare(
    *,
    partition_path: Path,
    materialization_jsonl: Path,
    materialization_receipt_path: Path,
    evaluation_freeze_receipt_path: Path,
    private_dir: Path,
    label_prompt_path: Path = DEFAULT_LABEL_PROMPT,
    role_contract_path: Path = DEFAULT_ROLE_CONTRACT,
    evaluation_contract_path: Path = DEFAULT_EVALUATION_CONTRACT,
    schema_path: Path = DEFAULT_SCHEMA,
    packet_size: int = 40,
    actor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare immutable private packets; no provider call is performed."""
    _actor(actor)  # Must precede all source-bearing input reads.
    require(isinstance(packet_size, int) and packet_size > 0, "packet size must be positive")
    _assert_output_not_in_inputs(
        (private_dir,),
        (
            partition_path,
            materialization_jsonl,
            materialization_receipt_path,
            evaluation_freeze_receipt_path,
            role_contract_path,
            evaluation_contract_path,
            schema_path,
            label_prompt_path,
        ),
    )
    role, role_hash = _role_contract(role_contract_path)
    cycle = role["evaluation_cycle"]["evaluation_cycle_id"]
    evaluation_hash = _evaluation_contract(evaluation_contract_path, cycle)
    label_prompt_hash = _label_prompt(label_prompt_path)
    materialized, materialization_receipt_hash, materialization_hash = _materialization(
        materialization_jsonl, materialization_receipt_path
    )
    selected, freeze_receipt_hash, partition_hash = _partition(
        partition_path, evaluation_freeze_receipt_path, materialization_hash, cycle
    )
    rows = _packet_rows(selected, materialized)
    packet_count = (ROW_COUNT + packet_size - 1) // packet_size
    bindings = _bindings(
        role_hash=role_hash,
        graph_hash=roles.conflict_graph_sha256(role),
        cycle=cycle,
        evaluation_hash=evaluation_hash,
        materialization_receipt_hash=materialization_receipt_hash,
        materialization_hash=materialization_hash,
        freeze_receipt_hash=freeze_receipt_hash,
        partition_hash=partition_hash,
        label_prompt_hash=label_prompt_hash,
        selected=selected,
        packet_order=range(1, packet_count + 1),
    )
    root = _private_root(private_dir, create=True)
    _assert_private_tree(root)
    packet_bindings: list[dict[str, Any]] = []
    for index in range(1, packet_count + 1):
        current = rows[(index - 1) * packet_size : index * packet_size]
        value = _packet(index, packet_count, current, bindings)
        raw_hash = _write_private_json(root / "packets" / f"{index:04d}.json", value)
        packet_bindings.append(
            {
                "packet_index": index,
                "packet_id": value["packet_id"],
                "packet_sha256": raw_hash,
                "row_count": len(current),
                "identity_set_sha256": sha256_value([_identity(row) for row in current]),
            }
        )
    manifest = {
        "schema_version": "phase3_heldout_label_manifest_v1",
        "text_free": True,
        "bindings": bindings,
        "packet_count": packet_count,
        "row_count": ROW_COUNT,
        "packets": packet_bindings,
    }
    manifest["manifest_sha256"] = sha256_value(manifest)
    _validate_schema(manifest, schema_path, "manifest")
    _write_private_json(root / MANIFEST_NAME, manifest)
    return manifest


def _manifest(path: Path, schema_path: Path) -> dict[str, Any]:
    value = _read_json(path, "heldout label manifest")
    _validate_schema(value, schema_path, "manifest")
    body = dict(value)
    claimed = body.pop("manifest_sha256")
    require(claimed == sha256_value(body), "manifest hash drift")
    require(
        value["row_count"] == ROW_COUNT and len(value["packets"]) == value["packet_count"],
        "manifest packet denominator drift",
    )
    require(
        [item["packet_index"] for item in value["packets"]] == list(range(1, value["packet_count"] + 1)),
        "manifest packet order drift",
    )
    require(
        value["bindings"]["packet_order_sha256"] == sha256_value(list(range(1, value["packet_count"] + 1))),
        "manifest packet-order binding drift",
    )
    return value


def _load_packet(manifest: Mapping[str, Any], root: Path, packet_index: int) -> dict[str, Any]:
    require(1 <= packet_index <= manifest["packet_count"], "packet index out of range")
    path = root / "packets" / f"{packet_index:04d}.json"
    binding = manifest["packets"][packet_index - 1]
    _regular(path, "private packet")
    require(sha256_file(path) == binding["packet_sha256"], "private packet hash drift")
    value = _read_json(path, "private packet")
    body = dict(value)
    packet_id = body.pop("packet_id", None)
    require(packet_id == "heldout_label_packet:" + sha256_value(body), "packet identity drift")
    require(
        value.get("packet_index") == packet_index
        and value.get("packet_count") == manifest["packet_count"]
        and value.get("packet_id") == binding["packet_id"]
        and value.get("bindings") == manifest["bindings"]
        and value.get("actor") == ACTOR,
        "packet binding drift",
    )
    require(
        len(value.get("rows", [])) == binding["row_count"]
        and sha256_value([_identity(row) for row in value["rows"]]) == binding["identity_set_sha256"],
        "packet row order drift",
    )
    return value


def _parse_response(raw: bytes, packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    response = _strict_json_bytes(raw, "reviewer response")
    require(set(response) == {"labels"} and isinstance(response["labels"], list), "reviewer response shape drift")
    labels = response["labels"]
    expected = [_identity(row) for row in packet["rows"]]
    observed: list[list[str]] = []
    for label in labels:
        require(isinstance(label, Mapping), "reviewer label shape drift")
        require(
            set(label) == {"unit_id", "unit_sha256", "decision_code", "clean_modern_standard_prose", "modern_genre_id"},
            "reviewer label shape drift",
        )
        observed.append(_identity(label))
        decision = label["decision_code"]
        standard = label["clean_modern_standard_prose"]
        genre = label["modern_genre_id"]
        require(isinstance(decision, str) and type(standard) is bool, "reviewer label value type drift")
        if decision == "agree":
            require(
                standard is True and isinstance(genre, str) and genre in AGREE_GENRES,
                "agree label semantics drift",
            )
        else:
            require(
                decision in REJECT_CODES and standard is False and genre is None,
                "reject label semantics drift",
            )
    require(
        observed == expected and len(set(map(tuple, observed))) == len(expected),
        "reviewer identity/order bijection drift",
    )
    return [dict(label) for label in labels]


def _invalid_first(packet: Mapping[str, Any], raw: bytes) -> str | None:
    try:
        response = _strict_json_bytes(raw, "first reviewer response")
    except HeldoutLabelTransportError:
        return "strict_json"
    if not (set(response) == {"labels"} and isinstance(response["labels"], list)):
        return "response_shape"
    try:
        _parse_response(raw, packet)
    except HeldoutLabelTransportError as exc:
        if "identity/order bijection" in str(exc):
            return "identity_order"
        return "label_schema_or_semantics"
    return None


def ingest(
    *,
    manifest_path: Path,
    packet_index: int,
    raw_response_path: Path,
    private_dir: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    actor: Mapping[str, Any] | None = None,
    attempt_kind: str = "first",
    invalid_first_raw_path: Path | None = None,
) -> dict[str, Any]:
    """Ingest one already-obtained raw response, preserving it before parsing."""
    _actor(actor)
    require(attempt_kind in {"first", "retry-01"}, "attempt kind drift")
    _assert_output_not_in_inputs(
        (private_dir,), (raw_response_path, *([invalid_first_raw_path] if invalid_first_raw_path else []), schema_path)
    )
    root = _private_root(private_dir, create=False)
    _assert_private_tree(root)
    manifest = _manifest(manifest_path, schema_path)
    packet = _load_packet(manifest, root, packet_index)
    _regular(raw_response_path, "raw reviewer response")
    raw = raw_response_path.read_bytes()
    labels = _parse_response(raw, packet)
    invalid_hash: str | None = None
    invalid_reason: str | None = None
    if attempt_kind == "retry-01":
        require(invalid_first_raw_path is not None, "retry requires preserved invalid first response")
        _regular(invalid_first_raw_path, "invalid first reviewer response")
        invalid = invalid_first_raw_path.read_bytes()
        invalid_reason = _invalid_first(packet, invalid)
        require(invalid_reason is not None, "retry forbidden after valid first response")
        invalid_hash = _write_private(root / "invalid-first" / f"{packet_index:04d}.raw", invalid)
    else:
        require(invalid_first_raw_path is None, "first attempt cannot include retry evidence")
    raw_hash = _write_private(root / "raw" / f"{packet_index:04d}.raw", raw)
    response_hash = _write_private_json(root / "responses" / f"{packet_index:04d}.json", {"labels": labels})
    bindings_sha256 = sha256_value(manifest["bindings"])
    sealed = [
        {
            "unit_id": label["unit_id"],
            "unit_sha256": label["unit_sha256"],
            "decision_code": label["decision_code"],
            "clean_modern_standard_prose": label["clean_modern_standard_prose"],
            "modern_genre_id": label["modern_genre_id"],
            "evaluation_cycle_id": manifest["bindings"]["evaluation_cycle_id"],
            "bindings_sha256": bindings_sha256,
            "reviewer": dict(ACTOR),
        }
        for label in labels
    ]
    sealed_hash = _write_private_json(root / "sealed" / f"{packet_index:04d}.json", sealed)
    receipt = {
        "schema_version": "phase3_heldout_label_transport_receipt_v1",
        "packet_index": packet_index,
        "packet_id": packet["packet_id"],
        "packet_sha256": sha256_file(root / "packets" / f"{packet_index:04d}.json"),
        "bindings": manifest["bindings"],
        "raw_sha256": raw_hash,
        "raw_byte_count": len(raw),
        "response_sha256": response_hash,
        "sealed_rows_sha256": sealed_hash,
        "attempt_kind": attempt_kind,
        "retry_count": 1 if attempt_kind == "retry-01" else 0,
        "invalid_first_raw_sha256": invalid_hash,
        "invalid_first_failure": invalid_reason,
        "actor": dict(ACTOR),
        "identity_order_bijection": True,
        "text_free": True,
    }
    receipt["receipt_sha256"] = sha256_value(receipt)
    _validate_schema(receipt, schema_path, "transportReceipt")
    _write_private_json(root / "transports" / f"{packet_index:04d}.json", receipt)
    return {"packet_index": packet_index, "raw_sha256": raw_hash, "sealed_rows_sha256": sealed_hash, "text_free": True}


def _transport(
    root: Path, manifest: Mapping[str, Any], index: int, schema_path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    packet = _load_packet(manifest, root, index)
    transport = _read_json(root / "transports" / f"{index:04d}.json", "transport receipt")
    _validate_schema(transport, schema_path, "transportReceipt")
    body = dict(transport)
    claimed = body.pop("receipt_sha256")
    require(claimed == sha256_value(body), "transport receipt hash drift")
    require(
        transport["packet_id"] == packet["packet_id"]
        and transport["packet_sha256"] == sha256_file(root / "packets" / f"{index:04d}.json")
        and transport["bindings"] == manifest["bindings"]
        and transport["actor"] == ACTOR,
        "transport actor or packet drift",
    )
    raw_path = root / "raw" / f"{index:04d}.raw"
    response_path = root / "responses" / f"{index:04d}.json"
    sealed_path = root / "sealed" / f"{index:04d}.json"
    for path in (raw_path, response_path, sealed_path):
        _regular(path, "transport private artifact")
    raw = raw_path.read_bytes()
    require(
        transport["raw_sha256"] == sha256_bytes(raw) and transport["raw_byte_count"] == len(raw),
        "raw response custody drift",
    )
    labels = _parse_response(raw, packet)
    response = _read_json(response_path, "parsed response")
    require(
        response == {"labels": labels} and transport["response_sha256"] == sha256_file(response_path),
        "parsed response custody drift",
    )
    sealed = _read_json(sealed_path, "sealed labels", list)
    bindings_sha256 = sha256_value(manifest["bindings"])
    expected = [
        {
            "unit_id": label["unit_id"],
            "unit_sha256": label["unit_sha256"],
            "decision_code": label["decision_code"],
            "clean_modern_standard_prose": label["clean_modern_standard_prose"],
            "modern_genre_id": label["modern_genre_id"],
            "evaluation_cycle_id": manifest["bindings"]["evaluation_cycle_id"],
            "bindings_sha256": bindings_sha256,
            "reviewer": dict(ACTOR),
        }
        for label in labels
    ]
    require(
        sealed == expected and transport["sealed_rows_sha256"] == sha256_file(sealed_path), "sealed label custody drift"
    )
    if transport["attempt_kind"] == "retry-01":
        first = root / "invalid-first" / f"{index:04d}.raw"
        _regular(first, "invalid first reviewer response")
        require(
            transport["invalid_first_raw_sha256"] == sha256_file(first)
            and transport["invalid_first_failure"] == _invalid_first(packet, first.read_bytes()),
            "retry evidence drift",
        )
    else:
        require(
            transport["invalid_first_raw_sha256"] is None and transport["invalid_first_failure"] is None,
            "first-response retry evidence drift",
        )
    return transport, sealed


def _public_safe(value: Any) -> None:
    forbidden = {
        "unit_id",
        "unit_sha256",
        "label",
        "labels",
        "source_text",
        "source_record",
        "locator",
        "raw",
        "response",
        "packet_id",
    }
    if isinstance(value, Mapping):
        require(not (set(value) & forbidden), "public receipt leaks private text or identity")
        for child in value.values():
            _public_safe(child)
    elif isinstance(value, list):
        for child in value:
            _public_safe(child)


def assemble(
    *,
    manifest_path: Path,
    private_dir: Path,
    public_receipt_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    actor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail closed unless every immutable packet has exactly one valid transport."""
    _actor(actor)
    _assert_output_not_in_inputs((public_receipt_path,), (manifest_path, schema_path))
    root = _private_root(private_dir, create=False)
    public_absolute = _absolute(public_receipt_path)
    require(
        root != public_absolute and root not in public_absolute.parents,
        "public receipt may not be inside private heldout tree",
    )
    _assert_private_tree(root)
    manifest = _manifest(manifest_path, schema_path)
    sealed_rows: list[dict[str, Any]] = []
    for index in range(1, manifest["packet_count"] + 1):
        _, sealed = _transport(root, manifest, index, schema_path)
        sealed_rows.extend(sealed)
    identities = [_identity(row) for row in sealed_rows]
    require(
        len(sealed_rows) == ROW_COUNT and sha256_value(identities) == manifest["bindings"]["selection_set_sha256"],
        "incomplete, duplicate, or out-of-order sealed labels",
    )
    sealed_hash = _write_private_json(root / "assembled" / "sealed-labels.json", sealed_rows)
    public = {
        "schema_version": "phase3_heldout_label_public_receipt_v1",
        "text_free": True,
        "bindings": manifest["bindings"],
        "manifest_sha256": sha256_file(manifest_path),
        "sealed_labels_sha256": sealed_hash,
        "row_count": ROW_COUNT,
        "packet_count": manifest["packet_count"],
        "actor": dict(ACTOR),
        "complete": True,
    }
    public["receipt_sha256"] = sha256_value(public)
    _validate_schema(public, schema_path, "publicReceipt")
    _public_safe(public)
    _write_private_json(public_receipt_path, public)
    return public


# Cycle002 transport -------------------------------------------------------
#
# Keep this separate from the historical 2,000-row clean-modern lane above.
# That lane is evidence for cycle001 only and must never become an implicit
# fallback for the complete cycle002 population.


def _write_public_json(path: Path, value: Mapping[str, Any]) -> str:
    """Atomically write a text-free public receipt without relaxing private ACLs."""
    _reject_symlink_components(path.parent, "public output parent")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (canonical_json(value) + "\n").encode("utf-8")
    if path.exists() or path.is_symlink():
        _regular(path, "public output")
        require(path.read_bytes() == payload, "immutable public output drift")
        return sha256_bytes(payload)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_FILE_MODE)
    except BaseException:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise
    return sha256_bytes(payload)


def _jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    _regular(path, label)
    rows: list[dict[str, Any]] = []
    for number, raw in enumerate(path.read_bytes().splitlines(), start=1):
        value = _strict_json_bytes(raw, f"{label} row {number}")
        rows.append(dict(value))
    return rows


def _cycle002_partition(path: Path) -> list[dict[str, Any]]:
    require(sha256_file(path) == CYCLE002_PARTITION_SHA256, "cycle002 partition hash drift")
    rows = _jsonl(path, "cycle002 canonical partition")
    required = {
        "family_id", "unit_id", "unit_sha256", "reason", "candidate_lane",
        "source_text_sha256", "frozen_locator_sha256",
    }
    require(
        len(rows) == CYCLE002_ROW_COUNT and len({row.get("unit_id") for row in rows}) == CYCLE002_ROW_COUNT,
        "cycle002 partition denominator drift",
    )
    require(all(set(row) == required and row["reason"] == "evaluation_only" for row in rows), "cycle002 partition row drift")
    lanes = {lane: sum(row["candidate_lane"] == lane for row in rows) for lane in ("clean_modern", "phenomenon_strata")}
    require(lanes == {"clean_modern": 2000, "phenomenon_strata": 7392}, "cycle002 partition lane drift")
    return rows


def _cycle002_materialization(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    require(sha256_file(path) == CYCLE002_MATERIALIZATION_SHA256, "cycle002 materialization hash drift")
    rows = _jsonl(path, "cycle002 canonical materialization")
    required = {
        "family_id", "unit_id", "unit_sha256", "frozen_locator", "frozen_locator_sha256",
        "document_or_edition_identity", "source_text", "source_record", "source_text_sha256",
    }
    require(len(rows) == MATERIALIZATION_COUNT, "cycle002 materialization denominator drift")
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        require(set(row) == required, "cycle002 materialization row drift")
        key = tuple(_identity(row))
        require(key not in result, "cycle002 materialization identity duplicate")
        require(
            sha256_bytes(str(row["source_text"]).encode("utf-8")) == row["source_text_sha256"],
            "cycle002 materialization text hash drift",
        )
        result[key] = row
    return result


def _cycle002_freeze_manifest(path: Path, schema_path: Path) -> dict[str, Any]:
    value = _read_json(path, "cycle002 freeze manifest")
    _validate_schema(value, schema_path, "cycle002FreezeManifest")
    body = dict(value)
    claimed = body.pop("manifest_sha256")
    require(claimed == sha256_value(body), "cycle002 freeze manifest hash drift")
    return value


def freeze_cycle002(
    *,
    partition_path: Path,
    materialization_jsonl: Path,
    private_dir: Path,
    public_receipt_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    """Freshen cycle002 custody while preserving the canonical 9,392 identities.

    The private index intentionally contains only identity/document/hash fields.
    It never copies corpus bodies; packet preparation reads bodies only from the
    already-private canonical materialization after rechecking its hash.
    """
    _assert_output_not_in_inputs((private_dir, public_receipt_path), (partition_path, materialization_jsonl, schema_path))
    partition = _cycle002_partition(partition_path)
    materialized = _cycle002_materialization(materialization_jsonl)
    index: list[dict[str, Any]] = []
    for row in partition:
        source = materialized.get(tuple(_identity(row)))
        require(source is not None, "cycle002 partition identity absent from materialization")
        require(
            source["family_id"] == row["family_id"]
            and source["source_text_sha256"] == row["source_text_sha256"]
            and source["frozen_locator_sha256"] == row["frozen_locator_sha256"],
            "cycle002 partition/materialization join drift",
        )
        index.append(
            {
                "family_id": source["family_id"],
                "unit_id": source["unit_id"],
                "unit_sha256": source["unit_sha256"],
                "document_or_edition_identity": source["document_or_edition_identity"],
                "candidate_lane": row["candidate_lane"],
                "source_text_sha256": source["source_text_sha256"],
                "frozen_locator_sha256": source["frozen_locator_sha256"],
            }
        )
    identities = [_identity(row) for row in partition]
    root = _private_root(private_dir, create=True)
    _assert_private_tree(root)
    index_hash = _write_private(root / "cycle002-freeze-index.jsonl", b"".join(canonical_json(row).encode("utf-8") + b"\n" for row in index))
    manifest = {
        "schema_version": "phase3_cycle002_heldout_freeze_manifest_v1",
        "text_free": True,
        "evaluation_cycle_id": CYCLE002_ID,
        "partition_manifest_sha256": sha256_file(partition_path),
        "materialization_jsonl_sha256": sha256_file(materialization_jsonl),
        "selection_set_sha256": sha256_value(identities),
        "selection_order_sha256": sha256_value(identities),
        "row_count": CYCLE002_ROW_COUNT,
        "lane_counts": {"clean_modern": 2000, "phenomenon_strata": 7392},
        "private_index_sha256": index_hash,
    }
    manifest["manifest_sha256"] = sha256_value(manifest)
    _validate_schema(manifest, schema_path, "cycle002FreezeManifest")
    manifest_hash = _write_private_json(root / "cycle002-freeze-manifest.json", manifest)
    public = {
        "schema_version": "phase3_cycle002_heldout_freeze_receipt_v1",
        "text_free": True,
        "evaluation_cycle_id": CYCLE002_ID,
        "freeze_manifest_sha256": manifest_hash,
        "partition_manifest_sha256": manifest["partition_manifest_sha256"],
        "materialization_jsonl_sha256": manifest["materialization_jsonl_sha256"],
        "selection_set_sha256": manifest["selection_set_sha256"],
        "row_count": CYCLE002_ROW_COUNT,
        "lane_counts": manifest["lane_counts"],
        "fresh_freeze": True,
    }
    public["receipt_sha256"] = sha256_value(public)
    _validate_schema(public, schema_path, "cycle002FreezeReceipt")
    _write_public_json(public_receipt_path, public)
    return public


def _cycle002_execution(role_contract_path: Path, evaluation_contract_path: Path) -> tuple[dict[str, Any], str, str]:
    """Require future role-contract task bindings before any source body is packed."""
    role_contract = _read_json(role_contract_path, "cycle002 role contract")
    evaluation_contract = _read_json(evaluation_contract_path, "cycle002 evaluation contract")
    require(role_contract.get("cycle002", {}).get("evaluation_cycle_id") == CYCLE002_ID, "cycle002 role cycle drift")
    require(evaluation_contract.get("cycle002", {}).get("evaluation_cycle_id") == CYCLE002_ID, "cycle002 evaluation cycle drift")
    execution = role_contract.get("cycle002_labeling_protocol")
    require(isinstance(execution, Mapping), "cycle002 role contract lacks two-pass heldout execution binding")
    expected_passes = [
        {
            "pass_id": pass_id,
            **{key: value for key, value in CYCLE002_ACTORS[pass_id].items() if key != "role_id"},
        }
        for pass_id in ("a", "b")
    ]
    require(
        execution.get("reviewer_role_id") == "heldout_label_reviewer"
        and execution.get("passes") == expected_passes,
        "cycle002 role contract heldout pass binding drift",
    )
    require(
        execution.get("independence_unit") == "task_id"
        and execution.get("provider_independent") is False
        and execution.get("provider_reuse_disclosed") is True
        and execution.get("deterministic_assembly_may_adjudicate") is False
        and execution.get("disagreement_disposition") == "unresolved_abstention",
        "cycle002 role contract disagreement protocol drift",
    )
    require(
        evaluation_contract.get("cycle002_labeling_protocol") == execution,
        "cycle002 role/evaluation labeling protocol disagreement",
    )
    return dict(execution), sha256_file(role_contract_path), sha256_file(evaluation_contract_path)


def _cycle002_prompt(path: Path) -> str:
    _regular(path, "cycle002 heldout label prompt")
    digest = sha256_file(path)
    require(digest == CYCLE002_LABEL_PROMPT_SHA256, "cycle002 heldout label prompt hash drift")
    return digest


def _cycle002_packet(
    *,
    pass_id: str,
    index: int,
    count: int,
    rows: Sequence[Mapping[str, Any]],
    bindings: Mapping[str, Any],
    oversize_singleton: bool,
) -> dict[str, Any]:
    value = {
        "schema_version": "phase3_cycle002_heldout_label_packet_v1",
        "pass_id": pass_id,
        "packet_index": index,
        "packet_count": count,
        "oversize_singleton": oversize_singleton,
        "actor": CYCLE002_ACTORS[pass_id],
        "bindings": dict(bindings),
        "rows": list(rows),
    }
    value["packet_id"] = "phase3_cycle002_heldout_label_packet:" + sha256_value(value)
    return value


def _cycle002_reference_evidence(source: Mapping[str, Any]) -> dict[str, str] | None:
    """Expose only frozen human UA-GEC evidence needed to derive exact gold."""
    if source["family_id"] != "ua_gec":
        return None
    record = source["source_record"]
    require(
        isinstance(record, Mapping)
        and set(record)
        == {"id", "error", "correct", "error_type", "doc_id", "annotator_id", "partition", "is_native", "source_lang"},
        "cycle002 UA-GEC source record shape drift",
    )
    require(
        all(isinstance(record[key], str) for key in ("error", "correct", "error_type")),
        "cycle002 UA-GEC reference evidence type drift",
    )
    if not all(record[key].strip() for key in ("error", "correct", "error_type")):
        return None
    require(record["error"] == source["source_text"], "cycle002 UA-GEC error text drift")
    return {
        "kind": "ua_gec_human_annotation",
        "corrected_text": record["correct"],
        "error_type": record["error_type"],
    }


def prepare_cycle002(
    *,
    freeze_manifest_path: Path,
    partition_path: Path,
    materialization_jsonl: Path,
    private_dir: Path,
    role_contract_path: Path = DEFAULT_CYCLE002_ROLE_CONTRACT,
    evaluation_contract_path: Path = DEFAULT_CYCLE002_EVALUATION_CONTRACT,
    label_prompt_path: Path = DEFAULT_CYCLE002_LABEL_PROMPT,
    schema_path: Path = DEFAULT_SCHEMA,
    packet_limit: int = CYCLE002_PACKET_LIMIT,
    byte_limit: int = CYCLE002_PACKET_BYTE_LIMIT,
) -> dict[str, Any]:
    """Create immutable 40-row-or-smaller packets for both independent Sol passes."""
    require(isinstance(packet_limit, int) and 0 < packet_limit <= CYCLE002_PACKET_LIMIT, "cycle002 packet limit drift")
    require(isinstance(byte_limit, int) and byte_limit > 0, "cycle002 byte limit drift")
    _assert_output_not_in_inputs(
        (private_dir,),
        (partition_path, materialization_jsonl, role_contract_path, evaluation_contract_path, label_prompt_path, schema_path),
    )
    require(
        _absolute(freeze_manifest_path) == _absolute(private_dir) / "cycle002-freeze-manifest.json",
        "cycle002 freeze manifest must be the immutable private-root freeze output",
    )
    freeze = _cycle002_freeze_manifest(freeze_manifest_path, schema_path)
    require(freeze["partition_manifest_sha256"] == sha256_file(partition_path), "cycle002 packet partition binding drift")
    require(freeze["materialization_jsonl_sha256"] == sha256_file(materialization_jsonl), "cycle002 packet materialization binding drift")
    _execution, role_hash, evaluation_hash = _cycle002_execution(role_contract_path, evaluation_contract_path)
    prompt_hash = _cycle002_prompt(label_prompt_path)
    partition = _cycle002_partition(partition_path)
    source_by_id = _cycle002_materialization(materialization_jsonl)
    rows: list[dict[str, Any]] = []
    for partition_row in partition:
        source = source_by_id[tuple(_identity(partition_row))]
        rows.append(
            {
                "family_id": source["family_id"],
                "unit_id": source["unit_id"],
                "unit_sha256": source["unit_sha256"],
                "document_or_edition_identity": source["document_or_edition_identity"],
                "candidate_lane": partition_row["candidate_lane"],
                "source_text": source["source_text"],
                "source_text_sha256": source["source_text_sha256"],
                "frozen_locator_sha256": source["frozen_locator_sha256"],
                "reference_evidence": _cycle002_reference_evidence(source),
            }
        )
    require(sha256_value([_identity(row) for row in rows]) == freeze["selection_set_sha256"], "cycle002 packet identity drift")
    root = _private_root(private_dir, create=True)
    _assert_private_tree(root)
    chunks: list[tuple[list[dict[str, Any]], bool]] = []
    current: list[dict[str, Any]] = []
    for row in rows:
        candidate = [*current, row]
        if current and (len(candidate) > packet_limit or len(canonical_json(candidate).encode("utf-8")) > byte_limit):
            chunks.append((current, False))
            current = [row]
        else:
            current = candidate
        if len(current) == 1 and len(canonical_json(current).encode("utf-8")) > byte_limit:
            chunks.append((current, True))
            current = []
    if current:
        chunks.append((current, False))
    require(
        all(len(chunk) <= packet_limit and (oversize or len(canonical_json(chunk).encode("utf-8")) <= byte_limit) for chunk, oversize in chunks),
        "cycle002 packet bounds drift",
    )
    require(sum(len(chunk) for chunk, _oversize in chunks) == CYCLE002_ROW_COUNT, "cycle002 packet denominator drift")
    bindings = {
        "evaluation_cycle_id": CYCLE002_ID,
        "freeze_manifest_sha256": sha256_file(freeze_manifest_path),
        "selection_set_sha256": freeze["selection_set_sha256"],
        "partition_manifest_sha256": sha256_file(partition_path),
        "materialization_jsonl_sha256": sha256_file(materialization_jsonl),
        "functional_role_contract_sha256": role_hash,
        "evaluation_contract_sha256": evaluation_hash,
        "label_prompt_logical_path": str(label_prompt_path.relative_to(ROOT)),
        "label_prompt_sha256": prompt_hash,
        "packet_limit": packet_limit,
        "byte_limit": byte_limit,
    }
    packets: dict[str, list[dict[str, Any]]] = {}
    for pass_id in sorted(CYCLE002_ACTORS):
        entries: list[dict[str, Any]] = []
        for index, (chunk, oversize) in enumerate(chunks, start=1):
            packet = _cycle002_packet(
                pass_id=pass_id,
                index=index,
                count=len(chunks),
                rows=chunk,
                bindings=bindings,
                oversize_singleton=oversize,
            )
            packet_hash = _write_private_json(root / "cycle002" / "packets" / pass_id / f"{index:04d}.json", packet)
            entries.append(
                {
                    "packet_index": index,
                    "packet_id": packet["packet_id"],
                    "packet_sha256": packet_hash,
                    "row_count": len(chunk),
                    "identity_set_sha256": sha256_value([_identity(row) for row in chunk]),
                    "oversize_singleton": oversize,
                }
            )
        packets[pass_id] = entries
    manifest = {
        "schema_version": "phase3_cycle002_heldout_label_manifest_v1",
        "text_free": True,
        "bindings": bindings,
        "row_count": CYCLE002_ROW_COUNT,
        "packet_count": len(chunks),
        "passes": packets,
    }
    manifest["manifest_sha256"] = sha256_value(manifest)
    _validate_schema(manifest, schema_path, "cycle002Manifest")
    _write_private_json(root / "cycle002" / "manifest.json", manifest)
    return manifest


def _cycle002_manifest(path: Path, schema_path: Path) -> tuple[dict[str, Any], Path]:
    value = _read_json(path, "cycle002 heldout manifest")
    _validate_schema(value, schema_path, "cycle002Manifest")
    body = dict(value)
    claimed = body.pop("manifest_sha256")
    require(claimed == sha256_value(body), "cycle002 heldout manifest hash drift")
    root = _private_root(path.parents[1], create=False)
    require(path.parent == root / "cycle002", "cycle002 manifest must be inside cycle002 private root")
    return value, root


def _cycle002_packet_load(
    manifest: Mapping[str, Any], root: Path, pass_id: str, packet_index: int
) -> dict[str, Any]:
    require(pass_id in CYCLE002_ACTORS, "cycle002 pass id drift")
    require(1 <= packet_index <= manifest["packet_count"], "cycle002 packet index out of range")
    binding = manifest["passes"][pass_id][packet_index - 1]
    path = root / "cycle002" / "packets" / pass_id / f"{packet_index:04d}.json"
    _regular(path, "cycle002 private packet")
    require(sha256_file(path) == binding["packet_sha256"], "cycle002 private packet hash drift")
    packet = _read_json(path, "cycle002 private packet")
    body = dict(packet)
    packet_id = body.pop("packet_id", None)
    require(packet_id == "phase3_cycle002_heldout_label_packet:" + sha256_value(body), "cycle002 packet identity drift")
    require(
        packet.get("schema_version") == "phase3_cycle002_heldout_label_packet_v1"
        and packet.get("pass_id") == pass_id
        and packet.get("packet_index") == packet_index
        and packet.get("packet_count") == manifest["packet_count"]
        and type(packet.get("oversize_singleton")) is bool
        and packet.get("oversize_singleton") == binding["oversize_singleton"]
        and packet.get("actor") == CYCLE002_ACTORS[pass_id]
        and packet.get("bindings") == manifest["bindings"]
        and packet.get("packet_id") == binding["packet_id"],
        "cycle002 packet binding drift",
    )
    require(
        len(packet.get("rows", [])) == binding["row_count"]
        and sha256_value([_identity(row) for row in packet["rows"]]) == binding["identity_set_sha256"],
        "cycle002 packet row bijection drift",
    )
    return packet


def _cycle002_label(label: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "unit_id", "unit_sha256", "label_state", "phenomenon", "benchmark_role", "document_or_edition_identity",
        "clean_modern_eligible", "modern_genre_id", "gold",
    }
    require(set(label) == required, "cycle002 reviewer label shape drift")
    require(_identity(label) == _identity(source), "cycle002 reviewer identity drift")
    require(
        label["document_or_edition_identity"] == source["document_or_edition_identity"],
        "cycle002 reviewer document identity drift",
    )
    require(label["label_state"] in {"supported", "abstain"}, "cycle002 label state drift")
    require(type(label["clean_modern_eligible"]) is bool, "cycle002 clean eligibility type drift")
    if label["label_state"] == "abstain":
        require(
            label["phenomenon"] is None
            and label["benchmark_role"] is None
            and label["clean_modern_eligible"] is False
            and label["modern_genre_id"] is None
            and label["gold"] == {"kind": "abstain", "reason": "uncertain_or_unsupported"},
            "cycle002 unsupported label must remain explicit abstention",
        )
        return dict(label)
    require(label["phenomenon"] in CYCLE002_PHENOMENA, "cycle002 phenomenon drift")
    require(label["benchmark_role"] in CYCLE002_ROLES, "cycle002 benchmark role drift")
    if label["clean_modern_eligible"]:
        require(label["modern_genre_id"] in CYCLE002_GENRES, "cycle002 clean genre drift")
    else:
        require(label["modern_genre_id"] is None, "cycle002 ineligible clean genre drift")
    gold = label["gold"]
    require(isinstance(gold, Mapping), "cycle002 gold shape drift")
    if label["benchmark_role"] == "positive":
        require(
            set(gold) == {"kind", "start", "end", "expected_correction"}
            and gold.get("kind") == "correction"
            and isinstance(gold.get("start"), int)
            and isinstance(gold.get("end"), int)
            and 0 <= gold["start"] < gold["end"] <= len(source["source_text"])
            and isinstance(gold.get("expected_correction"), str)
            and gold["expected_correction"].strip(),
            "cycle002 positive gold drift",
        )
        sealed = dict(label)
        sealed["gold"] = {
            **gold,
            "surface_sha256": sha256_bytes(source["source_text"][gold["start"] : gold["end"]].encode("utf-8")),
            "expected_correction_sha256": sha256_bytes(gold["expected_correction"].encode("utf-8")),
        }
        return sealed
    else:
        require(
            gold == {"kind": "abstain", "reason": "acceptable_control" if label["benchmark_role"] == "acceptable_control" else "protected"},
            "cycle002 nonpositive gold must be explicit abstention",
        )
    return dict(label)


def _cycle002_parse(raw: bytes, packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    response = _strict_json_bytes(raw, "cycle002 reviewer response")
    require(set(response) == {"labels"} and isinstance(response["labels"], list), "cycle002 reviewer response shape drift")
    labels = response["labels"]
    require(len(labels) == len(packet["rows"]), "cycle002 reviewer response denominator drift")
    parsed = [_cycle002_label(label, source) for label, source in zip(labels, packet["rows"], strict=True)]
    require(
        [_identity(label) for label in parsed] == [_identity(row) for row in packet["rows"]]
        and len({tuple(_identity(label)) for label in parsed}) == len(parsed),
        "cycle002 reviewer response identity/order bijection drift",
    )
    return parsed


def _cycle002_ingest_bytes(
    *, manifest_path: Path, packet_index: int, pass_id: str, raw: bytes, private_dir: Path, schema_path: Path
) -> dict[str, Any]:
    manifest, root = _cycle002_manifest(manifest_path, schema_path)
    require(root == _private_root(private_dir, create=False), "cycle002 private root drift")
    packet = _cycle002_packet_load(manifest, root, pass_id, packet_index)
    receipt_path = root / "cycle002" / "transports" / pass_id / f"{packet_index:04d}.json"
    require(not receipt_path.exists(), "cycle002 packet already has a completed transport receipt")
    attempt_dir = root / "cycle002" / "raw-attempts" / pass_id / f"{packet_index:04d}"
    attempt_index = 1
    while (attempt_dir / f"{attempt_index:03d}.raw").exists():
        attempt_index += 1
    # Every provider/external capture is retained before parsing. Invalid attempts
    # remain immutable and a later call may retry without overwriting evidence.
    attempt_path = attempt_dir / f"{attempt_index:03d}.raw"
    attempt_hash = _write_private(attempt_path, raw)
    labels = _cycle002_parse(raw, packet)
    raw_hash = _write_private(root / "cycle002" / "raw" / pass_id / f"{packet_index:04d}.raw", raw)
    response_hash = _write_private_json(root / "cycle002" / "responses" / pass_id / f"{packet_index:04d}.json", {"labels": labels})
    sealed = [
        {**label, "reviewer": dict(CYCLE002_ACTORS[pass_id]), "bindings_sha256": sha256_value(manifest["bindings"])}
        for label in labels
    ]
    sealed_hash = _write_private_json(root / "cycle002" / "sealed" / pass_id / f"{packet_index:04d}.json", sealed)
    receipt = {
        "schema_version": "phase3_cycle002_heldout_label_transport_receipt_v1",
        "pass_id": pass_id,
        "packet_index": packet_index,
        "packet_id": packet["packet_id"],
        "packet_sha256": sha256_file(root / "cycle002" / "packets" / pass_id / f"{packet_index:04d}.json"),
        "bindings": manifest["bindings"],
        "actor": dict(CYCLE002_ACTORS[pass_id]),
        "raw_attempt_index": attempt_index,
        "raw_attempt_sha256": attempt_hash,
        "raw_sha256": raw_hash,
        "raw_byte_count": len(raw),
        "response_sha256": response_hash,
        "sealed_rows_sha256": sealed_hash,
        "identity_order_bijection": True,
        "text_free": True,
    }
    receipt["receipt_sha256"] = sha256_value(receipt)
    _validate_schema(receipt, schema_path, "cycle002TransportReceipt")
    _write_private_json(receipt_path, receipt)
    return {
        "packet_index": packet_index,
        "pass_id": pass_id,
        "raw_attempt_index": attempt_index,
        "raw_sha256": raw_hash,
        "sealed_rows_sha256": sealed_hash,
    }


def ingest_cycle002(
    *,
    manifest_path: Path,
    packet_index: int,
    pass_id: str,
    raw_response_path: Path,
    private_dir: Path,
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict[str, Any]:
    """Ingest an externally captured response; no provider is contacted."""
    _regular(raw_response_path, "cycle002 raw reviewer response")
    return _cycle002_ingest_bytes(
        manifest_path=manifest_path,
        packet_index=packet_index,
        pass_id=pass_id,
        raw=raw_response_path.read_bytes(),
        private_dir=private_dir,
        schema_path=schema_path,
    )


def run_cycle002(
    *, manifest_path: Path, packet_index: int, pass_id: str, private_dir: Path, schema_path: Path = DEFAULT_SCHEMA
) -> dict[str, Any]:
    """Run one heldout packet only through the explicit Codex project bridge."""
    manifest, root = _cycle002_manifest(manifest_path, schema_path)
    require(root == _private_root(private_dir, create=False), "cycle002 private root drift")
    packet = _cycle002_packet_load(manifest, root, pass_id, packet_index)
    receipt_path = root / "cycle002" / "transports" / pass_id / f"{packet_index:04d}.json"
    require(not receipt_path.exists(), "cycle002 packet already has a completed transport receipt")
    prompt_path = ROOT / manifest["bindings"]["label_prompt_logical_path"]
    require(sha256_file(prompt_path) == manifest["bindings"]["label_prompt_sha256"], "cycle002 manifest prompt binding drift")
    prompt = prompt_path.read_bytes()
    command = [
        str(ROOT / ".venv/bin/python"),
        str(ROOT / "scripts/ai_agent_bridge/__main__.py"),
        "ask-codex",
        "-",
        "--from",
        "operator",
        "--task-id",
        CYCLE002_ACTORS[pass_id]["task_id"],
        "--to-model",
        "gpt-5.6-sol",
        "--new-session",
        "--no-timeout",
    ]
    payload = prompt + b"\n\n" + canonical_json(packet).encode("utf-8")
    completed = subprocess.run(command, input=payload, capture_output=True, check=False)
    require(completed.returncode == 0, "cycle002 Codex bridge invocation failed")
    return _cycle002_ingest_bytes(
        manifest_path=manifest_path,
        packet_index=packet_index,
        pass_id=pass_id,
        raw=completed.stdout,
        private_dir=private_dir,
        schema_path=schema_path,
    )


def _cycle002_sealed_packet(
    manifest: Mapping[str, Any], root: Path, pass_id: str, packet_index: int, schema_path: Path
) -> list[dict[str, Any]]:
    packet = _cycle002_packet_load(manifest, root, pass_id, packet_index)
    receipt_path = root / "cycle002" / "transports" / pass_id / f"{packet_index:04d}.json"
    sealed_path = root / "cycle002" / "sealed" / pass_id / f"{packet_index:04d}.json"
    raw_path = root / "cycle002" / "raw" / pass_id / f"{packet_index:04d}.raw"
    response_path = root / "cycle002" / "responses" / pass_id / f"{packet_index:04d}.json"
    for path in (receipt_path, sealed_path, raw_path, response_path):
        _regular(path, "cycle002 transport private artifact")
    receipt = _read_json(receipt_path, "cycle002 transport receipt")
    _validate_schema(receipt, schema_path, "cycle002TransportReceipt")
    body = dict(receipt)
    claimed = body.pop("receipt_sha256")
    require(claimed == sha256_value(body), "cycle002 transport receipt hash drift")
    require(
        receipt["pass_id"] == pass_id
        and receipt["packet_id"] == packet["packet_id"]
        and receipt["packet_sha256"] == sha256_file(root / "cycle002" / "packets" / pass_id / f"{packet_index:04d}.json")
        and receipt["bindings"] == manifest["bindings"]
        and receipt["actor"] == CYCLE002_ACTORS[pass_id]
        and receipt["raw_attempt_index"] >= 1
        and receipt["raw_sha256"] == sha256_file(raw_path)
        and receipt["raw_byte_count"] == raw_path.stat().st_size,
        "cycle002 transport receipt custody drift",
    )
    attempt_path = (
        root
        / "cycle002"
        / "raw-attempts"
        / pass_id
        / f"{packet_index:04d}"
        / f"{receipt['raw_attempt_index']:03d}.raw"
    )
    _regular(attempt_path, "cycle002 raw attempt")
    require(
        receipt["raw_attempt_sha256"] == sha256_file(attempt_path)
        and attempt_path.read_bytes() == raw_path.read_bytes(),
        "cycle002 selected raw-attempt custody drift",
    )
    labels = _cycle002_parse(raw_path.read_bytes(), packet)
    require(
        _read_json(response_path, "cycle002 parsed response") == {"labels": labels}
        and receipt["response_sha256"] == sha256_file(response_path),
        "cycle002 parsed response custody drift",
    )
    sealed = _read_json(sealed_path, "cycle002 sealed labels", list)
    expected = [
        {**label, "reviewer": dict(CYCLE002_ACTORS[pass_id]), "bindings_sha256": sha256_value(manifest["bindings"])}
        for label in labels
    ]
    require(sealed == expected and receipt["sealed_rows_sha256"] == sha256_file(sealed_path), "cycle002 sealed custody drift")
    return sealed


def run_pending_cycle002(
    *,
    manifest_path: Path,
    private_dir: Path,
    pass_ids: Sequence[str] = ("a", "b"),
    max_packets: int | None = None,
    schema_path: Path = DEFAULT_SCHEMA,
    progress: bool = False,
) -> dict[str, Any]:
    """Run a bounded, resumable slice of incomplete cycle002 packets."""
    requested = list(pass_ids)
    require(
        requested and len(requested) == len(set(requested)) and all(item in CYCLE002_ACTORS for item in requested),
        "cycle002 pending-run pass selection drift",
    )
    require(
        max_packets is None or (isinstance(max_packets, int) and max_packets > 0),
        "cycle002 max-packets drift",
    )
    manifest, root = _cycle002_manifest(manifest_path, schema_path)
    require(root == _private_root(private_dir, create=False), "cycle002 private root drift")
    pending: list[tuple[str, int]] = []
    skipped = 0
    for pass_id in requested:
        for packet_index in range(1, manifest["packet_count"] + 1):
            receipt_path = root / "cycle002" / "transports" / pass_id / f"{packet_index:04d}.json"
            if receipt_path.exists():
                _cycle002_sealed_packet(manifest, root, pass_id, packet_index, schema_path)
                skipped += 1
            else:
                pending.append((pass_id, packet_index))
    selected = pending if max_packets is None else pending[:max_packets]
    for ordinal, (pass_id, packet_index) in enumerate(selected, start=1):
        run_cycle002(
            manifest_path=manifest_path,
            packet_index=packet_index,
            pass_id=pass_id,
            private_dir=private_dir,
            schema_path=schema_path,
        )
        if progress:
            print(
                canonical_json(
                    {
                        "cycle002_progress": True,
                        "completed_in_batch": ordinal,
                        "batch_size": len(selected),
                        "pass_id": pass_id,
                        "packet_index": packet_index,
                    }
                ),
                flush=True,
            )
    return {
        "requested_pass_ids": requested,
        "completed_in_batch": len(selected),
        "verified_existing": skipped,
        "remaining": len(pending) - len(selected),
        "all_requested_complete": len(pending) == len(selected),
    }


def _cycle002_floor_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    accepted = [
        row
        for row in rows
        if row["disagreement_carrier"]["status"] == "agreement" and row["gold"]["label_state"] == "supported"
    ]
    strata: dict[str, dict[str, dict[str, Any]]] = {}
    passed = True
    for phenomenon in CYCLE002_PHENOMENA:
        strata[phenomenon] = {}
        for benchmark_role in sorted(CYCLE002_ROLES):
            current = [
                row for row in accepted
                if row["gold"]["phenomenon"] == phenomenon and row["gold"]["benchmark_role"] == benchmark_role
            ]
            documents = {row["document_or_edition_identity"] for row in current}
            item = {"count": len(current), "document_count": len(documents), "passed": len(current) >= 30 and len(documents) >= 3}
            strata[phenomenon][benchmark_role] = item
            passed = passed and item["passed"]
    clean = [
        row for row in accepted
        if row["gold"]["benchmark_role"] == "acceptable_control" and row["gold"]["clean_modern_eligible"] is True
    ]
    clean_documents = {row["document_or_edition_identity"] for row in clean}
    clean_genres = {row["gold"]["modern_genre_id"] for row in clean}
    clean_report = {
        "count": len(clean),
        "document_count": len(clean_documents),
        "genre_count": len(clean_genres),
        "passed": len(clean) >= 30 and len(clean_documents) >= 3 and len(clean_genres) >= 2,
    }
    return {"strata": strata, "clean_controls": clean_report, "passed": passed and clean_report["passed"]}


def assemble_cycle002(
    *, manifest_path: Path, private_dir: Path, public_receipt_path: Path, schema_path: Path = DEFAULT_SCHEMA
) -> dict[str, Any]:
    """Seal only two-pass agreements; disagreements remain unresolved abstentions."""
    _assert_output_not_in_inputs((public_receipt_path,), (manifest_path, schema_path))
    manifest, root = _cycle002_manifest(manifest_path, schema_path)
    require(root == _private_root(private_dir, create=False), "cycle002 private root drift")
    sealed_by_pass: dict[str, list[dict[str, Any]]] = {}
    for pass_id in sorted(CYCLE002_ACTORS):
        rows: list[dict[str, Any]] = []
        for index in range(1, manifest["packet_count"] + 1):
            rows.extend(_cycle002_sealed_packet(manifest, root, pass_id, index, schema_path))
        require(
            len(rows) == CYCLE002_ROW_COUNT
            and sha256_value([_identity(row) for row in rows]) == manifest["bindings"]["selection_set_sha256"],
            "cycle002 pass is incomplete or not the frozen identity bijection",
        )
        sealed_by_pass[pass_id] = rows
    comprehensive: list[dict[str, Any]] = []
    disagreements = 0
    for left, right in zip(sealed_by_pass["a"], sealed_by_pass["b"], strict=True):
        require(_identity(left) == _identity(right), "cycle002 cross-pass identity order drift")
        left_gold = {key: value for key, value in left.items() if key not in {"reviewer", "bindings_sha256"}}
        right_gold = {key: value for key, value in right.items() if key not in {"reviewer", "bindings_sha256"}}
        agreement = left_gold == right_gold
        disagreements += int(not agreement)
        comprehensive.append(
            {
                "unit_id": left["unit_id"],
                "unit_sha256": left["unit_sha256"],
                "document_or_edition_identity": left["document_or_edition_identity"],
                "pass_a": left_gold,
                "pass_b": right_gold,
                "gold": left_gold if agreement else {"kind": "abstain", "reason": "pass_disagreement"},
                "disagreement_carrier": {
                    "status": "agreement" if agreement else "unresolved_abstention",
                    "deterministic_assembly_adjudicated": False,
                    "pass_a_sha256": sha256_value(left_gold),
                    "pass_b_sha256": sha256_value(right_gold),
                },
            }
        )
    floors = _cycle002_floor_report(comprehensive)
    complete = floors["passed"]
    sealed_hash = _write_private_json(root / "cycle002" / "assembled" / "comprehensive-sealed-labels.json", comprehensive)
    bundle = {
        "schema_version": "phase3_cycle002_comprehensive_sealed_label_bundle_v1",
        "text_free": True,
        "evaluation_cycle_id": CYCLE002_ID,
        "freeze_manifest_sha256": sha256_file(root / "cycle002-freeze-manifest.json"),
        "packet_manifest_sha256": sha256_file(manifest_path),
        "sealed_labels_sha256": sealed_hash,
        "row_count": CYCLE002_ROW_COUNT,
        "packet_count": manifest["packet_count"],
        "pass_count": 2,
        "disagreement_count": disagreements,
        "floor_report": floors,
        "complete": complete,
        "author_restart_allowed": complete,
        "frozen_before_rule_extraction": True,
    }
    bundle["receipt_sha256"] = sha256_value(bundle)
    _validate_schema(bundle, schema_path, "cycle002PublicReceipt")
    _write_private_json(root / "cycle002" / "assembled" / "comprehensive-label-bundle.json", bundle)
    _write_public_json(public_receipt_path, bundle)
    return bundle


def _config(path: Path) -> dict[str, Any]:
    return _read_json(path, "CLI configuration")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "freeze-cycle002",
            "prepare-cycle002",
            "run-cycle002",
            "run-pending-cycle002",
            "ingest-cycle002",
            "assemble-cycle002",
            "prepare",
            "ingest",
            "assemble",
        ),
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Strict JSON command configuration; only cycle002 run commands invoke the pinned Codex bridge.",
    )
    args = parser.parse_args(argv)
    try:
        config = _config(args.input)
        if args.command == "freeze-cycle002":
            result = freeze_cycle002(
                partition_path=Path(config["partition_path"]),
                materialization_jsonl=Path(config["materialization_jsonl"]),
                private_dir=Path(config["private_dir"]),
                public_receipt_path=Path(config["public_receipt_path"]),
                schema_path=Path(config.get("schema_path", DEFAULT_SCHEMA)),
            )
        elif args.command == "prepare-cycle002":
            result = prepare_cycle002(
                freeze_manifest_path=Path(config["freeze_manifest_path"]),
                partition_path=Path(config["partition_path"]),
                materialization_jsonl=Path(config["materialization_jsonl"]),
                private_dir=Path(config["private_dir"]),
                role_contract_path=Path(config.get("role_contract_path", DEFAULT_CYCLE002_ROLE_CONTRACT)),
                evaluation_contract_path=Path(config.get("evaluation_contract_path", DEFAULT_CYCLE002_EVALUATION_CONTRACT)),
                label_prompt_path=Path(config.get("label_prompt_path", DEFAULT_CYCLE002_LABEL_PROMPT)),
                schema_path=Path(config.get("schema_path", DEFAULT_SCHEMA)),
                packet_limit=config.get("packet_limit", CYCLE002_PACKET_LIMIT),
                byte_limit=config.get("byte_limit", CYCLE002_PACKET_BYTE_LIMIT),
            )
        elif args.command == "run-cycle002":
            result = run_cycle002(
                manifest_path=Path(config["manifest_path"]),
                packet_index=config["packet_index"],
                pass_id=config["pass_id"],
                private_dir=Path(config["private_dir"]),
                schema_path=Path(config.get("schema_path", DEFAULT_SCHEMA)),
            )
        elif args.command == "run-pending-cycle002":
            result = run_pending_cycle002(
                manifest_path=Path(config["manifest_path"]),
                private_dir=Path(config["private_dir"]),
                pass_ids=config.get("pass_ids", ["a", "b"]),
                max_packets=config.get("max_packets"),
                schema_path=Path(config.get("schema_path", DEFAULT_SCHEMA)),
                progress=True,
            )
        elif args.command == "ingest-cycle002":
            result = ingest_cycle002(
                manifest_path=Path(config["manifest_path"]),
                packet_index=config["packet_index"],
                pass_id=config["pass_id"],
                raw_response_path=Path(config["raw_response_path"]),
                private_dir=Path(config["private_dir"]),
                schema_path=Path(config.get("schema_path", DEFAULT_SCHEMA)),
            )
        elif args.command == "assemble-cycle002":
            result = assemble_cycle002(
                manifest_path=Path(config["manifest_path"]),
                private_dir=Path(config["private_dir"]),
                public_receipt_path=Path(config["public_receipt_path"]),
                schema_path=Path(config.get("schema_path", DEFAULT_SCHEMA)),
            )
        elif args.command == "prepare":
            result = prepare(
                partition_path=Path(config["partition_path"]),
                materialization_jsonl=Path(config["materialization_jsonl"]),
                materialization_receipt_path=Path(config["materialization_receipt_path"]),
                evaluation_freeze_receipt_path=Path(config["evaluation_freeze_receipt_path"]),
                label_prompt_path=Path(config.get("label_prompt_path", DEFAULT_LABEL_PROMPT)),
                private_dir=Path(config["private_dir"]),
                role_contract_path=Path(config.get("role_contract_path", DEFAULT_ROLE_CONTRACT)),
                evaluation_contract_path=Path(config.get("evaluation_contract_path", DEFAULT_EVALUATION_CONTRACT)),
                schema_path=Path(config.get("schema_path", DEFAULT_SCHEMA)),
                packet_size=config.get("packet_size", 40),
                actor=config.get("actor"),
            )
        elif args.command == "ingest":
            result = ingest(
                manifest_path=Path(config["manifest_path"]),
                packet_index=config["packet_index"],
                raw_response_path=Path(config["raw_response_path"]),
                private_dir=Path(config["private_dir"]),
                schema_path=Path(config.get("schema_path", DEFAULT_SCHEMA)),
                actor=config.get("actor"),
                attempt_kind=config.get("attempt_kind", "first"),
                invalid_first_raw_path=Path(config["invalid_first_raw_path"])
                if config.get("invalid_first_raw_path")
                else None,
            )
        elif args.command == "assemble":
            result = assemble(
                manifest_path=Path(config["manifest_path"]),
                private_dir=Path(config["private_dir"]),
                public_receipt_path=Path(config["public_receipt_path"]),
                schema_path=Path(config.get("schema_path", DEFAULT_SCHEMA)),
                actor=config.get("actor"),
            )
        else:
            raise HeldoutLabelTransportError("unknown heldout label transport command")
    except (HeldoutLabelTransportError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(canonical_json({"ok": True, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
