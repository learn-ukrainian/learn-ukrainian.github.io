#!/usr/bin/env python3
"""Tests for the Cycle 007 public canary runner and receipt generator."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler


def _load_canary_runner() -> Any:
    path = ROOT / "batch_state" / "phase3-run-cycle007-public-canaries-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_public_canaries", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CANARY = _load_canary_runner()


def _build_mock_labels(sidecar: dict[str, Any], *, trap_agreed: bool = False, shadow_only: bool = False, antonenko_only: bool = False, control_rejected: bool = False, control_missing_evidence: bool = False) -> list[dict[str, Any]]:
    rows = CANARY.fixture_rows()
    trap_ev = sidecar["rows"][0]["evidence"]
    trap_antonenko = next(e["evidence_id"] for e in trap_ev if e["channel"] == "antonenko_style" and e["status"] == "attested")
    trap_shadow = next(e["evidence_id"] for e in trap_ev if e["channel"] == "russian_shadow_suspicion" and e["status"] == "attested")

    ctrl_ev = sidecar["rows"][1]["evidence"]
    ctrl_vesum = next(e["evidence_id"] for e in ctrl_ev if e["channel"] == "vesum_attestation" and e["status"] == "attested")
    ctrl_heritage = next(e["evidence_id"] for e in ctrl_ev if e["channel"] == "heritage_attestation" and e["status"] == "attested")
    ctrl_meta = next(e["evidence_id"] for e in ctrl_ev if e["channel"] == "source_metadata")

    if shadow_only:
        trap_eids = [trap_shadow]
    elif antonenko_only:
        trap_eids = [trap_antonenko]
    else:
        trap_eids = sorted([trap_antonenko, trap_shadow])

    if trap_agreed:
        trap_label = {
            "unit_id": rows[0]["unit_id"],
            "unit_sha256": rows[0]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "scientific_expository",
            "evidence_ids": trap_eids,
        }
    else:
        trap_label = {
            "unit_id": rows[0]["unit_id"],
            "unit_sha256": rows[0]["unit_sha256"],
            "decision_code": "reject_insufficient_locator_evidence",
            "clean_modern_standard_prose": False,
            "modern_genre_id": None,
            "evidence_ids": trap_eids,
        }

    if control_rejected:
        control_label = {
            "unit_id": rows[1]["unit_id"],
            "unit_sha256": rows[1]["unit_sha256"],
            "decision_code": "reject_insufficient_locator_evidence",
            "clean_modern_standard_prose": False,
            "modern_genre_id": None,
            "evidence_ids": sorted([ctrl_vesum, ctrl_heritage]),
        }
    elif control_missing_evidence:
        control_label = {
            "unit_id": rows[1]["unit_id"],
            "unit_sha256": rows[1]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "scientific_expository",
            "evidence_ids": [ctrl_meta],
        }
    else:
        control_label = {
            "unit_id": rows[1]["unit_id"],
            "unit_sha256": rows[1]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "scientific_expository",
            "evidence_ids": sorted([ctrl_vesum, ctrl_heritage]),
        }

    return [trap_label, control_label]


def test_fixture_structure() -> None:
    rows = CANARY.fixture_rows()
    assert len(rows) == 2
    assert rows[0]["source_text"] == "слідуючий раз"
    assert rows[0]["unit_id"] == f"{CANARY.DOMAIN}-trap"
    assert rows[0]["family_id"] == CANARY.DOMAIN
    assert len(rows[0]["unit_sha256"]) == 64

    assert rows[1]["source_text"] == "філіжанка"
    assert rows[1]["unit_id"] == f"{CANARY.DOMAIN}-control"
    assert rows[1]["family_id"] == CANARY.DOMAIN
    assert len(rows[1]["unit_sha256"]) == 64


def test_compile_public_sidecar_with_synthetic_mcp(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    client.close()

    assert sidecar["schema_version"] == compiler.SIDECAR_SCHEMA_VERSION
    assert sidecar["row_count"] == 2
    assert sidecar["lane"] == "clean_label"

    trap_ev = sidecar["rows"][0]["evidence"]
    antonenko = [e for e in trap_ev if e["channel"] == "antonenko_style" and e["status"] == "attested"]
    shadow = [e for e in trap_ev if e["channel"] == "russian_shadow_suspicion" and e["status"] == "attested"]
    heritage_trap = [e for e in trap_ev if e["channel"] == "heritage_attestation" and e["status"] == "attested"]

    assert len(antonenko) >= 1
    assert len(shadow) >= 1
    assert len(heritage_trap) == 0

    ctrl_ev = sidecar["rows"][1]["evidence"]
    vesum_ctrl = [e for e in ctrl_ev if e["channel"] == "vesum_attestation" and e["status"] == "attested"]
    heritage_ctrl = [e for e in ctrl_ev if e["channel"] == "heritage_attestation" and e["status"] == "attested"]
    shadow_ctrl = [e for e in ctrl_ev if e["channel"] == "russian_shadow_suspicion" and e["status"] == "attested"]
    style_ctrl = [e for e in ctrl_ev if e["channel"] == "antonenko_style" and e["status"] == "attested"]

    assert len(vesum_ctrl) >= 1
    assert len(heritage_ctrl) >= 1
    assert len(shadow_ctrl) == 0
    assert len(style_ctrl) == 0


def test_semantic_canary_assertions_pass_valid(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    client.close()

    labels = _build_mock_labels(sidecar)
    validated = CANARY.SOURCE.validate("clean_label", {"rows": CANARY.fixture_rows()}, CANARY.canonical({"labels": labels}), sidecar=sidecar)
    assert len(validated["labels"]) == 2
    passed, preserved = CANARY.verify_semantic_canary_assertions(sidecar, labels)
    assert passed is True
    assert preserved is True


def test_gemini_prompt_contains_public_rows_and_compiled_evidence(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    rows = CANARY.fixture_rows()
    sidecar = CANARY.compile_public_sidecar(client, rows)
    client.close()

    prompt = CANARY.gemini_prompt("a" * 64, rows, sidecar).decode("utf-8")
    assert "слідуючий раз" in prompt
    assert "філіжанка" in prompt
    assert sidecar["sidecar_id"] in prompt
    for row in sidecar["rows"]:
        assert all(evidence["evidence_id"] in prompt for evidence in row["evidence"])


def test_semantic_canary_assertions_reject_trap_agreed(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    client.close()

    labels = _build_mock_labels(sidecar, trap_agreed=True)
    with pytest.raises(CANARY.CanarySemanticError):
        CANARY.verify_semantic_canary_assertions(sidecar, labels)


def test_semantic_canary_assertions_reject_russian_shadow_only(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    client.close()

    labels = _build_mock_labels(sidecar, shadow_only=True)
    with pytest.raises(CANARY.CanarySemanticError, match="russian_shadow_suspicion_alone_insufficient"):
        CANARY.verify_semantic_canary_assertions(sidecar, labels)


def test_semantic_canary_assertions_reject_antonenko_only(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    client.close()

    labels = _build_mock_labels(sidecar, antonenko_only=True)
    with pytest.raises(CANARY.CanarySemanticError, match="trap_missing_required_antonenko_or_shadow_evidence"):
        CANARY.verify_semantic_canary_assertions(sidecar, labels)


def test_semantic_canary_assertions_reject_heritage_control_rejected(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    client.close()

    labels = _build_mock_labels(sidecar, control_rejected=True)
    with pytest.raises(CANARY.CanarySemanticError, match="heritage_control_not_agreed"):
        CANARY.verify_semantic_canary_assertions(sidecar, labels)


def test_semantic_canary_assertions_reject_heritage_control_missing_evidence(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    client.close()

    labels = _build_mock_labels(sidecar, control_missing_evidence=True)
    with pytest.raises(CANARY.SOURCE.Invalid):
        CANARY.SOURCE.validate("clean_label", {"rows": CANARY.fixture_rows()}, CANARY.canonical({"labels": labels}), sidecar=sidecar)


def test_semantic_canary_assertions_require_both_vesum_and_heritage(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    client.close()
    labels = _build_mock_labels(sidecar)
    control_evidence = {item["evidence_id"]: item for item in sidecar["rows"][1]["evidence"]}
    labels[1]["evidence_ids"] = [
        evidence_id
        for evidence_id in labels[1]["evidence_ids"]
        if control_evidence[evidence_id]["channel"] == "vesum_attestation"
    ]

    with pytest.raises(CANARY.CanarySemanticError, match="heritage_control_missing_vesum_or_heritage_evidence"):
        CANARY.verify_semantic_canary_assertions(sidecar, labels)


def test_semantic_canary_assertions_reject_control_style_warning(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    client.close()
    labels = _build_mock_labels(sidecar)
    warning = next(item for item in sidecar["rows"][1]["evidence"] if item["channel"] == "antonenko_style")
    warning["status"] = "attested"

    with pytest.raises(CANARY.CanarySemanticError, match="heritage_control_has_style_or_shadow_warning"):
        CANARY.verify_semantic_canary_assertions(sidecar, labels)


def _make_gemini_fake_provider(tmp_path: Path, sidecar: dict[str, Any]) -> Path:
    labels = _build_mock_labels(sidecar)
    script = tmp_path / "mock_gemini.py"
    labels_json = json.dumps(labels)
    code = f"""#!/usr/bin/env python3
