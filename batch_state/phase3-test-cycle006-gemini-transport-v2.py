#!/usr/bin/env python3
"""Synthetic-only proof for the Cycle-006 stdin-only Gemini transport."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def load() -> Any:
    spec = importlib.util.spec_from_file_location(
        "cycle006_gemini_transport", HERE / "phase3-run-cycle006-gemini-label-provider-batch-v2.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUN = load()


def load_canary() -> Any:
    spec = importlib.util.spec_from_file_location(
        "cycle006_gemini_public_canary", HERE / "phase3-test-cycle006-gemini-public-canary-v2.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CANARY = load_canary()
EXPECTED_CODES = {
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


def put(path: Path, value: Any) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    data = RUN.canonical(value)
    path.write_bytes(data)
    os.chmod(path, 0o600)
    return data


def put_raw(path: Path, value: bytes) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    path.write_bytes(value)
    os.chmod(path, 0o600)
    return value


def rows(count: int, lane: str = "clean_label") -> list[dict[str, Any]]:
    return [
        {
            "unit_id": f"synthetic-private-{lane}-{position:02d}",
            "unit_sha256": f"{position:064x}",
            "family_id": "pravopys_2026_complete",
        }
        for position in range(1, count + 1)
    ]


def synthetic_prompt(lane: str, provider: str) -> bytes:
    title = (
        "Phase 3 Cycle 006 held-out clean-modern label review"
        if lane == "clean_label"
        else "Phase 3 Cycle 006 held-out residual label review"
    )
    text = f"# {title}\n\nSynthetic {provider} {lane} fixture.\n"
    if provider == "gemini":
        text += "\n\n## Cycle 006 ordinal response contract\n\nReturn exactly `labels_by_position` with keys p01 through pNN.\n"
    return text.encode()


def make_package(root: Path, *, lane: str = "clean_label", index: int = 1, count: int = 50) -> Path:
    package = root / "package"
    package.mkdir(parents=True, mode=0o700)
    os.chmod(package, 0o700)
    prompt_hashes: dict[str, str] = {}
    prompt_bindings = []
    for lane_key, provider in sorted((lane_key, provider) for lane_key in RUN.LANES for provider in ("grok", "gemini")):
        filename = f"{provider}-{'clean' if lane_key == 'clean_label' else 'residual'}-label.md"
        relative = f"prompts/{filename}"
        payload = synthetic_prompt(lane_key, provider)
        prompt_hashes[relative] = RUN.digest(put_raw(package / relative, payload))
        prompt_bindings.append(
            {"lane": lane_key, "provider": provider, "path": relative, "sha256": prompt_hashes[relative]}
        )
    custody_value = {"synthetic": True, "prompt_sha256s": prompt_hashes, "prompt_bindings": prompt_bindings}
    custody_value["receipt_sha256"] = RUN.digest(RUN.canonical(custody_value))
    custody = put(package / "custody-receipt.json", custody_value)
    RUN.EXPECTED_CUSTODY_SHA256 = RUN.digest(custody)
    packet_rows = rows(count, lane)
    body = {
        "schema_version": "phase3_cycle006_private_packet_v1",
        "evaluation_cycle_id": RUN.CYCLE,
        "lane": lane,
        "packet_index": index,
        "row_count": count,
        "rows": packet_rows,
        "packet_identity_set_sha256": RUN.digest(RUN.canonical(sorted(RUN._identity(row) for row in packet_rows))),
    }
    packet_path = package / lane / f"packet-{index:04d}.json"
    packet_data = put(packet_path, body)
    entry = {
        "lane": lane,
        "packet_index": index,
        "canonical_basename": packet_path.name,
        "row_count": count,
        "raw_sha256": RUN.digest(packet_data),
        "packet_identity_set_sha256": body["packet_identity_set_sha256"],
    }
    manifest = {
        "schema_version": "phase3_cycle006_label_manifest_v2",
        "evaluation_cycle_id": RUN.CYCLE,
        "custody_receipt_raw_sha256": RUN.EXPECTED_CUSTODY_SHA256,
        "packets": [entry],
        "prompt_sha256s": prompt_hashes,
        "prompt_bindings": prompt_bindings,
    }
    manifest["receipt_sha256"] = RUN.digest(RUN.canonical(manifest))
    manifest_bytes = put(package / "label-manifest.json", manifest)
    RUN.EXPECTED_LABEL_MANIFEST_SHA256 = RUN.digest(manifest_bytes)
    return package


FAKE = r"""#!/usr/bin/env python3
import json, os, pathlib, re, sys
argv = sys.argv
pathlib.Path(os.environ["FAKE_ARGV"]).write_text(json.dumps(argv))
log = pathlib.Path(argv[argv.index("--log-file") + 1])
assert log.stat().st_mode & 0o777 == 0o600
event = json.loads(sys.stdin.readline())
assert event["event"] == "user"
prompt = event["message"]["content"][0]["text"]
assert "Phase 3 Cycle 006 held-out clean-modern label review" in prompt
assert "Cycle 006 ordinal response contract" in prompt
rows = json.loads(prompt.split("--- BEGIN IMMUTABLE PRIVATE PACKET JSON ---\n", 1)[1].split("--- END", 1)[0])["rows"]
challenge = re.search(r"liveness_challenge: ([0-9a-f]{64})", prompt)
state = pathlib.Path(os.environ["FAKE_STATE"])
count = int(state.read_text()) if state.exists() else 0
state.write_text(str(count + 1))
mode = os.environ.get("FAKE_MODE", "valid")
if mode == "invalid" or (mode == "retry" and count == 0):
    print("not-json")
    raise SystemExit(0)
