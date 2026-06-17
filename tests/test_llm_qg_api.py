"""Tests for LLM quality-gate Monitor API projections."""

from __future__ import annotations

from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.state_router as state_router

client = TestClient(api_main.app, raise_server_exceptions=False)


def _folk_scored_module(body: dict) -> dict:
    return next(module for module in body["modules"] if module["has_llm_qg"])


def test_folk_llm_qg_track_returns_scored_modules():
    resp = client.get("/api/state/llm-qg/folk")
    body = resp.json()

    assert resp.status_code == 200
    assert body["track"] == "folk"
    assert body["summary"]["scored"] >= 6
    assert body["summary"]["total"] == len(state_router.get_plan_slugs("folk"))
    assert len(body["modules"]) == body["summary"]["total"]

    scored = [module for module in body["modules"] if module["has_llm_qg"]]
    assert scored
    for module in scored:
        assert isinstance(module["dimensions"], dict)
        assert len(module["dimensions"]) >= 5
        assert all(isinstance(score, (int, float)) for score in module["dimensions"].values())


def test_track_with_no_llm_qg_artifacts_returns_unscored_modules():
    resp = client.get("/api/state/llm-qg/a2")
    body = resp.json()

    assert resp.status_code == 200
    assert body["track"] == "a2"
    assert body["summary"]["scored"] == 0
    assert body["summary"]["unscored"] == body["summary"]["total"]
    assert all(module["has_llm_qg"] is False for module in body["modules"])
    assert all(module["dimensions"] is None for module in body["modules"])


def test_llm_qg_unknown_track_returns_404():
    resp = client.get("/api/state/llm-qg/no-such-track")

    assert resp.status_code == 404
    assert resp.json() == {"error": "Track 'no-such-track' not found"}


def test_llm_qg_verbose_includes_evidence_default_omits_it():
    compact = _folk_scored_module(client.get("/api/state/llm-qg/folk").json())
    verbose = _folk_scored_module(client.get("/api/state/llm-qg/folk?verbose=true").json())

    compact_dim = next(iter(compact["dimensions"].values()))
    verbose_dim = next(iter(verbose["dimensions"].values()))

    assert isinstance(compact_dim, (int, float))
    assert isinstance(verbose_dim, dict)
    assert "evidence" in verbose_dim


def test_module_slug_compact_projection_includes_llm_qg_block():
    track = client.get("/api/state/llm-qg/folk").json()
    slug = _folk_scored_module(track)["slug"]

    body = client.get(f"/api/state/module/folk/slug/{slug}").json()

    assert body["slug"] == slug
    assert body["llm_qg"] is not None
    assert body["llm_qg"]["verdict"] is not None
    assert isinstance(body["llm_qg"]["dimensions"], dict)
    assert all(isinstance(score, (int, float)) for score in body["llm_qg"]["dimensions"].values())
