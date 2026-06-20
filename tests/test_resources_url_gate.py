from __future__ import annotations

import pytest

from scripts.build import linear_pipeline

BAD_URLS = [
    "https://www.ukrlib.com.ua/narod/book.php?id=11",
    "https://www.ukrlib.com.ua/narod/",
    "https://osvita.ua/school/literature/",
    "https://diasporiana.org.ua/category/folklor/",
    "https://www.ukrlib.com.ua/narod/",
    "https://www.ukrlib.com.ua/narod/book.php?id=2",
    "https://www.ukrlib.com.ua/narod/book.php?id=6",
    "https://osvita.ua/school/literature/",
    "https://diasporiana.org.ua/category/folklor/",
]


@pytest.mark.parametrize("url", BAD_URLS)
def test_resources_url_resolve_rejects_known_bad_folk_urls(url: str) -> None:
    result = linear_pipeline._resources_url_resolve_gate(
        [{"title": "bad fixture", "role": "article", "url": url}],
        level="folk",
        resource_liveness_fn=None,
    )

    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["checked"] == 1
    assert result["results"][0]["resolved"] is False


def test_resources_url_resolve_accepts_allowlisted_absolute_urls() -> None:
    resources = [
        {
            "title": "Іпатіївський літопис",
            "role": "reading",
            "url": "http://litopys.org.ua/ipatlet/ipat.htm",
            "notes": "прочитай уривок літопису й познач формулу оповіді",
        },
        {
            "title": "Купало",
            "role": "wiki",
            "url": "https://uk.wikipedia.org/wiki/Купало",
        },
        {
            "title": "Замовляння",
            "role": "wiki",
            "url": "https://uk.wikipedia.org/wiki/Замовляння",
        },
    ]

    result = linear_pipeline._resources_url_resolve_gate(
        resources,
        level="folk",
        resource_liveness_fn=None,
    )

    assert result["passed"] is True
    assert result["checked"] == 3
    assert {entry["reason"] for entry in result["results"]} == {"resolved"}


def test_resources_url_resolve_rejects_relative_urls() -> None:
    result = linear_pipeline._resources_url_resolve_gate(
        [
            {
                "title": "Topic wiki",
                "role": "reading",
                "url": "wiki/folk/kupalo",
                "notes": "прочитай короткий локальний огляд теми",
            }
        ],
        level="folk",
        resource_liveness_fn=None,
    )

    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["checked"] == 1
    assert result["results"][0]["resolved"] is False
    assert result["results"][0]["reason"] == "relative_url_not_allowed"


def test_resources_url_resolve_is_not_applicable_to_core_tracks() -> None:
    result = linear_pipeline._resources_url_resolve_gate(
        [
            {
                "title": "Learner video",
                "role": "youtube",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            }
        ],
        level="a1",
        resource_liveness_fn=None,
    )

    assert result["passed"] is True
    assert result["skipped"] == "not_applicable_non_seminar_level"
    assert result["checked"] == 0


def test_resources_url_resolve_static_path_does_not_attempt_liveness() -> None:
    result = linear_pipeline._resources_url_resolve_gate(
        [
            {
                "title": "Вікіджерела",
                "role": "reading",
                "url": "https://uk.wikisource.org/wiki/Енеїда_(Котляревський)",
                "notes": "прочитай початок твору й зверни увагу на регістр",
            }
        ],
        level="folk",
        resource_liveness_fn=None,
    )

    assert result["passed"] is True
    assert result["liveness_checked"] is False
    assert result["results"][0]["live"] is None


def test_resources_url_resolve_does_not_http_check_relative_refs() -> None:
    def fail_if_called(url: str) -> bool:
        raise AssertionError(f"unexpected liveness check for {url}")

    result = linear_pipeline._resources_url_resolve_gate(
        [
            {
                "title": "Topic wiki",
                "role": "reading",
                "url": "wiki/folk/zamovliannia-zaklynannia-prymovky",
                "notes": "прочитай локальний огляд теми",
            }
        ],
        level="folk",
        resource_liveness_fn=fail_if_called,
    )

    assert result["passed"] is False
    assert result["results"][0]["resolved"] is False
    assert result["results"][0]["reason"] == "relative_url_not_allowed"


def test_resources_url_resolve_rejects_scheme_less_relative_url() -> None:
    result = linear_pipeline._resources_url_resolve_gate(
        [
            {
                "title": "Local resource",
                "role": "article",
                "url": "foo/bar",
            }
        ],
        level="folk",
        resource_liveness_fn=None,
    )

    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["checked"] == 1
    assert result["results"][0]["resolved"] is False
    assert result["results"][0]["reason"] == "relative_url_not_allowed"
