"""Tests for /api/state/reviewer-ghosts/{track} (GH #1529 P3).

Seeds an on-disk fixture tree of ghost bundles, then exercises the router
directly with FastAPI's ``TestClient`` — no running API server required.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


def _write_bundle(
    curriculum_root: Path,
    *,
    level: str,
    slug: str,
    round_num: int,
    reviewer_agent: str,
    ghost_findings: list[dict],
    generated_at: datetime,
    top_dimension: str = "mixed",
    content_sha256: str = "sha",
) -> Path:
    review_dir = curriculum_root / level / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    path = review_dir / f"{slug}-ghost-review-r{round_num}.yaml"
    payload = {
        "slug": slug,
        "round": round_num,
        "dimension": top_dimension,
        "reviewer_agent": reviewer_agent,
        "ghost_findings": ghost_findings,
        "content_sha256": content_sha256,
        "generated_at": generated_at.isoformat(),
    }
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), "utf-8"
    )
    return path


def _ghost_finding(
    *,
    dimension: str,
    anchor: str,
    severity: str = "major",
    normalized_id: str = "nf_test",
) -> dict:
    return {
        "finding_id": normalized_id,
        "dimension": dimension,
        "severity": severity,
        "location": "test location",
        "issue": "test issue",
        "reviewer_find_anchor": anchor,
        "anchor_validation": "anchor_missing",
        "raw_fix": {"find": anchor, "replace": "fixed"},
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Mount the reviewer_ghosts_router against a tmp curriculum root."""
    from api import reviewer_ghosts_router as rgr

    monkeypatch.setattr(rgr, "CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en")

    app = FastAPI()
    app.include_router(rgr.router, prefix="/api/state/reviewer-ghosts")
    return TestClient(app)


@pytest.fixture
def seeded_curriculum(tmp_path: Path) -> Path:
    """Seed a small fixture tree: 2 slugs × 2-3 bundles across dimensions."""
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"

    base_time = datetime(2026, 4, 24, 12, 0, 0, tzinfo=UTC)

    # a1/colors round 1 — 2 factual ghosts, codex reviewer, older
    _write_bundle(
        curriculum_root,
        level="a1",
        slug="colors",
        round_num=1,
        reviewer_agent="codex-tools",
        top_dimension="factual_accuracy",
        ghost_findings=[
            _ghost_finding(
                dimension="factual_accuracy", anchor="ghost-anchor-1", normalized_id="nf_a"
            ),
            _ghost_finding(
                dimension="factual_accuracy", anchor="ghost-anchor-2", normalized_id="nf_b"
            ),
        ],
        generated_at=base_time - timedelta(hours=2),
    )
    # a1/colors round 2 — 1 honesty ghost, claude reviewer, newer
    _write_bundle(
        curriculum_root,
        level="a1",
        slug="colors",
        round_num=2,
        reviewer_agent="claude-tools",
        top_dimension="honesty",
        ghost_findings=[
            _ghost_finding(
                dimension="honesty", anchor="ghost-anchor-3", normalized_id="nf_c"
            ),
        ],
        generated_at=base_time - timedelta(minutes=30),
    )
    # a1/sounds round 1 — 1 factual ghost, codex reviewer, newest
    _write_bundle(
        curriculum_root,
        level="a1",
        slug="sounds",
        round_num=1,
        reviewer_agent="codex-tools",
        top_dimension="factual_accuracy",
        ghost_findings=[
            _ghost_finding(
                dimension="factual_accuracy", anchor="ghost-anchor-4", normalized_id="nf_d"
            ),
        ],
        generated_at=base_time,
    )
    return curriculum_root


# ---------- no-filter aggregates ----------


