"""PR owner check: ownership comes from task records, never author or branch prefix."""

import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts.fleet import pr_owner_check as check
from scripts.orchestration.fleet_repos import FleetRepo

PUBLIC = "learn-ukrainian/learn-ukrainian.github.io"
PRIVATE = "learn-ukrainian/learn-ukrainian-infra-private"
REPOS = {
    "public": FleetRepo("public", PUBLIC, "learn-ukrainian", "public-monorepo", True),
    "infra-private": FleetRepo("infra-private", PRIVATE, "learn-ukrainian-infra-private", "private-infra"),
}


def pr(number, branch, **extra):
    return {"number": number, "headRefName": branch, "isCrossRepository": False, **extra}


def task(task_id, branch, status, repository=PUBLIC, started="2026-10-28T09:00:00+00:00", **extra):
    return {
        "task_id": task_id, "worktree_branch": branch, "status": status,
        "repository": repository, "started_at": started, **extra,
    }


def run(prs, records, alive=lambda record: True):
    return check.evaluate(prs, records, REPOS, alive)


def test_live_owner_in_each_repo_means_owned():
    prs = {PUBLIC: [pr(1, "claude/a")], PRIVATE: [pr(2, "codex/b")]}
    records = [task("a", "claude/a", "running"), task("b", "codex/b", "spawning", PRIVATE)]
    assert run(prs, records) == []


def test_branch_prefix_and_author_do_not_own():
    prs = {PUBLIC: [pr(1, "claude/a", author={"login": "claude"})]}
    (finding,) = run(prs, [])
    assert (finding.number, finding.last_task) == (1, None)
    assert "no task record" in finding.reason


def test_owner_in_other_repository_does_not_own():
    prs = {PRIVATE: [pr(7, "claude/a")]}
    (finding,) = run(prs, [task("a", "claude/a", "running", PUBLIC)])
    assert finding.repo == PRIVATE


@pytest.mark.parametrize("status", ["failed", "timeout", "cancelled", "no_deliverable", "crashed"])
def test_failed_last_owner_is_reported_with_status(status):
    (finding,) = run({PUBLIC: [pr(3, "x")]}, [task("t", "x", status)])
    assert status in finding.reason and finding.last_task == "t"


def test_done_owner_with_open_pr_is_unowned():
    (finding,) = run({PUBLIC: [pr(4, "x")]}, [task("t", "x", "done")])
    assert "still open" in finding.reason


def test_dead_supervisor_is_not_live():
    (finding,) = run({PUBLIC: [pr(5, "x")]}, [task("t", "x", "running")], alive=lambda record: False)
    assert "not verifiably alive" in finding.reason


def test_replacement_owner_after_failure_counts_and_latest_task_is_named():
    records = [
        task("old", "x", "failed", started="2026-10-28T08:00:00+00:00"),
        task("new", "x", "running", started="2026-10-28T09:00:00+00:00"),
    ]
    assert run({PUBLIC: [pr(6, "x")]}, records) == []
    (finding,) = run({PUBLIC: [pr(6, "x")]}, [records[0], task("newer", "x", "done", started="2026-10-28T10:00:00+00:00")])
    assert finding.last_task == "newer"


def test_fork_pr_is_never_owned_by_a_same_named_branch():
    prs = {PUBLIC: [pr(8, "claude/a", isCrossRepository=True)]}
    (finding,) = run(prs, [task("a", "claude/a", "running")])
    assert "fork" in finding.reason


def test_legacy_record_without_repository_belongs_to_default_repo():
    legacy = {"task_id": "old", "worktree_branch": "x", "status": "running", "started_at": "2026-10-01"}
    assert run({PUBLIC: [pr(1, "x")]}, [legacy]) == []
    assert len(run({PRIVATE: [pr(1, "x")]}, [legacy])) == 1


@pytest.mark.parametrize(
    "extra",
    [
        {},  # spawning/running with no supervisor evidence
        {"pid": 4242},  # pid without the recorded start identity
        {"pid": 4242, "process_start": None},
        {"pid": 4242, "process_start": "boot:1"},  # the pid is gone: identity lookup returns None
    ],
)
def test_real_liveness_needs_positive_supervisor_identity(monkeypatch, extra):
    from scripts.dispatcher import worker

    monkeypatch.setattr(worker, "_identity", lambda pid: None)
    for status in ("running", "spawning"):
        (finding,) = check.evaluate({PUBLIC: [pr(1, "x")]}, [task("t", "x", status, **extra)], REPOS)
        assert "not verifiably alive" in finding.reason


