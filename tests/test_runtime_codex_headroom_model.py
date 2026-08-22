"""Regression tests for Codex runtime inventory default vs live dispatched model.

Issue #7087: ``/runtime.html`` Headroom previously queried ``?agent=codex&model=gpt-5.6-luna``
because it solely read the static registry default, while all live delegate tasks and recent
calls use ``gpt-5.6-terra``. ``/api/runtime/agents`` now reports ``last_used_model`` and
``headroom_model`` derived from live usage records, and ``runtime.html`` queries headroom
for the active model.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api import runtime_router
from scripts.api.config import DASHBOARDS_DIR
from scripts.api.main import app
from scripts.api.runtime_router import list_runtime_agents

client = TestClient(app, raise_server_exceptions=False)


def _write_usage_record(file_path: Path, records: list[dict]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def test_agents_endpoint_reports_last_used_and_headroom_model(tmp_path: Path, monkeypatch) -> None:
    usage_dir = tmp_path / "api_usage"
    now = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)

    # 1. Without usage records, last_used_model is None and headroom_model falls back to default_model.
    agents = list_runtime_agents()
    codex = next(a for a in agents if a["name"] == "codex")
    assert codex["default_model"] == "gpt-5.6-luna"
    assert codex["last_used_model"] is None
    assert codex["headroom_model"] == "gpt-5.6-luna"

    # 2. Write live usage record for Codex with gpt-5.6-terra.
    today_file = usage_dir / f"usage_codex-delegate_{now:%Y-%m-%d}.jsonl"
    _write_usage_record(
        today_file,
        [
            {
                "ts": (now - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
                "agent": "codex",
                "entrypoint": "delegate",
                "model": "gpt-5.6-terra",
                "outcome": "ok",
                "duration_s": 14.2,
            }
        ],
    )

    response = client.get("/api/runtime/agents")
    assert response.status_code == 200
    agents_json = response.json()["agents"]
    codex_json = next(a for a in agents_json if a["name"] == "codex")
    assert codex_json["default_model"] == "gpt-5.6-luna"
    assert codex_json["last_used_model"] == "gpt-5.6-terra"
    assert codex_json["headroom_model"] == "gpt-5.6-terra"


def test_agents_endpoint_picks_most_recent_model_when_multiple_records(tmp_path: Path, monkeypatch) -> None:
    usage_dir = tmp_path / "api_usage"
    now = datetime.now(UTC)
    monkeypatch.setattr(runtime_router, "USAGE_DIR", usage_dir)

    usage_file = usage_dir / f"usage_codex-dispatch_{now:%Y-%m-%d}.jsonl"
    _write_usage_record(
        usage_file,
        [
            {
                "ts": (now - timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
                "agent": "codex",
                "entrypoint": "dispatch",
                "model": "gpt-5.6-luna",
                "outcome": "ok",
                "duration_s": 10.0,
            },
            {
                "ts": (now - timedelta(minutes=10)).isoformat().replace("+00:00", "Z"),
                "agent": "codex",
                "entrypoint": "delegate",
                "model": "gpt-5.6-terra",
                "outcome": "ok",
                "duration_s": 8.5,
            },
        ],
    )

    response = client.get("/api/runtime/agents")
    assert response.status_code == 200
    codex_json = next(a for a in response.json()["agents"] if a["name"] == "codex")
    assert codex_json["last_used_model"] == "gpt-5.6-terra"
    assert codex_json["headroom_model"] == "gpt-5.6-terra"


def test_runtime_dashboard_queries_headroom_with_headroom_or_last_used_model() -> None:
    html = (DASHBOARDS_DIR / "runtime.html").read_text(encoding="utf-8")
    assert "agent.headroom_model || agent.last_used_model || agent.default_model" in html
    assert "<th>Headroom Model</th>" in html
    assert "Using last-used or default model" in html