import sys, json

schema_idx = sys.argv.index("--json-schema")
schema_path = sys.argv[schema_idx + 1]
with open(schema_path) as f:
    schema = json.load(f)
challenge = schema["properties"]["liveness_challenge"]["enum"][0]

labels = json.loads({json.dumps(labels_json)})
labels_by_pos = {{
    "p01": labels[0],
    "p02": labels[1],
}}

structured_output = {{
    "labels_by_position": labels_by_pos,
    "liveness_challenge": challenge,
}}

events = [
    {{"event": "init", "init": {{"model": "Gemini 3.6 Flash (High)"}}, "conversation_id": "mock-conv-1"}},
    {{"event": "result", "result": {{"status": "SUCCESS", "structured_output": structured_output}}, "conversation_id": "mock-conv-1"}},
]

for ev in events:
    print(json.dumps(ev))
"""
    script.write_text(code)
    script.chmod(0o755)
    return script


def _make_grok_fake_provider(tmp_path: Path, sidecar: dict[str, Any]) -> Path:
    labels = _build_mock_labels(sidecar)
    script = tmp_path / "mock_grok.py"
    labels_json = json.dumps(labels)
    code = f"""#!/usr/bin/env python3
import sys, json, re

prompt = sys.stdin.read()
m = re.search(r"Echo this exact liveness challenge in liveness_challenge: ([0-9a-f]+)", prompt)
challenge = m.group(1) if m else "mock-challenge"

