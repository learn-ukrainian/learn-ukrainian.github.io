"""Immutable PR merge facts use the production REST path and durable cache."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from scripts.common.github_client import Response
from scripts.fleet_comms.efficiency_metrics import collect_stream_bottleneck_metrics

NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)
REPO = "acme/widgets"
MERGED = "2026-07-22T12:00:00Z"


def _plane(path: Path, numbers: list[int], *, repo: str = REPO) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE formal_review_jobs (
          review_id TEXT PRIMARY KEY,
          repository TEXT NOT NULL,
          pr_number INTEGER NOT NULL,
          created_at TEXT NOT NULL,
          stream_epic INTEGER,
          task_family TEXT
        );
        CREATE TABLE github_publications (
          publication_id TEXT PRIMARY KEY,
          review_id TEXT NOT NULL,
          published_at TEXT NOT NULL,
          status_context TEXT
        );
        """
    )
    for number in numbers:
        review_id = f"review-{repo}-{number}"
        conn.execute(
            "INSERT INTO formal_review_jobs VALUES (?, ?, ?, ?, ?, ?)",
            (review_id, repo, number, "2026-07-22T11:58:00+00:00", 4707, "fleet-comms-metrics"),
        )
        conn.execute(
            "INSERT INTO github_publications VALUES (?, ?, ?, ?)",
            (f"pub-{repo}-{number}", review_id, "2026-07-22T11:59:00+00:00", "fleet/cross-family-review"),
        )
    conn.commit()
    conn.close()


def _key(endpoint):
    match = re.fullmatch(r"repos/(.+)/pulls/(\d+)", endpoint)
    assert match, endpoint
    return match[1], int(match[2])


def _runner(calls, answers):
    def transport(method, endpoint, headers, body, timeout):
        assert method == "GET" and body is None
        assert timeout == 30
        calls.append(endpoint)
        return Response(200, {}, json.dumps({"merged_at": answers[_key(endpoint)]}).encode())

    return transport


def _collect(tmp_path: Path, numbers: list[int], runner, github_transport, *, repo: str = REPO):
    tasks = tmp_path / "tasks"
    tasks.mkdir(exist_ok=True)
    plane = tmp_path / "plane.sqlite3"
    if not plane.exists():
        _plane(plane, numbers, repo=repo)
    cache = tmp_path / "pr-merge-facts.json"
    github_transport(runner)
    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        merge_cache_path=cache,
    )
    return payload, cache


def test_warm_cache_issues_zero_gh_calls(tmp_path: Path, github_transport) -> None:
    calls: list[list[str]] = []
    answers = {(REPO, number): MERGED for number in (10, 11, 12)}
    runner = _runner(calls, answers)

    first, cache = _collect(tmp_path, [10, 11, 12], runner, github_transport)
    assert calls == [f"repos/{REPO}/pulls/{n}" for n in (10, 11, 12)]
    assert first["by_stream_epic"]["4707"]["gate_to_merge"]["n"] == 3
    stored = json.loads(cache.read_text(encoding="utf-8"))
    assert stored["facts"][f"{REPO}#10"] == MERGED

    calls.clear()
    second, _cache = _collect(tmp_path, [10, 11, 12], runner, github_transport)
    assert calls == []
    assert second["by_stream_epic"]["4707"]["gate_to_merge"]["n"] == 3


def test_misses_read_each_pull_request_once_across_batch_boundary(tmp_path: Path, github_transport) -> None:
    numbers = list(range(1, 52))
    calls: list[list[str]] = []
    answers = {(REPO, number): MERGED for number in numbers}
    payload, _cache = _collect(tmp_path, numbers, _runner(calls, answers), github_transport)

    assert len(calls) == 51
    assert [_key(endpoint) for endpoint in calls] == [(REPO, n) for n in numbers]
    assert payload["by_stream_epic"]["4707"]["gate_to_merge"]["n"] == 51
    assert payload["source_errors"] == []


def test_two_repositories_use_their_qualified_rest_endpoints(tmp_path: Path, github_transport) -> None:
    calls: list[list[str]] = []
    answers = {("acme/widgets", 1): MERGED, ("acme/other", 2): MERGED}
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    plane = tmp_path / "plane.sqlite3"
    conn = sqlite3.connect(plane)
    conn.executescript(
        """
        CREATE TABLE formal_review_jobs (
          review_id TEXT PRIMARY KEY,
          repository TEXT NOT NULL,
          pr_number INTEGER NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE github_publications (
          publication_id TEXT PRIMARY KEY,
          review_id TEXT NOT NULL,
          published_at TEXT NOT NULL
        );
        """
    )
    conn.execute(
        "INSERT INTO formal_review_jobs VALUES ('a', 'acme/widgets', 1, '2026-07-22T11:58:00+00:00')"
    )
    conn.execute(
        "INSERT INTO formal_review_jobs VALUES ('b', 'acme/other', 2, '2026-07-22T11:58:00+00:00')"
    )
    conn.execute("INSERT INTO github_publications VALUES ('pa', 'a', '2026-07-22T11:59:00+00:00')")
    conn.execute("INSERT INTO github_publications VALUES ('pb', 'b', '2026-07-22T11:59:00+00:00')")
    conn.commit()
    conn.close()

    github_transport(_runner(calls, answers))
    collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        merge_cache_path=tmp_path / "cache.json",
    )

    assert [_key(endpoint) for endpoint in calls] == [("acme/widgets", 1), ("acme/other", 2)]


