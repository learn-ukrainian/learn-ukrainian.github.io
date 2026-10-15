"""Per-caller hourly request counters in the shared GitHub client's counter store (#10730, #10660). No network."""

from __future__ import annotations

import json
import multiprocessing
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.common import github_budget_counters as counters
from scripts.common import github_client as gh

REPO_ROOT = Path(__file__).resolve().parents[2]
NOW = 10 * 3600 + 120  # two minutes into an hour bucket
HOUR = 10 * 3600


def reply(value=None, *, remaining=5000, reset=NOW + 3000, status=200):
    return gh.Response(
        status,
        {"X-RateLimit-Remaining": str(remaining), "X-RateLimit-Reset": str(reset)},
        json.dumps(value if value is not None else {}).encode(),
    )


def make(tmp_path, *, caller=None, now=NOW, answers=None):
    calls = []

    def transport(method, endpoint, headers, body, timeout):
        calls.append((method, endpoint))
        return answers(len(calls)) if answers else reply()

    return gh.GitHubClient(cache_dir=tmp_path, transport=transport, clock=lambda: now, env={}, caller=caller), calls


def store(tmp_path):
    return counters.store_path(tmp_path)


def rows(tmp_path):
    db = sqlite3.connect(store(tmp_path))
    try:
        return db.execute(
            "SELECT hour,resource,caller,count FROM caller_counter ORDER BY hour,resource,caller"
        ).fetchall()
    finally:
        db.close()


def seed_rows(tmp_path, entries):
    """Write counter rows directly, as an earlier client would have left them."""
    db = sqlite3.connect(store(tmp_path))
    db.execute(counters.SCHEMA)
    db.executemany("INSERT INTO caller_counter(hour,resource,caller,count) VALUES(?,?,?,?)", entries)
    db.commit()
    db.close()


def reported(tmp_path, resource="core"):
    """Durable counts as the Ops API report serves them: ``{caller: count}`` for the current hour."""
    rows_ = counters.report_for(tmp_path, NOW, limit=50)["windows"]["current"]["resources"][resource]
    return {row["caller"]: row["count"] for row in rows_}


def test_two_callers_produce_separate_counters(tmp_path):
    keeper, _ = make(tmp_path, caller="keeper")
    watcher, _ = make(tmp_path, caller="ci-watcher")
    for _ in range(3):
        keeper.request("GET", "repos/o/r/issues/1", fresh=True)
    watcher.request("GET", "repos/o/r/issues/2", fresh=True)
    assert rows(tmp_path) == [(HOUR, "core", "ci-watcher", 1), (HOUR, "core", "keeper", 3)]


def test_resources_are_counted_separately(tmp_path):
    client, _ = make(tmp_path, caller="drv")
    client.request("GET", "repos/o/r/issues/1")
    client.request("POST", "graphql", payload={"query": "query { viewer { login } }"})
    client.request("GET", "search/issues?q=x")
    client.request("GET", "search/code?q=x")
    assert rows(tmp_path) == [
        (HOUR, "core", "drv", 1),
        (HOUR, "graphql", "drv", 1),
        (HOUR, "search", "drv", 2),
    ]


def test_each_hour_has_its_own_bucket(tmp_path):
    early, _ = make(tmp_path, caller="drv", now=HOUR + 5)
    late, _ = make(tmp_path, caller="drv", now=HOUR + 3600 + 5)
    early.request("GET", "repos/o/r/issues/1")
    late.request("GET", "repos/o/r/issues/1")
    assert [(r[0], r[3]) for r in rows(tmp_path)] == [(HOUR, 1), (HOUR + 3600, 1)]


def test_cache_hits_count_nothing(tmp_path):
    # A stale answer served while the pool is exhausted is the client's only cache hit: no request leaves.
    client, calls = make(tmp_path, caller="drv", answers=lambda n: reply([1], remaining=0))
    client.request("GET", "repos/o/r/issues")
    served = client.request("GET", "repos/o/r/issues", allow_stale=True)
    assert served.stale and served.value == [1]
    assert len(calls) == 1
    assert rows(tmp_path) == [(HOUR, "core", "drv", 1)]


def test_a_304_revalidation_reaches_the_network_and_counts(tmp_path):
    first, _ = make(tmp_path, caller="drv", answers=lambda n: gh.Response(200, {"ETag": '"e"'}, b"[1]"))
    first.request("GET", "repos/o/r/issues")
    second, calls = make(tmp_path, caller="drv", answers=lambda n: gh.Response(304, {}, b""))
    assert second.request("GET", "repos/o/r/issues").status == 304
    assert len(calls) == 1
    assert rows(tmp_path) == [(HOUR, "core", "drv", 2)]


@pytest.mark.parametrize("tag", ["", "Keeper", "has space", "a/b", "x" * 65, "-lead", "k\nline", 7, b"keeper"])
def test_unknown_or_unsafe_explicit_tag_is_recorded_as_unknown(tmp_path, tag):
    client, _ = make(tmp_path, caller=tag)
    client.request("GET", "repos/o/r/issues/1")
    assert rows(tmp_path) == [(HOUR, "core", "unknown", 1)]


