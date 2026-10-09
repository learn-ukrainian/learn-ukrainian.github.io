"""Real temporary Git checkouts for dispatch tests that mock worker spawning."""

import subprocess
from pathlib import Path
from unittest.mock import patch


def isolate_dispatch_repo(monkeypatch, tmp_path, delegate):
    """Keep automatic read-only provisioning off the shared primary checkout.

    Git remains real even when the test replaces Popen to observe or fail the
    worker launch. Base resolution is pinned to this local fixture's HEAD.
    """
    real_run = subprocess.run
    real_popen = subprocess.Popen
    source = Path(__file__).resolve().parents[2]
    primary = tmp_path / "dispatch-source"
    for command in (
        ["git", "clone", "--quiet", "--shared", "--single-branch", "--no-checkout", str(source), str(primary)],
        [
            "git",
            "-C",
            str(primary),
            "sparse-checkout",
            "set",
            "--no-cone",
            "/scripts/delegate.py",
            "/scripts/config.py",
            "/scripts/config/",
            "/scripts/common/",
            "/scripts/ci/",
            "/scripts/agent_runtime/",
            "/scripts/orchestration/",
            "/agents_extensions/shared/rules/",
            "/.mcp/",
            "/tests/__init__.py",
            "/tests/helpers/",
            "/.gitignore",
            "/pyproject.toml",
        ],
        ["git", "-C", str(primary), "checkout", "--quiet", "-B", "main", "HEAD"],
        [
            "git",
            "-C",
            str(primary),
            "remote",
            "set-url",
            "origin",
            "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git",
        ],
    ):
        real_run(command, check=True, capture_output=True, timeout=60, env=delegate._sanitized_git_env())
    head = real_run(
        ["git", "-C", str(primary), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        env=delegate._sanitized_git_env(),
    ).stdout.strip()
    (primary / "docs").mkdir(exist_ok=True)
    (primary / "site/src").mkdir(parents=True, exist_ok=True)
    original_base = delegate._resolve_worktree_base_sha
    original_ensure = delegate._ensure_worktree
    original_add = delegate._run_worktree_add

    def base(**kwargs):
        return head if primary == delegate._REPO_ROOT else original_base(**kwargs)

    def git_run(command, *args, **kwargs):
        if command and Path(command[0]).name == "git":
            with patch.object(subprocess, "Popen", real_popen):
                return real_run(command, *args, **kwargs)
        return real_run(command, *args, **kwargs)

    def add(command, **kwargs):
        command = list(command)
        command.insert(command.index("add") + 1, "--no-checkout")
        return original_add(command, **kwargs)

    def sparse(worktree, **_kwargs):
        patterns = real_run(
            ["git", "-C", str(primary), "sparse-checkout", "list"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.splitlines()
        real_run(
            ["git", "-C", str(worktree), "sparse-checkout", "set", "--no-cone", *patterns],
            check=True,
            capture_output=True,
            timeout=30,
        )
        real_run(["git", "-C", str(worktree), "reset", "--hard", "HEAD"], check=True, capture_output=True, timeout=30)
        return {"fixture_sparse": True}

    def ensure(**kwargs):
        with (
            patch.object(subprocess, "Popen", real_popen),
            patch.object(subprocess, "run", real_run),
            patch.object(delegate, "_run_worktree_add", add),
            patch.object(delegate, "_apply_dispatch_sparse_checkout", sparse),
        ):
            return original_ensure(**kwargs)

    monkeypatch.chdir(primary)
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", base)
    monkeypatch.setattr(delegate, "_ensure_worktree", ensure)
    monkeypatch.setattr(subprocess, "run", git_run)
    return primary
