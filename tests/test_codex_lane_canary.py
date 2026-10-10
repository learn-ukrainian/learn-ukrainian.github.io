"""Codex canary control-flow tests."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.session_canary import codex_lane


@pytest.mark.parametrize("epic", ["../../tmp/evil", "/absolute/evil", "bad_name", "-infra", "infra-"])
def test_bootstrap_rejects_unsafe_epic_before_writing(tmp_path, epic):
    if epic == "/absolute/evil":
        epic = str(tmp_path / "absolute" / "evil")
    assert codex_lane.main(["--repo", str(tmp_path), "bootstrap", f"--epic={epic}", "--stream", "epic:7919"]) != 0
    assert not (tmp_path / ".claude").exists()


@pytest.mark.parametrize("provider", ["codex", "gemini", "glm"])
def test_lane_import_and_bare_hydration_do_not_import_slot_registry(provider) -> None:
    """Keep the bridge import graph outside the hook's bare-provider cold path."""
    code = """
import importlib
import importlib.abc
import os
import sys

class NoRegistry(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {"scripts.orchestration.handoff_slot_registry", "scripts.ai_agent_bridge"}:
            raise AssertionError("unneeded cold-path import: " + fullname)

sys.meta_path.insert(0, NoRegistry())
provider = sys.argv[1]
lane = importlib.import_module("scripts.session_canary." + provider + "_lane")
os.environ["SESSION_STREAM_AGENT"] = provider
calls = []
def hydrate(stream, identity):
    calls.append((stream, identity))
    return {"execution_allowed": True}, 1
lane.shared_hydration.build_hydration_capsule_with_retry = hydrate
assert lane.main(["hydrate", "--epic", "core", "--stream", "epic:123"]) == 0
assert calls == [("epic:123", provider)]
"""
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", code, provider],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert result.stdout == '{"execution_allowed": true}\nACTION: hydration ready — continue the current driver.\n'
    assert result.stderr == "hydration_attempts: 1\n"


def _allowed_capsule() -> dict[str, object]:
    return {"execution_allowed": True}


def test_score_pass_hydrates_then_continues(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(codex_lane, "_with_codex_handoffs", lambda function, args: 0)
    monkeypatch.setattr(
        codex_lane.shared_hydration, "build_hydration_capsule", lambda stream, lane, **_: _allowed_capsule()
    )

    assert codex_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 0
    assert "hydration ready — continue" in capsys.readouterr().out


def test_score_fail_handoff_closes_exact_lease_and_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(codex_lane, "_with_codex_handoffs", lambda function, args: 2)
    monkeypatch.setattr(codex_lane, "_close_exact_lease", lambda repo, epic: True)

    assert codex_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 2
    assert "FAIL-HANDOFF — exact lease closed" in capsys.readouterr().out


def test_hydrate_refuses_to_continue_when_capsule_is_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        codex_lane.shared_hydration,
        "build_hydration_capsule",
        lambda stream, lane, **_: {"execution_allowed": False},
    )

    assert codex_lane.main(["hydrate", "--epic", "harness"]) == 2
    assert "hydration blocked" in capsys.readouterr().err


def test_score_closes_lease_when_post_pass_hydration_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[tuple[object, str]] = []
    monkeypatch.setattr(codex_lane, "_with_codex_handoffs", lambda function, args: 0)
    monkeypatch.setattr(codex_lane, "cmd_hydrate", lambda args: 2)
    monkeypatch.setattr(codex_lane, "_close_exact_lease", lambda repo, epic: closed.append((repo, epic)) or True)

    assert codex_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 2
    assert closed and closed[0][1] == "harness"


def test_lease_environment_parser_reuses_gemini_reader(tmp_path: Path) -> None:
    env_path = tmp_path / "session-lease.env"
    env_path.write_text(
        "export SESSION_STREAM_PROCESS_ID=\"1234\"\nexport SESSION_STREAM_GENERATION='2'\nunrelated=value\n",
        encoding="utf-8",
    )

    assert codex_lane._read_lease_environment(env_path) == {
        "SESSION_STREAM_PROCESS_ID": "1234",
        "SESSION_STREAM_GENERATION": "2",
    }


