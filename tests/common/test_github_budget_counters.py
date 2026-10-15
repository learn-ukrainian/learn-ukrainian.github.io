"""Per-caller hourly request counters in the shared GitHub client database (#10730, #10660). No network."""

from __future__ import annotations

import json
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


def rows(tmp_path):
    db = sqlite3.connect(tmp_path / "cache.sqlite3")
    try:
        return db.execute("SELECT hour,resource,caller,count FROM caller_counter ORDER BY hour,resource,caller").fetchall()
    finally:
        db.close()


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
    monkeypatch.setitem(sys.modules, "__main__", SimpleNamespace(__spec__=SimpleNamespace(name="scripts.publish.__main__")))
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


def test_concurrent_threads_do_not_lose_or_corrupt_counts(tmp_path):
    threads, per_thread = 8, 25
    errors = []

    def work(index):
        client, _ = make(tmp_path, caller=f"worker-{index % 2}")
        try:
            for _ in range(per_thread):
                client.request("GET", "repos/o/r/issues/1", fresh=True)
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
    db = sqlite3.connect(tmp_path / "cache.sqlite3")
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
    db = sqlite3.connect(tmp_path / "cache.sqlite3")
    db.execute(counters.SCHEMA)
    for hour in (HOUR - week - 7200, HOUR - week - 3600, HOUR - week + 3600, HOUR - 3600):
        db.execute("INSERT INTO caller_counter(hour,resource,caller,count) VALUES(?,?,?,9)", (hour, "core", "old"))
    db.commit()
    db.close()
    client, _ = make(tmp_path, caller="drv")
    client.request("GET", "repos/o/r/issues/1")
    kept = [r[0] for r in rows(tmp_path)]
    assert kept == [HOUR - week + 3600, HOUR - 3600, HOUR]


def test_retention_boundary_is_exactly_seven_days(tmp_path):
    week = 7 * 24 * 3600
    db = sqlite3.connect(tmp_path / "cache.sqlite3")
    db.execute(counters.SCHEMA)
    for hour in (HOUR - week - 3600, HOUR - week):
        db.execute("INSERT INTO caller_counter(hour,resource,caller,count) VALUES(?,?,?,1)", (hour, "core", "old"))
    db.commit()
    db.close()
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
    db = sqlite3.connect(tmp_path / "cache.sqlite3")
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
    db = sqlite3.connect(tmp_path / "cache.sqlite3")
    assert db.execute("SELECT count,last_remaining,last_reset FROM caller_counter").fetchone() == (2, 3998, NOW + 99)
    db.close()


def test_report_orders_callers_by_count_then_name(tmp_path):
    db = sqlite3.connect(tmp_path / "cache.sqlite3")
    db.execute(counters.SCHEMA)
    for caller, count in (("b", 5), ("a", 5), ("z", 9), ("c", 1)):
        db.execute("INSERT INTO caller_counter(hour,resource,caller,count) VALUES(?,?,?,?)", (HOUR, "core", caller, count))
    db.execute("INSERT INTO caller_counter(hour,resource,caller,count) VALUES(?,?,?,?)", (HOUR - 3600, "search", "old", 2))
    db.commit()
    db.close()
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
    sqlite3.connect(tmp_path / "cache.sqlite3").close()
    assert counters.report_for(tmp_path, NOW)["windows"]["previous"]["resources"]["core"] == []
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


def test_a_storage_error_never_blocks_a_request(tmp_path, monkeypatch):
    def broken(*args, **kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(counters, "_record", broken)
    client, calls = make(tmp_path, caller="drv")
    assert client.request("GET", "repos/o/r/issues/1").status == 200
    assert len(calls) == 1