def test_real_liveness_accepts_matching_identity(monkeypatch):
    from scripts.dispatcher import worker

    monkeypatch.setattr(worker, "_identity", lambda pid: "boot:1" if pid == 4242 else None)
    live = task("t", "x", "running", pid=4242, process_start="boot:1")
    assert check.evaluate({PUBLIC: [pr(1, "x")]}, [live], REPOS) == []
    reused = task("t", "x", "running", pid=4242, process_start="boot:2")
    assert len(check.evaluate({PUBLIC: [pr(1, "x")]}, [reused], REPOS)) == 1


def live(task_id, branch, repository=PUBLIC):
    return task(task_id, branch, "running", repository, pid=4242, process_start="boot:1")


def patch_world(monkeypatch, prs, records, repos=REPOS):
    from scripts.dispatcher import worker

    monkeypatch.setattr(worker, "_identity", lambda pid: "boot:1")
    monkeypatch.setattr(check, "load_fleet_repos", lambda: repos)
    monkeypatch.setattr(check, "fetch_open_prs", lambda slug: prs[slug])
    from scripts.dispatcher import store

    monkeypatch.setattr(store, "list_tasks", lambda *a, **k: records)


def test_main_exit_codes_and_output(monkeypatch, capsys):
    prs = {PUBLIC: [pr(1, "a")], PRIVATE: [pr(2, "b")]}
    patch_world(monkeypatch, prs, [live("a", "a")])
    assert check.main(["--json"]) == 1
    assert [row["number"] for row in json.loads(capsys.readouterr().out)] == [2]
    patch_world(monkeypatch, prs, [live("a", "a"), live("b", "b", PRIVATE)])
    assert check.main([]) == 0
    assert capsys.readouterr().out == ""


def test_unreadable_github_is_unknown_not_clean(monkeypatch, capsys):
    patch_world(monkeypatch, {}, [])
    monkeypatch.setattr(check, "fetch_open_prs", lambda slug: (_ for _ in ()).throw(RuntimeError("gh down")))
    assert check.main([]) == 2
    assert "UNKNOWN" in capsys.readouterr().err


def test_unknown_repo_key_is_unknown(monkeypatch):
    patch_world(monkeypatch, {}, [])
    assert check.main(["--repo", "nope"]) == 2


def test_fetch_open_prs_fails_closed_on_gh_error_and_truncation(monkeypatch):
    def fake(stdout, returncode=0):
        return lambda *a, **k: SimpleNamespace(stdout=stdout, stderr="boom", returncode=returncode)

    monkeypatch.setattr(check.github_client, "run", fake("", 1))
    with pytest.raises(RuntimeError):
        check.fetch_open_prs(PUBLIC)
    monkeypatch.setattr(check.github_client, "run", fake(json.dumps([pr(1, "a")] * (check._PR_LIMIT + 1))))
    with pytest.raises(RuntimeError, match="truncated"):
        check.fetch_open_prs(PUBLIC)
    monkeypatch.setattr(check.github_client, "run", fake(json.dumps([pr(1, "a")] * check._PR_LIMIT)))
    assert len(check.fetch_open_prs(PUBLIC)) == check._PR_LIMIT
    monkeypatch.setattr(check.github_client, "run", fake(json.dumps([pr(1, "a")])))
    assert check.fetch_open_prs(PUBLIC) == [pr(1, "a")]


def test_fetch_open_prs_rejects_unusable_rows_and_transport_errors(monkeypatch):
    for rows in ([None], [{"number": "7", "headRefName": "a"}], [{"number": 7}], [{"number": True, "headRefName": "a"}]):
        monkeypatch.setattr(check.github_client, "run", lambda *a, rows=rows, **k: SimpleNamespace(stdout=json.dumps(rows), stderr="", returncode=0))
        with pytest.raises(RuntimeError):
            check.fetch_open_prs(PUBLIC)

    def timeout(*a, **k):
        raise subprocess.TimeoutExpired("gh", 60)

    monkeypatch.setattr(check.github_client, "run", timeout)
    with pytest.raises(RuntimeError, match="TimeoutExpired"):
        check.fetch_open_prs(PUBLIC)


def test_main_returns_unknown_for_a_record_without_task_id_and_for_timeouts(monkeypatch, capsys):
    patch_world(monkeypatch, {PUBLIC: [pr(1, "a")], PRIVATE: []}, [{"worktree_branch": "a", "status": "done"}])
    assert check.main([]) == 1
    assert "[" not in capsys.readouterr().out  # no task id to print, no crash
    monkeypatch.setattr(check, "evaluate", lambda *a, **k: (_ for _ in ()).throw(KeyError("number")))
    assert check.main([]) == 2
    assert "UNKNOWN" in capsys.readouterr().err


def test_documented_module_invocation_shows_help():
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.fleet.pr_owner_check", "--help"],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0 and "Exit codes:" in proc.stdout