@pytest.mark.parametrize(
    ("argv", "handler_name"),
    [
        (["bootstrap", "--epic", "Harness"], "cmd_bootstrap"),
        (["status", "--epic", "Harness"], "cmd_status"),
        (["hydrate", "--epic", "Harness"], "cmd_hydrate"),
        (["score", "--epic", "Harness", "--answers", "answers.json"], "cmd_score"),
    ],
)
def test_main_normalizes_epic_across_canary_subcommands(
    monkeypatch: pytest.MonkeyPatch, argv: list[str], handler_name: str
) -> None:
    observed: list[str] = []

    def record_epic(args: argparse.Namespace) -> int:
        observed.append(args.epic)
        return 0

    monkeypatch.setattr(codex_lane, handler_name, record_epic)

    assert codex_lane.main(argv) == 0
    assert observed == ["harness"]


def test_bootstrap_uses_normalized_epic_for_default_stream_id(tmp_path: Path) -> None:
    assert codex_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", " HARNESS "]) == 0

    board = (tmp_path / ".claude" / "harness-epic" / "CODEX-COLD-START.md").read_text(encoding="utf-8")
    from agents_extensions.shared.session_streams.inventory import stream_anchor_id

    infra_stream = stream_anchor_id("infra-harness", Path(__file__).resolve().parents[1])
    assert f"**Stream:** `{infra_stream}`" in board
    assert "none selected; start fresh and do not resume historical packets" in board
    assert "never invoke `codex resume`, `codex fork`" in board
    assert "launcher already minted the canary" in board
    assert "no Monitor-equivalent background capability" in board
    assert "never on compact count" in board


def test_bootstrap_uses_dedicated_devops_stream(tmp_path: Path) -> None:
    assert codex_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "devops"]) == 0

    board = (tmp_path / ".claude" / "devops-epic" / "CODEX-COLD-START.md").read_text(encoding="utf-8")
    assert "**Stream:** `epic:5703`" in board  # allow-hardcoded-epic: devops stream canary pin


def test_devops_alias_resolves_to_dedicated_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SESSION_STREAM_ID", raising=False)
    for selector in ("devops", "infra.devops"):
        assert (
            codex_lane._stream_id(argparse.Namespace(epic=selector, stream=None)) == "epic:5703"
        )  # allow-hardcoded-epic: devops launcher stream fixture


def test_bootstrap_records_exact_rollover_without_rendering_lease_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SESSION_STREAM_LEASE_ID", "lease-must-not-render")
    monkeypatch.setenv("CODEX_LAUNCHER_ROLLOVER_AGENT", "codex-infra")
    monkeypatch.setenv("CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID", "lineage-launcher-fresh")
    monkeypatch.setenv("CODEX_LAUNCHER_ROLLOVER_ID", "rollover-launcher-fresh")

    assert codex_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "infra"]) == 0

    board = (tmp_path / ".claude" / "infra-epic" / "CODEX-COLD-START.md").read_text(encoding="utf-8")
    assert "lineage-launcher-fresh" in board
    assert "rollover-launcher-fresh" in board
    assert "SessionStart must bind this task" in board
    assert "lease-must-not-render" not in board
    assert "credentials not rendered" in board


def test_bootstrap_rejects_partial_rollover_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID", "lineage-partial")
    monkeypatch.delenv("CODEX_LAUNCHER_ROLLOVER_AGENT", raising=False)
    monkeypatch.delenv("CODEX_LAUNCHER_ROLLOVER_ID", raising=False)

    assert codex_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "infra"]) == 2
    assert not (tmp_path / ".claude" / "infra-epic" / "CODEX-COLD-START.md").exists()


@pytest.mark.parametrize("lane_name", ["codex", "gemini", "glm"])
def test_hydrate_reports_retry_count_without_changing_capsule(monkeypatch, capsys, lane_name) -> None:
    import json

    from scripts.session_canary import gemini_lane, glm_lane

    lane = {"codex": codex_lane, "gemini": gemini_lane, "glm": glm_lane}[lane_name]
    capsule = {"execution_allowed": True}
    calls = []

    def retry(stream, identity):
        calls.append((stream, identity))
        return capsule, 2

    monkeypatch.delenv("SESSION_STREAM_AGENT", raising=False)
    monkeypatch.setattr(lane.shared_hydration, "build_hydration_capsule_with_retry", retry)
    assert lane.main(["hydrate", "--epic", "harness", "--stream", "epic:123"]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out.splitlines()[0]) == capsule
    assert output.err == "hydration_attempts: 2\n"
    assert calls == [("epic:123", lane._HOLDER_AGENT)]


