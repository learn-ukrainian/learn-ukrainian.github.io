#!/usr/bin/env python3
"""Cycle-006 v2 private Grok transport with immutable resumable seals.

The module deliberately contains no provider-specific private data.  A live
package is supplied by the operator outside disposable worktrees; synthetic
tests replace the provider executable and prompt bindings locally.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GROK = Path("/Users/krisztiankoos/.local/bin/grok")
CYCLE = "phase3-v2-1-evaluation-cycle-006"
AMENDMENT_SHA256 = "524e6eb4f18d38f104413fb32f421ff73c3d80bc411d338a6d8a31fabc087474"
CYCLE006_AMENDMENT_SHA256 = AMENDMENT_SHA256
CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
CUSTODY = CUSTODY_SHA256
SOURCE_CUSTODY_SHA256 = CUSTODY_SHA256
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"
LANES = {"clean_label": 40, "residual_label": 164}
ROW_COUNT = 10159
PACKET_COUNT = 204
PACKET_SCHEMA_VERSION = "phase3_cycle006_private_packet_v1"
MANIFEST_SCHEMA_VERSION = "phase3_cycle006_label_manifest_v2"
OUTPUT_ROOT = "label-output-grok-cycle006-v2"
CHUNK_SIZE = 20
PACKET_SIZE = 50
FINAL_PACKET_SIZE = 9

REJECTS = {
    "agree",
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
GENRES = {
    "expository_narrative",
    "scientific_expository",
    "instructional_content_expository",
}
TAX = (
    "alphabet_letter_names_and_graphic_inventory",
    "phoneme_grapheme_correspondence",
    "vowel_and_consonant_alternation",
    "soft_sign_and_miakyi_znak",
    "apostrophe",
    "prefix_and_suffix_spelling",
    "compound_solid_separate_hyphenated_spelling",
    "capitalization",
    "foreign_word_and_name_transmission",
    "proper_and_geographical_names",
    "declension_and_case_endings",
    "finite_verb_conjugation_and_forms",
    "numeral_agreement",
    "direct_address_vocative",
    "impersonal_no_to_expressed_agent",
    "participial_versus_lexicalized_chyi",
    "prepositional_government_valency",
    "lexical_interference",
    "semantic_false_friends_interlanguage_homonyms",
    "phrase_collocation",
    "syntactic_calque",
    "parallel_norms_and_acceptable_variants",
    "punctuation",
)
DEC = {"positive", "acceptable_control", "protected", "abstention", "disagreement"}
FAILURE_CODES = frozenset(
    {
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "ordinal_key_drift",
        "ordinal_identity_binding_drift",
        "label_json_invalid",
        "label_count_or_envelope_drift",
        "identity_or_order_drift",
        "identity_uniqueness_drift",
        "clean_label_schema_drift",
        "clean_label_invariant_drift",
        "residual_label_schema_drift",
        "residual_phenomenon_drift",
        "residual_scored_decision_insufficiency",
        "residual_2019_positive_forbidden",
        "residual_taxonomy_order_or_uniqueness_drift",
        "residual_primary_or_rollup_drift",
        "residual_null_rollup_drift",
    }
)
STRUCTURAL_CODES = frozenset(
    {
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "ordinal_key_drift",
        "ordinal_identity_binding_drift",
        "label_json_invalid",
        "label_count_or_envelope_drift",
        "clean_label_schema_drift",
        "residual_label_schema_drift",
        "residual_phenomenon_drift",
    }
)


class Error(ValueError):
    """Closed, privacy-safe transport failure."""

    def __init__(self, failure_code: str):
        self.failure_code = failure_code if failure_code in FAILURE_CODES else "stream_json_invalid"
        self.code = self.failure_code
        super().__init__(self.failure_code)


class Invalid(Error):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Invalid("stream_json_invalid")
        value[key] = item
    return value


def _regular(path: Path, mode: int | None = None) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        del exc
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("label_count_or_envelope_drift")


def _directory(path: Path, mode: int | None = None) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        del exc
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("label_count_or_envelope_drift")


def atomic(path: Path, value: Any, raw: bool = False) -> str:
    """Write one immutable mode-0600 seal transactionally."""

    if path.exists() or path.is_symlink():
        raise Error("label_count_or_envelope_drift")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    _directory(path.parent, 0o700)
    data = value if raw else canonical(value)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return digest(data)


def read(path: Path, label: str = "private value", *, response: bool = False) -> Any:
    try:
        _regular(path, 0o600)
        value = json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=pairs)
    except Error as exc:
        if response:
            raise Invalid(exc.failure_code) from exc
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Invalid):
        del label
        if response:
            raise Invalid("stream_json_invalid") from None
        raise Error("label_count_or_envelope_drift") from None
    return value


def _identity(row: Any) -> tuple[str, str]:
    if not isinstance(row, dict):
        raise Invalid("identity_or_order_drift")
    unit_id, unit_sha256 = row.get("unit_id"), row.get("unit_sha256")
    if (
        not isinstance(unit_id, str)
        or not isinstance(unit_sha256, str)
        or len(unit_sha256) != 64
        or any(character not in "0123456789abcdef" for character in unit_sha256)
    ):
        raise Invalid("identity_or_order_drift")
    return unit_id, unit_sha256


def identities(rows: list[Any]) -> list[tuple[str, str]]:
    values = [_identity(row) for row in rows]
    if len(values) != len(set(values)):
        raise Invalid("identity_uniqueness_drift")
    return values


def _packet_count(lane: str, index: int) -> int:
    if lane not in LANES or not 1 <= index <= LANES[lane]:
        raise Error("label_count_or_envelope_drift")
    return FINAL_PACKET_SIZE if lane == "residual_label" and index == LANES[lane] else PACKET_SIZE


def _manifest_path(package: Path) -> Path:
    path = package / "label-manifest.json"
    _regular(path, 0o600)
    return path


def _manifest(package: Path) -> dict[str, Any]:
    value = read(_manifest_path(package), "label manifest")
    custody_hash = _custody(package)
    if not isinstance(value, dict):
        raise Error("label_count_or_envelope_drift")
    source_manifest = value.get("source_label_manifest_raw_sha256")
    source_custody = value.get("source_custody_receipt_raw_sha256")
    amendment = value.get("cycle006_amendment_raw_sha256")
    if (
        value.get("schema_version") != MANIFEST_SCHEMA_VERSION
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or value.get("custody_receipt_raw_sha256") != custody_hash
        or source_manifest != SOURCE_MANIFEST_SHA256
        or source_custody != SOURCE_CUSTODY_SHA256
        or amendment != AMENDMENT_SHA256
        or value.get("packet_count") != PACKET_COUNT
        or value.get("row_count") != ROW_COUNT
        or value.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or value.get("text_free") is not True
        or not isinstance(value.get("packets"), list)
        or len(value["packets"]) != PACKET_COUNT
        or value.get("receipt_sha256")
        != digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))
    ):
        raise Error("label_count_or_envelope_drift")
    return value


def _custody(package: Path) -> str:
    path = package / "custody-receipt.json"
    _regular(path, 0o600)
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, Invalid):
        raise Error("label_count_or_envelope_drift") from None
    required = {
        "schema_version",
        "evaluation_cycle_id",
        "source_evaluation_cycle_id",
        "cycle006_amendment_raw_sha256",
        "source_custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "prompt_sha256s",
        "prompt_bindings",
        "text_free",
        "receipt_sha256",
    }
    if (
        not isinstance(value, dict)
        or not required.issubset(value)
        or value.get("schema_version") != "phase3_cycle006_custody_receipt_v2"
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or value.get("cycle006_amendment_raw_sha256") != AMENDMENT_SHA256
        or value.get("source_custody_receipt_raw_sha256") != SOURCE_CUSTODY_SHA256
        or value.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or value.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or value.get("text_free") is not True
        or value.get("receipt_sha256")
        != digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))
    ):
        raise Error("label_count_or_envelope_drift")
    return digest(raw)


def prompt_binding(package: Path, lane: str) -> tuple[Path, str, str]:
    """Resolve the reviewed prompt only from mutually sealed package bindings."""

    manifest = _manifest(package)
    bindings = manifest.get("prompt_bindings")
    if not isinstance(bindings, list):
        raise Error("label_count_or_envelope_drift")
    candidates = [
        candidate
        for candidate in bindings
        if isinstance(candidate, dict) and candidate.get("lane") == lane and candidate.get("provider") == "grok"
    ]
    if len(candidates) != 1:
        raise Error("label_count_or_envelope_drift")
    binding = candidates[0]
    if set(binding) != {"lane", "provider", "path", "sha256"}:
        raise Error("label_count_or_envelope_drift")
    custody_value = read(package / "custody-receipt.json", "custody receipt")
    prompt_hashes = manifest.get("prompt_sha256s")
    if (
        not isinstance(custody_value, dict)
        or custody_value.get("prompt_bindings") != bindings
        or not isinstance(prompt_hashes, dict)
        or custody_value.get("prompt_sha256s") != prompt_hashes
        or len({item.get("path") for item in bindings if isinstance(item, dict)}) != len(bindings)
        or any(
            not isinstance(item, dict)
            or set(item) != {"lane", "provider", "path", "sha256"}
            or not isinstance(item.get("path"), str)
            or not isinstance(item.get("sha256"), str)
            or prompt_hashes.get(item.get("path")) != item.get("sha256")
            for item in bindings
        )
    ):
        raise Error("label_count_or_envelope_drift")
    relative = binding["path"]
    expected_hash = binding["sha256"]
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise Error("label_count_or_envelope_drift")
    prompt_path = package / relative_path
    try:
        prompt_path.resolve(strict=True).relative_to(package.resolve())
    except (OSError, ValueError):
        raise Error("label_count_or_envelope_drift") from None
    _regular(prompt_path, 0o600)
    if digest(prompt_path.read_bytes()) != expected_hash:
        raise Error("label_count_or_envelope_drift")
    return prompt_path, relative, expected_hash


def packet(package: Path, lane: str, index: int) -> tuple[Path, dict[str, Any]]:
    _directory(package, 0o700)
    if lane not in LANES:
        raise Error("label_count_or_envelope_drift")
    count = _packet_count(lane, index)
    path = package / lane / f"packet-{index:04d}.json"
    _regular(path, 0o600)
    value = read(path, "private packet")
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "lane",
            "packet_index",
            "row_count",
            "rows",
            "packet_identity_set_sha256",
        }
        or value.get("schema_version") != PACKET_SCHEMA_VERSION
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("lane") != lane
        or value.get("packet_index") != index
        or value.get("row_count") != count
        or not isinstance(value.get("rows"), list)
        or len(value["rows"]) != count
    ):
        raise Error("label_count_or_envelope_drift")
    ids = identities(value["rows"])
    if value.get("packet_identity_set_sha256") != digest(canonical(sorted(ids))):
        raise Error("identity_or_order_drift")
    manifest = _manifest(package)
    matches = [
        item
        for item in manifest["packets"]
        if isinstance(item, dict) and item.get("lane") == lane and item.get("packet_index") == index
    ]
    expected = {
        "lane": lane,
        "packet_index": index,
        "canonical_basename": path.name,
        "row_count": count,
        "raw_sha256": digest(path.read_bytes()),
        "packet_identity_set_sha256": value["packet_identity_set_sha256"],
    }
    if len(matches) != 1 or matches[0] != expected:
        raise Error("identity_or_order_drift")
    return path, value


def _clean_shape(label: Any) -> None:
    if (
        not isinstance(label, dict)
        or set(label)
        != {
            "unit_id",
            "unit_sha256",
            "decision_code",
            "clean_modern_standard_prose",
            "modern_genre_id",
        }
        or label.get("decision_code") not in REJECTS
        or type(label.get("clean_modern_standard_prose")) is not bool
        or (label.get("modern_genre_id") is not None and label.get("modern_genre_id") not in GENRES)
    ):
        raise Invalid("clean_label_schema_drift")


def clean(label: dict[str, Any]) -> None:
    _clean_shape(label)
    accepted = label["decision_code"] == "agree"
    if (
        accepted != label["clean_modern_standard_prose"]
        or (accepted and label["modern_genre_id"] not in GENRES)
        or (not accepted and label["modern_genre_id"] is not None)
    ):
        raise Invalid("clean_label_invariant_drift")


def _residual_shape(label: Any) -> None:
    if (
        not isinstance(label, dict)
        or set(label)
        != {
            "unit_id",
            "unit_sha256",
            "phenomena",
            "primary_phenomenon_id",
            "item_decision_rollup",
        }
        or not isinstance(label.get("phenomena"), list)
        or not label["phenomena"]
        or label.get("item_decision_rollup") not in DEC
    ):
        raise Invalid("residual_label_schema_drift")
    for phenomenon in label["phenomena"]:
        if (
            not isinstance(phenomenon, dict)
            or set(phenomenon) != {"phenomenon_id", "decision_code", "evidence_sufficiency"}
            or phenomenon.get("phenomenon_id") not in TAX
            or phenomenon.get("decision_code") not in DEC
            or phenomenon.get("evidence_sufficiency") not in {"sufficient", "insufficient"}
        ):
            raise Invalid("residual_phenomenon_drift")


def residual(label: dict[str, Any], source_row: dict[str, Any]) -> None:
    _residual_shape(label)
    names: list[str] = []
    decisions: dict[str, str] = {}
    for phenomenon in label["phenomena"]:
        name = phenomenon["phenomenon_id"]
        decision = phenomenon["decision_code"]
        if (
            decision in {"positive", "acceptable_control", "protected"}
            and phenomenon["evidence_sufficiency"] != "sufficient"
        ):
            raise Invalid("residual_scored_decision_insufficiency")
        if source_row.get("family_id") == "pravopys_2019_complete" and decision == "positive":
            raise Invalid("residual_2019_positive_forbidden")
        names.append(name)
        decisions[name] = decision
    if len(names) != len(set(names)) or names != sorted(names, key=TAX.index):
        raise Invalid("residual_taxonomy_order_or_uniqueness_drift")
    viable = [name for name in names if decisions[name] not in {"abstention", "disagreement"}]
    primary = label["primary_phenomenon_id"]
    if viable:
        if primary not in viable or label["item_decision_rollup"] != decisions[primary]:
            raise Invalid("residual_primary_or_rollup_drift")
    elif primary is not None or label["item_decision_rollup"] != (
        "disagreement" if "disagreement" in decisions.values() else "abstention"
    ):
        raise Invalid("residual_null_rollup_drift")


def _structural_labels(lane: str, labels: Any, expected_count: int) -> list[dict[str, Any]]:
    if not isinstance(labels, dict):
        raise Invalid("label_json_invalid")
    if set(labels) != {"labels"} or not isinstance(labels["labels"], list):
        raise Invalid("label_count_or_envelope_drift")
    if len(labels["labels"]) != expected_count:
        raise Invalid("label_count_or_envelope_drift")
    for label in labels["labels"]:
        if lane == "clean_label":
            _clean_shape(label)
        else:
            _residual_shape(label)
    return labels["labels"]


def validate(lane: str, packet_value: dict[str, Any], raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, Invalid):
        raise Invalid("stream_json_invalid") from None
    rows = packet_value.get("rows") if isinstance(packet_value, dict) else None
    if not isinstance(rows, list):
        raise Invalid("label_count_or_envelope_drift")
    labels = _structural_labels(lane, value, len(rows))
    try:
        source_ids = identities(rows)
        label_ids = [_identity(label) for label in labels]
    except Invalid:
        raise
    if label_ids != source_ids:
        raise Invalid("identity_or_order_drift")
    if len(label_ids) != len(set(label_ids)):
        raise Invalid("identity_uniqueness_drift")
    for source, label in zip(rows, labels, strict=True):
        if lane == "clean_label":
            clean(label)
        else:
            residual(label, source)
    return value


def _decode_provider(raw: bytes, packet_value: dict[str, Any]) -> bytes:
    """Return canonical labels bytes while accepting only one public result.

    Native Grok is configured for plain JSON.  The one-result stream form is
    accepted for deterministic synthetic transport fixtures, but never more
    than one terminal result is admitted.
    """

    try:
        direct = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, Invalid):
        lines = [line for line in raw.splitlines() if line.strip()]
        if not lines:
            raise Invalid("stream_json_invalid") from None
        events: list[Any] = []
        for line in lines:
            try:
                events.append(json.loads(line.decode("utf-8", "strict"), object_pairs_hook=pairs))
            except (UnicodeDecodeError, json.JSONDecodeError, Invalid):
                raise Invalid("stream_json_invalid") from None
        results = [item for item in events if isinstance(item, dict) and item.get("event") == "result"]
        if len(results) != 1:
            raise Invalid("terminal_result_count_drift") from None
        result = results[0]
        if result.get("status") != "SUCCESS" or not isinstance(result.get("structured_output"), dict):
            raise Invalid("structured_output_envelope_drift") from None
        direct = result["structured_output"]
    if isinstance(direct, dict) and "structured_output" in direct:
        if (
            set(direct) != {"status", "structured_output"}
            or direct.get("status") != "SUCCESS"
            or not isinstance(direct["structured_output"], dict)
        ):
            raise Invalid("structured_output_envelope_drift")
        direct = direct["structured_output"]
    # Reparse through the unchanged validator so no free-form provider field
    # can reach a seal.
    canonical_value = canonical(direct)
    validate(packet_value["lane"], packet_value, canonical_value)
    return canonical_value


def _prompt(package_packet: Path, lane: str) -> bytes:
    try:
        package = package_packet.parents[1]
        prompt_path, basename, expected_hash = prompt_binding(package, lane)
        prompt_raw = prompt_path.read_bytes()
    except (KeyError, Error, OSError):
        raise Error("label_count_or_envelope_drift") from None
    if prompt_path.as_posix().endswith(basename) is False or digest(prompt_raw) != expected_hash:
        raise Error("label_count_or_envelope_drift")
    return (
        prompt_raw
        + b"\n\n--- BEGIN IMMUTABLE PRIVATE PACKET JSON ---\n"
        + package_packet.read_bytes()
        + b"\n--- END IMMUTABLE PRIVATE PACKET JSON ---\n"
    )


def _mark(out: Path, lane: str, index: int, attempt: int, code: str, *, retryable: bool) -> None:
    atomic(
        out / f"attempt-{attempt}-{index:04d}.terminal.json",
        {
            "schema_version": "phase3_cycle006_grok_attempt_v2",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "lane": lane,
            "packet_index": index,
            "attempt": attempt,
            "failure_code": code if code in FAILURE_CODES else "stream_json_invalid",
            "retryable": retryable,
            "text_free": True,
        },
    )


def _stop(package: Path, lane: str, index: int, code: str) -> None:
    path = package / OUTPUT_ROOT / "provider-stop.json"
    if path.exists() or path.is_symlink():
        return
    atomic(
        path,
        {
            "schema_version": "phase3_cycle006_grok_provider_stop_v2",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "lane": lane,
            "terminal_packet_index": index,
            "failure_code": code if code in FAILURE_CODES else "stream_json_invalid",
            "new_provider_calls_allowed": False,
            "text_free": True,
        },
    )


def _receipt_paths(package: Path, lane: str, index: int) -> tuple[Path, Path, Path, Path]:
    out = package / OUTPUT_ROOT / lane
    return (
        out / f"labels-{index:04d}.json",
        out / f"receipt-{index:04d}.json",
        out / f"raw-manifest-{index:04d}.json",
        out / f"raw-{index:04d}.raw",
    )


def _verify_sealed(
    package: Path, lane: str, index: int, packet_path: Path, packet_value: dict[str, Any]
) -> dict[str, Any]:
    labels_path, receipt_path, raw_manifest_path, raw_path = _receipt_paths(package, lane, index)
    paths = (labels_path, receipt_path, raw_manifest_path, raw_path)
    present = [path.exists() or path.is_symlink() for path in paths]
    if not any(present):
        raise Error("label_count_or_envelope_drift")
    if not all(present):
        raise Error("label_count_or_envelope_drift")
    for path in paths:
        _regular(path, 0o600)
    labels = read(labels_path, "labels")
    validate(lane, packet_value, canonical(labels))
    raw_manifest = read(raw_manifest_path, "raw manifest")
    receipt = read(receipt_path, "provider receipt")
    dynamic_manifest_hash = digest(_manifest_path(package).read_bytes())
    dynamic_custody_hash = digest((package / "custody-receipt.json").read_bytes())
    _prompt_path, prompt_name, prompt_hash = prompt_binding(package, lane)
    expected_manifest = {
        "schema_version": "phase3_cycle006_grok_raw_manifest_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": packet_value["row_count"],
        "packet_raw_sha256": digest(packet_path.read_bytes()),
        "packet_identity_set_sha256": packet_value["packet_identity_set_sha256"],
        "response_raw_sha256": digest(raw_path.read_bytes()),
        "text_free": True,
    }
    if (
        not isinstance(raw_manifest, dict)
        or set(raw_manifest) != set(expected_manifest) | {"manifest_sha256"}
        or any(raw_manifest.get(key) != value for key, value in expected_manifest.items())
        or raw_manifest.get("manifest_sha256") != digest(canonical(expected_manifest))
    ):
        raise Error("label_count_or_envelope_drift")
    expected_receipt = {
        "schema_version": "phase3_cycle006_grok_packet_label_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": dynamic_custody_hash,
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": dynamic_manifest_hash,
        "lane": lane,
        "packet_index": index,
        "row_count": packet_value["row_count"],
        "packet_raw_sha256": digest(packet_path.read_bytes()),
        "packet_identity_set_sha256": packet_value["packet_identity_set_sha256"],
        "raw_manifest_sha256": digest(raw_manifest_path.read_bytes()),
        "labels_sha256": digest(labels_path.read_bytes()),
        "response_raw_sha256": digest(raw_path.read_bytes()),
        "prompt_path": prompt_name,
        "prompt_sha256": prompt_hash,
        "attempt_count": receipt.get("attempt_count"),
        "exact_model": "grok-4.5",
        "model_family": "xai",
        "harness": "native_grok",
        "text_free": True,
    }
    if (
        not isinstance(receipt, dict)
        or receipt.get("receipt_sha256")
        != digest(canonical({key: value for key, value in receipt.items() if key != "receipt_sha256"}))
        or set(receipt) != set(expected_receipt) | {"receipt_sha256"}
        or receipt.get("attempt_count") not in {1, 2}
        or any(receipt.get(key) != value for key, value in expected_receipt.items())
    ):
        raise Error("label_count_or_envelope_drift")
    return {
        "ok": True,
        "lane": lane,
        "packet_index": index,
        "attempt_count": receipt["attempt_count"],
        "resumed": True,
        "text_free": True,
    }


def _provider_command(provider: Path) -> list[str]:
    # No prompt, packet, raw output, or runtime path is present in argv.
    return [
        str(provider),
        "--model",
        "grok-4.5",
        "--reasoning-effort",
        "high",
        "--output-format",
        "plain",
        "--permission-mode",
        "plan",
        "--no-alt-screen",
        "--no-memory",
        "--no-subagents",
        "--disable-web-search",
        "--verbatim",
    ]


def _provider_mode(provider: Path, *, synthetic_provider: bool) -> None:
    """Make synthetic executables explicit and reject fake live providers."""
    try:
        resolved = provider.resolve(strict=True)
        live = GROK.resolve(strict=True)
    except OSError as exc:
        raise Error("label_count_or_envelope_drift") from exc
    if synthetic_provider:
        if resolved == live:
            raise Error("label_count_or_envelope_drift")
    elif resolved != live:
        raise Error("label_count_or_envelope_drift")


def run_packet(
    package: Path,
    lane: str,
    index: int,
    provider: Path = GROK,
    *,
    synthetic_provider: bool = False,
) -> dict[str, Any]:
    _provider_mode(provider, synthetic_provider=synthetic_provider)
    packet_path, packet_value = packet(package, lane, index)
    labels_path, receipt_path, raw_manifest_path, raw_path = _receipt_paths(package, lane, index)
    present = [path.exists() or path.is_symlink() for path in (labels_path, receipt_path, raw_manifest_path, raw_path)]
    if all(present):
        return _verify_sealed(package, lane, index, packet_path, packet_value)
    if any(present):
        _stop(package, lane, index, "label_count_or_envelope_drift")
        raise Error("label_count_or_envelope_drift")
    if (package / OUTPUT_ROOT / "provider-stop.json").exists():
        raise Error("label_count_or_envelope_drift")
    out = package / OUTPUT_ROOT / lane
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(package / OUTPUT_ROOT, 0o700)
    os.chmod(out, 0o700)
    try:
        prompt_bytes = _prompt(packet_path, lane)
        # A stale started marker consumes an attempt.  It is never silently
        # erased; attempt two is the only resumable retry.
        for attempt in (1, 2):
            marker = out / f"attempt-{attempt}-{index:04d}.terminal.json"
            started = out / f"attempt-{attempt}-{index:04d}.started.json"
            if marker.exists() or started.exists():
                if attempt == 2:
                    raise Error("label_count_or_envelope_drift")
                continue
            atomic(
                started,
                {
                    "schema_version": "phase3_cycle006_grok_attempt_start_v2",
                    "evaluation_cycle_id": CYCLE,
                    "amendment_sha256": AMENDMENT_SHA256,
                    "lane": lane,
                    "packet_index": index,
                    "attempt": attempt,
                    "text_free": True,
                },
            )
            runtime = Path(tempfile.mkdtemp(prefix=f".cycle006-grok-{lane}-{index:04d}-{attempt}-", dir=package))
            os.chmod(runtime, 0o700)
            stdin_path = runtime / "prompt.stdin"
            raw_runtime = runtime / "provider.raw"
            try:
                atomic(stdin_path, prompt_bytes, raw=True)
                raw_descriptor = os.open(raw_runtime, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with stdin_path.open("rb") as stdin_handle, os.fdopen(raw_descriptor, "wb") as raw_handle:
                    result = subprocess.run(
                        _provider_command(provider),
                        stdin=stdin_handle,
                        stdout=raw_handle,
                        stderr=subprocess.DEVNULL,
                        check=False,
                        shell=False,
                    )
                if result.returncode:
                    _mark(out, lane, index, attempt, "stream_json_invalid", retryable=False)
                    raise Error("stream_json_invalid")
                body = raw_runtime.read_bytes()
                try:
                    normalized = _decode_provider(body, packet_value)
                except Invalid as exc:
                    # Identity and semantic validation are terminal; only a
                    # result that cannot be structurally extracted may retry.
                    retryable = exc.failure_code in STRUCTURAL_CODES
                    atomic(out / f"invalid-{attempt}-{index:04d}.raw", body, raw=True)
                    _mark(out, lane, index, attempt, exc.failure_code, retryable=retryable)
                    if retryable and attempt == 1:
                        continue
                    raise Error(exc.failure_code) from None
                # The normalized bytes have already passed the unchanged
                # validator, so all three seals can now be committed.
                raw_hash = atomic(raw_path, body, raw=True)
                labels_hash = atomic(labels_path, json.loads(normalized.decode("utf-8"), object_pairs_hook=pairs))
                raw_manifest = {
                    "schema_version": "phase3_cycle006_grok_raw_manifest_v2",
                    "evaluation_cycle_id": CYCLE,
                    "amendment_sha256": AMENDMENT_SHA256,
                    "lane": lane,
                    "packet_index": index,
                    "row_count": packet_value["row_count"],
                    "packet_raw_sha256": digest(packet_path.read_bytes()),
                    "packet_identity_set_sha256": packet_value["packet_identity_set_sha256"],
                    "response_raw_sha256": raw_hash,
                    "text_free": True,
                }
                raw_manifest["manifest_sha256"] = digest(canonical(raw_manifest))
                raw_manifest_hash = atomic(raw_manifest_path, raw_manifest)
                _prompt_path, prompt_name, prompt_hash = prompt_binding(package, lane)
                receipt = {
                    "schema_version": "phase3_cycle006_grok_packet_label_receipt_v2",
                    "evaluation_cycle_id": CYCLE,
                    "amendment_sha256": AMENDMENT_SHA256,
                    "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
                    "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
                    "manifest_raw_sha256": digest(_manifest_path(package).read_bytes()),
                    "lane": lane,
                    "packet_index": index,
                    "row_count": packet_value["row_count"],
                    "packet_raw_sha256": digest(packet_path.read_bytes()),
                    "packet_identity_set_sha256": packet_value["packet_identity_set_sha256"],
                    "raw_manifest_sha256": raw_manifest_hash,
                    "labels_sha256": labels_hash,
                    "response_raw_sha256": raw_hash,
                    "prompt_path": prompt_name,
                    "prompt_sha256": prompt_hash,
                    "attempt_count": attempt,
                    "exact_model": "grok-4.5",
                    "model_family": "xai",
                    "harness": "native_grok",
                    "text_free": True,
                }
                receipt["receipt_sha256"] = digest(canonical(receipt))
                atomic(receipt_path, receipt)
                return {
                    "ok": True,
                    "lane": lane,
                    "packet_index": index,
                    "attempt_count": attempt,
                    "text_free": True,
                }
            finally:
                stdin_path.unlink(missing_ok=True)
                shutil.rmtree(runtime, ignore_errors=True)
        raise Error("label_count_or_envelope_drift")
    except Error as exc:
        _stop(package, lane, index, exc.failure_code)
        raise


def batch(
    package: Path,
    lane: str,
    start: int,
    end: int,
    concurrency: int,
    provider: Path = GROK,
    *,
    synthetic_provider: bool = False,
) -> dict[str, Any]:
    _provider_mode(provider, synthetic_provider=synthetic_provider)
    if lane not in LANES or not 1 <= start <= end <= LANES[lane] or not 1 <= concurrency <= 4:
        raise Error("label_count_or_envelope_drift")
    if (package / OUTPUT_ROOT / "provider-stop.json").exists():
        raise Error("label_count_or_envelope_drift")
    results: list[dict[str, Any]] = []
    first_failure: dict[str, Any] | None = None
    pending = iter(range(start, end + 1))
    active: dict[concurrent.futures.Future[dict[str, Any]], int] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        while len(active) < concurrency:
            try:
                index = next(pending)
            except StopIteration:
                break
            active[pool.submit(run_packet, package, lane, index, provider, synthetic_provider=synthetic_provider)] = (
                index
            )
        while active:
            done, _ = concurrent.futures.wait(active, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                index = active.pop(future)
                try:
                    result = future.result()
                except Error as exc:
                    result = {
                        "ok": False,
                        "lane": lane,
                        "packet_index": index,
                        "failure_code": exc.failure_code,
                        "text_free": True,
                    }
                results.append(result)
                if not result.get("ok") and first_failure is None:
                    first_failure = result
            if first_failure is None:
                while len(active) < concurrency:
                    try:
                        index = next(pending)
                    except StopIteration:
                        break
                    active[
                        pool.submit(run_packet, package, lane, index, provider, synthetic_provider=synthetic_provider)
                    ] = index
    receipt = {
        "schema_version": "phase3_cycle006_grok_batch_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "lane": lane,
        "requested_packet_count": end - start + 1,
        "sealed_packet_count": sum(bool(item.get("ok")) for item in results),
        "terminal_failure_count": sum(not bool(item.get("ok")) for item in results),
        "stopped": first_failure is not None,
        "text_free": True,
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    atomic(package / OUTPUT_ROOT / f"batch-receipt-{lane}-{start:04d}-{end:04d}.json", receipt)
    return {"ok": first_failure is None, **receipt}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--lane", choices=tuple(LANES), required=True)
    parser.add_argument("--packet-index", type=int)
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--test-provider-bin", type=Path)
    args = parser.parse_args(argv)
    try:
        provider = args.test_provider_bin or GROK
        synthetic_provider = args.test_provider_bin is not None
        if args.packet_index is not None:
            result = run_packet(
                args.package,
                args.lane,
                args.packet_index,
                provider,
                synthetic_provider=synthetic_provider,
            )
        elif args.start is not None and args.end is not None:
            result = batch(
                args.package,
                args.lane,
                args.start,
                args.end,
                args.concurrency,
                provider,
                synthetic_provider=synthetic_provider,
            )
        else:
            raise Error("label_count_or_envelope_drift")
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "stream_json_invalid", "text_free": True}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
