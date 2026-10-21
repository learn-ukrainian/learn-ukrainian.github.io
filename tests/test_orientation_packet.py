"""Bounded orientation packet and lane-sized Work projection."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.work_router import projection_cache_key
from scripts.orientation_packet import PACKET_MAX_BYTES, build_packet, json_bytes
from scripts.work.normalize import build_projection
from scripts.work.sources_public import SectionResult

CLIENT = TestClient(app)


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


def _public_projection():
    payload = build_projection(
        {
            "issues": SectionResult(
                "issues", "ok", payload=[{"number": 10917, "title": "Fixture", "state": "OPEN"}], count=1
            )
        }
    )
    payload["items"][0]["projections"]["stream"] = {"status": "homed", "streams": ["monitor"]}
    payload["sources"] = payload["sources"][:1]
    payload["sources"][0]["reason"] = ""
    return payload


def test_projection_records_unassigned_pr(monkeypatch):
    import scripts.api.work_router as work_router

    payload = _public_projection()
    item = payload["items"][0]
    item["resource_kind"] = "pr"
    item["work_id"] = "wp1:pr:10917"
    payload["attention"][0]["work_id"] = item["work_id"]
    item["projections"]["stream"] = {"status": "n/a"}
    payload["denominator"].update(prs_open=1, streams_complete=True, omissions=[])
    before = deepcopy(payload)
    monkeypatch.setattr(work_router, "cache_get_with_age", lambda *_a, **_kw: (payload, 1.0))
    response = CLIENT.get("/api/work/v1/projection?stream=monitor")
    assert response.status_code == 200
    assert len(response.content) <= PACKET_MAX_BYTES
    body = response.json()
    assert body["items"] == []
    omission = body["denominator"]["omissions"][-1]
    assert omission["work_id"] == "wp1:pr:10917"
    assert omission["locator"] == "/api/work/v1/projection#/items/0"
    assert body["denominator"]["streams_complete"] is False
    assert payload == before


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
