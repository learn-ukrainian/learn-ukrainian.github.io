from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from scripts.build import v7_build


def _install_fake_subprocess_run(
    monkeypatch: Any,
    repo: Path,
    *,
    child_returncode: int = 0,
    worktree_add_returncode: int = 0,
    worktree_add_stderr: str = "",
) -> list[list[str]]:
    calls: list[list[str]] = []

    def fake_run(
        cmd: list[str],
        cwd: Path | str | None = None,
        capture_output: bool = False,
        text: bool = False,
        check: bool = False,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, capture_output, text, check, timeout
        calls.append(cmd)
        if cmd[:2] == ["git", "rev-parse"] and "--show-toplevel" in cmd:
            return subprocess.CompletedProcess(cmd, 0, f"{repo}\n", "")
        if cmd[:2] == ["git", "rev-parse"] and "--git-common-dir" in cmd:
            return subprocess.CompletedProcess(cmd, 0, f"{repo / '.git'}\n", "")
        if cmd[:2] == ["git", "rev-parse"] and "--verify" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "origin/main\n", "")
        if cmd[:2] == ["git", "rev-parse"] and "--short" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "abc1234\n", "")
        if cmd == ["git", "fetch", "origin"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:3] == ["git", "worktree", "add"]:
            if worktree_add_returncode == 0:
                Path(cmd[-2]).mkdir(parents=True, exist_ok=True)
            return subprocess.CompletedProcess(
                cmd,
                worktree_add_returncode,
                "",
                worktree_add_stderr,
            )
        return subprocess.CompletedProcess(cmd, child_returncode, "", "")

    monkeypatch.setattr(v7_build.subprocess, "run", fake_run)
    return calls


