"""Body-free telemetry contracts for legacy one-shot bridge aliases (#6106)."""

from __future__ import annotations

import json
import sqlite3
import stat
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.ai_agent_bridge import _acp_compat
from scripts.api import telemetry_router
from scripts.api.telemetry import legacy_comms
from scripts.telemetry import legacy_bridge


@pytest.fixture()
def telemetry_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "telemetry" / "legacy-comms.db"
    monkeypatch.setattr(legacy_bridge, "_DB_PATH", path)
    legacy_bridge._reset_initialized_paths_for_tests()
    return path


def _rows(path: Path) -> list[tuple]:
    with sqlite3.connect(str(path)) as connection:
        return connection.execute(
            """
            SELECT hour_utc, target, caller_family, started_count,
                   succeeded_count, failed_count, first_seen, last_seen
            FROM legacy_bridge_ask_usage
            ORDER BY target, caller_family
            """
        ).fetchall()


def _store_bytes(path: Path) -> bytes:
    return b"".join(
        candidate.read_bytes()
        for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm"))
        if candidate.exists()
    )


def test_default_store_resolves_from_a_linked_worktree_to_the_primary_checkout(
    tmp_path: Path,
) -> None:
    primary = tmp_path / "primary"
    worktree = tmp_path / "dispatch" / "task"
    worktree_git_dir = primary / ".git" / "worktrees" / "task"
    worktree_git_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {worktree_git_dir}\n", encoding="utf-8")

    assert legacy_bridge._shared_telemetry_db_path(worktree) == (
        primary / "data" / "telemetry" / "legacy_comms_routes.db"
    )


def test_release_snapshot_store_uses_its_primary_data_symlink(tmp_path: Path) -> None:
    primary_data = tmp_path / "primary" / "data"
    (primary_data / "telemetry").mkdir(parents=True)
    release = tmp_path / "release"
    release.mkdir()
    (release / "data").symlink_to(primary_data, target_is_directory=True)

    path = legacy_bridge._shared_telemetry_db_path(release)

    assert path == release / "data" / "telemetry" / "legacy_comms_routes.db"
    assert path.resolve() == (
        primary_data / "telemetry" / "legacy_comms_routes.db"
    ).resolve()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (None, "operator"),
        ("codex-infra", "openai"),
        ("claude-desktop", "anthropic"),
        ("agy", "google"),
        ("grok-build", "xai"),
        ("kimi-devops", "moonshot"),
        ("glm", "zhipu"),
        ("hermes", "deepseek"),
        ("cursor", "cursor"),
        ("private-caller-name", "unknown"),
    ],
)
def test_caller_identity_is_collapsed_to_a_fixed_family(source, expected) -> None:
    assert legacy_bridge.classify_caller_family(source) == expected


def test_success_failure_and_unfinished_counts_are_conservative(telemetry_db: Path) -> None:
    now = datetime(2026, 8, 2, 0, 30, tzinfo=UTC)
    success = legacy_bridge.record_bridge_invocation_start(
        "glm", "codex-infra", db_path=telemetry_db, now=now
    )
    legacy_bridge.record_bridge_invocation_finish(success, succeeded=True, now=now)
    failure = legacy_bridge.record_bridge_invocation_start(
        "glm", "codex-infra", db_path=telemetry_db, now=now
    )
    legacy_bridge.record_bridge_invocation_finish(failure, succeeded=False, now=now)
    legacy_bridge.record_bridge_invocation_start(
        "glm", "codex-infra", db_path=telemetry_db, now=now
    )

    payload = legacy_bridge.bridge_usage_summary("1h", db_path=telemetry_db, now=now)
    assert payload["started"] == 3
    assert payload["succeeded"] == 1
    assert payload["failed"] == 1
    assert payload["unfinished"] == 1
    glm = next(item for item in payload["targets"] if item["target"] == "glm")
    assert glm["by_caller_family"] == {"openai": 3}