@pytest.mark.parametrize("identity", ["codex", "codex-core", "codex-infra", "gemini"])
def test_hydrate_preserves_launcher_codex_identity(monkeypatch, capsys, identity) -> None:
    monkeypatch.setenv("SESSION_STREAM_AGENT", identity)
    observed = []

    def retry(stream, lane, **_):
        observed.append(lane)
        return {"execution_allowed": lane == identity}

    monkeypatch.setattr(codex_lane.shared_hydration, "build_hydration_capsule", retry)
    assert codex_lane.main(["hydrate", "--epic", "core", "--stream", "epic:123"]) == (2 if identity == "gemini" else 0)
    assert observed == ([] if identity == "gemini" else [identity])


@pytest.mark.parametrize("provider", ["codex", "gemini", "glm"])
@pytest.mark.parametrize("registration", ["registered", "removed", "prefix", "foreign", "empty"])
def test_hydrate_uses_exact_registered_provider_identity(monkeypatch, capsys, tmp_path, provider, registration) -> None:
    from scripts.orchestration import handoff_slot_registry
    from scripts.session_canary import gemini_lane, glm_lane

    lane = {"codex": codex_lane, "gemini": gemini_lane, "glm": glm_lane}[provider]
    # A local roster exercises GLM slots without changing live eligibility.
    roster = tmp_path / "area_assignments.yaml"
    roster.write_text(f"assignments:\n  core:\n    slots: [{provider}-core]\n", encoding="utf-8")
    monkeypatch.setattr(handoff_slot_registry._channels, "ASSIGNMENTS_PATH", roster)
    identity = {
        "registered": f"{provider}-core",
        "removed": f"{provider}-infra",
        "prefix": f"{provider}-core-forged",
        "foreign": "claude-core",
        "empty": "",
    }[registration]
    monkeypatch.setenv("SESSION_STREAM_AGENT", identity)
    calls = []

    def hydrate(stream, checked_identity):
        calls.append((stream, checked_identity))
        return {"execution_allowed": True}, 1

    monkeypatch.setattr(lane.shared_hydration, "build_hydration_capsule_with_retry", hydrate)
    rc = lane.main(["hydrate", "--epic", "core", "--stream", "epic:123"])
    output = capsys.readouterr()
    if registration == "registered":
        assert rc == 0
        assert calls == [("epic:123", identity)]
    else:
        assert rc == 2
        assert calls == []
        assert output.out == ""
        assert output.err == "ACTION: hydration blocked — unregistered lane identity for this provider.\n"


@pytest.mark.parametrize("provider", ["codex", "gemini", "glm"])
def test_hydrate_refuses_slot_when_registry_unavailable(monkeypatch, capsys, tmp_path, provider) -> None:
    from scripts.orchestration import handoff_slot_registry
    from scripts.session_canary import gemini_lane, glm_lane

    lane = {"codex": codex_lane, "gemini": gemini_lane, "glm": glm_lane}[provider]
    monkeypatch.setattr(handoff_slot_registry._channels, "ASSIGNMENTS_PATH", tmp_path / "missing.yaml")
    monkeypatch.setenv("SESSION_STREAM_AGENT", f"{provider}-core")
    monkeypatch.setattr(
        lane.shared_hydration,
        "build_hydration_capsule_with_retry",
        lambda *args: pytest.fail("unverified registration must not fetch or retry"),
    )
    assert lane.main(["hydrate", "--epic", "core", "--stream", "epic:123"]) == 2
    assert "unregistered lane identity" in capsys.readouterr().err


def test_cold_start_blocker_delta_policy():
    from scripts.driver_blockers import USAGE_RULE
    from scripts.session_canary import codex_lane

    body = codex_lane._cold_start_body(
        epic="infra",
        stream_id="epic:7919",
        handoff_rel="handoff.md",
        lease_summary="fixture",
        rollover_summary="none",
        binding_line="fixture",
    )
    assert USAGE_RULE.replace("$SESSION_EPIC", "infra") in body
    assert "exact case-sensitive standalone token RESOLVED <id>" in body
    assert "on its own non-active line (no other fields or prose)" in body
    assert body.count("scripts.driver_blockers delta") == 1
    assert body.count("scripts.driver_blockers record") == 1
