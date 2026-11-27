"""Integration coverage for the tracked Git hook delegator chain."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest

from tests.githooks import BINDING_ASSERTED, bind_hook_host_context
from tests.helpers.python import project_python

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
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_") and key not in BINDING_ASSERTED
    }
    env.pop("AGENT_NO_MERGE", None)
    env.pop("LEARN_UKRAINIAN_DISPATCH_TASK_ID", None)  # the fixture is not the invoking task's checkout
    if extra:
        env.update(extra)
    # Fixture Git must bypass the agent command shims, including local bare remotes.
    env["PATH"] = ":".join(part for part in env.get("PATH", os.defpath).split(":") if "agent_runtime/shims" not in part)
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


def _git(
    repo: Path,
    *args: str,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=repo, env=env, check=check)


def _write_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _project_python() -> str:
    return project_python()


def _fixture_repository(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "hook-test@example.invalid")
    _git(repo, "config", "user.name", "Hook Test")

    shutil.copytree(HOOK_DIR, repo / ".githooks")
    (repo / "scripts/lib").mkdir(parents=True)
    _write_executable(
        repo / "scripts/lib/project_interpreter.sh",
        "#!/usr/bin/env bash\nsource " + shlex.quote(str(files("lu_machinery.lib").joinpath("project_interpreter.sh"))) + "\n",
    )
    from tests.githooks import install_message_scanner

    install_message_scanner(repo)
    shutil.copy2(Path(str(files("lu_machinery").joinpath("install_git_hooks.sh"))), repo / "scripts/install_git_hooks.sh")
    # The post-merge guard runs from the installed release; the fixture records that call instead.
    _write_executable(
        repo / "scripts/pre_commit/project_python.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'if [[ "$*" == "-P -m lu_machinery.guardrails.primary_write_guard apply --hook" ]]; then\n'
        '  printf "primary-write-guard\\n" >> "$HOOK_LOG"\n'
        "  exit 0\n"
        "fi\n"
        f'exec "{_project_python()}" "$@"\n',
    )
    # The gate always runs this scanner from the repo being pushed. The fixture
    # has no secrets; the real scanner is covered by the opsec and gate tests.
    _write_executable(
        repo / "scripts/audit/lint_opsec_leaks.py",
        "import sys\nraise SystemExit(0)\n",
    )
    _write_executable(
        repo / "scripts/guardrails/primary_post_checkout_heal.sh",
        '#!/usr/bin/env bash\nprintf "primary-heal\\n" >> "$HOOK_LOG"\n',
    )
    (repo / ".pre-commit-config.yaml").write_text(
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: fixture-pre-commit\n"
        "        name: fixture pre-commit\n"
        '        entry: bash -c \'printf "pre-commit\\\\n" >> "$HOOK_LOG"\'\n'
        "        language: system\n"
        "        pass_filenames: false\n"
        "        stages: [pre-commit]\n"
        "      - id: fixture-commit-msg\n"
        "        name: fixture commit-msg\n"
        '        entry: bash -c \'printf "commit-msg\\\\n" >> "$HOOK_LOG"\'\n'
        "        language: system\n"
        "        pass_filenames: false\n"
        "        stages: [commit-msg]\n"
        "      - id: check-no-internal-ids\n"
        "        name: fixture internal ids\n"
        "        entry: bash -c 'exit 0'\n"
        "        language: system\n"
        "        pass_filenames: false\n"
        "        stages: [pre-commit]\n"
        "      - id: fixture-pre-push\n"
        "        name: fixture pre-push\n"
        '        entry: bash -c \'printf "pre-push:%s\\\\n" "$*" >> "$HOOK_LOG"\' --\n'
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
        "fi\n"
        'if [[ "$1" == "post-merge" && "${FAIL_LFS_POST_MERGE:-0}" == "1" ]]; then\n'
        "  exit 43\n"
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
    # post-checkout asks the runtime for the installed heal script; the fixture records that call.
    heal = shlex.quote(str(repo / "scripts/guardrails/primary_post_checkout_heal.sh"))
    bind_hook_host_context(
        tmp_path, env, product=repo, python=_project_python(),
        runtime_preamble=(
            'if [[ "${1-}" == -I && "${2-}" == -c && "${3-}" == *guardrails/primary_post_checkout_heal.sh* ]]; then\n'
            f"  echo {heal}; exit 0\n"
            "fi\n"
        ),
    )

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
    assert install.returncode == 0
    assert "pre-commit: installed" in install.stdout
    assert _git(repo, "config", "--get", "core.hooksPath", env=env, check=False).returncode != 0

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
    assert "lfs-post-merge" in calls

    updates = Path(env["LFS_STDIN_LOG"]).read_text(encoding="utf-8").splitlines()
    assert len(updates) == 1
    assert updates[0].split()[0] == "refs/heads/feature"
    assert updates[0].split()[2] == "refs/heads/main"


def test_installer_refuses_missing_hook_directory(tmp_path):
    repo, _, env = _fixture_repository(tmp_path)
    shutil.rmtree(repo / ".githooks")

    result = _run(
        ["bash", "scripts/install_git_hooks.sh"],
        cwd=repo,
        env=env,
        check=False,
    )

    assert result.returncode == 1
    assert "Tracked hooks directory not found" in result.stderr


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


def test_post_merge_reapplies_primary_guard_even_when_lfs_fails(tmp_path):
    repo, _, env = _fixture_repository(tmp_path)
    _run(["bash", "scripts/install_git_hooks.sh"], cwd=repo, env=env)

    result = _run(
        [str(repo / ".githooks/post-merge"), "0"],
        cwd=repo,
        env={**env, "FAIL_LFS_POST_MERGE": "1"},
        check=False,
    )

    assert result.returncode == 43
    calls = Path(env["HOOK_LOG"]).read_text(encoding="utf-8").splitlines()
    assert calls[-2:] == ["lfs-post-merge", "primary-write-guard"]


def test_full_pre_push_chain_replays_updates_to_the_pytest_guard(tmp_path):
    repo, _, env = _fixture_repository(tmp_path)
    _run(["bash", "scripts/install_git_hooks.sh"], cwd=repo, env=env)
    _git(repo, "checkout", "-b", "feature", env=env)
    trigger = repo / "tests" / "trigger.py"
    trigger.parent.mkdir(exist_ok=True)
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

    stamped = _run(
        [str(_project_python()), str(repo / ".githooks/pytest_stamp.py")],
        cwd=repo,
        env=env,
        input_text=json.dumps(
            {
                "cwd": str(repo),
                "hook_event_name": "PostToolUse",
                "tool_input": {"command": ".venv/bin/python -m pytest tests/ -q"},
                "tool_response": {"stdout": "2 passed in 0.01s"},
            }
        ),
    )
    assert stamped.returncode == 0
    assert len(list(Path(env["TMPDIR"]).glob("learn-uk-pytest.v2.*.stamp"))) == 1
    pushed = _git(repo, "push", "origin", "feature:main", env=env)
    assert pushed.returncode == 0
    calls = Path(env["HOOK_LOG"]).read_text(encoding="utf-8").splitlines()
    assert "lfs-pre-push" in calls




@pytest.mark.parametrize("hook_name", REQUIRED_HOOKS)
def test_hook_scripts_have_valid_bash_syntax(hook_name):
    result = _run(["bash", "-n", str(HOOK_DIR / hook_name)], cwd=REPO_ROOT)
    assert result.returncode == 0
