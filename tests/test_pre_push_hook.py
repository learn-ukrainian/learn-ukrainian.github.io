"""Integration tests for the repository-resolved pre-push pytest guard."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / ".githooks" / "pre-push"
PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
ZERO_SHA = "0" * 40


def _load_hook_module():
    """Import the hook for unit-level assertions; it has no .py suffix, so load by path."""
    import importlib.machinery
    import importlib.util

    spec = importlib.util.spec_from_loader(
        "pre_push_hook",
        importlib.machinery.SourceFileLoader("pre_push_hook", str(HOOK_PATH)),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_environment(extra_env: dict[str, str] | None = None) -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
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
    repo.mkdir()
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
        [str(PYTHON), str(HOOK_PATH), "origin", "unused"],
        capture_output=True,
        check=False,
        cwd=repo,
        env=env,
        input=update,
        text=True,
        timeout=30,
    )


def _stamp(tmp_path: Path, branch: str = "feature") -> Path:
    tmp_path.mkdir(exist_ok=True)
    return tmp_path / f"learn-uk-pytest.{branch}.stamp"


def test_blocks_main_update_with_trigger_path_and_no_stamp(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=tmp_path / "stamps")

    assert result.returncode == 1
    assert "Rerun pytest" in result.stderr
    assert "git push --no-verify" in result.stderr


def test_allows_main_update_with_fresh_stamp(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)
    stamp = _stamp(tmp_path / "stamps")
    stamp.touch()

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=stamp.parent)

    assert result.returncode == 0


def test_blocks_main_update_with_stamp_older_than_600_seconds(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)
    stamp = _stamp(tmp_path / "stamps")
    stamp.touch()
    stale_time = time.time() - 601
    os.utime(stamp, (stale_time, stale_time))

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=stamp.parent)

    assert result.returncode == 1


@pytest.mark.parametrize(
    ("tmpdir_value", "expected_parent"),
    [
        ("", "/tmp"),  # empty: shell ${TMPDIR:-/tmp} treats this as unset
        (None, "/tmp"),  # genuinely unset
        ("relative-tmp", "/tmp"),  # non-absolute: cwd-dependent, so both sides refuse it
        ("/var/custom-tmp", "/var/custom-tmp"),  # ordinary absolute value is honoured
    ],
)
def test_marker_path_resolution_matches_the_stamp_writer(tmpdir_value, expected_parent, monkeypatch):
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

    marker = hook._marker_path("feature")

    assert marker.parent == Path(expected_parent)
    assert marker.name == "learn-uk-pytest.feature.stamp"
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


def test_unresolvable_range_fails_open(tmp_path):
    repo, _, local_sha = _repo_with_change(tmp_path)

    result = _hook(repo, _update(local_sha, ZERO_SHA), tmpdir=tmp_path / "stamps")

    assert result.returncode == 0


def test_skip_pytest_hook_environment_escapes(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)

    result = _hook(
        repo,
        _update(local_sha, remote_sha),
        tmpdir=tmp_path / "stamps",
        extra_env={"SKIP_PYTEST_HOOK": "1"},
    )

    assert result.returncode == 0


def test_stamp_filesystem_error_fails_open(tmp_path):
    repo, remote_sha, local_sha = _repo_with_change(tmp_path)
    not_a_directory = tmp_path / "not-a-directory"
    not_a_directory.write_text("not a directory\n", encoding="utf-8")

    result = _hook(repo, _update(local_sha, remote_sha), tmpdir=not_a_directory)

    assert result.returncode == 0


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
    _git(repo, "config", "core.hooksPath", str(REPO_ROOT / ".githooks"))

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
    _git(repo, "config", "core.hooksPath", str(REPO_ROOT / ".githooks"))
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
