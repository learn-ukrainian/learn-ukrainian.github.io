"""Per-stream fleet bottlenecks use metadata-only lifecycle timestamps."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.fleet_comms import efficiency_metrics
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
    top_level_identity: bool = False,
) -> None:
    """Write a task record; identity uses the real ``task-lifecycle-carrier.v1`` shape.

    ``top_level_identity`` writes the legacy top-level keys instead, which no
    current producer emits but older records may carry.
    """
    record: dict[str, object] = {
        "task_id": name,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat() if finished else None,
    }
    identity: dict[str, object] = {}
    if stream_epic is not None:
        identity["stream_epic"] = stream_epic
    if task_family is not None:
        identity["task_family"] = task_family
    if top_level_identity:
        record.update(identity)
    elif identity:
        record["task_lifecycle"] = {
            "schema_version": "task-lifecycle-carrier.v1",
            "identity": identity,
        }
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
    error = payload["source_errors"][0]
    assert error["source"] == "dispatch"
    assert error["error_kind"] == "tasks_dir_missing"
    assert error["store"] == {"kind": "batch-tasks", "reachable": False}
    assert "error" not in error
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


def test_dispatch_history_includes_archived_records(tmp_path: Path) -> None:
    """#8625: archiving old terminal records must not shrink all-history metrics."""
    tasks_dir = tmp_path / "tasks"
    archive = tasks_dir / "archive"
    archive.mkdir(parents=True)
    for seconds in range(1, 21):
        _write_task(
            archive if seconds % 2 else tasks_dir,
            f"task-{seconds}",
            started=NOW - timedelta(seconds=seconds),
            finished=NOW,
            hard_timeout=seconds * 60,
        )
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    dispatch = payload["by_stream_epic"]["4707"]["dispatch"]
    assert dispatch["n"] == 20
    assert "p50" in dispatch["duration_s"]


