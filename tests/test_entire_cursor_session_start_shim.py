"""Security and reconciliation tests for the pinned native Cursor shim."""

from __future__ import annotations

import json
import re
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.entire import cursor_session_start_shim as shim


def _repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    return root.resolve()


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


def test_hook_delegates_exact_normalized_payload_without_reading_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
                    {"conversation_id": "session-6", "workspace_roots": [str(root)]}
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
    assert shim._hook() == 0
    assert calls[0][0] == ["/fake/entire", "hooks", "cursor", "session-start"]
    assert json.loads(calls[0][1]["input"])["transcript_path"] == str(
        nested / "session-6.jsonl"
    )
    assert calls[0][1]["cwd"] == root


@pytest.mark.parametrize("failure", [FileNotFoundError(), subprocess.TimeoutExpired("x", 1)])
def test_hook_failures_are_silent_and_fail_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    monkeypatch.setattr(
        shim.sys,
        "stdin",
        SimpleNamespace(buffer=SimpleNamespace(read=lambda _limit: b"not-json")),
    )
    monkeypatch.setattr(shim.subprocess, "run", lambda *_args, **_kwargs: (_ for _ in ()).throw(failure))
    assert shim._hook() == 0


def test_install_uninstall_are_atomic_idempotent_and_preserve_config(tmp_path: Path) -> None:
    path = tmp_path / "hooks.json"
    expected = _native_hooks(extra={"operator": [1, 2, 3]})
    path.write_text(json.dumps(expected), encoding="utf-8")
    assert shim._reconcile(path, "install") is True
    installed = json.loads(path.read_text(encoding="utf-8"))
    assert installed["custom"] == {"operator": [1, 2, 3]}
    assert installed["hooks"]["sessionStart"][0]["command"] == shim._SHIM_COMMAND
    assert installed["hooks"]["sessionStart"][1]["command"] == "operator-session-hook"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert shim._reconcile(path, "install") is False
    assert shim._reconcile(path, "check") is False
    assert shim._reconcile(path, "uninstall") is True
    assert json.loads(path.read_text())["hooks"]["sessionStart"][0]["command"] == (
        shim._STOCK_COMMANDS["sessionStart"]
    )
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
        entries.insert(0, {"command": shim._SHIM_COMMAND})
    path.write_text(json.dumps(parsed), encoding="utf-8")
    with pytest.raises(shim.ReconciliationError):
        shim._reconcile(path, "install")
