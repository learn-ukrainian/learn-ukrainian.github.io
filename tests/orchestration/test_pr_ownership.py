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


def fake_proc(monkeypatch, files):
    """Serve /proc reads from ``files``: a string is content, an exception is raised."""
    real = own.Path.read_text

    def read(self, *args, **kwargs):
        if str(self).startswith("/proc/"):
            value = files.get(str(self), FileNotFoundError(str(self)))
            if isinstance(value, Exception):
                raise value
            return value
        return real(self, *args, **kwargs)

    monkeypatch.setattr(own.Path, "read_text", read)


STAT = "7 (python) S" + " 0" * 18 + " 555 0"  # field 22 of proc(5), start ticks, is 555


def test_unobservable_owner_is_unknown_and_gone_owner_is_ownerless(monkeypatch):
    prs = [{"number": 42, "headRefName": "codex/x", "isCrossRepository": False}]
    owner = {**task("t"), "pid": 7, "process_start": "boot:555"}
    fake_proc(monkeypatch, {})  # the recorded pid no longer exists
    for extra in ({}, {"pid": 7}, {"pid": 7, "process_start": None}):
        (row,) = find(prs, [{**task("t"), **extra}], live=own.liveness)
        assert row.unknown and "cannot be observed" in row.reason
    (row,) = find(prs, [owner], live=own.liveness)
    assert not row.unknown and "not verifiably alive" in row.reason
    boot = {"/proc/sys/kernel/random/boot_id": "boot\n"}
    fake_proc(monkeypatch, {"/proc/7/stat": STAT, **boot})
    assert find(prs, [owner], live=own.liveness) == []
    fake_proc(monkeypatch, {"/proc/7/stat": STAT.replace(" 555 ", " 556 "), **boot})  # pid reused
    assert own.liveness(owner) is False
    (row,) = find(prs, [task("old", status="done"), task("succ", "claude/q")], {(REPO.casefold(), 42): "succ"},
                  live=lambda r: None if r and r["task_id"] == "succ" else False)
    assert row.unknown


@pytest.mark.parametrize("files", [
    {"/proc/7/stat": PermissionError("stat")},
    {"/proc/7/stat": STAT, "/proc/sys/kernel/random/boot_id": PermissionError("boot")},
    {"/proc/7/stat": "garbage"},
])
def test_any_unreadable_identity_source_is_unknown(monkeypatch, files):
    fake_proc(monkeypatch, files)
    assert own.liveness({**task("t"), "pid": 7, "process_start": "boot:555"}) is None

def fleet(tmp_path):
    with AuthorityService(root=tmp_path / "fleet") as service:
        service.create_channel(own.CTO_CHANNEL)  # exists in the live authority store
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
    assert (recipient, kind) == ("claude-cto", "request") and KEY in body
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


def test_unreadable_source_is_unknown_and_never_counts_toward_grace(tmp_path):
    path = tmp_path / "state.json"
    good = dict(path=path, service_factory=fleet(tmp_path))
    ownerless_now = lambda h: ({KEY}, {KEY: ownerless()})  # noqa: E731
    own.keeper_tick(now=at(0), observe=ownerless_now, **good)

    def broken(handoffs):
        raise RuntimeError("gh down")

    lines, failed = own.keeper_tick(now=at(5), observe=broken, **good)
    assert failed and "UNKNOWN" in lines[0]
    state = own.load(path)
    assert state["episodes"] == {} and state["last_tick"]["ok"] is False
    # The clock restarts once the source is readable again: no alert at minute 60.
    own.keeper_tick(now=at(60), observe=ownerless_now, **good)
    assert own.keeper_tick(now=at(70), observe=ownerless_now, **good)[0][0].endswith("undelivered=0")
    assert inbox(tmp_path) == []
    own.keeper_tick(now=at(75), observe=ownerless_now, **good)
    assert len(inbox(tmp_path)) == 1
    # A raised alert survives an unknown tick.
    own.keeper_tick(now=at(80), observe=broken, **good)
    assert own.load(path)["episodes"][KEY]["alerted_at"]

