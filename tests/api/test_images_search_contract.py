"""Image search returns a usable image reference, not only a description match (#10667 D10)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.images_router import router
from scripts.api.monitor_context import fixture_context

ROUTE = "/api/images/annotations"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    images = tmp_path / "data" / "textbook_images"
    images.mkdir(parents=True)
    rows = [
        {
            "image_id": "img-page",
            "image_path": "data/textbook_images/grade-3/book-p3-img1.png",
            "pdf_stem": "book",
            "page": 3,
            "description_uk": "Козак верхи на коні.",
            "teaching_value": "high",
            "element_type": "illustration",
        },
        {
            "image_id": "img-unplaced",
            "image_path": "data/textbook_images/grade-3/unplaced.png",
            "pdf_stem": "",
            "page": None,
            "description_uk": "Козак без прив'язки до сторінки.",
            "teaching_value": "medium",
            "element_type": "illustration",
        },
        {
            "image_id": "img-missing-pdf",
            "image_path": "data/textbook_images/grade-3/missing.png",
            "pdf_stem": "missing-book",
            "page": 1,
            "description_uk": "Козак зі сторінки відсутньої книги.",
            "teaching_value": "medium",
            "element_type": "illustration",
        },
        {
            "image_id": "img-out-of-range",
            "image_path": "data/textbook_images/grade-3/out-of-range.png",
            "pdf_stem": "book",
            "page": 99,
            "description_uk": "Козак за межами книги.",
            "teaching_value": "medium",
            "element_type": "illustration",
        },
    ]
    with (images / "image_text_pairs.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    _write_pdf(tmp_path / "data" / "textbooks" / "grade-3" / "book.pdf", pages=3)
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(router, prefix="/api/images")
    return TestClient(app)


def _write_pdf(path: Path, *, pages: int) -> None:
    import pymupdf

    path.parent.mkdir(parents=True)
    document = pymupdf.open()
    try:
        for _ in range(pages):
            document.new_page()
        document.save(path)
    finally:
        document.close()


def test_description_search_exposes_a_retrievable_image_url(client: TestClient) -> None:
    response = client.get(ROUTE, params={"q": "козак"})
    assert response.status_code == 200
    items = {item["image_id"]: item for item in response.json()["items"]}

    assert items["img-page"]["render_url"] == "/api/images/page_render/book/3.png"
    assert items["img-page"]["description_uk"].startswith("Козак")
    # A page identity or bounds the catalog cannot prove must not promise a URL.
    for image_id in ("img-unplaced", "img-missing-pdf", "img-out-of-range"):
        assert items[image_id]["render_url"] is None

    # The advertised image must be retrievable, never a 404.
    image = client.get(items["img-page"]["render_url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content.startswith(b"\x89PNG")


def test_withheld_render_urls_would_have_been_404_or_out_of_range(client: TestClient) -> None:
    assert client.get("/api/images/page_render/missing-book/1.png").status_code == 404
    assert client.get("/api/images/page_render/book/99.png").status_code == 400


def test_non_matching_query_returns_no_rows(client: TestClient) -> None:
    response = client.get(ROUTE, params={"q": "гетьман"})
    assert response.status_code == 200
    assert response.json()["total"] == 0
