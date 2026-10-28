"""Ownerless-PR alert, accepted handoffs and queue custody (scripts/orchestration/pr_ownership.py)."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.fleet_comms.authority import AuthorityService
from scripts.orchestration import merge_queue_keeper as keeper
from scripts.orchestration import pr_ownership as own
from scripts.orchestration.fleet_repos import FleetRepo
from scripts.publish import recovery

REPO = "learn-ukrainian/learn-ukrainian.github.io"
KEY = own.pr_key(REPO, 42)
T0 = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
HEAD = "a" * 40


def ownerless(number=42, unknown=False):
    return own.Finding(REPO, number, "codex/x", "last owner ended timeout, PR not MERGED", "old", unknown=unknown)


def at(minutes):
    return T0 + timedelta(minutes=minutes)


def task(task_id, branch="codex/x", status="running"):
    return {"task_id": task_id, "worktree_branch": branch, "status": status, "repository": REPO}


def is_live(record):
    return record is not None and record.get("status") in {"running", "spawning"}


def accepted(data, minutes, successor="succ", **extra):
    data["handoffs"][KEY] = {"successor": successor, "predecessor": None, "accepted_at": at(minutes).isoformat(),
                             "head": HEAD, "custody": [], "rerun_allowance": "unspent", **extra}


# --- alert episodes ---------------------------------------------------------------


def test_alert_after_fifteen_minutes_once_then_hourly_reminder():
    data = own._empty()
    assert own.step(data, {KEY}, {KEY: ownerless()}, at(0))["alert"] == []
    assert own.step(data, {KEY}, {KEY: ownerless()}, at(14))["alert"] == []
    notices = own.step(data, {KEY}, {KEY: ownerless()}, at(15))
    assert [row["pr"] for row in notices["alert"]] == [KEY]
    assert own.step(data, {KEY}, {KEY: ownerless()}, at(30)) == {"alert": [], "reminder": [], "cleared": []}
    assert [row["pr"] for row in own.step(data, {KEY}, {KEY: ownerless()}, at(75))["reminder"]] == [KEY]


def test_owner_returning_inside_grace_cancels_silently():
    data = own._empty()
    own.step(data, {KEY}, {KEY: ownerless()}, at(0))
    assert own.step(data, {KEY}, {}, at(10)) == {"alert": [], "reminder": [], "cleared": []}
    assert data["episodes"] == {}


def test_unknown_telemetry_never_starts_advances_or_clears():
    data = own._empty()
    own.step(data, {KEY}, {KEY: ownerless(unknown=True)}, at(0))
    assert data["episodes"] == {}
    own.step(data, {KEY}, {KEY: ownerless()}, at(0))
    own.step(data, {KEY}, {KEY: ownerless()}, at(15))
    before = json.dumps(data["episodes"], sort_keys=True)
    accepted(data, 20)
    assert own.step(data, {KEY}, {KEY: ownerless(unknown=True)}, at(90)) == {"alert": [], "reminder": [], "cleared": []}
    assert json.dumps(data["episodes"], sort_keys=True) == before


def test_alert_stays_outstanding_until_a_successor_accepts():
    data = own._empty()
    own.step(data, {KEY}, {KEY: ownerless()}, at(0))
    own.step(data, {KEY}, {KEY: ownerless()}, at(15))
    # A task now owns the branch, but nobody recorded acceptance: still outstanding.
    assert own.step(data, {KEY}, {}, at(20))["cleared"] == []
    assert data["episodes"][KEY]["alerted_at"]
    # A handoff accepted before this episode began does not count.
    accepted(data, -5)
    assert own.step(data, {KEY}, {}, at(21))["cleared"] == []
    accepted(data, 22)
    notices = own.step(data, {KEY}, {}, at(23))
    assert notices["cleared"][0]["how"] == "handoff accepted by succ"
    assert data["episodes"] == {} and data["history"][-1]["event"] == "cleared"


def test_closed_pr_clears_alert_and_drops_handoff():
    data = own._empty()
    own.step(data, {KEY}, {KEY: ownerless()}, at(0))
    own.step(data, {KEY}, {KEY: ownerless()}, at(15))
    accepted(data, 16)
    notices = own.step(data, set(), {}, at(20))
    assert notices["cleared"][0]["how"] == "PR no longer open"
    assert data["episodes"] == {} and data["handoffs"] == {}


# --- the owner check with handoffs and unknown liveness ----------------------------

FLEET = {"public": FleetRepo("public", REPO, "learn-ukrainian", "public-monorepo", True)}


def find(prs, records, handoffs=None, live=is_live):
    return own.findings({REPO: prs}, records, FLEET, handoffs or {}, live)


def test_accepted_successor_owns_from_another_branch_while_live():
    prs = [{"number": 42, "headRefName": "codex/x", "isCrossRepository": False}]
    records = [task("old", status="timeout"), task("succ", "claude/queue")]
    (row,) = find(prs, records)
    assert not row.unknown and row.last_task == "old"
    assert find(prs, records, {(REPO.casefold(), 42): "succ"}) == []
    finished = [task("old", status="timeout"), task("succ", "claude/queue", "done")]
    (row,) = find(prs, finished, {(REPO.casefold(), 42): "succ"})
    assert not row.unknown
    fork = [{"number": 42, "headRefName": "codex/x", "isCrossRepository": True}]
    assert find(fork, records, {(REPO.casefold(), 42): "succ"}) == []


def test_unobservable_owner_is_unknown_and_gone_owner_is_ownerless(monkeypatch):
    from scripts.dispatcher import worker

    prs = [{"number": 42, "headRefName": "codex/x", "isCrossRepository": False}]
    monkeypatch.setattr(worker, "_identity", lambda pid: None)  # the recorded pid no longer exists
    for extra in ({}, {"pid": 7}, {"pid": 7, "process_start": None}):
        (row,) = find(prs, [{**task("t"), **extra}], live=own.liveness)
        assert row.unknown and "cannot be observed" in row.reason
    (row,) = find(prs, [{**task("t"), "pid": 7, "process_start": "boot:1"}], live=own.liveness)
    assert not row.unknown and "not verifiably alive" in row.reason
    monkeypatch.setattr(worker, "_identity", lambda pid: "boot:1")
    assert find(prs, [{**task("t"), "pid": 7, "process_start": "boot:1"}], live=own.liveness) == []
    monkeypatch.setattr(own.Path, "exists", lambda self: False)  # no process table on this host
    assert own.liveness({**task("t"), "pid": 7, "process_start": "boot:1"}) is None
    monkeypatch.undo()
    (row,) = find(prs, [task("old", status="done"), task("succ", "claude/q")], {(REPO.casefold(), 42): "succ"},
                  live=lambda r: None if r and r["task_id"] == "succ" else False)
    assert row.unknown


# --- keeper tick ------------------------------------------------------------------


def fleet(tmp_path):
    return lambda: AuthorityService(root=tmp_path / "fleet")


def inbox(tmp_path):
    with AuthorityService(root=tmp_path / "fleet") as service:
        rows = service._conn.execute("SELECT message_id, recipient, kind FROM comms_messages").fetchall()
        return [(row[1], row[2], service.read_message_body(row[0])) for row in rows]


def test_tick_alerts_cto_inbox_and_clears_on_accepted_handoff(tmp_path):
    path = tmp_path / "state.json"
    observation = ({KEY}, {KEY: ownerless()})
    tick = dict(path=path, observe=lambda handoffs: observation, service_factory=fleet(tmp_path))
    assert own.keeper_tick(now=at(0), **tick)[1] is False
    assert inbox(tmp_path) == []
    assert own.keeper_tick(now=at(3), **tick) == ([], False)  # throttled
    lines, failed = own.keeper_tick(now=at(15), **tick)
    assert not failed and f"pr ownership alert outstanding: {KEY}" in lines
    ((recipient, kind, body),) = inbox(tmp_path)
    assert (recipient, kind) == ("claude-cto", "supervisory-request") and KEY in body
    with own.locked(path) as data:
        accepted(data, 16)
    seen = {}

    def owned(handoffs):
        seen.update(handoffs)
        return {KEY}, {}

    lines, _ = own.keeper_tick(now=at(20), path=path, observe=owned, service_factory=fleet(tmp_path))
    assert seen == {(REPO.casefold(), 42): "succ"}
    assert "cleared=1" in lines[0]
    assert "Ownerless-PR alerts cleared" in inbox(tmp_path)[-1][2]


def test_unreadable_source_is_unknown_and_changes_nothing(tmp_path):
    path = tmp_path / "state.json"
    good = dict(path=path, service_factory=fleet(tmp_path))
    own.keeper_tick(now=at(0), observe=lambda h: ({KEY}, {KEY: ownerless()}), **good)
    before = own.load(path)["episodes"]

    def broken(handoffs):
        raise RuntimeError("gh down")

    lines, failed = own.keeper_tick(now=at(20), observe=broken, **good)
    assert failed and "UNKNOWN" in lines[0]
    state = own.load(path)
    assert state["episodes"] == before and state["last_tick"]["ok"] is False


def test_inbox_failure_commits_nothing_and_next_tick_resends(tmp_path):
    path = tmp_path / "state.json"
    observe = lambda handoffs: ({KEY}, {KEY: ownerless()})  # noqa: E731
    own.keeper_tick(now=at(0), path=path, observe=observe, service_factory=fleet(tmp_path))

    def down():
        raise OSError("inbox down")

    _, failed = own.keeper_tick(now=at(15), path=path, observe=observe, service_factory=down)
    assert failed and own.load(path)["episodes"][KEY]["alerted_at"] is None
    own.keeper_tick(now=at(16), path=path, observe=observe, service_factory=fleet(tmp_path))
    assert len(inbox(tmp_path)) == 1


def test_keeper_apply_runs_the_ownership_tick(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(keeper, "GitHub", lambda *args: object())
    monkeypatch.setattr(keeper, "run", lambda *a, **k: (_ for _ in ()).throw(keeper.KeeperError("queue down")))
    monkeypatch.setattr(own, "keeper_tick", lambda: calls.append(1) or (["pr ownership: open=0"], False))
    assert keeper.main(["--apply", "--repo-root", str(tmp_path)]) == 1  # queue failure still reported
    assert calls == [1]


# --- accept -----------------------------------------------------------------------


def do_accept(data, records, *, successor="succ", predecessor=None, custody=False, pr=None, rerun="unspent"):
    pr = pr or {"state": "OPEN", "headRefOid": HEAD, "headRefName": "codex/x", "isCrossRepository": False}
    return own.accept(data, repo=REPO, number=42, pr=pr, successor=successor, records=records,
                      predecessor=predecessor, custody=custody, now=at(30), rerun=rerun, live=is_live)


def test_accept_records_one_owner_and_refuses_a_second():
    data = own._empty()
    records = [task("old", status="timeout"), task("succ", "claude/queue"), task("other", "claude/other")]
    receipt = do_accept(data, records, rerun="RECOVERY_ALLOWANCE_SPENT: first=run-rerun")
    assert receipt["successor"] == "succ" and receipt["rerun_allowance"].startswith("RECOVERY_ALLOWANCE_SPENT")
    with pytest.raises(own.OwnershipError, match="one owner at a time: succ"):
        do_accept(data, records, successor="other")
    assert do_accept(data, records)["successor"] == "succ"  # re-accepting is idempotent


def test_accept_refuses_while_a_live_task_owns_the_branch_or_successor_is_not_live():
    records = [task("live-owner"), task("succ", "claude/queue"), task("dead", "claude/d", "done")]
    with pytest.raises(own.OwnershipError, match="live-owner"):
        do_accept(own._empty(), records)
    with pytest.raises(own.OwnershipError, match="not live"):
        do_accept(own._empty(), records, successor="dead")
    with pytest.raises(own.OwnershipError, match="unknown"):
        own.accept(own._empty(), repo=REPO, number=42, successor="succ", records=records, predecessor=None,
                   custody=False, now=at(30), rerun="unspent", live=lambda record: None,
                   pr={"state": "OPEN", "headRefOid": HEAD, "headRefName": "codex/x"})
    with pytest.raises(own.OwnershipError, match="MERGED"):
        do_accept(own._empty(), records, pr={"state": "MERGED", "headRefOid": HEAD, "headRefName": "codex/x"})


def test_custody_needs_the_live_waiting_owner_as_predecessor():
    records = [task("waiter"), task("integration", "claude/queue"), task("stranger", "claude/s")]
    with pytest.raises(own.OwnershipError, match="needs --custody"):
        do_accept(own._empty(), records, successor="integration", predecessor="waiter")
    with pytest.raises(own.OwnershipError, match="live owner"):
        do_accept(own._empty(), records, successor="integration", predecessor="stranger", custody=True)
    data = own._empty()
    receipt = do_accept(data, records, successor="integration", predecessor="waiter", custody=True)
    assert receipt["custody"] == list(own.CUSTODY_COVERS) and receipt["predecessor"] == "waiter"


def test_rerun_allowance_is_carried_across_owner_changes(tmp_path, monkeypatch):
    ledger = tmp_path / "ci-recovery.sqlite3"
    monkeypatch.setattr(recovery, "ledger_path", lambda cwd: ledger)
    assert own._rerun_allowance(REPO, 42, HEAD) == "unspent"
    # The first owner spends the head's one evidenced rerun ...
    recovery.consume(ledger, REPO, 42, HEAD, "run-rerun", {"run_id": 7})
    # ... and the successor's acceptance carries it: no fresh allowance on the same head.
    assert own._rerun_allowance(REPO, 42, HEAD).startswith("RECOVERY_ALLOWANCE_SPENT")
    assert own._rerun_allowance(REPO, 42, "b" * 40) == "unspent"


# --- queue exit -------------------------------------------------------------------


def custody_state(tick_minutes=25, ok=True):
    data = own._empty()
    data["last_tick"] = {"at": at(tick_minutes).isoformat(), "ok": ok}
    accepted(data, 26, successor="integration", predecessor="waiter", custody=list(own.CUSTODY_COVERS))
    return data


def exit_reasons(data, *, pr_head=HEAD, queued=True, state="OPEN", records=None, me="waiter"):
    records = records if records is not None else [task("waiter"), task("integration", "claude/queue")]
    return own.queue_exit(data, repo=REPO, number=42, pr={"state": state, "headRefOid": pr_head},
                          queued=queued, me=me, records=records, now=at(30), live=is_live)


def test_queue_exit_allowed_only_under_live_custody_with_the_alert_running():
    assert exit_reasons(custody_state()) == []
    assert "ownership alert" in exit_reasons(custody_state(tick_minutes=0))[0]
    assert "ownership alert" in exit_reasons(custody_state(ok=False))[0]
    assert "head moved" in exit_reasons(custody_state(), pr_head="b" * 40)[0]
    assert "merge queue" in exit_reasons(custody_state(), queued=None)[0]
    assert "closeout yourself" in exit_reasons(custody_state(), state="MERGED", queued=False)[0]
    dead = [task("waiter"), task("integration", "claude/queue", "timeout")]
    assert "not verifiably live" in exit_reasons(custody_state(), records=dead)[0]
    assert "no accepted queue custody" in exit_reasons(custody_state(), me="someone-else")[0]
    plain = custody_state()
    plain["handoffs"][KEY]["custody"] = []
    assert "no accepted queue custody" in exit_reasons(plain)[0]


# --- CLI --------------------------------------------------------------------------


@pytest.fixture
def world(tmp_path, monkeypatch):
    from scripts.dispatcher import store
    from scripts.orchestration import fleet_repos

    path = tmp_path / "pr_ownership" / "state.json"
    monkeypatch.setattr(own, "state_path", lambda: path)
    records = [task("waiter"), task("integration", "claude/queue")]
    monkeypatch.setattr(store, "list_tasks", lambda *a, **k: records)
    monkeypatch.setattr(own, "liveness", is_live)
    monkeypatch.setattr(own, "_gh_pr", lambda repo, n: {"state": "OPEN", "headRefOid": HEAD, "headRefName": "codex/x"})
    monkeypatch.setattr(own, "_rerun_allowance", lambda *a: "unspent")
    repo = fleet_repos.FleetRepo("public", REPO, "learn-ukrainian", "public-monorepo", True)
    monkeypatch.setattr(fleet_repos, "load_fleet_repos", lambda: {"public": repo})
    return path


def test_cli_accept_then_queue_exit(world, monkeypatch, capsys):
    monkeypatch.delenv(own.TASK_ENV, raising=False)
    assert own.main(["accept", "--pr", "42"]) == 2
    monkeypatch.setenv(own.TASK_ENV, "integration")
    assert own.main(["accept", "--pr", "42", "--custody", "--from", "waiter"]) == 0
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["accepted"] is True
    assert own.accepted_handoffs(world) == {(REPO.casefold(), 42): "integration"}
    from scripts import gh_merge_queue_status

    monkeypatch.setattr(gh_merge_queue_status, "fetch_live_status", lambda n, repo: type("S", (), {"queued": True}))
    monkeypatch.setenv(own.TASK_ENV, "waiter")
    with own.locked(world) as data:
        data["last_tick"] = {"at": datetime.now(UTC).isoformat(), "ok": True}
    capsys.readouterr()
    assert own.main(["queue-exit", "--pr", "42"]) == 0
    assert json.loads(capsys.readouterr().out) == {"may_exit": True, "reasons": []}
    assert own.main(["status"]) == 0


def test_documented_module_invocation_shows_help():
    import subprocess
    import sys

    proc = subprocess.run([sys.executable, "-m", "scripts.orchestration.pr_ownership", "--help"],
                          capture_output=True, text=True, timeout=60, check=False,
                          cwd=Path(__file__).resolve().parents[2])
    assert proc.returncode == 0 and "Exit codes:" in proc.stdout
