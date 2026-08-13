"""Hermes bridge and Entire fleet-capture lifecycle tests."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.errors import AgentUnavailableError
from scripts.agent_runtime.result import ParseResult, Result
from scripts.ai_agent_bridge._hermes import HERMES_DEFAULT_MODEL, _invoke_hermes
from scripts.entire import cursor_native_hook_shim as shim
from scripts.entire import fleet_capture as capture


def _repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    return root.resolve()


def test_status_paths_preserves_both_sides_of_nul_terminated_renames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = (
        b"R  new/location.py\0old/location.py\0"
        b" C copied/to.py\0copied/from.py\0"
        b" M ordinary.py\0?? untracked.py\0"
        b"?? batch_state/entire/private-spool.jsonl\0"
    )
    monkeypatch.setattr(
        capture.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=output),
    )

    assert capture._status_paths(tmp_path) == {
        "new/location.py",
        "old/location.py",
        "copied/to.py",
        "copied/from.py",
        "ordinary.py",
        "untracked.py",
    }


def _cursor_base(home: Path, root: Path) -> Path:
    project = shim._cursor_project_name(root)
    base = home / ".cursor" / "projects" / project / "agent-transcripts"
    base.mkdir(parents=True)
    return base


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/a//b/.worktrees/dispatch", "a-b-worktrees-dispatch"),
        ("///Users/operator/repo///", "Users-operator-repo"),
        ("/a/.-_ b/c", "a-b-c"),
    ],
)
def test_project_name_uses_current_cursor_separator_contract(
    raw: str, expected: str
) -> None:
    assert shim._cursor_project_name(Path(raw)) == expected


def test_project_name_matches_runtime_cursor_adapter() -> None:
    from scripts.agent_runtime.adapters.cursor import CursorAdapter

    for raw in (
        "/Users/operator/repo",
        "/Users/operator/repo/.worktrees/dispatch/codex/canary",
        "/private/tmp/a  b/repo",
    ):
        assert shim._cursor_project_name(Path(raw)) == CursorAdapter()._encode_workspace_path(raw)


def _patch_git_root(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    real_run = subprocess.run

    def fake_run(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=f"{root}\n")
        return real_run(command, **kwargs)

    monkeypatch.setattr(shim.subprocess, "run", fake_run)


def _native_hooks(*, extra: dict[str, object] | None = None) -> dict[str, object]:
    hooks: dict[str, object] = {
        name: [{"command": command}] for name, command in shim._STOCK_COMMANDS.items()
    }
    hooks["sessionStart"].append({"command": "operator-session-hook"})
    return {"version": 1, "custom": extra or {"preserved": True}, "hooks": hooks}


def test_nonempty_transcript_path_passes_original_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo_root(tmp_path)
    _patch_git_root(monkeypatch, root)
    raw = b'{ "conversation_id": "fixture", "transcript_path": "/native/path" }\n'
    normalized, resolved_root = shim._normalize(raw, cwd=root, home=tmp_path / "home")
    assert normalized == raw
    assert resolved_root == root


@pytest.mark.parametrize("missing", [None, ""])
def test_missing_path_resolves_nested_before_flat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str | None
) -> None:
    root = _repo_root(tmp_path)
    home = tmp_path / "home"
    base = _cursor_base(home, root)
    nested = base / "session-1" / "session-1.jsonl"
    nested.parent.mkdir()
    nested.write_bytes(b"not-read")
    (base / "session-1.jsonl").write_bytes(b"not-read-either")
    _patch_git_root(monkeypatch, root)
    payload = {
        "conversation_id": "session-1",
        "transcript_path": missing,
        "workspace_roots": [str(root)],
    }
    normalized, _ = shim._normalize(json.dumps(payload).encode(), cwd=root, home=home)
    assert json.loads(normalized)["transcript_path"] == str(nested.resolve())


def test_existing_nested_directory_authorizes_future_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo_root(tmp_path)
    home = tmp_path / "home"
    base = _cursor_base(home, root)
    nested = base / "session-2"
    nested.mkdir()
    _patch_git_root(monkeypatch, root)
    payload = {"conversation_id": "session-2", "workspace_roots": [str(root)]}
    normalized, _ = shim._normalize(json.dumps(payload).encode(), cwd=root, home=home)
    assert json.loads(normalized)["transcript_path"] == str(nested / "session-2.jsonl")


def test_current_collapsed_base_wins_and_legacy_base_is_never_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo" / ".worktrees" / "dispatch"
    root.mkdir(parents=True)
    root = root.resolve()
    home = tmp_path / "home"
    current = _cursor_base(home, root)
    current_nested = current / "session-current"
    current_nested.mkdir()
    legacy_name = re.sub(r"[^a-zA-Z0-9]", "-", str(root).lstrip("/"))
    legacy = home / ".cursor" / "projects" / legacy_name / "agent-transcripts"
    legacy_nested = legacy / "session-current"
    legacy_nested.mkdir(parents=True)
    _patch_git_root(monkeypatch, root)
    normalized, _ = shim._normalize(
        json.dumps(
            {"conversation_id": "session-current", "workspace_roots": [str(root)]}
        ).encode(),
        cwd=root,
        home=home,
    )
    assert json.loads(normalized)["transcript_path"] == str(
        current_nested / "session-current.jsonl"
    )
    legacy.rename(home / ".cursor" / "projects" / "legacy-not-consulted")


def test_legacy_only_base_is_not_a_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo" / ".worktrees" / "dispatch"
    root.mkdir(parents=True)
    root = root.resolve()
    home = tmp_path / "home"
    legacy_name = re.sub(r"[^a-zA-Z0-9]", "-", str(root).lstrip("/"))
    legacy = home / ".cursor" / "projects" / legacy_name / "agent-transcripts"
    (legacy / "session-legacy").mkdir(parents=True)
    _patch_git_root(monkeypatch, root)
    with pytest.raises(FileNotFoundError):
        shim._normalize(
            json.dumps(
                {"conversation_id": "session-legacy", "workspace_roots": [str(root)]}
            ).encode(),
            cwd=root,
            home=home,
        )


def test_flat_path_is_used_without_nested_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo_root(tmp_path)
    home = tmp_path / "home"
    base = _cursor_base(home, root)
    flat = base / "session-3.jsonl"
    flat.write_bytes(b"not-read")
    _patch_git_root(monkeypatch, root)
    payload = {"conversation_id": "session-3", "workspace_roots": [str(root)]}
    normalized, _ = shim._normalize(json.dumps(payload).encode(), cwd=root, home=home)
    assert json.loads(normalized)["transcript_path"] == str(flat.resolve())


@pytest.mark.parametrize("conversation_id", ["../escape", "a/b", "a\\b", ".", "..", ""])
def test_unsafe_conversation_id_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, conversation_id: str
) -> None:
    root = _repo_root(tmp_path)
    home = tmp_path / "home"
    _cursor_base(home, root)
    _patch_git_root(monkeypatch, root)
    with pytest.raises(ValueError):
        shim._normalize(
            json.dumps({"conversation_id": conversation_id}).encode(),
            cwd=root,
            home=home,
        )


def test_workspace_mismatch_and_symlink_escape_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo_root(tmp_path)
    home = tmp_path / "home"
    base = _cursor_base(home, root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (base / "session-4").symlink_to(outside, target_is_directory=True)
    _patch_git_root(monkeypatch, root)
    with pytest.raises(ValueError):
        shim._normalize(
            json.dumps(
                {"conversation_id": "session-4", "workspace_roots": [str(root)]}
            ).encode(),
            cwd=root,
            home=home,
        )
    with pytest.raises(ValueError):
        shim._normalize(
            json.dumps(
                {"conversation_id": "session-5", "workspace_roots": [str(outside)]}
            ).encode(),
            cwd=root,
            home=home,
        )


@pytest.mark.parametrize("verb", ["before-submit-prompt", "stop"])
def test_hook_delegates_exact_normalized_payload_without_reading_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, verb: str
) -> None:
    root = _repo_root(tmp_path)
    home = tmp_path / "home"
    base = _cursor_base(home, root)
    nested = base / "session-6"
    nested.mkdir()
    _patch_git_root(monkeypatch, root)
    calls: list[tuple[list[str], dict[str, object]]] = []
    monkeypatch.setattr(shim.Path, "home", lambda: home)
    monkeypatch.setattr(shim.Path, "cwd", lambda: root)
    monkeypatch.setattr(shim.shutil, "which", lambda _name: "/fake/entire")
    monkeypatch.setattr(
        shim.sys,
        "stdin",
        SimpleNamespace(
            buffer=SimpleNamespace(
                read=lambda _limit: json.dumps(
                    {
                        "conversation_id": "session-6",
                        "workspace_roots": [str(root)],
                        "prompt": "preserved prompt",
                    }
                ).encode()
            )
        ),
    )

    def fake_run(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=f"{root}\n")
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(shim.subprocess, "run", fake_run)
    assert shim._hook(verb) == 0
    assert calls[0][0] == ["/fake/entire", "hooks", "cursor", verb]
    delegated = json.loads(calls[0][1]["input"])
    assert delegated["transcript_path"] == str(
        nested / "session-6.jsonl"
    )
    assert delegated["prompt"] == "preserved prompt"
    assert calls[0][1]["cwd"] == root


def test_session_start_without_candidate_makes_no_entire_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo_root(tmp_path)
    home = tmp_path / "home"
    _cursor_base(home, root)
    calls: list[list[str]] = []
    monkeypatch.setattr(shim.Path, "home", lambda: home)
    monkeypatch.setattr(shim.Path, "cwd", lambda: root)
    monkeypatch.setattr(shim.shutil, "which", lambda _name: "/fake/entire")
    monkeypatch.setattr(
        shim.sys,
        "stdin",
        SimpleNamespace(
            buffer=SimpleNamespace(
                read=lambda _limit: json.dumps(
                    {"conversation_id": "not-created", "workspace_roots": [str(root)]}
                ).encode()
            )
        ),
    )

    def fake_run(command, **_kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=f"{root}\n")
        calls.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(shim.subprocess, "run", fake_run)
    assert shim._hook("session-start") == 0
    assert calls == []


@pytest.mark.parametrize("verb", ["session-start", "before-submit-prompt", "stop"])
def test_fleet_owner_fence_exits_before_reading_or_invoking(
    monkeypatch: pytest.MonkeyPatch, verb: str
) -> None:
    class Unreadable:
        def read(self, _limit):
            raise AssertionError("fleet-owned headless hook read stdin")

    monkeypatch.setenv("LU_ENTIRE_CAPTURE_OWNER", "fleet")
    monkeypatch.setattr(shim.sys, "stdin", SimpleNamespace(buffer=Unreadable()))
    monkeypatch.setattr(
        shim.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("fleet-owned headless hook invoked Entire")
        ),
    )
    assert shim._hook(verb) == 0


def test_repeated_turns_delegate_without_synthetic_session_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo_root(tmp_path)
    home = tmp_path / "home"
    nested = _cursor_base(home, root) / "session-repeat"
    nested.mkdir()
    _patch_git_root(monkeypatch, root)
    raw = json.dumps(
        {
            "conversation_id": "session-repeat",
            "workspace_roots": [str(root)],
            "prompt": "same identity",
        }
    ).encode()
    calls: list[list[str]] = []
    monkeypatch.setattr(shim.Path, "home", lambda: home)
    monkeypatch.setattr(shim.Path, "cwd", lambda: root)
    monkeypatch.setattr(shim.shutil, "which", lambda _name: "/fake/entire")
    monkeypatch.setattr(
        shim.sys, "stdin", SimpleNamespace(buffer=SimpleNamespace(read=lambda _limit: raw))
    )

    def fake_run(command, **_kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=f"{root}\n")
        calls.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(shim.subprocess, "run", fake_run)
    assert shim._hook("before-submit-prompt") == 0
    assert shim._hook("before-submit-prompt") == 0
    assert calls == [
        ["/fake/entire", "hooks", "cursor", "before-submit-prompt"],
        ["/fake/entire", "hooks", "cursor", "before-submit-prompt"],
    ]


def test_nonempty_stop_payload_is_delegated_byte_for_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo_root(tmp_path)
    raw = b'{ "conversation_id": "native-stop", "transcript_path": "/native/path" }\n'
    calls: list[bytes] = []
    monkeypatch.setattr(shim.Path, "home", lambda: tmp_path / "home")
    monkeypatch.setattr(shim.Path, "cwd", lambda: root)
    monkeypatch.setattr(shim.shutil, "which", lambda _name: "/fake/entire")
    monkeypatch.setattr(
        shim.sys, "stdin", SimpleNamespace(buffer=SimpleNamespace(read=lambda _limit: raw))
    )

    def fake_run(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=f"{root}\n")
        calls.append(kwargs["input"])
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(shim.subprocess, "run", fake_run)
    assert shim._hook("stop") == 0
    assert calls == [raw]


def test_missing_entire_is_silent_and_fail_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo_root(tmp_path)
    monkeypatch.setattr(
        shim.sys, "stdin", SimpleNamespace(
            buffer=SimpleNamespace(
                read=lambda _limit: b'{"conversation_id":"x","transcript_path":"/native"}'
            )
        )
    )
    monkeypatch.setattr(shim.Path, "cwd", lambda: root)
    monkeypatch.setattr(shim.shutil, "which", lambda _name: None)
    _patch_git_root(monkeypatch, root)
    assert shim._hook("before-submit-prompt") == 0


@pytest.mark.parametrize(
    "failure",
    [FileNotFoundError(), subprocess.TimeoutExpired("entire", 1)],
)
def test_entire_process_failures_are_silent_and_fail_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    root = _repo_root(tmp_path)
    raw = b'{"conversation_id":"x","transcript_path":"/native"}'
    monkeypatch.setattr(
        shim.sys, "stdin", SimpleNamespace(buffer=SimpleNamespace(read=lambda _limit: raw))
    )
    monkeypatch.setattr(shim.Path, "cwd", lambda: root)
    monkeypatch.setattr(shim.shutil, "which", lambda _name: "/fake/entire")

    def fake_run(command, **_kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=f"{root}\n")
        raise failure

    monkeypatch.setattr(shim.subprocess, "run", fake_run)
    assert shim._hook("before-submit-prompt") == 0


@pytest.mark.parametrize(
    "raw",
    [b"not-json", b"x" * ((1 << 20) + 1)],
    ids=["malformed", "oversized"],
)
def test_malformed_or_oversized_input_is_silent_and_fail_open(
    monkeypatch: pytest.MonkeyPatch, raw: bytes
) -> None:
    monkeypatch.setattr(
        shim.sys, "stdin", SimpleNamespace(buffer=SimpleNamespace(read=lambda _limit: raw))
    )
    assert shim._hook("stop") == 0


def test_install_uninstall_are_atomic_idempotent_and_preserve_config(tmp_path: Path) -> None:
    path = tmp_path / "hooks.json"
    expected = _native_hooks(extra={"operator": [1, 2, 3]})
    path.write_text(json.dumps(expected), encoding="utf-8")
    assert shim._reconcile(path, "install") is True
    installed = json.loads(path.read_text(encoding="utf-8"))
    assert installed["custom"] == {"operator": [1, 2, 3]}
    for hook_name, command in shim._MANAGED_COMMANDS.items():
        assert installed["hooks"][hook_name][0]["command"] == command
    assert installed["hooks"]["sessionStart"][1]["command"] == "operator-session-hook"
    for hook_name in set(shim._STOCK_COMMANDS) - set(shim._MANAGED_HOOKS):
        assert installed["hooks"][hook_name][0]["command"] == shim._STOCK_COMMANDS[
            hook_name
        ]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert shim._reconcile(path, "install") is False
    assert shim._reconcile(path, "check") is False
    assert shim._reconcile(path, "uninstall") is True
    restored = json.loads(path.read_text())
    for hook_name in shim._MANAGED_HOOKS:
        assert restored["hooks"][hook_name][0]["command"] == shim._STOCK_COMMANDS[hook_name]
    assert shim._reconcile(path, "uninstall") is False


@pytest.mark.parametrize("drift", ["missing", "duplicate", "both"])
def test_reconciliation_rejects_ambiguous_session_start(tmp_path: Path, drift: str) -> None:
    path = tmp_path / "hooks.json"
    parsed = _native_hooks()
    entries = parsed["hooks"]["sessionStart"]
    if drift == "missing":
        entries.pop(0)
    elif drift == "duplicate":
        entries.insert(0, {"command": shim._STOCK_COMMANDS["sessionStart"]})
    else:
        entries.insert(0, {"command": shim._MANAGED_COMMANDS["sessionStart"]})
    path.write_text(json.dumps(parsed), encoding="utf-8")
    with pytest.raises(shim.ReconciliationError):
        shim._reconcile(path, "install")


def test_reconciliation_rejects_mixed_target_state(tmp_path: Path) -> None:
    path = tmp_path / "hooks.json"
    parsed = _native_hooks()
    parsed["hooks"]["sessionStart"][0]["command"] = shim._MANAGED_COMMANDS[
        "sessionStart"
    ]
    path.write_text(json.dumps(parsed), encoding="utf-8")
    with pytest.raises(shim.ReconciliationError, match="mixed"):
        shim._reconcile(path, "install")


def _fake_run(hooks: list[tuple[str, dict[str, object]]]):
    def run(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=b"")
        assert Path(kwargs["cwd"]) == Path(kwargs["env"]["ENTIRE_REPO_ROOT"])
        payload = json.loads(kwargs["input"])
        hooks.append((command[-1], payload))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return run


def test_exact_owned_host_lifecycle_is_private_and_ephemeral(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hooks: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(capture.shutil, "which", lambda name: "/fake/entire")
    monkeypatch.setattr(capture.subprocess, "run", _fake_run(hooks))

    fleet = capture.FleetCapture.start(
        host_harness="hermes",
        runner_agent="deepseek",
        entrypoint="bridge",
        requested_model="deepseek-v4-flash",
        prompt="private-prompt-canary",
        repo_path=tmp_path,
        runtime_repo_root=tmp_path,
        plan_metadata={
            "hermes": {
                "requested_provider": "deepseek",
                "requested_model": "deepseek-v4-flash",
            }
        },
    )
    assert fleet is not None
    assert stat.S_IMODE(fleet.root.stat().st_mode) == 0o700
    assert stat.S_IMODE(fleet.session_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(fleet.transcript_path.stat().st_mode) == 0o600
    assert [name for name, _ in hooks] == ["session-start", "turn-start"]
    assert "private-prompt-canary" not in json.dumps(hooks[0][1]["raw_data"])
    assert hooks[1][1]["user_prompt"] == "private-prompt-canary"

    fleet.finish(
        response="private-response-canary",
        outcome="ok",
        returncode=0,
        actual_model="deepseek-v4.1",
        route_metadata={"actual_provider": "deepseek"},
    )
    assert [name for name, _ in hooks] == [
        "session-start",
        "turn-start",
        "turn-end",
        "session-end",
    ]
    assert not fleet.session_dir.exists()
    for name, payload in hooks:
        if name != "turn-start":
            assert "private-prompt-canary" not in json.dumps(payload["raw_data"])
        assert "private-response-canary" not in json.dumps(payload["raw_data"])


@pytest.mark.parametrize("host", [None, "", "codex", "claude-code", "opencode", "cursor", "kimi"])
def test_native_or_unowned_hosts_are_never_duplicated(tmp_path: Path, host: str | None) -> None:
    assert capture.FleetCapture.start(
        host_harness=host,
        runner_agent="fixture",
        entrypoint="runtime",
        requested_model="fixture",
        prompt="fixture",
        repo_path=tmp_path,
        runtime_repo_root=tmp_path,
    ) is None


def test_missing_entire_cli_has_no_spool_side_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(capture.shutil, "which", lambda _name: None)
    assert capture.FleetCapture.start(
        host_harness="hermes",
        runner_agent="deepseek",
        entrypoint="dispatch",
        requested_model="deepseek-v4-flash",
        prompt="fixture",
        repo_path=tmp_path,
        runtime_repo_root=tmp_path,
    ) is None
    assert not capture._capture_root(tmp_path).exists()


def test_cursor_headless_is_owned_without_claiming_native_cursor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hooks: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(capture.shutil, "which", lambda _name: "/fake/entire")
    monkeypatch.setattr(capture.subprocess, "run", _fake_run(hooks))
    fleet = capture.FleetCapture.start(
        host_harness="cursor-headless",
        runner_agent="cursor",
        entrypoint="dispatch",
        requested_model="auto",
        prompt="private cursor prompt",
        repo_path=tmp_path,
        runtime_repo_root=tmp_path,
        plan_metadata={
            "entire_fleet": {
                "requested_model": "auto",
                "actual_model_known": "false",
            }
        },
    )
    assert fleet is not None
    actual, route = capture.resolved_route(
        requested_model="auto",
        plan_metadata={
            "entire_fleet": {
                "requested_model": "auto",
                "actual_model_known": "false",
            }
        },
        substitution=None,
    )
    assert actual == ""
    assert route == {
        "requested_model": "auto",
        "actual_model": "",
        "actual_model_known": "false",
    }
    fleet.finish(
        response="private cursor response",
        outcome="ok",
        returncode=0,
        actual_model=actual,
        route_metadata=route,
    )
    terminal_raw = hooks[-1][1]["raw_data"]
    assert terminal_raw["harness"] == "cursor-headless"
    assert terminal_raw["runner_agent"] == "cursor"
    assert terminal_raw["requested_model"] == "auto"
    assert terminal_raw["actual_model_known"] == "false"
    assert "actual_model" not in terminal_raw
    assert "private cursor prompt" not in json.dumps(terminal_raw)
    assert "private cursor response" not in json.dumps(terminal_raw)


def test_cursor_adapter_marks_only_headless_runner_for_fleet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.agent_runtime.adapters.cursor import CursorAdapter

    monkeypatch.setattr("shutil.which", lambda _name: "/fake/cursor-agent")
    for mode in ("read-only", "workspace-write", "danger"):
        plan = CursorAdapter().build_invocation(
            prompt="fixture",
            mode=mode,
            cwd=tmp_path,
            model="auto",
            task_id="cursor-headless-fixture",
            session_id=None,
            tool_config={},
        )
        assert "-p" in plan.cmd
        assert plan.host_harness == "cursor-headless"
        assert plan.env_overrides == {"LU_ENTIRE_CAPTURE_OWNER": "fleet"}
        assert plan.metadata["entire_fleet"] == {
            "requested_model": "auto",
            "actual_model_known": "false",
        }


def test_entire_outage_is_fail_open_and_spool_is_cleaned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def timed_out(command, **kwargs):
        if command[0] == "git":
            return SimpleNamespace(returncode=0, stdout=b"")
        raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 1))

    monkeypatch.setattr(capture.shutil, "which", lambda name: "/fake/entire")
    monkeypatch.setattr(capture.subprocess, "run", timed_out)
    fleet = capture.FleetCapture.start(
        host_harness="agy",
        runner_agent="agy",
        entrypoint="dispatch",
        requested_model="gemini-3.6-flash-high",
        prompt="fixture",
        repo_path=tmp_path,
        runtime_repo_root=tmp_path,
    )
    assert fleet is not None
    fleet.finish(response="provider result", outcome="ok", returncode=0)
    assert not fleet.session_dir.exists()


def test_start_failure_cleans_private_spool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(capture.shutil, "which", lambda _name: "/fake/entire")
    monkeypatch.setattr(capture, "_atomic_jsonl", lambda *_args: (_ for _ in ()).throw(OSError()))

    with pytest.raises(OSError):
        capture.FleetCapture.start(
            host_harness="grok",
            runner_agent="grok-build",
            entrypoint="bridge",
            requested_model="grok-4.5",
            prompt="fixture",
            repo_path=tmp_path,
            runtime_repo_root=tmp_path,
        )

    root = capture._capture_root(tmp_path)
    assert not list(root.glob("fleet-*"))


def test_stale_cleanup_removes_only_exact_session_directories(tmp_path: Path) -> None:
    valid = tmp_path / "fleet-0123456789abcdef0123456789abcdef"
    unrelated = tmp_path / "operator-files"
    malformed = tmp_path / "fleet-not-a-session"
    for directory in (valid, unrelated, malformed):
        directory.mkdir()
        os.utime(directory, (0, 0))
    capture._cleanup_stale(tmp_path, now=capture._STALE_SECONDS + 1)
    assert not valid.exists()
    assert unrelated.exists()
    assert malformed.exists()


def test_resolved_route_preserves_truthful_substitution() -> None:
    actual, metadata = capture.resolved_route(
        requested_model="deepseek-v4-flash",
        plan_metadata={
            "hermes": {
                "requested_provider": "deepseek",
                "requested_model": "deepseek-v4-flash",
            }
        },
        substitution={
            "requested_provider": "deepseek",
            "requested_model": "deepseek-v4-flash",
            "actual_provider": "openrouter",
            "actual_model": "deepseek/deepseek-v4.1",
        },
    )
    assert actual == "deepseek/deepseek-v4.1"
    assert metadata == {
        "requested_provider": "deepseek",
        "requested_model": "deepseek-v4-flash",
        "actual_provider": "openrouter",
        "actual_model": "deepseek/deepseek-v4.1",
    }


def test_runner_starts_after_spawn_and_always_finishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from agent_runtime import runner as runtime_runner

    events: list[tuple[str, dict[str, object]]] = []

    class FakeCapture:
        @classmethod
        def start(cls, **kwargs):
            events.append(("start", kwargs))
            return cls()

        def finish(self, **kwargs):
            events.append(("finish", kwargs))

    class Adapter:
        def liveness_signal_paths(self, _plan):
            return ()

        def parse_response(self, **_kwargs):
            return ParseResult(ok=True, response="provider-ok")

    monkeypatch.setattr(runtime_runner, "FleetCapture", FakeCapture)
    python = Path(__file__).resolve().parents[1] / ".venv" / "bin" / "python"
    outcome = runtime_runner._execute_invocation_plan(
        agent_name="deepseek",
        adapter=Adapter(),
        plan=InvocationPlan(
            cmd=[str(python), "-c", "print('provider-ok')"],
            cwd=tmp_path,
            host_harness="hermes",
        ),
        prompt="fixture",
        mode="read-only",
        cwd=tmp_path,
        model="deepseek-v4-flash",
        task_id="fixture",
        session_id=None,
        entrypoint="bridge",
        hard_timeout=30,
        stall_timeout=30,
    )
    assert outcome.parse.ok is True
    assert [name for name, _ in events] == ["start", "finish"]
    assert events[0][1]["host_harness"] == "hermes"
    assert events[1][1]["response"] == "provider-ok"
    assert events[1][1]["outcome"] == "ok"


def test_spawn_refusal_creates_no_entire_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from agent_runtime import runner as runtime_runner

    class NoCapture:
        @classmethod
        def start(cls, **_kwargs):
            raise AssertionError("capture started before subprocess spawn")

    class Adapter:
        def liveness_signal_paths(self, _plan):
            return ()

    monkeypatch.setattr(runtime_runner, "FleetCapture", NoCapture)
    monkeypatch.setattr(runtime_runner, "write_record", lambda _record: None)
    with pytest.raises(runtime_runner.AgentUnavailableError):
        runtime_runner._execute_invocation_plan(
            agent_name="agy",
            adapter=Adapter(),
            plan=InvocationPlan(
                cmd=[str(tmp_path / "missing-binary")],
                cwd=tmp_path,
                host_harness="agy",
            ),
            prompt="fixture",
            mode="read-only",
            cwd=tmp_path,
            model="fixture",
            task_id="fixture",
            session_id=None,
            entrypoint="dispatch",
            hard_timeout=30,
            stall_timeout=30,
        )


def _hermes_result(*, ok: bool = True, response: str = "response body") -> Result:
    return Result(
        ok=ok,
        agent="deepseek",
        model="deepseek-v4-flash",
        mode="read-only",
        response=response,
        stderr_excerpt=None,
        duration_s=0.1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0 if ok else 1,
    )


def test_hermes_default_model_is_deepseek_flash():
    """DeepSeek Flash is the Hermes tool-heavy default."""
    assert HERMES_DEFAULT_MODEL == "deepseek-v4-flash"


def test_invoke_hermes_uses_shared_runtime():
    with patch(
        "scripts.agent_runtime.runner.invoke",
        return_value=_hermes_result(),
    ) as invoke_mock:
        assert _invoke_hermes("hello", "deepseek-v4-flash", task_id="task-1") == "response body"
    args, kwargs = invoke_mock.call_args
    assert args == ("hermes-deepseek", "hello")
    assert kwargs["model"] == "deepseek-v4-flash"
    assert kwargs["task_id"] == "task-1"
    assert kwargs["entrypoint"] == "bridge"
    assert kwargs["mode"] == "read-only"
    assert kwargs["tool_config"]["repo_read_root"]


def test_invoke_hermes_attaches_data_file(tmp_path):
    data_file = tmp_path / "context.md"
    data_file.write_text("# Context\nSome content.")
    with patch(
        "scripts.agent_runtime.runner.invoke",
        return_value=_hermes_result(response="ok"),
    ) as invoke_mock:
        _invoke_hermes("review this", "deepseek-v4-flash", data=str(data_file))
    prompt = invoke_mock.call_args.args[1]
    assert "Some content." in prompt
    assert "review this" in prompt


def test_invoke_hermes_raises_when_binary_missing():
    with patch(
        "scripts.agent_runtime.runner.invoke",
        side_effect=AgentUnavailableError("missing"),
    ):
        with pytest.raises(SystemExit, match="AgentUnavailableError"):
            _invoke_hermes("hello", "deepseek-v4-flash")


def test_invoke_hermes_raises_on_nonzero_exit():
    with patch(
        "scripts.agent_runtime.runner.invoke",
        return_value=_hermes_result(ok=False, response=""),
    ):
        with pytest.raises(SystemExit, match="no usable response"):
            _invoke_hermes("hello", "deepseek-v4-flash")