labels = json.loads({json.dumps(labels_json)})
output = {{
    "labels": labels,
    "liveness_challenge": challenge,
}}
print(json.dumps(output))
"""
    script.write_text(code)
    script.chmod(0o755)
    return script


def test_synthetic_gemini_canary_invocation(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    mock_bin = _make_gemini_fake_provider(tmp_path, sidecar)
    receipt_path = tmp_path / "gemini-canary-receipt.json"

    receipt = CANARY.invoke_canary(
        "gemini",
        mock_bin,
        execution_mode="synthetic",
        receipt_path=receipt_path,
        sources_client=client,
    )
    client.close()

    assert receipt["ok"] is True
    assert receipt["schema_version"] == "phase3_cycle007_gemini_public_canary_receipt_v1"
    assert receipt["execution_mode"] == "synthetic"
    assert receipt["exact_model"] == "Gemini 3.6 Flash (High)"
    assert receipt["model_family"] == "google"
    assert receipt["harness"] == "agy"
    assert receipt["provider_call_count"] == 1
    assert receipt["sources_mcp_used"] is True
    assert receipt["valid_evidence_ids"] is True
    assert receipt["russian_surzhyk_trap_rejected"] is True
    assert receipt["heritage_control_preserved"] is True
    assert receipt["provenance_basis"]["init_model"] == "Gemini 3.6 Flash (High)"
    assert receipt["provenance_basis"]["result_status"] == "SUCCESS"

    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    assert receipt["receipt_sha256"] == CANARY.digest(CANARY.canonical(unsigned))
    assert receipt_path.exists()


def test_synthetic_grok_canary_invocation(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    mock_bin = _make_grok_fake_provider(tmp_path, sidecar)
    receipt_path = tmp_path / "grok-canary-receipt.json"

    receipt = CANARY.invoke_canary(
        "grok",
        mock_bin,
        execution_mode="synthetic",
        receipt_path=receipt_path,
        sources_client=client,
    )
    client.close()

    assert receipt["ok"] is True
    assert receipt["schema_version"] == "phase3_cycle007_grok_public_canary_receipt_v1"
    assert receipt["execution_mode"] == "synthetic"
    assert receipt["exact_model"] == "grok-4.5"
    assert receipt["model_family"] == "xai"
    assert receipt["harness"] == "native_grok"
    assert receipt["provider_call_count"] == 1
    assert receipt["sources_mcp_used"] is True
    assert receipt["valid_evidence_ids"] is True
    assert receipt["russian_surzhyk_trap_rejected"] is True
    assert receipt["heritage_control_preserved"] is True

    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    assert receipt["receipt_sha256"] == CANARY.digest(CANARY.canonical(unsigned))
    assert receipt_path.exists()


def test_synthetic_provider_incapable_of_minting_real_receipt(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    mock_bin = _make_gemini_fake_provider(tmp_path, sidecar)
    receipt_path = tmp_path / "receipt.json"

    with pytest.raises(
        CANARY.CanaryError,
        match=r"provider_executable_mismatch|invalid_executable|real_mode_prohibits_injected_sources_client",
    ):
        CANARY.invoke_canary(
            "gemini",
            mock_bin,
            execution_mode="real",
            receipt_path=receipt_path,
            sources_client=client,
        )
    client.close()


def test_real_mode_rejects_injected_synthetic_sources_client(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    with pytest.raises(CANARY.CanaryError, match="real_mode_prohibits_injected_sources_client"):
        CANARY.invoke_canary(
            "gemini",
            CANARY.AGY,
            execution_mode="real",
            receipt_path=tmp_path / "receipt.json",
            sources_client=client,
        )
    client.close()


def test_real_mode_rejects_noncanonical_sources_endpoint(tmp_path: Path) -> None:
    with pytest.raises(CANARY.CanaryError, match="real_mode_sources_endpoint_drift"):
        CANARY.invoke_canary(
            "gemini",
            tmp_path / "provider-must-not-be-resolved",
            execution_mode="real",
            receipt_path=tmp_path / "receipt.json",
            mcp_endpoint="http://127.0.0.1:9876/mcp",
        )


def test_managed_sources_server_refuses_preexisting_listener(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CANARY, "_endpoint_is_listening", lambda _host, _port: True)

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("must not launch over an existing listener")

    monkeypatch.setattr(CANARY.subprocess, "Popen", forbidden)
    with pytest.raises(CANARY.CanaryError, match="reviewed_sources_endpoint_already_in_use"):
        CANARY._start_reviewed_sources_server(compiler.DEFAULT_MCP_ENDPOINT)


def test_runtime_python_preserves_virtualenv_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_python = tmp_path / "base-python"
    base_python.write_bytes(b"#!/bin/sh\n")
    base_python.chmod(0o700)
    venv_python = tmp_path / "venv-python"
    venv_python.symlink_to(base_python)
    monkeypatch.setattr(CANARY.sys, "executable", str(venv_python))

    selected = CANARY._runtime_python()

    assert selected == venv_python
    assert selected.resolve() == base_python


def test_runtime_python_rejects_missing_entry_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(CANARY.sys, "executable", str(tmp_path / "missing-python"))

    with pytest.raises(CANARY.CanaryError, match="reviewed_python_executable_unavailable"):
        CANARY._runtime_python()


def test_cli_synthetic_mcp_cannot_execute_real_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def forbidden(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal called
        called = True
        raise AssertionError("provider invocation must not occur")

    monkeypatch.setattr(CANARY, "invoke_canary", forbidden)
    monkeypatch.setattr(sys, "argv", ["canary", "--provider", "gemini", "--synthetic-mcp"])

    assert CANARY.main() == 2
    assert called is False


@pytest.mark.parametrize("attempts", [0, 3, True])
def test_canary_rejects_attempt_limit_outside_one_structural_retry(tmp_path: Path, attempts: int) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    with pytest.raises(CANARY.CanaryError, match="invalid_attempt_limit"):
        CANARY.invoke_canary(
            "grok",
            tmp_path / "unused-provider",
            execution_mode="synthetic",
            sources_client=client,
            max_attempts=attempts,
        )
    client.close()


def test_grok_rejects_noncanonical_output_envelope() -> None:
    raw = CANARY.canonical(
        {"structured_output": {"labels": [], "liveness_challenge": "a" * 64}}
    )
    with pytest.raises(CANARY.CanaryStructuralError, match="structured_output_envelope_drift"):
        CANARY._extract_grok(raw, "a" * 64)


@pytest.mark.parametrize(
    ("raw", "failure_code"),
    [
        (
            b'{"event":"init","init":[]}\n'
            b'{"event":"result","result":{"status":"SUCCESS","structured_output":{}}}\n',
            "init_envelope_drift",
        ),
        (
            b'{"event":"init","init":{}}\n'
            b'{"event":"result","result":{"status":"SUCCESS","structured_output":{}}}\n',
            "init_model_binding_drift",
        ),
        (
            b'{"event":"init","init":{"model":"Gemini 3.6 Flash (High)"}}\n'
            b'{"event":"result","result":[]}\n',
            "result_envelope_drift",
        ),
        (
            b'{"event":"init","init":{"model":"Gemini 3.6 Flash (High)"}}\n'
            b'{"event":"result","result":{"status":"ERROR"}}\n',
            "provider_result_status_error",
        ),
        (
            b'{"event":"init","init":{"model":"Gemini 3.6 Flash (High)"}}\n'
            b'{"event":"result","result":{"status":"SUCCESS"}}\n',
            "structured_output_missing",
        ),
        (
            b'{"event":"init","init":{"model":"Gemini 3.6 Flash (High)"}}\n'
            b'{"event":"result","result":{"status":"SUCCESS","structured_output":[]}}\n',
            "structured_output_type_drift",
        ),
        (
            b'{"event":"init","init":{"model":"Gemini 3.6 Flash (High)"}}\n'
            b'{"event":"result","result":{"status":"SUCCESS","structured_output":{}}}\n',
            "structured_output_keys_drift",
        ),
    ],
)
def test_gemini_stream_reports_text_free_structural_cause(raw: bytes, failure_code: str) -> None:
    with pytest.raises(CANARY.CanaryStructuralError, match=failure_code):
        CANARY._extract_gemini(raw, "a" * 64)


def test_gemini_output_reports_liveness_drift_separately() -> None:
    raw = CANARY.canonical(
        {"event": "init", "init": {"model": "Gemini 3.6 Flash (High)"}}
    ) + CANARY.canonical(
        {
            "event": "result",
            "result": {
                "status": "SUCCESS",
                "structured_output": {
                    "labels_by_position": {"p01": {}, "p02": {}},
                    "liveness_challenge": "b" * 64,
                },
            },
        }
    )

    with pytest.raises(CANARY.CanaryStructuralError, match="liveness_challenge_drift"):
        CANARY._extract_gemini(raw, "a" * 64)


def test_structural_retry_permitted_on_first_attempt_malformed(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    labels = _build_mock_labels(sidecar)
    labels_json = json.dumps(labels)

    script = tmp_path / "retry_provider.py"
    marker = tmp_path / "attempt_marker.txt"
    code = f"""#!/usr/bin/env python3
