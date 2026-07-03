"""Tests for the /api/state/scores endpoints + the llm_qg score reader.

The scores view is how the user watches the seminar quality-gate prototype
converge to >=8 (docs/folk-epic/seminar-quality-gate-design.md). It reads
per-module ``llm_qg.json`` (``.aggregate`` + ``.dimensions``) plus the audit
status cache, and must degrade gracefully when a module has not been scored.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.state_router as state_router
from scripts.api.state_router import _read_llm_qg_scores
from scripts.audit.llm_qg_store import DB_ENV_VAR, record_llm_qg

client = TestClient(api_main.app, raise_server_exceptions=False)


def _set_mtime_ns(path: Path, value: int) -> None:
    os.utime(path, ns=(value, value))


def _write_llm_qg(module_dir: Path, *, dims: dict[str, float], aggregate: dict) -> None:
    module_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "dimensions": {d: {"score": s, "evidence": "「x」", "verdict": "PASS"} for d, s in dims.items()},
        "aggregate": aggregate,
    }
    (module_dir / "llm_qg.json").write_text(json.dumps(payload), encoding="utf-8")


# --------------------------------------------------------------------------- #
# _read_llm_qg_scores — the pure reader
# --------------------------------------------------------------------------- #


def test_read_scores_parses_dims_and_aggregate(tmp_path: Path) -> None:
    _write_llm_qg(
        tmp_path,
        dims={"pedagogical": 7.0, "engagement": 6.8, "beauty": 8.0},
        aggregate={
            "verdict": "REVISE",
            "terminal_verdict": "REVISE",
            "min_score": 6.8,
            "min_dim": "engagement",
            "failing_dims": ["engagement", "pedagogical"],
            "warning_dims": [],
        },
    )
    out = _read_llm_qg_scores(tmp_path)
    assert out["dimensions"] == {"pedagogical": 7.0, "engagement": 6.8, "beauty": 8.0}
    assert out["aggregate"]["min_dim"] == "engagement"
    assert out["aggregate"]["terminal_verdict"] == "REVISE"
    # beauty surfaces generically — no code change needed when the dim lands.
    assert "beauty" in out["dimensions"]


def test_read_scores_missing_file_degrades(tmp_path: Path) -> None:
    out = _read_llm_qg_scores(tmp_path / "does-not-exist")
    assert out == {"aggregate": None, "dimensions": {}}


def test_read_scores_malformed_json_degrades(tmp_path: Path) -> None:
    (tmp_path / "llm_qg.json").write_text("{ not json", encoding="utf-8")
    out = _read_llm_qg_scores(tmp_path)
    assert out == {"aggregate": None, "dimensions": {}}


def test_read_scores_ignores_stale_file_fallback(tmp_path: Path) -> None:
    module_dir = tmp_path / "b1" / "stale-mod"
    _write_llm_qg(
        module_dir,
        dims={"naturalness": 8.0},
        aggregate={
            "verdict": "PASS",
            "terminal_verdict": "PASS",
            "min_score": 8.0,
            "min_dim": "naturalness",
            "failing_dims": [],
            "warning_dims": [],
        },
    )
    (module_dir / "module.md").write_text("## Changed\n\nНовий текст.\n", encoding="utf-8")
    _set_mtime_ns(module_dir / "llm_qg.json", 1_000_000_000)
    _set_mtime_ns(module_dir / "module.md", 2_000_000_000)

    out = _read_llm_qg_scores(module_dir)

    assert out == {"aggregate": None, "dimensions": {}}


def test_read_scores_corrupt_db_degrades(tmp_path: Path, monkeypatch) -> None:
    bad_db = tmp_path / "bad.db"
    bad_db.write_text("not sqlite", encoding="utf-8")
    monkeypatch.setenv(DB_ENV_VAR, str(bad_db))
    module_dir = tmp_path / "b1" / "unscored"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("## Тест\n\nЧекайте на номер.\n", encoding="utf-8")

    out = _read_llm_qg_scores(module_dir)

    assert out == {"aggregate": None, "dimensions": {}}


def test_read_scores_uses_persisted_current_qg_without_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(DB_ENV_VAR, str(tmp_path / "llm_qg.db"))
    module_dir = tmp_path / "b1" / "stored-mod"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("## Тест\n\nЧекайте на номер.\n", encoding="utf-8")
    record_llm_qg(
        level="b1",
        slug="stored-mod",
        module_dir=module_dir,
        payload={
            "dimensions": {"naturalness": {"score": 6.5, "verdict": "REVISE"}},
            "aggregate": {
                "verdict": "REVISE",
                "terminal_verdict": "PASS",
                "min_score": 6.5,
                "min_dim": "naturalness",
                "failing_dims": ["naturalness"],
                "warning_dims": ["naturalness"],
            },
        },
        gate_version="test.v1",
    )

    out = _read_llm_qg_scores(module_dir)

    assert out["dimensions"] == {"naturalness": 6.5}
    assert out["aggregate"]["min_dim"] == "naturalness"


# --------------------------------------------------------------------------- #
# /api/state/scores/{track}[/{slug}] — the endpoints
# --------------------------------------------------------------------------- #


def _fake_track(tmp_path: Path, monkeypatch) -> None:
    """Wire a one-path fake 'demo' track with a scored + an unscored module."""
    track_dir = tmp_path / "demo"
    _write_llm_qg(
        track_dir / "scored-mod",
        dims={"pedagogical": 7.0, "engagement": 6.8},
        aggregate={
            "verdict": "REVISE",
            "terminal_verdict": "REVISE",
            "min_score": 6.8,
            "min_dim": "engagement",
            "failing_dims": ["engagement"],
            "warning_dims": [],
        },
    )
    (track_dir / "unscored-mod").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(state_router, "LEVELS", [{"id": "demo", "name": "Demo", "path": "demo"}])
    monkeypatch.setattr(state_router, "CURRICULUM_ROOT", tmp_path)
    monkeypatch.setattr(
        state_router, "get_plan_slugs", lambda _t: [(1, "scored-mod"), (2, "unscored-mod")]
    )


def test_scores_track_lists_modules_with_scored_flag(tmp_path: Path, monkeypatch) -> None:
    _fake_track(tmp_path, monkeypatch)
    body = client.get("/api/state/scores/demo").json()
    assert body["track"] == "demo"
    assert body["count"] == 2
    assert body["scored"] == 1
    by_slug = {m["slug"]: m for m in body["modules"]}
    assert by_slug["scored-mod"]["scored"] is True
    assert by_slug["scored-mod"]["dimensions"]["engagement"] == 6.8
    assert by_slug["scored-mod"]["aggregate"]["min_dim"] == "engagement"
    assert by_slug["unscored-mod"]["scored"] is False
    assert by_slug["unscored-mod"]["aggregate"] is None
    assert "meta" in body


def test_scores_one_module(tmp_path: Path, monkeypatch) -> None:
    _fake_track(tmp_path, monkeypatch)
    body = client.get("/api/state/scores/demo/scored-mod").json()
    assert body["slug"] == "scored-mod"
    assert body["dimensions"]["pedagogical"] == 7.0
    assert body["aggregate"]["terminal_verdict"] == "REVISE"


def test_scores_unknown_track_404(tmp_path: Path, monkeypatch) -> None:
    _fake_track(tmp_path, monkeypatch)
    assert client.get("/api/state/scores/nope").status_code == 404


def test_scores_unknown_slug_404(tmp_path: Path, monkeypatch) -> None:
    _fake_track(tmp_path, monkeypatch)
    assert client.get("/api/state/scores/demo/nope").status_code == 404