def test_wrapper_records_result_truth_without_persisting_inputs(
    telemetry_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    markers = {
        "prompt": "private-prompt-6106",
        "task": "private-task-6106",
        "attachment": "private-attachment-6106",
        "model": "private-model-6106",
        "path": "private-output-path-6106",
        "source": "private-caller-6106",
    }

    def fake_impl(*args, **kwargs):
        assert markers["prompt"] in args
        assert markers["task"] == kwargs["task_id"]
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(_acp_compat, "_run_compat_ask_impl", fake_impl)
    result = _acp_compat.run_compat_ask(
        "glm",
        markers["prompt"],
        task_id=markers["task"],
        source=markers["source"],
        model=markers["model"],
        data=markers["attachment"],
        output_path=markers["path"],
    )

    assert result.ok is True
    persisted = _store_bytes(telemetry_db)
    assert all(value.encode() not in persisted for value in markers.values())
    assert _rows(telemetry_db)[0][1:6] == ("glm", "unknown", 1, 1, 0)


def test_wrapper_records_false_result_and_exception_as_failures(
    telemetry_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        _acp_compat,
        "_run_compat_ask_impl",
        lambda *_args, **_kwargs: SimpleNamespace(ok=False),
    )
    assert _acp_compat.run_compat_ask("kimi", "prompt", task_id="false-result").ok is False

    def fail(*_args, **_kwargs):
        raise RuntimeError("private-provider-error-6106")

    monkeypatch.setattr(_acp_compat, "_run_compat_ask_impl", fail)
    with pytest.raises(RuntimeError, match="private-provider-error-6106"):
        _acp_compat.run_compat_ask("kimi", "prompt", task_id="exception")

    payload = legacy_bridge.bridge_usage_summary("1h", db_path=telemetry_db)
    assert payload["started"] == 2
    assert payload["succeeded"] == 0
    assert payload["failed"] == 2
    assert b"private-provider-error-6106" not in _store_bytes(telemetry_db)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"command_target": "retired", "content": "prompt", "task_id": "task"},
        {"command_target": "glm", "content": "prompt", "task_id": ""},
    ],
)
def test_refused_invocations_do_not_start_coverage_or_usage(
    telemetry_db: Path,
    kwargs: dict,
) -> None:
    with pytest.raises(ValueError):
        _acp_compat.run_compat_ask(**kwargs)
    assert not telemetry_db.exists()