import sys, json, re, os
from pathlib import Path

marker_path = Path("{marker}")
if not marker_path.exists():
    marker_path.write_text("1")
    # First attempt: exit with error (structural failure)
    sys.exit(1)

# Second attempt: succeed
prompt = sys.stdin.read()
m = re.search(r"Echo this exact liveness challenge in liveness_challenge: ([0-9a-f]+)", prompt)
challenge = m.group(1) if m else "mock-challenge"

labels = json.loads({json.dumps(labels_json)})
output = {{
    "labels": labels,
    "liveness_challenge": challenge,
}}
print(json.dumps(output))
"""
    script.write_text(code)
    script.chmod(0o755)

    receipt = CANARY.invoke_canary(
        "grok",
        script,
        execution_mode="synthetic",
        sources_client=client,
    )
    client.close()

    assert receipt["ok"] is True
    assert receipt["provider_call_count"] == 2


def test_structural_retry_exhausted_fails(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    script = tmp_path / "always_fails.py"
    script.write_text("""#!/usr/bin/env python3
import sys
sys.exit(1)
""")
    script.chmod(0o755)

    with pytest.raises(CANARY.CanaryError, match="provider_process_nonzero_exit"):
        CANARY.invoke_canary(
            "grok",
            script,
            execution_mode="synthetic",
            sources_client=client,
        )
    client.close()


def test_semantic_failure_is_terminal_no_retry(tmp_path: Path) -> None:
    client = CANARY.make_synthetic_mcp_client(tmp_path)
    sidecar = CANARY.compile_public_sidecar(client)
    # Build semantically invalid labels (trap agreed)
    labels = _build_mock_labels(sidecar, trap_agreed=True)
    labels_json = json.dumps(labels)

    calls_file = tmp_path / "call_count.txt"
    script = tmp_path / "semantic_fail_provider.py"
    code = f"""#!/usr/bin/env python3
