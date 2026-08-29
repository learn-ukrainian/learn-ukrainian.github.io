from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "batch_state" / "phase3-run-cycle007-public-canaries-v1.py"


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("cycle007_public_canaries_test", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_cli_requires_explicit_provider_bin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = _load_runner()
    monkeypatch.setattr(
        sys,
        "argv",
        [str(RUNNER), "--provider", "gemini", "--receipt", str(tmp_path / "receipt.json")],
    )

    assert runner.main() == 2
    assert json.loads(capsys.readouterr().out) == {
        "failure_code": "provider_bin_required_for_real_mode",
        "ok": False,
        "text_free": True,
    }


def test_gemini_schema_decisions_are_all_known_to_evidence_validator() -> None:
    runner = _load_runner()
    rows = runner.fixture_rows()
    schema = runner.gemini_schema(rows, "challenge")

    positions = schema["properties"]["labels_by_position"]["properties"]
    for position in ("p01", "p02"):
        decision_enum = set(positions[position]["properties"]["decision_code"]["enum"])
        assert decision_enum == runner.SOURCE.REJECTS
        assert decision_enum <= runner.validator.KNOWN_DECISIONS


def test_grok_schema_preserves_ordered_row_identity_and_liveness() -> None:
    runner = _load_runner()
    rows = runner.fixture_rows()
    schema = runner.grok_schema(rows, "challenge")

    labels = schema["properties"]["labels"]
    assert labels["minItems"] == labels["maxItems"] == 2
    assert "additionalItems" not in labels
    assert isinstance(labels["items"], dict)
    assert labels["items"]["properties"]["unit_id"]["enum"] == [row["unit_id"] for row in rows]
    assert labels["items"]["properties"]["unit_sha256"]["enum"] == [row["unit_sha256"] for row in rows]
    assert schema["properties"]["liveness_challenge"] == {"enum": ["challenge"]}


def test_real_cli_passes_explicit_provider_bin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner()
    provider = (tmp_path / "agy").resolve()
    receipt = tmp_path / "receipt.json"
    observed: dict[str, object] = {}

    def fake_invoke(provider_name: str, provider_bin: Path, **kwargs: object) -> dict[str, object]:
        observed.update(provider_name=provider_name, provider_bin=provider_bin, **kwargs)
        return {"ok": True, "text_free": True}

    monkeypatch.setattr(runner, "invoke_canary", fake_invoke)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RUNNER),
            "--provider",
            "gemini",
            "--provider-bin",
            str(provider),
            "--receipt",
            str(receipt),
        ],
    )

    assert runner.main() == 0
    assert observed["provider_name"] == "gemini"
    assert observed["provider_bin"] == provider
    assert observed["execution_mode"] == "real"
    assert observed["receipt_path"] == receipt


def test_real_invoke_rejects_relative_and_symlink_provider(tmp_path: Path) -> None:
    runner = _load_runner()
    with pytest.raises(runner.CanaryError, match="provider_executable_not_absolute"):
        runner.invoke_canary("gemini", Path("agy"), execution_mode="real")

    target = tmp_path / "agy-real"
    target.write_bytes(b"#!/bin/sh\n")
    target.chmod(0o700)
    link = tmp_path / "agy"
    link.symlink_to(target)
    with pytest.raises(runner.CanaryError, match="invalid_executable"):
        runner.invoke_canary("gemini", link, execution_mode="real")


def test_canary_accepts_one_strict_response_json_and_rejects_ambiguity() -> None:
    runner = _load_runner()
    payload = {"labels_by_position": {"p01": {}, "p02": {}}, "liveness_challenge": "challenge"}

    decoded, transport = runner._strict_result_payload({"response": json.dumps(payload)})
    assert decoded == payload
    assert transport == "response_json"

    with pytest.raises(runner.CanaryStructuralError, match="structured_output_missing"):
        runner._strict_result_payload({"response": [json.dumps(payload), json.dumps(payload)]})


def test_batch_runner_accepts_one_fenced_response_json() -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_batch_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    payload = {"labels_by_position": {"p01": {}, "p02": {}}}

    assert runner._strict_result_payload({"response": f"```json\n{json.dumps(payload)}\n```"}) == payload


def test_batch_runner_classifies_non_success_without_disclosing_provider_text() -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_batch_status_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    raw = (
        json.dumps({"event": "init", "init": {"model": runner.MODEL}})
        + "\n"
        + json.dumps(
            {
                "event": "result",
                "result": {"status": "FAILURE", "error": {"code": "RESOURCE_EXHAUSTED"}},
            }
        )
        + "\n"
    ).encode()

    with pytest.raises(runner.Error) as exc_info:
        runner._agy_stream(raw)
    assert exc_info.value.code == "provider_status_quota_or_rate_limit"
    assert exc_info.value.structural is False
    assert {
        "provider_status_quota_or_rate_limit",
        "provider_status_capacity_unavailable",
        "provider_status_timeout",
        "provider_status_cancelled",
        "provider_status_internal_error",
    } == runner.PROVIDER_STATUS_RECOVERY_CODES
    assert runner.PROVIDER_STATUS_RECOVERY_CODES.isdisjoint(
        {
            "provider_status_authentication_or_permission",
            "provider_status_structured_request_rejected",
            "provider_status_unknown",
        }
    )


