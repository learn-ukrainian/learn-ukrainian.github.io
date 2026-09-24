from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit import lint_agent_trailer as lat
from scripts.audit.lint_agent_trailer import _check_commit, main, resolve_provenance_context


@pytest.fixture(autouse=True)
def _stub_primary_integrity_sweep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep delegate tests hermetic from the ambient checkout (same as tests/test_delegate.py:59)."""
    import scripts.audit.check_primary_integrity as cpi

    monkeypatch.setattr(
        cpi,
        "check_primary_integrity",
        lambda *_args, **_kwargs: (True, "primary on main (test stub)"),
    )


@pytest.fixture(autouse=True)
def _isolate_dispatch_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from ambient dispatch environment variables."""
    for var in (
        "LEARN_UKRAINIAN_DISPATCH_TASK_ID",
        "LEARN_UKRAINIAN_DISPATCH_AGENT",
        "LU_X_AGENT_TRAILER",
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "BUILDKITE",
        "JENKINS_URL",
        "PYTEST_PLUGINS",
    ):
        monkeypatch.delenv(var, raising=False)


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
    safe_name = task_id.replace("/", "_").replace("\\", "_")
    record_file = target_dir / f"{safe_name}.json"
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

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "impl-8638-r2")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True
    assert provenance.expected_trailer == "X-Agent: codex/impl-8638-r2"

    _mock_commit(monkeypatch, "fix: wrong trailer\n\nX-Agent: codex/8638-r2")

    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "FAIL"
    assert "task record '8638-r2' not found" in reason
    assert "expected literal trailer: 'X-Agent: codex/impl-8638-r2'" in reason

    # Also test via main
    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(tasks_dir)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert "X-Agent: codex/impl-8638-r2" in captured.out


def test_cwd_dispatch_worktree_resolves_primary_tasks_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """A dispatch-worktree cwd anchors batch_state/tasks to the primary checkout without --tasks-dir."""
    primary = tmp_path / "primary"
    primary_git = primary / ".git"
    primary_git.mkdir(parents=True)
    primary_tasks = primary / "batch_state" / "tasks"
    primary_tasks.mkdir(parents=True)
    _write_task_record(primary_tasks, "task-target", agent="codex")

    worktree_git_meta = primary_git / "worktrees" / "wt-target"
    worktree_git_meta.mkdir(parents=True)
    worktree = tmp_path / ".worktrees" / "dispatch" / "codex" / "task-target"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {worktree_git_meta}\n")

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "task-target")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")

    # Pass cwd=worktree WITHOUT tasks_dir=
    provenance = resolve_provenance_context(cwd=worktree)
    assert provenance.active is True
    assert provenance.tasks_dir == primary_tasks.resolve()
    assert provenance.expected_trailer == "X-Agent: codex/task-target"

    # Wrong-task trailer fails
    _mock_commit(monkeypatch, "feat: wrong trailer\n\nX-Agent: codex/wrong-task")
    verdict, reason = _check_commit("fake-sha", provenance=provenance, cwd=worktree)
    assert verdict == "FAIL"
    assert "task record 'wrong-task' not found" in reason
    assert "expected literal trailer: 'X-Agent: codex/task-target'" in reason

    # Also test via main() with --cwd and without --tasks-dir
    rc = main(["HEAD~1..HEAD", "--cwd", str(worktree)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert "X-Agent: codex/task-target" in captured.out


def test_correct_id_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "impl-8642", agent="agy")

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "impl-8642")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "agy")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True

    _mock_commit(monkeypatch, "fix: trailer lint\n\nX-Agent: agy/impl-8642")

    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: agy/impl-8642"

    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(tasks_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert "All 1 non-skipped commit(s) carry an X-Agent trailer." in captured.out


def test_archived_id_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "impl-8638-r1", agent="codex", archived=True)

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "impl-8638-r1")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True

    _mock_commit(monkeypatch, "fix: archived trailer\n\nX-Agent: codex/impl-8638-r1")

    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: codex/impl-8638-r1"

    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(tasks_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert "All 1 non-skipped commit(s) carry an X-Agent trailer." in captured.out


def test_blocker_1_agent_prefixed_task_id_normalization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Blocker 1: auto-finalize and worker trailer generation for tasks starting with agent name.

    For task 'codex-1472-foo', finalize commits 'codex/1472-foo'.
    The task record is 'codex-1472-foo.json'.
    Normalization-aware record lookup accepts '1472-foo' when 'codex-1472-foo.json' exists.
    """
    from scripts import delegate

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "codex-1472-foo", agent="codex")

    # Both finalize and LU_X_AGENT_TRAILER use _x_agent_trailer:
    trailer = delegate._x_agent_trailer("codex", "codex-1472-foo")
    assert trailer == "X-Agent: codex/1472-foo"

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "codex-1472-foo")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")
    monkeypatch.setenv("LU_X_AGENT_TRAILER", trailer)

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True
    assert provenance.expected_trailer == "X-Agent: codex/1472-foo"

    _mock_commit(monkeypatch, f"chore(dispatch): finalize codex task 1472-foo\n\n{trailer}")

    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: codex/1472-foo"

    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(tasks_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out


def test_earlier_round_commits_on_same_branch_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Finding 2: Earlier-round commits on the same branch must pass.

    Worktree is on round 2 (impl-8642-r2). An earlier commit on the branch
    carries round 1's trailer (impl-8642), whose record exists in tasks_dir.
    """
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "impl-8642-r2", agent="agy")
    _write_task_record(tasks_dir, "impl-8642", agent="agy", archived=True)

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "impl-8642-r2")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "agy")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True

    # R1 commit passes
    _mock_commit(monkeypatch, "feat: round 1 implementation\n\nX-Agent: agy/impl-8642")
    verdict_r1, reason_r1 = _check_commit("sha-r1", provenance=provenance)
    assert verdict_r1 == "PASS"
    assert reason_r1 == "X-Agent: agy/impl-8642"

    # R2 commit passes
    _mock_commit(monkeypatch, "fix: round 2 review fixes\n\nX-Agent: agy/impl-8642-r2")
    verdict_r2, reason_r2 = _check_commit("sha-r2", provenance=provenance)
    assert verdict_r2 == "PASS"
    assert reason_r2 == "X-Agent: agy/impl-8642-r2"


