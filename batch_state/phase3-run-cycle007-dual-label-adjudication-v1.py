#!/usr/bin/env python3
"""Fail-closed, fresh Anthropic-family selection of Cycle 007 disagreements.

Only a comparison packet's immutable disagreement records reach the selector.
It never creates a label: each response selects a sealed Grok candidate, a
sealed Gemini candidate, or explicitly requests ``unresolved``.
"""

from __future__ import annotations

import argparse
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
CYCLE = "phase3-v2-1-evaluation-cycle-007"
EVALUATION_CYCLE_ID = CYCLE
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
CYCLE007_AMENDMENT_SHA256 = AMENDMENT_SHA256
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
CUSTODY_SHA256 = SOURCE_CUSTODY_SHA256
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"
LANES = {"clean_label": 40, "residual_label": 164}
OUTPUT = "dual-label-adjudication-cycle007-v1"
COMPARE_OUTPUT = "dual-label-output-cycle007-v1"

MODEL = "Claude Sonnet 4.6 (Thinking)"
FAMILY = "anthropic"
HARNESS = "agy"
AGY = Path("/Users/krisztiankoos/.local/bin/agy")
MAX_STRUCTURAL_ATTEMPTS = 2
SELECTOR_INSTRUCTION = (
    "You are the fresh source-qualified Cycle 007 disagreement adjudicator. "
    "Use the supplied immutable source evidence sidecar and source authority; "
    "do not use model memory as authority. For every record choose exactly one "
    "existing candidate, grok or gemini, only when its cited evidence supports "
    "it. Otherwise choose unresolved. Do not create, rewrite, or explain labels."
)

