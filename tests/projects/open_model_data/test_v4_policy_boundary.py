"""Fixed policy is checked at real stage entrypoints, not by field equality."""

from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path

import pytest
from learn_ukrainian_v4_runtime import child_runtime, resources
from learn_ukrainian_v4_runtime import v4_a7_private_ledger as ledger
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused, digest

STAGES = [
    "a7_original_row_factory",
    "a8_admission_assembly",
    "a9_evaluation_package",
    "a10_pilot_review_gate",
    "a11_silver_release_gate",
    "a12_gold_overlay_gate",
    "a13_cleanup_recovery",
]


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("mutation", ["stale_top", "stale_completion", "missing_top"])
def test_stage_entrypoint_refuses_stale_or_missing_active_policy(stage, mutation):
    from learn_ukrainian_v4_runtime import v4_trust_authority as trust

    module = importlib.import_module("learn_ukrainian_v4_runtime.v4_" + stage)
    name = "data/projects/open_model_data/admission/dataset_v4_" + stage + "_receipt_v1.json"
    receipt = json.loads(resources.read_bytes(name))
    active = trust.load_production_trust_policy()[1]
    receipt["trust_policy_sha256"] = active if mutation == "stale_completion" else "f" * 64
    if mutation != "stale_top":
        receipt[stage.split("_", 1)[0] + "_completions"] = [{"trust_policy_sha256": "f" * 64}]
    if mutation == "missing_top":
        receipt.pop("trust_policy_sha256")
    with pytest.raises(ValueError, match="policy is not active"):
        module.validate_receipt_independently(receipt)


def test_admission_default_off_precedes_any_private_input_read(monkeypatch):
    monkeypatch.delenv("HRAMATKA_V4_ADMISSION_ENABLED", raising=False)
    arguments = {name: None for name in inspect.signature(ledger.construct_completion).parameters}
    with pytest.raises(OperationRefused, match="admission_disabled"):
        ledger.construct_completion(**arguments)


@pytest.mark.parametrize("harness", ["claude", "codex"])
@pytest.mark.parametrize(("role", "effort"), [("author", "medium"), ("reviewer", "high")])
def test_native_plan_binds_effort_and_keeps_secrets_out_of_argv(
    tmp_path: Path, harness: str, role: str, effort: str
) -> None:
    adapter = tmp_path / "fixture-cli"
    adapter.write_bytes(b"source-free fixture executable")
    adapter.chmod(0o400)
    capability = "synthetic-attempt-capability"
    provider_credential = "synthetic-provider-credential"
    profile = {
        "bwrap": "/usr/bin/bwrap",
        "bwrap_sha256": digest(Path("/usr/bin/bwrap").read_bytes()),
        "sources_url": "http://127.0.0.1:8766/mcp",
        "adapters": {
            harness: {
                "version": "fixture",
                "models": ["fixture-model"],
                "files": [{
                    "source": str(adapter),
                    "destination": "/runtime/fixture-cli",
                    "sha256": digest(adapter.read_bytes()),
                }],
                "executable": "/runtime/fixture-cli",
                "provider_env": {"claude": "ANTHROPIC_API_KEY", "codex": "OPENAI_API_KEY"}[harness],
            }
        },
    }
    claim = {
        "binding": {"expected_harness": harness, "expected_seat_or_model": "fixture-model", "role": role},
        "capability_token": capability,
    }

    if harness == "codex":
        profile["adapters"][harness]["files"].append({
            "source": str(adapter), "destination": "/runtime/codex-code-mode-host",
            "sha256": digest(adapter.read_bytes()),
        })
    command, environment = child_runtime._plan(profile, claim, provider_credential)
    launched_argv = "\x00".join(command)
    assert capability not in launched_argv
    assert provider_credential not in launched_argv
    assert environment["V4_SOURCES_ATTEMPT_CAPABILITY"] == capability
    provider_env = {"claude": "ANTHROPIC_API_KEY", "codex": "OPENAI_API_KEY"}[harness]
    assert environment[provider_env] == provider_credential
    if harness == "claude":
        assert command[command.index("--effort") + 1] == effort
        mcp_config = json.loads(command[command.index("--mcp-config") + 1])
        assert mcp_config["mcpServers"]["sources"]["headers"] == {
            "Authorization": "Bearer ${V4_SOURCES_ATTEMPT_CAPABILITY}"
        }
    else:
        assert "model_reasoning_effort=" + json.dumps(effort) in command
        assert command[command.index("--") + 2:command.index("--") + 5] == ["app-server", "--listen", "stdio://"]
        assert "--model" not in command and "--json" not in command
        assert "features.apps=false" in command
        permissions = {value for value in command if ".approval_mode=" in value}
        assert permissions == {
            f'mcp_servers.sources.tools.{name}.approval_mode="approve"'
            for name in ("verify_word", "verify_words", "verify_lemma", "verify_stress", "check_modern_form")
        }
        requests = child_runtime._codex_requests(claim["binding"])
        assert requests[2]["params"]["model"] == "fixture-model"
        assert requests[2]["params"]["approvalPolicy"] == "never"
        assert requests[2]["params"]["sandbox"] == "read-only"
        assert requests[3]["method"] == "mcpServerStatus/list"
    claim["binding"]["role"] = "caller-selected"
    with pytest.raises(OperationRefused, match="operation_role"):
        child_runtime._plan(profile, claim, provider_credential)


def test_codex_tool_runner_must_be_pinned_before_launch(tmp_path):
    binary = tmp_path / "fixture"
    binary.write_bytes(b"fixture")
    binary.chmod(0o400)
    profile = {
        "bwrap": "/usr/bin/bwrap", "bwrap_sha256": digest(Path("/usr/bin/bwrap").read_bytes()),
        "sources_url": "http://localhost:8766/mcp",
        "adapters": {"codex": {
            "version": "fixture", "models": ["fixture-model"], "provider_env": "OPENAI_API_KEY",
            "executable": "/runtime/fixture",
            "files": [{"source": str(binary), "destination": "/runtime/fixture",
                       "sha256": digest(binary.read_bytes())}],
        }},
    }
    claim = {"binding": {"expected_harness": "codex", "expected_seat_or_model": "fixture-model",
                         "role": "reviewer"}, "capability_token": "fixture-capability"}
    with pytest.raises(OperationRefused, match="adapter_tool_runner_unpinned"):
        child_runtime._plan(profile, claim, "fixture-provider")
