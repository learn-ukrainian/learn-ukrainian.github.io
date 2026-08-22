#!/usr/bin/env python3
"""Fresh selector-only adjudication of Cycle-006 v2 disagreements."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CYCLE = "phase3-v2-1-evaluation-cycle-006"
AMENDMENT_SHA256 = "524e6eb4f18d38f104413fb32f421ff73c3d80bc411d338a6d8a31fabc087474"
CYCLE006_AMENDMENT_SHA256 = AMENDMENT_SHA256
CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"
LANES = {"clean_label": 40, "residual_label": 164}
ROW_COUNT = 10159
OUTPUT = "dual-label-adjudication-cycle006-v2"
CHUNK_SIZE = 20
MODEL = "Claude Sonnet 4.6 (Thinking)"
FAMILY = "anthropic"
HARNESS = "agy"
AGY = Path("/Users/krisztiankoos/.local/bin/agy")
PROMPT = ROOT / "batch_state/phase3-cycle005-dual-label-adjudication-prompt-v1.md"
PROMPT_SHA256 = "8b932ccaf2626092b85ceed48d2ffc42abf007a472c22fbbee915e0e8ab3034e"
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
STRUCTURAL = frozenset(
    {
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "label_json_invalid",
        "label_count_or_envelope_drift",
    }
)


class Error(ValueError):
    def __init__(self, code: str):
        self.code = code if code in FAILURE_CODES else "stream_json_invalid"
        self.failure_code = self.code
        super().__init__(self.code)


class Invalid(Error):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    import hashlib

    return hashlib.sha256(raw).hexdigest()


def _package_custody(package: Path) -> str:
    """Return the hash of this materialized package's custody receipt."""
    path = package / "custody-receipt.json"
    _read(path)
    return digest(path.read_bytes())


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Invalid("stream_json_invalid")
        value[key] = item
    return value


def _load(name: str, path: Path) -> Any:
    if path.is_symlink() or not path.is_file():
        raise Error("label_count_or_envelope_drift")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Error("label_count_or_envelope_drift")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CMP = _load("cycle006_v2_adjudication_compare", ROOT / "batch_state/phase3-compare-cycle006-dual-labels-v2.py")
atomic = CMP.atomic


def _read(path: Path) -> Any:
    try:
        info = path.lstat()
        if info.st_mode & 0o170000 == 0o120000 or not path.is_file() or info.st_mode & 0o777 != 0o600:
            raise Error("label_count_or_envelope_drift")
        return json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Invalid, Error) as exc:
        del exc
        raise Error("label_count_or_envelope_drift") from None


def _identity(row: Any) -> tuple[str, str]:
    try:
        value = (row["unit_id"], row["unit_sha256"])
    except (KeyError, TypeError) as exc:
        del exc
        raise Error("identity_or_order_drift") from None
    if not isinstance(value[0], str) or not isinstance(value[1], str):
        raise Error("identity_or_order_drift")
    return value


def _identities(rows: list[Any]) -> list[tuple[str, str]]:
    values = [_identity(row) for row in rows]
    if len(values) != len(set(values)):
        raise Error("identity_uniqueness_drift")
    return values


def _compare_receipt(package: Path, lane: str, index: int) -> dict[str, Any]:
    path = package / CMP.OUTPUT / lane / f"receipt-{index:04d}.json"
    value = _read(path)
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != "phase3_cycle006_dual_label_packet_receipt_v2"
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("amendment_sha256") != AMENDMENT_SHA256
        or value.get("custody_receipt_raw_sha256") != _package_custody(package)
        or value.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or value.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or value.get("text_free") is not True
        or value.get("receipt_sha256")
        != digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))
    ):
        raise Error("label_count_or_envelope_drift")
    return value