FAILURE_CODES = frozenset(
    {
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "ordinal_identity_binding_drift",
        "label_json_invalid",
        "label_count_or_envelope_drift",
        "identity_or_order_drift",
        "identity_uniqueness_drift",
        "third_label_invented_drift",
        "adjudication_model_family_drift",
        "binding_failure",
        "mode_drift",
        "provider_transport_failure",
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
    return hashlib.sha256(raw).hexdigest()


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Invalid("stream_json_invalid")
        value[key] = item
    return value


def _regular(path: Path, mode: int | None = 0o600) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _directory(path: Path, mode: int | None = 0o700) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _private_directory(package: Path, path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    current = path
    while current != package:
        current.chmod(0o700)
        current = current.parent
    _directory(package, 0o700)


def read(path: Path, label: str = "sealed value") -> Any:
    del label
    try:
        _regular(path, 0o600)
        return json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Invalid, Error):
        raise Error("label_count_or_envelope_drift") from None


def atomic(path: Path, value: Any, *, raw: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _directory(path.parent, 0o700)
    data = value if raw else canonical(value)
    if not isinstance(data, bytes):
        raise Error("label_count_or_envelope_drift")
    if path.exists() or path.is_symlink():
        _regular(path, 0o600)
        if path.read_bytes() != data:
            raise Error("label_count_or_envelope_drift")
        return digest(data)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with open(fd, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
        os.chmod(path, 0o600)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return digest(data)


def _identity(value: Any) -> tuple[str, str]:
    try:
        identity = (value["unit_id"], value["unit_sha256"])
    except (KeyError, TypeError) as exc:
        raise Invalid("ordinal_identity_binding_drift") from exc
    if not isinstance(identity[0], str) or not isinstance(identity[1], str):
        raise Invalid("ordinal_identity_binding_drift")
    return identity


def validate_adjudication_selection(records: list[dict[str, Any]], payload: Any) -> list[dict[str, Any]]:
    if (
        not isinstance(payload, dict)
        or set(payload) != {"selections"}
        or not isinstance(payload["selections"], list)
        or len(payload["selections"]) != len(records)
    ):
        raise Invalid("structured_output_envelope_drift")
    validated: list[dict[str, Any]] = []
    seen: list[tuple[str, str]] = []
    for record, selection in zip(records, payload["selections"], strict=True):
        if not isinstance(record, dict) or not isinstance(selection, dict):
            raise Invalid("ordinal_identity_binding_drift")
        expected = _identity(record.get("source_row"))
        if set(selection) != {"unit_id", "unit_sha256", "selection"} or _identity(selection) != expected:
            raise Invalid("ordinal_identity_binding_drift")
        if selection.get("selection") not in {"grok", "gemini", "unresolved"}:
            raise Invalid("third_label_invented_drift")
        seen.append(expected)
        validated.append(selection)
    if len(seen) != len(set(seen)):
        raise Invalid("identity_uniqueness_drift")
    return validated


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


def _structured(raw: bytes) -> Any:
    try:
        events = [
            json.loads(line, object_pairs_hook=pairs)
            for line in raw.decode("utf-8", "strict").splitlines()
            if line.strip()
        ]
    except (UnicodeDecodeError, json.JSONDecodeError, Invalid) as exc:
        raise Invalid("stream_json_invalid") from exc
    init = [event for event in events if isinstance(event, dict) and event.get("event") == "init"]
    result = [event for event in events if isinstance(event, dict) and event.get("event") == "result"]
    if len(init) != 1 or len(result) != 1 or not events or events[0] is not init[0] or events[-1] is not result[0]:
        raise Invalid("terminal_result_count_drift")
    config, output = init[0].get("init"), result[0].get("result")
    if not isinstance(config, dict) or config.get("model") != MODEL:
        raise Invalid("structured_output_envelope_drift")
    if not isinstance(output, dict) or output.get("status") != "SUCCESS" or not isinstance(output.get("structured_output"), dict):
        raise Invalid("structured_output_envelope_drift")
    return output["structured_output"]


def _command(provider: Path, schema_path: Path) -> list[str]:
    return [str(provider), "--model", MODEL, "--mode", "plan", "--sandbox", "--disable-slash-commands", "--input-format", "stream-json", "--output-format", "stream-json", "--json-schema", str(schema_path)]


def agy_executable_sha256(provider: Path = AGY) -> str:
    try:
        resolved = provider.resolve(strict=True)
    except OSError as exc:
        raise Error("binding_failure") from exc
    if not resolved.is_file():
        raise Error("binding_failure")
    return digest(resolved.read_bytes())


def _provider_mode(provider: Path, *, expected_agy_sha256: str | None, synthetic_provider: bool) -> None:
    if synthetic_provider:
        if expected_agy_sha256 is not None:
            raise Error("mode_drift")
        try:
            if provider.resolve(strict=True) == AGY.resolve(strict=True):
                raise Error("mode_drift")
        except OSError as exc:
            raise Error("mode_drift") from exc
        return
    if (
        expected_agy_sha256 is None
        or len(expected_agy_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_agy_sha256)
    ):
        raise Error("binding_failure")
    try:
        if provider.resolve(strict=True) != AGY.resolve(strict=True):
            raise Error("binding_failure")
    except OSError as exc:
        raise Error("binding_failure") from exc


def _stop(package: Path, lane: str, index: int, code: str) -> None:
    path = package / OUTPUT / "provider-stop.json"
    if path.exists() or path.is_symlink():
        return
    _private_directory(package, path.parent)
    atomic(path, {"schema_version": "phase3_cycle007_dual_label_adjudication_stop_v1", "evaluation_cycle_id": CYCLE, "amendment_sha256": AMENDMENT_SHA256, "lane": lane, "terminal_packet_index": index, "failure_code": code if code in FAILURE_CODES else "stream_json_invalid", "new_provider_calls_allowed": False, "text_free": True})


def _paths(package: Path, lane: str, index: int) -> tuple[Path, Path, Path, Path]:
    out = package / OUTPUT / "final" / lane
    return (out / f"labels-{index:04d}.json", out / f"unresolved-{index:04d}.json", out / f"selection-{index:04d}.json", out / f"receipt-{index:04d}.json")


def _records(package: Path, lane: str, index: int) -> list[dict[str, Any]]:
    if lane not in LANES or not 1 <= index <= LANES[lane]:
        raise Error("label_count_or_envelope_drift")
    value = read(package / COMPARE_OUTPUT / lane / f"disagreements-{index:04d}.json")
    if not isinstance(value, dict) or set(value) != {"records"} or not isinstance(value["records"], list):
        raise Error("label_count_or_envelope_drift")
    records = value["records"]
    identities: list[tuple[str, str] | None] = []
    for record in records:
        if not isinstance(record, dict):
            identities.append(None)
            continue
        source = _identity(record.get("source_row"))
        try:
            if _identity(record["grok_label"]) != source or _identity(record["gemini_label"]) != source:
                raise Error("identity_or_order_drift")
        except (KeyError, TypeError, Invalid) as exc:
            raise Error("identity_or_order_drift") from exc
        identities.append(source)
    if any(identity is None for identity in identities) or len(identities) != len(set(identities)):
        raise Error("identity_uniqueness_drift")
    return records


def _selector_envelope(records: list[dict[str, Any]]) -> bytes:
    text = SELECTOR_INSTRUCTION + "\n--- BEGIN IMMUTABLE DISAGREEMENT RECORDS JSON ---\n" + canonical({"records": records}).decode("utf-8") + "--- END IMMUTABLE DISAGREEMENT RECORDS JSON ---\n"
    return canonical({"event": "user", "message": {"content": [{"type": "text", "text": text}]}})


def _select_with_provider(package: Path, lane: str, index: int, records: list[dict[str, Any]], provider: Path, *, expected_agy_sha256: str | None, synthetic_provider: bool) -> tuple[list[dict[str, Any]], int, str]:
    _provider_mode(provider, expected_agy_sha256=expected_agy_sha256, synthetic_provider=synthetic_provider)
    runtime = Path(tempfile.mkdtemp(prefix=f".cycle007-adjudication-{lane}-{index:04d}-", dir=package))
    os.chmod(runtime, 0o700)
    stdin_path, schema_path, raw_path = runtime / "prompt.stdin", runtime / "response-schema.json", runtime / "provider.raw"
    envelope = _selector_envelope(records)
    try:
        atomic(stdin_path, envelope, raw=True)
        atomic(schema_path, schema(len(records)))
        for attempt in range(1, MAX_STRUCTURAL_ATTEMPTS + 1):
            if not synthetic_provider and agy_executable_sha256(provider) != expected_agy_sha256:
                raise Error("binding_failure")
            with stdin_path.open("rb") as stdin_handle, raw_path.open("xb") as raw_handle:
                os.chmod(raw_path, 0o600)
                result = subprocess.run(_command(provider, schema_path), stdin=stdin_handle, stdout=raw_handle, stderr=subprocess.DEVNULL, check=False, shell=False)
            if result.returncode:
                _stop(package, lane, index, "provider_transport_failure")
                raise Error("provider_transport_failure")
            try:
                selections = validate_adjudication_selection(records, _structured(raw_path.read_bytes()))
            except Invalid as exc:
                raw_path.unlink(missing_ok=True)
                if exc.code not in STRUCTURAL or attempt == MAX_STRUCTURAL_ATTEMPTS:
                    _stop(package, lane, index, exc.code)
                    raise Error(exc.code) from None
                continue
            return selections, attempt, digest(envelope)
        raise Error("stream_json_invalid")
    finally:
        stdin_path.unlink(missing_ok=True)
        raw_path.unlink(missing_ok=True)
        schema_path.unlink(missing_ok=True)
        shutil.rmtree(runtime, ignore_errors=True)


def _seal(package: Path, lane: str, index: int, records: list[dict[str, Any]], selections: list[dict[str, Any]], *, attempt_count: int, input_sha256: str) -> dict[str, Any]:
    labels: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for record, selection in zip(records, selections, strict=True):
        if selection["selection"] == "grok":
            labels.append(record["grok_label"])
        elif selection["selection"] == "gemini":
            labels.append(record["gemini_label"])
        elif selection["selection"] == "unresolved":
            unresolved.append(record)
        else:
            raise Error("third_label_invented_drift")
    out_dir = package / OUTPUT / "final" / lane
    _private_directory(package, out_dir)
    labels_path, unresolved_path, selection_path, receipt_path = _paths(package, lane, index)
    body = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_packet_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "disagreement_count": len(records),
        "adjudicated_count": len(labels),
        "unresolved_count": len(unresolved),
        "immutable_disagreement_input_sha256": input_sha256,
        "selection_sha256": atomic(selection_path, {"selections": selections}),
        "labels_sha256": atomic(labels_path, {"labels": labels}),
        "unresolved_sha256": atomic(unresolved_path, {"records": unresolved}),
        "adjudicator": {"exact_model": MODEL, "model_family": FAMILY, "harness": HARNESS},
        "attempt_count": attempt_count,
        "candidate_only": True,
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    atomic(receipt_path, body)
    return body


def adjudicate_packet(package: Path, lane: str, index: int, selections_override: dict[str, Any] | None = None, *, provider: Path = AGY, expected_agy_sha256: str | None = None, synthetic_provider: bool = False) -> dict[str, Any]:
    """Seal one packet; a direct selection override is fixture-only, never real mode."""
    records = _records(package, lane, index)
    present = [path.exists() or path.is_symlink() for path in _paths(package, lane, index)]
    if all(present):
        return verify_packet(package, lane, index)
    if any(present):
        _stop(package, lane, index, "label_count_or_envelope_drift")
        raise Error("label_count_or_envelope_drift")
    if (package / OUTPUT / "provider-stop.json").exists():
        raise Error("binding_failure")
    if selections_override is not None:
        if not synthetic_provider:
            raise Error("mode_drift")
        selections = validate_adjudication_selection(records, selections_override)
        return _seal(package, lane, index, records, selections, attempt_count=0, input_sha256=digest(canonical({"records": records})))
    if not records:
        return _seal(package, lane, index, records, [], attempt_count=0, input_sha256=digest(canonical({"records": records})))
    selections, attempts, input_sha256 = _select_with_provider(package, lane, index, records, provider, expected_agy_sha256=expected_agy_sha256, synthetic_provider=synthetic_provider)
    return _seal(package, lane, index, records, selections, attempt_count=attempts, input_sha256=input_sha256)


def verify_packet(package: Path, lane: str, index: int) -> dict[str, Any]:
    records = _records(package, lane, index)
    labels_path, unresolved_path, selection_path, receipt_path = _paths(package, lane, index)
    labels, unresolved, selection, receipt = (read(path) for path in (labels_path, unresolved_path, selection_path, receipt_path))
    if not (isinstance(labels, dict) and set(labels) == {"labels"} and isinstance(labels["labels"], list) and isinstance(unresolved, dict) and set(unresolved) == {"records"} and isinstance(unresolved["records"], list) and isinstance(selection, dict) and isinstance(receipt, dict)):
        raise Error("label_count_or_envelope_drift")
    selections = validate_adjudication_selection(records, selection)
    expected_labels, expected_unresolved = [], []
    for record, chosen in zip(records, selections, strict=True):
        if chosen["selection"] == "grok":
            expected_labels.append(record["grok_label"])
        elif chosen["selection"] == "gemini":
            expected_labels.append(record["gemini_label"])
        else:
            expected_unresolved.append(record)
    expected = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_packet_receipt_v1", "evaluation_cycle_id": CYCLE, "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()), "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()), "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane, "packet_index": index, "disagreement_count": len(records), "adjudicated_count": len(expected_labels), "unresolved_count": len(expected_unresolved),
        "immutable_disagreement_input_sha256": receipt.get("immutable_disagreement_input_sha256"), "selection_sha256": digest(selection_path.read_bytes()),
        "labels_sha256": digest(labels_path.read_bytes()), "unresolved_sha256": digest(unresolved_path.read_bytes()),
        "adjudicator": {"exact_model": MODEL, "model_family": FAMILY, "harness": HARNESS}, "attempt_count": receipt.get("attempt_count"), "candidate_only": True, "text_free": True,
    }
    permitted_input_hashes = {digest(canonical({"records": records})), digest(_selector_envelope(records))}
    if (
        labels["labels"] != expected_labels or unresolved["records"] != expected_unresolved
        or receipt.get("immutable_disagreement_input_sha256") not in permitted_input_hashes
        or not isinstance(receipt.get("attempt_count"), int) or not 0 <= receipt["attempt_count"] <= MAX_STRUCTURAL_ATTEMPTS
        or set(receipt) != set(expected) | {"receipt_sha256"} or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(canonical(expected))
    ):
        raise Error("label_count_or_envelope_drift")
    return {
        "ok": True,
        "lane": lane,
        "packet_index": index,
        "disagreement_count": len(records),
        "adjudicated_count": len(expected_labels),
        "unresolved_count": len(expected_unresolved),
        "receipt_sha256": receipt["receipt_sha256"],
        "text_free": True,
    }


def adjudicate_all(
    package: Path,
    selections_by_packet: dict[tuple[str, int], dict[str, Any]] | None = None,
    *,
    provider: Path = AGY,
    expected_agy_sha256: str | None = None,
    synthetic_provider: bool = False,
) -> dict[str, Any]:
    """Resume frozen lane/order; direct overrides remain synthetic-fixture-only."""
    if selections_by_packet is not None and not synthetic_provider:
        raise Error("mode_drift")
    receipts: list[dict[str, Any]] = []
    unresolved_records: list[dict[str, Any]] = []
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            if (package / OUTPUT / "provider-stop.json").exists():
                raise Error("binding_failure")
            receipt = adjudicate_packet(
                package,
                lane,
                index,
                selections_override=selections_by_packet.get((lane, index)) if selections_by_packet else None,
                provider=provider,
                expected_agy_sha256=expected_agy_sha256,
                synthetic_provider=synthetic_provider,
            )
            receipts.append(receipt)
            unresolved = read(package / OUTPUT / "final" / lane / f"unresolved-{index:04d}.json")
            if not isinstance(unresolved, dict) or set(unresolved) != {"records"} or not isinstance(unresolved["records"], list):
                raise Error("label_count_or_envelope_drift")
            unresolved_records.extend(unresolved["records"])
    out_root = package / OUTPUT
    _private_directory(package, out_root)
    if unresolved_records:
        request = {
            "schema_version": "phase3_cycle007_operator_resolution_request_v1",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
            "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
            "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
            "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
            "unresolved_count": len(unresolved_records),
            "unresolved_records": unresolved_records,
            "text_free": False,
        }
        request["request_sha256"] = digest(canonical(request))
        atomic(out_root / "operator-resolution-request.json", request)
    batch = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_batch_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "packet_count": len(receipts),
        "total_disagreements": sum(value["disagreement_count"] for value in receipts),
        "total_adjudicated": sum(value["adjudicated_count"] for value in receipts),
        "total_unresolved": len(unresolved_records),
        "adjudicator": {"exact_model": MODEL, "model_family": FAMILY, "harness": HARNESS},
        "packet_receipt_union_sha256": digest(canonical([value["receipt_sha256"] for value in receipts])),
        "text_free": True,
    }
    batch["receipt_sha256"] = digest(canonical(batch))
    atomic(out_root / "batch-receipt.json", batch)
    return batch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--lane", choices=tuple(LANES))
    parser.add_argument("--packet-index", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--test-provider-bin", type=Path, help="explicit synthetic fixture transport only")
    parser.add_argument("--expected-agy-executable-sha", help="required exact AGY hash for a real selector call")
    args = parser.parse_args(argv)
    try:
        if args.all == (args.lane is not None or args.packet_index is not None) or (args.lane is None) != (args.packet_index is None):
            raise Error("mode_drift")
        synthetic_provider = args.test_provider_bin is not None
        if args.all:
            result = adjudicate_all(args.package, provider=args.test_provider_bin or AGY, expected_agy_sha256=args.expected_agy_executable_sha, synthetic_provider=synthetic_provider)
        else:
            result = adjudicate_packet(args.package, args.lane, args.packet_index, provider=args.test_provider_bin or AGY, expected_agy_sha256=args.expected_agy_executable_sha, synthetic_provider=synthetic_provider)
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "stream_json_invalid", "text_free": True}
    else:
        result = {"ok": True, **result}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
