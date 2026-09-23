"""Immutable PR merge facts are cached and looked up in GraphQL batches."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path

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


def _query_from(args: list[str]) -> str:
    for arg in args:
        if arg.startswith("query="):
            return arg.removeprefix("query=")
    raise AssertionError(f"graphql query missing from {args}")


def _pull_aliases(query: str) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    marks = list(
        re.finditer(r'r\d+: repository\(owner: "([^"]+)", name: "([^"]+)"\) \{', query)
    )
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(query)
        body = query[mark.end() : end]
        repo = f"{mark.group(1)}/{mark.group(2)}"
        for number in re.findall(r"pullRequest\(number: (\d+)\)", body):
            found.append((repo, int(number)))
    return found


def _runner(calls: list[list[str]], answers: dict[tuple[str, int], str | None]):
    def runner(args: list[str], timeout: float = 30) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        query = _query_from(args)
        data: dict[str, dict[str, dict[str, str | None]]] = {}
        marks = list(
            re.finditer(r'r(\d+): repository\(owner: "([^"]+)", name: "([^"]+)"\) \{', query)
        )
        for index, mark in enumerate(marks):
            end = marks[index + 1].start() if index + 1 < len(marks) else len(query)
            body = query[mark.end() : end]
            repo = f"{mark.group(2)}/{mark.group(3)}"
            node: dict[str, dict[str, str | None]] = {}
            for number_s in re.findall(r"p(\d+): pullRequest", body):
                raw = answers[(repo, int(number_s))]
                node[f"p{number_s}"] = {"mergedAt": raw}
            data[f"r{mark.group(1)}"] = node
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps({"data": data}), stderr="")

    return runner


def _collect(tmp_path: Path, numbers: list[int], runner, *, repo: str = REPO):
    tasks = tmp_path / "tasks"
    tasks.mkdir(exist_ok=True)
    plane = tmp_path / "plane.sqlite3"
    if not plane.exists():
        _plane(plane, numbers, repo=repo)
    cache = tmp_path / "pr-merge-facts.json"
    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        gh_runner=runner,
        merge_cache_path=cache,
    )
    return payload, cache


def test_warm_cache_issues_zero_gh_calls(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    answers = {(REPO, number): MERGED for number in (10, 11, 12)}
    runner = _runner(calls, answers)

    first, cache = _collect(tmp_path, [10, 11, 12], runner)
    assert len(calls) == 1
    assert calls[0][:3] == ["gh", "api", "graphql"]
    assert len(_pull_aliases(_query_from(calls[0]))) == 3
    assert first["by_stream_epic"]["4707"]["gate_to_merge"]["n"] == 3
    stored = json.loads(cache.read_text(encoding="utf-8"))
    assert stored["facts"][f"{REPO}#10"] == MERGED

    calls.clear()
    second, _cache = _collect(tmp_path, [10, 11, 12], runner)
    assert calls == []
    assert second["by_stream_epic"]["4707"]["gate_to_merge"]["n"] == 3


def test_misses_batch_into_one_call_per_fifty_pull_requests(tmp_path: Path) -> None:
    numbers = list(range(1, 52))
    calls: list[list[str]] = []
    answers = {(REPO, number): MERGED for number in numbers}
    payload, _cache = _collect(tmp_path, numbers, _runner(calls, answers))

    assert len(calls) == 2
    batches = [_pull_aliases(_query_from(call)) for call in calls]
    assert [len(batch) for batch in batches] == [50, 1]
    assert {number for _repo, number in batches[0] + batches[1]} == set(numbers)
    assert payload["by_stream_epic"]["4707"]["gate_to_merge"]["n"] == 51
    assert payload["source_errors"] == []


def test_two_repositories_share_one_graphql_call(tmp_path: Path) -> None:
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

    collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        gh_runner=_runner(calls, answers),
        merge_cache_path=tmp_path / "cache.json",
    )

    assert len(calls) == 1
    assert _pull_aliases(_query_from(calls[0])) == [("acme/widgets", 1), ("acme/other", 2)]


def test_null_merged_at_is_not_cached(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    answers = {(REPO, 7): MERGED, (REPO, 8): None}
    runner = _runner(calls, answers)

    first, cache = _collect(tmp_path, [7, 8], runner)
    assert len(calls) == 1
    facts = json.loads(cache.read_text(encoding="utf-8"))["facts"]
    assert f"{REPO}#7" in facts
    assert f"{REPO}#8" not in facts
    assert first["by_stream_epic"]["4707"]["gate_to_merge"]["raw"]["unfinished_count"] == 1

    calls.clear()
    _collect(tmp_path, [7, 8], runner)
    assert len(calls) == 1
    assert _pull_aliases(_query_from(calls[0])) == [(REPO, 8)]


def test_corrupt_cache_is_empty_and_does_not_crash(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    answers = {(REPO, 3): MERGED}
    cache = tmp_path / "pr-merge-facts.json"
    cache.write_text("{not json", encoding="utf-8")
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    plane = tmp_path / "plane.sqlite3"
    _plane(plane, [3])

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        gh_runner=_runner(calls, answers),
        merge_cache_path=cache,
    )

    assert len(calls) == 1
    assert payload["by_stream_epic"]["4707"]["gate_to_merge"]["n"] == 1
    assert payload["source_errors"] == []
    reloaded = json.loads(cache.read_text(encoding="utf-8"))
    assert reloaded["facts"][f"{REPO}#3"] == MERGED


def test_failed_fetch_is_fail_open(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(args: list[str], timeout: float = 30) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        raise subprocess.TimeoutExpired(args, timeout)

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    plane = tmp_path / "plane.sqlite3"
    _plane(plane, [4])
    cache = tmp_path / "cache.json"

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks,
        plane_db=plane,
        now=NOW,
        gh_runner=runner,
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