def test_review_true_runs_as_normal_ask_and_records_usage(
    telemetry_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``review=True`` is accepted as a normal ask (operator order 2026-08-06)."""

    def fake_impl(*_args, **_kwargs):
        assert _kwargs.get("review") is True
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(_acp_compat, "_run_compat_ask_impl", fake_impl)
    result = _acp_compat.run_compat_ask(
        "glm", "prompt", task_id="task", review=True
    )
    assert result.ok is True
    assert _rows(telemetry_db)[0][1:6] == ("glm", "operator", 1, 1, 0)


def test_storage_outage_never_replaces_bridge_result(
    telemetry_db: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_start(*_args, **_kwargs):
        raise OSError("synthetic telemetry outage")

    monkeypatch.setattr(legacy_bridge, "record_bridge_invocation_start", fail_start)
    monkeypatch.setattr(
        _acp_compat,
        "_run_compat_ask_impl",
        lambda *_args, **_kwargs: SimpleNamespace(ok=True),
    )
    result = _acp_compat.run_compat_ask("codex", "prompt", task_id="outage")
    assert result.ok is True
    assert not telemetry_db.exists()


def test_concurrent_process_style_buckets_are_atomic(telemetry_db: Path) -> None:
    now = datetime(2026, 8, 2, 0, 30, tzinfo=UTC)

    def record(_index: int) -> None:
        token = legacy_bridge.record_bridge_invocation_start(
            "agy", "claude-infra", db_path=telemetry_db, now=now
        )
        legacy_bridge.record_bridge_invocation_finish(token, succeeded=True, now=now)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(record, range(40)))

    row = _rows(telemetry_db)[0]
    assert row[1:6] == ("agy", "anthropic", 40, 40, 0)


def test_retention_permissions_and_complete_window_truth(telemetry_db: Path) -> None:
    now = datetime(2026, 8, 10, 0, 30, tzinfo=UTC)
    legacy_bridge.initialize_bridge_telemetry(
        telemetry_db,
        now=now - timedelta(days=8),
    )
    with sqlite3.connect(str(telemetry_db)) as connection:
        connection.execute(
            """
            INSERT INTO legacy_bridge_ask_usage(
                hour_utc, target, caller_family, started_count,
                succeeded_count, failed_count, first_seen, last_seen
            ) VALUES (?, 'glm', 'operator', 1, 1, 0, ?, ?)
            """,
            (
                "2026-04-01T00:00:00Z",
                "2026-04-01T00:00:00Z",
                "2026-04-01T00:00:00Z",
            ),
        )
        connection.commit()
    telemetry_db.chmod(0o644)

    token = legacy_bridge.record_bridge_invocation_start(
        "glm", "operator", db_path=telemetry_db, now=now
    )
    legacy_bridge.record_bridge_invocation_finish(token, succeeded=True, now=now)
    payload = legacy_bridge.bridge_usage_summary("7d", db_path=telemetry_db, now=now)

    assert payload["started"] == 1
    assert payload["window_fully_observed"] is True
    assert stat.S_IMODE(telemetry_db.stat().st_mode) == 0o600
    for sidecar in (Path(f"{telemetry_db}-wal"), Path(f"{telemetry_db}-shm")):
        if sidecar.exists():
            assert stat.S_IMODE(sidecar.stat().st_mode) == 0o600
    assert len(_rows(telemetry_db)) == 1


def test_http_and_bridge_tables_coexist_in_one_private_store(telemetry_db: Path) -> None:
    now = datetime(2026, 8, 2, 0, 30, tzinfo=UTC)
    legacy_comms.record_legacy_route_usage(
        "messages", "GET", "canary", 200, db_path=telemetry_db, now=now
    )
    token = legacy_bridge.record_bridge_invocation_start(
        "glm", "codex", db_path=telemetry_db, now=now
    )
    legacy_bridge.record_bridge_invocation_finish(token, succeeded=True, now=now)
    with sqlite3.connect(str(telemetry_db)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert "legacy_comms_route_usage" in tables
    assert "legacy_bridge_ask_usage" in tables
    assert stat.S_IMODE(telemetry_db.stat().st_mode) == 0o600


def test_read_only_api_returns_all_targets_and_rejects_invalid_window(
    telemetry_db: Path,
) -> None:
    app = FastAPI()
    app.include_router(telemetry_router.router)
    with TestClient(app) as client:
        response = client.get("/api/telemetry/legacy-bridge-asks?window=1h")
        assert response.status_code == 200
        payload = response.json()
        assert payload["started"] == 0
        assert payload["window_fully_observed"] is False
        assert len(payload["targets"]) == 9
        assert client.get(
            "/api/telemetry/legacy-bridge-asks?window=forever"
        ).status_code == 422


def test_terminal_recovery_recreates_a_conservative_start(telemetry_db: Path) -> None:
    now = datetime(2026, 8, 2, 0, 30, tzinfo=UTC)
    token = legacy_bridge.record_bridge_invocation_start(
        "glm", "codex", db_path=telemetry_db, now=now
    )
    telemetry_db.unlink()
    legacy_bridge.record_bridge_invocation_finish(token, succeeded=True, now=now)
    row = _rows(telemetry_db)[0]
    assert row[1:6] == ("glm", "openai", 1, 1, 0)


def test_summary_json_never_contains_raw_caller_value(telemetry_db: Path) -> None:
    token = legacy_bridge.record_bridge_invocation_start(
        "glm", "private-caller-family-6106", db_path=telemetry_db
    )
    legacy_bridge.record_bridge_invocation_finish(token, succeeded=True)
    payload = legacy_bridge.bridge_usage_summary("1h", db_path=telemetry_db)
    assert "private-caller-family-6106" not in json.dumps(payload)
    assert payload["by_caller_family"] == {"unknown": 1}