def _prepare_repo(monkeypatch: Any, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", repo)
    monkeypatch.setattr(v7_build, "_utc_timestamp", lambda: "20260513-123456")
    return repo


def test_worktree_auto_path_derives_path_and_branch(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    repo = _prepare_repo(monkeypatch, tmp_path)
    calls = _install_fake_subprocess_run(monkeypatch, repo)

    exit_code = v7_build.main(["a1", "my-morning", "--dry-run", "--worktree"])

    assert exit_code == 0
    add_cmd = next(cmd for cmd in calls if cmd[:3] == ["git", "worktree", "add"])
    assert add_cmd == [
        "git",
        "worktree",
        "add",
        "-b",
        "build/a1/my-morning-20260513-123456",
        str(repo / ".worktrees" / "builds" / "a1-my-morning-20260513-123456"),
        "origin/main",
    ]


def test_worktree_explicit_path_uses_path_and_basename_branch(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    repo = _prepare_repo(monkeypatch, tmp_path)
    calls = _install_fake_subprocess_run(monkeypatch, repo)

    exit_code = v7_build.main(
        [
            "a1",
            "my-morning",
            "--worktree",
            ".worktrees/builds/custom-20260513-123456",
            "--dry-run",
        ]
    )

    assert exit_code == 0
    add_cmd = next(cmd for cmd in calls if cmd[:3] == ["git", "worktree", "add"])
    assert add_cmd[4] == "build/a1/custom-20260513-123456"
    assert add_cmd[5] == str(repo / ".worktrees" / "builds" / "custom-20260513-123456")


def test_worktree_path_collision_errors_cleanly(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    repo = _prepare_repo(monkeypatch, tmp_path)
    target = repo / ".worktrees" / "builds" / "a1-my-morning-20260513-123456"
    target.mkdir(parents=True)
    calls = _install_fake_subprocess_run(monkeypatch, repo)

    exit_code = v7_build.main(["a1", "my-morning", "--worktree"])

    captured = capsys.readouterr()
    assert exit_code == 3
    assert (
        f"Worktree path {target} exists; remove with `git worktree remove {target}`"
        in captured.err
    )
    assert not any(cmd[:3] == ["git", "worktree", "add"] for cmd in calls)


def test_worktree_add_failure_propagates_stderr(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    repo = _prepare_repo(monkeypatch, tmp_path)
    _install_fake_subprocess_run(
        monkeypatch,
        repo,
        worktree_add_returncode=128,
        worktree_add_stderr="fatal: a branch named build/a1/my-morning exists",
    )

    exit_code = v7_build.main(["a1", "my-morning", "--worktree"])

    captured = capsys.readouterr()
    assert exit_code == 4
    assert "fatal: a branch named build/a1/my-morning exists" in captured.err


def test_worktree_build_success_prints_summary(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    repo = _prepare_repo(monkeypatch, tmp_path)
    _install_fake_subprocess_run(monkeypatch, repo, child_returncode=0)

    exit_code = v7_build.main(["a1", "my-morning", "--dry-run", "--worktree"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert (
        f"BUILD_WORKTREE={repo / '.worktrees' / 'builds' / 'a1-my-morning-20260513-123456'}"
        in captured.out
    )
    assert "BUILD_BRANCH=build/a1/my-morning-20260513-123456" in captured.out
    assert "BUILD_BASE=abc1234" in captured.out
    assert "BUILD_RESULT=success" in captured.out


def test_worktree_build_failure_prints_summary_and_preserves_worktree(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    repo = _prepare_repo(monkeypatch, tmp_path)
    calls = _install_fake_subprocess_run(monkeypatch, repo, child_returncode=17)

    exit_code = v7_build.main(["a1", "my-morning", "--dry-run", "--worktree"])

    captured = capsys.readouterr()
    assert exit_code == 17
    assert "BUILD_RESULT=failed" in captured.out
    assert not any(cmd[:3] == ["git", "worktree", "remove"] for cmd in calls)


def test_worktree_persists_artifacts_on_success(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """Build artifacts MUST be committed to the build branch on success.

    Per MEMORY.md #M-10, build artifacts (writer_prompt, writer_output.raw,
    hermes.write.jsonl, writer_tool_calls.json, knowledge_packet, etc.) are
    load-bearing for diagnosis and the self-correction loop. v7_build writes
    them to the worktree filesystem but does NOT commit them — without this
    persist step, ``git worktree remove`` silently destroys forensic
    evidence (2026-05-19→20 incident: 7 worktrees deleted, today's
    textbook_grounding diagnostic artifacts lost). Both ``git add -A`` and
    ``git commit --allow-empty`` must fire in the worktree.
    """
    repo = _prepare_repo(monkeypatch, tmp_path)
    calls = _install_fake_subprocess_run(monkeypatch, repo, child_returncode=0)
    worktree_path = repo / ".worktrees" / "builds" / "a1-my-morning-20260513-123456"

    exit_code = v7_build.main(["a1", "my-morning", "--dry-run", "--worktree"])

    assert exit_code == 0
    add_cmd = next(
        cmd
        for cmd in calls
        if cmd[:2] == ["git", "-C"]
        and cmd[2] == str(worktree_path)
        and cmd[3:] == ["add", "-A"]
    )
    assert add_cmd is not None
    commit_cmd = next(
        cmd
        for cmd in calls
        if cmd[:2] == ["git", "-C"]
        and cmd[2] == str(worktree_path)
        and cmd[3] == "commit"
    )
    assert "--allow-empty" in commit_cmd
    assert "--no-verify" in commit_cmd
    msg_idx = commit_cmd.index("-m") + 1
    assert "build(a1/my-morning)" in commit_cmd[msg_idx]
    assert "(success)" in commit_cmd[msg_idx]


def test_worktree_persists_artifacts_on_failure(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """Persist artifacts even when the build crashed mid-phase.

    A failed build's writer_prompt + partial writer_output is OFTEN the
    most valuable diagnostic evidence — those artifacts are what surface
    bugs like the 2026-05-19 textbook_grounding gap (writer DID retrieve
    correctly, gate just couldn't see it). The finally branch MUST commit
    regardless of child exit code.
    """
    repo = _prepare_repo(monkeypatch, tmp_path)
    calls = _install_fake_subprocess_run(monkeypatch, repo, child_returncode=17)
    worktree_path = repo / ".worktrees" / "builds" / "a1-my-morning-20260513-123456"

    exit_code = v7_build.main(["a1", "my-morning", "--dry-run", "--worktree"])

    assert exit_code == 17
    commit_cmds = [
        cmd
        for cmd in calls
        if cmd[:2] == ["git", "-C"]
        and cmd[2] == str(worktree_path)
        and cmd[3] == "commit"
    ]
    assert len(commit_cmds) == 1
    msg_idx = commit_cmds[0].index("-m") + 1
    assert "(failed)" in commit_cmds[0][msg_idx]
