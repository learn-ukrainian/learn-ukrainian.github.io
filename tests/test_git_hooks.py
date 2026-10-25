"""Integration coverage for the tracked Git hook delegator chain."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

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
    (repo / "scripts").mkdir()
    shutil.copy2(REPO_ROOT / "scripts/install_git_hooks.sh", repo / "scripts/install_git_hooks.sh")
    _write_executable(
        repo / "scripts/pre_commit/project_python.sh",
        f'#!/usr/bin/env bash\nset -euo pipefail\nexec "{_project_python()}" "$@"\n',
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


def test_credential_free_validation_does_not_demand_authenticated_lfs(tmp_path, monkeypatch, synthetic_opsec):
    """Real LFS lock authentication must not run when validating an ordinary outgoing blob."""
    import contextlib
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    import delegate
    from scripts.orchestration.safe_git_context import SafeGitContext
    from tests.test_delegate import _PinnedRemotePublicHead

    monkeypatch.setenv("PATH", os.defpath)
    repo, remote, env = _fixture_repository(tmp_path)
    env["PATH"] = os.defpath
    _git(repo, "checkout", "-b", "feature", env=env)
    (repo / "docs.md").write_text("credential-free validation\n")
    _git(repo, "add", "docs.md", env=env)
    _git(repo, "commit", "-m", "ordinary blob", env=env)
    head = _git(repo, "rev-parse", "HEAD", env=env).stdout.strip()
    base = _git(repo, "rev-parse", "origin/main", env=env).stdout.strip()
    requests = []
    validations = []
    allocated = []

    class AuthenticationRequired(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(self.path)
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="fixture"')
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), AuthenticationRequired)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    prepare = SafeGitContext.prepare_validation
    real_run = subprocess.run

    def validation(context, **kwargs):
        prepare(context, **kwargs)
        # The driver-owned fixture endpoint reproduces the real authentication
        # refusal with no credentials and no external service or worker config.
        context.checked("config", "lfs.url", f"http://127.0.0.1:{server.server_port}/lfs")
        context.checked("config", "lfs.locksverify", "true")
        context.env.update({name: env[name] for name in ("HOOK_LOG", "LFS_STDIN_LOG")})

    @contextlib.contextmanager
    def execution(_source, **_kwargs):
        with SafeGitContext(objects=repo / ".git/objects", temp_root=tmp_path,
                            origin=str(remote), local_remote=True) as context:
            context.source_git_dir = repo / ".git"
            context.driver_base = base
            context.interpreter = Path(_project_python())
            yield context

    @contextlib.contextmanager
    def credentials(**_kwargs):
        yield []

    def run(args, **kwargs):
        result = real_run(args, **kwargs)
        if str(args[0]).endswith("/pre-push"):
            validations.append((kwargs["input"], result))
            allocated.append(sum(path.stat().st_blocks * 512 for path in tmp_path.rglob("*")
                                 if path.is_file() and not path.is_symlink()))
        return result

    public = _PinnedRemotePublicHead()
    public.origin = remote
    monkeypatch.setattr(delegate, "_finalize_public_repository", lambda: public)
    monkeypatch.setattr(delegate, "_finalize_execution_context", execution)
    monkeypatch.setattr(delegate, "_finalize_transport_credentials", credentials)
    monkeypatch.setattr(SafeGitContext, "prepare_validation", validation)
    monkeypatch.setattr(subprocess, "run", run)
    try:
        result = delegate._auto_finalize_dirty_worktree(
            worktree=repo, task_id="credential-free-lfs", agent="codex", branch="feature",
            base_branch="main", base_sha=base, owned_paths=["docs.md"],
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    assert len(validations) == 1
    update, hook_result = validations[0]
    assert update == f"refs/heads/feature {head} refs/heads/feature {'0' * 40}\n"
    assert result.ok, (result.error, hook_result.stdout, hook_result.stderr, requests)
    assert hook_result.returncode == 0
    assert requests == []
    assert "pre-push:docs.md" in Path(env["HOOK_LOG"]).read_text()
    assert _git(remote, "rev-parse", "refs/heads/feature", env=env).stdout.strip() == head
    assert allocated and max(allocated) < 20 * 1024 * 1024
    print(json.dumps({"fixture_live_allocated_max_sample": max(allocated), "lfs_auth_requests": len(requests)}))


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