def inputs(
    package: Path, lane: str, index: int
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    compare_receipt = _compare_receipt(package, lane, index)
    contents, grok, gemini = CMP.inputs(package, lane, index)
    if compare_receipt.get("row_count") != contents.get("row_count"):
        raise Error("label_count_or_envelope_drift")
    disagreements: list[dict[str, Any]] = []
    source_ids = _identities(contents["rows"])
    if [_identity(label) for label in grok] != source_ids or [_identity(label) for label in gemini] != source_ids:
        raise Error("identity_or_order_drift")
    for source, left, right in zip(contents["rows"], grok, gemini, strict=True):
        if CMP.semantic(left) != CMP.semantic(right):
            disagreements.append({"source_row": source, "grok_label": left, "gemini_label": right})
    if compare_receipt.get("disagreement_count") != len(disagreements):
        raise Error("label_count_or_envelope_drift")
    return contents, grok, gemini, disagreements, compare_receipt


def disputes(package: Path, lane: str, index: int) -> list[dict[str, Any]]:
    return inputs(package, lane, index)[3]


def schema(count: int) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["selections"],
        "properties": {
            "selections": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["unit_id", "unit_sha256", "selection"],
                    "properties": {
                        "unit_id": {"type": "string"},
                        "unit_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "selection": {"enum": ["grok", "gemini", "unresolved"]},
                    },
                },
            }
        },
    }


def validate(records: list[dict[str, Any]], value: Any) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or set(value) != {"selections"}
        or not isinstance(value["selections"], list)
        or len(value["selections"]) != len(records)
    ):
        raise Invalid("label_count_or_envelope_drift")
    expected = [_identity(record["source_row"]) for record in records]
    seen: list[tuple[str, str]] = []
    for record, selection in zip(records, value["selections"], strict=True):
        if not isinstance(selection, dict) or set(selection) != {"unit_id", "unit_sha256", "selection"}:
            raise Invalid("label_json_invalid")
        identity = _identity(selection)
        if identity != _identity(record["source_row"]):
            raise Invalid("identity_or_order_drift")
        if selection["selection"] not in {"grok", "gemini", "unresolved"}:
            raise Invalid("ordinal_identity_binding_drift")
        seen.append(identity)
    if seen != expected:
        raise Invalid("identity_or_order_drift")
    if len(seen) != len(set(seen)):
        raise Invalid("identity_uniqueness_drift")
    return value


def _structured(raw: bytes) -> Any:
    """Parse AGY's documented ``event:init`` → ``event:result`` stream."""
    try:
        events = [
            json.loads(line, object_pairs_hook=pairs)
            for line in raw.decode("utf-8", "strict").splitlines()
            if line.strip()
        ]
    except (UnicodeDecodeError, json.JSONDecodeError, Invalid) as exc:
        raise Invalid("stream_json_invalid") from exc
    if not events:
        raise Invalid("stream_json_invalid")
    init_events = [event for event in events if isinstance(event, dict) and event.get("event") == "init"]
    result_events = [event for event in events if isinstance(event, dict) and event.get("event") == "result"]
    if len(init_events) != 1 or len(result_events) != 1:
        raise Invalid("terminal_result_count_drift")
    if events[0] is not init_events[0] or events[-1] is not result_events[0]:
        raise Invalid("terminal_result_count_drift")
    init, result_event = init_events[0], result_events[0]
    config, result = init.get("init"), result_event.get("result")
    if not isinstance(config, dict) or config.get("model") != MODEL:
        raise Invalid("structured_output_envelope_drift")
    if not isinstance(result, dict) or result.get("status") != "SUCCESS" or "structured_output" not in result:
        raise Invalid("structured_output_envelope_drift")
    output = result["structured_output"]
    if not isinstance(output, dict):
        raise Invalid("structured_output_envelope_drift")
    return output


def _command(provider: Path, schema_path: Path) -> list[str]:
    # The dispute chunk is stdin-only; schema_path is public runtime metadata.
    return [
        str(provider),
        "--model",
        MODEL,
        "--mode",
        "plan",
        "--sandbox",
        "--disable-slash-commands",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
        "--json-schema",
        str(schema_path),
    ]


def agy_executable_sha256(provider: Path = AGY) -> str:
    """Hash the resolved AGY executable immediately before a real call."""
    try:
        resolved = provider.resolve(strict=True)
    except OSError as exc:
        raise Error("structured_output_envelope_drift") from exc
    if not resolved.is_file():
        raise Error("structured_output_envelope_drift")
    return digest(resolved.read_bytes())


def _provider_mode(provider: Path, *, expected_agy_sha256: str | None, synthetic_provider: bool) -> None:
    """Require explicit synthetic mode or controller-bound real AGY mode."""
    if synthetic_provider:
        if expected_agy_sha256 is not None:
            raise Error("ordinal_identity_binding_drift")
        try:
            if provider.resolve(strict=True) == AGY.resolve(strict=True):
                raise Error("ordinal_identity_binding_drift")
        except OSError as exc:
            raise Error("ordinal_identity_binding_drift") from exc
        return
    if (
        expected_agy_sha256 is None
        or len(expected_agy_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_agy_sha256)
    ):
        raise Error("ordinal_identity_binding_drift")
    try:
        if provider.resolve(strict=True) != AGY.resolve(strict=True):
            raise Error("ordinal_identity_binding_drift")
    except OSError as exc:
        raise Error("ordinal_identity_binding_drift") from exc