if mode == "nonzero":
    print("not-json")
    raise SystemExit(23)
labels = {}
for position, row in enumerate(rows, 1):
    labels[f"p{position:02d}"] = {"unit_id": row["unit_id"], "unit_sha256": row["unit_sha256"], "decision_code": "agree", "clean_modern_standard_prose": True, "modern_genre_id": "scientific_expository"}
if mode == "semantic":
    labels["p01"]["clean_modern_standard_prose"] = False
print(json.dumps({"event": "init", "init": {"model": "Gemini 3.6 Flash (High)"}}))
out = {"labels_by_position": labels}
if challenge: out["liveness_challenge"] = challenge.group(1)
print(json.dumps({"event": "result", "result": {"conversation_id": "synthetic", "status": "SUCCESS", "structured_output": out}}))
"""


def labels_for(part: dict[str, Any], *, lane: str = "clean_label") -> dict[str, Any]:
    output: dict[str, Any] = {}
    for position, row in enumerate(part["rows"], 1):
        if lane == "clean_label":
            value = {
                "unit_id": row["unit_id"],
                "unit_sha256": row["unit_sha256"],
                "decision_code": "agree",
                "clean_modern_standard_prose": True,
                "modern_genre_id": "scientific_expository",
            }
        else:
            value = {
                "unit_id": row["unit_id"],
                "unit_sha256": row["unit_sha256"],
                "phenomena": [
                    {
                        "phenomenon_id": "punctuation",
                        "decision_code": "acceptable_control",
                        "evidence_sufficiency": "sufficient",
                    }
                ],
                "primary_phenomenon_id": "punctuation",
                "item_decision_rollup": "acceptable_control",
            }
        output[f"p{position:02d}"] = value
    return {"labels_by_position": output}


def assert_failure_code_mapping() -> None:
    assert RUN.FAILURE_CODES == EXPECTED_CODES

    def extract_code(raw: bytes) -> str:
        try:
            RUN._extract(raw)
        except RUN.Error as exc:
            return exc.code
        raise AssertionError("invalid stream accepted")

    valid_stream = (
        b'{"event":"init","init":{"model":"Gemini 3.6 Flash (High)"}}\n'
        b'{"event":"result","result":{"status":"SUCCESS","structured_output":{}}}\n'
    )
    assert RUN._extract(valid_stream) == {}
    assert extract_code(b"no-json") == "stream_json_invalid"
    for raw in (
        b'{"type":"result","status":"SUCCESS","structured_output":{}}\n',
        b'{"status":"SUCCESS","structured_output":{}}\n',
        b'{"event":"result","result":{"status":"SUCCESS","structured_output":{}}}\n',
        valid_stream + b'{"event":"init","init":{"model":"Gemini 3.6 Flash (High)"}}\n',
        b'{"event":"init","init":{"model":"Gemini 3.6 Flash (High)"}}\n',
        valid_stream + b'{"event":"result","result":{"status":"SUCCESS","structured_output":{}}}\n',
    ):
        assert extract_code(raw) == "terminal_result_count_drift"
    assert (
        extract_code(
            b'{"event":"init","init":{"model":"Gemini 3.7 Flash (High)"}}\n'
            b'{"event":"result","result":{"status":"SUCCESS","structured_output":{}}}\n'
        )
        == "structured_output_envelope_drift"
    )
    assert (
        extract_code(
            b'{"event":"init","init":{"model":"Gemini 3.6 Flash (High)"}}\n'
            b'{"event":"result","result":{"status":"FAIL","structured_output":{}}}\n'
        )
        == "structured_output_envelope_drift"
    )
    part = {"rows": rows(2), "chunk_index": 1, "chunk_count": 1}
    broken = labels_for(part)
    broken["labels_by_position"].pop("p02")
    try:
        RUN.normalize("clean_label", part, broken)
    except RUN.Error as exc:
        assert exc.code == "ordinal_key_drift"
    else:
        raise AssertionError("ordinal omission accepted")
    broken = labels_for(part)
    broken["labels_by_position"]["p01"]["unit_id"] = "substitution"
    try:
        RUN.normalize("clean_label", part, broken)
    except RUN.Error as exc:
        assert exc.code == "ordinal_identity_binding_drift"
    else:
        raise AssertionError("identity substitution accepted")
    messages = {
        "response envelope drift": "label_count_or_envelope_drift",
        "identity/order drift": "identity_or_order_drift",
        "identity uniqueness drift": "identity_uniqueness_drift",
        "clean schema drift": "clean_label_schema_drift",
        "clean invariant": "clean_label_invariant_drift",
        "residual schema drift": "residual_label_schema_drift",
        "residual phenomenon drift": "residual_phenomenon_drift",
        "scored decision insufficiency": "residual_scored_decision_insufficiency",
        "2019 positive forbidden": "residual_2019_positive_forbidden",
        "taxonomy order/unique drift": "residual_taxonomy_order_or_uniqueness_drift",
        "primary/rollup drift": "residual_primary_or_rollup_drift",
        "null rollup drift": "residual_null_rollup_drift",
    }
    assert {RUN._semantic_failure(RUN.SOURCE.Invalid(message)).code for message in messages} == set(messages.values())


def run_proof() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        provider = root / "fake-provider.py"
        provider.write_text(FAKE)
        provider.chmod(0o700)
        os.environ.update(
            {"FAKE_ARGV": str(root / "argv.json"), "FAKE_STATE": str(root / "state"), "FAKE_MODE": "valid"}
        )
        package = make_package(root)
        completed = subprocess.run(
            [
                sys.executable,
                str(HERE / "phase3-run-cycle006-gemini-label-provider-batch-v2.py"),
                "--package",
                str(package),
                "--lane",
                "clean_label",
                "--packet-index",
                "1",
                "--test-provider-bin",
                str(provider),
                "--expected-custody-sha",
                RUN.EXPECTED_CUSTODY_SHA256,
                "--expected-label-manifest-sha",
                RUN.EXPECTED_LABEL_MANIFEST_SHA256,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.stdout, completed.stderr
        result = json.loads(completed.stdout)
        assert completed.returncode == 0, (completed.stdout, completed.stderr)
        assert result["ok"] and result["row_count"] == 50
        assert [part["chunk_index"] for part in RUN.chunks(RUN.packet(package, "clean_label", 1)[1])] == [1, 2, 3]
        assert [len(part["rows"]) for part in RUN.chunks(RUN.packet(package, "clean_label", 1)[1])] == [20, 20, 10]
        argv = json.loads((root / "argv.json").read_text())
        assert "synthetic-private" not in json.dumps(argv)
        assert "--print" in argv and argv[argv.index("--print") + 1] == "" and "--json-schema" in argv
        assert argv[argv.index("--input-format") + 1] == "stream-json"
        assert argv[argv.index("--output-format") + 1] == "stream-json"
        assert not list(package.glob(".cycle006-gemini-*")), "runtime directory leaked"
        assert stat.S_IMODE((package / RUN.OUTPUT / "clean_label" / "labels-0001.json").stat().st_mode) == 0o600
        assert b"synthetic-private" not in (package / RUN.OUTPUT / "clean_label" / "receipt-0001.json").read_bytes()

        binary_drift_package = make_package(root / "binary-drift")
        (root / "state").unlink(missing_ok=True)
        original_agy = RUN.AGY
        try:
            RUN.AGY = provider
            try:
                RUN.run_packet(
                    binary_drift_package,
                    "clean_label",
                    1,
                    provider,
                    expected_agy_sha256="0" * 64,
                )
            except RUN.Error as exc:
                assert exc.code == "structured_output_envelope_drift"
            else:
                raise AssertionError("AGY executable drift reached a provider call")
        finally:
            RUN.AGY = original_agy
        assert not (root / "state").exists(), "AGY executable drift made a provider call"
        binary_marker = RUN._read_json(
            binary_drift_package / RUN.OUTPUT / "clean_label" / "chunks" / "packet-0001" / "attempt-1-chunk-01.terminal.json"
        )
        assert binary_marker["failure_stage"] == "executable_binding"
        assert binary_marker["provider_call_started"] is False
        assert binary_marker["executable_binding_result"] == "mismatch"
        assert binary_marker["provider_return_code"] == "not_started"

        (root / "state").unlink(missing_ok=True)
        canary = subprocess.run(
            [
                sys.executable,
                str(HERE / "phase3-test-cycle006-gemini-public-canary-v2.py"),
                "--test-provider-bin",
                str(provider),
                "--receipt",
                str(root / "synthetic-canary-receipt.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert canary.returncode == 0, canary.stderr
        canary_result = json.loads(canary.stdout)
        assert canary_result["ok"] is True
        assert canary_result["execution_mode"] == "synthetic"
        assert canary_result["real_provider_attested"] is False
        assert canary_result["harness"] == "agy" and canary_result["provenance_basis"] is None
        synthetic_receipt = root / "synthetic-canary-receipt.json"
        assert json.loads(synthetic_receipt.read_text()) == canary_result
        assert stat.S_IMODE(synthetic_receipt.stat().st_mode) == 0o600
        for raw in (
            b'{"event":"init","init":{}}\n{"event":"result","result":{"status":"SUCCESS","structured_output":{}}}\n',
            (
                b'{"event":"init","init":{"model":"Gemini 3.7 Flash (High)"}}\n'
                b'{"event":"result","result":{"status":"SUCCESS","structured_output":{}}}\n'
            ),
        ):
            try:
                CANARY.stream_provenance(raw, RUN.AGY, "a" * 64)
            except CANARY.RUN.Error as exc:
                assert exc.code == "structured_output_envelope_drift"
            else:
                raise AssertionError("missing or mismatched AGY terminal provenance was accepted")

        batch_package = make_package(root / "batch")
        batch_cli = subprocess.run(
            [
                sys.executable,
                str(HERE / "phase3-run-cycle006-gemini-label-provider-batch-v2.py"),
                "--package",
                str(batch_package),
                "--lane",
                "clean_label",
                "--start",
                "1",
                "--end",
                "1",
                "--concurrency",
                "1",
                "--test-provider-bin",
                str(provider),
                "--expected-custody-sha",
                RUN.EXPECTED_CUSTODY_SHA256,
                "--expected-label-manifest-sha",
                RUN.EXPECTED_LABEL_MANIFEST_SHA256,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert batch_cli.returncode == 0, batch_cli.stderr
        assert json.loads(batch_cli.stdout)["packet_count"] == 1

        retry_package = make_package(root / "retry")
        os.environ["FAKE_MODE"] = "retry"
        (root / "state").unlink(missing_ok=True)
        retry = RUN.run_packet(retry_package, "clean_label", 1, provider)
        assert retry["ok"] and json.loads((root / "state").read_text()) == 4
        assert (
            retry_package / RUN.OUTPUT / "clean_label" / "chunks" / "packet-0001" / "attempt-1-chunk-01.terminal.json"
        ).exists()

        structural_package = make_package(root / "structural")
        os.environ["FAKE_MODE"] = "invalid"
        (root / "state").unlink(missing_ok=True)
        try:
            RUN.run_packet(structural_package, "clean_label", 1, provider)
        except RUN.Error as exc:
            assert exc.code == "stream_json_invalid"
        else:
            raise AssertionError("persistent structural invalid response was accepted")
        assert json.loads((root / "state").read_text()) == 2
        structural_dir = structural_package / RUN.OUTPUT / "clean_label" / "chunks" / "packet-0001"
        for attempt in (1, 2):
            terminal = RUN._read_json(structural_dir / f"attempt-{attempt}-chunk-01.terminal.json")
            assert terminal["state"] == "terminal" and terminal["failure_code"] == "stream_json_invalid"
            assert terminal["failure_stage"] == "stream_parse"
            assert terminal["provider_call_started"] is True and terminal["provider_return_code"] == "zero"
            assert terminal["init_count"] == 0 and terminal["result_count"] == 0
            assert terminal["raw_byte_count"] > 0 and len(terminal["raw_sha256"]) == len(terminal["log_sha256"]) == 64
            assert terminal["first_event_kind"] == terminal["last_event_kind"] == "empty"
            assert terminal["model_binding_result"] == terminal["result_status"] == terminal["structured_output_type"] == "not_inspected"
            assert b"not-json" not in RUN.canonical(terminal)
        assert not list(structural_dir.glob("attempt-3-*"))
        stop_path = structural_package / RUN.OUTPUT / "provider-stop.json"
        stop_before = stop_path.read_bytes()
        assert stat.S_IMODE(stop_path.stat().st_mode) == 0o600
        RUN.stop(structural_package, "clean_label", 1, "stream_json_invalid")
        assert stop_path.read_bytes() == stop_before
        try:
            RUN.run_packet(structural_package, "clean_label", 1, provider)
        except RUN.Error as exc:
            assert exc.code == "ordinal_identity_binding_drift"
        else:
            raise AssertionError("provider-stop allowed a resumed provider call")
        assert json.loads((root / "state").read_text()) == 2

        semantic_package = make_package(root / "semantic")
        os.environ["FAKE_MODE"] = "semantic"
        (root / "state").unlink(missing_ok=True)
        try:
            RUN.run_packet(semantic_package, "clean_label", 1, provider)
        except RUN.Error as exc:
            assert exc.code == "clean_label_invariant_drift"
        else:
            raise AssertionError("semantic failure retried or accepted")
        assert json.loads((root / "state").read_text()) == 1
        stop = RUN._read_json(semantic_package / RUN.OUTPUT / "provider-stop.json")
        assert stop["failure_code"] == "clean_label_invariant_drift" and stop["text_free"] is True
        assert stop["failure_stage"] == "result_validation" and stop["provider_call_started"] is True
        RUN.stop(semantic_package, "clean_label", 1, "clean_label_invariant_drift")

        nonzero_package = make_package(root / "nonzero")
        os.environ["FAKE_MODE"] = "nonzero"
        (root / "state").unlink(missing_ok=True)
        try:
            RUN.run_packet(nonzero_package, "clean_label", 1, provider)
        except RUN.Error as exc:
            assert exc.code == "structured_output_envelope_drift"
        else:
            raise AssertionError("nonzero provider return was accepted")
        nonzero = RUN._read_json(
            nonzero_package / RUN.OUTPUT / "clean_label" / "chunks" / "packet-0001" / "attempt-1-chunk-01.terminal.json"
        )
        assert nonzero["failure_stage"] == "provider_return"
        assert nonzero["provider_call_started"] is True and nonzero["provider_return_code"] == "nonzero"
        assert json.loads((root / "state").read_text()) == 1, "nonzero return must not authorize retry"

        partial_package = make_package(root / "partial")
        partial = partial_package / RUN.OUTPUT / "clean_label" / "labels-0001.json"
        put(partial, {"labels": []})
        try:
            RUN.run_packet(partial_package, "clean_label", 1, provider)
        except RUN.Error:
            pass
        else:
            raise AssertionError("partial packet seal accepted")
        assert (partial_package / RUN.OUTPUT / "provider-stop.json").exists()
        partial_stop = RUN._read_json(partial_package / RUN.OUTPUT / "provider-stop.json")
        assert partial_stop["failure_stage"] == "package_binding"
        assert partial_stop["provider_call_started"] is False
        assert partial_stop["provider_return_code"] == "not_started"

        for code in sorted(EXPECTED_CODES):
            isolated = make_package(root / code)
            RUN.stop(isolated, "clean_label", 1, code)
            marker = RUN._read_json(isolated / RUN.OUTPUT / "provider-stop.json")
            assert marker["failure_code"] == code and marker["text_free"] is True


def main() -> None:
    assert_failure_code_mapping()
    run_proof()
    print('{"ok":true,"synthetic_only":true,"provider_calls":0,"text_free":true}')


if __name__ == "__main__":
    main()