def test_undelivered_alert_stays_in_the_outbox_and_is_resent_unchanged(tmp_path):
    path = tmp_path / "state.json"
    observe = lambda handoffs: ({KEY}, {KEY: ownerless()})  # noqa: E731
    own.keeper_tick(now=at(0), path=path, observe=observe, service_factory=fleet(tmp_path))

    def down():
        raise OSError("inbox down")

    lines, failed = own.keeper_tick(now=at(15), path=path, observe=observe, service_factory=down)
    assert failed and "undelivered=1" in lines[0]
    (entry,) = own.load(path)["outbox"]
    # The owner reason changes before the retry; the frozen payload does not.
    changed = lambda handoffs: ({KEY}, {KEY: own.Finding(REPO, 42, "codex/x", "new reason", "new")})  # noqa: E731
    lines, failed = own.keeper_tick(now=at(16), path=path, observe=changed, service_factory=fleet(tmp_path))
    assert not failed and "undelivered=0" in lines[0]
    assert [body for _, _, body in inbox(tmp_path)] == [entry["body"]]


def test_delivered_but_unsaved_entry_is_a_noop_on_retry(tmp_path):
    entry = own.outbox_entries({"alert": [{"pr": KEY, "since": at(0).isoformat(), "branch": "b", "reason": "r"}]})
    fleet(tmp_path)
    with AuthorityService(root=tmp_path / "fleet") as service:
        assert own.deliver(list(entry), service) == []
        outbox = list(entry)  # the save after delivery was lost
        assert own.deliver(outbox, service) == [] and outbox == []
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
                      predecessor=predecessor, custody=custody, now=at(30), rerun=rerun, live=is_live,
                      repos=FLEET)


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
                   custody=False, now=at(30), rerun="unspent", live=lambda record: None, repos=FLEET,
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
    monkeypatch.setattr(own, "_queued_at", lambda repo, n, head, base: head == HEAD)
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


# --- round-1 review regressions -----------------------------------------------------


def test_unreadable_process_is_unknown_and_blocks_takeover(monkeypatch):
    fake_proc(monkeypatch, {"/proc/4242/stat": PermissionError("/proc/4242/stat")})
    owner = {**task("owner"), "pid": 4242, "process_start": "boot:1"}
    assert own.liveness(owner) is None
    live = lambda r: own.liveness(r) if r and r["task_id"] == "owner" else is_live(r)  # noqa: E731
    with pytest.raises(own.OwnershipError, match="one owner at a time: owner"):
        own.accept(own._empty(), repo=REPO, number=42, successor="succ", predecessor=None, custody=False,
                   records=[owner, task("succ", "claude/q")], now=at(30), rerun="unspent", repos=FLEET, live=live,
                   pr={"state": "OPEN", "headRefOid": HEAD, "headRefName": "codex/x", "isCrossRepository": False})


def test_unknown_interval_restarts_the_grace_clock():
    data = own._empty()
    own.step(data, {KEY}, {KEY: ownerless()}, at(0))
    own.step(data, {KEY}, {KEY: ownerless(unknown=True)}, at(5))
    assert own.step(data, {KEY}, {KEY: ownerless()}, at(60))["alert"] == []
    assert [row["pr"] for row in own.step(data, {KEY}, {KEY: ownerless()}, at(75))["alert"]] == [KEY]


def test_custody_predecessor_must_own_this_pr_by_the_owner_check():
    other_repo = {**task("waiter"), "repository": "someone/else"}
    with pytest.raises(own.OwnershipError, match="live owner"):
        do_accept(own._empty(), [other_repo, task("integration", "claude/q")],
                  successor="integration", predecessor="waiter", custody=True)
    fork = {"state": "OPEN", "headRefOid": HEAD, "headRefName": "codex/x", "isCrossRepository": True}
    with pytest.raises(own.OwnershipError, match="live owner"):
        do_accept(own._empty(), [task("waiter"), task("integration", "claude/q")],
                  successor="integration", predecessor="waiter", custody=True, pr=fork)
    # An accepted successor on another branch is the PR's owner and may hand over custody.
    data = own._empty()
    accepted(data, 0, successor="waiter")
    receipt = do_accept(data, [task("waiter", "claude/w"), task("integration", "claude/q")],
                        successor="integration", predecessor="waiter", custody=True)
    assert receipt["predecessor"] == "waiter"


