"""Rendered quote rights, verbatim excerpt, and visible attribution regressions."""

import pytest

from scripts.build.fresh.assemble import (
    AssemblerError,
    _render_urok_markdown,
    assemble_expanded_document,
    build_resursy_entries,
    build_resursy_tab,
)
from scripts.curriculum.resolver.classify import classify_unit
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument

BOOK = "1-klas-bukvar-zaharijchuk-2025-1"


def render_quote(file=BOOK, quote="Synthetic exact excerpt", page=39):
    draft = {"steps": [{"id": "s1", "blocks": [{"kind": "quote", "ref": "T-001"}]}]}
    record = {"id": "T-001", "quote": quote, "source": {"kind": "textbook", "file": file, "page": page}}
    stressed = {"units": [{"tab": "urok", "step": "s1", "block": 0, "role": "record_print", "text": quote}]}
    return _render_urok_markdown(draft, stressed, {"texts": [record]}, {"words": []})


def test_rendered_quote_is_verbatim_and_attributed():
    quote = "Synthetic exact excerpt —  preserve  spacing!"
    markdown, units = render_quote(quote=quote)
    assert f"> {quote}\n>\n> — *Захарійчук, «Українська мова. Буквар», 1 клас, ч. 1, 2025, с. 39*" in markdown
    assert units.texts()[0] == quote


@pytest.mark.parametrize(
    "file,quote,page,code",
    [
        ("ulp-1-00-lesson-notes", "Synthetic excerpt", 39, "publication_right"),
        ("not-registered", "Synthetic excerpt", 39, "publication_right"),
        ("9-klas-tekhnolohiyi-bilenko-2026", "Synthetic excerpt", 39, "publication_right"),
        ("anna-ohoiko-500-verbs", "Synthetic excerpt", 39, "publication_right"),
        (BOOK, "x" * 801, 39, "publication_limit"),
        (BOOK, "Synthetic excerpt", None, "publication_attribution"),
    ],
)
def test_renderer_cannot_bypass_quote_admission(file, quote, page, code):
    with pytest.raises(AssemblerError) as caught:
        render_quote(file, quote, page)
    assert caught.value.code == code


@pytest.mark.parametrize(
    "file,citation",
    [
        (BOOK, "Захарійчук, «Українська мова. Буквар», 1 клас, ч. 1, 2025, с. 12"),
        ("1-klas-bukvar-zaharijchuk-2025-2", "Захарійчук, «Українська мова. Буквар», 1 клас, ч. 2, 2025, с. 12"),
        ("10-11-klas-mystectvo-nazarenko-2018", "Назаренко, «Мистецтво», 10–11 клас, 2018, с. 12"),
        ("5-klas-ukrmova-zabolotnyi-2023", "Заболотний, «Українська мова», 5 клас, 2022, с. 12"),
        ("7-klas-tekhnolohiyi-bilenko-2024", "Біленко, «Технології», 7 клас, 2023, с. 12"),
        (
            "9-klas-zarubizhna-literatura-kovbasenko-2026",
            "Ковбасенко, «Зарубіжна література», 9 клас, 2025, с. 12",
        ),
    ],
)
def test_quote_and_resources_show_same_human_citation(file, citation):
    markdown, _units = render_quote(file=file, page=12)
    assert citation in markdown
    pack = {
        "texts": [
            {
                "id": "T-001",
                "quote": "Synthetic excerpt",
                "source": {
                    "kind": "textbook",
                    "file": file,
                    "page": 12,
                    "work": "Spoofed English title",
                    "author": "Spoof",
                },
            }
        ]
    }
    tab = build_resursy_tab({"steps": [{"evidence": ["T-001"]}]}, pack)
    entry = tab["books"][0]
    assert entry["title"] == citation
    assert entry["pages"] == entry["author"] == ""
    assert file not in str(tab)


@pytest.mark.parametrize("file", ["9-klas-tekhnolohiyi-bilenko-2026", "uni-unregistered"])
def test_resources_omit_unconfirmed_title_with_warning(file):
    pack = {"texts": [{"id": "T-001", "source": {"kind": "textbook", "file": file, "page": 12}}]}
    warnings = []
    lesson = {"steps": [{"explains": ["T-001"]}]}
    assert build_resursy_entries(lesson, pack, warnings=warnings) == []
    assert build_resursy_tab(lesson, pack) == {}
    assert warnings == [{"code": "resource_citation_omitted", "record": "T-001", "reason": "citable_metadata_missing"}]


def test_bibliography_is_metadata_while_quote_prose_stays_checked():
    draft = {"status": "ok", "steps": [{"id": "s1", "blocks": [{"kind": "quote", "ref": "T-001"}]}]}
    pack = {"texts": [{"id": "T-001", "quote": "Цитата", "source": {"kind": "textbook", "file": BOOK, "page": 12}}]}
    plan = {"lessons": [{"n": 1, "steps": [{"id": "s1", "evidence": ["T-001"]}]}]}
    expanded, provenance = assemble_expanded_document(draft, plan, pack, {"words": []}, "a1", "fixture", 1)
    document = ExpandedDocument.from_data(expanded)
    allowlist = Allowlist.from_records([])
    citation = next(unit for unit in document.units if unit.tab == "resursy")
    assert citation.text == "Захарійчук, «Українська мова. Буквар», 1 клас, ч. 1, 2025, с. 12"
    assert all(token.final == "skipped:vesum_exempt" for token in classify_unit(citation, allowlist))
    quote = next(unit for unit in document.units if unit.tab == "urok")
    assert all(token.needs_lookup for token in classify_unit(quote, allowlist))
    resource_span = next(span for span in provenance["spans"] if span["tab"] == "resursy")
    assert resource_span["ref"] == "T-001" and resource_span["source"] == "record"


def test_ulp_resource_renders_homepage_and_episode_without_private_text():
    from scripts.generate_mdx.resources import format_resources_for_mdx

    record = {
        "id": "T-001",
        "source": {"kind": "textbook", "file": "ulp-1-00-lesson-notes", "page": 12},
        "episode_url": "https://www.ukrainianlessons.com/episode1/",
        "quote": "PRIVATE QUOTE",
        "supports": "PRIVATE SUPPORTS",
    }
    resources = build_resursy_tab({"steps": [{"explains": ["T-001"]}]}, {"texts": [record]})
    rendered = format_resources_for_mdx(resources, True)
    assert "[Ukrainian Lessons Podcast — Анна Огойко](https://www.ukrainianlessons.com/)" in rendered
    assert "[https://www.ukrainianlessons.com/episode1/](https://www.ukrainianlessons.com/episode1/)" in rendered
    assert "<https://www.ukrainianlessons.com/episode1/>" not in rendered
    assert "PRIVATE" not in rendered


def test_missing_resource_record_and_registry_still_fail(tmp_path, monkeypatch):
    from scripts.curriculum.evidence import publication

    with pytest.raises(AssemblerError, match="text_not_found"):
        build_resursy_tab({"steps": [{"explains": ["T-001"]}]}, {"texts": []})
    monkeypatch.setattr(publication, "REGISTRY_PATH", tmp_path / "absent")
    with pytest.raises(AssemblerError, match="publication_registry_unreadable"):
        build_resursy_tab(
            {"steps": [{"explains": ["T-001"]}]},
            {"texts": [{"id": "T-001", "source": {"kind": "textbook", "file": BOOK, "page": 12}}]},
        )