def _byte_planner_rows(runner: ModuleType, sidecar_sizes: list[int]) -> tuple[dict[str, object], dict[str, object]]:
    rows: list[dict[str, object]] = []
    sidecar_rows: list[dict[str, object]] = []
    for index, size in enumerate(sidecar_sizes, 1):
        identity = {"unit_id": f"unit-{index:02d}", "unit_sha256": f"{index:064x}"}
        rows.append(identity | {"source": "public"})
        sidecar_rows.append(identity | {"evidence": "x" * size})
    return (
        {
            "rows": rows,
            "packet_identity_set_sha256": runner.digest(
                runner.canonical(sorted(runner._identity(row) for row in rows))
            ),
        },
        {"rows": sidecar_rows},
    )


def test_batch_runner_plans_deterministic_frozen_order_byte_bounded_chunks() -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_byte_planner_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    contents, sidecar = _byte_planner_rows(runner, [90_000, 330_000, 90_000, 430_000])

    first = runner.chunks(
        contents,
        sidecar,
        template=b"public prompt",
        lane="clean_label",
        request_byte_budget=512 * 1024,
    )
    second = runner.chunks(
        contents,
        sidecar,
        template=b"public prompt",
        lane="clean_label",
        request_byte_budget=512 * 1024,
    )

    assert first == second
    assert [row["unit_id"] for part, _sidecar in first for row in part["rows"]] == [
        "unit-01",
        "unit-02",
        "unit-03",
        "unit-04",
    ]
    assert all(part["request_byte_count"] <= 512 * 1024 for part, _sidecar in first)
    plan = runner.request_plan(
        contents,
        first,
        lane="clean_label",
        packet_index=1,
        request_byte_budget=512 * 1024,
        label_prompt_sha256="a" * 64,
    )
    unsigned = {key: value for key, value in plan.items() if key != "plan_sha256"}
    assert plan["plan_sha256"] == runner.digest(runner.canonical(unsigned))
    assert plan["planner_version"] == runner.PLANNER_VERSION
    assert sum(chunk["row_count"] for chunk in plan["chunks"]) == 4


def test_batch_runner_refuses_single_row_over_byte_budget() -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_oversize_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    contents, sidecar = _byte_planner_rows(runner, [600_000])

    with pytest.raises(runner.Error, match="request_byte_budget_exceeded"):
        runner.chunks(
            contents,
            sidecar,
            template=b"public prompt",
            lane="clean_label",
            request_byte_budget=512 * 1024,
        )

    parts = runner.chunks(
        contents,
        sidecar,
        template=b"public prompt",
        lane="clean_label",
        request_byte_budget=640 * 1024,
    )
    assert len(parts) == 1
    assert parts[0][0]["request_byte_count"] <= 640 * 1024
    assert runner.DEFAULT_REQUEST_BYTE_BUDGET == 640 * 1024


def test_batch_runner_forbids_same_budget_retry_after_timeout(tmp_path: Path) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_timeout_retry_guard_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    package = tmp_path / "package"
    out = package / runner.OUTPUT / "clean_label/chunks/packet-0001"
    out.mkdir(parents=True, mode=0o700)
    started = out / "attempt-1-chunk-01.started.json"
    terminal = out / "attempt-1-chunk-01.terminal.json"
    started.write_bytes(runner.canonical({"state": "started", "text_free": True}))
    terminal.write_bytes(
        runner.canonical(
            {
                "failure_code": "provider_status_timeout",
                "failure_stage": "provider_return",
                "request_byte_budget": 512 * 1024,
                "text_free": True,
            }
        )
    )
    started.chmod(0o600)
    terminal.chmod(0o600)

    with pytest.raises(runner.Error, match="same_size_timeout_retry_forbidden"):
        runner._next_attempt(package, out, 1, request_byte_budget=512 * 1024)


