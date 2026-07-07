import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make sure scripts/crawl directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.crawl.download_textbooks import (
    TitleGuardError,
    check_filename_overlap,
    extract_pdf_links,
)


class MockResponse:
    def __init__(self, text, status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP Error")


def test_title_guard_mismatch():
    # Test case (a): page with right slug text but wrong content -> refusal (TitleGuardError)
    html_content = """
    <html>
    <head><title>Some other title - pidruchnyk.com.ua</title></head>
    <body>
        <a href="http://pidruchnyk.com.ua/uploads/book/ukrmova_2_bolsh.pdf">Download</a>
    </body>
    </html>
    """

    with patch("requests.get", return_value=MockResponse(html_content)):
        with pytest.raises(TitleGuardError) as excinfo:
            extract_pdf_links(slug="3029-ukr-mova-bukvar-1-klas-bolshakova", author="Большакова", grade=1)
        assert "expected author" in str(excinfo.value).lower()


def test_title_guard_success_and_canonical_dest():
    # Test case (c): dest naming canonical, also check successful title guard and pdf extraction
    html_content = """
    <html>
    <head><title>Буквар 1 клас Большакова 2025 - pidruchnyk.com.ua</title></head>
    <body>
        <a href="/uploads/book/ukrmova_1_bolsh_2025_1.pdf">Part 1</a>
        <a href="http://pidruchnyk.com.ua/uploads/book/ukrmova_1_bolsh_2025_2.pdf">Part 2</a>
    </body>
    </html>
    """

    with patch("requests.get", return_value=MockResponse(html_content)):
        pdfs = extract_pdf_links(slug="3029-ukr-mova-bukvar-1-klas-bolshakova", author="Большакова", grade=1, target_year=2025)

    assert len(pdfs) == 2
    assert pdfs[0]["filename"] == "ukrmova_1_bolsh_2025_1.pdf"
    assert pdfs[1]["filename"] == "ukrmova_1_bolsh_2025_2.pdf"


def test_drive_iframe_extraction():
    # Test case (b): iframe page -> Drive ID extracted
    html_content = """
    <html>
    <head><title>Етика 6 клас Мартинюк 2023 - pidruchnyk.com.ua</title></head>
    <body>
        <iframe src="https://drive.google.com/file/d/1esRiRruVTaSvo0c8mv90YTqjwmh2AP5G/preview" width="640" height="480"></iframe>
    </body>
    </html>
    """

    with patch("requests.get", return_value=MockResponse(html_content)):
        pdfs = extract_pdf_links(slug="2632-etyka-6-klas-martyniuk", author="Мартинюк", grade=6)

    assert len(pdfs) == 1
    assert pdfs[0]["gdrive_id"] == "1esRiRruVTaSvo0c8mv90YTqjwmh2AP5G"
    assert "uc?export=download&id=1esRiRruVTaSvo0c8mv90YTqjwmh2AP5G" in pdfs[0]["url"]


def test_check_filename_overlap():
    # Test our warn-only filename overlap checks
    # Case 1: Overlap exists
    assert check_filename_overlap("ukrmova_2_bolsh.pdf", "ukrainska_mova", "Большакова") is True

    # Case 2: Overlap exists via transliteration
    assert check_filename_overlap("5-klas-matematyka-ister-2022.pdf", "matematyka", "Істер") is True

    # Case 3: Overlap missing
    assert check_filename_overlap("random_filename_123.pdf", "ukrainska_mova", "Большакова") is False
