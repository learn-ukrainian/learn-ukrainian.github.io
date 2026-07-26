"""Integration coverage for the tracked ``core.hooksPath`` chain."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_DIR = REPO_ROOT / ".githooks"
REQUIRED_HOOKS = (
    "pre-commit",
    "commit-msg",
    "pre-push",
    "post-merge",
    "post-checkout",
    "post-commit",
)


def _clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.pop("AGENT_NO_MERGE", None)
    if extra:
        env.update(extra)
    return env


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        check=check,
        cwd=cwd,
        env=_clean_env(env),
        input=input_text,
        text=True,
        timeout=60,
    )


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=repo, env=env)


def _write_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _project_python() -> Path:
    common_dir = Path(
        _git(REPO_ROOT, "rev-parse", "--git-common-dir").stdout.strip()
    )
    if not common_dir.is_absolute():
        common_dir = REPO_ROOT / common_dir
    return common_dir.resolve().parent / ".venv" / "bin" / "python"


def _fixture_repository(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "hook-test@example.invalid")
    _git(repo, "config", "user.name", "Hook Test")

    shutil.copytree(HOOK_DIR, repo / ".githooks")
    (repo / "scripts").mkdir()
    shutil.copy2(REPO_ROOT / "scripts/install_git_hooks.sh", repo / "scripts/install_git_hooks.sh")
    _write_executable(
        repo / "scripts/pre_commit/project_python.sh",
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'exec "{_project_python()}" "$@"\n',
    )
    _write_executable(
        repo / "scripts/guardrails/primary_post_checkout_heal.sh",
        "#!/usr/bin/env bash\n"
        'printf "primary-heal\\n" >> "$HOOK_LOG"\n',
    )
    (repo / "scripts/guardrails/primary_write_guard.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        'with Path(os.environ["HOOK_LOG"]).open("a", encoding="utf-8") as stream:\n'
        '    stream.write("primary-write-guard\\n")\n',
        encoding="utf-8",
    )
    (repo / ".pre-commit-config.yaml").write_text(
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: fixture-pre-commit\n"
        "        name: fixture pre-commit\n"
        "        entry: bash -c 'printf \"pre-commit\\\\n\" >> \"$HOOK_LOG\"'\n"
        "        language: system\n"
        "        pass_filenames: false\n"
        "        stages: [pre-commit]\n"
        "      - id: fixture-commit-msg\n"
        "        name: fixture commit-msg\n"
        "        entry: bash -c 'printf \"commit-msg\\\\n\" >> \"$HOOK_LOG\"'\n"
        "        language: system\n"
        "        pass_filenames: false\n"
        "        stages: [commit-msg]\n"
        "      - id: fixture-pre-push\n"
        "        name: fixture pre-push\n"
        "        entry: bash -c 'printf \"pre-push:%s\\\\n\" \"$*\" >> \"$HOOK_LOG\"' --\n"
        "        language: system\n"
        "        files: ^docs\\.md$\n"
        "        stages: [pre-push]\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("base\n", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    _write_executable(
        bin_dir / "git-lfs",
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'printf "lfs-%s\\n" "$1" >> "$HOOK_LOG"\n'
        'if [[ "$1" == "pre-push" ]]; then\n'
        '  while IFS= read -r update; do printf "%s\\n" "$update" >> "$LFS_STDIN_LOG"; done\n'
        "fi\n"
        'if [[ "$1" == "post-checkout" && "${FAIL_LFS_POST_CHECKOUT:-0}" == "1" ]]; then\n'
        "  exit 42\n"
        "fi\n",
    )
    hook_log = tmp_path / "hook.log"
    lfs_stdin_log = tmp_path / "lfs-stdin.log"
    stamp_dir = tmp_path / "stamps"
    stamp_dir.mkdir()
    env = {
        "HOOK_LOG": str(hook_log),
        "LFS_STDIN_LOG": str(lfs_stdin_log),
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "PRE_COMMIT_HOME": str(tmp_path / "pre-commit-cache"),
        "TMPDIR": str(stamp_dir),
    }

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial", env=env)
    _run(["git", "init", "--bare", str(remote)], cwd=tmp_path, env=env)
    _git(repo, "remote", "add", "origin", str(remote), env=env)
    _git(repo, "push", "--no-verify", "origin", "HEAD:main", env=env)
    return repo, remote, env


def test_tracked_hook_chain_is_complete_and_executable():
    for hook_name in REQUIRED_HOOKS:
        hook = HOOK_DIR / hook_name
        assert hook.is_file(), hook_name
        assert os.access(hook, os.X_OK), hook_name
    assert (HOOK_DIR / "_lib.sh").is_file()
    assert (HOOK_DIR / "check-pytest-stamp.py").is_file()
    assert not os.access(HOOK_DIR / "check-pytest-stamp.py", os.X_OK)


def test_installer_and_all_hook_functions_run(tmp_path):
    repo, _, env = _fixture_repository(tmp_path)
    hook_log = Path(env["HOOK_LOG"])

    install = _run(["bash", "scripts/install_git_hooks.sh"], cwd=repo, env=env)
    assert "complete tracked Git hook chain" in install.stdout
    assert _git(repo, "config", "--get", "core.hooksPath", env=env).stdout.strip() == ".githooks"

    _git(repo, "checkout", "-b", "feature", env=env)
    (repo / "docs.md").write_text("docs-only change\n", encoding="utf-8")
    _git(repo, "add", "docs.md", env=env)
    _git(repo, "commit", "-m", "docs change", env=env)
    push = _git(repo, "push", "origin", "feature:main", env=env)
    assert push.returncode == 0

    _run([str(repo / ".githooks/post-merge"), "0"], cwd=repo, env=env)

    calls = hook_log.read_text(encoding="utf-8").splitlines()
    assert "primary-heal" in calls
    assert "pre-commit" in calls
    assert "commit-msg" in calls
    assert "pre-push:docs.md" in calls
    assert "primary-write-guard" in calls
    assert "lfs-post-checkout" in calls
    assert "lfs-post-commit" in calls
    assert "lfs-pre-push" in calls

    updates = Path(env["LFS_STDIN_LOG"]).read_text(encoding="utf-8").splitlines()
    assert len(updates) == 1
    assert updates[0].split()[0] == "refs/heads/feature"
    assert updates[0].split()[2] == "refs/heads/main"


def test_installer_refuses_an_incomplete_hook_directory(tmp_path):
    repo, _, env = _fixture_repository(tmp_path)
    (repo / ".githooks/commit-msg").unlink()

    result = _run(
        ["bash", "scripts/install_git_hooks.sh"],
        cwd=repo,
        env=env,
        check=False,
    )

    assert result.returncode == 1
    assert "Expected executable hook" in result.stderr


def test_post_checkout_heals_even_when_lfs_fails(tmp_path):
    repo, _, env = _fixture_repository(tmp_path)
    _run(["bash", "scripts/install_git_hooks.sh"], cwd=repo, env=env)

    result = _run(
        [str(repo / ".githooks/post-checkout"), "old", "new", "1"],
        cwd=repo,
        env={**env, "FAIL_LFS_POST_CHECKOUT": "1"},
        check=False,
    )

    assert result.returncode == 42
    calls = Path(env["HOOK_LOG"]).read_text(encoding="utf-8").splitlines()
    assert calls[-2:] == ["lfs-post-checkout", "primary-heal"]


def test_full_pre_push_chain_replays_updates_to_the_pytest_guard(tmp_path):
    repo, _, env = _fixture_repository(tmp_path)
    _run(["bash", "scripts/install_git_hooks.sh"], cwd=repo, env=env)
    _git(repo, "checkout", "-b", "feature", env=env)
    trigger = repo / "tests" / "trigger.py"
    trigger.parent.mkdir()
    trigger.write_text("TRIGGER = True\n", encoding="utf-8")
    _git(repo, "add", "tests/trigger.py", env=env)
    _git(repo, "commit", "-m", "trigger tests", env=env)

    blocked = _run(
        ["git", "push", "origin", "feature:main"],
        cwd=repo,
        env=env,
        check=False,
    )
    assert blocked.returncode == 1
    assert "Push to main blocked" in blocked.stderr

    stamp = Path(env["TMPDIR"]) / "learn-uk-pytest.feature.stamp"
    stamp.touch()
    pushed = _git(repo, "push", "origin", "feature:main", env=env)
    assert pushed.returncode == 0
    calls = Path(env["HOOK_LOG"]).read_text(encoding="utf-8").splitlines()
    assert "lfs-pre-push" in calls


def test_installer_materializes_hooks_in_a_sparse_linked_worktree(tmp_path):
    repo, _, env = _fixture_repository(tmp_path)
    sparse = tmp_path / "sparse-worktree"
    _git(repo, "worktree", "add", "-b", "sparse-test", str(sparse), env=env)
    _git(sparse, "sparse-checkout", "init", "--no-cone", env=env)
    _git(sparse, "sparse-checkout", "set", "README.md", env=env)

    assert not (sparse / ".githooks").exists()

    _run(["bash", "scripts/install_git_hooks.sh"], cwd=repo, env=env)
    _run(["bash", "scripts/install_git_hooks.sh"], cwd=repo, env=env)

    for hook_name in REQUIRED_HOOKS:
        assert (sparse / ".githooks" / hook_name).is_file()

    hook_log = Path(env["HOOK_LOG"])
    before = hook_log.read_text(encoding="utf-8").splitlines() if hook_log.exists() else []
    (sparse / "README.md").write_text("sparse change\n", encoding="utf-8")
    _git(sparse, "add", "README.md", env=env)
    _run(["bash", ".githooks/pre-commit"], cwd=sparse, env=env)
    after = hook_log.read_text(encoding="utf-8").splitlines()
    assert after.count("pre-commit") == before.count("pre-commit") + 1


@pytest.mark.parametrize("hook_name", REQUIRED_HOOKS)
def test_hook_scripts_have_valid_bash_syntax(hook_name):
    result = _run(["bash", "-n", str(HOOK_DIR / hook_name)], cwd=REPO_ROOT)
    assert result.returncode == 0
