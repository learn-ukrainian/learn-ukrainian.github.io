"""Shared dispatcher fixtures."""

import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml

from scripts.dispatcher import git, worker
from tests.dispatcher.worker_reap import Reaper, reap_root

DOCTOR_NOT_FETCHED = "Managed settings (remote): not fetched — requires an Enterprise or Team subscription"


@pytest.fixture(scope="session", autouse=True)
def dispatcher_worker_reaper() -> Iterator[Reaper]:
    """Fail the session if a dispatcher test left a detached worker alive.

    Defect class: a test leaks a detached worker process. The failure names that
    test and the pid. Per-test teardown kills the worker's group; this check is
    what remains at session end.
    """
    reaper = Reaper.start()
    try:
        yield reaper
    finally:
        reaper.finish()


@pytest.fixture(autouse=True)
def end_detached_dispatcher_workers(request: pytest.FixtureRequest, tmp_path: Path, dispatcher_worker_reaper: Reaper):
    """End workers this test detached, including when pytest-timeout uses ``os._exit``.

    The reaper is armed before the test body. Fixture teardown kills the groups.
    ``os._exit`` skips that teardown; the reaper's parent-death pipe does not.
    """
    dispatcher_worker_reaper.activate(tmp_path, request.node.nodeid)
    try:
        yield
    finally:
        dispatcher_worker_reaper.reap(tmp_path)


@pytest.fixture(autouse=True)
def agy_dispatch_guards(monkeypatch):
    """Record AGY guard provisioning only for in-process builds outside ``.worktrees/dispatch``.

    Those builds use disposable checkouts, where provisioning refuses. A build in a dispatch
    worktree, and every subprocess ``sandbox`` dispatch, runs the real provisioning.
    """
    from scripts.agent_runtime import agy_hook_config

    real, calls = agy_hook_config.require_dispatch_guards, []

    def provision(worktree, home):
        if "/.worktrees/dispatch/" in Path(worktree).absolute().as_posix() + "/":
            return real(worktree, home)
        calls.append(worktree)
        return None

    monkeypatch.setattr(agy_hook_config, "require_dispatch_guards", provision)
    return calls


@pytest.fixture(autouse=True)
def claude_doctor(tmp_path_factory, monkeypatch):
    """A read-only Claude dispatch asks ``claude doctor`` for server-managed settings; answer as a consumer login.

    CI has no Claude Code, and a developer host's own login must not decide a test. Tests that start a
    provider ``claude`` put their own stub first on ``PATH``.
    """
    return install_claude_doctor_stub(tmp_path_factory.mktemp("claude-doctor"), monkeypatch)


def install_claude_doctor_stub(bin_dir, monkeypatch):
    """Put a ``claude`` that answers only ``claude doctor``, as a consumer login, first on ``PATH``."""
    stub = bin_dir / "claude"
    stub.write_text(
        f"#!{sys.executable}\nimport sys\n"
        f"if sys.argv[1:] != ['doctor']:\n    sys.exit('claude doctor stub: ' + ' '.join(sys.argv[1:]))\n"
        f"print({DOCTOR_NOT_FETCHED!r})\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', os.defpath)}")
    return stub


SOURCE = Path(__file__).resolve().parents[2]
# The in-tree dispatcher's entry: a linked worktree re-executes its primary's copy before any dispatcher module loads.
IN_TREE_ENTRY = """import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.dispatcher.primary import exec_primary


def main() -> int:
    from scripts.dispatcher.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    exec_primary(sys.argv[1:])
    raise SystemExit(main())
"""
# Model strings the sandbox stub provider (stub_provider.py) or a sandbox test dispatches with.
STUB_MODELS = (
    "blocked", "cancel", "capacity", "capacity-dirty", "crash", "dirty", "echo", "empty", "error", "escape", "fail",
    "file", "governed", "pushed", "pushed-dirty", "pushed-nested", "requested-model-is-not-proof", "tree", "unpushed",
)


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=True, timeout=30
    ).stdout.strip()


