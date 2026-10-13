"""Branch ownership persists before a PR exists, including concurrent rounds."""

import json
from concurrent.futures import ProcessPoolExecutor

import pytest

from scripts.orchestration.author_binding import BindingError, BindingStore, bind_dispatch
from tests.test_delegate_admission import (
    _FakeStdin,
    _live_danger_args,
    _stub_worktree,
    delegate,
)
from tests.test_delegate_admission import tasks_dir as tasks_dir


def append_round(root, number):
    return BindingStore(root).append(
        repository="learn-ukrainian/learn-ukrainian",
        branch="codex/topic",
        task_id=f"writer-{number}",
        family="openai",
        driver="claude-harness",
        lane="infra-harness",
        issue=10530,
    )


def test_first_dispatch_and_second_round(tmp_path):
    store = BindingStore(tmp_path)
    assert store.load("learn-ukrainian/learn-ukrainian", "codex/topic") is None
    first = append_round(tmp_path, 0)
    assert first["pr"] is None
    assert first["round_count"] == 0
    append_round(tmp_path, 1)
    record = store.append(
        repository=first["repository"],
        branch=first["branch"],
        task_id="writer-2",
        family="anthropic",
        driver="claude-harness",
        lane="infra-harness",
        issue=10530,
    )
    assert record["author_task_ids"] == ["writer-0", "writer-1", "writer-2"]
    assert record["author_families"] == ["openai", "anthropic"]
    assert record["round_count"] == 2
    assert append_round(tmp_path, 1) == record
    assert store.attach_pr(first["repository"], first["branch"], 42)["pr"] == 42
    assert store.attach_pr(first["repository"], first["branch"], 42)["pr"] == 42
    with pytest.raises(BindingError, match="PR already attached"):
        store.attach_pr(first["repository"], first["branch"], 43)


def test_concurrent_rounds_do_not_lose_authors(tmp_path):
    with ProcessPoolExecutor(max_workers=2) as pool:
        list(pool.map(append_round, [tmp_path] * 8, range(8)))
    record = BindingStore(tmp_path).load("learn-ukrainian/learn-ukrainian", "codex/topic")
    assert set(record["author_task_ids"]) == {f"writer-{i}" for i in range(8)}
    assert record["round_count"] == 7


@pytest.mark.parametrize("raw", ["{", "{}", '{"schema_version":99}', "[]"])
def test_corruption_is_not_overwritten(tmp_path, raw):
    store = BindingStore(tmp_path)
    path = store.path("learn-ukrainian/learn-ukrainian", "codex/topic")
    path.parent.mkdir(parents=True)
    path.write_text(raw)
    with pytest.raises(BindingError):
        append_round(tmp_path, 0)
    assert path.read_text() == raw


def test_missing_binding_cannot_attach_pr(tmp_path):
    with pytest.raises(BindingError, match="missing"):
        BindingStore(tmp_path).attach_pr("learn-ukrainian/learn-ukrainian", "codex/topic", 42)


def test_dispatch_hook_records_only_writers_and_preserves_unknown_lane(tmp_path):
    state = {
        "repository": "learn-ukrainian/learn-ukrainian",
        "worktree_branch": "codex/topic",
        "task_id": "first",
        "agent": "codex",
        "model": "gpt-6.1-sol",
        "initiator": "claude-harness",
        "mode": "danger",
        "dor_preflight": {"issues": [10530]},
    }
    bind_dispatch(state, root=tmp_path, lane="infra-harness")
    record = BindingStore(tmp_path).load(state["repository"], state["worktree_branch"])
    assert record["author_families"] == ["openai"]
    for mode, review in [("read-only", False), ("danger", True)]:
        bind_dispatch({**state, "task_id": "reader", "mode": mode, "review": review}, root=tmp_path)
    assert BindingStore(tmp_path).load(state["repository"], state["worktree_branch"]) == record


