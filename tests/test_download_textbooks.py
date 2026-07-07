import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make sure scripts/crawl directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.crawl.download_textbooks import (
    TitleGuardError,
    check_filename_overlap,
    download_from_gdrive,
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
        pdfs = extract_pdf_links(
            slug="3029-ukr-mova-bukvar-1-klas-bolshakova", author="Большакова", grade=1, target_year=2025
        )

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


class MockGdriveResponse:
    def __init__(self, text_or_bytes, status_code=200, headers=None):
        if isinstance(text_or_bytes, str):
            self.content = text_or_bytes.encode("utf-8")
            self.text = text_or_bytes
        else:
            self.content = text_or_bytes
            self.text = text_or_bytes.decode("utf-8", errors="ignore")
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP Error")

    def iter_content(self, chunk_size=8192):
        for i in range(0, len(self.content), chunk_size):
            yield self.content[i : i + chunk_size]


def test_gdrive_view_only_html_refusal(tmp_path):
    # Test case: view-only HTML -> refusal + no dest file
    dest = tmp_path / "test_book.pdf"
    html_content = "<html><head><title>Can't download file</title></head><body>Preview only...</body></html>"
    mock_resp = MockGdriveResponse(html_content, headers={"Content-Type": "text/html"})

    with patch("requests.Session.get", return_value=mock_resp):
        with pytest.raises(ValueError) as excinfo:
            download_from_gdrive("gdrive_id_123", dest)
        assert "not a PDF" in str(excinfo.value)
        assert "Can't download file" in str(excinfo.value)

    assert not dest.exists()


def test_gdrive_uuid_form_confirm(tmp_path):
    # Test case: uuid-form confirm
    dest = tmp_path / "test_book.pdf"

    html_warning = """
    <html>
    <head><title>Google Drive - Warning</title></head>
    <body>
        <form id="downloadForm" action="/uc" method="GET">
            <input type="hidden" name="confirm" value="TOKEN_ABC">
            <input type="hidden" name="uuid" value="UUID_DEF">
        </form>
    </body>
    </html>
    """

    pdf_data = b"%PDF-1.4\n%..."

    def mock_get(url, params=None, **kwargs):
        params = params or {}
        if "confirm" in params:
            assert params["confirm"] == "TOKEN_ABC"
            assert params.get("uuid") == "UUID_DEF"
            return MockGdriveResponse(pdf_data, headers={"Content-Type": "application/pdf"})
        else:
            return MockGdriveResponse(html_warning, headers={"Content-Type": "text/html"})

    with patch("requests.Session.get", side_effect=mock_get):
        success = download_from_gdrive("gdrive_id_123", dest)

    assert success is True
    assert dest.exists()
    assert dest.read_bytes() == pdf_data


def test_title_guard_nbsp_both_ways():
    # Test case: NBSP title passes guard
    # Case 1: HTML has NBSP, expected has regular space
    html_content_1 = """
    <html>
    <head><title>Буквар 9\xa0клас Большакова 2025</title></head>
    <body>
        <a href="/uploads/book/ukrmova_9_bolsh_2025.pdf">Download</a>
    </body>
    </html>
    """
    with patch("requests.get", return_value=MockResponse(html_content_1)):
        pdfs = extract_pdf_links(slug="test-slug", author="Большакова", grade=9)
    assert len(pdfs) == 1

    # Case 2: HTML has regular space, expected has NBSP
    html_content_2 = """
    <html>
    <head><title>Буквар 9 клас О. Большакова 2025</title></head>
    <body>
        <a href="/uploads/book/ukrmova_9_bolsh_2025.pdf">Download</a>
    </body>
    </html>
    """
    with patch("requests.get", return_value=MockResponse(html_content_2)):
        pdfs = extract_pdf_links(slug="test-slug", author="О.\xa0Большакова", grade=9)
    assert len(pdfs) == 1
