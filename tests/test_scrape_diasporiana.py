"""Tests for the Diasporiana PDF scraper."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "rag"))

import scrape_diasporiana as sd

fitz = pytest.importorskip("fitz")
Image = pytest.importorskip("PIL.Image")
ImageDraw = pytest.importorskip("PIL.ImageDraw")
ImageFont = pytest.importorskip("PIL.ImageFont")


def _find_unicode_font() -> str:
    candidates = [
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate

    result = subprocess.run(
        ["fc-match", "-f", "%{file}\n", ":lang=uk"],
        capture_output=True,
        text=True,
        check=False,
    )
    font_path = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    if font_path and Path(font_path).exists():
        return font_path

    pytest.skip("No Unicode font with Cyrillic support available for PDF fixtures")


@pytest.fixture()
def sample_spec() -> sd.SourceSpec:
    return sd.SourceSpec(
        slug="diasporiana-test",
        volume=1,
        url="https://diasporiana.org.ua/test",
        work="Дорошенко — Нарис історії України, том 1",
        author="Дорошенко Д.",
        year=1932,
    )


@pytest.fixture()
def text_layer_pdf(tmp_path: Path) -> Path:
    font_path = _find_unicode_font()
    pdf_path = tmp_path / "text-layer.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_font(fontname="ukrfont", fontfile=font_path)

    lines = [
        "Гетьманщина і Нарис історії України.",
        "Український історичний текст про державу і козацтво.",
    ] * 18
    y = 60
    for line in lines:
        page.insert_text((40, y), line, fontsize=16, fontname="ukrfont")
        y += 22
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture()
def image_only_pdf(tmp_path: Path) -> Path:
    font_path = _find_unicode_font()
    image_path = tmp_path / "ocr-source.png"
    pdf_path = tmp_path / "image-only.pdf"

    image = Image.new("L", (1800, 2400), 255)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, 56)
    lines = [
        "Гетьманщина і Україна",
        "Дорошенко пише про козацтво",
        "Нарис історії України",
    ]
    y = 220
    for line in lines:
        draw.text((140, y), line, fill=0, font=font)
        y += 120
    image.save(image_path)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(fitz.Rect(30, 30, 565, 812), filename=str(image_path))
    doc.save(pdf_path)
    doc.close()
    return pdf_path


class TestDiasporianaTextLayerProbe:
    def test_text_layer_probe_extracts_cyrillic_pages(
        self,
        text_layer_pdf: Path,
        sample_spec: sd.SourceSpec,
    ) -> None:
        pages = sd.extract_text_layer_pages(
            text_layer_pdf,
            sample_spec,
            "https://diasporiana.org.ua/wp-content/uploads/test.pdf",
        )

        substantial, avg_cyr = sd.text_layer_is_substantial(
            pages,
            sd.get_pdf_page_count(text_layer_pdf),
        )

        assert substantial is True
        assert avg_cyr > sd.TEXT_LAYER_MIN_CYRILLIC_PER_PAGE
        assert pages
        assert "Гетьманщина" in pages[0].text
        assert pages[0].page == 1
        assert pages[0].volume == 1
        assert pages[0].work_title == sample_spec.work


@pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="Tesseract not installed",
)
class TestDiasporianaOcrFallback:
    def test_image_only_pdf_triggers_ocr(
        self,
        image_only_pdf: Path,
        sample_spec: sd.SourceSpec,
    ) -> None:
        text_pages = sd.extract_text_layer_pages(
            image_only_pdf,
            sample_spec,
            "https://diasporiana.org.ua/wp-content/uploads/test.pdf",
        )
        substantial, _ = sd.text_layer_is_substantial(
            text_pages,
            sd.get_pdf_page_count(image_only_pdf),
        )
        assert substantial is False

        ocr_pages = sd.ocr_pdf_pages(
            image_only_pdf,
            sample_spec,
            "https://diasporiana.org.ua/wp-content/uploads/test.pdf",
        )
        combined = "\n".join(page.text for page in ocr_pages)

        assert ocr_pages
        assert "Україна" in combined or "Нарис історії України" in combined


class TestDiasporianaRateLimiter:
    def test_rate_limiter_waits_between_requests(self) -> None:
        pacer = sd.RequestPacer()
        with patch("scrape_diasporiana.random.uniform", return_value=2.4), patch(
            "scrape_diasporiana.time.sleep"
        ) as sleep_mock:
            pacer.wait()
            sleep_mock.assert_not_called()
            pacer.wait()
            sleep_mock.assert_called_once_with(2.4)


class TestDiasporianaJsonlSchema:
    def test_chunk_schema_matches_existing_litopys_waves(
        self,
        sample_spec: sd.SourceSpec,
    ) -> None:
        pages = [
            sd.PageText(
                page=1,
                volume=1,
                author=sample_spec.author,
                year=sample_spec.year,
                work_title=sample_spec.work,
                source_url="https://diasporiana.org.ua/file.pdf#page=1",
                text=(
                    "Гетьманщина була важливою частиною історії України. " * 80
                    + "\n\n"
                    + "Дорошенко описує козацьку державу та її політичний розвиток. " * 60
                ),
            )
        ]

        chunks = sd.chunk_pages(pages, sample_spec)
        assert chunks

        fixture_path = ROOT / "data" / "literary_texts" / "wave12-krupnytsky-orlyk-biohrafiia.jsonl"
        with fixture_path.open(encoding="utf-8") as handle:
            fixture_chunk = json.loads(handle.readline())

        assert set(chunks[0].keys()) == set(fixture_chunk.keys())
        assert chunks[0]["author"] == sample_spec.author
        assert chunks[0]["work"] == sample_spec.work
        assert chunks[0]["year"] == sample_spec.year
