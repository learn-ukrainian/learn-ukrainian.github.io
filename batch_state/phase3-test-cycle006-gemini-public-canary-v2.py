#!/usr/bin/env python3
"""Run the public exact-20-position Cycle-006 Gemini transport canary.

Default mode invokes AGY against public synthetic rows. ``--static`` is a
no-provider schema proof and ``--test-provider-bin`` is the synthetic fixture
mode used by local behavior tests; neither accesses a private package.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PUBLIC_POSITIONS = 20
PUBLIC_CANARY_PROMPT = """# Phase 3 Cycle 006 held-out clean-modern label review

This is a public synthetic transport canary, not a private packet. Return only the schema-constrained result for the
ordinal public rows appended below. Preserve every `unit_id` and `unit_sha256` exactly. For each row choose a valid
clean-label decision: `agree` requires `clean_modern_standard_prose: true` and a valid modern genre; every reject
requires `clean_modern_standard_prose: false` and `modern_genre_id: null`.

## Cycle 006 ordinal response contract

For a chunk containing N rows, return exactly one JSON object with the top-level key `labels_by_position`. Its keys are
exactly `p01` through `pNN`; each value copies that ordinal row's `unit_id` and `unit_sha256` unchanged.
"""


def load() -> Any:
    spec = importlib.util.spec_from_file_location(
        "cycle006_public_canary_runner", HERE / "phase3-run-cycle006-gemini-label-provider-batch-v2.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUN = load()


def records() -> list[dict[str, str]]:
    return [
        {"unit_id": f"public-canary-{position:02d}", "unit_sha256": f"{position:064x}", "family_id": "public_canary"}
        for position in range(1, PUBLIC_POSITIONS + 1)
    ]


def response(rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "labels_by_position": {
            f"p{position:02d}": {
                "unit_id": row["unit_id"],
                "unit_sha256": row["unit_sha256"],
                "decision_code": "agree",
                "clean_modern_standard_prose": True,
                "modern_genre_id": "scientific_expository",
            }
            for position, row in enumerate(rows, 1)
        }
    }


def frozen_public_prompt() -> bytes:
    return PUBLIC_CANARY_PROMPT.encode("utf-8")


def canary_schema(rows: list[dict[str, str]], challenge: str) -> dict[str, Any]:
    value = RUN.schema("clean_label", rows)
    value["required"].append("liveness_challenge")
    value["properties"]["liveness_challenge"] = {"enum": [challenge]}
    return value


def normalize_canary(part: dict[str, Any], value: dict[str, Any], challenge: str) -> dict[str, Any]:
    if set(value) != {"labels_by_position", "liveness_challenge"} or value.get("liveness_challenge") != challenge:
        raise RUN.Error("structured_output_envelope_drift", structural=True)
    return RUN.normalize("clean_label", part, {"labels_by_position": value["labels_by_position"]})


def static_verify() -> dict[str, Any]:
    source_rows = records()
    assert len(source_rows) == PUBLIC_POSITIONS == RUN.CHUNK_SIZE
    part = {"chunk_index": 1, "chunk_count": 1, "rows": source_rows}
    contract = RUN.schema("clean_label", source_rows)
    positions = contract["properties"]["labels_by_position"]
    assert positions["required"] == [f"p{position:02d}" for position in range(1, PUBLIC_POSITIONS + 1)]
    assert positions["additionalProperties"] is False
    for position, row in enumerate(source_rows, 1):
        properties = positions["properties"][f"p{position:02d}"]["properties"]
        assert properties["unit_id"] == {"enum": [row["unit_id"]]}
        assert properties["unit_sha256"] == {"enum": [row["unit_sha256"]]}
    normalized = RUN.normalize("clean_label", part, response(source_rows))
    assert normalized == {"labels": list(response(source_rows)["labels_by_position"].values())}
    return receipt("static", 0)


def agy_executable_sha256(provider: Path) -> str:
    """Hash the resolved executable file that the real canary actually invoked."""
    try:
        resolved = provider.resolve(strict=True)
    except OSError as exc:
        raise RUN.Error("structured_output_envelope_drift", structural=True) from exc
    if not resolved.is_file():
        raise RUN.Error("structured_output_envelope_drift", structural=True)
    return RUN.digest(resolved.read_bytes())


def stream_provenance(raw: bytes, provider: Path, challenge: str) -> dict[str, str]:
    """Build real-provider evidence from documented AGY init/result fields and executable identity."""
    init, result = RUN._agy_stream(raw)
    model, status = init["init"]["model"], result["status"]
    init_id, result_id = init.get("conversation_id"), result.get("conversation_id")
    output = result.get("structured_output")
    if (
        model != RUN.MODEL
        or status != "SUCCESS"
        or not isinstance(init_id, str)
        or not init_id
        or init_id != result_id
        or not isinstance(output, dict)
        or output.get("liveness_challenge") != challenge
    ):
        raise RUN.Error("structured_output_envelope_drift", structural=True)
    return {
        "agy_executable_sha256": agy_executable_sha256(provider),
        "init_model": model,
        "result_status": status,
        "init_conversation_id": init_id,
        "result_conversation_id": result_id,
        "challenge_sha256": RUN.digest(challenge.encode()),
        "raw_stream_sha256": RUN.digest(raw),
    }


def receipt(execution_mode: str, provider_calls: int, provenance: dict[str, str] | None = None) -> dict[str, Any]:
    """Build a text-free canary receipt; only validated real AGY events attest provider use."""
    real = execution_mode == "real"
    if execution_mode not in {"static", "synthetic", "real"} or (real != (provenance is not None)):
        raise RUN.Error("structured_output_envelope_drift", structural=True)
    value: dict[str, Any] = {
        "schema_version": "phase3_cycle006_gemini_public_canary_receipt_v2",
        "evaluation_cycle_id": RUN.CYCLE,
        "ok": True,
        "execution_mode": execution_mode,
        "public_position_count": PUBLIC_POSITIONS,
        "provider_calls": provider_calls,
        "exact_model": RUN.MODEL,
        "harness": RUN.HARNESS,
        "real_provider_attested": real,
        "provenance_basis": provenance,
        "text_free": True,
    }
    value["receipt_sha256"] = RUN.digest(RUN.canonical(value))
    return value


def invoke(provider: Path, *, execution_mode: str, receipt_path: Path | None) -> dict[str, Any]:
    source_rows = records()
    part = {"chunk_index": 1, "chunk_count": 1, "rows": source_rows}
    runtime = Path(tempfile.mkdtemp(prefix=".cycle006-public-canary-"))
    os.chmod(runtime, 0o700)
    try:
        stdin_path, raw_path, schema_path, log_path = (
            runtime / "prompt.stdin",
            runtime / "provider.raw",
            runtime / "response-schema.json",
            runtime / "agy.log",
        )
        challenge = secrets.token_hex(32)
        prompt = RUN.compose_prompt(
            frozen_public_prompt()
            + f"\nEcho this exact liveness challenge in liveness_challenge: {challenge}\n".encode(),
            "clean_label",
            part,
        )
        RUN._atomic(stdin_path, RUN.stdin_event(prompt), raw=True)
        RUN._atomic(schema_path, canary_schema(source_rows, challenge))
        RUN._atomic(log_path, b"", raw=True)
        with stdin_path.open("rb") as stdin, raw_path.open("xb") as stdout:
            os.chmod(raw_path, 0o600)
            completed = subprocess.run(
                RUN._command(provider, schema_path, log_path),
                stdin=stdin,
                stdout=stdout,
                stderr=subprocess.DEVNULL,
                check=False,
                shell=False,
            )
        if completed.returncode:
            raise RUN.Error("structured_output_envelope_drift")
        raw = raw_path.read_bytes()
        normalize_canary(part, RUN._extract(raw), challenge)
        provenance = stream_provenance(raw, provider, challenge) if execution_mode == "real" else None
        if execution_mode == "real":
            if receipt_path is None:
                raise RUN.Error("structured_output_envelope_drift", structural=True)
            RUN._atomic(receipt_path.with_suffix(receipt_path.suffix + ".raw"), raw, raw=True)
        return receipt(execution_mode, 1, provenance)
    finally:
        shutil.rmtree(runtime, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", action="store_true", help="validate public shape only; no provider invocation")
    parser.add_argument("--test-provider-bin", type=Path, help="synthetic provider fixture; real mode omits this")
    parser.add_argument("--receipt", type=Path, help="0600 canary receipt; required for a real provider attestation")
    args = parser.parse_args()
    try:
        if args.static:
            if args.test_provider_bin:
                raise RUN.Error("ordinal_identity_binding_drift")
            result = static_verify()
            if args.receipt:
                RUN._atomic(args.receipt, result)
        elif args.test_provider_bin:
            result = invoke(args.test_provider_bin, execution_mode="synthetic", receipt_path=args.receipt)
            if args.receipt:
                RUN._atomic(args.receipt, result)
        else:
            if args.receipt is None:
                raise RUN.Error("structured_output_envelope_drift")
            result = invoke(RUN.AGY, execution_mode="real", receipt_path=args.receipt)
            RUN._atomic(args.receipt, result)
    except RUN.Error as exc:
        result = {"ok": False, "failure_code": exc.code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "structured_output_envelope_drift", "text_free": True}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