def test_a_tag_at_the_length_bound_is_kept(tmp_path):
    tag = "k" * counters.CALLER_MAX_LENGTH
    client, _ = make(tmp_path, caller=tag)
    client.request("GET", "repos/o/r/issues/1")
    assert rows(tmp_path)[0][2] == tag


def test_default_caller_comes_from_the_entry_module(monkeypatch):
    monkeypatch.setattr(counters, "_process_caller", None)
    monkeypatch.setitem(
        sys.modules, "__main__", SimpleNamespace(__spec__=SimpleNamespace(name="scripts.publish.__main__"))
    )
    assert counters.resolve_caller() == "scripts.publish"
    monkeypatch.setitem(sys.modules, "__main__", SimpleNamespace(__spec__=None))
    monkeypatch.setattr(sys, "argv", ["/x/My Poller.py"])
    assert counters.resolve_caller() == "my_poller"
    monkeypatch.setattr(sys, "argv", [""])
    assert counters.resolve_caller() == "unknown"


def test_process_tag_beats_the_default_and_loses_to_an_explicit_tag(monkeypatch):
    monkeypatch.setattr(counters, "_process_caller", None)
    counters.set_process_caller("keeper")
    assert counters.resolve_caller() == "keeper"
    assert counters.resolve_caller("drv") == "drv"
    counters.set_process_caller("Not Valid")
    assert counters.resolve_caller() == "unknown"


def test_the_client_resolves_its_tag_lazily(tmp_path, monkeypatch):
    monkeypatch.setattr(counters, "_process_caller", None)
    client, _ = make(tmp_path)
    counters.set_process_caller("late-tag")
    client.request("GET", "repos/o/r/issues/1")
    assert rows(tmp_path) == [(HOUR, "core", "late-tag", 1)]


