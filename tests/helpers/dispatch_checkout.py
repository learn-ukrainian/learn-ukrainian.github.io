"""Real temporary Git checkouts for dispatch tests that mock worker spawning."""

import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

_SPARSE_PATTERNS = (
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
)

# One template per (source checkout, source HEAD) per Python process. Under
# xdist every worker is its own process and builds its own template, so no
# mutable state is shared across workers. A template is never handed to a
# test; each test receives a private directory copy of it. Templates live in
# the worker's pytest basetemp (``tests/conftest.py`` registers the factory):
# tests patch ``tempfile.gettempdir`` and sweep that directory per test, which
# would delete a template kept there.
_TEMPLATES: dict[tuple[str, str], tuple[Path, str]] = {}
_TEMPLATE_FACTORY: pytest.TempPathFactory | None = None


def register_template_factory(factory: pytest.TempPathFactory) -> None:
    global _TEMPLATE_FACTORY
    _TEMPLATE_FACTORY = factory


def _git(real_run, env, *args: str) -> str:
    return real_run(["git", *args], check=True, capture_output=True, text=True, timeout=60, env=env).stdout.strip()


def _build_template(real_run, env, source: Path, destination: Path) -> str:
    """Create the sparse shared clone; return its HEAD sha."""
    for command in (
        ["clone", "--quiet", "--shared", "--single-branch", "--no-checkout", str(source), str(destination)],
        ["-C", str(destination), "sparse-checkout", "set", "--no-cone", *_SPARSE_PATTERNS],
        ["-C", str(destination), "checkout", "--quiet", "-B", "main", "HEAD"],
        [
            "-C",
            str(destination),
            "remote",
            "set-url",
            "origin",
            "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git",
        ],
    ):
        _git(real_run, env, *command)
    return _git(real_run, env, "-C", str(destination), "rev-parse", "HEAD")


def _template_for(real_run, env, source: Path) -> tuple[Path, str]:
    key = (str(source), _git(real_run, env, "-C", str(source), "rev-parse", "HEAD"))
    if key not in _TEMPLATES:
        if _TEMPLATE_FACTORY is None:
            raise RuntimeError("dispatch template factory not registered; tests/conftest.py provides it")
        destination = _TEMPLATE_FACTORY.mktemp("dispatch-source-template")
        head = _build_template(real_run, env, source, destination)
        _TEMPLATES[key] = (destination, head)
    return _TEMPLATES[key]


def isolate_dispatch_repo(monkeypatch, tmp_path, delegate):
    """Keep automatic read-only provisioning off the shared primary checkout.

    Git remains real even when the test replaces Popen to observe or fail the
    worker launch. Base resolution is pinned to this local fixture's HEAD.

    The sparse clone (clone, sparse-checkout set, checkout) is built once per
    process; each call gets a private directory copy of it, so tests that
    commit, branch or add worktrees never see each other's changes.
    """
    real_run = subprocess.run
    real_popen = subprocess.Popen
    source = Path(__file__).resolve().parents[2]
    primary = tmp_path / "dispatch-source"
    template, head = _template_for(real_run, delegate._sanitized_git_env(), source)
    # The copy owns its .git (refs, index, config, worktrees, HEAD); only
    # objects/info/alternates points back at the source object store.
    shutil.copytree(template, primary, symlinks=True)
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
