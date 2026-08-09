"""Integration tests for the repository-resolved pre-push pytest guard."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = REPO_ROOT / ".githooks" / "check-pytest-stamp.py"
STAMP_PATH = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "stamp-pytest.sh"
GIT_COMMON_DIR = Path(
    subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
        text=True, timeout=30,
    ).stdout.strip()
)
if not GIT_COMMON_DIR.is_absolute():
    GIT_COMMON_DIR = REPO_ROOT / GIT_COMMON_DIR
PYTHON = GIT_COMMON_DIR.resolve().parent / ".venv" / "bin" / "python"
ZERO_SHA = "0" * 40


def _load_hook_module():
    """Import the hook for unit-level assertions; it has no .py suffix, so load by path."""
    import importlib.machinery
    import importlib.util

    spec = importlib.util.spec_from_loader(
        "pre_push_hook",
        importlib.machinery.SourceFileLoader("pre_push_hook", str(GUARD_PATH)),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_environment(extra_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return an environment owned by this test's Git subprocesses.

    The agent-runtime Git shim rejects pushes to ``main`` when its
    ``AGENT_NO_MERGE`` guard is inherited. These tests create disposable
    repositories and must exercise their own hook, so remove that ambient
    policy as well as Git's worktree-specific variables.
    """
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.pop("AGENT_NO_MERGE", None)
    if extra_env:
        environment.update(extra_env)
    return environment


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        check=True,
        cwd=repo,
        env=_git_environment(env),
        text=True,
        timeout=30,
    )


def _repo_with_change(tmp_path: Path, changed_path: str = "tests/example.py") -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-b", "feature")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "initial")
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    changed = repo / changed_path
    changed.parent.mkdir(parents=True, exist_ok=True)
    changed.write_text("changed\n", encoding="utf-8")
    _git(repo, "add", changed_path)
    _git(repo, "commit", "-m", "change")
    local_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return repo, base_sha, local_sha


def _update(
    local_sha: str,
    remote_sha: str,
    *,
    local_ref: str = "refs/heads/feature",
    remote_ref: str = "refs/heads/main",
) -> str:
    return f"{local_ref} {local_sha} {remote_ref} {remote_sha}\n"


def _hook(
    repo: Path,
    update: str,
    *,
    tmpdir: Path,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = _git_environment()
    env["TMPDIR"] = str(tmpdir)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(PYTHON), str(GUARD_PATH), "origin", "unused"],
        capture_output=True,
        check=False,
        cwd=repo,
        env=env,
        input=update,
        text=True,
        timeout=30,
    )


def _stamp(tmp_path: Path, repo: Path, branch: str = "feature") -> Path:
    tmp_path.mkdir(exist_ok=True)
    hook = _load_hook_module()
    identity = hook.stamp_identity_for_branch(repo, branch)
    assert identity is not None
    return hook.marker_path(identity, {"TMPDIR": str(tmp_path)})


def _write_valid_stamp(tmp_path: Path, repo: Path, branch: str = "feature") -> Path:
    hook = _load_hook_module()
    identity = hook.stamp_identity_for_branch(repo, branch)
    assert identity is not None
    marker = hook.marker_path(identity, {"TMPDIR": str(tmp_path)})
    marker.parent.mkdir(exist_ok=True)
    marker.write_text(f"{identity.key}\n", encoding="utf-8")
    return marker


def _configure_guard_only_hook(repo: Path, tmp_path: Path) -> None:
    """Install only the custom guard for tests that isolate its Git behavior."""
    hook_dir = tmp_path / "guard-only-hooks"
    hook_dir.mkdir(exist_ok=True)
    hook = hook_dir / "pre-push"
    hook.write_text(
        f'#!/bin/sh\nexec "{PYTHON}" "{GUARD_PATH}" "$@"\n',
        encoding="utf-8",
    )
    hook.chmod(0o755)
    _git(repo, "config", "core.hooksPath", str(hook_dir))


