from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from scripts.audit import lint_agent_trailer as lat
from scripts.audit.lint_agent_trailer import ProvenanceContext, _check_commit, main, resolve_provenance_context


def _write_task_record(
    tasks_dir: Path,
    task_id: str,
    agent: str = "codex",
    *,
    worktree_path: str | None = None,
    archived: bool = False,
) -> Path:
    target_dir = tasks_dir / "archive" if archived else tasks_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    record_file = target_dir / f"{task_id}.json"
    data = {
        "task_id": task_id,
        "agent": agent,
        "worktree_path": worktree_path or f"/tmp/wt/{agent}/{task_id}",
    }
    record_file.write_text(json.dumps(data), encoding="utf-8")
    return record_file


def _mock_commit(
    monkeypatch: pytest.MonkeyPatch,
    body: str,
    subject: str = "feat: some commit",
    sha: str = "a1b2c3d4e5f67890123456789012345678901234",
) -> None:
    monkeypatch.setattr(lat, "_commits_in_range", lambda rev_range, cwd=None: [sha])
    monkeypatch.setattr(
        lat,
        "_commit_meta",
        lambda sha_arg, cwd=None: ("dev@example.com", "dev@example.com", "Dev", subject),
    )
    monkeypatch.setattr(lat, "_commit_body", lambda sha_arg, cwd=None: body)


def test_wrong_task_id_rejected_locally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "impl-8638-r2", agent="codex")

    provenance = ProvenanceContext(
        active=True,
        expected_task_id="impl-8638-r2",
        expected_agent="codex",
        tasks_dir=tasks_dir,
    )

    _mock_commit(monkeypatch, "fix: wrong trailer\n\nX-Agent: codex/8638-r2")

    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "FAIL"
    assert "task record '8638-r2' not found" in reason
    assert "expected literal trailer: 'X-Agent: codex/impl-8638-r2'" in reason

    # Also test via main
    monkeypatch.setattr(lat, "resolve_provenance_context", lambda tasks_dir=None, cwd=None: provenance)
    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(tasks_dir)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert "X-Agent: codex/impl-8638-r2" in captured.out