def test_the_store_is_one_wal_database_beside_an_untouched_cache(tmp_path):
    client, _ = make(tmp_path, caller="drv")
    client.request("GET", "repos/o/r/issues/1")
    db = sqlite3.connect(store(tmp_path))
    assert db.execute("PRAGMA journal_mode").fetchone() == ("wal",)
    db.close()
    cache = sqlite3.connect(tmp_path / "cache.sqlite3")
    tables = {name for (name,) in cache.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    cache.close()
    assert "caller_counter" not in tables  # counting never writes the cache database
    assert oct(store(tmp_path).stat().st_mode & 0o777) == oct(0o600)


def test_concurrent_threads_do_not_lose_or_corrupt_counts(tmp_path):
    threads, per_thread = 8, 25
    errors = []

    def work(index):
        client, _ = make(tmp_path, caller=f"worker-{index % 2}")
        try:
            for _ in range(per_thread):
                assert not client.request("GET", "repos/o/r/issues/1", fresh=True).counter_degraded
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    pool = [threading.Thread(target=work, args=(i,)) for i in range(threads)]
    for thread in pool:
        thread.start()
    for thread in pool:
        thread.join()
    assert not errors
    assert rows(tmp_path) == [
        (HOUR, "core", "worker-0", per_thread * threads // 2),
        (HOUR, "core", "worker-1", per_thread * threads // 2),
    ]
    db = sqlite3.connect(store(tmp_path))
    assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    db.close()


def test_concurrent_processes_do_not_lose_or_corrupt_counts(tmp_path):
    program = (
        "import json, sys\n"
        "from scripts.common import github_client as gh\n"
        "def transport(*a):\n"
        "    return gh.Response(200, {'X-RateLimit-Remaining': '5000', 'X-RateLimit-Reset': '99999'}, b'{}')\n"
        f"client = gh.GitHubClient(cache_dir=sys.argv[1], transport=transport, clock=lambda: {NOW}, env={{}}, caller='proc')\n"
        "for _ in range(15):\n"
        "    client.request('GET', 'repos/o/r/issues/1', fresh=True)\n"
    )
    children = [
        subprocess.Popen([sys.executable, "-c", program, str(tmp_path)], cwd=REPO_ROOT, stderr=subprocess.PIPE)
        for _ in range(3)
    ]
    assert [child.wait(timeout=60) for child in children] == [0, 0, 0]
    assert rows(tmp_path) == [(HOUR, "core", "proc", 45)]


def test_retention_drops_buckets_older_than_seven_days(tmp_path):
    week = 7 * 24 * 3600
    seed_rows(
        tmp_path,
        [
            (hour, "core", "old", 9)
            for hour in (HOUR - week - 7200, HOUR - week - 3600, HOUR - week + 3600, HOUR - 3600)
        ],
    )
    client, _ = make(tmp_path, caller="drv")
    client.request("GET", "repos/o/r/issues/1")
    kept = [r[0] for r in rows(tmp_path)]
    assert kept == [HOUR - week + 3600, HOUR - 3600, HOUR]


def test_retention_boundary_is_exactly_seven_days(tmp_path):
    week = 7 * 24 * 3600
    seed_rows(tmp_path, [(HOUR - week - 3600, "core", "old", 1), (HOUR - week, "core", "old", 1)])
    client, _ = make(tmp_path, caller="drv")
    client.request("GET", "repos/o/r/issues/1")
    assert [r[0] for r in rows(tmp_path)] == [HOUR - week, HOUR]


def test_rows_hold_no_request_content(tmp_path):
    secret = "ghp_SECRETTOKENVALUE1234567890"
    client = gh.GitHubClient(
        cache_dir=tmp_path,
        transport=lambda *a: reply(),
        clock=lambda: NOW,
        env={"GH_TOKEN": secret},
        caller="drv",
    )
    client.request("POST", "repos/secret-owner/secret-repo/issues/77/comments", payload={"body": "private-body-text"})
    client.request("POST", "graphql", payload={"query": "query { secretField }"})
    db = sqlite3.connect(store(tmp_path))
    columns = [c[1] for c in db.execute("PRAGMA table_info(caller_counter)")]
    stored = json.dumps(db.execute("SELECT * FROM caller_counter").fetchall())
    db.close()
    assert columns == ["hour", "resource", "caller", "count", "last_remaining", "last_reset"]
    for marker in (secret, "secret-owner", "secret-repo", "private-body-text", "secretField", "comments", "issues"):
        assert marker not in stored
    assert client.scope not in stored


def test_last_rate_limit_headers_are_kept_per_bucket(tmp_path):
    client, _ = make(tmp_path, caller="drv", answers=lambda n: reply(remaining=4000 - n, reset=NOW + 99))
    client.request("GET", "repos/o/r/issues/1")
    client.request("GET", "repos/o/r/issues/2")
    db = sqlite3.connect(store(tmp_path))
    assert db.execute("SELECT count,last_remaining,last_reset FROM caller_counter").fetchone() == (2, 3998, NOW + 99)
    db.close()


def test_report_orders_callers_by_count_then_name(tmp_path):
    seed_rows(
        tmp_path,
        [(HOUR, "core", caller, count) for caller, count in (("b", 5), ("a", 5), ("z", 9), ("c", 1))]
        + [(HOUR - 3600, "search", "old", 2)],
    )
    report = counters.report_for(tmp_path, NOW, limit=3)
    assert report["windows"]["current"]["resources"]["core"] == [
        {"caller": "z", "count": 9},
        {"caller": "a", "count": 5},
        {"caller": "b", "count": 5},
    ]
    assert report["windows"]["previous"]["resources"]["search"] == [{"caller": "old", "count": 2}]
    assert report["windows"]["current"]["hour_start"] == HOUR
    assert report["windows"]["previous"]["hour_start"] == HOUR - 3600


def test_report_carries_the_remaining_budget_and_ignores_expired_windows(tmp_path):
    client, _ = make(tmp_path, caller="drv", answers=lambda n: reply(remaining=321, reset=NOW + 500))
    client.request("GET", "repos/o/r/issues/1")
    report = counters.report_for(tmp_path, NOW)
    assert report["budget"] == {"core": {"remaining": 321, "reset_at": NOW + 500}}
    assert counters.report_for(tmp_path, NOW + 501)["budget"] == {}


def test_report_without_a_database_or_table_is_empty(tmp_path):
    empty = counters.report_for(tmp_path / "missing", NOW)
    assert empty["windows"]["current"]["resources"] == {"core": [], "graphql": [], "search": []}
    sqlite3.connect(store(tmp_path)).close()
    sqlite3.connect(tmp_path / "cache.sqlite3").close()
    assert counters.report_for(tmp_path, NOW)["windows"]["previous"]["resources"]["core"] == []
    assert counters.report_for(tmp_path, NOW)["budget"] == {}
    assert counters.report_for(None, NOW)["budget"] == {}


def test_report_command_prints_text_and_json(tmp_path, capsys):
    client, _ = make(tmp_path, caller="keeper", now=int(time.time()))
    client.request("GET", "repos/o/r/issues/1")
    assert counters.main(["report", "--cache-dir", str(tmp_path)]) == 0
    text = capsys.readouterr().out
    assert "current hour from" in text and "keeper" in text and "core" in text
    assert counters.main(["report", "--cache-dir", str(tmp_path), "--json", "--limit", "1"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert document["schema"] == "github-budget-callers.v1"
    assert document["windows"]["current"]["resources"]["core"] == [{"caller": "keeper", "count": 1}]


def test_report_command_rejects_a_bad_limit(tmp_path):
    with pytest.raises(SystemExit) as stop:
        counters.main(["report", "--cache-dir", str(tmp_path), "--limit", "0"])
    assert stop.value.code == 2


# --- a store failure drops the count and says so; it never fails or delays the request ----------


def test_a_storage_error_never_blocks_a_request(tmp_path, monkeypatch, caplog):
    def broken(*args, **kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(counters, "record", broken)
    client, calls = make(tmp_path, caller="drv")
    with caplog.at_level("WARNING", logger=counters.logger.name):
        first = client.request("GET", "repos/o/r/issues/1")
        second = client.request("GET", "repos/o/r/issues/2")
    assert first.status == 200 and second.status == 200 and len(calls) == 2
    assert first.counter_degraded and second.counter_degraded and client.dropped_counts == 2
    # One warning per client, never request content.
    assert [r.getMessage() for r in caplog.records] == ["github_counter_degraded pool=core caller=drv requests=1"]


def test_a_client_without_a_disk_cache_drops_counts_as_degraded(tmp_path, monkeypatch):
    monkeypatch.setattr(gh, "_cache_directory", lambda: None)
    client = gh.GitHubClient(transport=lambda *a: reply(), clock=lambda: NOW, env={}, caller="drv")
    result = client.request("GET", "repos/o/r/issues/1")
    assert result.status == 200 and result.counter_degraded and client.dropped_counts == 1


HOLDER = (
    "import sqlite3, sys, time\n"
    "db = sqlite3.connect(sys.argv[1], isolation_level=None)\n"
    "db.execute('BEGIN EXCLUSIVE')\n"
    "print('locked', flush=True)\n"
    "time.sleep(float(sys.argv[2]))\n"
    "db.execute('COMMIT')\n"
)


def hold(path, seconds):
    holder = subprocess.Popen(
        [sys.executable, "-c", HOLDER, str(path), str(seconds)], stdout=subprocess.PIPE, text=True, cwd=REPO_ROOT
    )
    assert holder.stdout.readline().strip() == "locked"
    return holder


def test_a_store_locked_past_the_bound_drops_the_count_without_delaying_the_request(tmp_path):
    client, _ = make(tmp_path, caller="drv")
    client.request("GET", "repos/o/r/issues/1", fresh=True)
    holder = hold(store(tmp_path), 3.0)
    try:
        started = time.monotonic()
        busy, calls = make(tmp_path, caller="drv")
        result = busy.request("GET", "repos/o/r/issues/2", fresh=True)
        waited = time.monotonic() - started
    finally:
        assert holder.wait(timeout=30) == 0
    assert result.status == 200 and len(calls) == 1
    assert result.counter_degraded and busy.dropped_counts == 1
    assert waited < counters.WRITE_BUSY_MS / 1000 + 1.0  # bounded by the write wait, not by the lock
    after, _ = make(tmp_path, caller="drv")
    assert not after.request("GET", "repos/o/r/issues/3", fresh=True).counter_degraded
    assert rows(tmp_path) == [(HOUR, "core", "drv", 2)]  # exactly the two counts that could be stored


def test_a_cache_locked_past_its_timeout_still_counts_the_request(tmp_path):
    # Review round 1 (F3): the cache falls back to private memory, the count stays durable.
    client, _ = make(tmp_path, caller="drv")
    client.request("GET", "repos/o/r/issues/1", fresh=True)
    holder = hold(tmp_path / "cache.sqlite3", 6.0)
    try:
        busy, calls = make(tmp_path, caller="drv")
        result = busy.request("GET", "repos/o/r/issues/2", fresh=True)
    finally:
        assert holder.wait(timeout=30) == 0
    assert result.status == 200 and len(calls) == 1 and not result.counter_degraded
    assert rows(tmp_path) == [(HOUR, "core", "drv", 2)]


# --- two writer processes (review round 2: F2) --------------------------------------------------


def _first_writer(cache_dir, now, in_transport, go, paused, resume):
    """Writer process A. Its transport waits for the parent; its count runs while the cache is locked.

    The spill design appended such a count to a file that another writer could merge and unlink
    before the append landed; the pause on that append is inert where counting is one SQLite upsert.
    """
    from scripts.common import github_budget_counters as counters
    from scripts.common import github_client as gh

    real_write = os.write

    def write(descriptor, data):
        if b"\tmp-a\t" in bytes(data):
            paused.set()
            resume.wait(30)
        return real_write(descriptor, data)

    os.write = write
    counters.COUNT_BUSY_SECONDS = 0.2  # the spill design's lock wait, shortened; unused by the SQLite store

    def transport(*args):
        in_transport.set()
        go.wait(30)
        return gh.Response(200, {}, b"{}")

    client = gh.GitHubClient(cache_dir=cache_dir, transport=transport, clock=lambda: now, env={}, caller="mp-a")
    if client.request("GET", "repos/o/r/issues/1", fresh=True).status != 200:
        raise SystemExit(3)


def _second_writer(cache_dir, now):
    from scripts.common import github_client as gh

    client = gh.GitHubClient(
        cache_dir=cache_dir, transport=lambda *a: gh.Response(200, {}, b"{}"), clock=lambda: now, env={}, caller="mp-b"
    )
    if client.request("GET", "repos/o/r/issues/2", fresh=True).status != 200:
        raise SystemExit(3)


def _barrier_writer(cache_dir, now, caller, requests, barrier):
    from scripts.common import github_client as gh

    client = gh.GitHubClient(
        cache_dir=cache_dir, transport=lambda *a: gh.Response(200, {}, b"{}"), clock=lambda: now, env={}, caller=caller
    )
    barrier.wait(30)
    degraded = sum(client.request("GET", "repos/o/r/issues/1", fresh=True).counter_degraded for _ in range(requests))
    if degraded:
        raise SystemExit(4)


def test_two_writer_processes_both_count_while_one_is_held_mid_count(tmp_path):
    context = multiprocessing.get_context("spawn")
    in_transport, go, paused, resume = (context.Event() for _ in range(4))
    with gh.GitHubClient(cache_dir=tmp_path, env={})._db():
        pass  # the cache exists before process A reads it
    first = context.Process(target=_first_writer, args=(str(tmp_path), NOW, in_transport, go, paused, resume))
    first.start()
    try:
        assert in_transport.wait(60), "process A never reached its transport"
        lock = sqlite3.connect(tmp_path / "cache.sqlite3", isolation_level=None)
        lock.execute("BEGIN EXCLUSIVE")
        go.set()
        paused.wait(2.5)  # the spill design pauses mid-append here; the SQLite store never does
        lock.execute("COMMIT")
        lock.close()
        second = context.Process(target=_second_writer, args=(str(tmp_path), NOW))
        second.start()
        second.join(60)
        resume.set()
        first.join(60)
    finally:
        resume.set()
        go.set()
        for process in multiprocessing.active_children():
            process.kill()
    assert (first.exitcode, second.exitcode) == (0, 0)
    assert reported(tmp_path) == {"mp-a": 1, "mp-b": 1}  # two sent requests, two durable counts


def test_writer_processes_released_together_lose_no_increment(tmp_path):
    context = multiprocessing.get_context("spawn")
    writers, per_writer = 3, 20
    barrier = context.Barrier(writers)
    processes = [
        context.Process(target=_barrier_writer, args=(str(tmp_path), NOW, f"mp-{i}", per_writer, barrier))
        for i in range(writers)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(120)
    assert [process.exitcode for process in processes] == [0] * writers  # 4 would mean a dropped count
    assert reported(tmp_path) == {f"mp-{i}": per_writer for i in range(writers)}


# --- the count boundary: counted once the request left, before anything else (F3, F5) -----------


def test_an_unavailable_transport_counts_nothing(tmp_path):
    client = gh.GitHubClient(
        cache_dir=tmp_path, env={"AGENT_REAL_GH": str(tmp_path / "no-such-gh")}, clock=lambda: NOW, caller="drv"
    )
    result = client.request("GET", "repos/o/r/issues/1", fresh=True)
    assert result.status == 599 and result.error == "github_http_error"
    assert reported(tmp_path) == {}


def test_a_reply_without_an_http_status_counts_nothing(tmp_path):
    fake = tmp_path / "gh-no-reply"
    fake.write_text("#!/bin/sh\necho 'could not reach the network'\nexit 1\n")
    fake.chmod(0o755)
    client = gh.GitHubClient(cache_dir=tmp_path, env={"AGENT_REAL_GH": str(fake)}, clock=lambda: NOW, caller="drv")
    result = client.request("GET", "repos/o/r/issues/1", fresh=True)
    assert result.status == 599
    assert reported(tmp_path) == {}


def test_a_crash_before_the_transport_returns_leaves_no_phantom_count(tmp_path):
    def transport(*args):
        raise RuntimeError("died before sending")

    client = gh.GitHubClient(cache_dir=tmp_path, transport=transport, clock=lambda: NOW, env={}, caller="drv")
    with pytest.raises(RuntimeError):
        client.request("GET", "repos/o/r/issues/1", fresh=True)
    assert reported(tmp_path) == {}


@pytest.mark.parametrize(
    "error",
    [ConnectionRefusedError("refused"), OSError("no route"), ValueError("bad header")],
    ids=["refused", "oserror", "local"],
)
def test_an_in_process_error_before_sending_counts_nothing(tmp_path, error):
    import urllib.error

    def transport(*args):
        raise urllib.error.URLError(error)

    client = gh.GitHubClient(cache_dir=tmp_path, transport=transport, clock=lambda: NOW, env={}, caller="drv")
    with pytest.raises(urllib.error.URLError):
        client.request("GET", "repos/o/r/issues/1", fresh=True)
    assert reported(tmp_path) == {}


@pytest.mark.parametrize(
    "error",
    [subprocess.TimeoutExpired("gh", 30), TimeoutError("read timed out"), ConnectionResetError("reset")],
    ids=["timeout-expired", "socket-timeout", "reset"],
)
def test_an_error_after_sending_still_counts(tmp_path, error):
    def transport(*args):
        raise error

    client = gh.GitHubClient(cache_dir=tmp_path, transport=transport, clock=lambda: NOW, env={}, caller="drv")
    with pytest.raises(type(error)):
        client.request("GET", "repos/o/r/issues/1", fresh=True)
    assert rows(tmp_path) == [(HOUR, "core", "drv", 1)]


@pytest.mark.parametrize("status", [404, 422, 500, 502])
def test_real_http_error_statuses_count(tmp_path, status):
    client, _ = make(tmp_path, caller="drv", answers=lambda n: reply(status=status))
    client.request("GET", "repos/o/r/issues/1", fresh=True)
    assert rows(tmp_path) == [(HOUR, "core", "drv", 1)]


def test_the_too_large_marker_still_counts_because_the_request_was_sent(tmp_path):
    def transport(*args):
        return gh.Response(200, {}, b"x" * 100)

    client = gh.GitHubClient(
        cache_dir=tmp_path, transport=transport, clock=lambda: NOW, env={}, caller="drv", max_response_bytes=10
    )
    assert client.request("GET", "repos/o/r/issues/1", fresh=True).status == 413
    assert rows(tmp_path) == [(HOUR, "core", "drv", 1)]


# A stand-in for gh 2.98 with the behaviour the client relies on, checked against the real binary:
# with debug on (gh's rule: GH_DEBUG not in "", 0, false, no; else DEBUG in true, 1, yes, api) it
# logs "* Request at/to" before each request and "* Request took" after it; an unknown flag fails
# before any request; a name lookup failure logs its "* dial tcp" line; --paginate logs every page.
FAKE_GH = """#!{python}
import os, sys, time
argv, env = sys.argv[1:], os.environ
debug = env["GH_DEBUG"] not in ("", "0", "false", "no") if "GH_DEBUG" in env else env.get("DEBUG") in ("true", "1", "yes", "api")
known = {{"--paginate", "--jq", "--include", "--method", "--input", "--hostname", "--header", "--slurp"}}
for word in argv[1:]:
    if word.startswith("--") and word.split("=")[0] not in known:
        sys.stderr.write("unknown flag: " + word + "\\n\\nUsage:  gh api <endpoint> [flags]\\n")
        raise SystemExit(1)
if debug and env.get("FAKE_GH_GIT"):
    sys.stderr.write("[git remote -v]\\n")
pages = int(env.get("FAKE_GH_PAGES", "1")) if "--paginate" in argv else 1
for page in range(1, pages + 1):
    if debug:
        sys.stderr.write("* Request at 2026-10-15 18:33:52.8 +0000 UTC m=+0.03\\n")
        sys.stderr.write("* Request to https://api.github.com/x?page=%d\\n" % page)
        sys.stderr.flush()
    if env.get("FAKE_GH_FAIL") == "dns":
        if debug:
            sys.stderr.write("* dial tcp: lookup api.github.com: no such host\\n* Request took 1ms\\n")
        sys.stderr.write("error connecting to api.github.com\\ncheck your internet connection or https://githubstatus.com\\n")
        raise SystemExit(1)
    if env.get("FAKE_GH_RECEIPT"):
        with open(env["FAKE_GH_RECEIPT"], "a") as handle:
            handle.write("sent\\n")
    if env.get("FAKE_GH_HANG"):
        time.sleep(60)
    if debug:
        sys.stderr.write("* Request took 1.2ms\\n")
    if "--include" in argv:
        sys.stdout.write("HTTP/2.0 200 OK\\nX-RateLimit-Remaining: 4000\\nX-RateLimit-Reset: 9999999999\\n\\n{{}}\\n")
    else:
        sys.stdout.write("%d\\n" % page)
if env.get("FAKE_GH_WARN"):
    sys.stderr.write("warning: something gh said\\n")
"""


@pytest.fixture
def fake_gh(tmp_path):
    path = tmp_path / "bin" / "gh"
    path.parent.mkdir()
    path.write_text(FAKE_GH.format(python=sys.executable))
    path.chmod(0o755)
    return path


def native_client(tmp_path, fake, **env):
    environment = {"AGENT_REAL_GH": str(fake), "PATH": os.environ.get("PATH", os.defpath), **env}
    return gh.GitHubClient(cache_dir=tmp_path, env=environment, clock=lambda: NOW, caller="drv")


PAGED = ["gh", "api", "--paginate", "--jq", ".[].n", "repos/o/r/issues"]  # --jq keeps it native
GRAPHQL_PAGED = [
    "gh",
    "api",
    "graphql",
    "--paginate",
    "--jq",
    ".data.repository.issues.nodes[].number",
    "-f",
    'query=query($endCursor:String){repository(owner:"o",name:"r"){issues(first:1,after:$endCursor)'
    "{nodes{number}pageInfo{hasNextPage endCursor}}}}",
]


@pytest.mark.parametrize("debug", [None, "0", "false", "", "no"], ids=["unset", "0", "false", "empty", "no"])
def test_native_pagination_counts_every_page_whatever_the_callers_debug_setting(tmp_path, fake_gh, debug):
    # Review round 2 (F4): a caller's own GH_DEBUG=0 silenced the request log and counted one page.
    env = {"FAKE_GH_PAGES": "3", **({} if debug is None else {"GH_DEBUG": debug})}
    proc = gh._run_command(PAGED, client=native_client(tmp_path, fake_gh, **env), capture_output=True)
    assert proc.returncode == 0 and proc.stdout == b"1\n2\n3\n"
    assert proc.stderr == b""  # the log the client asked for is not handed back
    assert reported(tmp_path) == {"drv": 3}


def test_native_graphql_pagination_counts_every_page(tmp_path, fake_gh):
    client = native_client(tmp_path, fake_gh, FAKE_GH_PAGES="3", GH_DEBUG="0")
    proc = gh._run_command(GRAPHQL_PAGED, client=client, capture_output=True)
    assert proc.returncode == 0 and proc.stdout == b"1\n2\n3\n"
    assert reported(tmp_path, "graphql") == {"drv": 3}


@pytest.mark.parametrize("debug", ["1", "api"])
def test_a_callers_own_request_log_is_counted_and_left_in_place(tmp_path, fake_gh, debug):
    client = native_client(tmp_path, fake_gh, FAKE_GH_PAGES="2", GH_DEBUG=debug)
    proc = gh._run_command(PAGED, client=client, capture_output=True, text=True)
    assert proc.stderr.count("* Request to ") == 2
    assert reported(tmp_path) == {"drv": 2}


def test_the_stripped_stderr_keeps_what_gh_itself_said(tmp_path, fake_gh):
    client = native_client(tmp_path, fake_gh, FAKE_GH_PAGES="2", FAKE_GH_WARN="1", FAKE_GH_GIT="1")
    proc = gh._run_command(PAGED, client=client, capture_output=True, text=True)
    assert proc.stderr == "warning: something gh said\n"
    assert reported(tmp_path) == {"drv": 2}


def test_an_unpaginated_native_command_counts_the_request_it_made(tmp_path, fake_gh):
    proc = gh._run_command(
        ["gh", "api", "--jq", ".x", "--slurp", "repos/o/r/issues"],
        client=native_client(tmp_path, fake_gh),
        capture_output=True,
    )
    assert proc.returncode == 0
    assert reported(tmp_path) == {"drv": 1}


def test_a_native_command_gh_rejected_before_any_request_counts_nothing(tmp_path, fake_gh):
    # Review round 2 (F5): an unknown flag fails before networking but was counted as one request.
    client = native_client(tmp_path, fake_gh)
    proc = gh._run_command(["gh", "api", "--not-a-real-flag", "repos/o/r/issues"], client=client, capture_output=True)
    assert proc.returncode == 1 and b"unknown flag" in proc.stderr
    assert reported(tmp_path) == {}


def test_a_name_lookup_failure_before_connecting_counts_nothing(tmp_path, fake_gh):
    proc = gh._run_command(PAGED, client=native_client(tmp_path, fake_gh, FAKE_GH_FAIL="dns"), capture_output=True)
    assert proc.returncode == 1 and proc.stderr.startswith(b"error connecting to")
    assert reported(tmp_path) == {}
    single = native_client(tmp_path, fake_gh, FAKE_GH_FAIL="dns")
    assert single.request("GET", "repos/o/r/issues/1", fresh=True).status == 599
    assert reported(tmp_path) == {}


def test_a_native_request_cut_off_by_its_timeout_still_counts(tmp_path, fake_gh):
    client = native_client(tmp_path, fake_gh, FAKE_GH_HANG="1")
    with pytest.raises(subprocess.TimeoutExpired):
        gh._run_command(PAGED, client=client, capture_output=True, timeout=2)
    assert reported(tmp_path) == {"drv": 1}


def injected(stderr, returncode=0, stdout=b"1\n"):
    def runner(command, **kwargs):
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)

    return runner


@pytest.mark.parametrize(
    ("stderr", "returncode", "expected"),
    [
        (b"", 0, {"drv": 1}),
        (b"unknown flag: --x\n", 1, {}),
        (b"gh: Not Found (HTTP 404)\n", 1, {"drv": 1}),
        (b"* Request at t\n* Request to u\n* Request took 1ms\n" * 2, 0, {"drv": 2}),
    ],
    ids=["success", "rejected", "http-error", "logged"],
)
def test_an_injected_runner_without_a_log_is_judged_by_its_result(tmp_path, stderr, returncode, expected):
    client, _ = make(tmp_path, caller="drv")
    gh._run_command(PAGED, client=client, runner=injected(stderr, returncode), capture_output=True)
    assert reported(tmp_path) == expected


def test_an_injected_runner_gets_the_callers_environment_unchanged(tmp_path):
    seen = []

    def runner(command, **kwargs):
        seen.append(kwargs["env"].get("GH_DEBUG"))
        return subprocess.CompletedProcess(command, 0, b"1\n", b"")

    client, _ = make(tmp_path, caller="drv")
    gh._run_command(PAGED, client=client, runner=runner, capture_output=True)
    assert seen == [None]


def gh_home(tmp_path):
    """Keep the installed gh's config and state (its device id) inside the test's directory."""
    home = tmp_path / "gh-home"
    return {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / "config"),
        "XDG_STATE_HOME": str(home / "state"),
        "XDG_CACHE_HOME": str(home / "cache"),
        "XDG_DATA_HOME": str(home / "data"),
        "GH_CONFIG_DIR": str(home / "gh-config"),
    }


def real_gh_binary():
    """The installed gh (not the repository shim), or ``None``."""
    from scripts.opsec.prepublish import PublishBlocked, real_gh

    try:
        return real_gh(dict(os.environ))
    except PublishBlocked:
        return None


# live_github: the installed gh runs, but it fails its flag parsing before any request.
@pytest.mark.live_github
@pytest.mark.skipif(real_gh_binary() is None, reason="needs the installed gh executable")
def test_the_real_gh_rejecting_an_unknown_flag_counts_nothing(tmp_path):
    client = gh.GitHubClient(
        cache_dir=tmp_path,
        env={
            "AGENT_REAL_GH": real_gh_binary(),
            **gh_home(tmp_path),
            "GH_TOKEN": "fixture-not-a-token",
            "PATH": os.defpath,
        },
        clock=lambda: NOW,
        caller="drv",
    )
    proc = gh._run_command(["gh", "api", "--not-a-real-flag", "repos/o/r/issues"], client=client, capture_output=True)
    assert proc.returncode == 1 and b"unknown flag" in proc.stderr
    assert reported(tmp_path) == {}


PAGE_SERVER = """
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

class Pages(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_GET(self):
        with open(sys.argv[1], "a") as handle:
            handle.write("request\\n")
        parts = urlsplit(self.path)
        page = int(parse_qs(parts.query).get("page", ["1"])[0])
        body = json.dumps([{"n": page}]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if page < 3:
            self.send_header("Link", '<http://api.github.localhost%s?page=%d>; rel="next"' % (parts.path, page + 1))
        self.end_headers()
        self.wfile.write(body)

server = ThreadingHTTPServer(("localhost", 0), Pages)
print(server.server_address[1], flush=True)
server.serve_forever()
"""


# live_github: the installed gh runs, against a loopback proxy only; GitHub is never contacted.
@pytest.mark.live_github
@pytest.mark.skipif(real_gh_binary() is None, reason="needs the installed gh executable")
def test_the_real_gh_paginating_three_pages_counts_three_with_debug_off(tmp_path):
    # gh speaks plain HTTP to github.localhost, so a loopback proxy can serve real pages.
    seen = tmp_path / "server-requests"
    server = subprocess.Popen([sys.executable, "-c", PAGE_SERVER, str(seen)], stdout=subprocess.PIPE, text=True)
    try:
        port = int(server.stdout.readline())
        proxy = f"http://localhost:{port}"
        client = gh.GitHubClient(
            cache_dir=tmp_path,
            env={
                "AGENT_REAL_GH": real_gh_binary(),
                **gh_home(tmp_path),
                "GH_HOST": "github.localhost",
                "GH_ENTERPRISE_TOKEN": "fixture-not-a-token",
                "GH_TOKEN": "fixture-not-a-token",
                "GH_DEBUG": "0",
                "HTTP_PROXY": proxy,
                "http_proxy": proxy,
                "NO_PROXY": "",
                "no_proxy": "",
                "PATH": os.defpath,
            },
            clock=lambda: NOW,
            caller="drv",
        )
        proc = gh._run_command(PAGED, client=client, capture_output=True, text=True)
    finally:
        server.send_signal(signal.SIGTERM)
        server.wait(timeout=10)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "1\n2\n3\n" and proc.stderr == ""
    assert seen.read_text().splitlines() == ["request"] * 3
    assert reported(tmp_path) == {"drv": 3}


# --- a crash right after the request left keeps its count (review round 2: F3) ------------------

CRASH_CHILD = """
import os, sys, time
from scripts.common import github_client as gh

cache_dir, mode, receipt, fake = sys.argv[1:5]
now = int(sys.argv[5])


def transport(*args):
    with open(receipt, "a") as handle:
        handle.write("sent\\n")
    return gh.Response(200, {"X-RateLimit-Remaining": "4000", "X-RateLimit-Reset": "9999999999"}, b"{}")


if mode == "in-process":
    client = gh.GitHubClient(cache_dir=cache_dir, transport=transport, clock=lambda: now, env={}, caller="crash")
else:
    environment = {"AGENT_REAL_GH": fake, "FAKE_GH_RECEIPT": receipt, "PATH": os.environ.get("PATH", os.defpath)}
    client = gh.GitHubClient(cache_dir=cache_dir, clock=lambda: now, env=environment, caller="crash")


def cut(frame, event, arg):
    # The first statement of the request after its transport handed the response back.
    if event == "line" and frame.f_code.co_name in ("request", "_request") and "response" in frame.f_locals:
        print("after-send", flush=True)
        time.sleep(120)
    return cut


sys.settrace(cut)
client.request("GET", "repos/o/r/issues/1", fresh=True)
print("not-cut", flush=True)
"""


@pytest.mark.parametrize("mode", ["in-process", "gh-process"])
def test_a_process_killed_right_after_its_request_left_keeps_the_count(tmp_path, fake_gh, mode):
    receipt = tmp_path / "transport-receipt"
    child = subprocess.Popen(
        [sys.executable, "-c", CRASH_CHILD, str(tmp_path), mode, str(receipt), str(fake_gh), str(NOW)],
        stdout=subprocess.PIPE,
        text=True,
        cwd=REPO_ROOT,
    )
    try:
        assert child.stdout.readline().strip() == "after-send"
        child.send_signal(signal.SIGKILL)
        assert child.wait(timeout=30) == -signal.SIGKILL
    finally:
        if child.poll() is None:
            child.kill()
    assert receipt.read_text().splitlines() == ["sent"]
    assert reported(tmp_path) == {"crash": 1}


def test_gh_log_parser_counts_only_requests_that_left():
    log = (
        b"[git remote -v]\n"
        b"* Request at a\n* Request to u1\n* Request took 1ms\n"
        b"* Request at b\n* Request to u2\n* dial tcp: lookup x: no such host\n* Request took 1ms\n"
        b"* Request at c\n* Request to u3\n* proxyconnect tcp: dial tcp proxy.invalid:9: connect: connection refused\n"
        b"* Request took 1ms\n"
        b"* Request at d\n* Request to u4\n* tls: first record does not look like a TLS handshake\n* Request took 1ms\n"
        b"* Request at e\n* Request to u5\n* context deadline exceeded\n* Request took 30s\n"
        b"gh: something\n"
        b"* Request at f\n* Request to u6\n"
    )
    logged, left, cleaned = gh._gh_request_log(log, strip=True)
    assert (logged, left) == (6, 3)  # u1, u5 (failed after sending) and u6 (cut off in flight)
    assert cleaned == b"gh: something\n"
    assert gh._gh_request_log(log.decode(), strip=False)[2] == log.decode()