def _run_stamp_writer(
    repo: Path,
    payload: dict[str, object],
    *,
    tmpdir: Path,
    hook_cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    resolved_payload = dict(payload)
    resolved_payload.setdefault("cwd", str(repo))
    resolved_payload.setdefault("hook_event_name", "PostToolUse")
    return subprocess.run(
        [str(STAMP_PATH)],
        capture_output=True,
        check=False,
        cwd=hook_cwd or repo,
        env=_git_environment({"TMPDIR": str(tmpdir)}),
        input=json.dumps(resolved_payload),
        text=True,
        timeout=30,
    )


def test_blocks_main_update_with_trigger_path_and_no_stamp(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=tmp_path / "stamps")

    assert result.returncode == 1
    assert "Rerun pytest" in result.stderr
    assert "git push --no-verify" in result.stderr


def test_allows_main_update_with_fresh_stamp(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)
    stamp = _write_valid_stamp(tmp_path / "stamps", repo)

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=stamp.parent)

    assert result.returncode == 0


def test_blocks_main_update_with_stamp_older_than_600_seconds(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)
    stamp = _write_valid_stamp(tmp_path / "stamps", repo)
    stale_time = time.time() - 601
    os.utime(stamp, (stale_time, stale_time))

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=stamp.parent)

    assert result.returncode == 1


def test_blocks_main_update_with_corrupt_stamp_content(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)
    stamp = _stamp(tmp_path / "stamps", repo)
    stamp.write_text("not-this-checkout\n", encoding="utf-8")

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=stamp.parent)

    assert result.returncode == 1
    assert "Rerun pytest" in result.stderr


@pytest.mark.parametrize(
    ("tmpdir_value", "expected_parent"),
    [
        ("", "/tmp"),  # empty: shell ${TMPDIR:-/tmp} treats this as unset
        (None, "/tmp"),  # genuinely unset
        ("relative-tmp", "/tmp"),  # non-absolute: cwd-dependent, so both sides refuse it
        ("/var/custom-tmp", "/var/custom-tmp"),  # ordinary absolute value is honoured
    ],
)
def test_marker_path_resolution_matches_the_stamp_writer(
    tmp_path,
    tmpdir_value,
    expected_parent,
    monkeypatch,
):
    """The reader must resolve TMPDIR exactly as `${TMPDIR:-/tmp}` does for the writer.

    Writer is `agents_extensions/shared/hooks/stamp-pytest.sh`. Two ways the two sides
    can disagree, both of which send the reader looking where the writer never wrote:

    * EMPTY TMPDIR — shell parameter expansion treats it as unset, but a Python
      `get("TMPDIR", "/tmp")` default does not; it yields "" and the marker becomes a
      relative path.
    * NON-ABSOLUTE TMPDIR — resolved against each side's own cwd, and those differ:
      the stamper runs from a PostToolUse cwd while git runs this hook from the
      worktree root. Both sides therefore refuse a relative value and fall back.

    This asserts the resolution rule directly, with no filesystem side effects — the
    earlier version created and deleted a real /tmp stamp, which could race and destroy
    a concurrent session's state (caught in cross-family review).
    """
    hook = _load_hook_module()
    if tmpdir_value is None:
        monkeypatch.delenv("TMPDIR", raising=False)
    else:
        monkeypatch.setenv("TMPDIR", tmpdir_value)

    repo, _, _ = _repo_with_change(tmp_path)
    identity = hook.stamp_identity_for_branch(repo, "feature")
    assert identity is not None
    marker = hook.marker_path(identity)

    assert marker.parent == Path(expected_parent)
    assert marker.name == f"learn-uk-pytest.v2.{identity.key}.stamp"
    assert marker.is_absolute(), "a relative marker path can never match the writer's"


def test_allows_non_triggering_paths(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path, "docs/example.md")

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=tmp_path / "stamps")

    assert result.returncode == 0