def test_correct_id_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "impl-8642", agent="agy")

    provenance = ProvenanceContext(
        active=True,
        expected_task_id="impl-8642",
        expected_agent="agy",
        tasks_dir=tasks_dir,
    )

    _mock_commit(monkeypatch, "fix: trailer lint\n\nX-Agent: agy/impl-8642")

    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: agy/impl-8642"

    monkeypatch.setattr(lat, "resolve_provenance_context", lambda tasks_dir=None, cwd=None: provenance)
    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(tasks_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert "All 1 non-skipped commit(s) carry an X-Agent trailer." in captured.out


def test_archived_id_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "impl-8638-r1", agent="codex", archived=True)

    provenance = ProvenanceContext(
        active=True,
        expected_task_id="impl-8638-r1",
        expected_agent="codex",
        tasks_dir=tasks_dir,
    )

    _mock_commit(monkeypatch, "fix: archived trailer\n\nX-Agent: codex/impl-8638-r1")

    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: codex/impl-8638-r1"

    monkeypatch.setattr(lat, "resolve_provenance_context", lambda tasks_dir=None, cwd=None: provenance)
    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(tasks_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert "All 1 non-skipped commit(s) carry an X-Agent trailer." in captured.out


def test_ci_mode_shape_only_with_skip_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    monkeypatch.setenv("CI", "true")

    # The task record does NOT exist in tasks_dir, but in CI it should stay shape-only
    _mock_commit(monkeypatch, "fix: commit in ci\n\nX-Agent: codex/impl-nonexistent")

    ctx = resolve_provenance_context(tasks_dir=tasks_dir)
    assert ctx.active is False
    assert "CI environment detected (CI)" in (ctx.skip_reason or "")

    verdict, reason = _check_commit("fake-sha", provenance=ctx)
    assert verdict == "PASS"
    assert reason == "X-Agent: codex/impl-nonexistent"

    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(tasks_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Task provenance check skipped: CI environment detected (CI)" in captured.out
    assert "PASS" in captured.out


def test_no_records_shape_only_with_skip_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    for var in lat._CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    empty_tasks_dir = tmp_path / "empty_tasks"
    empty_tasks_dir.mkdir()

    _mock_commit(monkeypatch, "fix: local commit without records\n\nX-Agent: codex/impl-1234")

    ctx = resolve_provenance_context(tasks_dir=empty_tasks_dir)
    assert ctx.active is False
    assert "no task records present" in (ctx.skip_reason or "")

    verdict, _reason = _check_commit("fake-sha", provenance=ctx)
    assert verdict == "PASS"

    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(empty_tasks_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Task provenance check skipped: no task records present" in captured.out
    assert "PASS" in captured.out


def test_ci_mode_still_rejects_missing_or_malformed_trailer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    ctx = resolve_provenance_context(tasks_dir=tasks_dir)
    assert ctx.active is False

    _mock_commit(monkeypatch, "fix: missing trailer without X-Agent")
    verdict, reason = _check_commit("fake-sha", provenance=ctx)
    assert verdict == "FAIL"
    assert "missing X-Agent trailer" in reason


def test_trailer_task_mismatch_with_known_worktree_rejected(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "task-alpha", agent="codex")
    _write_task_record(tasks_dir, "task-beta", agent="codex")

    provenance = ProvenanceContext(
        active=True,
        expected_task_id="task-alpha",
        expected_agent="codex",
        tasks_dir=tasks_dir,
    )

    # Commit carries task-beta, but worktree is task-alpha
    body = "feat: work on wrong task\n\nX-Agent: codex/task-beta"
    meta = ("dev@example.com", "dev@example.com", "Dev", "feat: work")

    class FakeGit:
        pass

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(lat, "_commit_meta", lambda sha, cwd=None: meta)
        mp.setattr(lat, "_commit_body", lambda sha, cwd=None: body)
        verdict, reason = _check_commit("fake-sha", provenance=provenance)
        assert verdict == "FAIL"
        assert "dispatch worktree task is 'task-alpha'" in reason
        assert "expected literal trailer: 'X-Agent: codex/task-alpha'" in reason


def test_trailer_agent_mismatch_with_known_worktree_rejected(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "task-alpha", agent="codex")

    provenance = ProvenanceContext(
        active=True,
        expected_task_id="task-alpha",
        expected_agent="codex",
        tasks_dir=tasks_dir,
    )

    meta = ("dev@example.com", "dev@example.com", "Dev", "feat: work")
    body = "feat: work on right task wrong agent\n\nX-Agent: agy/task-alpha"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(lat, "_commit_meta", lambda sha, cwd=None: meta)
        mp.setattr(lat, "_commit_body", lambda sha, cwd=None: body)
        verdict, reason = _check_commit("fake-sha", provenance=provenance)
        assert verdict == "FAIL"
        assert "dispatch worktree agent is 'codex'" in reason
        assert "expected literal trailer: 'X-Agent: codex/task-alpha'" in reason


def test_grok_build_alias_accepted(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "task-grok", agent="grok")

    provenance = ProvenanceContext(
        active=True,
        expected_task_id="task-grok",
        expected_agent="grok",
        tasks_dir=tasks_dir,
    )

    meta = ("dev@example.com", "dev@example.com", "Dev", "feat: work")
    body = "feat: work with grok-build alias\n\nX-Agent: grok-build/task-grok"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(lat, "_commit_meta", lambda sha, cwd=None: meta)
        mp.setattr(lat, "_commit_body", lambda sha, cwd=None: body)
        verdict, _reason = _check_commit("fake-sha", provenance=provenance)
        assert verdict == "PASS"


def test_worker_env_carries_lu_x_agent_trailer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """delegate.py exports LU_X_AGENT_TRAILER into worker_env."""
    from scripts import delegate

    recorded: dict[str, object] = {}

    class _FakeStdin:
        def write(self, _data):
            pass

        def close(self):
            pass

    class _FakeProc:
        pid = 12345
        stdin = _FakeStdin()

    def fake_popen(*args, **kwargs):
        recorded["env"] = kwargs.get("env", {})
        return _FakeProc()

    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)
    monkeypatch.delenv("PYTEST_PLUGINS", raising=False)
    fake_tasks = tmp_path / "batch_tasks"
    fake_tasks.mkdir()
    monkeypatch.setattr(delegate, "_TASKS_DIR", fake_tasks)

    args = argparse.Namespace(
        agent="codex",
        task_id="dispatch-trailer-test",
        prompt="test prompt",
        prompt_file=None,
        mode="read-only",
        model=None,
        cwd=None,
        worktree=None,
        hard_timeout=3600,
        allow_merge=False,
    )

    rc = delegate.cmd_dispatch(args)
    assert rc == 0
    env = recorded["env"]
    assert env["LU_X_AGENT_TRAILER"] == "X-Agent: codex/dispatch-trailer-test"
    assert env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] == "dispatch-trailer-test"
    assert env["LEARN_UKRAINIAN_DISPATCH_AGENT"] == "codex"


def test_prompt_preamble_mentions_lu_x_agent_trailer() -> None:
    """Prompt preamble for write-capable workers must mention LU_X_AGENT_TRAILER."""
    from scripts import delegate

    text = delegate._augment_prompt_with_worktree(
        "implement feature",
        Path("/tmp/dispatch-wt"),
        mode="workspace-write",
    )
    assert "LU_X_AGENT_TRAILER" in text
    assert "Commit your work (use the literal trailer in `$LU_X_AGENT_TRAILER`)." in text

    # Read-only prompt omits write-mode closeout
    read_only_text = delegate._augment_prompt_with_worktree(
        "inspect feature",
        Path("/tmp/dispatch-wt"),
        mode="read-only",
    )
    assert "LU_X_AGENT_TRAILER" not in read_only_text


def test_resolve_provenance_from_env_vars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "task-env-123", agent="kimi")

    for var in lat._CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "task-env-123")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "kimi")

    ctx = resolve_provenance_context(tasks_dir=tasks_dir)
    assert ctx.active is True
    assert ctx.expected_task_id == "task-env-123"
    assert ctx.expected_agent == "kimi"
    assert ctx.expected_trailer == "X-Agent: kimi/task-env-123"