def test_batch_runner_accepts_same_budget_only_for_exact_timeout_fix_receipt(
    tmp_path: Path,
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_timeout_fix_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    package = tmp_path / "package"
    out = package / runner.OUTPUT / "clean_label/chunks/packet-0001"
    out.mkdir(parents=True, mode=0o700)
    started = out / "attempt-1-chunk-01.started.json"
    terminal = out / "attempt-1-chunk-01.terminal.json"
    started.write_bytes(runner.canonical({"state": "started", "text_free": True}))
    terminal_value = {
        "schema_version": "phase3_cycle007_gemini_attempt_v2",
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "request_byte_budget": 640 * 1024,
        "text_free": True,
    }
    terminal.write_bytes(runner.canonical(terminal_value))
    started.chmod(0o600)
    terminal.chmod(0o600)
    body = {
        "schema_version": runner.TIMEOUT_FIX_RECOVERY_SCHEMA,
        "evaluation_cycle_id": runner.CYCLE,
        "source_provider_stop_sha256": "a" * 64,
        "started_marker_sha256": runner.digest(started.read_bytes()),
        "terminal_marker_sha256": runner.digest(terminal.read_bytes()),
        "failure_code": terminal_value["failure_code"],
        "failure_stage": terminal_value["failure_stage"],
        "prior_provider_call_count": 1,
        "authorized_additional_provider_calls": 1,
        "exact_model": runner.MODEL,
        "model_family": runner.FAMILY,
        "harness": runner.HARNESS,
        "text_free": True,
        "authorized_attempt": 2,
        "request_byte_budget": 640 * 1024,
        "gemini_runner_sha256": runner.digest(path.read_bytes()),
        "agy_print_timeout": runner.AGY_PRINT_TIMEOUT,
    }
    receipt = body | {"receipt_sha256": runner.digest(runner.canonical(body))}
    receipt_path = package / runner.OUTPUT / runner.RECOVERY_RECEIPT
    receipt_path.write_bytes(runner.canonical(receipt))
    receipt_path.chmod(0o600)

    assert runner._next_attempt(package, out, 1, request_byte_budget=640 * 1024) == 2
    receipt["gemini_runner_sha256"] = "0" * 64
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = runner.digest(runner.canonical(unsigned))
    receipt_path.write_bytes(runner.canonical(receipt))
    with pytest.raises(runner.Error, match="ordinal_identity_binding_drift"):
        runner._next_attempt(package, out, 1, request_byte_budget=640 * 1024)

    terminal_value["failure_code"] = "structured_output_envelope_drift"
    terminal.write_bytes(runner.canonical(terminal_value))
    receipt["failure_code"] = terminal_value["failure_code"]
    receipt["terminal_marker_sha256"] = runner.digest(terminal.read_bytes())
    receipt["gemini_runner_sha256"] = runner.digest(path.read_bytes())
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = runner.digest(runner.canonical(unsigned))
    receipt_path.write_bytes(runner.canonical(receipt))
    with pytest.raises(runner.Error, match="ordinal_identity_binding_drift"):
        runner._next_attempt(package, out, 1, request_byte_budget=640 * 1024)


def test_batch_runner_requires_exact_recovery_receipt_for_stopped_retry(tmp_path: Path) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_batch_recovery_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    package = tmp_path / "package"
    attempt = package / runner.OUTPUT / "clean_label/chunks/packet-0001"
    attempt.mkdir(parents=True, mode=0o700)
    started = attempt / "attempt-1-chunk-01.started.json"
    terminal = attempt / "attempt-1-chunk-01.terminal.json"
    started.write_bytes(runner.canonical({"state": "started", "text_free": True}))
    terminal_value = {
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "text_free": True,
    }
    terminal.write_bytes(runner.canonical(terminal_value))
    started.chmod(0o600)
    terminal.chmod(0o600)
    body = {
        "schema_version": "phase3_cycle007_gemini_provider_recovery_v1",
        "evaluation_cycle_id": runner.CYCLE,
        "source_provider_stop_sha256": "a" * 64,
        "started_marker_sha256": runner.digest(started.read_bytes()),
        "terminal_marker_sha256": runner.digest(terminal.read_bytes()),
        "failure_code": terminal_value["failure_code"],
        "failure_stage": terminal_value["failure_stage"],
        "prior_provider_call_count": 1,
        "authorized_additional_provider_calls": 1,
        "exact_model": runner.MODEL,
        "model_family": runner.FAMILY,
        "harness": runner.HARNESS,
        "text_free": True,
    }
    receipt = body | {"receipt_sha256": runner.digest(runner.canonical(body))}
    receipt_path = package / runner.OUTPUT / runner.RECOVERY_RECEIPT
    receipt_path.write_bytes(runner.canonical(receipt))
    receipt_path.chmod(0o600)

    assert runner._next_attempt(package, attempt, 1) == 2
    receipt["authorized_additional_provider_calls"] = 2
    receipt_path.write_bytes(runner.canonical(receipt))
    with pytest.raises(runner.Error, match="ordinal_identity_binding_drift"):
        runner._next_attempt(package, attempt, 1)


def _seed_runner_second_recovery(runner: ModuleType, package: Path) -> Path:
    out = package / runner.OUTPUT / "clean_label/chunks/packet-0001"
    out.mkdir(parents=True, mode=0o700)
    markers: dict[int, tuple[Path, Path]] = {}
    for attempt in (1, 2):
        started = out / f"attempt-{attempt}-chunk-01.started.json"
        terminal = out / f"attempt-{attempt}-chunk-01.terminal.json"
        started.write_bytes(runner.canonical({"attempt": attempt, "state": "started", "text_free": True}))
        terminal.write_bytes(
            runner.canonical(
                {
                    "attempt": attempt,
                    "state": "terminal",
                    "failure_code": "provider_status_timeout",
                    "failure_stage": "provider_return",
                    "text_free": True,
                }
            )
        )
        started.chmod(0o600)
        terminal.chmod(0o600)
        markers[attempt] = (started, terminal)
    first_started, first_terminal = markers[1]
    first_body = {
        "schema_version": "phase3_cycle007_gemini_provider_recovery_v1",
        "evaluation_cycle_id": runner.CYCLE,
        "source_provider_stop_sha256": "a" * 64,
        "started_marker_sha256": runner.digest(first_started.read_bytes()),
        "terminal_marker_sha256": runner.digest(first_terminal.read_bytes()),
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "prior_provider_call_count": 1,
        "authorized_additional_provider_calls": 1,
        "exact_model": runner.MODEL,
        "model_family": runner.FAMILY,
        "harness": runner.HARNESS,
        "text_free": True,
    }
    first_receipt = first_body | {"receipt_sha256": runner.digest(runner.canonical(first_body))}
    first_path = package / runner.OUTPUT / runner.RECOVERY_RECEIPT
    first_path.write_bytes(runner.canonical(first_receipt))
    first_path.chmod(0o600)
    second_started, second_terminal = markers[2]
    second_body = {
        "schema_version": "phase3_cycle007_gemini_provider_second_recovery_v1",
        "evaluation_cycle_id": runner.CYCLE,
        "source_provider_stop_sha256": "b" * 64,
        "prior_recovery_receipt_sha256": runner.digest(first_path.read_bytes()),
        "started_marker_sha256": runner.digest(second_started.read_bytes()),
        "terminal_marker_sha256": runner.digest(second_terminal.read_bytes()),
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "prior_provider_call_count": 2,
        "authorized_additional_provider_calls": 1,
        "authorized_attempt": 3,
        "exact_model": runner.MODEL,
        "model_family": runner.FAMILY,
        "harness": runner.HARNESS,
        "text_free": True,
    }
    second_receipt = second_body | {
        "receipt_sha256": runner.digest(runner.canonical(second_body))
    }
    second_path = package / runner.OUTPUT / runner.SECOND_RECOVERY_RECEIPT
    second_path.write_bytes(runner.canonical(second_receipt))
    second_path.chmod(0o600)
    return out


def test_batch_runner_accepts_only_exact_chained_attempt_three_receipt(tmp_path: Path) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_attempt_three_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    package = tmp_path / "package"
    out = _seed_runner_second_recovery(runner, package)

    assert runner._next_attempt(package, out, 1) == 3
    second_path = package / runner.OUTPUT / runner.SECOND_RECOVERY_RECEIPT
    receipt = json.loads(second_path.read_text(encoding="utf-8"))
    receipt["prior_recovery_receipt_sha256"] = "0" * 64
    second_path.write_bytes(runner.canonical(receipt))
    with pytest.raises(runner.Error, match="ordinal_identity_binding_drift"):
        runner._next_attempt(package, out, 1)


def test_batch_runner_accepts_exact_receipt_after_first_structural_call(
    tmp_path: Path,
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_legacy_structural_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    package = tmp_path / "package"
    out = _seed_runner_second_recovery(runner, package)

    first_terminal_path = out / "attempt-1-chunk-01.terminal.json"
    first_terminal = json.loads(first_terminal_path.read_text(encoding="utf-8"))
    first_terminal["failure_code"] = "structured_output_envelope_drift"
    first_terminal_path.write_bytes(runner.canonical(first_terminal))

    first_path = package / runner.OUTPUT / runner.RECOVERY_RECEIPT
    first = json.loads(first_path.read_text(encoding="utf-8"))
    first["failure_code"] = "structured_output_envelope_drift"
    first["terminal_marker_sha256"] = runner.digest(first_terminal_path.read_bytes())
    first_unsigned = {key: value for key, value in first.items() if key != "receipt_sha256"}
    first["receipt_sha256"] = runner.digest(runner.canonical(first_unsigned))
    first_path.write_bytes(runner.canonical(first))

    second_path = package / runner.OUTPUT / runner.SECOND_RECOVERY_RECEIPT
    second = json.loads(second_path.read_text(encoding="utf-8"))
    second["prior_recovery_receipt_sha256"] = runner.digest(first_path.read_bytes())
    second_unsigned = {key: value for key, value in second.items() if key != "receipt_sha256"}
    second["receipt_sha256"] = runner.digest(runner.canonical(second_unsigned))
    second_path.write_bytes(runner.canonical(second))

    assert runner._next_attempt(package, out, 1) == 3


def test_batch_runner_fresh_process_requires_then_accepts_exact_attempt_four_receipt(
    tmp_path: Path,
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_fresh_process_seed", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    package = tmp_path / "package"
    out = _seed_runner_second_recovery(runner, package)
    script = (
        "import importlib.util,sys;"
        "p=sys.argv[1];pkg=__import__('pathlib').Path(sys.argv[2]);"
        "s=importlib.util.spec_from_file_location('fresh',p);m=importlib.util.module_from_spec(s);"
        "s.loader.exec_module(m);o=pkg/m.OUTPUT/'clean_label/chunks/packet-0001';"
        "raise SystemExit(0 if m._next_attempt(pkg,o,1)==3 else 1)"
    )
    assert subprocess.run(
        [sys.executable, "-c", script, str(path), str(package)], check=False, timeout=30
    ).returncode == 0

    attempt_three_started = out / "attempt-3-chunk-01.started.json"
    attempt_three_terminal = out / "attempt-3-chunk-01.terminal.json"
    attempt_three_started.write_bytes(runner.canonical({"state": "started", "text_free": True}))
    attempt_three_terminal.write_bytes(
        runner.canonical(
            {
                "state": "terminal",
                "failure_code": "provider_status_timeout",
                "failure_stage": "provider_return",
                "text_free": True,
            }
        )
    )
    attempt_three_started.chmod(0o600)
    attempt_three_terminal.chmod(0o600)
    refusal_script = script.replace(
        "raise SystemExit(0 if m._next_attempt(pkg,o,1)==3 else 1)",
        "\ntry:m._next_attempt(pkg,o,1)\nexcept m.Error:raise SystemExit(0)\nraise SystemExit(1)",
    )
    assert subprocess.run(
        [sys.executable, "-c", refusal_script, str(path), str(package)], check=False, timeout=30
    ).returncode == 0

    prior_recovery = package / runner.OUTPUT / runner.SECOND_RECOVERY_RECEIPT
    fourth_body = {
        "schema_version": "phase3_cycle007_gemini_provider_second_recovery_v1",
        "evaluation_cycle_id": runner.CYCLE,
        "source_provider_stop_sha256": "c" * 64,
        "prior_recovery_receipt_sha256": runner.digest(prior_recovery.read_bytes()),
        "started_marker_sha256": runner.digest(attempt_three_started.read_bytes()),
        "terminal_marker_sha256": runner.digest(attempt_three_terminal.read_bytes()),
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "prior_provider_call_count": 3,
        "authorized_additional_provider_calls": 1,
        "authorized_attempt": 4,
        "exact_model": runner.MODEL,
        "model_family": runner.FAMILY,
        "harness": runner.HARNESS,
        "text_free": True,
    }
    fourth_receipt = fourth_body | {
        "receipt_sha256": runner.digest(runner.canonical(fourth_body))
    }
    fourth_path = out / "provider-recovery-chunk-01-attempt-4.json"
    fourth_path.write_bytes(runner.canonical(fourth_receipt))
    fourth_path.chmod(0o600)
    fourth_script = script.replace("==3", "==4")
    assert subprocess.run(
        [sys.executable, "-c", fourth_script, str(path), str(package)],
        check=False,
        timeout=30,
    ).returncode == 0


def test_batch_runner_has_no_permanent_retry_ceiling_and_requires_each_link(
    tmp_path: Path,
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_renewable_chain_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    package = tmp_path / "package"
    out = package / runner.OUTPUT / "clean_label/chunks/packet-0001"
    out.mkdir(parents=True, mode=0o700)
    prior_raw: bytes | None = None

    def add_timeout(attempt: int, *, authorize_next: bool) -> None:
        nonlocal prior_raw
        started = out / f"attempt-{attempt}-chunk-01.started.json"
        terminal = out / f"attempt-{attempt}-chunk-01.terminal.json"
        started.write_bytes(
            runner.canonical({"attempt": attempt, "state": "started", "text_free": True})
        )
        terminal.write_bytes(
            runner.canonical(
                {
                    "attempt": attempt,
                    "state": "terminal",
                    "failure_code": "provider_status_timeout",
                    "failure_stage": "provider_return",
                    "text_free": True,
                }
            )
        )
        started.chmod(0o600)
        terminal.chmod(0o600)
        if not authorize_next:
            return
        body = {
            "schema_version": (
                "phase3_cycle007_gemini_provider_recovery_v1"
                if prior_raw is None
                else "phase3_cycle007_gemini_provider_second_recovery_v1"
            ),
            "evaluation_cycle_id": runner.CYCLE,
            "source_provider_stop_sha256": f"{attempt:064x}",
            "started_marker_sha256": runner.digest(started.read_bytes()),
            "terminal_marker_sha256": runner.digest(terminal.read_bytes()),
            "failure_code": "provider_status_timeout",
            "failure_stage": "provider_return",
            "prior_provider_call_count": attempt,
            "authorized_additional_provider_calls": 1,
            "exact_model": runner.MODEL,
            "model_family": runner.FAMILY,
            "harness": runner.HARNESS,
            "text_free": True,
        }
        if prior_raw is not None:
            body |= {
                "prior_recovery_receipt_sha256": runner.digest(prior_raw),
                "authorized_attempt": attempt + 1,
            }
        receipt = body | {"receipt_sha256": runner.digest(runner.canonical(body))}
        if attempt == 1:
            receipt_path = package / runner.OUTPUT / runner.RECOVERY_RECEIPT
        elif attempt == 2:
            receipt_path = package / runner.OUTPUT / runner.SECOND_RECOVERY_RECEIPT
        else:
            receipt_path = (
                out / f"provider-recovery-chunk-01-attempt-{attempt + 1}.json"
            )
        receipt_path.write_bytes(runner.canonical(receipt))
        receipt_path.chmod(0o600)
        prior_raw = receipt_path.read_bytes()

    for attempt in range(1, 13):
        add_timeout(attempt, authorize_next=True)
    assert runner._next_attempt(package, out, 1) == 13

    add_timeout(13, authorize_next=False)
    with pytest.raises(runner.Error, match="ordinal_identity_binding_drift"):
        runner._next_attempt(package, out, 1)
    add_timeout(13, authorize_next=True)
    assert runner._next_attempt(package, out, 1) == 14


def test_batch_runner_pins_the_certified_evidence_compiler_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_batch_identity_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    monkeypatch.setattr(runner.compiler, "TOKENIZER_ID", "runtime-drift")
    monkeypatch.setattr(runner.compiler, "TOKENIZER_VERSION", "runtime-drift")
    monkeypatch.setattr(runner.compiler, "CODE_HASHES", {"compiler_sha256": "0" * 64})

    identity = runner._get_expected_identity()
    expected_hash = "8c66529479976f71ce5f28b82765a5916cc06c9dee737d7ce20bd89aa27cc522"
    assert identity["tokenizer_id"] == "phase3-cycle007-cyrillic-tokenizer-v1"
    assert identity["tokenizer_version"] == "1"
    assert set(identity["code_hashes"]) == {
        "compiler_id",
        "compiler_sha256",
        "compound_parser_id",
        "compound_parser_sha256",
        "compound_parser_version",
        "mcp_response_parser_id",
        "mcp_response_parser_sha256",
        "mcp_response_parser_version",
        "query_plan_id",
        "query_plan_sha256",
        "query_plan_version",
        "tokenizer_id",
        "tokenizer_sha256",
        "tokenizer_version",
    }
    assert {
        value
        for key, value in identity["code_hashes"].items()
        if key.endswith("_sha256")
    } == {expected_hash}
    assert identity["code_hashes"] is not runner.FROZEN_EVIDENCE_CODE_HASHES


def test_batch_runner_uses_controller_bound_source_identity_without_local_databases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_bound_sources_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    monkeypatch.setattr(runner.compiler, "DEFAULT_SERVER_CODE", tmp_path / "missing-server.py")
    monkeypatch.setattr(runner.compiler, "DEFAULT_SOURCES_DB", tmp_path / "missing-sources.db")
    monkeypatch.setattr(runner.compiler, "DEFAULT_VESUM_DB", tmp_path / "missing-vesum.db")
    runner.EXPECTED_SOURCES_ENDPOINT_IDENTITY = {
        "server_code_sha256": "1" * 64,
        "sources_db_sha256": "2" * 64,
        "vesum_db_sha256": "3" * 64,
    }

    identity = runner._get_expected_identity()

    assert identity["server_code_sha256"] == "1" * 64
    assert identity["sources_db_sha256"] == "2" * 64
    assert identity["vesum_db_sha256"] == "3" * 64


def test_grok_runner_uses_controller_bound_source_identity_without_local_databases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-grok-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_grok_bound_sources_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    monkeypatch.setattr(runner.compiler, "DEFAULT_SERVER_CODE", tmp_path / "missing-server.py")
    monkeypatch.setattr(runner.compiler, "DEFAULT_SOURCES_DB", tmp_path / "missing-sources.db")
    monkeypatch.setattr(runner.compiler, "DEFAULT_VESUM_DB", tmp_path / "missing-vesum.db")
    runner.EXPECTED_SOURCES_ENDPOINT_IDENTITY = {
        "server_code_sha256": "4" * 64,
        "sources_db_sha256": "5" * 64,
        "vesum_db_sha256": "6" * 64,
    }

    identity = runner._get_expected_identity()

    assert identity["server_code_sha256"] == "4" * 64
    assert identity["sources_db_sha256"] == "5" * 64
    assert identity["vesum_db_sha256"] == "6" * 64


def test_batch_stream_input_command_has_no_print_prompt() -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_batch_command_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    command = runner._command(Path("/provider"), Path("/schema.json"), Path("/agy.log"))

    assert command.count("--input-format") == 1
    assert command[command.index("--input-format") + 1] == "stream-json"
    assert command.count("--output-format") == 1
    assert command[command.index("--output-format") + 1] == "stream-json"
    assert "--print" not in command
    assert "--new-project" in command
    assert command.count("--print-timeout") == 1
    assert command[command.index("--print-timeout") + 1] == runner.AGY_PRINT_TIMEOUT == "120m"


def test_public_canary_uses_the_same_explicit_agy_print_timeout() -> None:
    canary = _load_runner()
    command = canary._gemini_command(Path("/provider"), Path("/schema.json"), Path("/agy.log"))

    assert command.count("--print-timeout") == 1
    assert command[command.index("--print-timeout") + 1] == canary.AGY_PRINT_TIMEOUT == "120m"


def test_grok_commands_use_only_the_reviewed_cli_isolation_flags() -> None:
    canary = _load_runner()
    path = ROOT / "batch_state" / "phase3-run-cycle007-grok-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_grok_batch_command_test", path)
    assert spec is not None and spec.loader is not None
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)

    expected_isolation_flags = {"--permission-mode", "--no-alt-screen", "--no-subagents", "--disable-web-search"}
    prompt_path = Path("/private/prompt")
    output_schema = {"type": "object"}
    session_id = "00000000-0000-4000-8000-000000000007"
    for command in (
        canary._grok_command(Path("/provider"), prompt_path, output_schema, session_id),
        batch._provider_command(Path("/provider"), prompt_path, output_schema, session_id),
    ):
        assert expected_isolation_flags <= set(command)
        assert "--no-memory" not in command
        assert command.count("--prompt-file") == 1
        assert command[command.index("--prompt-file") + 1] == str(prompt_path)
        assert command[command.index("--output-format") + 1] == "json"
        schema_argument = command[command.index("--json-schema") + 1]
        assert json.loads(schema_argument) == output_schema
        assert not schema_argument.endswith("\n")
        assert command[command.index("--session-id") + 1] == session_id


def test_grok_batch_schema_keeps_private_identity_out_of_bounded_argument() -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-grok-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_grok_batch_schema_test", path)
    assert spec is not None and spec.loader is not None
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)
    rows = [{"unit_id": f"private-unit-{index:02d}", "unit_sha256": f"{index:064x}"} for index in range(50)]

    for lane in ("clean_label", "residual_label"):
        schema = batch._provider_schema(lane, rows)
        labels = schema["properties"]["labels"]
        identity = labels["items"]["properties"]
        assert labels["minItems"] == labels["maxItems"] == 50
        assert identity["unit_id"] == {"type": "string", "minLength": 1}
        assert identity["unit_sha256"] == {"type": "string", "pattern": "^[0-9a-f]{64}$"}
        argument = json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        assert all(row["unit_id"] not in argument and row["unit_sha256"] not in argument for row in rows)
        assert len(argument.encode()) < 16_384
        assert not argument.endswith("\n")


def test_grok_batch_binds_and_removes_private_prompt_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-grok-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_grok_batch_prompt_test", path)
    assert spec is not None and spec.loader is not None
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)
    observed: dict[str, Path] = {}

    def fake_run(command: list[str], **kwargs: object) -> object:
        prompt_path = Path(command[command.index("--prompt-file") + 1])
        observed["prompt_path"] = prompt_path
        assert prompt_path.parent == tmp_path
        assert prompt_path.read_bytes() == b"public prompt"
        assert prompt_path.stat().st_mode & 0o777 == 0o600
        assert kwargs["input"] == b"public prompt"
        return batch.subprocess.CompletedProcess(command, 0, stdout=b"{}", stderr=b"")

    monkeypatch.setattr(batch.subprocess, "run", fake_run)
    result, session_id = batch._run_provider(
        Path("/provider"), b"public prompt", tmp_path, {"type": "object"}
    )

    assert result.returncode == 0
    assert session_id
    assert not observed["prompt_path"].exists()


