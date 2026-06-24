from __future__ import annotations

from typing import Any

from scripts.build import linear_pipeline


def _reading_external() -> dict[str, Any]:
    # Matches koliadky-style readings: an external free-full-text source_url.
    return {
        "title": "«Як ще не було початку світа»",
        "genre": "Колядка",
        "source": "Народна творчість; корпус ukrlib-narod-dumy",
        "source_url": "https://www.ukrlib.com.ua/narod/printout.php?id=5&bookid=2",
        "license": "public_domain",
        "hosting": "host",
        "reading_slug": "koliadka-yak-shche-ne-bulo",
    }


def _reading_corpus_only() -> dict[str, Any]:
    # Matches vesnianky-style readings: corpus-only, on-site hosted, NO external URL.
    return {
        "title": "«Вже весна воскресла, що ж сь нам принесла»",
        "genre": "Веснянка",
        "source": "Народна творчість; запис Грушевського; корпус chunk da46aa92_c0178",
        "license": "public_domain",
        "hosting": "host",
        "reading_slug": "vesnianka-vzhe-vesna-voskresla",
    }


def test_external_reading_becomes_url_bearing_resource() -> None:
    plan = {"readings": [_reading_external()]}
    resources = linear_pipeline._merge_resources(plan, [])
    readings = [r for r in resources if r.get("role") == "reading"]
    assert len(readings) == 1
    r = readings[0]
    # The external free-full-text URL is carried verbatim (allowlist-checkable),
    # never an on-site /readings/ path.
    assert r["url"] == "https://www.ukrlib.com.ua/narod/printout.php?id=5&bookid=2"
    assert not linear_pipeline._is_on_site_resource_url(r["url"])
    assert r.get("source_ref") == "koliadka-yak-shche-ne-bulo"


def test_corpus_only_reading_is_not_a_url_bearing_resource() -> None:
    # On-site-hosted, corpus-only readings are surfaced via :::primary-reading +
    # the reading_coverage gate — never as a fabricated /readings/<slug>/ resource
    # (which resources_url_resolve rejects as relative_url_not_allowed).
    plan = {"readings": [_reading_corpus_only()]}
    resources = linear_pipeline._merge_resources(plan, [])
    assert not any(r.get("role") == "reading" for r in resources)
    assert not any(
        linear_pipeline._is_on_site_resource_url(str(r.get("url") or "")) and r.get("url")
        for r in resources
    )


def test_mixed_readings_keep_external_drop_corpus_only() -> None:
    plan = {"readings": [_reading_external(), _reading_corpus_only()]}
    resources = linear_pipeline._merge_resources(plan, [])
    reading_urls = [r["url"] for r in resources if r.get("role") == "reading"]
    assert reading_urls == ["https://www.ukrlib.com.ua/narod/printout.php?id=5&bookid=2"]