def test_carrier_identity_groups_dispatch_without_top_level_fields(tmp_path: Path) -> None:
    """#11099: producers nest identity under task_lifecycle.identity only."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task(
        tasks_dir,
        "carrier",
        started=NOW - timedelta(seconds=10),
        finished=NOW,
        stream_epic=6943,
        task_family="infra",
    )
    record = json.loads((tasks_dir / "carrier.json").read_text(encoding="utf-8"))
    assert "stream_epic" not in record
    assert "task_family" not in record
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    assert payload["by_stream_epic"]["6943"]["dispatch"]["n"] == 1
    assert payload["by_task_family"]["infra"]["dispatch"]["n"] == 1
    assert payload["unclassified"]["by_stream_epic"]["dispatch"]["n"] == 0


def test_top_level_identity_remains_a_fallback(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task(
        tasks_dir,
        "legacy",
        started=NOW - timedelta(seconds=10),
        finished=NOW,
        top_level_identity=True,
    )
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    assert payload["by_stream_epic"]["4707"]["dispatch"]["n"] == 1
    assert payload["by_task_family"]["fleet-comms-metrics"]["dispatch"]["n"] == 1


def test_carrier_identity_takes_precedence_and_ignores_dor_preflight(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    started = (NOW - timedelta(seconds=10)).isoformat()
    base = {"task_id": "t", "started_at": started, "finished_at": NOW.isoformat()}
    records = {
        # carrier wins over the legacy top-level keys, per field
        "both": {
            **base,
            "stream_epic": 1,
            "task_family": "old",
            "task_lifecycle": {"identity": {"stream_epic": 6943}},
        },
        # list-valued dor_preflight.stream_epic is never read
        "dor-only": {**base, "dor_preflight": {"stream_epic": [6943, 9737]}},
    }
    for name, record in records.items():
        (tasks_dir / f"{name}.json").write_text(
            json.dumps({**record, "task_id": name}), encoding="utf-8"
        )
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    assert payload["by_stream_epic"]["6943"]["dispatch"]["n"] == 1
    assert "1" not in payload["by_stream_epic"]
    assert payload["by_task_family"]["old"]["dispatch"]["n"] == 1
    assert payload["unclassified"]["by_stream_epic"]["dispatch"]["n"] == 1


@pytest.mark.parametrize(
    ("record", "error_kind"),
    [
        ({"decision": "approve", "started_at": "2026-07-22T11:00:00+00:00"}, "not_a_task_record"),
        ({"task_id": "t", "status": "stub"}, "missing_started_at"),
        ({"task_id": "t", "started_at": None}, "missing_started_at"),
        ({"task_id": "t", "started_at": "garbage"}, "invalid_started_at"),
        ({"task_id": "t", "started_at": ""}, "invalid_started_at"),
    ],
)
def test_dispatch_source_errors_name_what_is_wrong(
    tmp_path: Path, record: dict[str, object], error_kind: str
) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "bad.json").write_text(json.dumps(record), encoding="utf-8")
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    dispatch_errors = [e for e in payload["source_errors"] if e["source"] == "dispatch"]
    assert [e["error_kind"] for e in dispatch_errors] == [error_kind]
    assert payload["unclassified"]["by_stream_epic"]["dispatch"]["n"] == 0


def _collect_with_deadline(tasks_dir: Path, plane_db: Path, *, seconds: float = 20.0) -> dict[str, object]:
    """Run the collector on a thread so a FIFO-blocked open fails the test, not the suite."""
    result: dict[str, object] = {}
    worker = threading.Thread(
        target=lambda: result.update(
            collect_stream_bottleneck_metrics(
                tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
            )
        ),
        daemon=True,
    )
    worker.start()
    worker.join(seconds)
    assert not worker.is_alive(), "collector blocked (a FIFO or device was opened)"
    return result


def _identity_payload(tmp_path: Path, records: dict[str, dict[str, object]]) -> dict[str, object]:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    started = (NOW - timedelta(seconds=10)).isoformat()
    for name, extra in records.items():
        record = {"task_id": name, "started_at": started, "finished_at": NOW.isoformat(), **extra}
        (tasks_dir / f"{name}.json").write_text(json.dumps(record), encoding="utf-8")
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)
    return collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )


_INVALID_STREAM_EPICS = [
    pytest.param([6943, 9737], id="list"),
    pytest.param({"epic": 6943}, id="dict"),
    pytest.param(6943.0, id="float"),
    pytest.param(True, id="bool"),
    pytest.param(-6943, id="negative-int"),
    pytest.param("", id="empty"),
    pytest.param("   ", id="whitespace"),
    pytest.param("epic-6943", id="non-digit-string"),
]
_INVALID_TASK_FAMILIES = [
    pytest.param(["infra"], id="list"),
    pytest.param({"name": "infra"}, id="dict"),
    pytest.param(1.5, id="float"),
    pytest.param(True, id="bool"),
    pytest.param("", id="empty"),
    pytest.param("   ", id="whitespace"),
]


@pytest.mark.parametrize("bad", _INVALID_STREAM_EPICS)
def test_invalid_carrier_stream_epic_falls_back_to_valid_top_level(
    tmp_path: Path, bad: object
) -> None:
    payload = _identity_payload(
        tmp_path,
        {"t": {"stream_epic": 6943, "task_lifecycle": {"identity": {"stream_epic": bad}}}},
    )

    assert list(payload["by_stream_epic"]) == ["6943"]
    assert payload["by_stream_epic"]["6943"]["dispatch"]["n"] == 1
    assert payload["unclassified"]["by_stream_epic"]["dispatch"]["n"] == 0
    assert payload["source_errors"] == []


@pytest.mark.parametrize("bad", _INVALID_STREAM_EPICS)
def test_invalid_stream_epic_without_fallback_is_unclassified(
    tmp_path: Path, bad: object
) -> None:
    payload = _identity_payload(
        tmp_path, {"t": {"task_lifecycle": {"identity": {"stream_epic": bad}}}}
    )

    assert payload["by_stream_epic"] == {}
    assert payload["unclassified"]["by_stream_epic"]["dispatch"]["n"] == 1


@pytest.mark.parametrize("bad", _INVALID_TASK_FAMILIES)
def test_invalid_carrier_task_family_falls_back_to_valid_top_level(
    tmp_path: Path, bad: object
) -> None:
    payload = _identity_payload(
        tmp_path,
        {"t": {"task_family": "infra", "task_lifecycle": {"identity": {"task_family": bad}}}},
    )

    assert list(payload["by_task_family"]) == ["infra"]
    assert payload["by_task_family"]["infra"]["dispatch"]["n"] == 1
    assert payload["unclassified"]["by_task_family"]["dispatch"]["n"] == 0
    assert payload["source_errors"] == []


@pytest.mark.parametrize("bad", _INVALID_TASK_FAMILIES)
def test_invalid_task_family_without_fallback_is_unclassified(
    tmp_path: Path, bad: object
) -> None:
    payload = _identity_payload(
        tmp_path, {"t": {"task_lifecycle": {"identity": {"task_family": bad}}}}
    )

    assert payload["by_task_family"] == {}
    assert payload["unclassified"]["by_task_family"]["dispatch"]["n"] == 1


def test_identity_values_are_normalised_before_grouping(tmp_path: Path) -> None:
    payload = _identity_payload(
        tmp_path,
        {
            "a": {"task_lifecycle": {"identity": {"stream_epic": " 6943 ", "task_family": " infra "}}},
            "b": {"task_lifecycle": {"identity": {"stream_epic": "06943", "task_family": "infra"}}},
        },
    )

    assert payload["by_stream_epic"]["6943"]["dispatch"]["n"] == 2
    assert payload["by_task_family"]["infra"]["dispatch"]["n"] == 2


def test_dispatch_records_scanned_equal_classified_unclassified_plus_errors(
    tmp_path: Path,
) -> None:
    """Every scanned task file lands in exactly one of: classified, unclassified, error."""
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "archive").mkdir(parents=True)
    started = (NOW - timedelta(seconds=10)).isoformat()
    base = {"task_id": "t", "started_at": started, "finished_at": NOW.isoformat()}
    identity = {"stream_epic": 6943, "task_family": "infra"}
    records: dict[str, dict[str, object]] = {
        "carrier": {**base, "task_lifecycle": {"identity": identity}},
        "archived-carrier": {**base, "task_lifecycle": {"identity": identity}},
        "fallback": {**base, **identity},
        "malformed-with-fallback": {
            **base,
            **identity,
            "task_lifecycle": {"identity": {"stream_epic": [1, 2], "task_family": {"x": 1}}},
        },
        "malformed-no-fallback": {
            **base,
            "task_lifecycle": {"identity": {"stream_epic": 1.5, "task_family": True}},
        },
        "no-identity": dict(base),
        "non-task": {"decision": "approve", "started_at": started},
        "missing-timestamp": {"task_id": "t"},
        "invalid-timestamp": {"task_id": "t", "started_at": "garbage"},
        "invalid-finished": {**base, "finished_at": "garbage"},
        "negative-duration": {**base, "started_at": NOW.isoformat(), "finished_at": started},
    }
    for name, record in records.items():
        directory = tasks_dir / "archive" if name.startswith("archived") else tasks_dir
        (directory / f"{name}.json").write_text(json.dumps(record), encoding="utf-8")
    (tasks_dir / "unreadable.json").write_text("{not json", encoding="utf-8")
    (tasks_dir / "not-object.json").write_text("[1, 2]", encoding="utf-8")
    # File-level hostile entries: each must be its own error kind, never dropped.
    os.mkfifo(tasks_dir / "fifo.json")
    (tasks_dir / "dir.json").mkdir()
    (tasks_dir / "loop.json").symlink_to("loop.json")
    (tasks_dir / "dangling.json").symlink_to("missing-target")
    with (tasks_dir / "huge.json").open("wb") as handle:
        handle.truncate(efficiency_metrics._MAX_TASK_RECORD_BYTES + 1)
    scanned = len(records) + 2 + 5
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)

    payload = _collect_with_deadline(tasks_dir, plane_db)

    dispatch_errors = [e for e in payload["source_errors"] if e["source"] == "dispatch"]
    assert sorted(e["error_kind"] for e in dispatch_errors) == [
        "invalid_finished_at",
        "invalid_started_at",
        "missing_started_at",
        "negative_duration",
        "not_a_task_record",
        "task_record_not_object",
        "task_record_not_regular",
        "task_record_not_regular",
        "task_record_too_large",
        "task_record_unreadable",
        "task_record_unreadable",
        "task_record_unreadable",
    ]
    for dimension in ("by_stream_epic", "by_task_family"):
        classified = sum(g["dispatch"]["n"] for g in payload[dimension].values())
        unclassified = payload["unclassified"][dimension]["dispatch"]["n"]
        assert classified + unclassified + len(dispatch_errors) == scanned
    assert payload["by_stream_epic"]["6943"]["dispatch"]["n"] == 4
    assert payload["unclassified"]["by_stream_epic"]["dispatch"]["n"] == 2


def _assert_aggregate_invariant(payload: dict[str, object], scanned: int) -> None:
    errors = [e for e in payload["source_errors"] if e["source"] == "dispatch"]
    for dimension in ("by_stream_epic", "by_task_family"):
        classified = sum(g["dispatch"]["n"] for g in payload[dimension].values())
        unclassified = payload["unclassified"][dimension]["dispatch"]["n"]
        assert classified + unclassified + len(errors) == scanned


def test_leading_zero_carrier_of_any_length_canonicalises_without_int_conversion(
    tmp_path: Path,
) -> None:
    zeros = "0" * 5000 + "6943"
    payload = _identity_payload(
        tmp_path,
        {
            "bare": {"task_lifecycle": {"identity": {"stream_epic": zeros}}},
            "with-fallback": {"stream_epic": 6943, "task_lifecycle": {"identity": {"stream_epic": zeros}}},
        },
    )

    assert list(payload["by_stream_epic"]) == ["6943"]
    assert payload["by_stream_epic"]["6943"]["dispatch"]["n"] == 2
    _assert_aggregate_invariant(payload, 2)


def test_all_zero_epic_string_canonicalises_to_single_zero(tmp_path: Path) -> None:
    payload = _identity_payload(
        tmp_path, {"t": {"task_lifecycle": {"identity": {"stream_epic": "0" * 5000}}}}
    )

    assert list(payload["by_stream_epic"]) == ["0"]


_OVERSIZED_EPICS = [
    pytest.param("1" + "0" * 5000, id="oversized-string"),
    pytest.param("9" * 19, id="nineteen-digit-string"),
    pytest.param(10**18, id="oversized-int-at-bound"),
    pytest.param(10**4000, id="oversized-int-4000-digits"),
]


@pytest.mark.parametrize("big", _OVERSIZED_EPICS)
def test_oversized_carrier_epic_falls_back_or_is_unclassified(tmp_path: Path, big: object) -> None:
    payload = _identity_payload(
        tmp_path,
        {
            "fallback": {"stream_epic": 6943, "task_lifecycle": {"identity": {"stream_epic": big}}},
            "bare": {"task_lifecycle": {"identity": {"stream_epic": big}}},
        },
    )

    assert list(payload["by_stream_epic"]) == ["6943"]
    assert payload["by_stream_epic"]["6943"]["dispatch"]["n"] == 1
    assert payload["unclassified"]["by_stream_epic"]["dispatch"]["n"] == 1
    _assert_aggregate_invariant(payload, 2)


@pytest.mark.parametrize("big", _OVERSIZED_EPICS)
def test_oversized_fallback_epic_does_not_override_valid_carrier(tmp_path: Path, big: object) -> None:
    payload = _identity_payload(
        tmp_path,
        {"t": {"stream_epic": big, "task_lifecycle": {"identity": {"stream_epic": 6943}}}},
    )

    assert list(payload["by_stream_epic"]) == ["6943"]
    _assert_aggregate_invariant(payload, 1)


def test_oversized_task_family_is_unclassified_or_falls_back(tmp_path: Path) -> None:
    payload = _identity_payload(
        tmp_path,
        {
            "fallback": {"task_family": "infra", "task_lifecycle": {"identity": {"task_family": "x" * 100_000}}},
            "bare": {"task_lifecycle": {"identity": {"task_family": "x" * 100_000}}},
            "at-bound": {"task_family": "y" * 128},
        },
    )

    assert sorted(payload["by_task_family"]) == ["infra", "y" * 128]
    assert payload["unclassified"]["by_task_family"]["dispatch"]["n"] == 1
    _assert_aggregate_invariant(payload, 3)


@pytest.mark.parametrize(
    "digits",
    [
        pytest.param("\u0666\u0669\u0664\u0663", id="arabic-indic"),
        pytest.param("\uff16\uff19\uff14\uff13", id="fullwidth"),
        pytest.param("\u00b2", id="superscript"),
    ],
)
def test_unicode_digit_epics_are_not_classified(tmp_path: Path, digits: str) -> None:
    payload = _identity_payload(
        tmp_path,
        {
            "carrier": {"task_lifecycle": {"identity": {"stream_epic": digits}}},
            "top": {"stream_epic": digits},
        },
    )

    assert payload["by_stream_epic"] == {}
    assert payload["unclassified"]["by_stream_epic"]["dispatch"]["n"] == 2
    _assert_aggregate_invariant(payload, 2)


_STARTED = b'{"task_id":"t","started_at":"2026-07-22T11:00:00+00:00"'


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(_STARTED + b',"stream_epic":1' + b"0" * 5000 + b"}", id="json-int-over-conversion-limit"),
        pytest.param(b"\xff\xfe" + _STARTED + b"}", id="invalid-utf8"),
        pytest.param(b"[" * 100_000, id="deeply-nested"),
    ],
)
def test_hostile_task_file_is_a_source_error_never_an_abort(tmp_path: Path, raw: bytes) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "hostile.json").write_bytes(raw)
    (tasks_dir / "good.json").write_text(
        json.dumps({"task_id": "g", "started_at": (NOW - timedelta(seconds=5)).isoformat(),
                    "finished_at": NOW.isoformat(), "stream_epic": 6943}),
        encoding="utf-8",
    )
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    dispatch_errors = [e["error_kind"] for e in payload["source_errors"] if e["source"] == "dispatch"]
    assert dispatch_errors == ["task_record_unreadable"]
    assert payload["by_stream_epic"]["6943"]["dispatch"]["n"] == 1
    json.dumps(payload)


def test_absurd_hard_timeout_cannot_inflate_the_bottleneck_threshold(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    started = (NOW - timedelta(seconds=5)).isoformat()
    for name, timeout in (("huge", 10**3000), ("bool", True), ("sane", 9000)):
        (tasks_dir / f"{name}.json").write_text(
            json.dumps({"task_id": name, "started_at": started, "hard_timeout": timeout}),
            encoding="utf-8",
        )
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)

    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir, plane_db=plane_db, now=NOW, github_lookup=_merged_at
    )

    assert payload["threshold_seconds"]["dispatch"] == 9000


def _file_level_payload(
    tmp_path: Path, make_hostile: Callable[[Path], None]
) -> tuple[dict[str, object], list[str]]:
    """One valid record plus whatever ``make_hostile`` plants beside it."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    _write_task(tasks_dir, "good", started=NOW - timedelta(seconds=5), finished=NOW)
    make_hostile(tasks_dir)
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)
    payload = _collect_with_deadline(tasks_dir, plane_db)
    kinds = [e["error_kind"] for e in payload["source_errors"] if e["source"] == "dispatch"]
    return payload, kinds


