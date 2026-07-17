from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from scripts.api import docs_router
from scripts.api.main import app
from tests.latency_budget import assert_under_budget


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def controlled_docs_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    safe_root = tmp_path / "safe-root"
    outside_root = tmp_path / "outside-root"
    safe_root.mkdir()
    outside_root.mkdir()

    (safe_root / "file.html").write_text("<!doctype html><title>safe</title>", encoding="utf-8")
    (safe_root / "script.py").write_text("print('blocked')", encoding="utf-8")
    (safe_root / "deploy.sh").write_text("echo blocked", encoding="utf-8")
    (safe_root / "config.env").write_text("SECRET=blocked", encoding="utf-8")
    (safe_root / ".hidden.html").write_text("hidden", encoding="utf-8")
    (outside_root / "secret.html").write_text("secret outside root", encoding="utf-8")
    (safe_root / "escape.html").symlink_to(outside_root / "secret.html")

    dashboards = tmp_path / "dashboards"
    dashboards.mkdir()
    (dashboards / "artifacts.html").write_text("<!doctype html><title>Artifacts</title>", encoding="utf-8")

    monkeypatch.setattr(docs_router, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(docs_router, "ALLOWED_ROOTS", {"safe": safe_root})
    monkeypatch.setattr(docs_router, "EFFECTIVE_ROOTS", {"safe": safe_root})
    monkeypatch.setattr(docs_router, "DISCOVERY_ROOTS", (safe_root,))

    return {"safe": safe_root, "outside": outside_root}


@pytest.fixture()
def controlled_client(controlled_docs_tree: dict[str, Path]) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def docs_tree_with_md(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Controlled tree that includes MD files under docs/ subdirectories."""
    docs_dir = tmp_path / "docs"
    proposals_dir = docs_dir / "proposals"
    handoffs_dir = docs_dir / "handoffs"
    archive_dir = docs_dir / "archive"
    raw_podcasts_dir = docs_dir / "resources" / "podcasts" / "raw"

    proposals_dir.mkdir(parents=True)
    handoffs_dir.mkdir(parents=True)
    archive_dir.mkdir(parents=True)
    raw_podcasts_dir.mkdir(parents=True)

    # HTML artifact in docs/proposals
    (proposals_dir / "rfc-001.html").write_text(
        '<!doctype html>\n<meta name="report-class" content="proposal">\n'
        '<meta name="report-title" content="RFC 001">\n'
        '<meta name="report-date" content="2026-05-01">\n'
        '<meta name="report-status" content="green">\n'
        '<meta name="report-author" content="team">\n'
        '<title>RFC 001</title>\n<body>content</body>',
        encoding="utf-8",
    )

    # MD artifact with YAML frontmatter in docs/handoffs
    (handoffs_dir / "session-1.md").write_text(
        "---\n"
        "class: handoff\n"
        "status: green\n"
        "date: 2026-05-17\n"
        "author: codex\n"
        "title: Session Handoff 1\n"
        "kpi_summary: Completed 3 modules\n"
        "related_issues: \"142, 150\"\n"
        "related_prs: \"201, 202\"\n"
        "agents: \"codex, gemini\"\n"
        "---\n"
        "\n"
        "# Session Handoff 1\n"
        "\n"
        "This is a handoff document.\n",
        encoding="utf-8",
    )

    # MD artifact WITHOUT frontmatter in docs/handoffs
    (handoffs_dir / "notes.md").write_text(
        "# Plain Notes\n"
        "\n"
        "No frontmatter here, just a heading.\n",
        encoding="utf-8",
    )

    # Excluded: docs/archive/old.html should NOT surface
    (archive_dir / "old.html").write_text(
        '<!doctype html><title>Archived</title>',
        encoding="utf-8",
    )

    # Excluded: docs/resources/podcasts/raw/* should NOT surface
    (raw_podcasts_dir / "raw.txt").write_text("raw podcast data", encoding="utf-8")
    (raw_podcasts_dir / "episode.md").write_text("# Raw Episode\n\nraw content\n", encoding="utf-8")

    # MD in docs/proposals (for dynamic root coverage)
    (proposals_dir / "proposal-2.md").write_text(
        "# Proposal 2\n\nSome proposal content.\n",
        encoding="utf-8",
    )

    dashboards = tmp_path / "dashboards"
    dashboards.mkdir()
    (dashboards / "artifacts.html").write_text("<!doctype html><title>Artifacts</title>", encoding="utf-8")

    monkeypatch.setattr(docs_router, "PROJECT_ROOT", tmp_path)
    # Clear ALLOWED_ROOTS so _build_effective_roots only discovers tmp_path dirs
    monkeypatch.setattr(docs_router, "ALLOWED_ROOTS", {})
    docs_router.EFFECTIVE_ROOTS = docs_router._build_effective_roots()
    monkeypatch.setattr(docs_router, "DISCOVERY_ROOTS", (tmp_path / "docs",))
    monkeypatch.setattr(docs_router, "DISCOVERY_EXCLUDES", ("docs/archive", "docs/resources/podcasts/raw"))

    return {"docs": docs_dir, "proposals": proposals_dir, "handoffs": handoffs_dir, "archive": archive_dir}


@pytest.fixture()
def docs_tree_client(docs_tree_with_md: dict[str, Path]) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _first_allowed_file(root_path: Path) -> Path:
    candidates = [
        path
        for path in root_path.rglob("*")
        if path.is_file()
        and path.suffix.lower() in docs_router._ALLOWED_EXT
        and not any(part.startswith(".") for part in path.relative_to(root_path).parts)
    ]
    candidates.sort(key=lambda path: (path.suffix.lower() != ".html", path.as_posix()))
    if not candidates:
        pytest.skip(f"no allowed documentation artifact under {root_path} (likely empty root post-cleanup)")
    return candidates[0]


@pytest.mark.parametrize("root_key", list(docs_router.ALLOWED_ROOTS))
def test_docs_router_serves_allowed_root_files(client: TestClient, root_key: str):
    root_path = docs_router.ALLOWED_ROOTS[root_key]
    file_path = _first_allowed_file(root_path)
    artifact_path = f"/artifacts/{root_key}/{file_path.relative_to(root_path).as_posix()}"

    response = client.get(quote(artifact_path, safe="/"))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(docs_router._MIME_TYPES[file_path.suffix.lower()])
    assert response.headers["cache-control"] == "max-age=300, must-revalidate"


def test_docs_router_root_index_lists_allowed_roots(client: TestClient):
    response = client.get("/artifacts/?format=json")

    assert response.status_code == 200
    body = response.json()
    assert {root["id"] for root in body["roots"]} == set(docs_router.EFFECTIVE_ROOTS)
    assert len(body["roots"]) >= 10  # ≥ 10 — EFFECTIVE_ROOTS may grow with dynamic roots (#2106)
    assert all({"id", "path", "exists"} <= set(root) for root in body["roots"])


def test_docs_router_includes_proposals_and_poc(client: TestClient):
    """Regression: /api/artifacts/html must surface docs/proposals and docs/poc.

    Both directories ship genuine artifacts (RFCs, PoC designs, syllabi).
    Pre-fix, the ALLOWED_ROOTS whitelist omitted them, hiding RFC-001 and
    PoC lesson/site designs from the API listing. If you remove either
    root from the whitelist again, this test will tell you (rather than
    a user noticing artifacts missing in production).
    """
    response = client.get("/api/artifacts/html")
    assert response.status_code == 200
    body = response.json()
    paths = {a["path"] for a in body["artifacts"]}

    # Don't pin specific filenames — the directories' contents will
    # evolve. Pin the *prefix* coverage instead so we're robust to file
    # renames but still catch root-drop regressions.
    assert any(p.startswith("docs/proposals/") for p in paths), (
        "no docs/proposals/*.html in /api/artifacts/html — ALLOWED_ROOTS"
        " regression? Add 'docs/proposals' back to scripts/api/docs_router.py."
    )
    assert any(p.startswith("docs/poc/") for p in paths), (
        "no docs/poc/*.html in /api/artifacts/html — ALLOWED_ROOTS"
        " regression? Add 'docs/poc' back to scripts/api/docs_router.py."
    )


def test_docs_router_directory_listing_includes_file_metadata(client: TestClient):
    response = client.get("/artifacts/audit?format=json")

    assert response.status_code == 200
    body = response.json()
    assert body["root"] == "audit"
    assert body["relative_path"] == ""
    assert body["items_count"] == len(body["items"])
    assert body["items"]
    assert any({"name", "size", "mtime"} <= set(item) for item in body["items"])


def test_docs_router_root_listing_retains_logical_symlink_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    live_root = tmp_path / "live" / "docs"
    logical_root = tmp_path / ".runtime" / "api" / "releases" / ("a" * 40) / "docs"
    live_root.mkdir(parents=True)
    (live_root / "report.md").write_text("# Report\n", encoding="utf-8")
    logical_root.parent.mkdir(parents=True)
    logical_root.symlink_to(live_root, target_is_directory=True)
    asserted_paths: list[Path] = []

    def record_assertion(full_path: Path, _root_path: Path) -> None:
        asserted_paths.append(full_path)

    monkeypatch.setattr(docs_router, "_assert_under_root", record_assertion)

    listing = docs_router._directory_listing("safe", "safe", logical_root, "")

    assert listing["items_count"] == 1
    assert asserted_paths[0] == logical_root
    assert asserted_paths[0] != logical_root.resolve()


@pytest.mark.parametrize(
    "path",
    [
        "/artifacts/../../../etc/passwd",
        "/artifacts/..%2f..%2f..%2fetc/passwd",
        "/artifacts/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
    ],
)
def test_docs_router_blocks_traversal_variants(controlled_client: TestClient, path: str):
    response = controlled_client.get(path)

    assert response.status_code in {403, 404}
    assert response.status_code < 500


def test_docs_router_blocks_symlink_escape(controlled_client: TestClient):
    response = controlled_client.get("/artifacts/safe/escape.html")

    assert response.status_code in {403, 404}
    assert "secret outside root" not in response.text


@pytest.mark.parametrize("filename", ["script.py", "deploy.sh", "config.env"])
def test_docs_router_blocks_forbidden_extensions(controlled_client: TestClient, filename: str):
    response = controlled_client.get(f"/artifacts/safe/{filename}")

    assert response.status_code in {403, 404}


def test_docs_router_blocks_unapproved_root(controlled_client: TestClient):
    response = controlled_client.get("/artifacts/scripts/api/main.py")

    assert response.status_code in {403, 404}


def test_docs_router_missing_file_404(controlled_client: TestClient):
    response = controlled_client.get("/artifacts/safe/missing.html")

    assert response.status_code == 404


def test_docs_router_blocks_hidden_file(controlled_client: TestClient):
    response = controlled_client.get("/artifacts/safe/.hidden.html")

    assert response.status_code in {403, 404}
    assert "hidden" not in response.text


def test_docs_router_serves_100kb_html_within_smoke_budget(
    controlled_docs_tree: dict[str, Path],
    controlled_client: TestClient,
):
    large_file = controlled_docs_tree["safe"] / "large.html"
    large_file.write_text("<!doctype html>\n" + ("x" * 100_000), encoding="utf-8")

    start = time.perf_counter()
    response = controlled_client.get("/artifacts/safe/large.html")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert_under_budget(
        elapsed,
        0.2,
        f"/artifacts/safe/large.html took {elapsed:.3f}s (budget 0.2s)",
    )


def test_docs_router_concurrent_access_sanity(controlled_client: TestClient):
    def fetch_file(_index: int):
        return controlled_client.get("/artifacts/safe/file.html")

    with ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(fetch_file, range(10)))

    assert len(responses) == 10
    assert all(response.status_code == 200 for response in responses)
    assert all("safe" in response.text for response in responses)


# ── New tests for MD artifact support (#2106) ──


def test_artifacts_api_surfaces_md_files(docs_tree_client: TestClient):
    """MD files in docs/ subdirectories should appear in /api/artifacts/html."""
    response = docs_tree_client.get("/api/artifacts/html")
    assert response.status_code == 200
    body = response.json()

    paths = {a["path"] for a in body["artifacts"]}
    assert "docs/handoffs/session-1.md" in paths, (
        "MD file with frontmatter not surfaced in artifacts API"
    )
    assert "docs/handoffs/notes.md" in paths, (
        "MD file without frontmatter not surfaced in artifacts API"
    )
    assert "docs/proposals/proposal-2.md" in paths, (
        "MD file in proposals not surfaced in artifacts API"
    )


def test_artifacts_md_with_yaml_frontmatter(docs_tree_client: TestClient):
    """MD with YAML frontmatter should have metadata extracted."""
    response = docs_tree_client.get("/api/artifacts/html")
    assert response.status_code == 200
    body = response.json()

    # Find the session-1.md artifact
    session = next(
        (a for a in body["artifacts"] if a["path"] == "docs/handoffs/session-1.md"),
        None,
    )
    assert session is not None, "session-1.md not found in artifacts"

    assert session["class"] == "handoff"
    assert session["status"] == "green"
    assert session["date"] == "2026-05-17"
    assert session["author"] == "codex"
    assert session["title"] == "Session Handoff 1"
    assert session["kpi_summary"] == "Completed 3 modules"
    assert session["related_issues"] == [142, 150]
    assert session["related_prs"] == [201, 202]
    assert session["agents"] == ["codex", "gemini"]


def test_artifacts_md_without_frontmatter(docs_tree_client: TestClient):
    """MD without frontmatter should have class=document, date from mtime."""
    response = docs_tree_client.get("/api/artifacts/html")
    assert response.status_code == 200
    body = response.json()

    notes = next(
        (a for a in body["artifacts"] if a["path"] == "docs/handoffs/notes.md"),
        None,
    )
    assert notes is not None, "notes.md not found in artifacts"

    assert notes["class"] == "document"
    # Title should be first H1
    assert notes["title"] == "Plain Notes"
    # date should be ISO date from mtime
    assert len(notes["date"]) == 10  # YYYY-MM-DD
    assert notes["status"] == "unknown"


def test_artifacts_type_filter_md_only(docs_tree_client: TestClient):
    """?type=md should return only MD artifacts."""
    response = docs_tree_client.get("/api/artifacts/html?type=md")
    assert response.status_code == 200
    body = response.json()

    for artifact in body["artifacts"]:
        assert artifact["path"].endswith(".md"), (
            f"Expected only MD files, got {artifact['path']}"
        )
    # Should have our MD files
    paths = {a["path"] for a in body["artifacts"]}
    assert "docs/handoffs/session-1.md" in paths
    assert "docs/handoffs/notes.md" in paths


def test_artifacts_type_filter_html_only(docs_tree_client: TestClient):
    """?type=html should return only HTML artifacts."""
    response = docs_tree_client.get("/api/artifacts/html?type=html")
    assert response.status_code == 200
    body = response.json()

    for artifact in body["artifacts"]:
        assert artifact["path"].endswith(".html"), (
            f"Expected only HTML files, got {artifact['path']}"
        )


def test_artifacts_archive_excluded(docs_tree_client: TestClient):
    """docs/archive/* files should NOT appear in artifacts."""
    response = docs_tree_client.get("/api/artifacts/html")
    assert response.status_code == 200
    body = response.json()

    paths = {a["path"] for a in body["artifacts"]}
    assert not any(p.startswith("docs/archive/") for p in paths), (
        "docs/archive/* should be excluded from artifacts"
    )


def test_artifacts_podcasts_raw_excluded(docs_tree_client: TestClient):
    """docs/resources/podcasts/raw/* files should NOT appear in artifacts."""
    response = docs_tree_client.get("/api/artifacts/html")
    assert response.status_code == 200
    body = response.json()

    paths = {a["path"] for a in body["artifacts"]}
    assert not any("podcasts/raw" in p for p in paths), (
        "docs/resources/podcasts/raw/* should be excluded from artifacts"
    )


def test_artifacts_dynamic_root_surfaces(docs_tree_client: TestClient):
    """New docs/<dir> with content should auto-surface no code change (#2106)."""
    response = docs_tree_client.get("/api/artifacts/html")
    assert response.status_code == 200
    body = response.json()

    paths = {a["path"] for a in body["artifacts"]}
    # proposals should contain both HTML and MD
    assert "docs/proposals/rfc-001.html" in paths
    assert "docs/proposals/proposal-2.md" in paths
    # handoffs should contain MD
    assert "docs/handoffs/session-1.md" in paths
