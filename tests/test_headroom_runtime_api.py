"""Tests for local Headroom proxy stats exposed through /api/runtime."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

import scripts.api.runtime_router as runtime_router
from scripts.api.main import app


def test_headroom_stats_endpoint_summarizes_proxy_payload(monkeypatch) -> None:
    def fake_request(path: str, *, timeout_s: float) -> dict[str, Any]:
        assert timeout_s == 0.75
        if path == "/health":
            return {
                "status": "healthy",
                "ready": True,
                "version": "0.26.0",
                "uptime_seconds": 123.4,
                "config": {"backend": "anthropic"},
                "checks": {
                    "memory": {
                        "enabled": True,
                        "ready": True,
                        "status": "healthy",
                        "backend": "local",
                        "initialized": True,
                    }
                },
            }
        if path == "/stats":
            return {
                "summary": {
                    "api_requests": 10,
                    "primary_model": "claude-opus-4-8",
                    "compression": {
                        "requests_compressed": 8,
                        "avg_compression_pct": 6.5,
                        "best_compression_pct": 15.9,
                        "best_detail": "100 -> 84 tokens",
                        "total_tokens_removed": 1200,
                    },
                    "cost": {
                        "without_headroom_usd": 10.0,
                        "with_headroom_usd": 7.5,
                        "total_saved_usd": 2.5,
                        "savings_pct": 25.0,
                    },
                    "mcp": {"compressions": 3, "tokens_removed": 99, "retrievals": 1},
                },
                "persistent_savings": {
                    "lifetime": {
                        "requests": 11,
                        "tokens_saved": 1200,
                        "compression_savings_usd": 2.5,
                        "total_input_tokens": 10000,
                        "total_input_cost_usd": 7.5,
                    },
                    "display_session": {
                        "requests": 4,
                        "tokens_saved": 400,
                        "compression_savings_usd": 1.25,
                        "total_input_tokens": 5000,
                        "total_input_cost_usd": 3.75,
                        "savings_percent": 8.0,
                        "started_at": "2026-06-18T05:00:00Z",
                        "last_activity_at": "2026-06-18T06:00:00Z",
                    },
                },
                "prefix_cache": {
                    "totals": {
                        "cache_read_tokens": 20000,
                        "cache_write_tokens": 2000,
                        "hit_rate": 96.7,
                        "request_hit_rate": 98.7,
                        "bust_count": 2,
                        "net_savings_usd": 120.0,
                    }
                },
                "requests": {
                    "total": 10,
                    "cached": 9,
                    "failed": 0,
                    "rate_limited": 0,
                    "by_provider": {"anthropic": 10},
                    "by_model": {"claude-opus-4-8": 10},
                },
                "tokens": {
                    "input": 8800,
                    "output": 500,
                    "saved": 1200,
                    "total_before_compression": 10000,
                    "proxy_total_before_compression": 10000,
                    "savings_percent": 12.0,
                },
            }
        raise AssertionError(path)

    monkeypatch.setattr(runtime_router, "_request_headroom_json", fake_request)

    response = TestClient(app).get("/api/runtime/headroom/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["service"]["memory"] == {
        "enabled": True,
        "ready": True,
        "status": "healthy",
        "backend": "local",
        "initialized": True,
    }
    assert body["summary"]["tokens_saved"] == 1200
    assert body["summary"]["cost_saved_usd"] == 2.5
    assert body["session"]["tokens_saved"] == 400
    assert body["mcp"] == {"compressions": 3, "tokens_removed": 99, "retrievals": 1}
    assert body["prefix_cache"]["request_hit_rate"] == 98.7
    assert body["requests"]["by_model"] == {"claude-opus-4-8": 10}


def test_headroom_stats_endpoint_degrades_when_proxy_is_unavailable(monkeypatch) -> None:
    def fake_request(path: str, *, timeout_s: float) -> dict[str, Any]:
        raise OSError(f"{path} unavailable")

    monkeypatch.setattr(runtime_router, "_request_headroom_json", fake_request)

    response = TestClient(app).get("/api/runtime/headroom/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["status"] == "unavailable"
    assert len(body["errors"]) == 2
    assert body["summary"]["tokens_saved"] is None
