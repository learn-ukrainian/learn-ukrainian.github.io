from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from scripts.api import docs_router
from scripts.api.main import app


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
    return {"safe": safe_root, "outside": outside_root}


@pytest.fixture()
def controlled_client(controlled_docs_tree: dict[str, Path]) -> TestClient:
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
    assert candidates, f"no allowed documentation artifact found under {root_path}"
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
    assert {root["id"] for root in body["roots"]} == set(docs_router.ALLOWED_ROOTS)
    assert len(body["roots"]) == 8
    assert all({"id", "path", "exists"} <= set(root) for root in body["roots"])


def test_docs_router_directory_listing_includes_file_metadata(client: TestClient):
    response = client.get("/artifacts/audit?format=json")

    assert response.status_code == 200
    body = response.json()
    assert body["root"] == "audit"
    assert body["relative_path"] == ""
    assert body["items_count"] == len(body["items"])
    assert body["items"]
    assert any({"name", "size", "mtime"} <= set(item) for item in body["items"])


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
    assert elapsed < 0.2


def test_docs_router_concurrent_access_sanity(controlled_client: TestClient):
    def fetch_file(_index: int):
        return controlled_client.get("/artifacts/safe/file.html")

    with ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(fetch_file, range(10)))

    assert len(responses) == 10
    assert all(response.status_code == 200 for response in responses)
    assert all("safe" in response.text for response in responses)