def test_null_merged_at_is_not_cached(tmp_path: Path, github_transport) -> None:
    calls: list[list[str]] = []
    answers = {(REPO, 7): MERGED, (REPO, 8): None}
    runner = _runner(calls, answers)

    first, cache = _collect(tmp_path, [7, 8], runner, github_transport)
    assert len(calls) == 2
    facts = json.loads(cache.read_text(encoding="utf-8"))["facts"]
    assert f"{REPO}#7" in facts
    assert f"{REPO}#8" not in facts
    assert first["by_stream_epic"]["4707"]["gate_to_merge"]["raw"]["unfinished_count"] == 1

    calls.clear()
    _collect(tmp_path, [7, 8], runner, github_transport)
    assert len(calls) == 1
    assert [_key(endpoint) for endpoint in calls] == [(REPO, 8)]


def test_corrupt_cache_is_empty_and_does_not_crash(tmp_path: Path, github_transport) -> None:
    calls: list[list[str]] = []
    answers = {(REPO, 3): MERGED}
    cache = tmp_path / "pr-merge-facts.json"
    cache.write_text("{not json", encoding="utf-8")
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    plane = tmp_path / "plane.sqlite3"
    _plane(plane, [3])
    github_transport(_runner(calls, answers))

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        merge_cache_path=cache,
    )

    assert len(calls) == 1
    assert payload["by_stream_epic"]["4707"]["gate_to_merge"]["n"] == 1
    assert payload["source_errors"] == []
    reloaded = json.loads(cache.read_text(encoding="utf-8"))
    assert reloaded["facts"][f"{REPO}#3"] == MERGED


def test_failed_fetch_is_fail_open(tmp_path: Path, github_transport) -> None:
    calls: list[list[str]] = []

    def runner(method, endpoint, headers, body, timeout):
        calls.append(endpoint)
        raise subprocess.TimeoutExpired(endpoint, timeout)

    github_transport(runner)

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    plane = tmp_path / "plane.sqlite3"
    _plane(plane, [4])
    cache = tmp_path / "cache.json"

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        merge_cache_path=cache,
    )

    assert len(calls) == 1
    assert payload["source_errors"] == [{
        "source": "github",
        "error_kind": "pr_lookup_failed",
        "pr_number": 4,
        "store": {"kind": "comms-plane", "reachable": True},
    }]
    assert not cache.exists()


def test_partial_rest_failure_caches_successful_pull_requests(tmp_path: Path, github_transport) -> None:
    """A failed REST lookup preserves successful merge facts in the batch."""
    calls = []

    def transport(method, endpoint, headers, body, timeout):
        calls.append(endpoint)
        repo, number = _key(endpoint)
        assert repo == REPO and method == "GET"
        if number == 12:
            return Response(404, {}, b'{"message":"Not Found"}')
        return Response(200, {}, json.dumps({"merged_at": None if number == 11 else MERGED}).encode())

    first, cache = _collect(tmp_path, [10, 11, 12], transport, github_transport)
    facts = json.loads(cache.read_text(encoding="utf-8"))["facts"]
    assert facts == {f"{REPO}#10": MERGED}
    assert all(value is not None for value in facts.values())
    gate = first["by_stream_epic"]["4707"]["gate_to_merge"]
    assert gate["n"] == 1
    assert gate["raw"]["unfinished_count"] == 1
    assert first["source_errors"] == [{
        "source": "github",
        "error_kind": "pr_lookup_failed",
        "pr_number": 12,
        "store": {"kind": "comms-plane", "reachable": True},
    }]

    calls.clear()
    _collect(tmp_path, [10, 11, 12], transport, github_transport)
    assert len(calls) == 2
    assert {_key(endpoint) for endpoint in calls} == {(REPO, 11), (REPO, 12)}


def test_unparseable_rest_body_fails_each_lookup(tmp_path: Path, github_transport) -> None:
    calls: list[list[str]] = []

    def runner(method, endpoint, headers, body, timeout):
        calls.append(endpoint)
        return Response(200, {}, b"not-json")

    github_transport(runner)

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    plane = tmp_path / "plane.sqlite3"
    _plane(plane, [4, 5])
    cache = tmp_path / "cache.json"

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        merge_cache_path=cache,
    )

    assert len(calls) == 2
    assert {item["pr_number"] for item in payload["source_errors"]} == {4, 5}
    assert {item["error_kind"] for item in payload["source_errors"]} == {"pr_lookup_failed"}
    assert not cache.exists()


def test_rest_payload_without_merge_fact_fails_each_lookup(tmp_path: Path, github_transport) -> None:
    calls: list[list[str]] = []

    def runner(method, endpoint, headers, body, timeout):
        calls.append(endpoint)
        return Response(200, {}, b'{"message":"Something went wrong"}')

    github_transport(runner)

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    plane = tmp_path / "plane.sqlite3"
    _plane(plane, [6, 7])
    cache = tmp_path / "cache.json"

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        merge_cache_path=cache,
    )

    assert len(calls) == 2
    assert {item["pr_number"] for item in payload["source_errors"]} == {6, 7}
    assert not cache.exists()
