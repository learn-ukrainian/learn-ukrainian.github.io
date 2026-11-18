"""Response and containment regressions for artifact path handling (#9648)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from lu_machinery.api import docs_router
from lu_machinery.api.monitor_context import MonitorContext, fixture_context, get_ctx

from scripts.project_api import artifacts_router


@pytest.fixture()
def artifact_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MonitorContext:
    files = {
        "docs/handoffs/session.md": (
            "---\nclass: handoff\nstatus: green\ndate: 2026-10-01\n"
            "author: codex\ntitle: 'Session: one'\nkpi_summary: complete\n"
            "related_issues: '#9648, 42, invalid'\nrelated_prs: '11, 12'\n"
            "agents: 'codex, claude'\n---\n# Ignored title\n"
        ),
        "docs/proposals/report.HTML": (
            '<META name="report-class" content="proposal" />\n'
            '<meta name="report-date" content="2026-09-01">\n'
            '<meta name="report-title" content="Proposal">\n'
            '<meta name="report-author" content="team">\n'
            '<meta name="report-kpi-summary" content="ready">\n'
            '<meta name="report-related-issues" content="7, #8">\n'
        ),
        "docs/research/nested/notes.md": "# Plain notes\n\nNo frontmatter.\n",
        "audit/fallback.md": "---\nstatus: false\ntitle: null\n---\n# Fallback title\n",
        "docs/research/malformed.md": "---\ntitle: [broken\n---\n# Malformed title\n",
        "docs/research/long.md": "# Head title\n" + "body\n" * 2000 + "# Late title\n",
        "docs/archive/old.md": "# Excluded archive\n",
        "docs/resources/podcasts/raw/episode.md": "# Excluded raw source\n",
        "docs/research/.hidden.md": "# Hidden file\n",
        "docs/research/.hidden/note.md": "# Hidden directory\n",
        "docs/research/ignored.txt": "# Wrong extension\n",
    }
    for relative, content in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        os.utime(path, ns=(946684800000000000, 946684800000000000))

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 3, tzinfo=UTC)

    # Only generated_at is request-time dependent; freeze it for byte comparison.
    monkeypatch.setattr(docs_router, "datetime", FrozenDatetime)
    return fixture_context(tmp_path)


@pytest.mark.parametrize(
    ("query", "filters"),
    [
        ("", {}),
        ("?type=html", {"types": ("html",)}),
        ("?type=md", {"types": ("md",)}),
        (
            "?class=handoff&status=green&author=codex&date_from=2026-10-01",
            {"class_filter": "handoff", "status": "green", "author": "codex", "date_from": "2026-10-01"},
        ),
        ("?date_from=2026-09-01", {"date_from": "2026-09-01"}),
    ],
)
def test_artifacts_response_bytes_match_uncached_collector(
    artifact_context: MonitorContext, monkeypatch: pytest.MonkeyPatch, query: str, filters: dict
) -> None:
    """The cached, request-filtered route must serialise exactly what the collector returns for those filters.

    A defect class this also pins: the stat-fingerprinted cache serving a list from before a new file was written.
    """
    monkeypatch.setattr(artifacts_router, "_ARTIFACT_FINGERPRINT_TTL_S", 0.0)
    app = FastAPI()
    app.include_router(artifacts_router.router, prefix="/api/artifacts")
    app.dependency_overrides[get_ctx] = lambda: artifact_context
    with TestClient(app) as client:
        with monkeypatch.context() as baseline:
            # Restore the collector's original relative-path operation, including
            # resolved containment, to produce the pre-change response on the same inputs.
            baseline.setattr(docs_router, "_relative_to_root", lambda path, root: path.relative_to(root).as_posix())
            before = JSONResponse(
                docs_router.collect_html_artifacts(ctx=artifact_context, **{"types": ("html", "md"), **filters})
            ).body
        after = client.get(f"/api/artifacts/html{query}")
    assert after.status_code == 200
    assert after.content == before
    if not query:
        assert after.json()["total"] == 6

    (artifact_context.roots.project_root / "docs/research/added.md").write_text(
        "---\nclass: handoff\nstatus: green\ndate: 2026-10-02\nauthor: codex\n---\n# Added\n", encoding="utf-8"
    )
    with TestClient(app) as client:
        refreshed = client.get(f"/api/artifacts/html{query}")
    expected = JSONResponse(
        docs_router.collect_html_artifacts(ctx=artifact_context, **{"types": ("html", "md"), **filters})
    ).body
    assert refreshed.content == expected
    if not query:
        assert refreshed.json()["total"] == 7


def test_docs_resolved_containment_rejects_escape(tmp_path: Path) -> None:
    root = tmp_path / "approved"
    root.mkdir()
    outside = tmp_path / "approved-sibling"
    outside.mkdir()
    target = outside / "outside.md"
    target.write_text("outside", encoding="utf-8")
    link = root / "escape.md"
    link.symlink_to(target)
    for path in (link, target, root / ".." / "approved-sibling" / "outside.md"):
        with pytest.raises(HTTPException) as error:
            docs_router._assert_under_root(path, root)
        assert error.value.status_code == 403

    inside = root / "inside.md"
    inside.write_text("inside", encoding="utf-8")
    link.unlink()
    link.symlink_to(inside)
    docs_router._assert_under_root(link, root)
    logical_root = tmp_path / "logical"
    logical_root.symlink_to(root, target_is_directory=True)
    docs_router._assert_under_root(logical_root / "inside.md", logical_root)
    assert docs_router._relative_to_root(logical_root / "inside.md", logical_root) == "inside.md"