def _stop(package: Path, lane: str, index: int, code: str) -> None:
    path = package / OUTPUT / "provider-stop.json"
    if path.exists() or path.is_symlink():
        return
    atomic(
        path,
        {
            "schema_version": "phase3_cycle006_adjudication_stop_v2",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "lane": lane,
            "terminal_packet_index": index,
            "failure_code": code if code in FAILURE_CODES else "stream_json_invalid",
            "new_provider_calls_allowed": False,
            "text_free": True,
        },
    )


def _paths(package: Path, lane: str, index: int) -> tuple[Path, Path, Path]:
    out = package / OUTPUT / "final" / lane
    return (
        out / f"labels-{index:04d}.json",
        out / f"unresolved-{index:04d}.json",
        out / f"receipt-{index:04d}.json",
    )


def _base_value(
    package: Path, lane: str, index: int
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if lane not in LANES or not 1 <= index <= LANES[lane]:
        raise Error("label_count_or_envelope_drift")
    return inputs(package, lane, index)


def _effective(
    contents: dict[str, Any],
    grok: list[dict[str, Any]],
    gemini: list[dict[str, Any]],
    records: list[dict[str, Any]],
    choices: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    choice_map: dict[tuple[str, str], str] = {}
    for item in choices:
        identity = _identity(item)
        if identity in choice_map:
            raise Error("identity_uniqueness_drift")
        choice_map[identity] = item["selection"]
    expected = [_identity(record["source_row"]) for record in records]
    if list(choice_map) != expected:
        raise Error("identity_or_order_drift")
    labels: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    for source, left, right in zip(contents["rows"], grok, gemini, strict=True):
        identity = _identity(source)
        if CMP.semantic(left) == CMP.semantic(right):
            labels.append(left)
            continue
        selection = choice_map[identity]
        if selection == "grok":
            labels.append(left)
        elif selection == "gemini":
            labels.append(right)
        elif selection == "unresolved":
            unresolved.append({"unit_id": identity[0], "unit_sha256": identity[1]})
        else:
            raise Error("ordinal_identity_binding_drift")
    return labels, unresolved


def _seal_final(
    package: Path,
    lane: str,
    index: int,
    contents: dict[str, Any],
    grok: list[dict[str, Any]],
    gemini: list[dict[str, Any]],
    records: list[dict[str, Any]],
    choices: list[dict[str, Any]],
    compare_receipt: dict[str, Any],
    attempt_count: int,
) -> dict[str, Any]:
    labels, unresolved = _effective(contents, grok, gemini, records, choices)
    labels_path, unresolved_path, receipt_path = _paths(package, lane, index)
    labels_hash = atomic(labels_path, {"labels": labels})
    unresolved_hash = atomic(unresolved_path, {"identities": unresolved})
    body = {
        "schema_version": "phase3_cycle006_final_label_packet_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": _package_custody(package),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": contents["row_count"],
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "compare_receipt_sha256": compare_receipt["receipt_sha256"],
        "disagreement_count": len(records),
        "selection_count": len(choices),
        "accepted_count": len(labels),
        "unresolved_count": len(unresolved),
        "labels_sha256": labels_hash,
        "unresolved_sha256": unresolved_hash,
        "adjudicator": {
            "exact_model": MODEL,
            "model_family": FAMILY,
            "harness": HARNESS,
        },
        "attempt_count": attempt_count,
        "candidate_only": True,
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    atomic(receipt_path, body)
    return verify_packet(package, lane, index)


def run_packet(
    package: Path,
    lane: str,
    index: int,
    provider: Path = AGY,
    *,
    expected_agy_sha256: str | None = None,
    synthetic_provider: bool = False,
) -> dict[str, Any]:
    _provider_mode(
        provider,
        expected_agy_sha256=expected_agy_sha256,
        synthetic_provider=synthetic_provider,
    )
    contents, grok, gemini, records, compare_receipt = _base_value(package, lane, index)
    labels_path, unresolved_path, receipt_path = _paths(package, lane, index)
    present = [path.exists() or path.is_symlink() for path in (labels_path, unresolved_path, receipt_path)]
    if all(present):
        return verify_packet(package, lane, index)
    if any(present):
        _stop(package, lane, index, "label_count_or_envelope_drift")
        raise Error("label_count_or_envelope_drift")
    if (package / OUTPUT / "provider-stop.json").exists():
        raise Error("label_count_or_envelope_drift")
    out = package / OUTPUT / lane / "chunks" / f"packet-{index:04d}"
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(package / OUTPUT, 0o700)
    os.chmod(package / OUTPUT / lane, 0o700)
    os.chmod(package / OUTPUT / lane / "chunks", 0o700)
    os.chmod(out, 0o700)
    choices: list[dict[str, Any]] = []
    attempt_count = 0
    if records:
        try:
            prompt_raw = PROMPT.read_bytes()
            if digest(prompt_raw) != PROMPT_SHA256:
                raise Error("label_count_or_envelope_drift")
        except (OSError, ValueError):
            raise Error("label_count_or_envelope_drift") from None
        for chunk, start in enumerate(range(0, len(records), CHUNK_SIZE), 1):
            part = records[start : start + CHUNK_SIZE]
            target = out / f"selections-chunk-{chunk:02d}.json"
            chunk_receipt = out / f"receipt-chunk-{chunk:02d}.json"
            present_chunk = [
                target.exists() or target.is_symlink(),
                chunk_receipt.exists() or chunk_receipt.is_symlink(),
            ]
            if all(present_chunk):
                value = _read(target)
                validate(part, value)
                receipt = _read(chunk_receipt)
                if receipt.get("receipt_sha256") != digest(
                    canonical({key: item for key, item in receipt.items() if key != "receipt_sha256"})
                ):
                    raise Error("label_count_or_envelope_drift")
                choices.extend(value["selections"])
                continue
            if any(present_chunk):
                _stop(package, lane, index, "label_count_or_envelope_drift")
                raise Error("label_count_or_envelope_drift")
            for attempt in (1, 2):
                attempt_count = max(attempt_count, attempt)
                runtime = Path(
                    tempfile.mkdtemp(
                        prefix=f".cycle006-adjudication-{lane}-{index:04d}-{chunk:02d}-{attempt}-", dir=package
                    )
                )
                os.chmod(runtime, 0o700)
                stdin_path = runtime / "prompt.stdin"
                schema_path = runtime / "response-schema.json"
                raw_path = runtime / "provider.raw"
                try:
                    schema_hash = atomic(schema_path, schema(len(part)))
                    text = (
                        prompt_raw
                        + b"\n--- BEGIN PRIVATE DISPUTE CHUNK JSON ---\n"
                        + canonical({"records": part})
                        + b"--- END PRIVATE DISPUTE CHUNK JSON ---\n"
                    )
                    atomic(
                        stdin_path,
                        json.dumps(
                            {"event": "user", "message": {"content": [{"type": "text", "text": text.decode("utf-8")}]}},
                            separators=(",", ":"),
                        ).encode()
                        + b"\n",
                        raw=True,
                    )
                    if not synthetic_provider and agy_executable_sha256(provider) != expected_agy_sha256:
                        raise Error("structured_output_envelope_drift")
                    with stdin_path.open("rb") as stdin_handle, raw_path.open("xb") as raw_handle:
                        os.chmod(raw_path, 0o600)
                        result = subprocess.run(
                            _command(provider, schema_path),
                            stdin=stdin_handle,
                            stdout=raw_handle,
                            stderr=subprocess.DEVNULL,
                            check=False,
                            shell=False,
                        )
                    if result.returncode:
                        _stop(package, lane, index, "stream_json_invalid")
                        raise Error("stream_json_invalid")
                    try:
                        selected = validate(part, _structured(raw_path.read_bytes()))
                    except Invalid as exc:
                        retryable = exc.code in STRUCTURAL
                        marker = out / f"invalid-{attempt}-chunk-{chunk:02d}.raw"
                        atomic(marker, raw_path.read_bytes(), raw=True)
                        if not retryable or attempt == 2:
                            _stop(package, lane, index, exc.code)
                            raise Error(exc.code) from None
                        continue
                    choices.extend(selected["selections"])
                    chunk_body = {
                        "schema_version": "phase3_cycle006_adjudication_chunk_receipt_v2",
                        "evaluation_cycle_id": CYCLE,
                        "amendment_sha256": AMENDMENT_SHA256,
                        "lane": lane,
                        "packet_index": index,
                        "chunk_index": chunk,
                        "chunk_count": (len(records) + CHUNK_SIZE - 1) // CHUNK_SIZE,
                        "row_count": len(part),
                        "chunk_identity_set_sha256": digest(
                            canonical([_identity(record["source_row"]) for record in part])
                        ),
                        "response_raw_sha256": digest(raw_path.read_bytes()),
                        "selection_sha256": digest(canonical(selected)),
                        "attempt_count": attempt,
                        "schema_sha256": schema_hash,
                        "exact_model": MODEL,
                        "model_family": FAMILY,
                        "harness": HARNESS,
                        "text_free": True,
                    }
                    chunk_body["receipt_sha256"] = digest(canonical(chunk_body))
                    atomic(target, selected)
                    atomic(chunk_receipt, chunk_body)
                    break
                finally:
                    stdin_path.unlink(missing_ok=True)
                    shutil.rmtree(runtime, ignore_errors=True)
            else:
                _stop(package, lane, index, "label_count_or_envelope_drift")
                raise Error("label_count_or_envelope_drift")
    else:
        attempt_count = 0
    return _seal_final(package, lane, index, contents, grok, gemini, records, choices, compare_receipt, attempt_count)


def verify_packet(package: Path, lane: str, index: int) -> dict[str, Any]:
    contents, grok, gemini, records, compare_receipt = _base_value(package, lane, index)
    labels_path, unresolved_path, receipt_path = _paths(package, lane, index)
    labels = _read(labels_path)
    unresolved = _read(unresolved_path)
    receipt = _read(receipt_path)
    if (
        not isinstance(labels, dict)
        or set(labels) != {"labels"}
        or not isinstance(labels["labels"], list)
        or not isinstance(unresolved, dict)
        or set(unresolved) != {"identities"}
        or not isinstance(unresolved["identities"], list)
        or not isinstance(receipt, dict)
        or receipt.get("schema_version") != "phase3_cycle006_final_label_packet_receipt_v2"
        or receipt.get("evaluation_cycle_id") != CYCLE
        or receipt.get("amendment_sha256") != AMENDMENT_SHA256
        or receipt.get("custody_receipt_raw_sha256") != _package_custody(package)
        or receipt.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or receipt.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or receipt.get("candidate_only") is not True
        or receipt.get("text_free") is not True
        or receipt.get("receipt_sha256")
        != digest(canonical({key: item for key, item in receipt.items() if key != "receipt_sha256"}))
    ):
        raise Error("label_count_or_envelope_drift")
    source_ids = [_identity(row) for row in contents["rows"]]
    label_ids = [_identity(label) for label in labels["labels"]]
    unresolved_ids = [_identity(item) for item in unresolved["identities"]]
    if len(label_ids) != receipt.get("accepted_count") or len(unresolved_ids) != receipt.get("unresolved_count"):
        raise Error("label_count_or_envelope_drift")
    if len(set(label_ids + unresolved_ids)) != len(source_ids) or set(label_ids + unresolved_ids) != set(source_ids):
        raise Error("identity_uniqueness_drift")
    expected_disputes = {_identity(record["source_row"]): record for record in records}
    choices: dict[tuple[str, str], str] = {}
    for chunk_path in sorted(
        (package / OUTPUT / lane / "chunks" / f"packet-{index:04d}").glob("selections-chunk-*.json")
    ):
        value = _read(chunk_path)
        if not isinstance(value, dict) or set(value) != {"selections"}:
            raise Error("label_count_or_envelope_drift")
        for selection in value["selections"]:
            identity = _identity(selection)
            if identity in choices or identity not in expected_disputes:
                raise Error("identity_or_order_drift")
            if selection.get("selection") not in {"grok", "gemini", "unresolved"}:
                raise Error("ordinal_identity_binding_drift")
            choices[identity] = selection["selection"]
    if set(choices) != set(expected_disputes):
        raise Error("identity_or_order_drift")
    expected_labels, expected_unresolved = _effective(
        contents,
        grok,
        gemini,
        records,
        [
            {"unit_id": identity[0], "unit_sha256": identity[1], "selection": choices[identity]}
            for identity in [_identity(record["source_row"]) for record in records]
        ],
    )
    if labels["labels"] != expected_labels or unresolved["identities"] != expected_unresolved:
        raise Error("identity_or_order_drift")
    expected_receipt = {
        "schema_version": "phase3_cycle006_final_label_packet_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": _package_custody(package),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": contents["row_count"],
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "compare_receipt_sha256": compare_receipt["receipt_sha256"],
        "disagreement_count": len(records),
        "selection_count": len(choices),
        "accepted_count": len(expected_labels),
        "unresolved_count": len(expected_unresolved),
        "labels_sha256": digest(labels_path.read_bytes()),
        "unresolved_sha256": digest(unresolved_path.read_bytes()),
        "adjudicator": receipt.get("adjudicator"),
        "attempt_count": receipt.get("attempt_count"),
        "candidate_only": True,
        "text_free": True,
    }
    if set(receipt) != set(expected_receipt) | {"receipt_sha256"} or any(
        receipt.get(key) != value for key, value in expected_receipt.items()
    ):
        raise Error("label_count_or_envelope_drift")
    return {
        "ok": True,
        "lane": lane,
        "packet_index": index,
        "accepted_count": len(expected_labels),
        "unresolved_count": len(expected_unresolved),
        "text_free": True,
    }


def verify_complete(package: Path) -> dict[str, Any]:
    accepted = unresolved = packets = 0
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            result = verify_packet(package, lane, index)
            accepted += result["accepted_count"]
            unresolved += result["unresolved_count"]
            packets += 1
    if packets != sum(LANES.values()) or accepted + unresolved != ROW_COUNT:
        raise Error("label_count_or_envelope_drift")
    return {
        "ok": True,
        "complete": True,
        "packet_count": packets,
        "row_count": ROW_COUNT,
        "accepted_count": accepted,
        "unresolved_count": unresolved,
        "residual_zero": unresolved == 0,
        "text_free": True,
    }


def run_all(
    package: Path,
    provider: Path = AGY,
    *,
    expected_agy_sha256: str | None = None,
    synthetic_provider: bool = False,
) -> dict[str, Any]:
    """Resume every packet in frozen lane/order, then prove packet coverage."""
    _provider_mode(
        provider,
        expected_agy_sha256=expected_agy_sha256,
        synthetic_provider=synthetic_provider,
    )
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            if (package / OUTPUT / "provider-stop.json").exists():
                raise Error("ordinal_identity_binding_drift")
            run_packet(
                package,
                lane,
                index,
                provider,
                expected_agy_sha256=expected_agy_sha256,
                synthetic_provider=synthetic_provider,
            )
    return verify_complete(package)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--lane", choices=tuple(LANES))
    parser.add_argument("--packet-index", type=int)
    parser.add_argument("--verify-complete", action="store_true")
    parser.add_argument(
        "--all", action="store_true", help="resume every missing packet sequentially and verify coverage"
    )
    parser.add_argument("--test-provider-bin", type=Path)
    parser.add_argument(
        "--expected-agy-executable-sha",
        help="controller-bound AGY executable SHA256; required for real provider calls",
    )
    args = parser.parse_args(argv)
    try:
        if args.verify_complete and (args.all or args.lane is not None or args.packet_index is not None):
            raise Error("ordinal_identity_binding_drift")
        if args.all and (args.lane is not None or args.packet_index is not None):
            raise Error("ordinal_identity_binding_drift")
        synthetic_provider = args.test_provider_bin is not None
        if not args.verify_complete:
            _provider_mode(
                args.test_provider_bin or AGY,
                expected_agy_sha256=args.expected_agy_executable_sha,
                synthetic_provider=synthetic_provider,
            )
        if args.verify_complete:
            result = verify_complete(args.package)
        elif args.all:
            result = run_all(
                args.package,
                args.test_provider_bin or AGY,
                expected_agy_sha256=args.expected_agy_executable_sha,
                synthetic_provider=synthetic_provider,
            )
        elif args.lane is not None and args.packet_index is not None:
            result = run_packet(
                args.package,
                args.lane,
                args.packet_index,
                args.test_provider_bin or AGY,
                expected_agy_sha256=args.expected_agy_executable_sha,
                synthetic_provider=synthetic_provider,
            )
        else:
            raise Error("label_count_or_envelope_drift")
    except Error as exc:
        result = {"ok": False, "failure_code": exc.code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "stream_json_invalid", "text_free": True}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
