from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api import state_build, state_router
from scripts.api.main import app


def _write_module_files(root: Path, slug: str) -> None:
    module_dir = root / "curriculum" / "l2-uk-en" / "b2" / slug
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.md").write_text("# Module\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")

    mdx_dir = root / "site" / "src" / "content" / "docs" / "b2"
    mdx_dir.mkdir(parents=True, exist_ok=True)
    (mdx_dir / f"{slug}.mdx").write_text("---\ntitle: Module\n---\n", encoding="utf-8")


def test_compute_module_range_status_reports_complete_and_remaining(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(state_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(state_build, "CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en")
    monkeypatch.setattr(
        state_build,
        "get_plan_slugs",
        lambda track_id: [(32, "m32"), (33, "m33"), (34, "m34")],
    )

    _write_module_files(tmp_path, "m32")
    _write_module_files(tmp_path, "m33")
    score_dir = tmp_path / "docs" / "audits"
    score_dir.mkdir(parents=True)
    (score_dir / "b2-current-llm-scores-test.md").write_text(
        "B2 M32 `m32`,9/10,B+,Yes,done\n",
        encoding="utf-8",
    )
    (score_dir / "a1-current-llm-scores-test.md").write_text(
        "A1 M33 `m33`,9/10,B+,Yes,wrong track\n",
        encoding="utf-8",
    )

    result = state_build.compute_module_range_status(
        "b2",
        {"path": "b2"},
        start=32,
        end=34,
    )

    assert result["deterministic"] is True
    assert result["total"] == 3
    assert result["complete"] == 1
    assert result["content_complete"] == 2
    assert result["score_persisted"] == 1
    assert result["incomplete"] == 2
    assert result["remaining"] == [
        {"num": 33, "slug": "m33", "missing": ["score"]},
        {
            "num": 34,
            "slug": "m34",
            "missing": ["module", "activities", "vocabulary", "mdx", "score"],
        },
    ]
    assert result["modules"][0]["status"] == "complete"
    assert result["modules"][1]["status"] == "partial"
    assert result["modules"][2]["status"] == "missing"


def test_compute_module_range_status_accepts_unpadded_score_module_numbers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(state_build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(state_build, "CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en")
    monkeypatch.setattr(state_build, "get_plan_slugs", lambda track_id: [(7, "m7")])

    _write_module_files(tmp_path, "m7")
    score_dir = tmp_path / "docs" / "audits"
    score_dir.mkdir(parents=True)
    (score_dir / "b2-current-llm-scores-test.md").write_text(
        "B2 M7 `m7`,9/10,B+,Yes,done\n",
        encoding="utf-8",
    )

    result = state_build.compute_module_range_status(
        "b2",
        {"path": "b2"},
        start=7,
        end=7,
    )

    assert result["complete"] == 1
    assert result["remaining"] == []


def test_compute_module_range_status_rejects_invalid_ranges() -> None:
    with pytest.raises(ValueError, match="positive"):
        state_build.compute_module_range_status("b2", {"path": "b2"}, start=0, end=1)

    with pytest.raises(ValueError, match="greater than or equal"):
        state_build.compute_module_range_status("b2", {"path": "b2"}, start=2, end=1)


def test_module_range_status_route_returns_computed_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "track": "b2",
        "range": {"start": 32, "end": 41},
        "total": 10,
        "complete": 10,
        "content_complete": 10,
        "score_persisted": 10,
        "incomplete": 0,
        "remaining": [],
        "modules": [],
        "deterministic": True,
        "source": "test",
    }
    calls: list[tuple[str, str, int, int]] = []

    def fake_compute(
        track_id: str,
        level_cfg: dict,
        *,
        start: int,
        end: int,
    ) -> dict:
        calls.append((track_id, level_cfg["path"], start, end))
        return payload

    state_router.cache_invalidate("module_range_b2_32_41")
    monkeypatch.setattr(state_router, "compute_module_range_status", fake_compute)
    client = TestClient(app)

    response = client.get("/api/state/module-range/b2?start=32&end=41")

    assert response.status_code == 200
    assert response.json() == payload
    assert calls == [("b2", "b2", 32, 41)]


def test_module_range_status_route_rejects_inverted_range() -> None:
    client = TestClient(app)

    response = client.get("/api/state/module-range/b2?start=41&end=32")

    assert response.status_code == 422
    assert response.json() == {"error": "end must be greater than or equal to start"}
