"""Tests for the read-only #6106 legacy Broker Ops report and facade."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.fleet_comms.cli import EXIT_ERROR, EXIT_OK, main
from scripts.fleet_comms.legacy_broker_report import build_legacy_broker_report


def _seed_telemetry(path: Path, *, coverage_started_at: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE telemetry_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE legacy_comms_route_usage (
                hour_utc TEXT NOT NULL,
                route_id TEXT NOT NULL,
                method TEXT NOT NULL,
                caller_class TEXT NOT NULL,
                status_class TEXT NOT NULL,
                count INTEGER NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            );
            CREATE TABLE legacy_bridge_ask_usage (
                hour_utc TEXT NOT NULL,
                target TEXT NOT NULL,
                caller_family TEXT NOT NULL,
                started_count INTEGER NOT NULL,
                succeeded_count INTEGER NOT NULL,
                failed_count INTEGER NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            );
            """
        )
        started = coverage_started_at.isoformat().replace("+00:00", "Z")
        connection.executemany(
            "INSERT INTO telemetry_meta(key, value) VALUES (?, ?)",
            [
                ("coverage_started_at", started),
                ("bridge_coverage_started_at", started),
            ],
        )


def _insert_usage(path: Path, *, now: datetime) -> None:
    observed = now.isoformat().replace("+00:00", "Z")
    with sqlite3.connect(path) as connection:
        connection.executemany(
            """
            INSERT INTO legacy_comms_route_usage(
                hour_utc, route_id, method, caller_class, status_class,
                count, first_seen, last_seen
            ) VALUES (?, 'messages', 'GET', ?, '2xx', ?, ?, ?)
            """,
            [
                (observed, "browser", 2, observed, observed),
                (observed, "automation", 3, observed, observed),
                (observed, "canary", 1, observed, observed),
            ],
        )
        connection.executemany(
            """
            INSERT INTO legacy_bridge_ask_usage(
                hour_utc, target, caller_family, started_count,
                succeeded_count, failed_count, first_seen, last_seen
            ) VALUES (?, 'glm', ?, ?, ?, ?, ?, ?)
            """,
            [
                (observed, "operator", 4, 3, 1, observed, observed),
                (observed, "openai", 2, 2, 0, observed, observed),
                (observed, "unknown", 1, 0, 0, observed, observed),
            ],
        )


def _store_for(report: dict, kind: str) -> dict:
    return next(item for item in report["stores"] if item["kind"] == kind)


def test_report_classifies_all_usage_without_mutating_telemetry(tmp_path: Path) -> None:
    now = datetime(2026, 8, 9, 12, tzinfo=UTC)
    database = tmp_path / "legacy.db"
    _seed_telemetry(database, coverage_started_at=now - timedelta(days=8))
    _insert_usage(database, now=now)
    before = hashlib.sha256(database.read_bytes()).hexdigest()

    report = build_legacy_broker_report(7, routes_db=database, now=now)

    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    assert report["read_only"] is True
    routes = _store_for(report, "legacy_comms_routes")
    assert routes["window_fully_observed"] is True
    assert routes["usage"] == {
        "seat": {"count": 2, "by_caller": {"browser": 2}},
        "background": {"count": 3, "by_caller": {"automation": 3}},
        "other": {"count": 1, "by_caller": {"canary": 1}},
    }
    bridge = _store_for(report, "legacy_bridge")
    assert bridge["usage"] == {
        "seat": {"count": 4, "by_caller": {"operator": 4}},
        "background": {"count": 2, "by_caller": {"openai": 2}},
        "other": {"count": 1, "by_caller": {"unknown": 1}},
    }
    assert bridge["outcomes"] == {"succeeded": 5, "failed": 1, "unfinished": 1}
    assert report["zero_use_candidate"] == {
        "eligible": False,
        "reason_codes": ["legacy_bridge_has_usage", "legacy_comms_routes_has_usage"],
        "operator_declaration_required": True,
    }


def test_report_allows_only_complete_empty_windows(tmp_path: Path) -> None:
    now = datetime(2026, 8, 9, 12, tzinfo=UTC)
    database = tmp_path / "legacy.db"
    _seed_telemetry(database, coverage_started_at=now - timedelta(days=8))

    report = build_legacy_broker_report(7, routes_db=database, now=now)

    assert report["zero_use_candidate"] == {
        "eligible": True,
        "reason_codes": [],
        "operator_declaration_required": True,
    }


