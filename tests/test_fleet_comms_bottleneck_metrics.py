"""Per-stream fleet bottlenecks use metadata-only lifecycle timestamps."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.fleet_comms.efficiency_metrics import collect_stream_bottleneck_metrics

NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)


def _write_task(
    tasks_dir: Path,
    name: str,
    *,
    started: datetime,
    finished: datetime | None,
    stream_epic: int | None = 4707,
    task_family: str | None = "fleet-comms-metrics",
    hard_timeout: int | None = None,
) -> None:
    record: dict[str, object] = {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat() if finished else None,
    }
    if stream_epic is not None:
        record["stream_epic"] = stream_epic
    if task_family is not None:
        record["task_family"] = task_family
    if hard_timeout is not None:
        record["hard_timeout"] = hard_timeout
    (tasks_dir / f"{name}.json").write_text(json.dumps(record), encoding="utf-8")


def _plane_db(path: Path, *, with_identity: bool = True) -> None:
    identity_columns = ", stream_epic INTEGER, task_family TEXT" if with_identity else ""
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE formal_review_jobs (
          review_id TEXT PRIMARY KEY,
          repository TEXT NOT NULL,
          pr_number INTEGER NOT NULL,
          created_at TEXT NOT NULL
        """
        + identity_columns
        + """
        );
        CREATE TABLE github_publications (
          publication_id TEXT PRIMARY KEY,
          review_id TEXT NOT NULL,
          published_at TEXT NOT NULL
        );
        """
    )
    columns = "review_id, repository, pr_number, created_at"
    values: tuple[object, ...] = (
        "review-1",
        "learn-ukrainian/learn-ukrainian.github.io",
        5644,
        "2026-07-22T11:58:00+00:00",
    )
    if with_identity:
        columns += ", stream_epic, task_family"
        values += (4707, "fleet-comms-metrics")
    placeholders = ", ".join("?" for _ in values)
    conn.execute(f"INSERT INTO formal_review_jobs ({columns}) VALUES ({placeholders})", values)
    conn.execute(
        "INSERT INTO github_publications VALUES (?, ?, ?)",
        ("pub-1", "review-1", "2026-07-22T11:59:00+00:00"),
    )
    conn.commit()
    conn.close()


def _merged_at(*, repo: str, pr_number: int) -> tuple[datetime | None, str | None]:
    assert repo == "learn-ukrainian/learn-ukrainian.github.io"
    assert pr_number == 5644
    return datetime(2026, 7, 22, 12, 0, tzinfo=UTC), None


def test_percentiles_omitted_below_twenty_samples(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for seconds in range(1, 20):
        _write_task(
            tasks_dir,
            f"task-{seconds}",
            started=NOW - timedelta(seconds=seconds),
            finished=NOW,
        )
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    duration = payload["by_stream_epic"]["4707"]["dispatch"]["duration_s"]
    assert payload["by_stream_epic"]["4707"]["dispatch"]["n"] == 19
    assert "p50" not in duration
    assert "p95" not in duration


def test_percentiles_are_deterministic_at_twenty_samples(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    for seconds in range(1, 21):
        _write_task(
            tasks_dir,
            f"task-{seconds}",
            started=NOW - timedelta(seconds=seconds),
            finished=NOW,
        )
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    duration = payload["by_task_family"]["fleet-comms-metrics"]["dispatch"]["duration_s"]
    assert duration["p50"] == 10.5
    assert duration["p95"] == 19.05


def test_injected_clock_reports_exact_unfinished_backlog_age(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task(
        tasks_dir,
        "running",
        started=NOW - timedelta(seconds=123),
        finished=None,
        hard_timeout=8_000,
    )
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    span = payload["by_stream_epic"]["4707"]["dispatch"]
    assert span["backlog_age_s"] == 123.0
    assert span["raw"]["unfinished_count"] == 1
    assert payload["threshold_seconds"]["dispatch"] == 8_000


def test_missing_lifecycle_identity_is_unclassified(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task(
        tasks_dir,
        "unclassified",
        started=NOW - timedelta(seconds=10),
        finished=NOW,
        stream_epic=None,
        task_family=None,
    )
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    assert payload["unclassified"]["by_stream_epic"]["dispatch"]["n"] == 1
    assert payload["unclassified"]["by_task_family"]["formal_cf_publication"]["n"] == 1


def test_broken_source_is_visible_while_other_source_reports(tmp_path: Path) -> None:
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tmp_path / "missing-tasks", plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    assert payload["source_errors"]
    assert payload["source_errors"][0]["source"] == "dispatch"
    assert payload["by_stream_epic"]["4707"]["formal_cf_publication"]["n"] == 1


def test_payload_never_contains_task_prompt_or_message_body(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task(tasks_dir, "task", started=NOW - timedelta(seconds=10), finished=NOW)
    task = tasks_dir / "task.json"
    record = json.loads(task.read_text(encoding="utf-8"))
    record["prompt"] = "PRIVATE PROMPT TEXT"
    record["body"] = "PRIVATE MESSAGE BODY"
    task.write_text(json.dumps(record), encoding="utf-8")
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )
    serialized = json.dumps(payload).lower()

    assert payload["content_included"] is False
    assert "private prompt" not in serialized
    assert "private message" not in serialized
    assert '"prompt"' not in serialized
    assert '"body"' not in serialized