def test_grok_canary_requires_documented_json_envelope_and_matching_session() -> None:
    runner = _load_runner()
    payload = {"labels": [{"one": 1}, {"two": 2}], "liveness_challenge": "challenge"}
    session_id = "00000000-0000-4000-8000-000000000007"
    envelope = {
        "text": f"Schema result follows.\n```json\n{json.dumps(payload)}\n```",
        "sessionId": session_id,
        "stopReason": "end_turn",
        "requestId": "request-7",
    }

    assert runner._extract_grok(("CLI presentation\n" + json.dumps(envelope)).encode(), "challenge", session_id) == {
        "labels": payload["labels"]
    }
    with pytest.raises(runner.CanaryStructuralError, match="structured_output_envelope_drift"):
        runner._extract_grok(json.dumps(envelope).encode(), "challenge", "wrong-session")
    with pytest.raises(runner.CanaryStructuralError, match="structured_output_envelope_drift"):
        runner._extract_grok(json.dumps(payload).encode(), "challenge", session_id)
    trailing = envelope | {"text": f"{json.dumps(payload)}\nuntrusted trailing prose"}
    with pytest.raises(runner.CanaryStructuralError, match="schema_json_trailing_drift"):
        runner._extract_grok(json.dumps(trailing).encode(), "challenge", session_id)
    doubled = (json.dumps(envelope) + "\n" + json.dumps(envelope)).encode()
    with pytest.raises(runner.CanaryStructuralError, match="outer_json_trailing_drift"):
        runner._extract_grok(doubled, "challenge", session_id)


