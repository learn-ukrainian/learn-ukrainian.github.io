"""Repository admission isolation, legacy compatibility and atomicity (#11375)."""

from __future__ import annotations

import json
import multiprocessing
import os
import sqlite3
import subprocess
import time

import pytest

from scripts.guardrails import delegate_ownership as ownership
from tests.test_delegate_ownership_relaxation import FakeTime

PID = os.getpid()
PATH_PAIRS = [
    ("tests/unit.py", "tests/unit.py"),
    ("tests", "tests/unit.py"),
    ("tests/unit.py", "tests"),
    ("tests/**", "tests/unit.py"),
    ("tests/*.py", "tests/unit.py"),
    ("**", "tests/unit.py"),
]


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, timeout=15,
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    ).stdout.strip()


@pytest.fixture
def repositories(tmp_path):
    repos = [tmp_path / "one", tmp_path / "two"]
    for repo in repos:
        repo.mkdir()
        _git(repo, "init", "-q")
    _git(repos[0], "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "fixture")
    worktree = tmp_path / "linked"
    _git(repos[0], "worktree", "add", "-q", "--detach", str(worktree))
    return *repos, worktree


def _ledger(tmp_path, repo, monkeypatch):
    # Changing cwd keeps these regressions executable against the old API too.
    with monkeypatch.context() as patch:
        patch.chdir(repo)
        return ownership.OwnershipLedger(tmp_path / "ownership.sqlite3", task_state_dir=tmp_path)


def _admit(ledger, task, paths, **kwargs):
    return ledger.admit(task_id=task, mode="workspace-write", owned_paths=paths, pid=PID, **kwargs)


def _claims(ledger):
    with ledger._connect(read_only=True) as conn:
        return [tuple(row) for row in conn.execute("SELECT * FROM write_claims ORDER BY task_id, claim_json")]


@pytest.mark.parametrize("held,incoming", PATH_PAIRS)
@pytest.mark.parametrize("state", ["running", "queued", "stale"])
def test_cross_repository_paths_never_conflict_or_wait(tmp_path, repositories, monkeypatch, held, incoming, state):
    """A foreign holder or waiter cannot delay admission or be reclaimed by it."""
    a = _ledger(tmp_path, repositories[0], monkeypatch)
    b = _ledger(tmp_path, repositories[1], monkeypatch)
    assert _admit(a, "holder", [held]).admitted
    if state == "stale":
        (tmp_path / "holder.json").write_text(json.dumps({"pid": PID, "status": "done"}))
    elif state == "queued":
        with a._connect() as conn:
            stored = conn.execute("SELECT claim_json FROM write_claims").fetchone()[0]
            conn.execute("INSERT INTO write_waiters (task_id, claims_json, pid, enqueued_at, deadline) VALUES (?,?,?,?,?)",
                         ("waiting", f"[{stored}]", PID, time.time(), time.time() + 3600))
    before = _claims(a)
    result = _admit(b, "incoming", [incoming], wait_s=30,
                    sleep=lambda _: pytest.fail("foreign holder must never queue"))
    assert result.admitted and not result.would_refuse and not result.skipped
    assert not result.conflicts and result.waited_s >= 0
    with b._connect(read_only=True) as conn:
        events = [r[0] for r in conn.execute("SELECT event FROM admission_events WHERE task_id = 'incoming'")]
        assert events == ["admitted"]
        assert conn.execute("SELECT count(*) FROM write_waiters WHERE task_id = 'incoming'").fetchone()[0] == 0
    assert [row for row in _claims(a) if row[0] == "holder"] == before


@pytest.mark.parametrize("held,incoming", PATH_PAIRS[:4])
def test_linked_worktrees_still_conflict_and_queue(tmp_path, repositories, monkeypatch, held, incoming):
    a = _ledger(tmp_path, repositories[0], monkeypatch)
    linked = _ledger(tmp_path, repositories[2], monkeypatch)
    assert _admit(a, "holder", [held]).admitted
    assert not _admit(linked, "refused", [incoming]).admitted
    fake = FakeTime(limit=15)
    fake.hooks.append(lambda: a.release("holder", pid=PID))
    result = _admit(linked, "waiting", [incoming], wait_s=15, poll_s=1,
                    sleep=fake.sleep, clock=fake.clock, monotonic=fake.clock)
    assert result.admitted and result.waited_s == 1
    with linked._connect(read_only=True) as conn:
        assert [r[0] for r in conn.execute("SELECT event FROM admission_events WHERE task_id = 'waiting'")] == [
            "queued", "admitted",
        ]


def test_foreign_waiter_does_not_block_unknown_intent_or_get_reaped(tmp_path, repositories, monkeypatch):
    a = _ledger(tmp_path, repositories[0], monkeypatch)
    b = _ledger(tmp_path, repositories[1], monkeypatch)
    assert _admit(b, "holder-b", ["tests/unit.py"]).admitted
    fake = FakeTime(limit=15)

    def while_waiting():
        # Exercise a real waiter, not only a hand-built queue row.
        b.release("holder-b", pid=PID)
        assert _admit(a, "no-paths-a", []).admitted
        with b._connect(read_only=True) as conn:
            row = conn.execute("SELECT task_id FROM write_waiters").fetchone()
            assert row[0] == "waiting-b"

    fake.hooks.append(while_waiting)
    assert _admit(b, "waiting-b", ["tests/unit.py"], wait_s=15, poll_s=1,
                  sleep=fake.sleep, clock=fake.clock, monotonic=fake.clock).admitted


def test_reclamation_release_and_pid_binding_preserve_foreign_rows(tmp_path, repositories, monkeypatch):
    a = _ledger(tmp_path, repositories[0], monkeypatch)
    b = _ledger(tmp_path, repositories[1], monkeypatch)
    # Duplicate task IDs in distinct repositories must not replace each other.
    assert _admit(a, "same-task", ["tests/unit.py"]).admitted
    assert _admit(b, "same-task", ["tests/unit.py"]).admitted
    with a._connect() as conn:
        conn.execute("UPDATE write_claims SET created_at = 0")
    (tmp_path / "same-task.json").write_text(json.dumps({"pid": PID, "status": "done"}))
    foreign = [r for r in _claims(a) if json.loads(r[1]).get("repository_identity") == b.repository_identity]
    with a._connect() as conn:
        assert a._reconcile_stale(conn) == ["same-task"]
    assert _claims(b) == foreign
    assert _admit(a, "same-task", ["tests/unit.py"]).admitted
    a.update_claim_pid("same-task", 99999999)
    a.release("same-task")
    assert _claims(b) == foreign
    # PID-qualified release must also remain scoped, including same-PID peers.
    (tmp_path / "same-task.json").unlink()
    assert _admit(a, "same-task", ["tests/unit.py"]).admitted
    a.release("same-task", pid=PID)
    assert _claims(b) == foreign


@pytest.mark.parametrize("legacy_kind", ["file", "subtree", "ownership_unknown"])
def test_legacy_claims_default_to_each_current_repository(tmp_path, repositories, monkeypatch, legacy_kind):
    a = _ledger(tmp_path, repositories[0], monkeypatch)
    with a._connect() as conn:
        conn.execute("INSERT INTO write_claims VALUES (?,?,?,?)", (
            "legacy", json.dumps({"raw": "tests", "kind": legacy_kind, "norm": "tests"}), PID, time.time(),
        ))
    before = _claims(a)
    for repo in repositories:
        current = _ledger(tmp_path, repo, monkeypatch)
        result = _admit(current, "incoming", ["tests/unit.py"])
        assert not result.admitted and result.would_refuse
    assert _claims(a) == before


def test_legacy_waiters_remain_visible_to_unknown_intent(tmp_path, repositories, monkeypatch):
    ledger = _ledger(tmp_path, repositories[0], monkeypatch)
    with ledger._connect() as conn:
        conn.execute("INSERT INTO write_waiters (task_id, claims_json, pid, enqueued_at, deadline) VALUES (?,?,?,?,?)", (
            "legacy-waiter", json.dumps([ownership.normalize_claim("tests").as_dict()]), PID, time.time(), time.time() + 30,
        ))
    assert not _admit(ledger, "no-paths", []).admitted


@pytest.mark.parametrize("missing", [False, True])
def test_unresolvable_identity_keeps_global_admission_and_typed_note(tmp_path, repositories, monkeypatch, capsys, missing):
    a = _ledger(tmp_path, repositories[0], monkeypatch)
    assert _admit(a, "holder", ["tests/unit.py"]).admitted
    outside = tmp_path / "outside"
    outside.mkdir()
    if missing:
        unknown = ownership.OwnershipLedger(a.path, task_state_dir=tmp_path, cwd=outside / "missing")
    else:
        unknown = _ledger(tmp_path, outside, monkeypatch)
    result = _admit(unknown, "incoming", ["tests/unit.py"])
    assert not result.admitted and not result.skipped
    assert result.as_dict()["notes"] == ["repository_identity_unresolved"]
    with unknown._connect(read_only=True) as conn:
        event = json.loads(conn.execute("SELECT payload FROM admission_events WHERE task_id = 'incoming'").fetchone()[0])
    assert event["notes"] == ["repository_identity_unresolved"]
    assert str(outside) not in capsys.readouterr().err
    # An unknown repository may admit disjoint paths, but must remain globally visible.
    admitted = _admit(unknown, "global", ["other.py"])
    assert admitted.admitted and not admitted.skipped
    b = _ledger(tmp_path, repositories[1], monkeypatch)
    assert not _admit(b, "other-repo", ["other.py"]).admitted


def test_identity_ignores_git_environment_and_resolves_symlinks(tmp_path, repositories, monkeypatch):
    a = _ledger(tmp_path, repositories[0], monkeypatch)
    alias = tmp_path / "alias"
    alias.symlink_to(repositories[2], target_is_directory=True)
    monkeypatch.setenv("GIT_DIR", str(repositories[1] / ".git"))
    monkeypatch.setenv("GIT_COMMON_DIR", str(repositories[1] / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(repositories[1]))
    linked = _ledger(tmp_path, alias, monkeypatch)
    assert a.repository_identity == linked.repository_identity == str((repositories[0] / ".git").resolve())


def test_common_directory_identity_preserves_trailing_spaces(tmp_path, monkeypatch):
    """Stripping Git output must not change the identity of a separate Git directory."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    common = tmp_path / "git store "
    _git(checkout, "init", "-q", f"--separate-git-dir={common}")
    ledger = _ledger(tmp_path, checkout, monkeypatch)
    assert ledger.repository_identity == str(common.resolve())


@pytest.mark.parametrize("held", ["tests/**", "**"])
def test_old_reader_new_row_keeps_same_repository_protection(tmp_path, repositories, monkeypatch, held):
    ledger = _ledger(tmp_path, repositories[0], monkeypatch)
    assert _admit(ledger, "new-holder", [held]).admitted
    # Historical reader selects these four columns and ignores extra JSON keys.
    with sqlite3.connect(ledger.path) as conn:
        row = conn.execute("SELECT task_id, claim_json, pid, created_at FROM write_claims").fetchone()
    payload = json.loads(row[1])
    assert payload["repository_identity"] == ledger.repository_identity
    old_claim = ownership.PathClaim(raw=str(payload.get("raw", "")),
                                    kind=ownership.ClaimKind(str(payload.get("kind"))), norm=str(payload.get("norm", "")))
    assert ownership.claims_conflict(ownership.normalize_claim("tests/unit.py"), old_claim) or (
        old_claim.kind == ownership.ClaimKind.UNKNOWN
    )
    assert not _admit(ledger, "new-reader", ["tests/unit.py"]).admitted


def test_events_and_results_never_expose_repository_realpaths(tmp_path, repositories, monkeypatch, capsys):
    ledger = _ledger(tmp_path, repositories[0], monkeypatch)
    assert _admit(ledger, "holder", ["tests/unit.py"]).admitted
    fake = FakeTime(limit=2)
    notices = []
    result = _admit(ledger, "incoming", ["tests/unit.py"], wait_s=1, poll_s=1,
                    sleep=fake.sleep, clock=fake.clock, monotonic=fake.clock, on_queued=notices.append)
    assert result.queue_timeout
    public = json.dumps(result.as_dict()) + str(notices) + capsys.readouterr().err
    with ledger._connect(read_only=True) as conn:
        events = [json.loads(r[0]) for r in conn.execute("SELECT payload FROM admission_events")]
    assert events
    for event in events:
        assert event["repository_id"] == result.as_dict()["repository_id"]
        assert len(event["repository_id"]) == 16
    public += json.dumps(events)
    assert str(tmp_path) not in public and ledger.repository_identity not in public


def test_foreign_holder_timeout_never_changes_queue_budget(tmp_path, repositories, monkeypatch):
    a = _ledger(tmp_path, repositories[0], monkeypatch)
    b = _ledger(tmp_path, repositories[1], monkeypatch)
    assert _admit(a, "short-a", ["tests/unit.py"]).admitted
    assert _admit(b, "long-b", ["tests/unit.py"]).admitted
    for task, budget in (("short-a", 3), ("long-b", 100)):
        (tmp_path / f"{task}.json").write_text(json.dumps({"status": "running", "pid": PID, "hard_timeout": budget}))
    fake = FakeTime(limit=3)
    result = _admit(a, "waiting-a", ["tests/unit.py"], wait_s=1, poll_s=1,
                    sleep=fake.sleep, clock=fake.clock, monotonic=fake.clock)
    assert result.queue_timeout and result.waited_s == 3
    assert {c["other_task_id"] for c in result.conflicts} == {"short-a"}


def test_public_helpers_use_explicit_checkout_for_admission_and_pid_binding(tmp_path, repositories, monkeypatch):
    a = _ledger(tmp_path, repositories[0], monkeypatch)
    assert _admit(a, "holder", ["tests/unit.py"]).admitted
    monkeypatch.chdir(repositories[0])
    result = ownership.admit_write_paths(
        task_id="foreign", mode="workspace-write", owned_paths=["tests/unit.py"], pid=PID,
        ledger_path=a.path, task_state_dir=tmp_path, cwd=repositories[1],
    )
    assert result.admitted and not result.conflicts
    ownership.update_write_claim_pid("foreign", 99999999, ledger_path=a.path,
                                    task_state_dir=tmp_path, cwd=repositories[1])
    with a._connect(read_only=True) as conn:
        assert [tuple(r) for r in conn.execute("SELECT task_id, pid FROM write_claims ORDER BY task_id")] == [
            ("foreign", 99999999), ("holder", PID),
        ]


def _process_admission(repo, ledger_path, state_dir, task, barrier, results, release):
    os.chdir(repo)
    ledger = ownership.OwnershipLedger(ledger_path, task_state_dir=state_dir)
    barrier.wait(timeout=15)
    result = ledger.admit(task_id=task, mode="workspace-write", owned_paths=["tests/unit.py"], pid=os.getpid())
    results.put(result.admitted)
    release.wait(timeout=15)  # Keep each claim's PID live until all results are observed.


@pytest.mark.parametrize("same_repository", [False, True])
def test_concurrent_processes_preserve_atomic_repository_admission(tmp_path, repositories, monkeypatch, same_repository):
    ledger = _ledger(tmp_path, repositories[0], monkeypatch)
    with ledger._connect():
        pass
    ctx = multiprocessing.get_context("fork")
    barrier, results, release = ctx.Barrier(4), ctx.Queue(), ctx.Event()
    repos = [repositories[0], repositories[2]] if same_repository else repositories[:2]
    processes = [ctx.Process(target=_process_admission, args=(
        repos[i % 2], ledger.path, tmp_path, f"writer-{i}", barrier, results, release,
    )) for i in range(4)]
    try:
        for proc in processes:
            proc.start()
        decisions = [results.get(timeout=20) for _ in processes]
        assert sum(decisions) == (1 if same_repository else 2)
        assert len(_claims(ledger)) == (1 if same_repository else 2)
        with ledger._connect(read_only=True) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        release.set()
        for proc in processes:
            proc.join(timeout=20)
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=5)
    assert all(proc.exitcode == 0 for proc in processes)