def test_queue_membership_is_bound_to_the_custody_head(monkeypatch):
    from scripts.orchestration import integration_sweep

    def membership(self, repo, pr):
        if pr["headRefOid"] != "b" * 40:  # the same observation shows the head moved to B
            raise integration_sweep.SweepError("merge queue head moved or membership unavailable")
        return True

    monkeypatch.setattr(integration_sweep.GitHubAdapter, "queue_membership", membership)
    assert own._queued_at(REPO, 42, HEAD, "main") is None
    assert own._queued_at(REPO, 42, "b" * 40, "main") is True
    assert "custody head" in exit_reasons(custody_state(), queued=None)[0]


def test_notice_identity_ignores_the_clock(tmp_path):
    notices = {"alert": [{"pr": KEY, "since": at(0).isoformat(), "branch": "codex/x", "reason": "r"}]}
    assert own.outbox_entries(notices) == own.outbox_entries(notices)
    later = {"alert": [{"pr": KEY, "since": at(0).isoformat(), "branch": "codex/x", "reason": "r2"}]}
    assert own.outbox_entries(later)[0]["key"] == own.outbox_entries(notices)[0]["key"]

def test_malformed_nested_state_fails_the_tick_without_raising(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({**own._empty(), "episodes": {KEY: None}}))
    lines, failed = own.keeper_tick(now=at(0), path=path, observe=lambda h: pytest.fail("observed"),
                                    service_factory=fleet(tmp_path))
    assert failed and "state unusable" in lines[0]


def test_keeper_keeps_its_queue_result_when_the_ownership_tick_raises(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(keeper, "GitHub", lambda *args: object())
    monkeypatch.setattr(keeper, "run", lambda *a, **k: (["#42 enqueued"], False))
    monkeypatch.setattr(own, "keeper_tick", lambda: (_ for _ in ()).throw(AttributeError("boom")))
    assert keeper.main(["--apply", "--repo-root", str(tmp_path)]) == 1
    assert "#42 enqueued" in capsys.readouterr().out


def test_rate_limit_is_a_skip_for_the_ownership_tick(tmp_path):
    from scripts.common.github_client import GitHubRateLimited

    def limited(handoffs):
        raise GitHubRateLimited("2026-10-28T13:00:00Z")

    path = tmp_path / "s.json"
    own.keeper_tick(now=at(0), path=path, observe=lambda h: ({KEY}, {KEY: ownerless()}),
                    service_factory=fleet(tmp_path))
    lines, failed = own.keeper_tick(now=at(5), path=path, observe=limited, service_factory=fleet(tmp_path))
    assert not failed and "skipped" in lines[0]
    state = own.load(path)
    assert state["last_tick"]["ok"] is False  # queue-exit stays closed
    assert state["episodes"] == {}  # rate-limited time never counts toward grace


def test_retry_after_a_channel_context_change_reconciles_instead_of_stalling(tmp_path):
    entry = own.outbox_entries({"alert": [{"pr": KEY, "since": at(0).isoformat(), "branch": "b", "reason": "r"}]})
    fleet(tmp_path)
    with AuthorityService(root=tmp_path / "fleet") as service:
        assert own.deliver(list(entry), service) == []
        # The save after delivery is lost, then the channel's context revision moves on.
        service.set_channel_context(own.CTO_CHANNEL, "new channel context")
        outbox = list(entry)
        assert own.deliver(outbox, service) == [] and outbox == []
        broken = [{**entry[0], "key": "pr-ownership:alert:other"}]
        service.close()
        assert own.deliver(broken, service) and broken  # a real failure stays queued
    assert len(inbox(tmp_path)) == 1