def test_grok_canary_retry_mints_a_fresh_session(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner()
    provider = tmp_path / "grok"
    provider.write_bytes(b"#!/bin/sh\n")
    provider.chmod(0o700)
    sources = runner.make_synthetic_mcp_client(tmp_path / "sources")
    observed_sessions: list[str] = []

    def fake_run(command: list[str], **kwargs: object) -> object:
        observed_sessions.append(command[command.index("--session-id") + 1])
        kwargs["stdout"].write(b"{}")
        return runner.subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    with pytest.raises(runner.CanaryError, match="structural_retry_exhausted"):
        runner.invoke_canary(
            "grok",
            provider,
            execution_mode="synthetic",
            sources_client=sources,
            max_attempts=2,
        )

    assert len(observed_sessions) == 2
    assert len(set(observed_sessions)) == 2


def test_grok_batch_decodes_only_documented_matching_session_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-grok-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_grok_batch_decode_test", path)
    assert spec is not None and spec.loader is not None
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)
    payload = {"labels": [{"unit_id": "one"}]}
    session_id = "00000000-0000-4000-8000-000000000007"
    envelope = {
        "text": f"Schema result follows.\n{json.dumps(payload)}",
        "sessionId": session_id,
        "stopReason": "end_turn",
        "requestId": "request-7",
    }
    validated: list[bytes] = []

    def fake_validate(lane: str, packet: dict[str, object], raw: bytes, **kwargs: object) -> dict[str, object]:
        assert lane == "clean_label"
        assert packet == {"lane": "clean_label"}
        validated.append(raw)
        return payload

    monkeypatch.setattr(batch, "validate", fake_validate)
    decoded = batch._decode_provider(
        ("CLI presentation\n" + json.dumps(envelope)).encode(),
        {"lane": "clean_label"},
        expected_session_id=session_id,
    )

    assert decoded == batch.canonical(payload)
    assert validated == [batch.canonical(payload)]
    with pytest.raises(batch.Invalid, match="structured_output_envelope_drift"):
        batch._decode_provider(
            json.dumps(envelope).encode(),
            {"lane": "clean_label"},
            expected_session_id="wrong-session",
        )
    trailing = envelope | {"text": f"{json.dumps(payload)}\nuntrusted trailing prose"}
    with pytest.raises(batch.Invalid, match="schema_json_trailing_drift"):
        batch._decode_provider(
            json.dumps(trailing).encode(),
            {"lane": "clean_label"},
            expected_session_id=session_id,
        )