def _assert_valid_record_and_one_error(payload: dict[str, object], kinds: list[str], expected: str) -> None:
    assert kinds == [expected]
    assert payload["by_stream_epic"]["4707"]["dispatch"]["n"] == 1
    _assert_aggregate_invariant(payload, 2)
    json.dumps(payload)


def test_fifo_beside_valid_record_is_counted_and_never_opened(tmp_path: Path) -> None:
    payload, kinds = _file_level_payload(tmp_path, lambda d: os.mkfifo(d / "pipe.json"))

    _assert_valid_record_and_one_error(payload, kinds, "task_record_not_regular")


def test_symlink_to_fifo_is_counted_and_never_opened(tmp_path: Path) -> None:
    def plant(tasks_dir: Path) -> None:
        os.mkfifo(tasks_dir / "pipe.fifo")
        (tasks_dir / "link.json").symlink_to("pipe.fifo")

    payload, kinds = _file_level_payload(tmp_path, plant)

    _assert_valid_record_and_one_error(payload, kinds, "task_record_not_regular")


def test_looping_symlink_beside_valid_record_is_counted(tmp_path: Path) -> None:
    payload, kinds = _file_level_payload(tmp_path, lambda d: (d / "loop.json").symlink_to("loop.json"))

    _assert_valid_record_and_one_error(payload, kinds, "task_record_unreadable")


