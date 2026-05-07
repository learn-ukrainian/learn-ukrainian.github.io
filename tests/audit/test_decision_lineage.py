"""Tests for the decision lineage scanner."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api import decisions_router
from scripts.api.main import app
from scripts.audit.decision_lineage import build_lineage_response


def _git(repo: Path, *args: str, date: str | None = None) -> None:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        env.pop(key, None)
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True)


def _commit(repo: Path, message: str, date: str) -> None:
    _git(repo, "add", ".", date=date)
    _git(repo, "commit", "-m", message, date=date)


def test_decision_lineage_finds_path_title_and_declared_id_aliases(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Decision Test")

    decisions = repo / "docs" / "decisions"
    decisions.mkdir(parents=True)
    notes = repo / "docs" / "notes.md"

    alpha = decisions / "2026-01-01-alpha-path.md"
    alpha.write_text(
        "# ADR-001: Alpha Path Decision\n\n"
        "**Status**: Accepted\n\n"
        "The alpha path is accepted.\n",
        encoding="utf-8",
    )
    beta = decisions / "2026-01-02-beta-routing.md"
    beta.write_text(
        "---\n"
        "decision_ids:\n"
        "  - BETA-42\n"
        "---\n"
        "# Beta Routing Decision\n\n"
        "Beta routing is accepted.\n",
        encoding="utf-8",
    )
    notes.write_text("Initial notes.\n", encoding="utf-8")
    _commit(repo, "Initial decision files", "2026-01-01T00:00:00+00:00")

    alpha.write_text(alpha.read_text("utf-8") + "\nPath touch follow-up.\n", encoding="utf-8")
    _commit(repo, "Touch alpha decision path (#101)", "2026-01-02T00:00:00+00:00")

    notes.write_text("Follow Alpha Path Decision in the builder.\n", encoding="utf-8")
    _commit(repo, "Reference Alpha Path Decision title", "2026-01-03T00:00:00+00:00")

    notes.write_text(notes.read_text("utf-8") + "Implement BETA-42 fallback.\n", encoding="utf-8")
    _commit(repo, "Reference BETA-42 declared ID PR #202", "2026-01-04T00:00:00+00:00")

    response = build_lineage_response(repo)
    by_file = {item["file_path"]: item for item in response["decisions"]}

    alpha_record = by_file["docs/decisions/2026-01-01-alpha-path.md"]
    beta_record = by_file["docs/decisions/2026-01-02-beta-routing.md"]
    alpha_subjects = {commit["subject"] for commit in alpha_record["commits"]}
    beta_subjects = {commit["subject"] for commit in beta_record["commits"]}

    assert "Touch alpha decision path (#101)" in alpha_subjects
    assert "Reference Alpha Path Decision title" in alpha_subjects
    assert "Reference BETA-42 declared ID PR #202" in beta_subjects
    assert alpha_record["prs"] == ["#101"]
    assert beta_record["prs"] == ["#202"]
    assert "ADR-001" in alpha_record["aliases"]
    assert "Alpha Path Decision" in alpha_record["aliases"]
    assert "BETA-42" in beta_record["aliases"]


def test_decision_id_filter_matches_alias(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Decision Test")

    decisions = repo / "docs" / "decisions"
    decisions.mkdir(parents=True)
    (decisions / "2026-01-01-alpha-path.md").write_text(
        "# ADR-001: Alpha Path Decision\n\nAccepted.\n",
        encoding="utf-8",
    )
    _commit(repo, "Initial ADR-001 (#303)", "2026-01-01T00:00:00+00:00")

    response = build_lineage_response(repo, decision_id="ADR-001")

    assert response["count"] == 1
    assert response["decisions"][0]["decision_id"] == "ADR-001"


def test_monitor_api_lineage_endpoint(monkeypatch):
    expected = {
        "count": 1,
        "decisions": [
            {
                "decision_id": "ADR-008",
                "file_path": "docs/decisions/example.md",
                "aliases": ["ADR-008"],
                "commits": [],
                "prs": [],
                "first_cited_at": None,
                "last_cited_at": None,
            }
        ],
    }
    seen: dict[str, str | None] = {}

    def fake_load_lineage(decision_id: str | None = None) -> dict:
        seen["decision_id"] = decision_id
        return expected

    monkeypatch.setattr(decisions_router, "_load_lineage", fake_load_lineage)

    response = TestClient(app).get("/api/decisions/lineage?decision_id=ADR-008")

    assert response.status_code == 200
    assert response.json() == expected
    assert seen["decision_id"] == "ADR-008"
