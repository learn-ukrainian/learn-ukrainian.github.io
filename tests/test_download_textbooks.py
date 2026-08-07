import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make sure scripts/crawl directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.crawl.download_textbooks import (
    DownloadValidationError,
    TitleGuardError,
    _fallback_for_component,
    check_filename_overlap,
    download_from_gdrive,
    download_pdf,
    extract_pdf_links,
    extract_shkola_pdf_links,
    find_retained_book_pdfs,
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


def test_direct_pdf_and_drive_link_are_one_book_with_a_mirror():
    html_content = """
    <html>
    <head><title>Українська мова 6 клас Заболотний 2023</title></head>
    <body>
      <a href="https://schoolbook.example/Zabolotnyi_2023.pdf">PDF</a>
      <a href="https://drive.google.com/uc?export=download&id=DRIVE_MIRROR">Drive</a>
    </body>
    </html>
    """

    with patch("requests.get", return_value=MockResponse(html_content)):
        pdfs = extract_pdf_links(
            slug="2591-ukrmova-6-klas-zabolotnyi-2023",
            author="Заболотний",
            grade=6,
            target_year=2023,
        )

    assert len(pdfs) == 1
    assert pdfs[0]["filename"] == "Zabolotnyi_2023.pdf"
    assert pdfs[0]["alternate_downloads"] == [
        {
            "url": "https://docs.google.com/uc?export=download&id=DRIVE_MIRROR",
            "label": "Google Drive mirror",
            "filename": "DRIVE_MIRROR.pdf",
            "gdrive_id": "DRIVE_MIRROR",
        }
    ]


def test_shkola_form_resolves_only_requested_edition_to_drive():
    html_content = """
    <html><head><title>Підручник Українська мова 6 клас Заболотний 2023</title></head>
    <body>
      <form method="POST"><button name="vslink" value="NEW" title="Завантажити Заболотний 2023">Завантажити</button></form>
      <form method="POST"><button name="vslink" value="OLD" title="Завантажити Заболотний 2020">2020</button></form>
    </body></html>
    """

    class RedirectResponse(MockResponse):
        def __init__(self, location):
            super().__init__("", status_code=303, headers={"Location": location})

        def close(self):
            pass

    class FakeSession:
        def __init__(self):
            self.headers = {}
            self.posts = []

        def get(self, url, **_kwargs):
            response = MockResponse(html_content)
            response.url = url
            return response

        def post(self, url, *, data, **_kwargs):
            self.posts.append((url, data))
            return RedirectResponse(
                "https://drive.google.com/uc?export=download&id=DRIVE_2023"
            )

    session = FakeSession()
    with patch("requests.Session", return_value=session):
        pdfs = extract_shkola_pdf_links(
            "https://shkola.in.ua/2835-ukrainska-mova-6-klas-zabolotnyi.html",
            author="Заболотний",
            grade=6,
            target_year=2023,
        )

    assert session.posts == [
        (
            "https://shkola.in.ua/2835-ukrainska-mova-6-klas-zabolotnyi.html",
            {"vslink": "NEW"},
        )
    ]
    assert pdfs == [
        {
            "url": "https://drive.google.com/uc?export=download&id=DRIVE_2023",
            "label": "Завантажити Заболотний 2023 Завантажити",
            "filename": "DRIVE_2023.pdf",
            "gdrive_id": "DRIVE_2023",
        }
    ]


def test_multi_part_fallback_matches_primary_component_position():
    fallback = [
        {"gdrive_id": "PART_1"},
        {"gdrive_id": "PART_2"},
    ]

    assert _fallback_for_component(
        fallback,
        primary_count=2,
        component_index=1,
    ) == {"gdrive_id": "PART_2"}

    with pytest.raises(DownloadValidationError, match="volume count"):
        _fallback_for_component(fallback, primary_count=1, component_index=0)


def test_check_filename_overlap():
    # Test our warn-only filename overlap checks
    # Case 1: Overlap exists
    assert check_filename_overlap("ukrmova_2_bolsh.pdf", "ukrainska_mova", "Большакова") is True

    # Case 2: Overlap exists via transliteration
    assert check_filename_overlap("5-klas-matematyka-ister-2022.pdf", "matematyka", "Істер") is True

    # Case 3: Overlap missing
    assert check_filename_overlap("random_filename_123.pdf", "ukrainska_mova", "Большакова") is False


def test_retained_store_must_already_exist(tmp_path):
    from scripts.crawl.download_textbooks import resolve_retained_store

    with pytest.raises(ValueError, match="existing directory"):
        resolve_retained_store(tmp_path / "missing-drive-store")


def test_retained_match_uses_metadata_without_opening_cloud_pdf(tmp_path):
    retained = tmp_path / "grade-06" / "6-klas-ukrmova-golub-2023.pdf"
    retained.parent.mkdir()
    retained.write_bytes(b"cloud-placeholder")
    wrong_year = retained.parent / "6-klas-ukrmova-golub-2022.pdf"
    wrong_year.write_bytes(b"other")
    wrong_subject = retained.parent / "6-klas-ukrlit-golub-2023.pdf"
    wrong_subject.write_bytes(b"other")

    matches = find_retained_book_pdfs(
        tmp_path,
        {
            "grade": 6,
            "subject": "ukrainska_mova",
            "author": "Голуб",
            "year": 2023,
        },
    )

    assert matches == [retained]


def test_retained_match_accepts_combined_grade_volume(tmp_path):
    retained = tmp_path / "grade-10" / "10-11-klas-mystectvo-nazarenko-2018.pdf"
    retained.parent.mkdir()
    retained.write_bytes(b"cloud-placeholder")

    matches = find_retained_book_pdfs(
        tmp_path,
        {
            "grade": 10,
            "subject": "mystetstvo",
            "author": "Назаренко",
            "year": 2018,
        },
    )

    assert matches == [retained]


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
        <form id="downloadForm" action="https://drive.usercontent.google.com/download" method="GET">
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
            assert url == "https://drive.usercontent.google.com/download"
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


def test_download_pdf_atomic_success(tmp_path):
    dest = tmp_path / "grade-06" / "book.pdf"
    pdf_data = b"%PDF-1.7\nfixture-bytes"
    response = MockGdriveResponse(pdf_data, headers={"Content-Length": str(len(pdf_data))})

    with patch("requests.get", return_value=response):
        assert download_pdf("https://example.test/book.pdf", dest, retained_store=tmp_path) is True

    assert dest.read_bytes() == pdf_data
    assert list(dest.parent.glob("*.part")) == []


def test_duplicate_download_reuse(tmp_path):
    existing = tmp_path / "grade-06" / "existing.pdf"
    existing.parent.mkdir(parents=True)
    pdf_data = b"%PDF-1.7\nidentical"
    existing.write_bytes(pdf_data)
    dest = tmp_path / "grade-06" / "new-name.pdf"
    response = MockGdriveResponse(pdf_data)

    with patch("requests.get", return_value=response):
        assert download_pdf("https://example.test/book.pdf", dest, retained_store=tmp_path) is False

    assert not dest.exists()
    assert existing.read_bytes() == pdf_data
    assert list(dest.parent.glob("*.part")) == []


def test_duplicate_scan_hashes_only_same_size_cloud_candidates(tmp_path):
    from scripts.crawl import download_textbooks

    same_size = tmp_path / "same.pdf"
    different_size = tmp_path / "different.pdf"
    candidate = b"%PDF-1.7\ncandidate"
    same_size.write_bytes(b"%PDF-1.7\nnot-same!")
    assert same_size.stat().st_size == len(candidate)
    different_size.write_bytes(b"%PDF-1.7\nmuch-longer-than-the-candidate")
    hashed: list[str] = []
    real_hash = download_textbooks._sha256_file

    def tracked_hash(path):
        hashed.append(path.name)
        return real_hash(path)

    response = MockGdriveResponse(candidate)
    dest = tmp_path / "new.pdf"
    with (
        patch("requests.get", return_value=response),
        patch.object(download_textbooks, "_sha256_file", side_effect=tracked_hash),
    ):
        assert download_pdf("https://example.test/book.pdf", dest, retained_store=tmp_path) is True

    assert hashed == ["same.pdf"]


def test_download_pdf_rejects_bad_signature_and_cleans_temp(tmp_path):
    dest = tmp_path / "book.pdf"
    response = MockGdriveResponse(b"not a PDF", headers={"Content-Type": "text/html"})

    with patch("requests.get", return_value=response), pytest.raises(DownloadValidationError, match="not a PDF"):
        download_pdf("https://example.test/book.pdf", dest, retained_store=tmp_path)

    assert not dest.exists()
    assert list(tmp_path.glob("*.part")) == []


def test_download_pdf_rejects_declared_size_limit_before_retain(tmp_path):
    dest = tmp_path / "book.pdf"
    response = MockGdriveResponse(
        b"%PDF-1.7\nlarge",
        headers={"Content-Length": "100"},
    )

    with patch("requests.get", return_value=response), pytest.raises(DownloadValidationError, match="declared response size"):
        download_pdf(
            "https://example.test/book.pdf",
            dest,
            retained_store=tmp_path,
            max_size_bytes=10,
        )

    assert not dest.exists()
    assert list(tmp_path.glob("*.part")) == []


def test_download_pdf_removes_temp_after_stream_exception(tmp_path):
    class RaisingResponse(MockGdriveResponse):
        def iter_content(self, chunk_size=8192):
            yield b"%PDF-1.7\npartial"
            raise RuntimeError("fixture stream failed")

    dest = tmp_path / "book.pdf"
    with patch("requests.get", return_value=RaisingResponse(b"unused")), pytest.raises(RuntimeError, match="fixture stream failed"):
        download_pdf("https://example.test/book.pdf", dest, retained_store=tmp_path)

    assert not dest.exists()
    assert list(tmp_path.glob("*.part")) == []
