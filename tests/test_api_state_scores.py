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

import scripts.api.state_compute as state_compute
from scripts.api.state_router import _read_llm_qg_scores
from scripts.audit.llm_qg_store import DB_ENV_VAR, record_llm_qg


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


def test_read_llm_qg_marks_file_fallback_as_non_authoritative(tmp_path: Path) -> None:
    track_dir = tmp_path / "b1"
    module_dir = track_dir / "display-only"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("## Тест\n\nТекст.\n", encoding="utf-8")
    _write_llm_qg(
        module_dir,
        dims={"naturalness": 8.0},
        aggregate={"verdict": "PASS", "terminal_verdict": "PASS"},
    )

    observed = state_compute.read_llm_qg(track_dir, "display-only")

    assert observed is not None
    assert observed["_qg_source"] == "file_observation"
    assert observed["_qg_authoritative"] is False


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
