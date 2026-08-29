"""Fixture isolation for the #7269 step 12c MonitorContext cluster.

These routers must read decisions / hermes cron / ghost bundles / the
research registry through the request's MonitorContext, never through
deleted module-level Path globals.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.governance_router import router as governance_router
from scripts.api.hermes_cron_router import router as hermes_cron_router
from scripts.api.issues_router import router as issues_router
from scripts.api.knowledge_router import router as knowledge_router
from scripts.api.monitor_context import fixture_context
from scripts.api.reviewer_ghosts_router import router as reviewer_ghosts_router
from scripts.audit import check_adrs


def _cluster_client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(governance_router, prefix="/api/state/governance")
    app.include_router(hermes_cron_router, prefix="/api/hermes-cron")
    app.include_router(issues_router, prefix="/api/issues")
    app.include_router(knowledge_router, prefix="/api/knowledge")
    app.include_router(reviewer_ghosts_router, prefix="/api/state/reviewer-ghosts")
    return TestClient(app, raise_server_exceptions=False)


def test_fixture_governance_reads_only_context_decisions(tmp_path: Path) -> None:
    """A fixture app must not walk the production ADR tree or decisions file."""
    decisions_file = tmp_path / "docs" / "decisions" / "decisions.yaml"
    decisions_file.parent.mkdir(parents=True)
    decisions_file.write_text(
        """decisions:
  - id: dec-fixture-only
    status: active
    date: "2026-01-01"
    expires: "2026-01-01"
    scope: tooling
    title: "Fixture decision"
    reasoning: "Isolation"
    evidence: "Isolation"
    alternatives: []
    superseded_by: null
    depends_on: []
""",
        encoding="utf-8",
    )

    client = _cluster_client(tmp_path)
    response = client.get("/api/state/governance")
    assert response.status_code == 200
    body = response.json()
    assert [decision["id"] for decision in body["decisions"]["stale"]] == [
        "dec-fixture-only"
    ]
    assert body["decisions"]["total"] == 1
    # Production check_adrs still sees the live tree; the fixture must not.
    assert check_adrs.ADR_DIR.is_dir()
    assert body["adrs"] == {
        "total": 0,
        "stale_proposed_count": 0,
        "error_count": 0,
        "warning_count": 0,
        "broken_chains": [],
        "orphaned_refs": [],
        "promotion_candidates": [],
        "index": [],
    }


def test_fixture_hermes_cron_reads_batch_state_root(tmp_path: Path) -> None:
    cron_dir = tmp_path / "batch_state" / "hermes_cron"
    cron_dir.mkdir(parents=True)
    payload = {"summary": {"findings_total": 0}, "source": "fixture"}
    (cron_dir / "latest.json").write_text(
        '{"summary": {"findings_total": 0}, "source": "fixture"}',
        encoding="utf-8",
    )

    client = _cluster_client(tmp_path)
    response = client.get("/api/hermes-cron/latest")
    assert response.status_code == 200
    assert response.json() == payload


def test_fixture_reviewer_ghosts_reads_curriculum_root(tmp_path: Path) -> None:
    review_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1" / "review"
    review_dir.mkdir(parents=True)
    generated = datetime(2026, 4, 24, 12, 0, tzinfo=UTC)
    (review_dir / "colors-ghost-review-r1.yaml").write_text(
        yaml.safe_dump(
            {
                "slug": "colors",
                "round": 1,
                "reviewer_agent": "codex-tools",
                "ghost_findings": [
                    {
                        "dimension": "factual_accuracy",
                        "reviewer_find_anchor": "fixture-anchor",
                    }
                ],
                "generated_at": generated.isoformat(),
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    client = _cluster_client(tmp_path)
    response = client.get("/api/state/reviewer-ghosts/a1")
    assert response.status_code == 200
    body = response.json()
    assert body["total_ghost_findings"] == 1
    assert body["by_dimension"] == {"factual_accuracy": 1}
    assert body["recent"][0]["anchor"] == "fixture-anchor"


def test_fixture_issues_map_runs_gh_from_context_root(
    tmp_path: Path, monkeypatch
) -> None:
    captured: dict[str, Path] = {}

    def _fake_run(args, cwd=None, **_kwargs):
        captured["cwd"] = Path(cwd)
        class _Proc:
            returncode = 127
            stdout = ""
            stderr = "fixture gh unavailable"

        return _Proc()

    monkeypatch.setattr("scripts.api.issues_router.subprocess.run", _fake_run)
    client = _cluster_client(tmp_path)
    response = client.get("/api/issues/map")
    assert response.status_code == 200
    body = response.json()
    assert body["categories"] == {}
    assert "error" in body
    assert captured["cwd"] == tmp_path.resolve()


def test_fixture_knowledge_monitor_uses_context_root(tmp_path: Path) -> None:
    client = _cluster_client(tmp_path)
    response = client.get("/api/knowledge/monitor")
    assert response.status_code == 200
    body = response.json()
    assert body["discovery_enabled"] is False
    assert "lifecycle" in body