def test_allows_feature_destination_regardless_of_stamp(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)

    result = _hook(
        repo,
        _update(local_sha, remote_sha, remote_ref="refs/heads/some-feature"),
        tmpdir=tmp_path / "stamps",
    )

    assert result.returncode == 0


def test_head_to_main_from_non_main_branch_is_judged_from_remote_ref(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)

    result = _hook(
        repo,
        _update(local_sha, remote_sha, local_ref="HEAD"),
        tmpdir=tmp_path / "stamps",
    )

    assert result.returncode == 1


def test_branch_delete_is_allowed(tmp_path):
    repo, remote_sha, _ = _repo_with_change(tmp_path)

    result = _hook(repo, _update(ZERO_SHA, remote_sha), tmpdir=tmp_path / "stamps")

    assert result.returncode == 0


def test_new_remote_main_ref_uses_merge_base_fallback(tmp_path):
    repo, base_sha, local_sha = _repo_with_change(tmp_path)
    _git(repo, "update-ref", "refs/remotes/origin/main", base_sha)

    result = _hook(repo, _update(local_sha, ZERO_SHA), tmpdir=tmp_path / "stamps")

    assert result.returncode == 1


def test_unresolvable_range_refuses_main_update_with_actionable_override(tmp_path):
    repo, _, local_sha = _repo_with_change(tmp_path)

    result = _hook(repo, _update(local_sha, ZERO_SHA), tmpdir=tmp_path / "stamps")

    assert result.returncode == 1
    assert "could not determine changed paths" in result.stderr
    assert "git push --no-verify" in result.stderr


def test_skip_pytest_hook_environment_escapes(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)

    result = _hook(
        repo,
        _update(local_sha, remote_sha),
        tmpdir=tmp_path / "stamps",
        extra_env={"SKIP_PYTEST_HOOK": "1"},
    )

    assert result.returncode == 0


def test_stamp_filesystem_error_refuses_main_update_with_actionable_override(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)
    not_a_directory = tmp_path / "not-a-directory"
    not_a_directory.write_text("not a directory\n", encoding="utf-8")

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=not_a_directory)

    assert result.returncode == 1
    assert "could not inspect the pytest stamp" in result.stderr
    assert "git push --no-verify" in result.stderr


def test_unresolvable_local_ref_refuses_triggering_main_update(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)

    result = _hook(
        repo,
        _update(local_sha, remote_sha, local_ref=local_sha),
        tmpdir=tmp_path / "stamps",
    )

    assert result.returncode == 1
    assert "could not determine the local source branch" in result.stderr
    assert "git push --no-verify" in result.stderr


def test_git_environment_removes_the_agent_push_guard(monkeypatch):
    monkeypatch.setenv("AGENT_NO_MERGE", "1")

    assert "AGENT_NO_MERGE" not in _git_environment()


@pytest.mark.parametrize(
    "command",
    (
        ".venv/bin/python -m pytest tests/test_pre_push_hook.py -q",
        "/arbitrary/path/.venv/bin/python -m pytest tests/test_pre_push_hook.py -q",
    ),
)
def test_stamp_writer_records_captured_successful_pytest_runs(tmp_path, command):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"

    result = _run_stamp_writer(
        repo,
        {
            "tool_input": {"command": command},
            "tool_response": {"stdout": "2 passed in 0.01s"},
        },
        tmpdir=stamp_dir,
    )

    assert result.returncode == 0
    assert _stamp(stamp_dir, repo).exists()


