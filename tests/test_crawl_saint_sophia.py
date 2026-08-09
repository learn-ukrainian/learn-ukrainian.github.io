"""Network-free coverage for the Saint Sophia historical-source crawler."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from scripts.crawl import crawl_saint_sophia as crawler

ROOT = "https://saintsophia.dh.gu.se/api/"


def _record(record_id: int, **changes: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": record_id,
        "title": f"Inscription {record_id}",
        "published": True,
        "transcription": "[α]·β",
        "epidoc_text": "<TEI><text>[α]·β</text></TEI>",
        "epidoc_interpretation": "<TEI><text>β</text></TEI>",
        "interpretative_edition": "[α] β",
        "romanisation": "a b",
        "translation_ukr": "тест",
        "translation_eng": "test",
        "comments_ukr": "примітка",
        "comments_eng": "note",
        "language": 1,
        "writingsystem": 2,
        "min_year": 100,
        "max_year": 200,
    }
    record.update(changes)
    return record


class FakeApi:
    def __init__(self, inscription_pages: list[list[dict[str, object]]] | None = None) -> None:
        self.calls: list[str] = []
        self.inscription_pages = inscription_pages or [[_record(1), _record(2)], [_record(3)]]

    def __call__(self, url: str, _timeout: float) -> bytes:
        self.calls.append(url)
        if url == ROOT:
            return b'{"version":"fixture-v1", "spacing": true}'
        parsed = urlparse(url)
        endpoint = parsed.path.removeprefix("/api/")
        page = int(parse_qs(parsed.query).get("page", ["1"])[0])
        if endpoint == "inscriptions/inscription/":
            results = self.inscription_pages[page - 1]
            next_url = None
            if page < len(self.inscription_pages):
                next_url = f"{ROOT}inscriptions/inscription/?depth=2&page={page + 1}"
            return json.dumps(
                {"count": sum(map(len, self.inscription_pages)), "next": next_url, "results": results},
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
        if endpoint == "inscriptions/language/":
            results = [{"id": 1, "text": "Greek"}]
        elif endpoint == "inscriptions/writingsystem/":
            results = [{"id": 2, "text": "Greek alphabet"}]
        else:
            results = []
        return json.dumps({"count": len(results), "next": None, "results": results}, separators=(",", ":")).encode()


def _crawl(tmp_path: Path, fake: FakeApi, *, previous: Path | None = None) -> Path:
    return crawler.crawl_snapshot(
        tmp_path / "snapshot",
        api_root=ROOT,
        previous_jsonl=previous,
        fetch_bytes=fake,
        page_size=2,
    )


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_complete_pagination_preserves_raw_bytes_and_text_layers(tmp_path: Path) -> None:
    fake = FakeApi()
    output = _crawl(tmp_path, fake)

    rows = _jsonl(output / "historical_source_records.jsonl")
    assert [row["source_record_id"] for row in rows] == ["1", "2", "3"]
    assert rows[0]["original_transcription"] == "[α]·β"
    assert rows[0]["epidoc_text"] == "<TEI><text>[α]·β</text></TEI>"
    assert rows[0]["interpretative_edition"] == "[α] β"
    assert rows[0]["commentary_ukr"] == "примітка"
    assert rows[0]["source_language_label"] == "Greek"
    assert rows[0]["metadata"]["source_record"]["transcription"] == "[α]·β"
    raw_root = output / "raw" / "api-root.json"
    assert raw_root.read_bytes() == b'{"version":"fixture-v1", "spacing": true}'


def test_raw_page_bytes_are_stored_without_reserialization(tmp_path: Path) -> None:
    fake = FakeApi()
    output = _crawl(tmp_path, fake)
    expected = json.dumps(
        {"count": 3, "next": f"{ROOT}inscriptions/inscription/?depth=2&page=2", "results": fake.inscription_pages[0]},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    assert (output / "raw" / "pages" / "inscriptions__inscription" / "page-000001.json").read_bytes() == expected


def test_epidoc_parse_failure_and_invalid_dates_are_quarantined_without_repair(tmp_path: Path) -> None:
    bad = _record(1, epidoc_text="<TEI><text>unclosed", min_year=400, max_year=100)
    fake = FakeApi([[bad]])
    output = _crawl(tmp_path, fake)
    row = _jsonl(output / "historical_source_records.jsonl")[0]
    assert row["epidoc_text"] == "<TEI><text>unclosed"
    assert row["min_year"] == 400
    assert row["max_year"] == 100
    assert row["disposition"] == "quarantined_metadata"
    assert row["quality_flags"] == ["date_range_inversion", "epidoc_parse_failure"]


def test_nontextual_record_is_retained(tmp_path: Path) -> None:
    no_text = _record(
        1,
        transcription="",
        epidoc_text="",
        epidoc_interpretation="",
        interpretative_edition="",
        romanisation="",
        translation_ukr="",
        translation_eng="",
        comments_ukr="",
        comments_eng="",
    )
    output = _crawl(tmp_path, FakeApi([[no_text]]))
    row = _jsonl(output / "historical_source_records.jsonl")[0]
    assert row["source_record_id"] == "1"
    assert row["disposition"] == "non_textual_or_no_text"


def test_lookup_failure_is_quarantined_instead_of_inventing_a_label(tmp_path: Path) -> None:
    output = _crawl(tmp_path, FakeApi([[_record(1, language=999)]]))
    row = _jsonl(output / "historical_source_records.jsonl")[0]
    assert row["source_language_label"] is None
    assert row["metadata"]["source_language_id"] == 999
    assert row["disposition"] == "quarantined_metadata"
    assert row["quality_flags"] == ["source_language_lookup_failure"]


def test_null_portal_layers_are_preserved_as_null(tmp_path: Path) -> None:
    source = _record(
        1,
        title=None,
        epidoc_text=None,
        epidoc_interpretation=None,
        translation_ukr=None,
        comments_ukr=None,
        language=None,
        writingsystem=None,
    )
    row = _jsonl(_crawl(tmp_path, FakeApi([[source]])) / "historical_source_records.jsonl")[0]
    assert row["title"] is None
    assert row["epidoc_text"] is None
    assert row["translation_ukr"] is None
    assert row["commentary_ukr"] is None
    assert row["source_language_label"] is None
    assert "source_language_lookup_failure" not in row["quality_flags"]


@pytest.mark.parametrize(
    ("pages", "message"),
    [
        ([[_record(1)], [_record(1)]], "duplicate"),
        ([[_record(1)]], "incomplete pagination"),
    ],
)
def test_duplicate_ids_and_count_mismatches_fail_without_partial_output(
    tmp_path: Path, pages: list[list[dict[str, object]]], message: str
) -> None:
    fake = FakeApi(pages)
    if message == "incomplete pagination":
        original = fake

        def count_mismatch(url: str, timeout: float) -> bytes:
            raw = original(url, timeout)
            if "inscription" in url and url != ROOT:
                payload = json.loads(raw)
                payload["count"] = 2
                return json.dumps(payload).encode()
            return raw

        fetch = count_mismatch
    else:
        fetch = fake
    target = tmp_path / "snapshot"
    with pytest.raises(crawler.CrawlError, match=message):
        crawler.crawl_snapshot(target, api_root=ROOT, fetch_bytes=fetch)
    assert not target.exists()
    assert not list(tmp_path.glob(".snapshot.tmp-*"))


def test_rejects_cross_host_next_url(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"

    def bad_next(_url: str, _timeout: float) -> bytes:
        return b'{"count":1,"next":"https://example.invalid/api/next","results":[{}]}'

    with pytest.raises(crawler.CrawlError, match="unexpected pagination scheme or host"):
        crawler.fetch_endpoint(
            "inscriptions/language/",
            api_root=ROOT,
            raw_directory=raw_dir,
            timeout=1,
            retries=0,
            page_size=1,
            fetch_bytes=bad_next,
        )


def test_same_host_http_next_is_upgraded_without_insecure_request(tmp_path: Path) -> None:
    calls: list[str] = []

    def downgraded_next(url: str, _timeout: float) -> bytes:
        calls.append(url)
        page = int(parse_qs(urlparse(url).query).get("page", ["1"])[0])
        if page == 1:
            return (
                b'{"count":2,"next":"http://saintsophia.dh.gu.se/api/inscriptions/'
                b'language/?page=2","results":[{"id":1}]}'
            )
        return b'{"count":2,"next":null,"results":[{"id":2}]}'

    rows, manifest = crawler.fetch_endpoint(
        "inscriptions/language/",
        api_root=ROOT,
        raw_directory=tmp_path / "raw",
        timeout=1,
        retries=0,
        page_size=1,
        fetch_bytes=downgraded_next,
    )
    assert [row["id"] for row in rows] == [1, 2]
    assert calls[1].startswith("https://saintsophia.dh.gu.se/")
    assert manifest[0]["pagination_http_to_https_upgrade"] is True


def test_only_allowlisted_contributor_endpoint_accepts_bare_list(tmp_path: Path) -> None:
    def bare_list(_url: str, _timeout: float) -> bytes:
        return b'[{"authors_ordered":["Contributor"],"author_id":[1]}]'

    rows, _manifest = crawler.fetch_endpoint(
        "inscriptions/inscription-contributors/",
        api_root=ROOT,
        raw_directory=tmp_path / "allowed" / "raw",
        timeout=1,
        retries=0,
        page_size=1,
        fetch_bytes=bare_list,
    )
    assert rows == [{"authors_ordered": ["Contributor"], "author_id": [1]}]
    with pytest.raises(crawler.CrawlError, match="unexpected paginated response shape"):
        crawler.fetch_endpoint(
            "inscriptions/language/",
            api_root=ROOT,
            raw_directory=tmp_path / "rejected" / "raw",
            timeout=1,
            retries=0,
            page_size=1,
            fetch_bytes=bare_list,
        )


def test_rejects_media_next_url_before_requesting_it(tmp_path: Path) -> None:
    calls: list[str] = []

    def media_next(url: str, _timeout: float) -> bytes:
        calls.append(url)
        return b'{"count":1,"next":"https://saintsophia.dh.gu.se/api/images/1","results":[{}]}'

    with pytest.raises(crawler.CrawlError, match="refusing media"):
        crawler.fetch_endpoint(
            "inscriptions/language/",
            api_root=ROOT,
            raw_directory=tmp_path / "raw",
            timeout=1,
            retries=0,
            page_size=1,
            fetch_bytes=media_next,
        )
    assert calls == [f"{ROOT}inscriptions/language/?page_size=1"]


def test_rejects_same_host_next_url_outside_allowed_endpoint(tmp_path: Path) -> None:
    calls: list[str] = []

    def escaped_next(url: str, _timeout: float) -> bytes:
        calls.append(url)
        return (
            b'{"count":1,"next":"https://saintsophia.dh.gu.se/api/inscriptions/tags/",'
            b'"results":[{}]}'
        )

    with pytest.raises(crawler.CrawlError, match="escaped the allowed endpoint"):
        crawler.fetch_endpoint(
            "inscriptions/language/",
            api_root=ROOT,
            raw_directory=tmp_path / "raw",
            timeout=1,
            retries=0,
            page_size=1,
            fetch_bytes=escaped_next,
        )
    assert calls == [f"{ROOT}inscriptions/language/?page_size=1"]


def test_dispositions_have_exactly_the_source_record_ids_and_no_media_calls(tmp_path: Path) -> None:
    fake = FakeApi()
    output = _crawl(tmp_path, fake)
    records = _jsonl(output / "historical_source_records.jsonl")
    dispositions = _jsonl(output / "dispositions.jsonl")
    assert {row["source_record_id"] for row in records} == {row["source_record_id"] for row in dispositions}
    media_terms = ("image", "iiif", "annotation-media", "rti", "mesh", "geojson", "download")
    assert not any(term in url.lower() for term in media_terms for url in fake.calls)


def test_incremental_diff_lists_added_changed_and_removed_ids(tmp_path: Path) -> None:
    previous = tmp_path / "previous.jsonl"
    previous.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {"source_record_id": "1", "raw_record_sha256": crawler._sha256(crawler._stable_json_bytes(_record(1)))},
                {"source_record_id": "2", "raw_record_sha256": "changed"},
                {"source_record_id": "9", "raw_record_sha256": "removed"},
            )
        )
        + "\n",
        encoding="utf-8",
    )
    receipt = json.loads(_crawl(tmp_path, FakeApi(), previous=previous).joinpath("coverage-receipt.json").read_text(encoding="utf-8"))
    assert receipt["diff"]["added_source_record_ids"] == ["3"]
    assert receipt["diff"]["changed_source_record_ids"] == ["2"]
    assert receipt["diff"]["removed_source_record_ids"] == ["9"]
