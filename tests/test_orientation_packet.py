"""Bounded orientation packet and lane-sized Work projection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.driver_state as driver_state
from scripts.api.main import app
from scripts.api.work_router import projection_cache_key
from scripts.fleet_comms.cold_start_board import MAX_BOARD_BYTES
from scripts.inbox_pending import probe
from scripts.orchestration.issue_stream_audit import load_registry
from scripts.orientation_packet import PACKET_MAX_BYTES, build_packet, cap_projection, json_bytes

CLIENT = TestClient(app)


def test_packet_bound_matches_cold_start_board():
    assert PACKET_MAX_BYTES == MAX_BOARD_BYTES == 16384


def test_probe_rejects_limits_before_opening_a_store():
    for limit in (0, 501, True, "5"):
        result = probe("grok-monitor", limit=limit)
        assert result["probe"] == "unknown"
        assert result["ids"] == []


def _state(tmp_path: Path, epic: str, body: str) -> None:
    directory = tmp_path / ".claude" / f"{epic}-epic"
    directory.mkdir(parents=True)
    (directory / "DRIVER-STATE.md").write_text(body, encoding="utf-8")


def _orders(count: int = 1) -> dict:
    ids = [f"message_{index:032x}" for index in range(count)]
    return {"probe": "ok", "count": count, "ids": ids, "truncated": False}


def _session() -> dict:
    return {
        "hash": "abc",
        "bytes": 12,
        "locator": "docs/session-state/current.md",
        "sections": {"agent": "monitor"},
        "observed_at": "2026-10-17T00:00:00Z",
        "freshness": "live",
    }


@pytest.mark.parametrize("epic", sorted(load_registry()))
def test_every_registered_lane_packet_fits(epic, tmp_path, monkeypatch):
    monkeypatch.delenv("LU_DRIVER_MIN_WORKERS", raising=False)
    _state(
        tmp_path,
        epic,
        "## Current goals\n- keep the lane inside one packet\n"
        "## Next\n- read the packet\n"
        "## Holds\n- a public hold\n"
        "## Stops\n- a public stop\n",
    )
    packet = build_packet(
        epic,
        root=tmp_path,
        orders=_orders(),
        session=_session(),
    )
    raw = json_bytes(packet, newline=True)
    assert len(raw) <= PACKET_MAX_BYTES
    assert packet["epic"] == epic
    assert set(packet["runtime"]) == {"worker_target"}
    assert packet["runtime"]["worker_target"] == "UNKNOWN"
    assert [row["id"] for row in packet["holds"]] == ["hold-1"]
    assert [row["id"] for row in packet["stops"]] == ["stop-1"]
    assert [row["id"] for row in packet["goals"]] == ["goal-1"]
    assert [row["id"] for row in packet["orders"]] == ["message_" + f"{0:032x}"]
    assert "markdown" not in packet["session"]
    assert packet["freshness"] == "live"
    assert packet["complete"] is True
    names = {source["name"] for source in packet["sources"]}
    assert {"driver_state", "orders", "session", "open_prs", "live_workers", "plane"} <= names


def test_overflow_keeps_hold_stop_and_goal_ids(tmp_path, monkeypatch):
    monkeypatch.delenv("LU_DRIVER_MIN_WORKERS", raising=False)
    holds = "\n".join(f"- hold {index} " + ("h" * 400) for index in range(6))
    stops = "\n".join(f"- stop {index} " + ("s" * 400) for index in range(6))
    goals = "\n".join(f"- goal {index} " + ("g" * 400) for index in range(6))
    nxt = "\n".join(f"- next {index} " + ("n" * 400) for index in range(6))
    _state(
        tmp_path,
        "monitor",
        f"## Current goals\n{goals}\n## Next\n{nxt}\n## Holds\n{holds}\n## Stops\n{stops}\n",
    )
    packet = build_packet(
        "monitor",
        root=tmp_path,
        orders=_orders(400),
        session=_session(),
    )
    assert len(json_bytes(packet, newline=True)) <= PACKET_MAX_BYTES
    assert [row["id"] for row in packet["holds"]] == [f"hold-{index}" for index in range(1, 7)]
    assert [row["id"] for row in packet["stops"]] == [f"stop-{index}" for index in range(1, 7)]
    assert [row["id"] for row in packet["goals"]] == [f"goal-{index}" for index in range(1, 7)]
    assert packet["orders"]
    assert len(packet["orders"]) < 400
    assert packet["complete"] is False
    assert packet["omitted"]["count"] > 0


def test_cli_prints_a_bounded_packet(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("LU_DRIVER_MIN_WORKERS", raising=False)
    monkeypatch.setattr(driver_state, "_repo_root", lambda start=None: tmp_path)
    _state(tmp_path, "monitor", "## Current goals\n- one public goal\n")
    assert driver_state.main(["packet", "--epic", "monitor"]) == 0
    text = capsys.readouterr().out
    packet = json.loads(text)
    assert packet["epic"] == "monitor"
    assert text.endswith("\n")
    assert len(text.encode()) <= PACKET_MAX_BYTES
    assert set(packet["runtime"]) == {"worker_target"}


def test_cap_projection_keeps_attention_prefix_and_does_not_mutate():
    items = []
    attention = []
    for index in range(40):
        work_id = f"wp1:issue:{index}"
        items.append({"work_id": work_id, "title": "t" * 500})
        attention.append({"work_id": work_id, "attention_rank": index})
    payload = {"items": items, "attention": attention, "denominator": {"omissions": []}}
    capped = cap_projection(payload)
    assert len(json_bytes(capped)) <= PACKET_MAX_BYTES
    assert len(capped["items"]) < len(items)
    assert capped["items"][0]["work_id"] == "wp1:issue:0"
    assert capped["denominator"]["omissions"][-1] == {
        "class": "orientation_bound",
        "reason": "lane_projection_bytes",
        "count": len(items) - len(capped["items"]),
    }
    assert len(payload["items"]) == 40
    assert "omissions" not in payload or payload["denominator"]["omissions"] == []


def test_projection_requires_one_known_lane():
    missing = CLIENT.get("/api/work/v1/projection")
    assert missing.status_code == 400
    assert missing.json()["detail"]["error"] == "lane_required"
    unknown = CLIENT.get("/api/work/v1/projection?stream=not-a-lane")
    assert unknown.status_code == 400
    assert unknown.json()["detail"]["error"] == "unknown_stream"
    blank = CLIENT.get("/api/work/v1/projection?stream=")
    assert blank.status_code == 400
    assert blank.json()["detail"]["error"] == "invalid_saved_view"
    forbidden = CLIENT.get("/api/work/v1/projection?q=secret")
    assert forbidden.status_code == 400
    assert forbidden.json()["detail"]["error"] == "invalid_saved_view"


def test_projection_registry_failure_is_closed(monkeypatch):
    import scripts.api.work_router as work_router

    monkeypatch.setattr(work_router, "_known_streams", lambda *_args, **_kwargs: None)
    response = CLIENT.get("/api/work/v1/projection?stream=monitor")
    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "registry_unavailable"


def test_projection_lane_filter_caps_and_leaves_the_cache(monkeypatch):
    import scripts.api.work_router as work_router

    items = []
    attention = []
    for index in range(30):
        work_id = f"wp1:issue:{index}"
        lane = "infra-harness" if index % 2 == 0 else "devops"
        items.append(
            {
                "work_id": work_id,
                "title": "t" * 2000,
                "projections": {"stream": {"streams": [lane]}},
            }
        )
        attention.append({"work_id": work_id, "attention_rank": index})
    payload = {"items": items, "attention": attention, "denominator": {"omissions": []}, "cache_age_s": 1.0}
    monkeypatch.setattr(work_router, "cache_get_with_age", lambda *_args, **_kwargs: (payload, 1.0))
    monkeypatch.setattr(work_router, "_known_streams", lambda *_args, **_kwargs: ["devops", "infra-harness"])
    response = CLIENT.get("/api/work/v1/projection?stream=infra-harness")
    assert response.status_code == 200
    body = response.json()
    assert len(response.content) <= PACKET_MAX_BYTES
    assert body["items"]
    assert all(item["projections"]["stream"]["streams"] == ["infra-harness"] for item in body["items"])
    assert len(body["items"]) < 15
    assert body["denominator"]["omissions"][-1]["reason"] == "lane_projection_bytes"
    assert len(payload["items"]) == 30
    assert payload["items"][1]["projections"]["stream"]["streams"] == ["devops"]
    assert payload["denominator"]["omissions"] == []
    # The warm key stays unscoped. A lane query must not mint a second cache entry.
    assert "stream" not in projection_cache_key({})
