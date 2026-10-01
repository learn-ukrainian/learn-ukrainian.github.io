"""Rendered quote rights, verbatim excerpt, and visible attribution regressions."""

import pytest

from scripts.build.fresh.assemble import (
    AssemblerError,
    _render_urok_markdown,
    assemble_expanded_document,
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


@pytest.mark.parametrize("file", ["9-klas-tekhnolohiyi-bilenko-2026", "unregistered"])
def test_resources_refuse_unconfirmed_title(file):
    pack = {"texts": [{"id": "T-001", "source": {"kind": "textbook", "file": file, "page": 12}}]}
    with pytest.raises(AssemblerError, match="publication_attribution"):
        build_resursy_tab({"steps": [{"evidence": ["T-001"]}]}, pack)


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