def test_grok_terminal_json_rule_rejects_multiple_values_but_skips_malformed_decoys() -> None:
    canary = _load_runner()
    path = ROOT / "batch_state" / "phase3-run-cycle007-grok-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_grok_batch_terminal_json_test", path)
    assert spec is not None and spec.loader is not None
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)
    value = {"labels": []}

    for runner in (canary, batch):
        assert runner._strict_grok_text_json(f"presentation {{broken\n{json.dumps(value)}") == value
        with pytest.raises(
            (canary.CanaryStructuralError, batch.Invalid), match="schema_json_trailing_drift"
        ):
            runner._strict_grok_text_json(f"{json.dumps(value)}\n{json.dumps(value)}")


def test_batch_stream_rejects_reported_cwd_mismatch(tmp_path: Path) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_batch_cwd_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    raw = (
        runner.canonical({"event": "init", "init": {"model": runner.MODEL, "cwd": str(tmp_path)}})
        + runner.canonical(
            {
                "event": "result",
                "result": {
                    "status": "SUCCESS",
                    "structured_output": {"labels_by_position": {"p01": {}}},
                },
            }
        )
    )

    assert runner._extract(raw, expected_cwd=tmp_path) == {"labels_by_position": {"p01": {}}}
    with pytest.raises(runner.Error, match="structured_output_envelope_drift"):
        runner._extract(raw, expected_cwd=tmp_path.parent)
