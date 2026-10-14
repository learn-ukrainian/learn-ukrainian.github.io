"""Regression coverage for the no-cost dispatch-lane self-test (#4879)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.agent_runtime import lane_probe
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.orchestration import handoff_slot_registry


class _FakeAdapter:
    name = "fake"
    supported_modes = frozenset({"read-only", "workspace-write"})

    def __init__(self, command: list[str]) -> None:
        self.command = command
        self.calls: list[dict[str, object]] = []

    def build_invocation(self, **kwargs: object) -> InvocationPlan:
        self.calls.append(kwargs)
        return InvocationPlan(cmd=self.command, cwd=Path(str(kwargs["cwd"])))


def _registered_lane(monkeypatch, name: str = "fake") -> None:
    monkeypatch.setitem(
        lane_probe.AGENTS,
        name,
        {
            "adapter": "tests.fake:Adapter",
            "default_model": None,
            "cost_tier": "low",
            "capabilities": frozenset(),
            "cli_available": True,
            "resume_policy": "never",
        },
    )


def test_probe_builds_adapter_then_runs_plain_binary_version(monkeypatch, tmp_path):
    _registered_lane(monkeypatch)
    adapter = _FakeAdapter(["fake-cli", "run", "ignored"])
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(lane_probe, "_load_adapter", lambda _agent: adapter)

    def fake_run(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(lane_probe.subprocess, "run", fake_run)

    result = lane_probe.probe_lane("fake", cwd=tmp_path, timeout_seconds=2)

    assert result["status"] == "healthy"
    assert adapter.calls[0]["mode"] == "read-only"
    assert calls[0]["command"] == ["fake-cli", "--version"]
    assert calls[0]["timeout"] == 2
    assert calls[0]["check"] is False
    assert calls[0]["stdin"] is lane_probe.subprocess.DEVNULL


def test_probe_keeps_npx_package_in_version_command(monkeypatch, tmp_path):
    _registered_lane(monkeypatch)
    adapter = _FakeAdapter(["npx", "@anthropic-ai/claude-code@latest", "-p", "ignored"])
    commands: list[list[str]] = []
    monkeypatch.setattr(lane_probe, "_load_adapter", lambda _agent: adapter)
    monkeypatch.setattr(
        lane_probe.subprocess,
        "run",
        lambda command, **_kwargs: commands.append(command) or SimpleNamespace(returncode=0),
    )

    result = lane_probe.probe_lane("fake", cwd=tmp_path)

    assert result["status"] == "healthy"
    assert commands == [["npx", "@anthropic-ai/claude-code@latest", "--version"]]


def test_probe_reports_build_failure_without_running_a_command(monkeypatch, tmp_path):
    _registered_lane(monkeypatch)

    class FailingAdapter(_FakeAdapter):
        def build_invocation(self, **kwargs: object) -> InvocationPlan:
            raise RuntimeError("broken adapter")

    monkeypatch.setattr(lane_probe, "_load_adapter", lambda _agent: FailingAdapter([]))
    monkeypatch.setattr(lane_probe.subprocess, "run", lambda *_args, **_kwargs: AssertionError("must not run"))

    result = lane_probe.probe_lane("fake", cwd=tmp_path)

    assert result["status"] == "unhealthy"
    assert result["reason"] == "RuntimeError while building or spawning the adapter"


def test_probe_reports_nonzero_version_exit(monkeypatch, tmp_path):
    _registered_lane(monkeypatch)
    monkeypatch.setattr(lane_probe, "_load_adapter", lambda _agent: _FakeAdapter(["fake-cli"]))
    monkeypatch.setattr(lane_probe.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=23))

    result = lane_probe.probe_lane("fake", cwd=tmp_path)

    assert result["status"] == "unhealthy"
    assert result["reason"] == "version command exited 23"


def test_unknown_executable_lane_remains_unhealthy(tmp_path):
    result = lane_probe.probe_lane("codex-atlas", cwd=tmp_path)

    assert result["status"] == "unhealthy"
    assert result["reason"] == "agent is not registered"


def test_probe_uses_write_mode_for_kimi_without_executing_a_prompt(monkeypatch, tmp_path):
    _registered_lane(monkeypatch, "kimi")
    adapter = _FakeAdapter(["kimi", "-p", "ignored"])
    adapter.name = "kimi"
    adapter.supported_modes = frozenset({"workspace-write"})  # the Kimi adapters admit nothing else
    monkeypatch.setattr(lane_probe, "_load_adapter", lambda _agent: adapter)
    monkeypatch.setattr(lane_probe.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=0))

    result = lane_probe.probe_lane("kimi", cwd=tmp_path)

    assert result["status"] == "healthy"
    assert adapter.calls[0]["mode"] == "workspace-write"


def test_disabled_lane_is_reported_as_skipped(monkeypatch, tmp_path):
    monkeypatch.setitem(
        lane_probe.AGENTS,
        "disabled",
        {
            "adapter": "tests.fake:Adapter",
            "default_model": None,
            "cost_tier": "low",
            "capabilities": frozenset(),
            "cli_available": False,
            "resume_policy": "never",
        },
    )
    monkeypatch.setattr(lane_probe, "_load_adapter", lambda _agent: AssertionError("must not load"))

    result = lane_probe.probe_lane("disabled", cwd=tmp_path)

    assert result["status"] == "skipped"
    assert result["reason"] == "lane is disabled in the runtime registry"
    assert isinstance(result["duration_ms"], int)


def test_probe_removes_codex_temp_output_created_by_synthetic_plan(monkeypatch, tmp_path):
    _registered_lane(monkeypatch)
    output_file = tmp_path / "codex-runtime-lane-health-probe-123.txt"
    output_file.write_text("synthetic", encoding="utf-8")
    adapter = _FakeAdapter(["fake-cli"])

    def build_with_output(**kwargs: object) -> InvocationPlan:
        return InvocationPlan(cmd=adapter.command, cwd=Path(str(kwargs["cwd"])), output_file=output_file)

    monkeypatch.setattr(adapter, "build_invocation", build_with_output)
    monkeypatch.setattr(lane_probe, "_load_adapter", lambda _agent: adapter)
    monkeypatch.setattr(lane_probe.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=0))
    monkeypatch.setattr(lane_probe.tempfile, "gettempdir", lambda: str(tmp_path))

    result = lane_probe.probe_lane("fake", cwd=tmp_path)

    assert result["status"] == "healthy"
    assert not output_file.exists()


def test_session_start_wires_the_active_lane_probe() -> None:
    hook = Path("agents_extensions/shared/hooks/session-setup.sh").read_text(encoding="utf-8")

    assert "scripts.agent_runtime.lane_probe" in hook
    assert '--handoff-agent "$HANDOFF_AGENT"' in hook
    assert 'HANDOFF_AGENT="$SESSION_HANDOFF_AGENT"' in hook
    assert "--timeout 2" in hook


def test_handoff_resolution_covers_registry_and_area_lanes(monkeypatch, tmp_path):
    areas = yaml.safe_load(Path("scripts/config/area_assignments.yaml").read_text())["assignments"]
    slots = {slot for area in areas.values() for slot in area["slots"]}
    # #10511 registers the held muse runtime seat, so its launcher slots resolve to it.
    launcher_only: set[str] = set()
    assert {slot for slot in slots if slot.split("-", 1)[0] not in lane_probe.AGENTS} == launcher_only
    assert {lane_probe.resolve_handoff_agent(slot) for slot in ("muse-devops", "muse-monitor")} == {"muse"}
    for slot in slots:
        provider = slot.split("-", 1)[0]
        assert lane_probe.resolve_handoff_agent(slot) == (slot if slot in launcher_only else provider)
    for provider in lane_probe.AGENTS:
        if "-" not in provider:
            for area, assignment in areas.items():
                if assignment["slots"]:
                    continue
                assert lane_probe.resolve_handoff_agent(f"{provider}-{area}") == provider
    _registered_lane(monkeypatch, "new-provider")
    # A runtime key with a hyphen still resolves its explicitly registered slot
    # in a mixed roster. It cannot acquire another provider's monitor alias.
    areas["monitor"]["slots"].append("new-provider-monitor")
    roster = tmp_path / "area_assignments.yaml"
    roster.write_text(yaml.safe_dump({"assignments": areas}), encoding="utf-8")
    monkeypatch.setattr(handoff_slot_registry._channels, "ASSIGNMENTS_PATH", roster)
    assert lane_probe.resolve_handoff_agent("new-provider-monitor") == "new-provider"
    assert lane_probe.resolve_handoff_agent("new-provider-new-lane") == "new-provider-new-lane"
    assert lane_probe.resolve_handoff_agent("unknown-lane") == "unknown-lane"
    assert lane_probe.resolve_handoff_agent("claude") == "claude"


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini", "grok", "kimi", "cursor"])
@pytest.mark.parametrize("returncode", [0, 23])
def test_legacy_monitor_cli_probes_its_runtime_provider(monkeypatch, tmp_path, capsys, provider, returncode):
    loaded = []
    commands = []
    adapter = _FakeAdapter(["fixture-cli"])
    monkeypatch.setattr(lane_probe, "_load_adapter", lambda agent: loaded.append(agent) or adapter)

    def version(command, **_kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(lane_probe, "run_version_probe", version)
    assert lane_probe.resolve_handoff_agent(f"{provider}-monitor") == provider
    assert lane_probe.main(["--handoff-agent", f"{provider}-monitor", "--cwd", str(tmp_path)]) == bool(returncode)
    payload = json.loads(capsys.readouterr().out)
    assert loaded == [provider]
    assert commands == [["fixture-cli"]]
    assert payload["probes"][0]["agent"] == provider
    assert payload["probes"][0]["status"] == ("unhealthy" if returncode else "healthy")
    assert payload["summary"] == {"healthy": int(not returncode), "unhealthy": int(bool(returncode)), "skipped": 0}


@pytest.mark.parametrize("selection", ["--agent", "--handoff-agent"])
@pytest.mark.parametrize(
    "identity, reason",
    [
        ("muse-devops", "registered handoff slot has no runtime adapter"),
        ("muse-monitor", "registered handoff slot has no runtime adapter"),
        ("muse", "agent is not registered"),
        ("unknown-monitor", "agent is not registered"),
        ("unknown-devops", "agent is not registered"),
    ],
)
def test_launcher_only_and_unknown_slots_fail_closed(monkeypatch, tmp_path, capsys, selection, identity, reason):
    def unexpected(*_args, **_kwargs):
        pytest.fail("an unavailable runtime must not load an adapter or execute a version probe")

    # Registered slots without a runtime seat stay launcher-only (the pre-#10511 roster).
    monkeypatch.delitem(lane_probe.AGENTS, "muse")
    monkeypatch.setattr(lane_probe, "_load_adapter", unexpected)
    monkeypatch.setattr(lane_probe, "run_version_probe", unexpected)
    assert "muse" not in lane_probe.AGENTS
    assert lane_probe.resolve_handoff_agent(identity) == identity
    assert lane_probe.main([selection, identity, "--cwd", str(tmp_path)]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"] == {"healthy": 0, "unhealthy": 1, "skipped": 0}
    probe = payload["probes"][0]
    assert probe["agent"] == identity
    assert probe["status"] == "unhealthy"
    assert probe["reason"] == reason


@pytest.mark.parametrize("identity", ["claude-", "claude-typo-lane", "CLAUDE-infra", "claudex-infra", "kimi-folk"])
def test_handoff_cli_rejects_unmintable_identity(monkeypatch, tmp_path, capsys, identity):
    def unexpected_adapter(_agent):
        pytest.fail("an unmintable identity must not probe a provider")

    monkeypatch.setattr(lane_probe, "_load_adapter", unexpected_adapter)
    assert lane_probe.main(["--handoff-agent", identity, "--cwd", str(tmp_path)]) == 1
    probe = json.loads(capsys.readouterr().out)["probes"][0]
    assert probe["agent"] == identity
    assert probe["status"] == "unhealthy"
    assert probe["reason"] == "agent is not registered"


@pytest.mark.parametrize("returncode", [0, 23])
def test_handoff_cli_probes_provider_and_preserves_broken_lane(monkeypatch, tmp_path, capsys, returncode):
    adapter = _FakeAdapter(["fake-claude"])
    loaded = []
    monkeypatch.setattr(lane_probe, "_load_adapter", lambda agent: loaded.append(agent) or adapter)
    monkeypatch.setattr(lane_probe.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=returncode))
    assert lane_probe.main(["--handoff-agent", "claude-open-model-data", "--cwd", str(tmp_path)]) == bool(returncode)
    probe = json.loads(capsys.readouterr().out)["probes"][0]
    assert loaded == ["claude"]
    assert probe["agent"] == "claude"
    assert probe["status"] == ("unhealthy" if returncode else "healthy")
    if returncode:
        assert probe["reason"] == "version command exited 23"


@pytest.mark.parametrize("selection", ["--agent", "--handoff-agent"])
@pytest.mark.parametrize("identity", ["muse", "muse-devops", "muse-monitor"])
def test_held_muse_runtime_fails_closed_without_version_probe(monkeypatch, tmp_path, capsys, selection, identity):
    """#10511: the held seat loads its adapter, which refuses before argv or any process."""

    def unexpected(*_args, **_kwargs):
        pytest.fail("a held runtime must not execute a version probe")

    monkeypatch.setattr(lane_probe, "run_version_probe", unexpected)
    if selection == "--handoff-agent" or identity == "muse":
        assert lane_probe.resolve_handoff_agent(identity) == "muse"
    assert lane_probe.main([selection, identity, "--cwd", str(tmp_path)]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"] == {"healthy": 0, "unhealthy": 1, "skipped": 0}
    probe = payload["probes"][0]
    expected = "muse" if selection == "--handoff-agent" else identity
    assert probe["agent"] == expected and probe["status"] == "unhealthy"
    if expected == "muse":
        assert probe["reason"] == "MuseGuardParityRefused while building or spawning the adapter"
    else:
        assert probe["reason"] == "agent is not registered"
    assert list(tmp_path.iterdir()) == []
