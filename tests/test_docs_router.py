from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api import artifacts_router, docs_router


@pytest.fixture()
def docs_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    roots: dict[str, Path] = {}
    for key in docs_router.ALLOWED_ROOTS:
        root = tmp_path / key
        root.mkdir(parents=True)
        roots[key] = root
        (root / "REPORT.html").write_text(
            """
            <!doctype html><meta name="report-class" content="audit">
            <meta name="report-date" content="2026-05-09">
            <meta name="report-status" content="ok">
            <meta name="report-title" content="Fixture report">
            <meta name="report-kpi-summary" content="1 check passed">
            <meta name="report-related-issues" content="1814, 1822">
            <meta name="report-related-prs" content="1816">
            <meta name="report-agents" content="codex,claude">
            <meta name="report-author" content="codex">
            """,
            encoding="utf-8",
        )
    (tmp_path / "playgrounds").mkdir()
    (tmp_path / "playgrounds" / "artifacts.html").write_text("<!doctype html><title>Artifacts</title>", encoding="utf-8")
    monkeypatch.setattr(docs_router, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(docs_router, "ALLOWED_ROOTS", roots)
    monkeypatch.setattr(artifacts_router, "PROJECT_ROOT", tmp_path)
    app = FastAPI()
    app.include_router(artifacts_router.router, prefix="/api/artifacts")
    app.include_router(docs_router.router, prefix="/artifacts")
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("root_key", list(docs_router.ALLOWED_ROOTS))
def test_docs_router_serves_allowed_html_roots(docs_client: TestClient, root_key: str):
    response = docs_client.get(f"/artifacts/{root_key}/REPORT.html")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "max-age=300"


def test_docs_router_root_serves_browser_ui(docs_client: TestClient):
    response = docs_client.get("/artifacts/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Artifacts" in response.text


def test_docs_router_root_json_lists_roots(docs_client: TestClient):
    response = docs_client.get("/artifacts/?format=json")
    assert response.status_code == 200
    body = response.json()
    assert len(body["roots"]) == len(docs_router.ALLOWED_ROOTS)


def test_docs_router_directory_listing_json(docs_client: TestClient):
    response = docs_client.get("/artifacts/audit?format=json")
    assert response.status_code == 200
    body = response.json()
    assert body["root"] == "audit"
    assert body["items"][0]["name"] == "REPORT.html"
    assert body["items"][0]["meta"]["title"] == "Fixture report"


@pytest.mark.parametrize("path", [
    "/artifacts/../../../etc/passwd",
    "/artifacts/..%2f..%2f..%2fetc/passwd",
    "/artifacts/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
])
def test_docs_router_blocks_traversal(docs_client: TestClient, path: str):
    assert docs_client.get(path).status_code in {403, 404}


def test_docs_router_blocks_symlink_outside_root(docs_client: TestClient, tmp_path: Path):
    outside = tmp_path / "outside.html"
    outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "audit" / "linked.html"
    link.symlink_to(outside)
    assert docs_client.get("/artifacts/audit/linked.html").status_code in {403, 404}


def test_docs_router_blocks_forbidden_extension(docs_client: TestClient, tmp_path: Path):
    (tmp_path / "audit" / "script.py").write_text("print('no')", encoding="utf-8")
    assert docs_client.get("/artifacts/audit/script.py").status_code in {403, 404}


def test_docs_router_blocks_unapproved_root(docs_client: TestClient, tmp_path: Path):
    (tmp_path / "scripts" / "api").mkdir(parents=True)
    (tmp_path / "scripts" / "api" / "main.py").write_text("x = 1", encoding="utf-8")
    assert docs_client.get("/artifacts/scripts/api/main.py").status_code in {403, 404}


def test_docs_router_missing_file_404(docs_client: TestClient):
    assert docs_client.get("/artifacts/audit/missing.html").status_code == 404


def test_docs_router_blocks_hidden_file(docs_client: TestClient, tmp_path: Path):
    hidden_dir = tmp_path / "audit" / ".git"
    hidden_dir.mkdir()
    (hidden_dir / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")
    assert docs_client.get("/artifacts/audit/.git/HEAD").status_code in {403, 404}


def test_html_artifact_listing_extracts_metadata_and_filters(docs_client: TestClient):
    response = docs_client.get("/api/artifacts/html?class=audit&status=ok&author=codex")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(docs_router.ALLOWED_ROOTS)
    artifact = body["artifacts"][0]
    assert artifact["title"] == "Fixture report"
    assert artifact["related_issues"] == [1814, 1822]
    assert artifact["related_prs"] == [1816]
    assert artifact["agents"] == ["codex", "claude"]