def test_resolve_provenance_from_worktree_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    wt_dir = repo_root / ".worktrees" / "dispatch" / "codex" / "task-wt-456"
    wt_dir.mkdir(parents=True)

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "task-wt-456", agent="codex", worktree_path=str(wt_dir))

    for var in lat._CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_AGENT", raising=False)
    monkeypatch.delenv("LU_X_AGENT_TRAILER", raising=False)

    monkeypatch.setattr(lat, "_resolve_repo_root", lambda cwd=None: repo_root)
    monkeypatch.setattr(lat, "_resolve_worktree_dir", lambda cwd=None: wt_dir)

    ctx = resolve_provenance_context(tasks_dir=tasks_dir, cwd=wt_dir)
    assert ctx.active is True
    assert ctx.expected_task_id == "task-wt-456"
    assert ctx.expected_agent == "codex"
    assert ctx.expected_trailer == "X-Agent: codex/task-wt-456"


def test_resolve_provenance_not_in_dispatch_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "some-task", agent="codex")

    for var in lat._CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_AGENT", raising=False)
    monkeypatch.delenv("LU_X_AGENT_TRAILER", raising=False)

    monkeypatch.setattr(lat, "_resolve_repo_root", lambda cwd=None: repo_root)
    monkeypatch.setattr(lat, "_resolve_worktree_dir", lambda cwd=None: repo_root)

    ctx = resolve_provenance_context(tasks_dir=tasks_dir, cwd=repo_root)
    assert ctx.active is False
    assert "not inside a dispatch worktree" in (ctx.skip_reason or "")