def test_aggregate_across_track_no_filters(
    client: TestClient, seeded_curriculum: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from api import reviewer_ghosts_router as rgr

    monkeypatch.setattr(rgr, "CURRICULUM_ROOT", seeded_curriculum)

    response = client.get("/api/state/reviewer-ghosts/a1")
    assert response.status_code == 200
    body = response.json()

    assert body["track"] == "a1"
    assert body["total_ghost_findings"] == 4
    assert body["by_dimension"] == {"factual_accuracy": 3, "honesty": 1}
    assert body["by_reviewer_agent"] == {"codex-tools": 3, "claude-tools": 1}
    # Newest first — the a1/sounds bundle at base_time is the newest.
    assert body["recent"][0]["slug"] == "sounds"
    assert body["recent"][0]["dimension"] == "factual_accuracy"
    assert len(body["recent"]) == 4


# ---------- slug filter ----------


def test_slug_filter_narrows_to_one_module(
    client: TestClient, seeded_curriculum: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from api import reviewer_ghosts_router as rgr

    monkeypatch.setattr(rgr, "CURRICULUM_ROOT", seeded_curriculum)

    response = client.get("/api/state/reviewer-ghosts/a1?slug=colors")
    assert response.status_code == 200
    body = response.json()

    # colors has 2 factual + 1 honesty = 3 findings across 2 bundles
    assert body["total_ghost_findings"] == 3
    assert body["by_dimension"] == {"factual_accuracy": 2, "honesty": 1}
    assert body["by_reviewer_agent"] == {"codex-tools": 2, "claude-tools": 1}
    # sounds entries must not appear
    assert all(row["slug"] == "colors" for row in body["recent"])


# ---------- since filter ----------


def test_since_filter_excludes_older_bundles(
    client: TestClient, seeded_curriculum: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from api import reviewer_ghosts_router as rgr

    monkeypatch.setattr(rgr, "CURRICULUM_ROOT", seeded_curriculum)

    # Cutoff excludes the 2h-old a1/colors r1 bundle (2 findings), keeps
    # the 30-min-old a1/colors r2 (1) + base_time a1/sounds r1 (1) = 2.
    cutoff = (datetime(2026, 4, 24, 12, 0, 0, tzinfo=UTC) - timedelta(hours=1))
    response = client.get(
        "/api/state/reviewer-ghosts/a1", params={"since": cutoff.isoformat()}
    )
    assert response.status_code == 200
    body = response.json()

    assert body["total_ghost_findings"] == 2
    assert body["by_dimension"] == {"factual_accuracy": 1, "honesty": 1}
    # No factual_accuracy=3 leak from the pre-cutoff bundle
    assert "codex-tools" in body["by_reviewer_agent"]
    # All remaining rows are at-or-after cutoff
    for row in body["recent"]:
        parsed = datetime.fromisoformat(row["generated_at"])
        assert parsed >= cutoff


# ---------- filter edge cases ----------


def test_since_rejects_invalid_iso8601(
    client: TestClient, seeded_curriculum: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from api import reviewer_ghosts_router as rgr

    monkeypatch.setattr(rgr, "CURRICULUM_ROOT", seeded_curriculum)

    response = client.get("/api/state/reviewer-ghosts/a1?since=not-a-date")
    assert response.status_code == 400
    assert "ISO-8601" in response.json()["detail"]


def test_unknown_track_returns_404(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from api import reviewer_ghosts_router as rgr

    monkeypatch.setattr(
        rgr, "CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en"
    )
    response = client.get("/api/state/reviewer-ghosts/not-a-real-track")
    assert response.status_code == 404


def test_empty_track_returns_zero_aggregates(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Valid track id but no ghost bundles on disk.
    from api import reviewer_ghosts_router as rgr

    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    (curriculum_root / "a1" / "review").mkdir(parents=True)
    monkeypatch.setattr(rgr, "CURRICULUM_ROOT", curriculum_root)

    response = client.get("/api/state/reviewer-ghosts/a1")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "track": "a1",
        "total_ghost_findings": 0,
        "by_dimension": {},
        "by_reviewer_agent": {},
        "recent": [],
    }