def test_explicit_bridge_store_replaces_co_located_bridge_counts(tmp_path: Path) -> None:
    now = datetime(2026, 8, 9, 12, tzinfo=UTC)
    routes_database = tmp_path / "routes.db"
    bridge_database = tmp_path / "bridge.db"
    _seed_telemetry(routes_database, coverage_started_at=now - timedelta(days=8))
    _insert_usage(routes_database, now=now)
    _seed_telemetry(bridge_database, coverage_started_at=now - timedelta(days=8))

    report = build_legacy_broker_report(
        7,
        routes_db=routes_database,
        bridge_db=bridge_database,
        now=now,
    )

    bridge_reports = [item for item in report["stores"] if item["kind"] == "legacy_bridge"]
    assert len(bridge_reports) == 1
    assert bridge_reports[0]["path"] == str(bridge_database)
    assert bridge_reports[0]["usage"]["seat"]["count"] == 0


def test_report_refuses_to_treat_missing_or_incomplete_telemetry_as_zero_use(tmp_path: Path) -> None:
    now = datetime(2026, 8, 9, 12, tzinfo=UTC)
    missing = build_legacy_broker_report(7, routes_db=tmp_path / "missing.db", now=now)
    assert missing["zero_use_candidate"]["eligible"] is False
    assert missing["zero_use_candidate"]["reason_codes"] == [
        "legacy_bridge_not_readable",
        "legacy_comms_routes_not_readable",
    ]

    database = tmp_path / "incomplete.db"
    _seed_telemetry(database, coverage_started_at=now - timedelta(days=6))
    incomplete = build_legacy_broker_report(7, routes_db=database, now=now)
    assert incomplete["zero_use_candidate"]["reason_codes"] == [
        "legacy_bridge_window_incomplete",
        "legacy_comms_routes_window_incomplete",
    ]


def test_fleet_broker_report_cli_is_json_and_exit_zero(tmp_path: Path, capsys) -> None:
    database = tmp_path / "missing.db"

    rc = main(["fleet", "broker-report", "--days", "7", "--routes-db", str(database)])

    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "fleet-broker-report.v1"
    assert payload["zero_use_candidate"]["eligible"] is False


def test_fleet_broker_report_rejects_unsupported_windows(capsys) -> None:
    rc = main(["fleet", "broker-report", "--days", "0"])

    assert rc == EXIT_ERROR
    assert "days must be between 1 and 90" in capsys.readouterr().err


def test_fleet_status_and_help_expose_the_facade_contract(tmp_path: Path, capsys) -> None:
    rc = main(["fleet", "status", "--root", str(tmp_path / "uninitialized")])
    assert rc == EXIT_OK
    status = json.loads(capsys.readouterr().out)
    assert status["health"] == {
        "db_exists": False,
        "enabled": True,
        "healthy": False,
        "mode": "authority",
        "read_only": True,
        "schema_version": None,
    }

    rc = main(["fleet", "help"])
    assert rc == EXIT_OK
    help_payload = json.loads(capsys.readouterr().out)
    assert set(help_payload) == {"truth", "hand", "eyes", "note"}
    assert "broker_report" in help_payload["truth"]
    assert "reap_report" in help_payload["hand"]
    assert {"board", "backlog", "dead"} <= set(help_payload["eyes"])


def test_fleet_reap_report_forwards_only_the_established_guards(monkeypatch, capsys) -> None:
    from scripts.orchestration import reap_worktrees

    observed: list[list[str]] = []

    def fake_main(args: list[str]) -> int:
        observed.append(args)
        return 0

    monkeypatch.setattr(reap_worktrees, "main", fake_main)

    assert main(["fleet", "reap-report"]) == EXIT_OK
    assert main(["fleet", "reap-report", "--apply", "--json", "--repo-root", "/repo"]) == EXIT_OK
    assert capsys.readouterr().out == ""
    assert observed == [
        ["--merged", "--dry-run"],
        ["--merged", "--apply", "--repo-root", "/repo", "--json"],
    ]
