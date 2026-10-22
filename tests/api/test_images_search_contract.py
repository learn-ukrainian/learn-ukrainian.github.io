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
    ]
    with (images / "image_text_pairs.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    app = FastAPI()
    app.state.ctx = fixture_context(tmp_path)
    app.include_router(router, prefix="/api/images")
    return TestClient(app)


def test_description_search_exposes_a_renderable_image_url(client: TestClient) -> None:
    response = client.get(ROUTE, params={"q": "козак"})
    assert response.status_code == 200
    items = {item["image_id"]: item for item in response.json()["items"]}

    assert items["img-page"]["render_url"] == "/api/images/page_render/book/3.png"
    assert items["img-page"]["description_uk"].startswith("Козак")
    # Missing page identity stays explicitly unknown; it must not borrow another page.
    assert items["img-unplaced"]["render_url"] is None


def test_non_matching_query_returns_no_rows(client: TestClient) -> None:
    response = client.get(ROUTE, params={"q": "гетьман"})
    assert response.status_code == 200
    assert response.json()["total"] == 0