def test_exemptions_shape_checked_only_when_provenance_active(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Finding 3: *-inline/*, */inline, and dependabot/* are shape-checked only."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "task-active", agent="codex")

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "task-active")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True

    exempt_trailers = [
        "X-Agent: claude-inline/orchestrator",
        "X-Agent: agy-inline/fix-typo",
        "X-Agent: codex/inline",
        "X-Agent: agy/inline",
        "X-Agent: dependabot/npm_and_yarn_deps",
    ]

    for trailer in exempt_trailers:
        _mock_commit(monkeypatch, f"chore: some inline commit\n\n{trailer}")
        verdict, reason = _check_commit("sha-exempt", provenance=provenance)
        assert verdict == "PASS"
        assert reason == trailer


def test_gemini_agy_alias_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Finding 4: gemini and agy are treated as the same agent for record comparison."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "impl-8642", agent="agy")

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "impl-8642")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "agy")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True

    # Worker following GEMINI.md:76 writes gemini/<task-id>
    _mock_commit(monkeypatch, "fix: gemini commit\n\nX-Agent: gemini/impl-8642")
    verdict, reason = _check_commit("sha-gemini", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: gemini/impl-8642"

    # Reverse: record with "gemini" and trailer with "agy"
    _write_task_record(tasks_dir, "old-task", agent="gemini")
    _mock_commit(monkeypatch, "fix: agy commit\n\nX-Agent: agy/old-task")
    verdict_rev, reason_rev = _check_commit("sha-agy", provenance=provenance)
    assert verdict_rev == "PASS"
    assert reason_rev == "X-Agent: agy/old-task"


def test_deepseek_plain_trailer_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Finding 5: plain deepseek in _TRAILER_RE and LU_X_AGENT_TRAILER."""
    from scripts import delegate

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "1234-fix-parse", agent="deepseek")

    trailer = delegate._x_agent_trailer("deepseek", "1234-fix-parse")
    assert trailer == "X-Agent: deepseek/1234-fix-parse"

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "1234-fix-parse")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "deepseek")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True

    _mock_commit(monkeypatch, f"feat: deepseek dispatch\n\n{trailer}")
    verdict, reason = _check_commit("sha-deepseek", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: deepseek/1234-fix-parse"


def test_detection_requires_record_to_exist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Finding 6: provenance check is active only when record is found; else shape-only."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "nonexistent-task")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")

    ctx = resolve_provenance_context(tasks_dir=tasks_dir)
    assert ctx.active is False
    assert "task record 'nonexistent-task' not found" in (ctx.skip_reason or "")

    # Shape-valid commit passes because provenance check is skipped
    _mock_commit(monkeypatch, "feat: commit\n\nX-Agent: codex/any-task")
    verdict, _ = _check_commit("sha-shape", provenance=ctx)
    assert verdict == "PASS"


def test_resolve_provenance_no_env_marker_is_shape_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Detection without LEARN_UKRAINIAN_DISPATCH_TASK_ID is inactive (shape-only)."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "some-task", agent="codex")

    ctx = resolve_provenance_context(tasks_dir=tasks_dir)
    assert ctx.active is False
    assert "dispatch task environment marker not set" in (ctx.skip_reason or "")

    _mock_commit(monkeypatch, "feat: operator commit\n\nX-Agent: codex/some-task")
    verdict, _ = _check_commit("sha-op", provenance=ctx)
    assert verdict == "PASS"

    rc = main(["HEAD~1..HEAD", "--tasks-dir", str(tasks_dir)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Task provenance check skipped: dispatch task environment marker not set" in captured.out


def test_ci_mode_shape_only_with_skip_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "ci-task")

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


def test_trailer_agent_mismatch_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "task-alpha", agent="codex")

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "task-alpha")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True

    _mock_commit(monkeypatch, "feat: wrong agent\n\nX-Agent: agy/task-alpha")
    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "FAIL"
    assert "trailer 'X-Agent: agy/task-alpha' names agent 'agy'" in reason
    assert "dispatch worktree agent is 'codex'" in reason
    assert "expected literal trailer: 'X-Agent: codex/task-alpha'" in reason


def test_grok_build_alias_accepted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task_record(tasks_dir, "task-grok", agent="grok")

    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "task-grok")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "grok")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True

    _mock_commit(monkeypatch, "feat: work with grok-build alias\n\nX-Agent: grok-build/task-grok")
    verdict, _reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "PASS"


def test_worker_env_carries_lu_x_agent_trailer(monkeypatch: pytest.MonkeyPatch) -> None:
    """delegate.py exports LU_X_AGENT_TRAILER into worker_env via _build_worker_env and _x_agent_trailer."""
    from scripts import delegate

    monkeypatch.setattr(delegate, "_resolve_github_token", lambda: None)

    # Direct helper verification
    assert delegate._x_agent_trailer("codex", "dispatch-trailer-test") == "X-Agent: codex/dispatch-trailer-test"
    assert delegate._x_agent_trailer("codex", "codex-1472-foo") == "X-Agent: codex/1472-foo"

    env = delegate._build_worker_env(
        task_id="dispatch-trailer-test",
        dispatch_agent="codex",
        base_env={},
    )
    assert env["LU_X_AGENT_TRAILER"] == "X-Agent: codex/dispatch-trailer-test"
    assert env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] == "dispatch-trailer-test"
    assert env["LEARN_UKRAINIAN_DISPATCH_AGENT"] == "codex"


def test_literal_expected_trailer_accepted_without_record_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Should-fix 2: literal expected trailer passes before any record lookup.

    1. Task id 'fix:parse' -> record 'fix:parse.json', trailer 'codex/fix-parse'.
    2. Task id 'codex/foo' -> record 'codex_foo.json', trailer 'codex/foo'.
    """
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    # Case 1: task id fix:parse
    _write_task_record(tasks_dir, "fix:parse", agent="codex")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "fix:parse")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")
    monkeypatch.delenv("LU_X_AGENT_TRAILER", raising=False)

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True
    assert provenance.expected_trailer == "X-Agent: codex/fix-parse"

    _mock_commit(monkeypatch, "fix: parse colon in task id\n\nX-Agent: codex/fix-parse")
    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: codex/fix-parse"

    # Case 2: task id codex/foo -> record codex_foo.json
    _write_task_record(tasks_dir, "codex/foo", agent="codex")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "codex/foo")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True
    assert provenance.expected_trailer == "X-Agent: codex/foo"

    _mock_commit(monkeypatch, "feat: handle codex slash task\n\nX-Agent: codex/foo")
    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: codex/foo"


def test_candidate_order_and_agent_match_preference(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Nit: For trailer 'codex/1472-foo', try {agent}-task first and prefer matching agent record.

    Both '1472-foo.json' (owned by another agent, e.g. claude) and
    'codex-1472-foo.json' (owned by codex) exist -> 'codex/1472-foo' passes.
    """
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    # 1472-foo owned by claude
    _write_task_record(tasks_dir, "1472-foo", agent="claude")
    # codex-1472-foo owned by codex
    _write_task_record(tasks_dir, "codex-1472-foo", agent="codex")

    # Current dispatch is for a different task to exercise the record lookup path
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "other-task")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "codex")
    _write_task_record(tasks_dir, "other-task", agent="codex")

    provenance = resolve_provenance_context(tasks_dir=tasks_dir)
    assert provenance.active is True

    _mock_commit(monkeypatch, "fix: commit on branch\n\nX-Agent: codex/1472-foo")
    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "PASS"
    assert reason == "X-Agent: codex/1472-foo"

    # If the matching record is removed, the remaining record owned by claude causes agent mismatch
    (tasks_dir / "codex-1472-foo.json").unlink()
    verdict, reason = _check_commit("fake-sha", provenance=provenance)
    assert verdict == "FAIL"
    assert "dispatch worktree agent is 'claude'" in reason


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

    read_only_text = delegate._augment_prompt_with_worktree(
        "inspect feature",
        Path("/tmp/dispatch-wt"),
        mode="read-only",
    )
    assert "LU_X_AGENT_TRAILER" not in read_only_text