import sys, json, re
from pathlib import Path

calls_path = Path("{calls_file}")
current = int(calls_path.read_text()) if calls_path.exists() else 0
calls_path.write_text(str(current + 1))

prompt = sys.stdin.read()
m = re.search(r"Echo this exact liveness challenge in liveness_challenge: ([0-9a-f]+)", prompt)
challenge = m.group(1) if m else "mock-challenge"

labels = json.loads({json.dumps(labels_json)})
output = {{
    "labels": labels,
    "liveness_challenge": challenge,
}}
print(json.dumps(output))
"""
    script.write_text(code)
    script.chmod(0o755)

    with pytest.raises(CANARY.CanarySemanticError):
        CANARY.invoke_canary(
            "grok",
            script,
            execution_mode="synthetic",
            sources_client=client,
        )
    client.close()

    # Verify provider was called exactly once — semantic error is terminal with NO retry!
    assert calls_file.read_text() == "1"


def test_static_verify_mode() -> None:
    gem_res = CANARY.static_verify("gemini")
    assert gem_res["ok"] is True
    assert gem_res["mode"] == "static"
    assert gem_res["provider"] == "gemini"

    grok_res = CANARY.static_verify("grok")
    assert grok_res["ok"] is True
    assert grok_res["mode"] == "static"
    assert grok_res["provider"] == "grok"


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="canary_tests_"))
    try:
        test_fixture_structure()
        test_compile_public_sidecar_with_synthetic_mcp(tmp / "t1")
        test_semantic_canary_assertions_pass_valid(tmp / "t2")
        test_semantic_canary_assertions_reject_trap_agreed(tmp / "t3")
        test_semantic_canary_assertions_reject_russian_shadow_only(tmp / "t4")
        test_semantic_canary_assertions_reject_antonenko_only(tmp / "t5")
        test_semantic_canary_assertions_reject_heritage_control_rejected(tmp / "t6")
        test_semantic_canary_assertions_reject_heritage_control_missing_evidence(tmp / "t7")
        test_synthetic_gemini_canary_invocation(tmp / "t8")
        test_synthetic_grok_canary_invocation(tmp / "t9")
        test_synthetic_provider_incapable_of_minting_real_receipt(tmp / "t10")
        test_structural_retry_permitted_on_first_attempt_malformed(tmp / "t11")
        test_structural_retry_exhausted_fails(tmp / "t12")
        test_semantic_failure_is_terminal_no_retry(tmp / "t13")
        test_static_verify_mode()
        print(json.dumps({"ok": True, "tests_passed": 14, "text_free": True}))
        return 0
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