@pytest.fixture
def sandbox(tmp_path, hermetic_monitor):
    repo, tasks = tmp_path / "public", tmp_path / "tasks"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "stub@example.invalid")
    run_git(repo, "config", "user.name", "Stub")
    for relative in ("scripts/dispatcher", "scripts/common", "scripts/review", "scripts/storage"):
        shutil.copytree(SOURCE / relative, repo / relative, ignore=shutil.ignore_patterns("__pycache__"))
    for relative in ("scripts/lib/project_interpreter.sh", "scripts/agent_runtime/bounded_advisory.py",
                     "scripts/orchestration/worktree_paths.py", "scripts/orchestration/task_record_store.py"):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SOURCE / relative, target)
    # Disposable repositories share the test interpreter; they own no project environment.
    resolver = repo / "scripts/common/repo_root.py"
    with resolver.open("a") as stream:
        stream.write(f"\n\ndef project_interpreter(root=None):\n    return Path({sys.executable!r})\n")
    audit = repo / "scripts/audit"
    audit.mkdir(parents=True)
    shutil.copy(SOURCE / "scripts/audit/lint_opsec_leaks.py", audit / "lint_opsec_leaks.py")
    # The product's scripts/dispatch.py runs the installed release (#13017). The sandbox exercises
    # the retained in-tree copy until cutover slice 3 deletes it, so it carries that copy's entry.
    (repo / "scripts/dispatch.py").write_text(IN_TREE_ENTRY)
    (repo / "scripts/__init__.py").write_text(f"__path__.append({str(SOURCE / 'scripts')!r})\n")
    (repo / "scripts/fleet").mkdir()
    (repo / "scripts/fleet/__init__.py").touch()
    # D5: expose only the credit reader and the artifact preservation settlement removal runs,
    # keeping the common reaper stub isolated.
    for name in ("credit_lane.py", "claude_account_lane.py", "ignored_task_output.py", "regenerable_output.py",
                 "terminal_abandon.py"):
        shutil.copy(SOURCE / "scripts/fleet" / name, repo / "scripts/fleet" / name)
    config = repo / "scripts/config"
    config.mkdir()
    (config / "fleet_repos.yaml").write_text(
        yaml.safe_dump(
            {
                "repos": {
                    "public": {
                        "default": True,
                        "local_name": "public",
                        "github": str(remote),
                        "transport": "file",
                        "role": "public-monorepo",
                    },
                    "private": {"local_name": "private", "github": "example/private", "role": "private-product"},
                }
            }
        )
    )
    # Dispatch admission refuses a model the catalog does not name (C-4967). The stub provider reads its
    # behaviour from the model string, so this disposable copy alone names each stub behaviour as an
    # exact alias of the model the sandbox's --agent sol runs.
    catalog = yaml.safe_load((SOURCE / "scripts/config/model_catalog.yaml").read_text())
    catalog["models"]["gpt-6.1-sol"].setdefault("aliases", []).extend(STUB_MODELS)
    (config / "model_catalog.yaml").write_text(yaml.safe_dump(catalog, sort_keys=False))
    shutil.copy(SOURCE / "scripts/config/credit_lanes.yaml", config / "credit_lanes.yaml")
    # This checkout is the product checkout of the copied machinery (product_root, C-4746): it
    # carries the product marker, and the product files the dispatcher reads come from it, with
    # the review hooks module the hooks file names.
    marker = repo / "curriculum/l2-uk-en/curriculum.yaml"
    marker.parent.mkdir(parents=True)
    marker.write_text("levels: {}\n")
    (repo / "scripts/curriculum").mkdir()
    for name in ("review_hooks.v1.json", "review_attempt_hooks.py", "admission_policy.v1.json"):
        shutil.copy(SOURCE / "scripts/curriculum" / name, repo / "scripts/curriculum")
    # A workspace-write AGY dispatch provisions both workspace guards from the product checkout.
    for relative in ("agents_extensions/agy/hooks.json", "agents_extensions/shared/hooks/guard-primary-checkout-write.py"):
        (repo / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SOURCE / relative, repo / relative)
    schema_dir = repo / "schemas"
    schema_dir.mkdir()
    shutil.copy(SOURCE / "schemas/code-review-findings.v1.schema.json", schema_dir)
    shutil.copy(Path(__file__).with_name("stub_provider.py"), repo / "scripts/dispatcher/providers/codex.py")
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "fixture")
    # Origin advertises main as its default branch: review authorship is read from it (C-2902).
    run_git(repo, "init", "--bare", "--initial-branch=main", str(remote))
    run_git(repo, "remote", "add", "origin", str(remote))
    run_git(repo, "push", "-u", "origin", "main")
    # The dispatcher runs as a subprocess here, out of reach of the in-process probe stub
    # (conftest ``dispatch_slice_probe``); without the forced fallback it asks the host user
    # manager and starts every stub worker in a real ``lu-worker-*`` scope.
    env = {**os.environ, "LU_TASKS_DIR": str(tasks), "LU_DISPATCH_ISOLATION": "fallback"}
    env.pop("PYTHONPATH", None)
    # The sandbox is another checkout: the product and primary roots this test process named for
    # its own checkout (scripts/__init__.py) are not the sandbox's configuration.
    for name in ("LU_PRODUCT_ROOT", "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT"):
        env.pop(name, None)

    def cli(*args, expected=0, stdin=None):
        result = subprocess.run(
            [sys.executable, "scripts/dispatch.py", *args],
            cwd=repo,
            env=env,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == expected, (result.stdout, result.stderr)
        return result

    def dispatch(model="echo", *args):
        result = cli("dispatch", "--agent", "sol", "--model", model, "--prompt", "literal final response", *args)
        task_id, nonce = result.stdout.splitlines()
        return task_id, nonce

    def settle(task, expected=0):
        deadline = time.monotonic() + 15
        record = json.loads(
            cli(
                "wait", task[0], "--run-nonce", task[1], "--timeout", "15", "--poll-interval", "0.02", expected=expected
            ).stdout
        )
        # A terminal record precedes supervisor exit; recovery must see its claim released (#12121).
        while worker._identity(record["pid"]) == record["process_start"]:
            assert time.monotonic() < deadline, "supervisor still alive after settlement"
            time.sleep(0.02)
        return record

    def sweep():
        result = subprocess.run(
            [sys.executable, "-c", "from scripts.dispatcher.worker import settle_left_worktrees; settle_left_worktrees()"],
            cwd=repo, env=env, text=True, capture_output=True, timeout=30,
        )
        assert result.returncode == 0, (result.stdout, result.stderr)

    def review_models(*models):
        """File the stub reviewer ``models`` under OpenAI in the sandbox catalog copy only."""
        catalog = yaml.safe_load((config / "model_catalog.yaml").read_text())
        catalog["models"]["gpt-6.1-sol"].setdefault("runtime_model_ids", []).extend(models)
        (config / "model_catalog.yaml").write_text(yaml.safe_dump(catalog, sort_keys=False))

    def review_target(*models):
        """Arguments for a read-only review of one Anthropic-authored commit by the stub ``models``.

        A review needs a reviewed range and a reviewer family outside its authors (C-2902).
        """
        review_models(*models)
        head = run_git(repo, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m",
                       "authored change\n\nX-Agent: claude/claude-opus-5-5")
        return "--base", "main", "--pinned-head", head

    box = SimpleNamespace(repo=repo, tasks=tasks, remote=remote, env=env, cli=cli, dispatch=dispatch, settle=settle,
                          sweep=sweep, review_models=review_models, review_target=review_target)
    try:
        yield box
    finally:
        # cancel() only signals a supervisor that is still the recorded process. The provider
        # is its own session, and pytest-timeout's os._exit never reaches this fixture.
        reap_root(tmp_path)


def await_file(path, *, ready=lambda content: True):
    deadline = time.monotonic() + 10
    while not path.exists() or not (content := path.read_text()) or not ready(content):
        assert time.monotonic() < deadline, f"stub did not populate {path.name}"
        time.sleep(0.02)
    return content


def prior_worktree(sandbox, name="prior-round", start="origin/main"):
    """An earlier round's worktree; a task's own clean worktree is removed when it settles."""
    tree = sandbox.repo / ".worktrees/dispatch/codex" / name
    git.create_worktree(sandbox.repo, tree, f"codex/{name}", run_git(sandbox.repo, "rev-parse", start))
    return tree


def local_branches(repo):
    return run_git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").split()


def in_process_repo(sandbox, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(git, "ROOT", sandbox.repo)
    monkeypatch.setattr(git, "CONFIG", sandbox.repo / "scripts/config/fleet_repos.yaml")


@pytest.fixture
def delivery_settle(sandbox):
    run_git(sandbox.repo, "push", "origin", "main:release")
    # The probes reuse one worktree; a borrowed (--cwd) worktree survives each settlement.
    tree = prior_worktree(sandbox, "delivery-probe", "origin/release")
    record = sandbox.settle(sandbox.dispatch("echo", "--cwd", str(tree), "--base", "origin/release"))
    # Synthetic write records need the trusted remote omitted from read-only dispatches.
    record["worktree_remote_url"] = str(sandbox.remote)
    # Existing settle probes also cover records created before the start-SHA field.
    record.pop("worktree_start_sha", None)
    def settle(model="echo", owned=("delivered.txt",)):
        record.update(mode="workspace-write", model=model, status="running", owned_paths=list(owned or []))
        if owned is None:
            record.pop("owned_paths")
        path = sandbox.tasks / f"{record['task_id']}.json"
        path.write_text(json.dumps(record))
        subprocess.run([
            sys.executable, "-c", "import sys; from pathlib import Path; "
            "from scripts.dispatcher.worker import supervise; "
            "supervise(Path(sys.argv[1]), {}, 0.2 if sys.argv[2] == 'blocked' else 10)", str(path), model,
        ], cwd=sandbox.repo, env=sandbox.env, check=True, timeout=30)
        return json.loads(path.read_text())
    return record, settle


@pytest.fixture
def merged_delivery_world(tmp_path, monkeypatch):
    """A write task whose branch cannot show its delivery, with a scripted GitHub and ownership ledger."""
    from scripts.common import github_client
    from scripts.orchestration import pr_ownership

    world = SimpleNamespace(
        prs={}, files={}, listed=[], published=(None, True), lookup_error=None,
        record={
            "task_id": "merge-probe", "mode": "workspace-write", "status": "done", "error": None,
            "owned_paths": ["docs/owned.md"], "worktree_remote_url": "https://github.com/org/repo.git",
            "worktree_base_ref": "origin/main", "worktree_branch": "claude/merge-probe", "publish_branch": None,
            "started_at": "2026-10-29T08:00:00+00:00", "head_sha": "a" * 40, "commits_ahead": 0,
            "push_state": "unpushed", "worktree_dirty_on_exit": False,
        },
    )

    def gh(args, **_):
        if world.lookup_error:
            raise world.lookup_error
        words = args[1:]
        out = (json.dumps(world.listed) if words[:2] == ["pr", "list"]
               else json.dumps(world.prs[int(words[2])]) if words[:2] == ["pr", "view"]
               else "\n".join(json.dumps(name) for name in world.files[int(words[2].split("/")[4])]))
        return SimpleNamespace(returncode=0, stdout=out, stderr="")

    state = tmp_path / "state.json"
    monkeypatch.setattr(pr_ownership, "state_path", lambda: state)
    monkeypatch.setattr(github_client, "run", gh)
    monkeypatch.setattr(git, "_canonical_publication", lambda *_: world.published)
    monkeypatch.setattr(git, "ownership_git", Mock(side_effect=subprocess.CalledProcessError(
        128, ["git", "fetch"], stderr="branch gone")))

    def accept(*numbers):
        history = [{"event": "accepted", "pr": f"org/repo#{n}", "successor": "merge-probe"} for n in numbers]
        state.write_text(json.dumps({"schema": 1, "last_tick": None, "episodes": {}, "handoffs": {},
                                     "history": history, "outbox": []}))

    world.accept = accept
    return world


MERGED = {"state": "MERGED", "baseRefName": "main", "mergedAt": "2026-10-29T09:00:00Z"}