def test_stamp_writer_leaves_no_stamp_from_detached_head(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    _git(repo, "checkout", "--detach", "HEAD")

    result = _run_stamp_writer(
        repo,
        {
            "tool_input": {"command": ".venv/bin/python -m pytest tests/test_pre_push_hook.py -q"},
            "tool_response": {"stdout": "2 passed in 0.01s"},
        },
        tmpdir=stamp_dir,
    )

    assert result.returncode == 0
    assert not stamp_dir.exists()


def test_stamp_writer_does_not_fallback_to_system_python(tmp_path):
    repo = tmp_path / "repo-without-venv"
    hook = repo / "agents_extensions/shared/hooks/stamp-pytest.sh"
    helper = repo / ".githooks/pytest_stamp.py"
    fake_bin = tmp_path / "fake-bin"
    system_python_log = tmp_path / "system-python.log"
    hook.parent.mkdir(parents=True)
    helper.parent.mkdir(parents=True)
    fake_bin.mkdir()
    shutil.copy2(STAMP_PATH, hook)
    helper.write_text("raise SystemExit(99)\n", encoding="utf-8")
    (repo / "package.json").write_text("{}\n", encoding="utf-8")
    _git(repo, "init", "-b", "feature")
    fake_python = fake_bin / "python3"
    fake_python.write_text(
        '#!/bin/sh\nprintf "called\\n" >> "$SYSTEM_PYTHON_LOG"\n',
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    environment = _git_environment(
        {
            "CLAUDE_PROJECT_DIR": str(repo),
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "SYSTEM_PYTHON_LOG": str(system_python_log),
        }
    )

    result = subprocess.run(
        [str(hook)],
        capture_output=True,
        check=False,
        cwd=repo,
        env=environment,
        input=json.dumps(
            {
                "cwd": str(repo),
                "hook_event_name": "PostToolUse",
                "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q"},
            }
        ),
        text=True,
        timeout=30,
    )

    assert result.returncode == 0
    assert not system_python_log.exists()


def test_stamp_writer_uses_tool_workdir_instead_of_hook_process_cwd(tmp_path):
    tested_repo, _, _ = _repo_with_change(tmp_path / "tested")
    hook_repo, _, _ = _repo_with_change(tmp_path / "hook")
    _git(hook_repo, "branch", "-m", "main")
    stamp_dir = tmp_path / "stamps"
    payload = {
        "cwd": str(hook_repo),
        "hook_event_name": "PostToolUse",
        "tool_input": {
            "command": ".venv/bin/python -m pytest tests/ -q",
            "workdir": str(tested_repo),
        },
        "tool_response": {"stdout": "2 passed in 0.01s"},
    }

    result = _run_stamp_writer(
        tested_repo,
        payload,
        tmpdir=stamp_dir,
        hook_cwd=hook_repo,
    )

    assert result.returncode == 0
    assert _stamp(stamp_dir, tested_repo).exists()
    assert not _stamp(stamp_dir, hook_repo, "main").exists()


def test_successful_shell_wrapper_does_not_mask_failed_pytest(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q || true"},
        "tool_output": "================== 1 failed, 19 passed in 0.65s ==================",
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert not _stamp(stamp_dir, repo).exists()


def test_codex_post_tool_use_with_failed_pytest_output_does_not_stamp(tmp_path):
    """Codex emits PostToolUse even when Bash exits nonzero."""
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q"},
        "tool_response": {"stdout": "1 failed, 0 passed in 0.10s"},
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert not _stamp(stamp_dir, repo).exists()


def test_codex_post_tool_use_with_passing_pytest_output_stamps(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q"},
        "tool_response": {"stdout": "2 passed in 0.01s"},
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert _stamp(stamp_dir, repo).exists()


def test_codex_post_tool_use_with_no_tests_ran_does_not_stamp(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_input": {"command": ".venv/bin/python -m pytest -k matches_nothing -q"},
        "tool_response": {"stdout": "no tests ran in 0.00s"},
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert not _stamp(stamp_dir, repo).exists()


@pytest.mark.parametrize(
    "output_payload",
    (
        {},
        {"tool_output": ""},
        {"tool_response": {"stdout": ""}},
        {"tool_response": {"stdout": None}},
    ),
)
def test_codex_post_tool_use_with_missing_or_empty_output_does_not_stamp(tmp_path, output_payload):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload: dict[str, object] = {
        "hook_event_name": "PostToolUse",
        "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q"},
    }
    payload.update(output_payload)

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert not _stamp(stamp_dir, repo).exists()


def test_codex_post_tool_use_with_mixed_passing_and_failing_summaries_does_not_stamp(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q"},
        "tool_response": {
            "stdout": "2 passed in 0.01s\n1 failed, 1 passed in 0.01s"
        },
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert not _stamp(stamp_dir, repo).exists()


@pytest.mark.parametrize(
    "command",
    (
        ".venv/bin/python -m pytest --collect-only",
        ".venv/bin/python -m pytest --co",
        ".venv/bin/python -m pytest --help",
    ),
)
def test_successful_non_execution_pytest_modes_do_not_stamp(tmp_path, command):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"

    result = _run_stamp_writer(
        repo,
        {
            "hook_event_name": "PostToolUse",
            "tool_input": {"command": command},
        },
        tmpdir=stamp_dir,
    )

    assert result.returncode == 0
    assert not _stamp(stamp_dir, repo).exists()


def test_command_level_directory_change_is_not_misattributed_to_payload_cwd(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_input": {"command": "cd elsewhere && .venv/bin/python -m pytest -q"},
        "tool_output": "====================== 10 passed in 0.40s ======================",
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert not _stamp(stamp_dir, repo).exists()


def test_every_pytest_segment_must_have_a_passing_summary(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_input": {
            "command": (
                ".venv/bin/python -m pytest tests/first.py -q; "
                ".venv/bin/python -m pytest tests/second.py -q || true"
            )
        },
        "tool_output": "====================== 10 passed in 0.40s ======================",
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert not _stamp(stamp_dir, repo).exists()


@pytest.mark.parametrize(
    ("output", "should_stamp"),
    (
        ("============================= 20 passed in 0.65s ==============================", True),
        ("============================= 1 failed, 19 passed in 0.65s ==============================", False),
        ("============================= no tests ran in 0.12s ==============================", False),
    ),
)
def test_stamp_writer_checks_pytest_result_after_a_compound_command(tmp_path, output, should_stamp):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload = {
        "hook_event_name": "PostToolUseFailure",
        "tool_input": {"command": ".venv/bin/python -m pytest tests/ -v && exit 1"},
        "tool_output": output,
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert _stamp(stamp_dir, repo).exists() is should_stamp


def test_nested_known_tool_response_can_prove_compound_pytest_success(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    payload = {
        "hook_event_name": "PostToolUseFailure",
        "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q && exit 1"},
        "tool_response": {
            "stdout": "====================== 10 passed in 0.40s ======================"
        },
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert _stamp(stamp_dir, repo).exists()


def test_unrelated_payload_text_cannot_fake_a_passing_summary(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    stamp_dir = tmp_path / "stamps"
    passing_text = "====================== 10 passed in 0.40s ======================"
    payload = {
        "hook_event_name": "PostToolUseFailure",
        "tool_input": {
            "command": ".venv/bin/python -m pytest tests/ -q && exit 1",
            "description": passing_text,
        },
        "metadata": {"note": passing_text},
    }

    result = _run_stamp_writer(repo, payload, tmpdir=stamp_dir)

    assert result.returncode == 0
    assert not _stamp(stamp_dir, repo).exists()


def test_same_branch_name_in_another_repo_cannot_reuse_stamp(tmp_path):
    first_repo, _, _ = _repo_with_change(tmp_path / "first")
    second_repo, remote_sha, local_sha = _repo_with_change(tmp_path / "second")
    stamp_dir = tmp_path / "stamps"

    writer = _run_stamp_writer(
        first_repo,
        {
            "hook_event_name": "PostToolUse",
            "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q"},
            "tool_response": {"stdout": "2 passed in 0.01s"},
        },
        tmpdir=stamp_dir,
    )
    guarded_push = _hook(
        second_repo,
        _update(local_sha, remote_sha),
        tmpdir=stamp_dir,
    )

    assert writer.returncode == 0
    assert _stamp(stamp_dir, first_repo).exists()
    assert _stamp(stamp_dir, first_repo) != _stamp(stamp_dir, second_repo)
    assert guarded_push.returncode == 1


def test_no_verify_skips_hook_for_an_actual_push(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    remote = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
        env=_git_environment(),
        text=True,
        timeout=30,
    )
    _git(repo, "remote", "add", "origin", str(remote))
    _configure_guard_only_hook(repo, tmp_path)

    result = subprocess.run(
        ["git", "push", "--no-verify", "origin", "HEAD:main"],
        capture_output=True,
        check=False,
        cwd=repo,
        env=_git_environment(),
        text=True,
        timeout=30,
    )

    assert result.returncode == 0


def test_actual_head_to_main_push_is_blocked_from_a_non_main_branch(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    remote = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
        env=_git_environment(),
        text=True,
        timeout=30,
    )
    _git(repo, "remote", "add", "origin", str(remote))
    _configure_guard_only_hook(repo, tmp_path)
    _git(repo, "push", "--no-verify", "origin", "HEAD:main")

    (repo / "tests" / "second.py").write_text("second change\n", encoding="utf-8")
    _git(repo, "add", "tests/second.py")
    _git(repo, "commit", "-m", "second change")

    result = subprocess.run(
        ["git", "push", "origin", "HEAD:main"],
        capture_output=True,
        check=False,
        cwd=repo,
        env=_git_environment(),
        text=True,
        timeout=30,
    )

    assert result.returncode == 1
    assert "Push to main blocked" in result.stderr


def test_actual_head_to_main_push_accepts_stamp_for_the_invoking_worktree(tmp_path):
    repo, _, _ = _repo_with_change(tmp_path)
    remote = tmp_path / "remote.git"
    stamp_dir = tmp_path / "stamps"
    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
        env=_git_environment(),
        text=True,
        timeout=30,
    )
    _git(repo, "remote", "add", "origin", str(remote))
    _configure_guard_only_hook(repo, tmp_path)
    _git(repo, "push", "--no-verify", "origin", "HEAD:main")

    (repo / "tests" / "second.py").write_text("second change\n", encoding="utf-8")
    _git(repo, "add", "tests/second.py")
    _git(repo, "commit", "-m", "second change")
    writer = _run_stamp_writer(
        repo,
        {
            "hook_event_name": "PostToolUse",
            "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q"},
            "tool_response": {"stdout": "2 passed in 0.01s"},
        },
        tmpdir=stamp_dir,
    )

    result = subprocess.run(
        ["git", "push", "origin", "HEAD:main"],
        capture_output=True,
        check=False,
        cwd=repo,
        env=_git_environment({"TMPDIR": str(stamp_dir)}),
        text=True,
        timeout=30,
    )

    assert writer.returncode == 0
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "historical_shell_form",
    (
        "cd worktree && cd main && git push",
        "pushd worktree; popd; git push",
        "git -C main push",
    ),
)
def test_shell_forms_cannot_change_a_stdin_ref_verdict(tmp_path, historical_shell_form):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)

    result = _hook(
        repo,
        _update(local_sha, remote_sha),
        tmpdir=tmp_path / "stamps",
        extra_env={"HISTORICAL_SHELL_FORM": historical_shell_form},
    )

    assert result.returncode == 1


def test_poisoned_git_environment_cannot_change_a_stdin_ref_verdict(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)

    result = _hook(
        repo,
        _update(local_sha, remote_sha),
        tmpdir=tmp_path / "stamps",
        extra_env={
            "GIT_OBJECT_DIRECTORY": "not-a-git-object-directory",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": "not-an-alternate-object-directory",
            "GIT_COMMON_DIR": "not-a-git-common-directory",
        },
    )

    assert result.returncode == 1