def test_dangling_symlink_beside_valid_record_is_counted(tmp_path: Path) -> None:
    payload, kinds = _file_level_payload(tmp_path, lambda d: (d / "dangling.json").symlink_to("nowhere"))

    _assert_valid_record_and_one_error(payload, kinds, "task_record_unreadable")


def test_directory_named_like_a_task_file_is_counted(tmp_path: Path) -> None:
    payload, kinds = _file_level_payload(tmp_path, lambda d: (d / "folder.json").mkdir())

    _assert_valid_record_and_one_error(payload, kinds, "task_record_not_regular")


def test_symlink_to_a_valid_record_is_still_read(tmp_path: Path) -> None:
    def plant(tasks_dir: Path) -> None:
        (tasks_dir / "alias.json").symlink_to("good.json")

    payload, _kinds = _file_level_payload(tmp_path, plant)

    assert _kinds == []
    assert payload["by_stream_epic"]["4707"]["dispatch"]["n"] == 2


def test_file_vanishing_between_listing_and_read_is_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    listing = efficiency_metrics._task_record_paths

    def listing_with_ghost(directory: Path, *, optional: bool) -> list[Path]:
        paths = listing(directory, optional=optional)
        return [*paths, directory / "vanished.json"] if not optional else paths

    monkeypatch.setattr(efficiency_metrics, "_task_record_paths", listing_with_ghost)

    payload, kinds = _file_level_payload(tmp_path, lambda _d: None)

    _assert_valid_record_and_one_error(payload, kinds, "task_record_unreadable")


