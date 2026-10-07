"""#9782: a post-rebase admission receipt and refusal describe what the rebase did.

The planned family superset can include a commit git then drops as patch-equivalent.
Enforcement already uses the families the recorder enumerates afterwards; the receipt
must record those. A refusal after that rebase must say the worktree was rebased and
name ORIG_HEAD and the branch reflog entry, never a host path.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.orchestration import job_host_exec
from scripts.review import record_cf_verdict as recorder
from tests.test_authoring_review_feasibility import (
    OPUS,
    REAL_RESOLVER,
    REAL_VALIDATOR,
    SOL,
    FakeGitHub,
    MiniRepo,
    _admitted_host,
    admitted_dispatch_cleanup,
    last_receipt,
    mini_repo,
    pr_row,
    reused_worktree_behind_main,
)

REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
_SAME_PATCH = "same upstream change\n"
_BRANCH = "claude/writer-1"
_REFLOG = f"{_BRANCH}@{{1}}"


class _Stopped(Exception):
    """The dispatch was admitted and reached worktree provisioning."""


@pytest.fixture(autouse=True)
def recorder_matcher(synthetic_opsec):
    from tests.opsec_fixtures import synthetic_rules

    rules = synthetic_rules(rule="3-absolute-path", level=3, pattern=r"(?<![<\w:])/[A-Za-z][^\s`'\"<>),;\]}|*]*")
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))


@pytest.fixture
def tasks(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "tasks"
    root.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(root))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    return root


@pytest.fixture
def repo(tmp_path, monkeypatch) -> MiniRepo:
    return mini_repo(tmp_path, monkeypatch)


@pytest.fixture
def github(monkeypatch) -> FakeGitHub:
    fake = FakeGitHub()
    real_run = subprocess.run

    def run(command, *args, **kwargs):
        if isinstance(command, list) and command and command[0] == "gh":
            return fake.run(command)
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", run)
    return fake


@pytest.fixture
def boundary(repo, tasks, monkeypatch, github):
    """``cmd_dispatch`` on the miniature repository. Rebase stays tripped until a test restores it."""
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo.root)
    monkeypatch.setattr(delegate, "_local_repo_root", repo.root)
    monkeypatch.chdir(repo.root)
    monkeypatch.setattr(delegate, "_credit_period_refusal", lambda *_args: None)
    monkeypatch.setattr(delegate, "_check_capacity_hint", lambda *_args, **_kwargs: None)
    for name in ("_resolve_dirty_primary_checkout_error", "_resolve_primary_integrity_error"):
        monkeypatch.setattr(delegate, name, lambda **_kwargs: None)
    for name in (
        "_warn_node_modules_integrity",
        "_warn_venv_integrity",
        "_warn_worktree_cleanup_integrity",
        "_warn_if_monitor_api_unreachable",
    ):
        monkeypatch.setattr(delegate, name, lambda: None)
    calls: list[str] = []

    def tripwire(name):
        def fire(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(f"{name} ran for a refused dispatch")

        return fire

    for target, name, label in (
        (delegate.dispatch_isolation, "spawn_detached_worker", "provider launch"),
        (delegate, "_adapter_model_rejection", "model probe"),
        (job_host_exec, "forward_dispatch", "forwarding"),
        (job_host_exec, "decide_dispatch_placement", "placement"),
        (delegate, "_archive_task_artifacts", "archival"),
        (delegate, "_sweep_runtime_tmp_orphans", "runtime cleanup"),
        (delegate, "_resolve_worktree_base_sha", "rebase"),
        (delegate, "_validate_existing_worktree", "rebase"),
        (delegate, "_ensure_worktree", "worktree creation"),
    ):
        monkeypatch.setattr(target, name, tripwire(label))

    def dispatch(*extra: str, writer: str = OPUS, mode: str = "workspace-write", task_id: str = "writer-1"):
        agent, _, model = writer.partition("/")
        argv = [
            "dispatch",
            "--agent",
            agent,
            "--model",
            model,
            "--task-id",
            task_id,
            "--initiator",
            "claude",
            "--mode",
            mode,
            "--prompt",
            "Implement the change.",
            *extra,
        ]
        return delegate.cmd_dispatch(delegate.build_parser().parse_args(argv))

    dispatch.calls = calls
    return dispatch


def _patch_equivalent_worktree(repo: MiniRepo, github: FakeGitHub) -> tuple[Path, str, str]:
    """A reused worktree whose only commit matches a commit already on main, author for author differently.

    Git drops that commit on rebase. The plan still counted both families.
    """
    release = repo.publish("trunk", to="release")
    repo.git("checkout", "-q", "trunk")
    main = repo.commit(OPUS, path="src/app.py", text=_SAME_PATCH, message="main moves on")
    repo.publish("trunk", to="main")
    checkout = delegate._auto_worktree_path("claude", "writer-1", repo_root=repo.root)
    repo.git("worktree", "add", "-q", "-b", _BRANCH, str(checkout), release)
    MiniRepo(checkout).commit(SOL, path="src/app.py", text=_SAME_PATCH, message="same change")
    github.prs = [pr_row(42, "release", release, head=_BRANCH)]
    return checkout, release, main


def _refusal_text(err: str) -> str:
    """The typed refusal line and its JSON receipt, without the rebase warning."""
    return "\n".join(line for line in err.splitlines() if line.startswith("❌") or line.startswith("{"))


def test_patch_equivalent_rebase_receipt_records_the_families_git_kept(
    boundary, github, capsys, repo, tasks, monkeypatch
):
    """The plan counted Anthropic and OpenAI; rebase dropped the OpenAI commit as patch-equivalent.

    The dispatch stays admitted. The receipt's rebased families are the recorder's, and the planned
    superset remains on its own field.
    """
    checkout, release, main = _patch_equivalent_worktree(repo, github)
    captured: dict = {}
    real_moved = delegate._authoring_target_moved

    def capture_moved(admission, **kwargs):
        result = real_moved(admission, **kwargs)
        captured["result"] = result
        captured["record"] = dict(admission.record)
        return result

    monkeypatch.setattr(delegate, "_authoring_target_moved", capture_moved)
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", REAL_RESOLVER)
    monkeypatch.setattr(delegate, "_validate_existing_worktree", REAL_VALIDATOR)

    def stop_before_provision(**_kwargs):
        raise _Stopped

    monkeypatch.setattr(delegate, "_ensure_worktree", stop_before_provision)
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch), pytest.raises(_Stopped):
        boundary("--worktree", "--owned-path", "docs/a.md")
    err = capsys.readouterr().err
    assert captured["result"] is None, err
    rebased = MiniRepo(checkout).sha("HEAD")
    assert rebased == main, err  # the OpenAI commit was dropped
    actual = recorder.collect_branch_review_facts(
        repository=REPOSITORY,
        repo_root=repo.root,
        base_tip_sha=release,
        head_sha=rebased,
        task_root=tasks,
        incoming_agent="claude",
        incoming_model="claude-opus-5-5",
        owned_paths=("docs/a.md",),
    )
    receipt = captured["record"]
    assert sorted(actual.existing_families) == ["anthropic"]
    assert receipt["rebase_existing_families"] == ["anthropic", "openai"]
    assert receipt["rebased_existing_families"] == sorted(actual.existing_families)
    assert receipt["rebased_head_sha"] == rebased
    assert boundary.calls == []
    # Stopped at provisioning: the receipt is on the admission, and no task record was published.
    assert not (tasks / "writer-1.json").exists()


def test_post_rebase_refusal_names_the_rebase_and_how_to_recover(boundary, github, capsys, repo, tasks, monkeypatch):
    """Another writer commits before the admitted rebase runs. The rebased head is refused.

    The worktree has moved. The refusal names that, the pre-rebase head, and the two recovery refs.
    """
    checkout, _release, main = reused_worktree_behind_main(repo, github, main_trailer=OPUS)
    admitted = MiniRepo(checkout).sha("HEAD")
    monkeypatch.setattr(delegate, "_validate_existing_worktree", REAL_VALIDATOR)

    def resolve_after_another_writer(**kwargs):
        MiniRepo(checkout).commit(SOL, message="another writer")
        return REAL_RESOLVER(**kwargs)

    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", resolve_after_another_writer)
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch):
        rc = boundary("--worktree", "--owned-path", "docs/a.md")
    err = capsys.readouterr().err
    assert rc == 2, err
    pre = MiniRepo(checkout).sha("ORIG_HEAD")
    assert MiniRepo(checkout).sha(_REFLOG) == pre
    assert pre != admitted
    text = _refusal_text(err)
    assert "Worktree was rebased" in text
    assert "pre-rebase head" in text
    assert pre in text
    assert "ORIG_HEAD" in text
    assert _REFLOG in text
    assert "Branch preserved" not in text
    assert str(checkout) not in text
    assert "provider_calls=0" in text
    receipt = last_receipt(err)
    assert receipt["refusal"] == delegate.AUTHORING_REVIEW_TARGET_MOVED
    assert receipt["binding"] == "rebase"
    assert receipt["rebase_onto"] == main
    assert receipt["admitted_sha"] == admitted
    assert receipt["pre_rebase_head"] == pre
    assert receipt["recovery_refs"] == ["ORIG_HEAD", _REFLOG]
    assert list(tasks.rglob("*")) == []
    assert boundary.calls == []