def test_binding_schema_rejects_changed_identity(tmp_path):
    record = append_round(tmp_path, 0)
    path = BindingStore(tmp_path).path(record["repository"], record["branch"])
    record["branch"] = "codex/other"
    path.write_text(json.dumps(record))
    with pytest.raises(BindingError):
        BindingStore(tmp_path).load(record["repository"], "codex/topic")


@pytest.mark.parametrize("corrupt", [False, True])
def test_real_dispatch_binds_before_spawn_or_refuses_corruption(tasks_dir, monkeypatch, corrupt):
    _stub_worktree(monkeypatch, tasks_dir)
    repo = "learn-ukrainian/learn-ukrainian"
    monkeypatch.setattr(delegate, "_resolve_dispatch_repository", lambda *_: repo)
    store = BindingStore(tasks_dir.parent / "author-lifecycle" / "v1")
    if corrupt:
        path = store.path(repo, "codex/adm")
        path.parent.mkdir(parents=True)
        path.write_text("{")
    observed = []

    class Process:
        pid = 13579
        stdin = _FakeStdin()

    def spawn(*_args, **_kwargs):
        record = store.load(repo, "codex/adm")
        observed.append(record["author_task_ids"])
        return Process()

    monkeypatch.setattr(delegate.subprocess, "Popen", spawn)
    args = _live_danger_args(tasks_dir, "first-author")
    args.research_track = "infra-harness"
    assert delegate.cmd_dispatch(args) == (1 if corrupt else 0)
    assert observed == ([] if corrupt else [["first-author"]])
    if corrupt:
        state = delegate._read_state(delegate._state_path(args.task_id))
        assert state["failure_reason"] == "dispatch_not_started"
        assert state["returncode_reason"] == "ownership binding unavailable; worker not started"


def test_unclassified_dispatch_does_not_change_admission(tmp_path):
    bind_dispatch({"repository": None, "mode": "danger", "worktree_branch": "topic"}, root=tmp_path)
    assert not tmp_path.joinpath("bindings").exists()


def test_atomic_replace_failure_preserves_binding(tmp_path, monkeypatch):
    from scripts.orchestration import author_binding

    first = append_round(tmp_path, 0)
    monkeypatch.setattr(author_binding.os, "replace", lambda *_: (_ for _ in ()).throw(OSError("failed rename")))
    with pytest.raises(OSError, match="failed rename"):
        append_round(tmp_path, 1)
    assert BindingStore(tmp_path).load(first["repository"], first["branch"]) == first
    assert list((tmp_path / "bindings").glob(".author-*")) == []


def test_binding_symlink_is_corruption_not_ownership(tmp_path):
    store = BindingStore(tmp_path)
    record = append_round(tmp_path, 0)
    path = store.path(record["repository"], record["branch"])
    target = tmp_path / "elsewhere.json"
    path.rename(target)
    path.symlink_to(target)
    with pytest.raises(BindingError, match="symlink"):
        append_round(tmp_path, 1)
    assert json.loads(target.read_text())["round_count"] == 0


def test_task_identity_is_opaque_and_does_not_change_dispatch_admission(tmp_path):
    store = BindingStore(tmp_path)
    record = store.append(
        repository="owner/repo",
        branch="codex/topic",
        task_id="codex/round:1",
        family="openai",
        driver="driver",
        lane="unknown",
    )
    assert record["author_task_ids"] == ["codex/round:1"]


def test_dispatch_hook_does_not_guess_foreign_issue_card(tmp_path):
    state = {
        "repository": "owner/public-code",
        "worktree_branch": "codex/topic",
        "task_id": "writer",
        "agent": "codex",
        "model": "gpt-6.1-sol",
        "initiator": "driver",
        "mode": "danger",
        "dor_preflight": {"issues": [971], "issue_repositories": [{"issue": 971, "repo": "owner/private-cards"}]},
    }
    bind_dispatch(state, root=tmp_path, lane="infra-harness")
    assert BindingStore(tmp_path).load("owner/public-code", "codex/topic")["issue"] is None