@pytest.mark.parametrize(
    ("padding", "expected"),
    [(-1, None), (0, None), (1, "task_record_too_large")],
    ids=["below-cap", "at-cap", "just-above-cap"],
)
def test_task_record_size_cap_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, padding: int, expected: str | None
) -> None:
    cap = 4096
    monkeypatch.setattr(efficiency_metrics, "_MAX_TASK_RECORD_BYTES", cap)
    started = (NOW - timedelta(seconds=5)).isoformat()
    body = json.dumps({"task_id": "big", "started_at": started, "finished_at": NOW.isoformat(), "stream_epic": 4707})

    def plant(tasks_dir: Path) -> None:
        (tasks_dir / "big.json").write_text(body + " " * (cap + padding - len(body)), encoding="utf-8")

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    plant(tasks_dir)
    assert (tasks_dir / "big.json").stat().st_size == cap + padding
    plane_db = tmp_path / "plane.sqlite3"
    _plane_db(plane_db, with_identity=False)

    payload = _collect_with_deadline(tasks_dir, plane_db)

    kinds = [e["error_kind"] for e in payload["source_errors"] if e["source"] == "dispatch"]
    assert kinds == ([expected] if expected else [])
    assert payload["by_stream_epic"].get("4707", {}).get("dispatch", {}).get("n", 0) == (0 if expected else 1)
    _assert_aggregate_invariant(payload, 1)


def test_hundred_megabyte_file_is_counted_without_being_read(tmp_path: Path) -> None:
    def plant(tasks_dir: Path) -> None:
        with (tasks_dir / "huge.json").open("wb") as handle:
            handle.write(b'{"task_id":"x","padding":"')
            handle.truncate(100 * 1024 * 1024)

    payload, kinds = _file_level_payload(tmp_path, plant)

    _assert_valid_record_and_one_error(payload, kinds, "task_record_too_large")


def test_memory_error_while_parsing_is_a_source_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_loads = json.loads

    def loads(text: str) -> object:
        if '"boom"' in text:
            raise MemoryError
        return real_loads(text)

    monkeypatch.setattr(efficiency_metrics.json, "loads", loads)

    def plant(tasks_dir: Path) -> None:
        (tasks_dir / "boom.json").write_text('{"task_id": "boom"}', encoding="utf-8")

    payload, kinds = _file_level_payload(tmp_path, plant)

    _assert_valid_record_and_one_error(payload, kinds, "task_record_unreadable")
